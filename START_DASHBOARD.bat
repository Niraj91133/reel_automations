@echo off
title Reel Automation Control Dashboard
cd /d "%~dp0"
echo ========================================================
echo   REEL AUTOMATION LIVE CONTROL CENTER (WEB UI)
echo ========================================================
echo Starting Streamlit Dashboard on http://localhost:8501 ...
echo.
streamlit run dashboard.py
pause

