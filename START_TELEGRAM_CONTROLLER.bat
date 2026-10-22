@echo off
title Instagram Reels Telegram Controller
cd /d "%~dp0"
echo ========================================================
echo    TELEGRAM 24/7 COMMAND CONTROLLER (Startup + Politics)
echo ========================================================
echo.
echo Startup Bot:  @my_reel_auto_bot (/startup, /run)
echo Politics Bot: @my_reel_news_bot (/politics, /run)
echo.
echo Starting controller service...
echo.

python telegram_controller.py

pause
