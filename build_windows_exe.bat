@echo off
REM Build Windows .exe file using PyInstaller
REM This script requires PyInstaller to be installed:
REM   python -m pip install pyinstaller

echo Installing/updating PyInstaller...
python -m pip install pyinstaller --quiet

echo Building Windows executable...
pyinstaller --onefile --windowed --name ALAg --icon=icon.ico 2>nul || pyinstaller --onefile --windowed --name ALAg alag_app.py

echo.
echo Build complete!
echo The executable is located at: dist\ALAg.exe
echo.
pause
