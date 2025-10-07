#!/bin/bash
#
# Terminal Initialization Script
# This script can be sourced or executed to set up a terminal session
# for the A0 Code Execution MCP
#

# Exit on error for executed scripts (but not sourced)
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    set -e
fi

# Set terminal environment
export TERM="${TERM:-xterm-256color}"
export PYTHONUNBUFFERED=1

# Disable history file to avoid polluting user's history
unset HISTFILE

# Set up prompt (this will be overridden by the TTY session)
export PS1="A0> "

# Common PATH additions (adjust as needed)
if [ -d "/usr/local/bin" ] && [[ ":$PATH:" != *":/usr/local/bin:"* ]]; then
    export PATH="/usr/local/bin:$PATH"
fi

# Python path setup
if [ -n "$PYTHONPATH" ]; then
    export PYTHONPATH="$PYTHONPATH:$(pwd)"
else
    export PYTHONPATH="$(pwd)"
fi

# Load user's shell configuration if available
# This is useful for picking up environment variables, aliases, etc.
if [ -f "$HOME/.bashrc" ]; then
    source "$HOME/.bashrc" 2>/dev/null || true
fi

if [ -f "$HOME/.bash_profile" ]; then
    source "$HOME/.bash_profile" 2>/dev/null || true
fi

# Virtual environment activation (if specified)
# The VENV_PATH variable can be set before sourcing this script
if [ -n "$VENV_PATH" ] && [ -f "$VENV_PATH/bin/activate" ]; then
    echo "Activating virtual environment: $VENV_PATH"
    source "$VENV_PATH/bin/activate"
fi

# Welcome message (only if executed, not sourced)
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    echo "A0 Code Execution Terminal Initialized"
    echo "Python: $(python3 --version 2>&1)"
    echo "Shell: $SHELL"
    echo "Working Directory: $(pwd)"
fi

# Export a marker variable to indicate this script has run
export A0_TERMINAL_INITIALIZED=1
