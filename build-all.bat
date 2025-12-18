@echo off
setlocal EnableDelayedExpansion

echo ==========================================
echo   ServerScout - Full Build Process
echo ==========================================
echo.

:: Set paths
set "PROJECT_DIR=%~dp0"
set "BACKEND_DIR=%PROJECT_DIR%backend"
set "ELECTRON_DIR=%PROJECT_DIR%electron"

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    pause
    exit /b 1
)

:: Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH
    pause
    exit /b 1
)

echo [1/5] Checking Python dependencies...
cd /d "%BACKEND_DIR%"
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install Python dependencies
    pause
    exit /b 1
)
echo       Done!

echo.
echo [2/5] Installing PyInstaller...
pip install pyinstaller --quiet
echo       Done!

echo.
echo [3/5] Building Python backend with PyInstaller...
echo       This may take a few minutes...
pyinstaller --noconfirm serverscout.spec
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed
    pause
    exit /b 1
)
echo       Done!

echo.
echo [4/5] Installing Electron dependencies...
cd /d "%ELECTRON_DIR%"
call npm install
if errorlevel 1 (
    echo [ERROR] Failed to install Electron dependencies
    pause
    exit /b 1
)
echo       Done!

echo.
echo [5/5] Building Electron application...
echo       Creating installer and portable versions...
call npm run build
if errorlevel 1 (
    echo [ERROR] Electron build failed
    pause
    exit /b 1
)

echo.
echo ==========================================
echo   BUILD COMPLETE!
echo ==========================================
echo.
echo   Output files are in:
echo   %ELECTRON_DIR%\dist
echo.
echo   - ServerScout Setup x.x.x.exe  (Installer)
echo   - ServerScout-Portable-x.x.x.exe (Portable)
echo.
pause
