# Robot Camera System

Simple, reliable Raspberry Pi camera server with easy Python client for robot vision applications.

## 🚀 Quick Start

### 1. Pi Camera Server Setup (One Command)

On your Raspberry Pi, run:
```bash
curl -sSL https://raw.githubusercontent.com/kelvinchow23/robot_system_tools/master/pi_cam_server/install.sh | bash
```

This will:
- Clone this repo
- Install all dependencies using system packages
- Set up camera server as systemd service
- Enable auto-start on boot
- Start the service immediately

### 2. Client Setup

On your client computer:

```bash
# Clone the repo
git clone https://github.com/kelvinchow23/robot_system_tools.git
cd robot_system_tools

# Configure your Pi's IP address
# Edit client_config.yaml and set your Pi's IP

# Test the connection
python test_camera_with_config.py
```

## 📱 Usage

### Simple Photo Capture

```python
from picam import PiCam, PiCamConfig

# Load config and capture photo
config = PiCamConfig.from_yaml("client_config.yaml")
cam = PiCam(config)
photo_path = cam.capture_photo()

if photo_path:
    print(f"Photo saved: {photo_path}")
```

### Camera Calibration for AprilTag Detection

For accurate AprilTag pose estimation, calibrate your camera first:

```bash
# 1. Generate a checkerboard pattern to print
python generate_checkerboard.py --width 10 --height 7 --output my_checkerboard.png

# 2. Print the checkerboard and mount on rigid surface

# 3. Run calibration (captures 20 images by default)
python calibrate_camera.py --images 20 --checkerboard 9 6 --square-size 25.0

# 4. Test the calibration
python test_calibration.py --capture-new
```

The calibration creates `camera_calibration.yaml` with camera intrinsics needed for pose estimation.

### Robot Vision Workflow

```python
# Full workflow with AprilTag detection
python test_robot_vision.py
```

## 📁 File Structure

```
robot_system_tools/
├── pi_cam_server/           # Pi camera server
│   ├── camera_server.py     # Main server application
│   ├── camera_config.yaml   # Server configuration
│   ├── setup.sh            # Pi setup script
│   ├── install.sh           # One-line installer
│   ├── requirements.txt     # Dependencies
│   ├── pi_led_controller.py # LED status indication
│   └── check_pi_leds.py     # Check available LEDs
├── picam.py                 # Client library
├── client_config.yaml       # Client configuration
├── test_camera_with_config.py  # Simple test
├── test_robot_vision.py     # Full workflow test
├── calibrate_camera.py      # Camera calibration routine
├── test_calibration.py      # Test calibration results
├── generate_checkerboard.py # Generate calibration pattern
└── README.md               # This file
```

## 💡 LED Status Indication

The camera server uses onboard LEDs to show status:

**Pi Zero 2W:**
- **🟢 Green LED (ACT)**: Main status indicator
  - Blinking: Server starting up
  - Steady: Server running normally  
  - Brief flash: Photo being captured
- **Error indication**: Uses available LED (mmc0 or default-on)
  - Blinking pattern indicates server errors

**Pi 5:**
- **🟢 Green LED (ACT)**: Server status  
- **🔴 Red LED (PWR)**: Error indication

Check available LEDs on your Pi:
```bash
# On the Pi, run:
python3 pi_cam_server/check_pi_leds.py
```

## ⚙️ Configuration

### Server Config (`pi_cam_server/camera_config.yaml`)
- Camera settings (resolution, rotation, format)
- Server port and directories
- Image quality settings

### Client Config (`client_config.yaml`)
```yaml
server:
  host: "192.168.1.100"  # Your Pi's IP
  port: 2222
client:
  download_directory: "photos"
  timeout: 10
```

## 🔧 Server Management

On the Pi:

```bash
# Check status
sudo systemctl status camera-server

# View logs
sudo journalctl -u camera-server -f

# Restart service
sudo systemctl restart camera-server

# Stop/start service
sudo systemctl stop camera-server
sudo systemctl start camera-server
```

## 🖥️ Supported Hardware

- **Raspberry Pi Zero 2W** ✅ Tested
- **Raspberry Pi 5** ✅ Tested  
- **Pi Camera v1/v2/v3** ✅ All supported
- **USB Cameras** ✅ Via libcamera

## 🏗️ Architecture

Simple TCP protocol on port 2222:
1. Client connects to Pi server
2. Sends "CAPTURE" command
3. Server captures photo and returns image data
4. Client saves photo locally

The system uses systemd for reliability and auto-start.

## 🔍 Troubleshooting

### Pi Server Issues
```bash
# Check service status
sudo systemctl status camera-server

# View error logs
sudo journalctl -u camera-server -n 50

# Test camera hardware
rpicam-still --timeout 1 -o test.jpg
```

### Client Connection Issues
```bash
# Test connectivity
ping your-pi-ip

# Check port access
telnet your-pi-ip 2222
```

### Common Solutions
- **Camera not found**: Enable camera with `sudo raspi-config`
- **Service won't start**: Check logs and camera hardware
- **Connection refused**: Verify Pi IP in `client_config.yaml`
- **Permission denied**: Ensure setup script ran with proper permissions

## 📄 License

MIT License
