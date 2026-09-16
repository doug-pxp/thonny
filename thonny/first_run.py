import os.path
import tkinter as tk
import tkinter.font as tk_font
from logging import getLogger
from tkinter import ttk

from thonny import is_portable, languages, ui_utils

logger = getLogger(__name__)

STD_MODE_TEXT = "Regular (recommended)"
SIMPLE_MODE_TEXT = "Simplified"
RPI_MODE_TEXT = "Simplified, with Raspberry Pi theme and line-based debugger"


class FirstRunWindow(tk.Tk):
    def __init__(self, configuration_manager):
        logger.info("Creating FirstRunWindow")
        super().__init__(className="Thonny")
        style = ttk.Style()
        # Native Windows themes ignore several ttk foreground/background settings,
        # which made the dark first-run form render light controls with light text.
        # Clam is cross-platform and consistently honors our Softsembly palette.
        style.theme_use("clam")

        # Keep the very first launch visually consistent with Softsembly's dark product theme.
        background = "#171719"
        panel = "#1E1E22"
        border = "#303038"
        primary_text = "#F5F5F6"
        secondary_text = "#A6A6AF"
        yellow = "#FFE29A"
        green = "#79F56B"

        # Make first-launch controls readable even before the main workbench has
        # initialized its UI scaling settings.
        for font_name in ["TkDefaultFont", "TkTextFont"]:
            try:
                font = tk_font.nametofont(font_name)
                if int(font.cget("size")) > 0 and int(font.cget("size")) < 11:
                    font.configure(size=11)
            except Exception:
                pass

        self.configure(background=background)
        style.configure("TFrame", background=background)
        style.configure("TLabel", background=background, foreground=primary_text)
        style.configure(
            "Softsembly.TButton",
            background=yellow,
            foreground=background,
            bordercolor=yellow,
            focuscolor=yellow,
            padding=(12, 6),
        )
        style.map(
            "Softsembly.TButton",
            background=[("active", "#F4D378"), ("pressed", green), ("disabled", border)],
            foreground=[("disabled", secondary_text)],
        )
        style.configure(
            "Softsembly.TCombobox",
            fieldbackground=panel,
            background=panel,
            foreground=primary_text,
            arrowcolor=yellow,
            bordercolor=border,
            lightcolor=border,
            darkcolor=border,
            padding=4,
        )
        style.map(
            "Softsembly.TCombobox",
            fieldbackground=[("readonly", panel), ("disabled", panel)],
            background=[("readonly", panel)],
            foreground=[("readonly", primary_text), ("disabled", secondary_text)],
            selectbackground=[("readonly", panel)],
            selectforeground=[("readonly", primary_text)],
        )

        self.title("Welcome to Softsembly!" + "   [portable]" if is_portable() else "")
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.ok = False

        self.conf = configuration_manager

        self.main_frame = ttk.Frame(self)
        self.main_frame.grid(row=1, column=1, sticky="nsew")
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        self.main_frame.rowconfigure(1, weight=1)

        logo_file = os.path.join(os.path.dirname(__file__), "res", "thonny.png")
        self.logo = tk.PhotoImage(file=logo_file)

        logo_label = ttk.Label(self.main_frame, image=self.logo)
        logo_label.grid(row=1, rowspan=3, column=1, sticky="nsew")

        self.padx = ui_utils.ems_to_pixels(3)
        self.pady = ui_utils.ems_to_pixels(3)

        self.language_variable = ui_utils.create_string_var(
            languages.BASE_LANGUAGE_NAME, self.on_change_language
        )
        self.add_combo(
            1, "Language:", self.language_variable, list(languages.LANGUAGES_DICT.values())
        )

        # Softsembly has one beginner-friendly default experience. Advanced
        # configuration remains available later under Tools -> Options.
        self.mode_variable = tk.StringVar(value=STD_MODE_TEXT)

        ready_label = ttk.Label(
            self.main_frame,
            text="Python is ready. No setup required.",
            foreground=green,
        )
        ready_label.grid(
            row=2, column=2, columnspan=2,
            padx=(0, self.padx), pady=(self.pady * 0.5, 0), sticky="w"
        )

        ok_button = ttk.Button(self.main_frame, text="Let's go!", command=self.on_ok, style="Softsembly.TButton")
        ok_button.grid(
            row=3, column=3, padx=(0, self.padx), pady=(self.pady * 0.7, self.pady), sticky="se"
        )

        self.center()

    def on_change_language(self):
        print(self.language_variable.get())

    def add_combo(self, row, label_text, variable, values):
        pady = ui_utils.ems_to_pixels(0.7)
        label = ttk.Label(self.main_frame, text=label_text)
        label.grid(row=row, column=2, sticky="sw", pady=(pady, 0))
        assert isinstance(variable, tk.Variable)
        combobox = ttk.Combobox(
            self.main_frame,
            exportselection=False,
            textvariable=variable,
            state="readonly",
            height=15,
            # Actual length of longest value creates too wide combobox
            width=40 if ui_utils.running_on_mac_os() else 45,
            values=values,
            style="Softsembly.TCombobox",
        )
        combobox.grid(
            row=row,
            column=3,
            padx=(ui_utils.ems_to_pixels(1), self.padx),
            sticky="sw",
            pady=(pady, 0),
        )

    def center(self):
        # https://stackoverflow.com/questions/3352918/how-to-center-a-window-on-the-screen-in-tkinter
        self.eval("tk::PlaceWindow . center")

    def on_ok(self):
        if self.mode_variable.get() in [SIMPLE_MODE_TEXT, RPI_MODE_TEXT]:
            self.conf.set_option("general.ui_mode", "simple")
            if self.mode_variable.get() == RPI_MODE_TEXT:
                self.conf.set_option("debugger.preferred_debugger", "faster")
                self.conf.set_option("view.ui_theme", "Raspberry Pi")

        self.conf.set_option(
            "general.language", languages.get_language_code_by_name(self.language_variable.get())
        )

        self.conf.save()

        self.ok = True
        self.destroy()
