@echo off
echo ========================================
echo Building ServerScout Backend (v1.2.0)
echo ========================================
echo.

cd backend

echo Installing PyInstaller if needed...
pip install pyinstaller --quiet

echo.
echo Building backend executable...
pyinstaller build-backend.spec --clean --noconfirm

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Backend build successful!
    echo Executable: backend\dist\serverscout-backend.exe
    echo ========================================
) else (
    echo.
    echo ========================================
    echo Backend build FAILED!
    echo ========================================
    pause
    exit /b 1
)

cd ..
pause








