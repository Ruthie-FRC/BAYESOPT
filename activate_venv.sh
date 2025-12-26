#!/bin/bash
# Auto-activation script for BayesOpt virtual environment
# Source this file in your shell configuration to automatically activate
# the virtual environment when you cd into this directory.
#
# Add to your ~/.bashrc or ~/.zshrc:
#   source /path/to/BAYESOPT/activate_venv.sh
#

# Function to check if we're in the BayesOpt directory or a subdirectory
_bayesopt_activate_venv() {
    local bayesopt_root
    local current_dir="$PWD"

    # Try to find the BAYESOPT directory by looking for bayesopt/ and START_TUNER.sh
    while [[ "$current_dir" != "/" ]]; do
        if [[ -d "$current_dir/bayesopt" ]] && [[ -f "$current_dir/START_TUNER.sh" ]]; then
            bayesopt_root="$current_dir"
            break
        fi
        current_dir=$(dirname "$current_dir")
    done

    # If we found the BayesOpt directory and not already in the venv
    if [[ -n "$bayesopt_root" ]] && [[ "$VIRTUAL_ENV" != "$bayesopt_root/.venv" ]]; then
        # Create venv if it doesn't exist
        if [[ ! -d "$bayesopt_root/.venv" ]]; then
            echo "Creating virtual environment..."
            python3 -m venv "$bayesopt_root/.venv"

            # Install dependencies
            source "$bayesopt_root/.venv/bin/activate"
            echo "Installing dependencies..."
            pip install --quiet --upgrade pip
            pip install --quiet -r "$bayesopt_root/bayesopt/tuner/requirements.txt"
            pip install --quiet -r "$bayesopt_root/dashboard/requirements.txt"
            echo "✓ Virtual environment created and dependencies installed"
        else
            source "$bayesopt_root/.venv/bin/activate"
            echo "✓ Virtual environment activated (.venv)"
        fi
    fi

    # Deactivate if we've left the BayesOpt directory
    if [[ -z "$bayesopt_root" ]] && [[ -n "$VIRTUAL_ENV" ]] && [[ "$VIRTUAL_ENV" == *"/.venv" ]]; then
        # Only deactivate if the venv is in a parent directory we've left
        local venv_parent=$(dirname "$VIRTUAL_ENV")
        if [[ "$PWD" != "$venv_parent"* ]]; then
            deactivate 2>/dev/null || true
            echo "✓ Virtual environment deactivated"
        fi
    fi
}

# Hook into cd command for bash (with safeguards)
if [[ -n "$BASH_VERSION" ]]; then
    # Only override cd if not already overridden
    if ! type -t cd | grep -q "function"; then
        _bayesopt_cd() {
            builtin cd "$@"
            local result=$?
            _bayesopt_activate_venv
            return $result
        }
        alias cd='_bayesopt_cd'
    fi
fi

# Hook into chpwd for zsh
if [[ -n "$ZSH_VERSION" ]]; then
    autoload -U add-zsh-hook
    add-zsh-hook chpwd _bayesopt_activate_venv
fi

# Activate on shell startup if we're already in the directory
_bayesopt_activate_venv
