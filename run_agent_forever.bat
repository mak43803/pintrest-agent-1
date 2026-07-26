@echo off
title Baddies Beauty - Autonomous 24/7 AI Agent Watchdog
color 0A
cd /d "%~dp0"

echo =================================================================
echo  👑 BADDIES BEAUTY - AUTONOMOUS 24/7 AI AGENT LAUNCHER
echo =================================================================
echo  - Auto-Heals Python code errors using AI (Gemini API)
echo  - Auto-Repairs Amazon Affiliate tags (savvyshop0965-20)
echo  - Auto-Restarts main.py continuously 24/7
echo =================================================================
echo.

:START
python watchdog.py
echo.
echo [WATCHDOG] Process stopped or crashed. Restarting Watchdog in 10 seconds...
timeout /t 10 /nobreak > nul
goto START
