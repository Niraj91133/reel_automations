@echo off
title Multi-Account Reel Automations (4 Channels)
cd /d "%~dp0"
echo ========================================================
echo   MULTI-ACCOUNT 24/7 AUTOMATIONS (4 CHANNELS)
echo   120 REELS/DAY + 80 STORIES/DAY (200 TOTAL/DAY)
echo ========================================================
echo [1/4] Launching Telegram Master Controller...
start "Master Controller" python master_controller.py
echo [2/4] Launching Autopilot Hunting Daemon...
start "Autopilot Daemon" python run_3channel_autopilot.py
echo [3/4] Launching 4-Channel 30-Reel/Day Scheduled Dispatcher...
start "4-Channel Reel Dispatcher" python run_all_4channels_tomorrow_dispatcher.py
echo [4/4] Launching 4-Channel 20-Story/Day Scheduled Dispatcher...
start "4-Channel Story Dispatcher" python run_all_4channels_story_dispatcher.py
echo ========================================================
echo  ALL 4 ENGINES ONLINE!
echo  - 120 Reels / Day (30 per Channel)
echo  - 80 Stories / Day (20 per Channel)
echo  - Meta Iron Shield Active & Guarding
echo ========================================================
timeout /t 5
