"""Softsembly product identity and palette.

Single source of truth for everything that makes this fork "Softsembly" rather
than stock Thonny. Keep this module free of tkinter / workbench imports so any
part of the app (first-run window, theme plugin, about dialog, build scripts)
can import it cheaply and early.
"""

APP_NAME = "Softsembly"
APP_VERSION = "0.7.1"
PUBLISHER = "ProgrammingXP"
UPSTREAM_NAME = "Thonny"
UPSTREAM_URL = "https://github.com/thonny/thonny"

# Product accents. ProgrammingXP is the umbrella brand; Softsembly uses
# yellow + green as its primary accents on a dark graphite foundation.
YELLOW = "#FFE29A"
YELLOW_ACTIVE = "#F4D378"
GREEN = "#79F56B"
PXP_PURPLE = "#A99BFF"
PXP_CYAN = "#62DFE8"
PXP_PINK = "#FF8098"

# Surfaces and text
BACKGROUND = "#171719"
EDITOR_BACKGROUND = "#141416"
PANEL = "#1E1E22"
ELEVATED = "#232329"
BORDER = "#303038"
PRIMARY_TEXT = "#F5F5F6"
SECONDARY_TEXT = "#A6A6AF"
DISABLED_TEXT = "#686872"
MUTED_TEXT = "#72727D"
ERROR = "#F26B6B"


def get_display_version() -> str:
    return f"{APP_NAME} {APP_VERSION}"
