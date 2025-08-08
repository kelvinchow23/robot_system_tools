#!/bin/bash
# Setup script for solid_dosing_client

echo "=== Setting up solid_dosing_client dependencies ==="

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "Using virtual environment: $VIRTUAL_ENV"
else
    echo "No virtual environment detected. Creating one..."
    python3 -m venv client_env
    source client_env/bin/activate
    echo "Created and activated client_env"
fi

echo "Installing Python dependencies..."

# Install basic dependencies
pip install --upgrade pip

# For now, we don't need dotenv since we commented it out
# pip install python-dotenv

echo "Testing client imports..."
python3 -c "
import os
import socket
import logging
from pathlib import Path
from time import sleep

print('✓ All required modules imported successfully')
print('✓ Client should work without additional dependencies')
"

echo ""
echo "=== Setup complete ==="
echo ""
echo "To run the client:"
echo "  python3 solid_dosing_client"
echo ""
echo "Make sure your Pi camera server is running at 192.168.1.3:2222"
echo ""
echo "The client will:"
echo "  1. Connect to the Pi camera server"
echo "  2. Send 'TAKE_PHOTO' command"
echo "  3. Receive and save photos to 'Detection_Photos' directory"
