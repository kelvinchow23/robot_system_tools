# Robot Camera System

Simple Raspberry Pi camera server for robot vision applications.

## 🚀 Quick Setup

### For Fresh Raspberry Pi (Debian Bookworm)

Run this single command on your fresh Pi:

```bash
curl -sSL https://raw.githubusercontent.com/kelvinchow23/robot_system_tools/master/setup_pi_camera.sh | bash
```

That's it! The script will:
- Install all dependencies
- Enable camera interface
- Setup Python environment
- Install and start camera server
- Configure auto-start service

### Manual Setup (if preferred)

```bash
# 1. Clone repository
git clone https://github.com/kelvinchow23/robot_system_tools.git
cd robot_system_tools

# 2. Run setup script
chmod +x setup_pi_camera.sh
./setup_pi_camera.sh
```

## 📋 What You Get

### Pi Camera Server (`pi_cam_server/`)
- Standalone camera server for Raspberry Pi
- Runs on port 2222 by default
- Auto-starts on boot via systemd
- Handles photo capture requests over network

### Client Tools
- `camera_client.py` - Basic camera client
- `picam.py` - Simple camera class for other scripts
- `test_robot_vision.py` - Complete workflow test
- `detect_apriltags.py` - AprilTag detection
- `calibrate_camera.py` - Camera calibration

## 🧪 Testing

After setup, test from your PC:

```bash
# Test connection
python camera_client.py <pi-ip> --test

# Capture photo
python camera_client.py <pi-ip>

# Complete robot vision workflow
python test_robot_vision.py <pi-ip>
```

## 🔧 Server Management

```bash
# Check status
sudo systemctl status camera-server

# View logs
sudo journalctl -u camera-server -f

# Restart service
sudo systemctl restart camera-server
```

## 📁 Project Structure

```
robot_system_tools/
├── pi_cam_server/          # Pi camera server
│   ├── camera_server.py    # Main server application
│   ├── requirements.txt    # Python dependencies
│   └── setup.sh           # Local setup script
├── setup_pi_camera.sh      # One-command Pi setup
├── camera_client.py        # Camera client
├── picam.py               # Simple camera class
├── test_robot_vision.py   # Workflow testing
├── detect_apriltags.py    # AprilTag detection
└── calibrate_camera.py    # Camera calibration
```

## 🎯 Simple Usage

```python
from picam import PiCam, PiCamConfig

# Connect to Pi camera
config = PiCamConfig(hostname='192.168.1.100')
camera = PiCam(config)

# Test connection
if camera.test_connection():
    # Capture photo
    photo_path = camera.capture_photo()
    print(f"Photo saved: {photo_path}")
```

---

**Ready to use in seconds!** 🍓📸
