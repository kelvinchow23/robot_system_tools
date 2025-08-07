#!/bin/bash
# Quick setup script for Pi Zero 2W camera server

set -e  # Exit on any error

echo "=== Pi Zero 2W Camera Server Setup ==="

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "Warning: This script is designed for Raspberry Pi"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
echo "Installing system dependencies..."
sudo apt install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    libcamera-dev \
    libcamera-apps \
    python3-libcamera \
    libatlas-base-dev \
    libjpeg-dev \
    python3-opencv \
    libcap-dev \
    build-essential \
    python3-yaml \
    python3-numpy

# Try to install picamera2 system package if available
sudo apt install -y python3-picamera2 || echo "python3-picamera2 not available, will install via pip"

# Check if camera is enabled
echo "Checking camera configuration..."
if ! grep -q "^camera_auto_detect=1" /boot/config.txt; then
    echo "Enabling camera interface..."
    echo "camera_auto_detect=1" | sudo tee -a /boot/config.txt
    echo "Camera enabled. Please reboot after setup completes."
fi

# Setup virtual environment
echo "Setting up Python virtual environment..."
if [ ! -d "ur3_cam_env" ]; then
    echo "Creating ur3_cam_env virtual environment..."
    python3 -m venv ur3_cam_env
else
    echo "Using existing ur3_cam_env virtual environment..."
fi

# Activate virtual environment and install packages
echo "Installing Python packages..."
source ur3_cam_env/bin/activate
pip install --upgrade pip

# Configure pip for slow Pi Zero 2W connections
pip config set global.timeout 300
pip config set global.retries 5

# Install packages with error handling
echo "Installing essential Python packages (may take several minutes)..."

# Try to install yaml first
echo "Installing PyYAML..."
pip install --timeout=300 --retries=5 PyYAML || {
    echo "PyYAML pip install failed, checking system package..."
    python3 -c "
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
try:
    import yaml
    print('✓ Using system yaml package')
except ImportError:
    print('✗ yaml not available via system packages either')
    print('Trying to install python3-yaml system package...')
    import subprocess
    subprocess.run(['sudo', 'apt', 'install', '-y', 'python3-yaml'])
"
}

echo "Installing python-dotenv..."
pip install --timeout=300 --retries=5 python-dotenv || echo "python-dotenv failed, continuing..."

echo "Installing picamera2..."
pip install --timeout=300 --retries=5 picamera2 || {
    echo "picamera2 pip install failed, checking system package..."
    python3 -c "
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
try:
    from picamera2 import Picamera2
    print('✓ Using system picamera2 package')
except ImportError:
    print('✗ picamera2 not available via system packages either')
    exit(1)
"
}

echo "Skipping heavy packages (numpy, scipy, apriltags) to avoid memory issues..."
echo "You can install them manually later if needed."

# Test camera
echo "Testing camera setup..."
python3 -c "
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')  # Include system packages
try:
    from picamera2 import Picamera2
    print('✓ Picamera2 import successful')
    cam = Picamera2()
    print('✓ Camera initialization successful')
    cam.close()
    print('✓ Camera test completed successfully')
except Exception as e:
    print(f'✗ Camera test failed: {e}')
    print('Try: sudo raspi-config -> Interface Options -> Camera -> Enable')
"

# Test basic server dependencies
echo "Testing server dependencies..."
python3 -c "
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
try:
    import socket, threading, os
    from datetime import datetime
    from pathlib import Path
    from time import sleep
    print('✓ Basic Python modules working')
    
    # Test yaml specifically
    try:
        import yaml
        print('✓ yaml module working')
    except ImportError:
        print('✗ yaml module still not found')
        print('Try: sudo apt install python3-yaml')
        exit(1)
        
    print('✓ All basic server dependencies working')
except Exception as e:
    print(f'✗ Server dependency test failed: {e}')
"

# Skip AprilTag test for now
echo "Skipping AprilTag test (not installed to avoid memory issues)"

echo ""
echo "=== Setup Complete ==="
echo "To run the camera server:"
echo "  source ur3_cam_env/bin/activate"
echo "  python3 solid_dosing_server"
echo ""
echo "Note: AprilTag detection not installed due to Pi Zero 2W memory limitations"
echo "To install AprilTag support later (if you have more memory/swap):"
echo "  source ur3_cam_env/bin/activate"
echo "  pip install pupil-apriltags"
echo ""
echo "If camera test failed, you may need to:"
echo "  1. Reboot the Pi (if camera was just enabled)"
echo "  2. Check camera cable connection"
echo "  3. Run: sudo raspi-config -> Interface Options -> Camera -> Enable"
