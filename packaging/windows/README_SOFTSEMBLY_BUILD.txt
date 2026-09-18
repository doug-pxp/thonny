SOFTSEMBLY v0.5 — WINDOWS INSTALLER BUILD
=========================================

FAST PATH
---------
From the repository root, double-click:

    packaging\windows\BUILD_WINDOWS_INSTALLER.bat

The script will:
1. Find your Python 3.14 development installation.
2. Install Inno Setup 6 with winget if needed.
3. Copy Python into a private Softsembly runtime.
4. Install Softsembly's dependencies into that private runtime.
5. Install the CURRENT LOCAL Softsembly source tree.
6. Verify the packaged runtime and BasedPyright.
7. Create a Windows installer.

OUTPUT
------
    packaging\windows\dist\Softsembly-Setup-0.5.0-x64.exe

IMPORTANT
---------
Python is required only on the developer machine to BUILD this v0.5 installer.
The customer installer contains its own private Python runtime.

v0.5 is intentionally unsigned. Windows SmartScreen may warn when testing a downloaded copy.
Code signing is a later release-hardening step.

CUSTOM PYTHON LOCATION
----------------------
If Python 3.14 is somewhere unusual, set this before building:

    $env:SOFTSEMBLY_PYTHON_HOME = 'C:\path\to\Python314'

Then run BUILD_WINDOWS_INSTALLER.bat.
