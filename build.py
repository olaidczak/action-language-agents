#!/usr/bin/env python3
"""
Cross-platform build script for Action Language with Agents
Works on Windows, macOS, and Linux
"""

import subprocess
import sys
import os
from pathlib import Path


def main():
    print("=" * 60)
    print("Action Language with Agents - Build Executable")
    print("=" * 60)
    print()

    # Detect platform
    platform = sys.platform
    if platform == "win32":
        print("Platform: Windows")
        output_name = "ALAg.exe"
        output_path = Path("dist") / output_name
    elif platform == "darwin":
        print("Platform: macOS")
        output_name = "ALAg.app"
        output_path = Path("dist") / output_name
    else:
        print("Platform: Linux")
        output_name = "ALAg"
        output_path = Path("dist") / output_name
    
    print()

    # Step 1: Install PyInstaller
    print("Step 1: Installing PyInstaller...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "pyinstaller", "-q"],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            print("✓ PyInstaller installed successfully")
        else:
            print("✗ Failed to install PyInstaller")
            print(result.stderr)
            return 1
    except Exception as e:
        print(f"✗ Error installing PyInstaller: {e}")
        return 1

    print()

    # Step 2: Build executable
    print("Step 2: Building executable...")
    try:
        cmd = [
            sys.executable, "-m", "pyinstaller",
            "--onefile",
            "--windowed",
            "--name", "ALAg",
            "alag_app.py"
        ]
        
        # Add icon if it exists
        if Path("icon.ico").exists():
            cmd.extend(["--icon", "icon.ico"])
            print("  → Using custom icon (icon.ico)")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✓ Build completed successfully")
        else:
            print("✗ Build failed")
            print(result.stderr)
            return 1
    except Exception as e:
        print(f"✗ Error building executable: {e}")
        return 1

    print()
    print("=" * 60)
    print("Build Summary")
    print("=" * 60)
    print(f"Output: {output_path.absolute()}")
    print()

    if platform == "win32":
        print("To run the application:")
        print(f"  Double-click {output_path}")
        print(f"  Or from command line: {output_path}")
    elif platform == "darwin":
        print("To run the application:")
        print(f"  open {output_path}")
        print(f"  Or double-click {output_path} in Finder")
        print()
        print("To create an Applications alias:")
        print(f"  ln -s \"$(pwd)/{output_path}\" ~/Applications/ALAg.app")
    else:
        print("To run the application:")
        print(f"  ./{output_path}")
    
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
