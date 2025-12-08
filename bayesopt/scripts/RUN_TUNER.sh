#!/bin/bash
# ============================================================
# FRC SHOOTER TUNER - AUTO-START DAEMON
# Runs in background, drivers do nothing!
# ============================================================

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Run daemon in background
nohup python3 tuner_daemon.py > /dev/null 2>&1 &

# Optional: Show a quick message
echo "FRC Tuner daemon started in background"
# ============================================================
