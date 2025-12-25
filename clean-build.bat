@echo off
echo ========================================
echo Cleaning Previous Builds
echo ========================================
echo.

echo Cleaning Electron dist folder...
if exist "electron\dist" (
    rmdir /s /q "electron\dist"
    echo Electron dist folder cleaned.
)

echo Cleaning Backend dist folder...
if exist "backend\dist" (
    rmdir /s /q "backend\dist"
    echo Backend dist folder cleaned.
)

echo Cleaning Backend build files...
if exist "backend\build" (
    rmdir /s /q "backend\build"
    echo Backend build folder cleaned.
)

if exist "backend\serverscout-backend.spec" (
    del /q "backend\serverscout-backend.spec"
    echo Old spec file removed.
)

echo.
echo ========================================
echo Clean Complete!
echo ========================================
echo.
pause








