"""Softsembly visual theme.

This module intentionally layers on Thonny's existing theme infrastructure instead of
replacing it. Keeping the customization in one plugin makes future upstream merges
and Softsembly iterations safer.
"""

from copy import deepcopy

from thonny import get_workbench
from thonny.plugins.base_syntax_themes import default_dark
from thonny.plugins.clean_ui_themes import clean
from thonny.softsembly import (
    BACKGROUND,
    BORDER,
    DISABLED_TEXT,
    EDITOR_BACKGROUND,
    ELEVATED,
    ERROR,
)
from thonny.softsembly import GREEN as SOFTSEMBLY_GREEN
from thonny.softsembly import (
    MUTED_TEXT,
    PANEL,
    PRIMARY_TEXT,
    PXP_CYAN,
    PXP_PINK,
    PXP_PURPLE,
    SECONDARY_TEXT,
)
from thonny.softsembly import YELLOW as SOFTSEMBLY_YELLOW


def softsembly_syntax():
    theme = deepcopy(default_dark())

    theme["TEXT"].update(
        foreground=PRIMARY_TEXT,
        insertbackground=SOFTSEMBLY_YELLOW,
        background=EDITOR_BACKGROUND,
    )
    theme["GUTTER"].update(foreground=MUTED_TEXT, background=BACKGROUND)
    theme["current_line"].update(background="#1D1D21")
    theme["sel"].update(foreground=PRIMARY_TEXT, background="#49442D")

    # PXP family colors appear primarily in syntax, while Softsembly yellow/green
    # remain the strongest product accents.
    theme["definition"].update(foreground=PRIMARY_TEXT)
    theme["builtin"].update(foreground=PXP_CYAN)
    theme["keyword"].update(foreground=PXP_PURPLE, font="BoldEditorFont")
    theme["string"].update(foreground=SOFTSEMBLY_GREEN)
    theme["string3"].update(foreground=SOFTSEMBLY_GREEN, background=None)
    theme["open_string"].update(foreground=SOFTSEMBLY_GREEN, background="#203521")
    theme["open_string3"].update(foreground=SOFTSEMBLY_GREEN, background="#203521")
    theme["number"].update(foreground=SOFTSEMBLY_YELLOW)
    theme["comment"].update(foreground=MUTED_TEXT)
    theme["welcome"].update(foreground=SOFTSEMBLY_YELLOW)
    theme["magic"].update(foreground=PXP_PINK)

    # Shell / output states
    theme["prompt"].update(foreground=SOFTSEMBLY_GREEN, font="BoldEditorFont")
    theme["stdin"].update(foreground=PXP_CYAN)
    theme["stdout"].update(foreground=PRIMARY_TEXT)
    theme["stderr"].update(foreground=ERROR)
    theme["value"].update(foreground=SOFTSEMBLY_YELLOW)
    theme["hyperlink"].update(foreground=PXP_CYAN, underline=True)

    theme["surrounding_parens"].update(foreground=SOFTSEMBLY_YELLOW, font="BoldEditorFont")
    theme["matched_name"].update(background="#30302A")
    theme["current_found"].update(foreground=BACKGROUND, background=SOFTSEMBLY_YELLOW)

    return theme


def load_plugin() -> None:
    dark_images = {"tab-close-active": "tab-close-active-dark"}

    get_workbench().add_ui_theme(
        "Softsembly Dark",
        "Enhanced Clam",
        clean(
            frame_background=BACKGROUND,
            text_background=PANEL,
            normal_detail=ELEVATED,
            high_detail="#4A452E",
            low_detail=BORDER,
            normal_foreground=SECONDARY_TEXT,
            high_foreground=PRIMARY_TEXT,
            low_foreground=DISABLED_TEXT,
        ),
        images=dark_images,
    )

    get_workbench().add_syntax_theme("Softsembly Dark", "Default Dark", softsembly_syntax)
