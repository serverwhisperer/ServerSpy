@echo off
echo ========================================
echo Removing build files from Git history
echo ========================================
echo.
echo WARNING: This will rewrite git history!
echo Make sure you have a backup!
echo.
pause

REM Remove build files from git history
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch electron/dist/ServerScout-Portable-1.2.0.exe electron/dist/ServerScout-Setup-1.2.0.exe" --prune-empty --tag-name-filter cat -- --all

echo.
echo ========================================
echo History cleaned!
echo ========================================
echo.
echo Now you can push:
echo   git push origin main --force
echo.
echo WARNING: Force push will overwrite remote history!
echo.
pause
