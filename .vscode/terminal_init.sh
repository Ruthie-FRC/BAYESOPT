#!/bin/bash
# Terminal initialization script for BayesOpt (Bash)
# This script is automatically run when opening a bash terminal in VS Code
# It activates the Python virtual environment if it exists

# Source the system bash profile if it exists (needed when using --init-file)
if [[ -f ~/.bashrc ]]; then
    source ~/.bashrc
elif [[ -f ~/.bash_profile ]]; then
    source ~/.bash_profile
elif [[ -f /etc/profile ]]; then
    source /etc/profile
fi

# Get the workspace root (parent of .vscode directory)
bayesopt_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
venv_path="$bayesopt_root/.venv"
venv_activate="$venv_path/bin/activate"

# Check if virtual environment exists
if [[ -f "$venv_activate" ]]; then
    # Activate the virtual environment
    source "$venv_activate"
    echo "✓ Virtual environment activated (.venv)"
else
    echo "ℹ Virtual environment not found. Run START.sh or START.bat to create it."
fi
