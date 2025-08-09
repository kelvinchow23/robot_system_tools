#!/bin/bash
# Deploy Pi Camera Server
# Usage: ./deploy_to_pi.sh <pi-ip-address>

set -e

if [ $# -ne 1 ]; then
    echo "Usage: $0 <pi-ip-address>"
    echo "Example: $0 192.168.1.100"
    exit 1
fi

PI_IP=$1
PI_USER="pi"
TARGET_DIR="/home/pi/robot_camera"

echo "🚀 Deploying camera server to Pi at $PI_IP"
echo "=" * 50

# Check if we can reach the Pi
echo "🔍 Testing connection to Pi..."
if ! ping -c 1 -W 1 $PI_IP > /dev/null 2>&1; then
    echo "❌ Cannot reach Pi at $PI_IP"
    echo "   Check IP address and network connection"
    exit 1
fi

echo "✅ Pi is reachable"

# Create target directory on Pi
echo "📁 Creating target directory on Pi..."
ssh $PI_USER@$PI_IP "mkdir -p $TARGET_DIR"

# Copy pi_cam_server directory contents
echo "📋 Copying Pi server files..."
scp -r pi_cam_server/* $PI_USER@$PI_IP:$TARGET_DIR/

# Copy src directory
echo "📋 Copying source code..."
scp -r src $PI_USER@$PI_IP:$TARGET_DIR/

# Copy config if it exists
if [ -f "camera_config.yaml" ]; then
    echo "📋 Copying configuration..."
    scp camera_config.yaml $PI_USER@$PI_IP:$TARGET_DIR/
fi

# Make setup script executable
echo "🔧 Making setup script executable..."
ssh $PI_USER@$PI_IP "chmod +x $TARGET_DIR/setup.sh"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. SSH to Pi: ssh $PI_USER@$PI_IP"
echo "2. Run setup: cd $TARGET_DIR && ./setup.sh"
echo "3. Test server: python camera_server.py"
echo "4. Start service: sudo systemctl start camera-server"
echo ""
echo "Quick setup command:"
echo "ssh $PI_USER@$PI_IP 'cd $TARGET_DIR && ./setup.sh'"
