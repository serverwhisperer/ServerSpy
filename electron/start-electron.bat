@echo off
echo ==========================================
echo   ServerScout - Electron Desktop App
echo ==========================================
echo.

cd /d "%~dp0"

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing Electron dependencies...
    call npm install
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        echo Make sure Node.js is installed from https://nodejs.org
        pause
        exit /b 1
    )
)

echo Starting ServerScout...
call npm start

