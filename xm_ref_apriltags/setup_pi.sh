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
    python3-opencv

# Check if camera is enabled
echo "Checking camera configuration..."
if ! grep -q "^camera_auto_detect=1" /boot/config.txt; then
    echo "Enabling camera interface..."
    echo "camera_auto_detect=1" | sudo tee -a /boot/config.txt
    echo "Camera enabled. Please reboot after setup completes."
fi

# Setup virtual environment
echo "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment and install packages
echo "Installing Python packages..."
source venv/bin/activate
pip install --upgrade pip

# Install packages with error handling
pip install -r requirements.txt || {
    echo "Some packages failed to install. Trying with system packages..."
    pip install picamera2 PyYAML python-dotenv pupil-apriltags scipy
}

# Test camera
echo "Testing camera setup..."
python3 -c "
try:
    from picamera2 import Picamera2
    print('✓ Picamera2 import successful')
    cam = Picamera2()
    print('✓ Camera initialization successful')
    cam.close()
except Exception as e:
    print(f'✗ Camera test failed: {e}')
"

# Test AprilTag detection
echo "Testing AprilTag detection..."
python3 -c "
try:
    from pupil_apriltags import Detector
    print('✓ AprilTag detector import successful')
    detector = Detector()
    print('✓ AprilTag detector initialization successful')
except Exception as e:
    print(f'✗ AprilTag test failed: {e}')
"

echo ""
echo "=== Setup Complete ==="
echo "To run the camera server:"
echo "  source venv/bin/activate"
echo "  python3 solid_dosing_server"
echo ""
echo "If camera test failed, you may need to:"
echo "  1. Reboot the Pi (if camera was just enabled)"
echo "  2. Check camera cable connection"
echo "  3. Run: sudo raspi-config -> Interface Options -> Camera -> Enable"
