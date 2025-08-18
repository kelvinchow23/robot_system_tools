# Robot Camera System

Simple Raspberry Pi camera server for robot vision applications using system packages only.

## 🚀 Quick Setup

### One-Command Install (Fresh Raspberry Pi)

For a fresh Debian Bookworm image, run this single command:

```bash
curl -sSL https://raw.githubusercontent.com/kelvinchow23/robot_system_tools/master/pi_cam_server/install.sh | bash
```

This will:
- Install git if needed
- Clone the repository to `~/robot_system_tools` (works with any user)
- Install system dependencies (no pip/venv) 
- Enable camera interface
- Setup systemd service for current user
- Configure auto-start on boot

### Manual Install (if preferred)

```bash
# Clone repository
git clone https://github.com/kelvinchow23/robot_system_tools.git
cd robot_system_tools/pi_cam_server

# Run setup
chmod +x setup.sh
./setup.sh
```

## 📋 After Installation

### Testing the Server
```bash
# Test manually (on Pi)
cd ~/robot_system_tools/pi_cam_server
python3 camera_server.py

# Test from client computer
python3 test_client.py <PI_IP>

# Or use the PiCam class
python3 -c "from picam import test_camera; print('✅ Connected' if test_camera('<PI_IP>') else '❌ Failed')"
```

### Service Management  
```bash
# Check status
sudo systemctl status camera-server

# View logs
sudo journalctl -u camera-server -f

# Start/stop/restart
sudo systemctl start camera-server
sudo systemctl stop camera-server  
sudo systemctl restart camera-server
```

## 📋 What You Get

### Pi Camera Server (`pi_cam_server/`)
- Standalone camera server for Raspberry Pi
- Runs on port 2222 by default
- Auto-starts on boot via systemd
- Uses system packages only (no virtual environments)
- Photos saved to `pi_cam_server/photos/`

### Client Tools
- `picam.py` - Simple PiCam class for easy camera operations
- `camera_client.py` - Lower-level camera client (use PiCam instead)
- `test_client.py` - Simple connection test
- `test_robot_vision.py` - Complete workflow test using PiCam

### Using the PiCam Class
```python
from picam import PiCam, PiCamConfig

# Simple usage
camera = PiCam()
if camera.test_connection():
    photo_path = camera.capture_photo()
    print(f"Photo saved: {photo_path}")

# With custom config
config = PiCamConfig(hostname="your-pi-ip", port=2222)
camera = PiCam(config)
photo_path = camera.capture_photo("my_photo.jpg")
```
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
