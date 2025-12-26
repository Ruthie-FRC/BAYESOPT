#!/bin/bash
# Setup script for GitHub Codespaces
# This runs automatically when the codespace is created

set -e

echo "🚀 Setting up BayesOpt development environment..."

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate and install dependencies
echo "📦 Installing dependencies..."
source .venv/bin/activate

# Upgrade pip
pip install --quiet --upgrade pip

# Install tuner dependencies
echo "  - Installing tuner dependencies..."
pip install --quiet -r bayesopt/tuner/requirements.txt

# Install dashboard dependencies
echo "  - Installing dashboard dependencies..."
pip install --quiet -r dashboard/requirements.txt

# Append auto-activation to bashrc if not already there
if [[ -f ~/.bashrc ]]; then
    if ! grep -q "_activate_bayesopt_venv" ~/.bashrc; then
        echo "" >> ~/.bashrc
        echo "# Auto-activate BayesOpt virtual environment" >> ~/.bashrc
        cat .devcontainer/bashrc_append.sh >> ~/.bashrc
        echo "✅ Added auto-activation to ~/.bashrc"
    fi
else
    echo "⚠️  Warning: ~/.bashrc not found, skipping auto-activation setup"
fi

echo "✅ Setup complete!"
echo ""
echo "Virtual environment is at: .venv"
echo "All dependencies have been installed automatically."
echo ""
echo "The terminal will automatically activate the venv when opened."
