"""Live GUI Preview panel for Softsembly.

Shows a tkinter/turtle program's window inside the IDE and refreshes it as the
student types. The Run button is untouched: the preview is a separate,
throwaway process that is killed and relaunched on every change, while Run is
the real run with shell, debugger and input().

How it works
------------
1. Editor text changes -> wait until typing pauses (debounce).
2. Skip files that don't import a GUI library; syntax-check with compile().
   On a syntax error the last working preview stays up with a warning.
3. Kill the previous preview process and start
   `python softsembly_preview_bootstrap.py <temp copy> <real path> <frame id>`.
   The bootstrap embeds the program's first Tk window into our container frame
   (Tk's `use=` option) and reports progress through marker lines on stdout.
4. A watchdog kills the preview if the program never opens a window, or if the
   window's event loop stops running. The bootstrap sends a heartbeat from a Tk
   timer, which only fires while the event loop runs, so an endless loop in
   setup code or in a button handler stops the heartbeat.
"""

import json
import os
import queue
import re
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from logging import getLogger
from tkinter import ttk
from typing import Optional

import thonny
from thonny import get_runner, get_workbench
from thonny import softsembly as palette
from thonny.ui_utils import SafeScrollbar, ems_to_pixels

logger = getLogger(__name__)

MARKER = "@@SSPREVIEW@@ "
BOOTSTRAP_PATH = os.path.join(os.path.dirname(thonny.__file__), "softsembly_preview_bootstrap.py")

# Only previews programs that use a Tk-based GUI library.
GUI_IMPORT_RE = re.compile(
    r"^\s*(?:import|from)\s+(?:tkinter|turtle|customtkinter|ttkbootstrap)\b", re.MULTILINE
)

LIVE_OPTION = "softsembly_preview.live"

STATUS_INFO = "info"
STATUS_OK = "ok"
STATUS_WARN = "warn"
STATUS_ERROR = "error"


