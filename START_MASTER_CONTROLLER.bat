@echo off
title Multi-Account Reel Automation Master Controller
cd /d "%~dp0"
echo ========================================================
echo   MULTI-ACCOUNT INSTAGRAM REEL AUTOMATION CONTROLLER
echo ========================================================
echo Channels: Startup Road, Healthy Diet, Trading Pulse, Viral Finds
echo Starting Telegram Listener and Background Multi-Channel Scheduler...
echo.
python master_controller.py
pause
