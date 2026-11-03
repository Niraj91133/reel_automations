@echo off
title 100% Hands-Off Instagram Autopilot (Multi-Account)
cd /d "%~dp0"
echo ========================================================
echo   100%% HANDS-OFF FULL AUTOPILOT REEL AUTOMATION
echo   (Anti-Crash & Low CPU Mode Enabled)
echo ========================================================
echo  Accounts Active:
echo   1. Startup Road (@startup_road)
echo   2. Gudtree (@gudtree_)
echo   3. Trading Road (@trading_road_)
echo   4. Trending Road (@trending_road)
echo ========================================================
echo  Safety Guardrails Active:
echo   - FFmpeg CPU limited to 2 worker threads (prevents PC freezing)
echo   - Playwright image/media blocking (keeps browser RAM under 100MB)
echo   - Automatic 15s cooldown and RAM flush between accounts
echo ========================================================
echo.
echo Choose Run Mode:
echo   [1] 1 Reel per Account (Quick Daily Sweep - 4 Reels Total)
echo   [2] 10 Reels per Account Sequentially (Full 40-Reel Batch)
echo   [3] Single Account Only (Startup Road)
echo.

set /p mode="Choose option (1-3, or press Enter for [1]): "

if "%mode%"=="2" (
    echo.
    echo Running 10 Reels per account sequentially...
    python core/full_autopilot.py all 10
    goto done
)

if "%mode%"=="3" (
    echo.
    echo Running Startup Road (10 Reels)...
    python core/full_autopilot.py startup_road 10
    goto done
)

echo.
echo Running 1 Reel per account sequentially...
python core/full_autopilot.py all 1

:done
echo.
echo ========================================================
echo Autopilot run finished! Check your Telegram Bot and Instagram feeds.
echo ========================================================
pause
