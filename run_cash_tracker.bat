@echo off
echo Starting Cash Tracker...
cd /d "%~dp0"
if exist "dist\CashTracker.exe" (
    start "" "dist\CashTracker.exe"
) else (
    echo Error: CashTracker.exe not found in the dist directory.
    echo Please make sure you have built the application using build.py
    pause
) 