@echo off
echo ==========================================
echo   ServerScout - Build Script
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

REM Navigate to backend directory
cd /d "%~dp0backend"

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Building executable...
echo.

REM Build with PyInstaller
pyinstaller --onedir --noconsole ^
    --add-data "../frontend;frontend" ^
    --add-data "../data;data" ^
    --add-data "../exports;exports" ^
    --name=ServerScout ^
    --icon=NONE ^
    app.py

if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

REM Copy start script to dist folder
echo @echo off > dist\ServerScout\start.bat
echo cd /d "%%~dp0" >> dist\ServerScout\start.bat
echo echo Starting ServerScout... >> dist\ServerScout\start.bat
echo start "" "http://localhost:5000" >> dist\ServerScout\start.bat
echo ServerScout.exe >> dist\ServerScout\start.bat

echo.
echo ==========================================
echo   Build completed successfully!
echo ==========================================
echo.
echo Output location: %~dp0backend\dist\ServerScout
echo.
echo To run the application:
echo   1. Navigate to dist\ServerScout folder
echo   2. Run start.bat
echo.
pause

