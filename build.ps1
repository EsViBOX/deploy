<#
Automated build for deploy.exe
Requires: uv, PyInstaller, Python 3.13
#>

$ErrorActionPreference = "Stop"

Write-Host "Cleaning previous build"
Remove-Item -Recurse -Force dist,build -ErrorAction SilentlyContinue

Write-Host "Syncing dependencies"
uv sync

Write-Host "Building one-file console app"
python -m PyInstaller -n deploy.exe --onefile --distpath dist --workpath build --clean src\deploy_simple\main.py

Write-Host "Build complete -> dist\deploy.exe"