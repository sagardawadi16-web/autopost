@echo off
cd /d "C:\Users\LENOVO\Downloads\autopost"
echo ========================================================
echo Connecting Secondary Gmail YouTube Channel (Ghibli)
echo ========================================================
python -m src.uploader.authorize_channel --channel ghibli
pause
