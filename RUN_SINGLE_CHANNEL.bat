@echo off
title Run Single Channel Automation
cd /d "%~dp0"
echo ========================================================
echo        SELECT CHANNEL TO RUN REEL PIPELINE
echo ========================================================
echo  [1] Startup Road (startup_road)
echo  [2] Healthy Diet and Snacks (healthy_diet)
echo  [3] Trading Pulse (trading_pulse)
echo  [4] Viral Finds Gadgets (viral_finds)
echo ========================================================
set /p choice="Enter choice (1-4): "

if "%choice%"=="1" set CHANNEL=startup_road
if "%choice%"=="2" set CHANNEL=healthy_diet
if "%choice%"=="3" set CHANNEL=trading_pulse
if "%choice%"=="4" set CHANNEL=viral_finds

if "%CHANNEL%"=="" (
    echo Invalid choice!
    pause
    exit /b
)

echo.
echo Running pipeline for %CHANNEL% (1 Reel)...
python run_channel.py --channel=%CHANNEL% --limit=1
echo.
pause
