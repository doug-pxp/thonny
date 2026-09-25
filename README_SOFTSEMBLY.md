# Softsembly (ProgrammingXP fork of Thonny)

Beginner-first Python IDE. See `SOFTSEMBLY_CHANGELOG.md` for what differs from
upstream Thonny, and `packaging/windows/README_SOFTSEMBLY_BUILD.txt` to build the
Windows installer.

## Run from source (Windows, PowerShell)

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e . -r packaging\requirements-softsembly.txt
# Optional, if you have the sibling checkout that uv.lock expects:
.\.venv\Scripts\python.exe -m pip install ..\minny
.\.venv\Scripts\python.exe -m thonny
```

`python -m thonny --version` should print `Softsembly 0.7.0 (Thonny ...)`.

## Where Softsembly-specific code lives

| What | Where |
|---|---|
| Name, version, palette | `thonny/softsembly.py` |
| Dark UI + syntax theme | `thonny/plugins/softsembly_theme.py` |
| Defaults (theme, backend) | `thonny/defaults.ini` |
| First-run window | `thonny/first_run.py` |
| Language-server recovery | `thonny/workbench.py` ("Language servers" section), `thonny/lsp_proxy.py` |
| BasedPyright discovery | `thonny/plugins/basedpyright.py` |
| Installer | `packaging/windows/` |

Logs: `%APPDATA%\Softsembly\frontend.log` (the settings folder is
`%APPDATA%\Softsembly`).
