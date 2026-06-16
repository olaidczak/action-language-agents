# Quick Start Guide - Clean Button & Executable Building

## 1. Clean Button

### What it does
The **"Clean all"** button in the **4. Query & run** tab resets the entire application to its initial state:
- Clears all fluents, actions, and agents
- Removes all domain description statements
- Removes all observations and action occurrences
- Clears all queries
- Clears the output panel
- Sets time T back to 9

### When to use it
- After testing an example, instead of restarting the program
- To quickly start a new scenario without closing and reopening the app
- To reset if you've made experimental changes you want to discard

### How to use it
1. Open the **4. Query & run** tab
2. Click the **"Clean all"** button
3. The status bar will confirm: "All data cleared. Apply a signature to begin."
4. Go to **1. Signature** tab and apply a new signature to begin a fresh scenario

---

## 2. Building Executables

### For Windows

**Option 1: Automatic (Recommended)**
```cmd
build_windows_exe.bat
```

**Option 2: Cross-platform Python script**
```cmd
python build.py
```

Result: `dist\ALAg.exe`

### For macOS

**Option 1: Automatic (Recommended)**
```bash
chmod +x build_macos_app.sh
./build_macos_app.sh
```

**Option 2: Cross-platform Python script**
```bash
python3 build.py
```

Result: `dist/ALAg.app`

### Running the executables

**Windows:**
- Double-click `dist\ALAg.exe`
- Or: `dist\ALAg.exe`

**macOS:**
- `open dist/ALAg.app`
- Or double-click in Finder
- Or create an alias: `ln -s "$(pwd)/dist/ALAg.app" ~/Applications/ALAg.app`

---

## 3. Files Overview

### New/Updated files

| File | Purpose |
|------|---------|
| `alag_app.py` | Updated with "Clean all" button and `_clean_all()` method |
| `build_windows_exe.bat` | Windows batch script to build .exe |
| `build_macos_app.sh` | macOS shell script to build .app |
| `build.py` | Cross-platform Python build script |
| `BUILD_GUIDE.md` | Detailed build instructions and troubleshooting |

### Existing files (unchanged)
- `alag_engine.py` — Reasoning engine
- `example_tests.py` — Tests
- `README.md` — Project overview
- `USER_GUIDE.md` — User guide

---

## 4. Build Requirements

- Python 3.10+
- PyInstaller (automatically installed by build scripts)
- For macOS: May need Xcode Command Line Tools

```bash
# Optional: Pre-install PyInstaller
python -m pip install pyinstaller
```

---

## 5. Key Features of the Clean Button

✓ **No need to restart** — Clean all data and start fresh instantly  
✓ **Preserves code** — Doesn't touch the application itself  
✓ **Safe** — Just clears form fields and internal state  
✓ **Quick workflow** — Test multiple scenarios in succession  

---

## 6. Example Workflow

1. **Load Example:**
   - Go to tab "0. Examples"
   - Select an example and click "Load example + build"

2. **Modify:**
   - Go to different tabs and edit the scenario

3. **Test:**
   - Go to tab "4. Query & run"
   - Click "Build models & show trajectory"
   - Ask queries Q1 and Q2

4. **Clean & Repeat:**
   - Click "Clean all" button
   - Go to tab "1. Signature"
   - Apply a new signature
   - Create a new scenario

---

For more details, see [BUILD_GUIDE.md](BUILD_GUIDE.md) and [USER_GUIDE.md](USER_GUIDE.md).
