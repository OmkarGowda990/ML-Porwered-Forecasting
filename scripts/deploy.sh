#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

REPO_PATH="/home/ubuntu/ML-Porwered-Forecasting"
SERVICE_NAME="streamlit-app.service"
VENV_PYTHON="/home/ubuntu/ml-venv/bin/python3"
VENV_PIP="/home/ubuntu/ml-venv/bin/pip"

echo "Navigating to repository..."
cd $REPO_PATH

# 1. Pull the latest code
echo "Pulling latest code from GitHub..."
git pull

# 2. Check for dependency changes and install them
if git diff --name-only HEAD@{1} HEAD | grep -qE "requirements\.txt|requirements-dev\.txt"; then
    echo "requirements changed. Installing new dependencies..."
    $VENV_PIP install -r requirements.txt
fi

# 3. Restart the Streamlit service
echo "Restarting Systemd service: $SERVICE_NAME"
sudo systemctl restart $SERVICE_NAME

echo "Deployment complete."