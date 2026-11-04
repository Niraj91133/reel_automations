@echo off
title 5-Reels Verification Test (5 Min Gap)
cd /d "%~dp0"
echo ========================================================
echo   MULTI-ACCOUNT 5-REELS VERIFICATION (5 MIN GAP)
echo ========================================================
echo Channels: Startup Road, Gudtree, Trading Road, Trending Road
echo Sending 5 reels from each account to @im_raaaj_ with 5 mins gap...
echo.
python test_5_reels_flow.py 5 5
pause

