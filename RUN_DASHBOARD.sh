#!/bin/bash
# Automated launcher for BayesOpt Dashboard
# Creates venv, installs dependencies, and launches dashboard

set -e

echo "=========================================="
echo "  BayesOpt Dashboard Launcher"
echo "=========================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8 or newer from python.org"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Found Python $PYTHON_VERSION"

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
echo "Installing dashboard dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r dashboard/requirements.txt
echo "✓ Dependencies installed"

# Launch dashboard
echo ""
echo "=========================================="
echo "  Launching Dashboard..."
echo "=========================================="
echo ""
echo "Open your browser to: http://localhost:8050"
echo ""
echo "Press Ctrl+C to stop the dashboard"
echo ""

python -m dashboard.app
