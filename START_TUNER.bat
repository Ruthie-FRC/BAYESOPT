@echo off
REM ═══════════════════════════════════════════════════════════════════════════
REM  BAYESIAN OPTIMIZATION TUNER - WINDOWS LAUNCHER
REM  Double-click this file to start the tuner with a popup window!
REM  
REM  The tuner runs on your laptop and connects to the robot via NetworkTables.
REM  All calculations happen on your laptop - only coefficient updates are sent
REM  to the robot via NetworkTables for the Java code to read.
REM ═══════════════════════════════════════════════════════════════════════════

REM Change to the script's directory
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.8+ from https://www.python.org/
    echo.
    echo Make sure to check "Add Python to PATH" during installation!
    pause
    exit /b 1
)

REM Install dependencies if needed (quietly)
pip install -r bayesopt/tuner/requirements.txt --quiet 2>nul

REM Start the tuner GUI (pythonw runs without console window)
REM Using python instead of pythonw so errors are visible
start "Bayesian Optimization Tuner" python -m bayesopt.tuner.gui

REM Exit immediately - the GUI window is now running
exit
