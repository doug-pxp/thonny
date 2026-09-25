SOFTSEMBLY — WINDOWS INSTALLER BUILD
====================================

FAST PATH
---------
From the repository root, double-click:

    packaging\windows\BUILD_WINDOWS_INSTALLER.bat

The script will:
1. Read the version from thonny\softsembly.py (APP_VERSION).
2. Find your Python 3.14 development installation.
3. Install Inno Setup 6 with winget if needed.
4. Copy Python into a private Softsembly runtime.
5. Install Thonny's bundle requirements plus packaging\requirements-softsembly.txt
   (basedpyright, ruff, tkinterdnd2), and ..\minny if that checkout exists.
6. Install the CURRENT LOCAL Softsembly source tree.
7. Smoke-test the packaged runtime.
8. Create a Windows installer.

OUTPUT
------
    packaging\windows\dist\Softsembly-Setup-<version>-x64.exe

RELEASING A NEW VERSION
-----------------------
Change APP_VERSION in thonny\softsembly.py and add an entry to
SOFTSEMBLY_CHANGELOG.md. Nothing else needs to be edited.

IMPORTANT
---------
Python is required only on the developer machine to BUILD the installer.
The customer installer contains its own private Python runtime.

The installer is unsigned. Windows SmartScreen may warn when testing a
downloaded copy. Code signing is a later release-hardening step.

CUSTOM PYTHON LOCATION
----------------------
If Python 3.14 is somewhere unusual, set this before building:

    $env:SOFTSEMBLY_PYTHON_HOME = 'C:\path\to\Python314'

Then run BUILD_WINDOWS_INSTALLER.bat.
