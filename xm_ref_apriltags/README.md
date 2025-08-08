# UR3 Robot Arm Camera System

Distributed camera system for robot vision with separated server (Pi Zero 2W) and client (robot computer) components.

## Architecture

```
┌─────────────────────────┐      ┌─────────────────────────────┐
│     Pi Zero 2W          │      │    Robot Computer           │
│    (Camera Server)      │ ◄──► │    (Vision Client)          │
│                         │      │                             │
│  📸 Camera Capture      │      │  🎯 AprilTag Detection      │
│  🌐 Network Serving     │      │  📐 Camera Calibration      │
│  ⚙️  Minimal Setup      │      │  🧠 Computer Vision         │
│                         │      │                             │
│  server/                │      │  client/                    │
│  ├─ camera_server.py    │      │  ├─ camera_client.py        │
│  ├─ config.yaml         │      │  ├─ detect_apriltags.py     │
│  └─ requirements.txt    │      │  ├─ calibrate_camera.py     │
│                         │      │  └─ requirements.txt        │
└─────────────────────────┘      └─────────────────────────────┘
```

## Quick Start

### 1. Setup Camera Server (Pi Zero 2W)
```bash
cd server/
./setup.sh
python3 camera_server.py
```

### 2. Setup Vision Client (Robot Computer)
```bash
cd client/
./setup.sh
python robot_vision_workflow.py
```

## Components

### 📸 Camera Server (`server/`)
- **Lightweight Pi Zero 2W setup**
- **Photo capture and serving**
- **Minimal dependencies**
- **Network accessible camera**

[Server Documentation →](server/README.md)

### 🎯 Vision Client (`client/`)
- **Full computer vision stack**
- **AprilTag detection with 3D pose**
- **Camera calibration tools**
- **Robot integration ready**

[Client Documentation →](client/README.md)

## Benefits of Split Architecture

### 🚀 Performance
- **Pi focuses on camera** - No heavy CV processing
- **Client handles compute** - Full processing power for vision
- **Parallel operation** - Multiple clients can connect

### 🔧 Maintainability  
- **Separate concerns** - Camera vs. vision logic
- **Independent updates** - Update client/server separately
- **Clear interfaces** - Simple network protocol

### 🎯 Flexibility
- **Multiple clients** - Robot, laptop, monitoring systems
- **Different platforms** - Windows, Linux, embedded systems
- **Scalable processing** - Add more vision clients as needed

## Network Protocol

Simple TCP-based photo request/response:

1. **Client connects** to `ur3-picam-apriltag:2222`
2. **Client sends** `"TAKE_PHOTO"`
3. **Server captures** photo and sends:
   - Filename (with length prefix)
   - File size (with length prefix)  
   - Image data (in chunks)
4. **Client confirms** filename and size
5. **Connection closes**

## Configuration

Both client and server share the same `config.yaml` format:

```yaml
# Network settings
network:
  server_port: 2222
  hostname: "ur3-picam-apriltag"

# Camera settings
camera:
  focus_mode: "continuous"
  horizontal_flip: true
  vertical_flip: true

# File settings  
files:
  photo_directory: "photos"
  download_directory: "downloaded_photos"
```

## Robot Integration Examples

### Basic Photo Capture
```python
from client.camera_client import CameraClient

client = CameraClient()
photo_path = client.request_photo()
print(f"Photo saved: {photo_path}")
```

### AprilTag Detection
```python
from client.detect_apriltags import AprilTagDetector

detector = AprilTagDetector()
results = detector.capture_and_detect()

for detection in results['detections']:
    print(f"Tag {detection['tag_id']}: {detection['distance_cm']:.1f}cm")
```

### Complete Vision Pipeline
```python
from client.robot_vision_workflow import *

# 1. Calibrate camera (one-time setup)
run_calibration()

# 2. In robot control loop
def get_target_position():
    results = capture_and_detect()
    if results:
        return results['detections'][0]['pose_translation']
    return None

# 3. Use in robot
target_pos = get_target_position()
if target_pos:
    robot.move_to_position(target_pos)
```

## File Structure

```
xm_ref_apriltags/
├── README.md                    # This file
├── server/                      # Pi Zero 2W camera server
│   ├── camera_server.py
│   ├── config.yaml
│   ├── requirements.txt
│   └── setup.sh
├── client/                      # Robot computer vision client
│   ├── camera_client.py
│   ├── detect_apriltags.py
│   ├── calibrate_camera.py
│   ├── robot_vision_workflow.py
│   ├── requirements.txt
│   └── setup.sh
└── archive/                     # Legacy files
    └── (old implementations)
```

## Troubleshooting

### Connection Issues
```bash
# Test server from client machine
ping ur3-picam-apriltag
telnet ur3-picam-apriltag 2222

# Check server status on Pi
python3 server/camera_server.py
```

### Camera Issues
```bash
# On Pi, test camera
python3 -c "from picamera2 import Picamera2; cam = Picamera2(); cam.start(); cam.capture_file('test.jpg')"
```

### Vision Issues
```bash
# On client, test detection
python client/detect_apriltags.py
```

## Development

### Adding New Features
- **Server-side**: Add to `server/camera_server.py`
- **Client-side**: Add to `client/` directory
- **Shared**: Update `config.yaml` and utilities

### Network Protocol Extensions
Extend the simple protocol in `network_utils.py` for new commands beyond `TAKE_PHOTO`.

## Hardware Requirements

### Camera Server (Pi Zero 2W)
- **RAM**: 512MB (minimal OS recommended)
- **Storage**: 8GB+ microSD card
- **Camera**: Pi Camera Module v1/v2/v3
- **Network**: WiFi or Ethernet

### Vision Client
- **RAM**: 4GB+ (for computer vision)
- **CPU**: Multi-core recommended
- **GPU**: Optional (OpenCV can use)
- **Storage**: Varies by image storage needs
