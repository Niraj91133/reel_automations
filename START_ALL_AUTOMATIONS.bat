@echo off
title Multi-Account Reel Automations (4 Channels)
cd /d "%~dp0"
echo ========================================================
echo   MULTI-ACCOUNT 24/7 AUTOMATIONS (4 CHANNELS - 120 REELS)
echo ========================================================
echo [1/3] Launching Telegram Master Controller...
start "Master Controller" python master_controller.py
echo [2/3] Launching 3-Channel 100%% Autopilot Daemon...
start "3-Channel Autopilot Daemon" python run_3channel_autopilot.py
echo [3/3] Launching 4-Channel 30-Reel/Day Scheduled Dispatcher...
start "4-Channel Daily Dispatcher" python run_all_4channels_tomorrow_dispatcher.py
echo ========================================================
echo  ALL 4 ENGINES ONLINE! 120 REELS READY TO POST.
echo  Check your Telegram Bot for live notifications.
echo ========================================================
timeout /t 5
