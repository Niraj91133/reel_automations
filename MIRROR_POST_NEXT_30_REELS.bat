@echo off
title The Startup Road - Daily 30-Reel Mirror Dispatcher
cd /d "%~dp0"

echo ========================================================
echo   THE STARTUP ROAD - REEL MIRROR ENGINE (30 REELS BATCH)
echo ========================================================
echo Source Account:      @startup_road (Chronological Bottom-Up)
echo Destination Account: @the_startuproad
echo Batch Size:          30 Reels
echo ========================================================
echo.

python mirror_pipeline.py --batch 30

echo.
echo ========================================================
echo Batch dispatch complete! Check @the_startuproad on Instagram.
echo ========================================================
pause
