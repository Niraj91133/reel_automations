@echo off
title Start 30-Posts Automation in Background
cd /d "%~dp0"

echo ========================================================
echo   STARTING STARTUP ROAD 24/7 BACKGROUND SERVICE
echo ========================================================
echo.
echo Target Account: @startup_road
echo Schedule:       30 Posts / Day (6:00 AM to 10:00 PM IST)
echo Mode:           Completely Silent Background Process (No Windows)
echo.
echo Launching background service via VBS...
wscript.exe run_background_controller.vbs

echo.
echo ========================================================
echo SUCCESS! Automation is now running in the background.
echo You can check live progress in your Telegram Bot (@my_reel_auto_bot):
echo Send "/status" or "/account" anytime!
echo ========================================================
timeout /t 5
