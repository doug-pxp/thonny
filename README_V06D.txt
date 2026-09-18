Softsembly v0.6d — Stability + DPI Scaling Patch

Fixes:
- Language-server crashes no longer break unrelated UI actions.
- Dead BasedPyright proxies are invalidated globally.
- Softsembly automatically retries unexpected language-server exits (with bounded backoff).
- LSP requests/notifications gracefully skip while language services are unavailable.
- Toolbar, editor, file handling, settings and other UI remain usable if BasedPyright is down.
- Fresh Windows installs now use automatic DPI-aware scaling.
- Existing Softsembly installs using the old 1.25 default are migrated to automatic scaling.
- Windows system DPI is used as a lower bound for Tk scaling on HiDPI/laptop displays.

Tested:
- Python syntax compilation passed for modified modules.

After applying to source, test with the development launcher first. Then rebuild the Windows installer to test the packaged customer experience.
