Softsembly v0.6f — Responsive + Language-Service Portability Fix

This is a combined patch. It contains the v0.6d language-server lifecycle fixes,
the v0.6e responsive display/DPI fixes, and the runtime-safe BasedPyright resolver.

Key fixes:
- Dead language servers are invalidated globally instead of remaining registered.
- Language services retry safely in the background without breaking unrelated UI.
- Windows uses DPI-aware scaling and responsive screen/work-area based layout.
- Saved window geometry is clamped when moving between different screen sizes.
- Auto UI scaling remains the default and manual overrides remain available.
- BasedPyright discovery no longer requires venv activation or PATH modification.
- Dev venvs resolve .venv/Scripts/basedpyright-langserver.exe correctly.
- Packaged Windows runtimes resolve their private Scripts directory correctly.
- macOS/Linux resolve the private bin directory correctly.
- Final fallback runs BasedPyright as a module with Softsembly's own Python runtime.

Apply the contents of this ZIP over the Softsembly repository root.

You should now be able to launch development Softsembly directly with:

    .\.venv\Scripts\python.exe -m thonny

without activating the venv or manually editing PATH.
