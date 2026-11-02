@echo off
title Startup Road 24/7 Controller & Auto-Publisher
cd /d "%~dp0"
echo ========================================================
echo    STARTUP ROAD AUTOMATION & AUTO-PUBLISHING CONTROLLER
echo ========================================================
echo.
echo Source Chat:   Instagram DM (@im_raaaj_)
echo Destination:   Instagram Account (@startup_road)
echo Telegram Bot:  @my_reel_auto_bot (/run, /account, /status)
echo Auto-Schedule: Daily 10:00 PM IST
echo.
echo Starting 24/7 service...
echo.

python telegram_controller.py

pause
