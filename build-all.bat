@echo off
echo ========================================
echo Building ServerScout v1.2.0
echo ========================================
echo.

REM Step 0: Clean previous builds
echo [0/4] Cleaning previous builds...
call clean-build.bat
if %ERRORLEVEL% NEQ 0 (
    echo Clean failed! Continuing anyway...
)

REM Step 1: Build Backend
echo.
echo [1/4] Building backend executable...
call build-backend.bat
if %ERRORLEVEL% NEQ 0 (
    echo Backend build failed! Aborting.
    pause
    exit /b 1
)

REM Step 2: Verify backend exe exists
echo.
echo [2/4] Verifying backend executable...
if not exist "backend\dist\serverscout-backend.exe" (
    echo ERROR: Backend executable not found!
    pause
    exit /b 1
)
echo Backend executable verified.

REM Step 3: Build Electron (Portable + Installer)
echo.
echo [3/4] Building Electron application...
cd electron

echo Installing dependencies if needed...
call npm install --silent

echo.
echo Building Portable version (v1.2.0)...
call npm run build:portable
if %ERRORLEVEL% NEQ 0 (
    echo Portable build failed!
    cd ..
    pause
    exit /b 1
)

echo.
echo Building Installer version (v1.2.0)...
call npm run build:win
if %ERRORLEVEL% NEQ 0 (
    echo Installer build failed!
    cd ..
    pause
    exit /b 1
)

cd ..

cd ..

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Output files in electron\dist\:
echo   - Portable: ServerScout-Portable-1.2.0.exe
echo   - Installer: ServerScout-Setup-1.2.0.exe
echo.
echo Note: win-unpacked folder is intermediate build output.
echo       You can delete it - only the .exe files are needed.
echo.
pause




