@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Could not find .venv in this Softsembly repo.
  echo Run this file from the root of your existing Softsembly checkout.
  pause
  exit /b 1
)

rem Preserve the development runtime exactly as an activated venv would.
rem This lets Softsembly discover bundled dev tools such as basedpyright-langserver.
set "PATH=%CD%\.venv\Scripts;%PATH%"
set "VIRTUAL_ENV=%CD%\.venv"

set "CUSTOMER_PROFILE=%CD%\.softsembly_customer_preview"
if exist "%CUSTOMER_PROFILE%" rmdir /s /q "%CUSTOMER_PROFILE%"
mkdir "%CUSTOMER_PROFILE%"
set "THONNY_USER_DIR=%CUSTOMER_PROFILE%"

echo Starting Softsembly as a brand-new customer...
".venv\Scripts\python.exe" -m thonny

endlocal
