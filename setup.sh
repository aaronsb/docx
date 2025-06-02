#!/bin/bash
# setup.sh - Root-level setup script for Memory Graph Extract
# This is a convenience wrapper that calls the main setup script

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if the actual setup script exists
if [ -f "$SCRIPT_DIR/scripts/mge-setup" ]; then
    # Make sure it's executable
    chmod +x "$SCRIPT_DIR/scripts/mge-setup"
    
    # Run the actual setup script
    exec "$SCRIPT_DIR/scripts/mge-setup" "$@"
else
    echo "Error: Setup script not found at scripts/mge-setup"
    echo "Please ensure you're running this from the project root directory."
    exit 1
fi