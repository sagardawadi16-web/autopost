@echo off
title AutoPost - Powerhouse Production Batch (Run Once)
cd /d "%~dp0"

echo ======================================================================
echo   Executing Daily Powerhouse Batch (All 3 Streams + Analytics)
echo ======================================================================
echo.

python -m src.daily_powerhouse_runner --target-channel ghibli

pause
