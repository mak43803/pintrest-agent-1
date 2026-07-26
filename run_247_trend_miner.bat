@echo off
TITLE BADDIES BEAUTY — 24/7 AUTONOMOUS TREND MINER AGENT
COLOR 0A

:: Automatically switch working directory to project folder
cd /d "c:\Users\mazzu\OneDrive\Desktop\pintrest ai agent"

echo =================================================================
echo  👑 BADDIES BEAUTY — 24/7 PRODUCT INTELLIGENCE MINER LAUNCHER
echo =================================================================
echo.
echo Running 24/7 background sweeps across TikTok, Reddit, Quora,
echo Pinterest, Amazon, Sephora, Boots, and Target...
echo.

:loop
python -m trend_miner.runner --daemon --interval 21600
echo.
echo ⚠️ Daemon interrupted or restarted. Restarting in 10 seconds...
timeout /t 10
goto loop
