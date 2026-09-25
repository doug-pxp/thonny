# Softsembly changelog

Softsembly is a ProgrammingXP fork of the open-source Thonny IDE (MIT).
Upstream history is in `CHANGELOG.rst`; this file tracks only Softsembly changes.
The version number lives in one place: `thonny/softsembly.py` (`APP_VERSION`).

## 0.7.1 — Drag-and-drop fix

- Fixed "Internal Tk error: Unsupported URI scheme 'd'" when dragging a file
  from Explorer. TkDND on Windows delivers paths with forward slashes
  (`D:/dir/a.py`), and Thonny's path detection only recognizes backslash paths,
  so the drive letter was read as a URI scheme. Dropped paths are now
  normalized before opening. The drop bug was already in the code; 0.7.0 is the
  first build that bundled tkinterdnd2, so it's the first build where drops ran.
- Re-dropping a file that is already open focuses its tab instead of opening
  a duplicate.
- A file that fails to open from a drop now shows a status-bar message instead
  of an error dialog.

## 0.7.0 — Stability refactor

Language services (autocomplete, diagnostics, highlighting)
- Fixed a restart loop in packaged builds. Ruff wasn't bundled, so it crashed at
  launch, and recovery restarted *every* language server, which killed BasedPyright
  over and over (43 restarts in 40 s in testing). BasedPyright rarely finished
  starting, so installed builds had little or no autocomplete or diagnostics.
- Recovery is now per server. Only the server that crashed is restarted, others
  are untouched, and each server gets its own budget of 3 retries (500/1000/1500 ms).
  The budget is refunded only after the server has stayed up for 30 s, so a
  server that crashes right after starting can't loop forever.
- Fixed "Unknown request: textDocument/documentHighlight" (and similar) error
  popups. `get_main_language_server_proxy()` could hand BasedPyright-only
  requests to Ruff when Ruff happened to start first. It now returns only the
  main server, or nothing while that server is still starting.
- Ruff is only registered when it is installed in the running Python.
- Name highlighting, calltips and autocomplete no longer show modal error dialogs.
  Routine errors (content modified, request cancelled, unsupported method) are
  logged. Anything else goes to the status bar.
- Fixed busy loops in the stdout/stderr listener threads when a server exits
  (thousands of blank log lines, and a race that could raise "Internal error").
- A failure while handling one server message is logged and shown in the status
  bar instead of a modal "Internal error" dialog.
- Refactor: language-server startup is split into `_create_ls_proxy()` and
  `_build_ls_initialize_params()` instead of one 100-line method.

UI and branding
- Fixed the first-run window title being blank (operator-precedence bug).
- The Windows 1.25 → auto scaling migration now runs once per profile. Before,
  it ran on every launch, so a user could never keep 1.25 on purpose.
- The About dialog and `--version` show the Softsembly version (0.7.0) plus the
  underlying Thonny version. They used to show "Softsembly 6.0.0.dev1".
- New `thonny/softsembly.py`: app name, version, publisher and palette in one
  module. The theme plugin and first-run window import from it instead of
  duplicating hex values.

Packaging
- New `packaging/requirements-softsembly.txt` (basedpyright, ruff, tkinterdnd2).
  Drag-and-drop from Explorer now actually works in installed builds.
- The build script reads the version from `thonny/softsembly.py`, installs the
  sibling `..\minny` checkout when present (needed for micro:bit / Pico plugins),
  and its smoke test also checks ruff and tkinterdnd2.

## 0.6f — Responsive + language-service portability
- DPI-aware scaling on Windows (per-monitor-v2 with fallbacks), screen/work-area
  based default window size, saved geometry clamped to the current monitor.
- BasedPyright found without venv activation or PATH changes (venv Scripts,
  bundled runtime, bin dir, then `python -m basedpyright.langserver`).

## 0.6d — Stability + DPI scaling
- Language-server crashes no longer break unrelated UI; dead proxies invalidated;
  bounded automatic retries; LSP traffic skipped while unavailable.
- Existing installs on the old 1.25 default migrated to automatic scaling.

## Branding recovery patch
- Restored Softsembly Dark UI/syntax theme, naming, app and installer icons, and
  icon embedding in the packaged executable.

## 0.5 — Windows installer packaging
- One-command installer build with a private Python 3.14 runtime, local source
  install, Softsembly.exe launcher, shortcuts and file associations.
- Separate Softsembly settings profile. Unsigned (code signing comes later).
