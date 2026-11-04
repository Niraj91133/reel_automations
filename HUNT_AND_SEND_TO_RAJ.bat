@echo off
title Hunt and Send 80 Reels to Raj
cd /d "%~dp0"
echo ========================================================
echo       VIRAL REEL HUNTER - SEND 80 REELS TO RAJ
echo ========================================================
echo Select Channel to Hunt:
echo 1. Startup Road (@startup_road)
echo 2. Gudtree (@gudtree_)
echo 3. Trading Road (@trading_road_)
echo 4. Trending Road (@trending_road)
echo.
set /p ch_choice="Enter choice (1, 2, 3, or 4): "

if "%ch_choice%"=="1" set target=startup_road
if "%ch_choice%"=="2" set target=healthy_diet
if "%ch_choice%"=="3" set target=trading_pulse
if "%ch_choice%"=="4" set target=viral_finds

if "%target%"=="" (
    echo Invalid choice. Exiting.
    pause
    exit /b
)

echo.
echo Starting Keyword + Hashtag Viral Hunt for %target%...
python -c "from core.config_manager import get_channel_config; from core.niche_hunter import hunt_niche_reels, send_hunted_reels_to_raj_chat; cfg = get_channel_config('%target%'); cand = hunt_niche_reels(cfg, target_count=80); send_hunted_reels_to_raj_chat(cfg, cand, max_to_send=80)"
pause

