@echo off
REM Start ServerScout with HTTPS enabled
echo Starting ServerScout with HTTPS...
set USE_HTTPS=true
cd /d %~dp0backend
python app.py
pause




