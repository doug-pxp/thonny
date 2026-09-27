"""Runs a student's GUI program so that its window appears inside Softsembly.

Launched by thonny/plugins/softsembly_preview.py in a separate, throwaway
process:

    python softsembly_preview_bootstrap.py <source_copy> <display_path> <container_id>

- source_copy:  temp file holding the editor's current (possibly unsaved) text
- display_path: the file's real path (used for __file__ and tracebacks), or "<untitled>"
- container_id: window id of the IDE frame the program's window is embedded into

The student's code runs unchanged. This script patches `tkinter.Tk` so the
first window gets `use=<container_id>`, which makes Tk draw it inside the IDE's
preview panel instead of as a separate window.

Only the standard library is used here, and nothing from `thonny` is imported,
because this runs in the student's interpreter.

The IDE is told what happened through marker lines on stdout (anything else on
stdout is the student's own print output and is ignored):

    @@SSPREVIEW@@ {"event": "window"}        first Tk window created
    @@SSPREVIEW@@ {"event": "alive"}         heartbeat: the window's event loop is running
    @@SSPREVIEW@@ {"event": "error", ...}    exception (message + line number)
    @@SSPREVIEW@@ {"event": "no_window"}     program finished without a window
    @@SSPREVIEW@@ {"event": "notice", ...}   something worth telling the student
"""

import builtins
import json
import os
import sys
import traceback

MARKER = "@@SSPREVIEW@@ "
HEARTBEAT_MS = 500

_real_stdout = sys.__stdout__


def emit(event: str, **fields) -> None:
    fields["event"] = event
    try:
        # Leading newline: the student may have printed without a trailing newline.
        _real_stdout.write("\n" + MARKER + json.dumps(fields) + "\n")
        _real_stdout.flush()
    except Exception:
        pass


def _make_dpi_aware() -> None:
    """Match Softsembly's own DPI mode so the embedded window isn't rescaled."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        user32 = ctypes.windll.user32
        try:
            set_context = user32.SetProcessDpiAwarenessContext
            set_context.argtypes = [ctypes.c_void_p]
            set_context.restype = ctypes.c_bool
            if set_context(ctypes.c_void_p(-4)):  # PER_MONITOR_AWARE_V2
                return
        except (AttributeError, OSError):
            pass
        try:
            ctypes.OleDLL("shcore").SetProcessDpiAwareness(2)
            return
        except (AttributeError, OSError):
            pass
        user32.SetProcessDPIAware()
    except Exception:
        pass


def _error_line(exc: BaseException, display_path: str):
    """Line number of the innermost traceback frame that is in the student's file."""
    line = None
    for frame in traceback.extract_tb(exc.__traceback__):
        if frame.filename == display_path:
            line = frame.lineno
    if line is None and isinstance(exc, SyntaxError) and exc.filename == display_path:
        line = exc.lineno
    return line


def _report(exc: BaseException, display_path: str, when: str) -> None:
    emit(
        "error",
        when=when,
        type=type(exc).__name__,
        message=str(exc),
        line=_error_line(exc, display_path),
    )
    traceback.print_exception(type(exc), exc, exc.__traceback__)


def _install_patches(container_id: str, display_path: str, state: dict) -> None:
    import tkinter

    original_init = tkinter.Tk.__init__

    def start_heartbeat(root) -> None:
        # Tk timers only fire while the event loop is running, however the
        # program entered it (root.mainloop(), tk.mainloop(), turtle.done(),
        # update() during an animation...). So a steady heartbeat means the
        # window is responsive, and a missing one means the code is stuck.
        def beat():
            emit("alive")
            try:
                root.after(HEARTBEAT_MS, beat)
            except Exception:
                pass

        root.after(0, beat)

    def patched_init(self, *args, **kwargs):
        # Tk(screenName, baseName, className, useTk, sync, use): only embed the
        # first window, and only if the student didn't choose `use` themselves.
        if state["root"] is None and "use" not in kwargs and len(args) < 6:
            kwargs["use"] = container_id
            original_init(self, *args, **kwargs)
            state["root"] = self
            emit("window")
            start_heartbeat(self)
        else:
            original_init(self, *args, **kwargs)
            if state["root"] is not None and self is not state["root"]:
                emit(
                    "notice",
                    message="Your program opened a second main window; "
                    "it appears outside the preview.",
                )

    def report_callback_exception(self, exc_type, exc_value, exc_tb):
        # Errors in button handlers etc. while the student clicks around the preview
        _report(exc_value, display_path, when="callback")

    tkinter.Tk.__init__ = patched_init
    tkinter.Tk.report_callback_exception = report_callback_exception

    def preview_input(prompt=""):
        if not state["input_reported"]:
            state["input_reported"] = True
            emit(
                "notice",
                message="input() returns an empty string in the preview. Press Run to type.",
            )
        return ""

    builtins.input = preview_input


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: softsembly_preview_bootstrap.py <source> <display_path> <container_id>")
        return 2

    source_path, display_path, container_id = sys.argv[1:4]
    _make_dpi_aware()

    with open(source_path, encoding="utf-8") as fp:
        source = fp.read()

    state = {"root": None, "input_reported": False}
    _install_patches(container_id, display_path, state)

    # Make the program see the same environment as a normal Run would.
    sys.argv = [display_path]
    if os.path.isfile(display_path):
        sys.path.insert(0, os.path.dirname(os.path.abspath(display_path)))
    globs = {"__name__": "__main__", "__file__": display_path, "__builtins__": builtins}

    try:
        code = compile(source, display_path, "exec")
        exec(code, globs)
    except SystemExit:
        return 0
    except BaseException as exc:
        _report(exc, display_path, when="startup")

    root = state["root"]
    if root is None:
        emit("no_window")
        return 0

    # Keep the window alive even if the program forgot mainloop() or crashed
    # halfway, so the student sees everything that was built up to that point.
    try:
        if root.winfo_exists():
            root.mainloop()
    except BaseException:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
