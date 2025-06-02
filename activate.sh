#!/bin/bash
# Activate the Memory Graph Extract virtual environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
    echo "Memory Graph Extract environment activated"
    echo "Use 'mge' command to start extracting documents"
else
    echo "Virtual environment not found. Run ./scripts/mge-setup first."
fi
