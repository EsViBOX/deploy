#!/bin/bash
set -e

echo "Cleaning previous build"
rm -rf dist build

echo "Syncing dependencies (includes PyInstaller)"
uv sync

echo "Building one-file console app"
uv run python -m PyInstaller -n deploy --onefile --distpath dist --workpath build --clean src/deploy_simple/main.py

echo "Build complete -> dist/deploy"