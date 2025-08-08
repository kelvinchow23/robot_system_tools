#!/bin/bash
# Setup script for UR3 Robot Arm Camera System on Pi Zero 2W
# This installs ONLY the camera server components (no heavy CV libraries)

echo "Setting up UR3 Camera Server on Pi Zero 2W..."

# Update system
echo "Updating system packages..."
sudo apt update

# Install minimal system dependencies for camera server
echo "Installing camera server dependencies..."
sudo apt install -y python3-picamera2 python3-libcamera python3-yaml python3-pip

# Install minimal Python dependencies for server
echo "Installing minimal Python packages for server..."
pip3 install PyYAML

echo "Server-only setup complete!"
echo ""
echo "📝 Note: This Pi is configured as a CAMERA SERVER only"
echo "   For AprilTag detection, install client requirements on your robot computer:"
echo "   pip install -r requirements_client.txt"
echo ""
echo "🚀 Usage:"
echo "   Start camera server:  python3 camera_server.py"
echo "   Test from client:     python3 camera_client.py"
echo ""
echo "🔧 Optional: Install full computer vision stack on Pi (not recommended for Pi Zero):"
echo "   sudo apt install python3-opencv python3-numpy python3-matplotlib python3-scipy"
echo "   pip3 install pupil-apriltags"
