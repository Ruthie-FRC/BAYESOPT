@echo off
REM Automated launcher for BayesOpt Dashboard
REM Creates venv, installs dependencies, and launches dashboard

echo ==========================================
echo   BayesOpt Dashboard Launcher
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
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo Found %PYTHON_VERSION%

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
echo Installing dashboard dependencies...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r dashboard\requirements.txt
echo [32m✓ Dependencies installed[0m

REM Launch dashboard
echo.
echo ==========================================
echo   Launching Dashboard...
echo ==========================================
echo.
echo Open your browser to: http://localhost:8050
echo.
echo Press Ctrl+C to stop the dashboard
echo.

python -m dashboard.app

pause
