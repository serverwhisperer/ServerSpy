@echo off
echo ==========================================
echo   ServerScout - Backend Build (PyInstaller)
echo ==========================================
echo.

cd /d "%~dp0"

echo [1/3] Installing dependencies...
pip install -r requirements.txt --quiet
pip install pyinstaller --quiet
echo       Done!

echo.
echo [2/3] Cleaning previous build...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
echo       Done!

echo.
echo [3/3] Building with PyInstaller...
echo       This may take a few minutes...
pyinstaller --noconfirm serverscout.spec
if errorlevel 1 (
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo ==========================================
echo   Build Complete!
echo ==========================================
echo.
echo   Output: %~dp0dist\serverscout-backend
echo.
echo   To test, run: dist\serverscout-backend\serverscout-backend.exe
echo.
pause


