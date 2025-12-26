@echo off
REM ═══════════════════════════════════════════════════════════════════════════
REM  BAYESOPT UNIFIED LAUNCHER - WINDOWS
REM  
REM  One script to run everything! Choose between:
REM  - Tuner: Bayesian optimization tuner with GUI
REM  - Dashboard: Web-based monitoring dashboard
REM  - Both: Run tuner and dashboard together
REM ═══════════════════════════════════════════════════════════════════════════

echo ==========================================
echo   BayesOpt Unified Launcher
echo ==========================================
echo.

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Check if Python is available
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or newer from python.org
    echo.
    echo Make sure to check "Add Python to PATH" during installation!
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo Found %PYTHON_VERSION%

REM Verify Python 3.8+
python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python 3.8 or newer is required
    echo Please upgrade your Python installation from python.org
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo.
    echo Creating virtual environment...
    python -m venv .venv
    echo [32m✓ Virtual environment created[0m
)

REM Activate virtual environment
echo.
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo.
echo Installing dependencies...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r bayesopt\tuner\requirements.txt
python -m pip install --quiet -r dashboard\requirements.txt
echo [32m✓ All dependencies installed[0m

REM Launch both components
echo.
echo ==========================================
echo   Launching BayesOpt...
echo ==========================================
echo.
echo Starting Dashboard in background...
start "BayesOpt Dashboard" python -m dashboard.app
echo Dashboard running at: http://localhost:8050
echo.
echo Starting Tuner GUI...
python -m bayesopt.tuner.gui

REM When tuner closes, ask if user wants to keep dashboard running
echo.
set /p stop_dashboard="Tuner closed. Stop dashboard? (y/n): "
if /i "%stop_dashboard%"=="y" (
    echo Stopping dashboard...
    taskkill /FI "WINDOWTITLE eq BayesOpt Dashboard*" /F >nul 2>nul
) else (
    echo Dashboard still running at http://localhost:8050
    echo To stop it, close the "BayesOpt Dashboard" window
)

pause
