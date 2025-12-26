# Auto-activate virtual environment in Codespaces
# This is automatically appended to ~/.bashrc in the container

# Function to activate venv if in BAYESOPT directory
_activate_bayesopt_venv() {
    if [[ -d "${WORKSPACE_FOLDER}/.venv" ]] || [[ -d "$(pwd)/.venv" ]]; then
        local venv_path="${WORKSPACE_FOLDER}/.venv"
        if [[ ! -d "$venv_path" ]]; then
            venv_path="$(pwd)/.venv"
        fi

        if [[ -f "$venv_path/bin/activate" ]] && [[ "$VIRTUAL_ENV" != "$venv_path" ]]; then
            source "$venv_path/bin/activate"
            echo "✅ Virtual environment activated (.venv)"
        fi
    fi
}

# Run on shell startup
_activate_bayesopt_venv

# Hook to reactivate on cd (for Codespaces)
cd() {
    builtin cd "$@"
    _activate_bayesopt_venv
}
