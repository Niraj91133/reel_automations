@echo off
title Stop Background Automation
echo ========================================================
echo   STOPPING STARTUP ROAD BACKGROUND AUTOMATION
echo ========================================================
echo.
echo Terminating running python controller tasks...
taskkill /F /FI "WINDOWTITLE eq Startup Road*" /T 2>nul
taskkill /F /IM python.exe /FI "MODULES eq telegram_controller.py" 2>nul
wmic process where "CommandLine like '%%telegram_controller.py%%'" call terminate 2>nul

echo.
echo Background controller stopped successfully.
echo.
pause
