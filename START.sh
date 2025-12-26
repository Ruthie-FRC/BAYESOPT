#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
#  BAYESOPT UNIFIED LAUNCHER - MAC/LINUX
#  
#  One script to run everything! Choose between:
#  - Tuner: Bayesian optimization tuner with GUI
#  - Dashboard: Web-based monitoring dashboard
#  - Both: Run tuner and dashboard together
#  
#  On Mac/Linux, you may need to make this executable first:
#    chmod +x START.sh
# ═══════════════════════════════════════════════════════════════════════════

set -e

echo "=========================================="
echo "  BayesOpt Unified Launcher"
echo "=========================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8 or newer from python.org"
    echo ""
    read -p "Press Enter to exit..." dummy
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Found Python $PYTHON_VERSION"

# Verify Python 3.8+
python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "ERROR: Python 3.8 or newer is required"
    echo "Please upgrade your Python installation"
    echo ""
    read -p "Press Enter to exit..." dummy
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source .venv/bin/activate

# Install/upgrade dependencies
echo ""
echo "Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r bayesopt/tuner/requirements.txt
pip install --quiet -r dashboard/requirements.txt
echo "✓ All dependencies installed"

# Launch both components
echo ""
echo "=========================================="
echo "  Launching BayesOpt..."
echo "=========================================="
echo ""
echo "Starting Dashboard in background..."
python3 -m dashboard.app &
DASHBOARD_PID=$!
echo "Dashboard running at: http://localhost:8050 (PID: $DASHBOARD_PID)"
echo ""
echo "Starting Tuner GUI..."
python3 -m bayesopt.tuner.gui

# When tuner closes, ask if user wants to keep dashboard running
echo ""
read -p "Tuner closed. Stop dashboard? (y/n): " stop_dashboard
if [[ "$stop_dashboard" == "y" || "$stop_dashboard" == "Y" ]]; then
    echo "Stopping dashboard..."
    kill $DASHBOARD_PID 2>/dev/null || true
else
    echo "Dashboard still running at http://localhost:8050"
    echo "To stop it later, run: kill $DASHBOARD_PID"
fi
