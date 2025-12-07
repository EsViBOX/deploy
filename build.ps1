<#
Automated build for deploy.exe
Requires: uv, PyInstaller, Python 3.13
#>

$ErrorActionPreference = "Stop"

Write-Host "Cleaning previous build" -ForegroundColor Cyan
Remove-Item -Recurse -Force dist,build -ErrorAction SilentlyContinue

Write-Host "Syncing dependencies" -ForegroundColor Cyan
uv sync --link-mode=copy

Write-Host "Installing PyInstaller" -ForegroundColor Cyan
uv pip install pyinstaller

Write-Host "Building one-file console app" -ForegroundColor Cyan
python -m PyInstaller -n deploy-simple.exe --onefile --distpath dist --workpath build --clean src\deploy_simple\main.py

Write-Host "Build complete -> dist\deploy-simple.exe" -ForegroundColor Green