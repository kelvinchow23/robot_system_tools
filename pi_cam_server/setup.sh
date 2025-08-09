#!/bin/bash
# Pi Camera Server Setup Script
# Run this script on Raspberry Pi to setup camera server

set -e  # Exit on any error

echo "🍓 Setting up Pi Camera Server"
echo "================================"

# Check if running on Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    echo "   This script is designed for Pi deployment"
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo "📦 Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install system dependencies
echo "🔧 Installing system dependencies..."
sudo apt install -y python3-pip python3-venv python3-dev
sudo apt install -y libcamera-apps libcamera-dev
sudo apt install -y python3-libcamera python3-kms++

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python packages..."
pip install -r requirements.txt

# Copy source files from parent directory
echo "📋 Copying source files..."
if [ -d "../src" ]; then
    cp -r ../src .
    echo "✅ Source files copied"
else
    echo "⚠️  Source directory not found at ../src"
    echo "   Make sure you're running this from the pi_cam_server directory"
fi

# Copy config if it exists
if [ -f "../camera_config.yaml" ]; then
    cp ../camera_config.yaml .
    echo "✅ Configuration copied"
fi

# Create project directories
mkdir -p photos logs

# Create systemd service
echo "⚙️  Creating systemd service..."
sudo tee /etc/systemd/system/camera-server.service > /dev/null <<EOF
[Unit]
Description=Robot Camera Server
After=network.target
Wants=network.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/home/pi/robot_camera
Environment=PYTHONPATH=/home/pi/robot_camera
ExecStart=/home/pi/robot_camera/venv/bin/python /home/pi/robot_camera/camera_server.py --daemon
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Enable camera
echo "📷 Enabling camera interface..."
sudo raspi-config nonint do_camera 0

# Set hostname (optional)
read -p "🏷️  Set hostname to 'ur3-picam-apriltag'? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "ur3-picam-apriltag" | sudo tee /etc/hostname
    sudo sed -i 's/127.0.1.1.*/127.0.1.1\tur3-picam-apriltag/' /etc/hosts
    echo "✅ Hostname set to ur3-picam-apriltag"
fi

# Create photos directory
mkdir -p photos

# Set permissions
chmod +x camera_server.py

echo ""
echo "✅ Pi Camera Server setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Reboot Pi: sudo reboot"
echo "   2. Test camera: python camera_server.py"
echo "   3. Enable service: sudo systemctl enable camera-server"
echo "   4. Start service: sudo systemctl start camera-server"
echo ""
echo "🔧 Service management:"
echo "   Status: sudo systemctl status camera-server"
echo "   Logs:   sudo journalctl -u camera-server -f"
echo "   Stop:   sudo systemctl stop camera-server"
echo ""
