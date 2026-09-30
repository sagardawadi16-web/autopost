@echo off
cd /d "C:\Users\LENOVO\Downloads\autopost"
echo ========================================================
echo Generating @GHIBLISTYLESTUDIO Landscape Story Video (16:9)
echo ========================================================
python -m src.ghibli_pipeline --type story --scenes 4
pause
