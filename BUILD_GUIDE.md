# Building Executables for Windows and macOS

This guide explains how to build standalone executables for both Windows and macOS using PyInstaller.

## Requirements

- Python 3.10 or later
- PyInstaller (will be installed automatically by the build scripts)

## Building for Windows

### Method 1: Using the batch file (Recommended)

1. Open Command Prompt or PowerShell
2. Navigate to the project directory
3. Run:
   ```cmd
   build_windows_exe.bat
   ```

The script will:
- Install PyInstaller if not already installed
- Build the executable
- Place the result in `dist\ALAg.exe`

### Method 2: Manual build

```cmd
python -m pip install pyinstaller
pyinstaller --onefile --windowed --name ALAg alag_app.py
```

The executable will be created at `dist\ALAg.exe`.

### Running the Windows executable

Double-click `dist\ALAg.exe` to launch the application, or run from command line:
```cmd
dist\ALAg.exe
```

---

## Building for macOS

### Method 1: Using the shell script (Recommended)

1. Open Terminal
2. Navigate to the project directory
3. Make the script executable (first time only):
   ```bash
   chmod +x build_macos_app.sh
   ```
4. Run:
   ```bash
   ./build_macos_app.sh
   ```

The script will:
- Install PyInstaller if not already installed
- Build the application
- Place the result in `dist/ALAg.app`

### Method 2: Manual build

```bash
python3 -m pip install pyinstaller
pyinstaller --onefile --windowed --name ALAg alag_app.py
```

The application will be created at `dist/ALAg.app`.

### Running the macOS application

#### Option 1: From Finder
Navigate to the `dist` folder and double-click `ALAg.app`

#### Option 2: From Terminal
```bash
open dist/ALAg.app
```

#### Option 3: Create an alias (optional)
To make it easier to launch, create a symlink in your Applications folder:
```bash
ln -s "$(pwd)/dist/ALAg.app" ~/Applications/ALAg.app
```

---

## Creating a Python cross-platform build script

If you want a single Python script that works on both Windows and macOS, use the following:

```python
# build.py
import subprocess
import sys
import os

def build_executable():
    """Build executable for current platform."""
    
    # Install PyInstaller
    print("Installing/updating PyInstaller...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller", "--quiet"])
    
    # Build executable
    print("Building executable...")
    subprocess.run([
        sys.executable, "-m", "pyinstaller",
        "--onefile",
        "--windowed",
        "--name", "ALAg",
        "alag_app.py"
    ])
    
    # Print result location
    if sys.platform == "win32":
        output = "dist\\ALAg.exe"
        print(f"\nBuild complete! Executable at: {output}")
    elif sys.platform == "darwin":
        output = "dist/ALAg.app"
        print(f"\nBuild complete! Application at: {output}")
        print(f"Run with: open {output}")
    else:
        output = "dist/ALAg"
        print(f"\nBuild complete! Executable at: {output}")

if __name__ == "__main__":
    build_executable()
```

Run it with:
```bash
python build.py
```

---

## Troubleshooting

### Issue: "pyinstaller: command not found"
**Solution:** Install PyInstaller manually:
```bash
python -m pip install pyinstaller
```

### Issue: Icon not found (Windows)
If you have an `icon.ico` file, the Windows batch script will attempt to use it. If not found, it will build without a custom icon. To add an icon:
1. Place your 256x256 `.ico` file in the project directory
2. Name it `icon.ico`
3. Run the build script again

### Issue: "Permission denied" (macOS)
Make the shell script executable:
```bash
chmod +x build_macos_app.sh
```

### Issue: macOS warns "App is damaged" or "from an unidentified developer"
This is normal for unsigned apps on macOS. To run the app:
1. Right-click `ALAg.app` → Open
2. Or use Terminal: `open -a ALAg`

To permanently allow it, run:
```bash
xattr -d com.apple.quarantine dist/ALAg.app
```

---

## Advanced options

For more PyInstaller options, see the [PyInstaller documentation](https://pyinstaller.org/en/stable/usage.html).

Common options:
- `--icon=path/to/icon.ico` — Add a custom icon
- `--add-data src:dest` — Bundle additional data files
- `--hidden-import=module` — Include modules not detected automatically
- `-y` or `--noconfirm` — Don't ask for confirmation

Example:
```bash
pyinstaller --onefile --windowed --icon=icon.ico --name ALAg alag_app.py
```
