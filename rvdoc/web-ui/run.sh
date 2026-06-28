#!/usr/bin/env bash
# Simple launcher for RVDoc web UI
# - creates a virtual environment the first time
# - installs Flask inside that environment
# - runs the Flask app

set -e
VENV_DIR=".venv"

# Create the virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment…"
  python3 -m venv "$VENV_DIR"
fi

# Activate the virtual environment
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

# Install Flask (quietly, so the output is short)
pip install --quiet flask

# Run the web server
python app.py
