@echo off
title AI Viral Content Research Scout (Multi-Account Sequential)
cd /d "%~dp0"

echo ========================================================
echo   AI MULTI-ACCOUNT VIRAL REEL SCOUT ENGINE
echo   (Lightweight & Anti-Crash Mode: Max 90MB RAM)
echo ========================================================
echo.
echo  Accounts Active:
echo   [1] ALL 4 Accounts Sequentially (10 Reels Each with Cooldown)
echo   [2] Startup Road Only (@startup_road - 10 Reels)
echo   [3] Gudtree Only (@gudtree_ - 10 Reels)
echo   [4] Trading Road Only (@trading_road_ - 10 Reels)
echo   [5] Trending Road Only (@trending_road - 10 Reels)
echo.
echo  Sequential Safety:
echo   * Each account runs in an isolated browser
echo   * Media & video assets blocked (saves 85%% RAM & CPU)
echo   * Automatic 15s cooldown & RAM flush between accounts
echo   * Destination: @im_raaaj_ Instagram DM Chat
echo ========================================================
echo.

set /p choice="Choose an option (1-5, or press Enter for ALL): "

if "%choice%"=="2" (
    echo.
    echo Running Startup Road (10 Reels)...
    python core/niche_scout.py 10 startup_road
    goto done
)
if "%choice%"=="3" (
    echo.
    echo Running Gudtree (10 Reels)...
    python core/niche_scout.py 10 healthy_diet
    goto done
)
if "%choice%"=="4" (
    echo.
    echo Running Trading Road (10 Reels)...
    python core/niche_scout.py 10 trading_pulse
    goto done
)
if "%choice%"=="5" (
    echo.
    echo Running Trending Road (10 Reels)...
    python core/niche_scout.py 10 viral_finds
    goto done
)

echo.
echo Running ALL 4 Accounts Sequentially (10 Reels each)...
python core/niche_scout.py 10 all

:done
echo.
echo ========================================================
echo Workflow finished! Check @im_raaaj_ chat and Telegram.
echo ========================================================
pause
