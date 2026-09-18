Softsembly Branding Recovery Patch

Purpose:
- Restores the Softsembly Dark UI and syntax theme
- Restores Softsembly naming/status text
- Restores the Softsembly app icon and installer icon
- Restores executable icon embedding during Windows packaging

This patch intentionally does NOT replace:
- thonny/workbench.py
- thonny/main.py
- thonny/lsp_proxy.py
- thonny/plugins/basedpyright.py
- thonny/plugins/general_config_page.py

Those files contain the newer v0.6f stability/runtime/responsive-display fixes.

After applying, test dev mode first. Then rebuild and reinstall the Windows installer for packaged icon/branding changes.
