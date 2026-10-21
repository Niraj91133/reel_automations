@echo off
title Instagram Reel Automation Runner (im_raaaj_ Chat)
cd /d "%~dp0"
echo ========================================================
echo   INSTAGRAM REEL AUTOMATION PIPELINE (im_raaaj_ Chat)
echo ========================================================
echo.
echo Source: Instagram DM Chat (im_raaaj_)
echo Limit: 10 Shared Reels
echo.
echo Starting automation...
echo.

python run_dm_automation.py

echo.
echo ========================================================
echo Done! Check your Telegram Bot for processed reels.
echo ========================================================
pause
