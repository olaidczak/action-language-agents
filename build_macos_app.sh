#!/bin/bash
# Build macOS .app bundle using PyInstaller
# This script requires PyInstaller to be installed:
#   python -m pip install pyinstaller

echo "Installing/updating PyInstaller..."
python3 -m pip install pyinstaller --quiet

echo "Building macOS application..."
pyinstaller --onefile --windowed --name ALAg alag_app.py

echo ""
echo "Build complete!"
echo "The application is located at: dist/ALAg.app"
echo ""
echo "To run the app:"
echo "  open dist/ALAg.app"
echo ""
