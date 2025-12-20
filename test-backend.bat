@echo off
echo ========================================
echo Testing Backend Executable
echo ========================================
echo.

if not exist "backend\dist\serverscout-backend.exe" (
    echo ERROR: Backend executable not found!
    echo Please run build-backend.bat first.
    pause
    exit /b 1
)

echo Starting backend executable...
echo.
echo This will show debug output.
echo Press Ctrl+C to stop.
echo.

cd backend\dist
serverscout-backend.exe

pause

