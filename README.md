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

### Robot Vision Workflow

```python
# Full workflow with AprilTag detection
python test_robot_vision.py
```

### Camera Calibration

For accurate AprilTag pose estimation:

```bash
# 1. Print the calibration chessboard (8x6 external corners, 30mm squares)
# Use: camera_calibration/Calibration chessboard (US Letter).pdf
# Print at 100% scale, mount on rigid surface

# 2. Capture 10 calibration photos
cd camera_calibration
python capture_calibration_photos.py

# 3. Calculate camera intrinsics from photos
python calculate_camera_intrinsics.py

# This creates camera_calibration.yaml in the camera_calibration directory
```

### AprilTag Detection

```bash
# Single detection with pose estimation
python test_apriltag_detection.py

# Continuous detection mode
python test_apriltag_detection.py --continuous

# Custom tag size (measure your printed tags in mm)
python test_apriltag_detection.py --tag-size 50.0
```

## 📁 File Structure

```
robot_system_tools/
├── pi_cam_server/           # Pi camera server
│   ├── camera_server.py     # Main server application
│   ├── camera_config.yaml   # Server configuration
│   ├── setup.sh            # Pi setup script
│   ├── install.sh           # One-line installer
│   └── requirements.txt     # Python dependencies
├── camera_calibration/      # Camera calibration workflow
│   ├── capture_calibration_photos.py  # Capture calibration images
│   ├── calculate_camera_intrinsics.py # Calculate intrinsics
│   ├── camera_calibration.yaml        # Generated camera intrinsics
│   ├── Calibration chessboard (US Letter).pdf  # Chessboard pattern
│   ├── QUALITY_GUIDE.md               # Quality metrics guide
│   └── README.md                      # Calibration documentation
├── handeye_calibration/     # Hand-eye calibration for robots
│   ├── collect_handeye_data.py        # Data collection for UR robots
│   ├── calculate_handeye_calibration.py  # Solve calibration problem
│   ├── coordinate_transformer.py      # Runtime coordinate transformation
│   └── README.md                      # Hand-eye calibration guide
├── ur_robot_interface.py    # Universal Robots interface via RTDE
├── picam.py                 # Pi camera client library
├── client_config.yaml       # Client configuration
├── test_camera_capture.py   # Basic camera test
├── test_apriltag_detection.py  # AprilTag detection and pose estimation
├── test_robot_vision.py     # Complete vision system test
└── README.md               # This file
```

## 🤖 Robot Integration

### Hand-Eye Calibration for UR Robots

For robot manipulation applications, perform hand-eye calibration to transform camera coordinates to robot base frame:

```bash
# Step 1: Collect calibration data
cd handeye_calibration
python collect_handeye_data.py --robot-ip 192.168.1.100 --auto-poses

# Step 2: Calculate hand-eye transformation
python calculate_handeye_calibration.py --input handeye_data_*.json --validate

# Step 3: Use for coordinate transformation
python coordinate_transformer.py --calibration handeye_calibration_*.yaml
```

### Runtime Robot Vision

```python
from ur_robot_interface import URRobotInterface
from handeye_calibration.coordinate_transformer import CoordinateTransformer

# Initialize robot and transformer
robot = URRobotInterface('192.168.1.100')
transformer = CoordinateTransformer('handeye_calibration.yaml')

# Detect AprilTag and transform to robot coordinates
current_robot_pose = robot.get_tcp_pose()
robot_detection = transformer.transform_apriltag_detection(
    apriltag_detection, current_robot_pose
)

# Get tag position in robot base frame
tag_position = robot_detection['robot_frame_pose']['translation_vector']
```

See `handeye_calibration/README.md` for detailed instructions.

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
