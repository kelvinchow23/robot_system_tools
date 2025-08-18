#!/bin/bash
# Raspberry Pi Camera Server Setup
# One-command setup for fresh Raspberry Pi OS (Debian Bookworm)
# Usage: curl -sSL https://raw.githubusercontent.com/kelvinchow23/robot_system_tools/master/setup_pi_camera.sh | bash

set -e

echo "🍓 Raspberry Pi Camera Server Setup"
echo "===================================="
echo ""

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "❌ This script must be run on a Raspberry Pi"
    exit 1
fi

echo "This script will:"
echo "  • Update system packages"
echo "  • Enable camera interface"
echo "  • Install dependencies"
echo "  • Download camera server code"
echo "  • Setup systemd service"
echo "  • Test camera functionality"
echo ""

read -p "Continue? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Setup cancelled"
    exit 0
fi

# Get current user info
CURRENT_USER=$(whoami)
USER_HOME=$(eval echo "~$CURRENT_USER")
INSTALL_DIR="$USER_HOME/pi_camera_server"

echo ""
echo "🔄 Updating system packages..."
sudo apt update -y
sudo apt upgrade -y

echo ""
echo "📷 Enabling camera interface..."
sudo raspi-config nonint do_camera 0

echo ""
echo "🔧 Installing dependencies..."
sudo apt install -y python3-pip python3-venv python3-dev git
sudo apt install -y libcamera-apps libcamera-dev
sudo apt install -y python3-libcamera python3-kms++
sudo apt install -y libcap-dev libarchive-dev

echo ""
echo "📦 Setting up camera server..."

# Create installation directory
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Create Python virtual environment
echo "   Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python packages
echo "   Installing Python packages..."
pip install --upgrade pip
pip install PyYAML>=6.0 picamera2>=0.3.0 opencv-python-headless>=4.5.0

# Create directories
mkdir -p photos logs

# Download camera server code
echo "   Creating camera server..."
cat > camera_server.py << 'EOF'
#!/usr/bin/env python3
"""Pi Camera Server - Standalone Application"""
import socket
import threading
import os
import yaml
import argparse
from pathlib import Path
from datetime import datetime

try:
    from picamera2 import Picamera2
    CAMERA_AVAILABLE = True
except ImportError:
    CAMERA_AVAILABLE = False

class CameraConfig:
    def __init__(self):
        self.server_port = 2222
        self.photo_directory = "photos"

class CameraServer:
    def __init__(self, config=None):
        self.config = config or CameraConfig()
        self.server_socket = None
        self.running = False
        Path(self.config.photo_directory).mkdir(exist_ok=True)
        
        self.camera = None
        if CAMERA_AVAILABLE:
            try:
                self.camera = Picamera2()
                print("✅ Camera initialized")
            except Exception as e:
                print(f"❌ Camera initialization failed: {e}")

    def take_photo(self):
        if not self.camera:
            raise Exception("Camera not available")
        
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"capture_{timestamp}.jpg"
        filepath = Path(self.config.photo_directory) / filename
        
        config = self.camera.create_still_configuration()
        self.camera.configure(config)
        self.camera.start()
        self.camera.capture_file(str(filepath))
        self.camera.stop()
        
        print(f"📸 Photo captured: {filename}")
        return str(filepath)

    def handle_client(self, client_socket, client_address):
        try:
            command = client_socket.recv(1024).decode().strip()
            
            if command == "CAPTURE":
                try:
                    photo_path = self.take_photo()
                    with open(photo_path, 'rb') as f:
                        photo_data = f.read()
                    response = f"OK {len(photo_data)}\n".encode()
                    client_socket.send(response)
                    client_socket.send(photo_data)
                except Exception as e:
                    error_msg = f"ERROR {str(e)}\n".encode()
                    client_socket.send(error_msg)
            
            elif command == "TEST":
                response = "OK Camera server ready\n".encode()
                client_socket.send(response)
            
            else:
                response = "ERROR Unknown command\n".encode()
                client_socket.send(response)
                
        except Exception as e:
            print(f"❌ Client handling error: {e}")
        finally:
            client_socket.close()

    def start_server(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.config.server_port))
            self.server_socket.listen(5)
            
            self.running = True
            print(f"🎥 Camera server listening on port {self.config.server_port}")
            
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                except Exception as e:
                    if self.running:
                        print(f"❌ Accept error: {e}")
        except Exception as e:
            print(f"❌ Server start error: {e}")
        finally:
            self.stop_server()

    def stop_server(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        if self.camera:
            self.camera.close()

def main():
    parser = argparse.ArgumentParser(description="Pi Camera Server")
    parser.add_argument("--port", type=int, default=2222, help="Server port")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    
    args = parser.parse_args()
    
    config = CameraConfig()
    if args.port != 2222:
        config.server_port = args.port
    
    server = CameraServer(config)
    
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\n🛑 Stopping server...")
        server.stop_server()

if __name__ == "__main__":
    main()
EOF

chmod +x camera_server.py

echo ""
echo "⚙️  Creating systemd service..."
sudo tee /etc/systemd/system/pi-camera-server.service > /dev/null <<EOF
[Unit]
Description=Pi Camera Server
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/camera_server.py --daemon
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable pi-camera-server

echo ""
echo "🧪 Testing camera hardware..."
if libcamera-hello --list-cameras > /dev/null 2>&1; then
    echo "   ✅ Camera hardware detected"
else
    echo "   ❌ Camera hardware not detected"
    echo "   Make sure camera is connected and enabled"
fi

echo ""
echo "🚀 Starting camera server..."
sudo systemctl start pi-camera-server
sleep 3

if sudo systemctl is-active --quiet pi-camera-server; then
    echo "   ✅ Camera server started successfully"
else
    echo "   ❌ Camera server failed to start"
    echo "   Check logs: sudo journalctl -u pi-camera-server -n 10"
fi

echo ""
echo "✅ Setup Complete!"
echo "=================="
echo ""
echo "📋 Installation summary:"
echo "   📁 Install directory: $INSTALL_DIR"
echo "   🎥 Service name: pi-camera-server"
echo "   📡 Default port: 2222"
echo ""
echo "🔧 Useful commands:"
echo "   sudo systemctl status pi-camera-server"
echo "   sudo systemctl restart pi-camera-server"
echo "   sudo journalctl -u pi-camera-server -f"
echo ""

PI_IP=$(hostname -I | awk '{print $1}')
echo "🎯 Test from your PC:"
echo "   python camera_client.py $PI_IP --test"
echo ""