class PreviewView(ttk.Frame):
    DEBOUNCE_MS = 700
    WINDOW_TIMEOUT_MS = 5000  # program must create tk.Tk() within this time
    HEARTBEAT_TIMEOUT_MS = 5000  # ...and its event loop must keep running (heartbeats)
    POLL_MS = 100

    def __init__(self, master):
        super().__init__(master)
        self._proc: Optional[subprocess.Popen] = None
        self._generation = 0  # increments per launch; stale events are ignored
        self._events: "queue.Queue" = queue.Queue()
        self._container: Optional[tk.Frame] = None
        self._container_item = None
        self._temp_source: Optional[str] = None
        self._debounce_id = None
        self._poll_id = None
        self._watchdog_id = None
        self._got_window = False
        self._responsive = False
        self._last_launched_source: Optional[str] = None
        self._error_line: Optional[int] = None
        self._stderr_tail: list = []
        self._showing_error = False
        self._auto_fitted_paths: set = set()
        self._display_path = ""

        self._init_widgets()

        wb = get_workbench()
        self._tab_binding = wb.get_editor_notebook().bind(
            "<<NotebookTabChanged>>", lambda e: self._schedule_refresh(force=True), True
        )
        wb.bind_class("EditorCodeViewText", "<<TextChange>>", self._on_text_change, True)
        wb.bind("Save", lambda e: self._schedule_refresh(), True)
        wb.bind("WorkbenchClose", lambda e: self.winfo_exists() and self.stop(), True)
        self.bind("<Map>", lambda e: self._schedule_refresh(force=True), True)
        self.bind("<Unmap>", lambda e: self._on_unmap(), True)
        self.bind("<<ThemeChanged>>", lambda e: self._apply_theme(), True)

    # ------------------------------------------------------------------ UI

    def _init_widgets(self) -> None:
        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=ems_to_pixels(0.5), pady=4)

        get_workbench().set_default(LIVE_OPTION, True)
        self._live_var = tk.BooleanVar(value=get_workbench().get_option(LIVE_OPTION))
        ttk.Checkbutton(
            toolbar, text="Live", variable=self._live_var, command=self._on_live_toggled
        ).pack(side="left")
        ttk.Button(
            toolbar, text="Refresh", command=lambda: self._schedule_refresh(force=True, delay=0)
        ).pack(side="left", padx=(8, 0))

        self._status = ttk.Label(self, text="", anchor="w", justify="left", cursor="")
        self._status.grid(row=1, column=0, columnspan=2, sticky="ew", padx=ems_to_pixels(0.5))
        self._status.bind("<Button-1>", self._on_status_click, True)
        self._status.bind(
            "<Configure>", lambda e: self._status.configure(wraplength=max(e.width - 8, 100)), True
        )

        self._canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        self._vsb = SafeScrollbar(self, orient="vertical", command=self._canvas.yview)
        self._hsb = SafeScrollbar(self, orient="horizontal", command=self._canvas.xview)
        self._canvas.configure(yscrollcommand=self._vsb.set, xscrollcommand=self._hsb.set)
        self._canvas.grid(row=2, column=0, sticky="nsew", pady=(4, 0))
        self._vsb.grid(row=2, column=1, sticky="ns", pady=(4, 0))
        self._hsb.grid(row=3, column=0, sticky="ew")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self._apply_theme()

    def _apply_theme(self) -> None:
        style = ttk.Style()
        bg = style.lookup("TFrame", "background") or palette.BACKGROUND
        self._canvas.configure(background=bg)
        self._status_colors = {
            STATUS_INFO: style.lookup("TLabel", "foreground") or palette.SECONDARY_TEXT,
            STATUS_OK: palette.GREEN,
            STATUS_WARN: palette.YELLOW,
            STATUS_ERROR: palette.ERROR,
        }

    def _set_status(self, text: str, kind: str = STATUS_INFO, line: Optional[int] = None) -> None:
        self._error_line = line
        color = getattr(self, "_status_colors", {}).get(kind)
        self._status.configure(text=text, foreground=color, cursor="hand2" if line else "")

    def _on_status_click(self, event=None) -> None:
        if not self._error_line:
            return
        editor = get_workbench().get_editor_notebook().get_current_editor()
        if editor is None:
            return
        text = editor.get_text_widget()
        index = f"{self._error_line}.0"
        text.mark_set("insert", index)
        text.see(index)
        text.focus_set()

    # ------------------------------------------------------------ triggers

    def _on_text_change(self, event=None) -> None:
        if self.winfo_exists() and self._live_var.get():
            self._schedule_refresh()

    def _on_live_toggled(self) -> None:
        get_workbench().set_option(LIVE_OPTION, self._live_var.get())
        if self._live_var.get():
            self._schedule_refresh(force=True, delay=0)

    def _on_unmap(self) -> None:
        # Panel hidden (other tab selected, view closed): free the process.
        if self._debounce_id:
            self.after_cancel(self._debounce_id)
            self._debounce_id = None
        self.stop()
        self._last_launched_source = None

    def _schedule_refresh(self, force: bool = False, delay: Optional[int] = None) -> None:
        # Class/workbench bindings outlive this widget, so guard every entry point.
        if not self.winfo_exists():
            return
        if self._debounce_id:
            self.after_cancel(self._debounce_id)
        self._debounce_id = self.after(
            self.DEBOUNCE_MS if delay is None else delay, lambda: self._refresh(force)
        )

    # ------------------------------------------------------------- refresh

    def _refresh(self, force: bool = False) -> None:
        self._debounce_id = None
        if not self.winfo_ismapped():
            return

        editor = get_workbench().get_editor_notebook().get_current_editor()
        if editor is None:
            self.stop()
            self._set_status("Open a Python file to preview its window.")
            return

        source = editor.get_content()
        if not force and source == self._last_launched_source:
            return

        if not GUI_IMPORT_RE.search(source):
            self.stop()
            self._last_launched_source = None
            self._set_status("The preview shows programs that use tkinter or turtle.")
            return

        path = editor.get_target_path() if editor.is_local() else None
        display_path = path or "<untitled>"

        try:
            compile(source, display_path, "exec")
        except SyntaxError as e:
            what = "The preview" if self._proc is None else "The last working preview"
            where = f"Line {e.lineno}: " if e.lineno else ""
            self._set_status(
                f"{where}{e.msg}. {what} will update when this is fixed.",
                STATUS_WARN,
                line=e.lineno,
            )
            return
        except Exception as e:  # e.g. null bytes, recursion limit
            self._set_status(f"Can't preview this code: {e}", STATUS_WARN)
            return

        self._launch(source, display_path, os.path.dirname(path) if path else None)

    def _launch(self, source: str, display_path: str, cwd: Optional[str]) -> None:
        self.stop()
        self._generation += 1
        generation = self._generation
        self._got_window = False
        self._responsive = False
        self._showing_error = False
        self._stderr_tail = []
        self._last_launched_source = source
        self._display_path = display_path

        fd, self._temp_source = tempfile.mkstemp(prefix="softsembly_preview_", suffix=".py")
        with os.fdopen(fd, "w", encoding="utf-8") as fp:
            fp.write(source)

        # A fresh container per launch: Tk containers aren't reliably reusable
        # after the embedded application exits.
        self._container = tk.Frame(self._canvas, container=True, borderwidth=0)
        self._container_item = self._canvas.create_window(0, 0, window=self._container, anchor="nw")
        self._container.bind("<Configure>", self._update_scrollregion, True)
        self.update_idletasks()

        cmd = [
            _get_preview_python(),
            BOOTSTRAP_PATH,
            self._temp_source,
            display_path,
            str(self._container.winfo_id()),
        ]
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
        env.pop("PYTHONSTARTUP", None)
        kwargs = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        logger.info("Starting GUI preview: %r (cwd=%r)", cmd, cwd)
        try:
            self._proc = subprocess.Popen(
                cmd,
                cwd=cwd or tempfile.gettempdir(),
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                **kwargs,
            )
        except OSError as e:
            logger.exception("Could not start preview")
            self._set_status(f"Could not start the preview: {e}", STATUS_ERROR)
            self._cleanup_after_stop()
            return

        self._set_status("Starting preview…")
        threading.Thread(
            target=self._read_stdout,
            args=(self._proc.stdout, generation),
            daemon=True,
            name="PreviewStdout",
        ).start()
        # Each launch gets its own stderr buffer, so output from a previous
        # (still exiting) process can never leak into this one's messages.
        threading.Thread(
            target=self._read_stderr,
            args=(self._proc.stderr, self._stderr_tail),
            daemon=True,
            name="PreviewStderr",
        ).start()

        self._watchdog_id = self.after(self.WINDOW_TIMEOUT_MS, lambda: self._watchdog(generation))
        self._poll_id = self.after(self.POLL_MS, self._poll)

    def _update_scrollregion(self, event=None) -> None:
        if self._container is None:
            return
        width, height = self._container.winfo_reqwidth(), self._container.winfo_reqheight()
        self._canvas.configure(scrollregion=(0, 0, width, height))
        if width > 1:
            self._fit_panel_width(width)

    def _fit_panel_width(self, app_width: int) -> None:
        """Widen the side panel so the app fits, once per file.

        Never shrinks the panel, is capped at 45% of the window, and only happens
        once per file per session, so a width the user sets by hand is respected.
        """
        if self._display_path in self._auto_fitted_paths:
            return
        self._auto_fitted_paths.add(self._display_path)

        wb = get_workbench()
        try:
            paned, pane = wb._main_pw, wb._east_pw  # Softsembly-owned layout internals
        except AttributeError:
            return
        notebook = getattr(self, "containing_notebook", None)
        if notebook is None or not str(notebook).startswith(str(pane)):
            return  # the user moved the panel to the left/bottom; leave the layout alone

        extra = self._vsb.winfo_reqwidth() + ems_to_pixels(2)
        needed = app_width + extra
        current = pane.winfo_width()
        target = min(needed, int(wb.winfo_width() * 0.45))
        if target > current:
            paned.paneconfigure(pane, width=target)

    # ------------------------------------------------- process communication

    def _read_stdout(self, stream, generation: int) -> None:
        for raw in iter(stream.readline, b""):
            line = raw.decode("utf-8", errors="replace").strip()
            if line.startswith(MARKER):
                try:
                    self._events.put((generation, json.loads(line[len(MARKER) :])))
                except ValueError:
                    pass
        self._events.put((generation, {"event": "exited"}))

    @staticmethod
    def _read_stderr(stream, tail: list) -> None:
        # Drain stderr so the pipe never fills up and blocks the program.
        for raw in iter(stream.readline, b""):
            tail.append(raw.decode("utf-8", errors="replace").rstrip())
            del tail[:-20]

    def _poll(self) -> None:
        self._poll_id = None
        while True:
            try:
                generation, msg = self._events.get_nowait()
            except queue.Empty:
                break
            if generation == self._generation:
                self._handle_event(msg)

        if self._proc is not None:
            self._poll_id = self.after(self.POLL_MS, self._poll)

    def _handle_event(self, msg: dict) -> None:
        event = msg.get("event")
        if event == "window":
            self._got_window = True
            self._restart_watchdog(self.HEARTBEAT_TIMEOUT_MS)
        elif event == "alive":
            self._restart_watchdog(self.HEARTBEAT_TIMEOUT_MS)
            if not self._responsive:
                self._responsive = True
                # After a startup error the bootstrap still runs the event loop to
                # keep the partial window visible; don't hide the error message.
                if not self._showing_error:
                    self._set_status("Live preview. Press Run to test it for real.", STATUS_OK)
        elif event == "error":
            self._showing_error = True
            line = msg.get("line")
            where = f"Line {line}: " if line else ""
            prefix = "While the app was running: " if msg.get("when") == "callback" else ""
            self._set_status(
                f"{prefix}{where}{msg.get('type')}: {msg.get('message')}", STATUS_ERROR, line=line
            )
        elif event == "notice":
            if self._status.cget("text").startswith("Live preview"):
                self._set_status(msg.get("message", ""), STATUS_INFO)
        elif event == "no_window":
            self._set_status("This program finished without opening a window.")
        elif event == "exited":
            self._proc = None
            self._cancel_watchdog()
            self._cleanup_after_stop()
            # Process died without the bootstrap explaining why (e.g. a crash in
            # Tk itself): show the last line it printed to stderr.
            explained = self._error_line is not None or self._status.cget("text").startswith(
                "This program"
            )
            if not explained and not self._responsive and self._stderr_tail:
                self._set_status(f"Preview stopped: {self._stderr_tail[-1]}", STATUS_ERROR)
            elif self._responsive and not self._showing_error:
                # e.g. the student's Quit button called window.destroy()
                self._set_status(
                    "The app closed itself. Edit the code or press Refresh to reopen it."
                )

    # ------------------------------------------------------------ watchdogs

    def _restart_watchdog(self, ms: int) -> None:
        self._cancel_watchdog()
        generation = self._generation
        self._watchdog_id = self.after(ms, lambda: self._watchdog(generation))

    def _cancel_watchdog(self) -> None:
        if self._watchdog_id:
            self.after_cancel(self._watchdog_id)
            self._watchdog_id = None

    def _watchdog(self, generation: int) -> None:
        self._watchdog_id = None
        if generation != self._generation or self._proc is None:
            return
        if self._responsive:
            msg = "The app stopped responding (an endless loop in an event handler?). Preview stopped."
        elif self._got_window:
            msg = (
                "The window opened but the code after tk.Tk() is still running "
                "(an endless loop?). Preview stopped."
            )
        else:
            msg = "The code took too long before creating a window (an endless loop?). Preview stopped."
        self.stop()
        self._set_status(msg, STATUS_WARN)

    # ------------------------------------------------------------- stopping

    def stop(self) -> None:
        self._cancel_watchdog()
        if self._poll_id:
            self.after_cancel(self._poll_id)
            self._poll_id = None
        proc, self._proc = self._proc, None
        if proc is not None and proc.poll() is None:
            proc.kill()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                logger.warning("Preview process %s did not exit", proc.pid)
        self._cleanup_after_stop()

    def _cleanup_after_stop(self) -> None:
        """Remove the embedded frame and temp file. Call only when no process is running."""
        if self._container_item is not None:
            self._canvas.delete(self._container_item)
            self._container_item = None
        if self._container is not None:
            self._container.destroy()
            self._container = None
        if self._temp_source:
            try:
                os.remove(self._temp_source)
            except OSError:
                pass
            self._temp_source = None

    def destroy(self) -> None:
        self.stop()
        try:
            get_workbench().get_editor_notebook().unbind(
                "<<NotebookTabChanged>>", self._tab_binding
            )
        except tk.TclError:
            pass
        super().destroy()


def _get_preview_python() -> str:
    """Prefer the interpreter students' programs run with (the backend)."""
    exe = None
    try:
        proxy = get_runner().get_backend_proxy()
        if (
            proxy is not None
            and proxy.has_local_interpreter()
            and proxy.interpreter_is_cpython_compatible()
        ):
            exe = proxy.get_target_executable()
    except Exception:
        logger.exception("Could not query backend interpreter")

    if not exe or not os.path.exists(exe):
        exe = sys.executable

    # python.exe (not pythonw.exe) so stdout/stderr pipes work; the console
    # window is suppressed with CREATE_NO_WINDOW instead.
    console_exe = exe.replace("pythonw.exe", "python.exe")
    return console_exe if os.path.exists(console_exe) else exe


def load_plugin() -> None:
    get_workbench().add_view(PreviewView, "GUI Preview", "ne", visible_by_default=True)
