#!/bin/bash
# Complete Fresh Raspberry Pi Camera Server Setup
# Run this on a fresh Raspberry Pi OS installation

set -e  # Exit on any error

echo "🍓 Fresh Raspberry Pi Camera Server Setup"
echo "========================================"
echo ""

# Check if running on Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "❌ This script must be run on a Raspberry Pi"
    exit 1
fi

echo "📋 This script will:"
echo "   1. Update system packages"
echo "   2. Enable camera interface"
echo "   3. Clone robot system tools repository"
echo "   4. Setup camera server with virtual environment"
echo "   5. Configure systemd service"
echo "   6. Test camera functionality"
echo ""

read -p "Continue with fresh setup? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Setup cancelled"
    exit 0
fi

echo ""
echo "🔄 Step 1: Updating system packages..."
sudo apt update
sudo apt upgrade -y

echo ""
echo "📷 Step 2: Enabling camera interface..."
sudo raspi-config nonint do_camera 0

echo ""
echo "🔧 Step 3: Installing system dependencies..."
sudo apt install -y python3-pip python3-venv python3-dev git
sudo apt install -y libcamera-apps libcamera-dev
sudo apt install -y python3-libcamera python3-kms++
sudo apt install -y libcap-dev libarchive-dev

echo ""
echo "📦 Step 4: Cloning repository..."
cd $HOME
if [ -d "robot_system_tools" ]; then
    echo "   Repository already exists, updating..."
    cd robot_system_tools
    git pull
else
    echo "   Cloning fresh repository..."
    git clone https://github.com/kelvinchow23/robot_system_tools.git
    cd robot_system_tools
fi

echo ""
echo "🐍 Step 5: Setting up camera server..."
cd pi_cam_server

# Create virtual environment
echo "   Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "   Installing Python packages..."
pip install -r requirements.txt

# Create directories
mkdir -p photos logs

echo ""
echo "⚙️  Step 6: Creating systemd service..."
CURRENT_USER=$(whoami)
USER_HOME=$(eval echo "~$CURRENT_USER")
sudo tee /etc/systemd/system/camera-server.service > /dev/null <<EOF
[Unit]
Description=Robot Camera Server
After=network.target
Wants=network.target

[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$USER_HOME/robot_system_tools/pi_cam_server
Environment=PYTHONPATH=$USER_HOME/robot_system_tools/pi_cam_server
ExecStart=$USER_HOME/robot_system_tools/pi_cam_server/venv/bin/python $USER_HOME/robot_system_tools/pi_cam_server/camera_server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable camera-server

echo ""
echo "🧪 Step 7: Testing camera..."
echo "   Testing camera hardware..."
if libcamera-hello --list-cameras > /dev/null 2>&1; then
    echo "   ✅ Camera hardware detected"
else
    echo "   ❌ Camera hardware not detected"
    echo "   Check camera connection and reboot"
    exit 1
fi

echo ""
echo "🚀 Step 8: Starting camera server..."
sudo systemctl start camera-server

# Wait a moment for service to start
sleep 3

# Check service status
if sudo systemctl is-active --quiet camera-server; then
    echo "   ✅ Camera server started successfully"
else
    echo "   ❌ Camera server failed to start"
    echo "   Check logs: sudo journalctl -u camera-server -n 20"
    exit 1
fi

echo ""
echo "🏷️  Step 9: Optional hostname setup..."
read -p "Set hostname to 'ur3-picam-apriltag'? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "ur3-picam-apriltag" | sudo tee /etc/hostname > /dev/null
    sudo sed -i 's/127.0.1.1.*/127.0.1.1\tur3-picam-apriltag/' /etc/hosts
    echo "   ✅ Hostname set to ur3-picam-apriltag"
    HOSTNAME_CHANGED=true
else
    HOSTNAME_CHANGED=false
fi

echo ""
echo "✅ Fresh Pi Camera Server Setup Complete!"
echo "========================================"
echo ""
echo "📋 Summary:"
echo "   📷 Camera hardware: Enabled and tested"
echo "   🐍 Python environment: Created with dependencies"
echo "   ⚙️  Systemd service: Enabled and running"
echo "   🌐 Server: Listening on port 2222"
echo ""
echo "🔧 Useful commands:"
echo "   Status: sudo systemctl status camera-server"
echo "   Logs:   sudo journalctl -u camera-server -f"
echo "   Stop:   sudo systemctl stop camera-server"
echo "   Start:  sudo systemctl start camera-server"
echo ""
echo "🌐 Network info:"
PI_IP=$(hostname -I | awk '{print $1}')
echo "   Pi IP address: $PI_IP"
echo "   Test from PC: python camera_client.py $PI_IP --test"
echo ""

if [ "$HOSTNAME_CHANGED" = true ]; then
    echo "⚠️  Reboot recommended for hostname change:"
    echo "   sudo reboot"
else
    echo "🎯 Ready to use! Test from your PC:"
    echo "   python camera_client.py $PI_IP --test"
fi

echo ""
