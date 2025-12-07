@echo off
REM ============================================================
REM FRC SHOOTER TUNER - AUTO-START DAEMON
REM Runs in background, drivers do nothing!
REM ============================================================

REM Change to the directory where this script is located
cd /d "%~dp0"

REM Run silently in background (no window)
start /B pythonw tuner_daemon.py

REM Optional: Show a quick message
echo FRC Tuner daemon started in background
timeout /t 2 /nobreak >nul

REM Optional: Keep the script running to prevent exit
REM (uncomment if you want to keep the window open)
REM pause
REM ============================================================
