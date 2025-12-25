# ServerScout v1.2.0 - Build Instructions

## Prerequisites

1. **Python 3.8+** with pip
2. **Node.js 18+** with npm
3. **PyInstaller** (will be installed automatically)
4. **Electron Builder** (will be installed automatically)

## Quick Build (All Versions)

Run the main build script:

```batch
build-all.bat
```

This will:
1. Build the backend executable (Python → EXE)
2. Build the Electron Portable version
3. Build the Electron Installer version

## Step-by-Step Build

### Step 1: Build Backend

```batch
build-backend.bat
```

This creates: `backend\dist\serverscout-backend.exe`

### Step 2: Build Electron Application

#### Portable Version (No Installation Required)

```batch
cd electron
npm run build:portable
```

Output: `electron\dist\ServerScout-Portable-1.2.0.exe`

**Portable Version:**
- Single EXE file
- No installation needed
- Can be run from USB drive
- All files embedded in the executable
- Data stored in user's AppData folder

#### Installer Version

```batch
cd electron
npm run build:win
```

Output: `electron\dist\ServerScout-Setup-1.2.0.exe`

**Installer Version:**
- Standard Windows installer
- Creates Start Menu shortcuts
- Creates Desktop shortcut
- Can be uninstalled via Control Panel

## Output Files

After building, you'll find:

- **Portable**: `electron\dist\ServerScout-Portable-1.2.0.exe`
- **Installer**: `electron\dist\ServerScout-Setup-1.2.0.exe`

## File Structure (Portable)

The portable EXE contains:
- Electron runtime
- Frontend files (HTML, CSS, JS)
- Backend executable (`serverscout-backend.exe`)
- All dependencies

When run, it extracts to a temporary location and runs from there.

## Troubleshooting

### Backend Build Fails

- Ensure all Python dependencies are installed: `pip install -r backend/requirements.txt`
- Install PyInstaller: `pip install pyinstaller`

### Electron Build Fails

- Ensure Node.js dependencies are installed: `cd electron && npm install`
- Check that backend executable exists: `backend\dist\serverscout-backend.exe`

### Icon Missing Warning

If you see icon warnings, you can:
- Add `icon.ico` to `electron\` folder (256x256 recommended)
- Or remove the `icon` line from `package.json`

## Version Information

Current Version: **1.2.1**

To update version, edit:
- `electron\package.json` → `"version": "1.2.1"`
- `build-all.bat` → Update version references








