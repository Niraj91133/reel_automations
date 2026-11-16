@echo off
title The Startup Road - Mirror Queue Status
cd /d "%~dp0"

echo ========================================================
echo   THE STARTUP ROAD - QUEUE POSITION & REMAINING DAYS
echo ========================================================
echo.
python mirror_pipeline.py --status
echo.
echo ========================================================
pause
