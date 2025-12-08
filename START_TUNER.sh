#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
#  BAYESIAN OPTIMIZATION TUNER - MAC/LINUX LAUNCHER
#  Double-click this file to start the tuner with a popup window!
#  
#  The tuner runs on your laptop and connects to the robot via NetworkTables.
#  All calculations happen on your laptop - only coefficient updates are sent
#  to the robot via NetworkTables for the Java code to read.
#  
#  On Mac/Linux, you may need to make this executable first:
#    chmod +x START_TUNER.sh
# ═══════════════════════════════════════════════════════════════════════════

# Change to the script's directory
cd "$(dirname "$0")"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed!"
    echo "Please install Python 3.8+ using your package manager or from https://www.python.org/"
    read -p "Press Enter to exit..."
    exit 1
fi

# Install dependencies if needed (quietly)
pip3 install -r bayesopt/tuner/requirements.txt --quiet 2>/dev/null || pip install -r bayesopt/tuner/requirements.txt --quiet

# Start the tuner GUI
python3 -m bayesopt.tuner.gui &

echo "Tuner window opened!"
