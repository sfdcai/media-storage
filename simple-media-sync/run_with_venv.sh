#!/bin/bash
# Wrapper script to run commands with virtual environment

# Activate virtual environment
source /opt/media-sync-env/bin/activate

# Change to project directory
cd "$(dirname "$0")"

# Run the command passed as arguments
exec "$@"
