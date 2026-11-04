@echo off
title Night Cloud-Scheduler (Schedule Tomorrow's 25 Reels)
cd /d "%~dp0"
echo ========================================================
echo   NIGHT CLOUD-SCHEDULER - PRE-BAKE TOMORROW'S REELS
echo ========================================================
echo Select Channel to Schedule:
echo 1. Startup Road (@startup_road) - 25 Reels
echo 2. Gudtree (@gudtree_) - 25 Reels
echo 3. Trading Road (@trading_road_) - 25 Reels
echo 4. Trending Road (@trending_road) - 25 Reels
echo 5. ALL 4 CHANNELS SEQUENTIALLY (100 Reels Total)
echo.
set /p ch_choice="Enter choice (1, 2, 3, 4, or 5): "

if "%ch_choice%"=="1" set target=startup_road
if "%ch_choice%"=="2" set target=healthy_diet
if "%ch_choice%"=="3" set target=trading_pulse
if "%ch_choice%"=="4" set target=viral_finds
if "%ch_choice%"=="5" set target=all

if "%target%"=="" (
    echo Invalid choice. Exiting.
    pause
    exit /b
)

if "%target%"=="all" (
    echo Starting Night Cloud-Scheduling for ALL 4 Channels...
    python -c "from master_controller import run_all_cloud_schedules; run_all_cloud_schedules()"
) else (
    echo Starting Night Cloud-Scheduling for %target%...
    python -c "from core.cloud_scheduler import cloud_schedule_channel_for_tomorrow; cloud_schedule_channel_for_tomorrow('%target%', target_count=25)"
)

pause

