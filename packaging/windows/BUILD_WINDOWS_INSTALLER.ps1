$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$BuildDir = Join-Path $ScriptDir 'build'
$DistDir = Join-Path $ScriptDir 'dist'
$Version = '0.5.0'

Write-Host ''
Write-Host '============================================' -ForegroundColor Yellow
Write-Host ' Softsembly v0.5 Windows Installer Builder' -ForegroundColor Yellow
Write-Host '============================================' -ForegroundColor Yellow
Write-Host ''

$pythonCandidates = @()
if ($env:SOFTSEMBLY_PYTHON_HOME) { $pythonCandidates += $env:SOFTSEMBLY_PYTHON_HOME }
$pythonCandidates += @(
    'C:\Python314',
    (Join-Path $env:ProgramFiles 'Python314'),
    (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python314')
)

$PythonHome = $null
foreach ($candidate in $pythonCandidates) {
    if ($candidate -and (Test-Path (Join-Path $candidate 'python.exe'))) {
        $PythonHome = $candidate
        break
    }
}

if (-not $PythonHome) {
    throw @'
Python 3.14 was not found in a supported location.
Your development machine currently needs Python 3.14 only to BUILD Softsembly.
Students will NOT need Python installed.

Expected locations include:
  C:\Python314
  C:\Program Files\Python314
  %LOCALAPPDATA%\Programs\Python\Python314

Or set SOFTSEMBLY_PYTHON_HOME to your Python 3.14 folder.
'@
}

Write-Host "Using build Python: $PythonHome" -ForegroundColor Cyan

$isccCandidates = @(
    (Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe'),
    (Join-Path $env:ProgramFiles 'Inno Setup 6\ISCC.exe'),
    (Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe')
)
$iscc = $null
foreach ($candidate in $isccCandidates) {
    if ($candidate -and (Test-Path $candidate)) { $iscc = $candidate; break }
}

if (-not $iscc) {
    Write-Host 'Inno Setup 6 is not installed. Attempting installation with winget...' -ForegroundColor Yellow
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw 'Inno Setup 6 is required and winget is unavailable. Install Inno Setup 6, then run this script again.'
    }
    winget install --id JRSoftware.InnoSetup -e --accept-package-agreements --accept-source-agreements
    foreach ($candidate in $isccCandidates) {
        if ($candidate -and (Test-Path $candidate)) { $iscc = $candidate; break }
    }
    if (-not $iscc) { throw 'Inno Setup installation completed but ISCC.exe could not be found. Reopen PowerShell and run the build again.' }
}

Write-Host "Using Inno Setup: $iscc" -ForegroundColor Cyan

if (Test-Path $BuildDir) { Remove-Item $BuildDir -Recurse -Force }
if (Test-Path $DistDir) { Remove-Item $DistDir -Recurse -Force }
New-Item -ItemType Directory -Path $BuildDir | Out-Null
New-Item -ItemType Directory -Path $DistDir | Out-Null

Write-Host '[1/6] Copying private Python runtime...' -ForegroundColor Green
& robocopy $PythonHome $BuildDir /E /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -gt 7) { throw "robocopy failed with exit code $LASTEXITCODE" }

$Runner = Join-Path $ScriptDir 'ThonnyRunner314\x64\Release\thonny.exe'
if (-not (Test-Path $Runner)) { throw "Bundled GUI runner was not found: $Runner" }
Copy-Item $Runner (Join-Path $BuildDir 'softsembly.exe') -Force
Copy-Item (Join-Path $ScriptDir 'thonny_python.ini') $BuildDir -Force

$BundledPython = Join-Path $BuildDir 'python.exe'

# Do not accidentally ship unrelated packages from the developer's global Python.
$BundledSitePackages = Join-Path $BuildDir 'Lib\site-packages'
$BundledScripts = Join-Path $BuildDir 'Scripts'
if (Test-Path $BundledSitePackages) { Remove-Item $BundledSitePackages -Recurse -Force }
if (Test-Path $BundledScripts) { Remove-Item $BundledScripts -Recurse -Force }

Write-Host '[2/6] Installing runtime dependencies...' -ForegroundColor Green
& $BundledPython -s -m ensurepip --upgrade
if ($LASTEXITCODE) { throw 'Could not bootstrap pip in bundled Python.' }
& $BundledPython -s -m pip install --disable-pip-version-check --no-warn-script-location --upgrade pip wheel
if ($LASTEXITCODE) { throw 'Could not prepare pip in bundled Python.' }
& $BundledPython -s -m pip install --disable-pip-version-check --no-warn-script-location --no-cache-dir -r (Join-Path $Root 'packaging\requirements-regular-bundle.txt')
if ($LASTEXITCODE) { throw 'Could not install Softsembly runtime dependencies.' }
& $BundledPython -s -m pip install --disable-pip-version-check --no-warn-script-location --no-cache-dir basedpyright
if ($LASTEXITCODE) { throw 'Could not install BasedPyright.' }

Write-Host '[3/6] Installing THIS Softsembly source tree...' -ForegroundColor Green
& $BundledPython -s -m pip install --disable-pip-version-check --no-warn-script-location --no-cache-dir $Root
if ($LASTEXITCODE) { throw 'Could not install local Softsembly source.' }

Write-Host '[4/6] Adding licenses and Softsembly metadata...' -ForegroundColor Green
Copy-Item (Join-Path $Root 'LICENSE.txt') $BuildDir -Force
Copy-Item (Join-Path $Root 'THIRD_PARTY_NOTICES.txt') $BuildDir -Force
Copy-Item (Join-Path $Root 'SOFTSEMBLY_VERSION.txt') $BuildDir -Force
Copy-Item (Join-Path $Root 'SOFTSEMBLY_REVISION.txt') $BuildDir -Force
if (Test-Path (Join-Path $Root 'licenses')) {
    Copy-Item (Join-Path $Root 'licenses') (Join-Path $BuildDir 'licenses') -Recurse -Force
}

Write-Host '[5/6] Running bundled-runtime smoke test...' -ForegroundColor Green
& $BundledPython -s -c "import thonny, basedpyright; print('Softsembly runtime OK'); print(thonny.__file__)"
if ($LASTEXITCODE) { throw 'Bundled runtime smoke test failed.' }
$bp = Join-Path $BuildDir 'Scripts\basedpyright-langserver.exe'
if (-not (Test-Path $bp)) { throw "BasedPyright launcher missing from bundled runtime: $bp" }

Write-Host '[6/6] Building Windows installer...' -ForegroundColor Green
$Iss = Join-Path $ScriptDir 'softsembly_inno_setup.iss'
& $iscc "/DAppVer=$Version" "/DSourceFolder=$BuildDir" $Iss
if ($LASTEXITCODE) { throw 'Inno Setup failed to build the installer.' }

$Installer = Join-Path $DistDir "Softsembly-Setup-$Version-x64.exe"
if (-not (Test-Path $Installer)) { throw "Build finished, but installer was not found: $Installer" }

Write-Host ''
Write-Host 'SUCCESS' -ForegroundColor Green
Write-Host "Installer: $Installer" -ForegroundColor White
Write-Host ''
Write-Host 'Next test:' -ForegroundColor Yellow
Write-Host '  1. Double-click the installer.'
Write-Host '  2. Install Softsembly.'
Write-Host '  3. Launch it from the Start menu.'
Write-Host '  4. Create calculator.py.'
Write-Host '  5. Test Run, input(), Save, close, and reopen.'
Write-Host ''
Write-Host 'NOTE: v0.5 is unsigned, so Windows SmartScreen may warn during testing.' -ForegroundColor Yellow
