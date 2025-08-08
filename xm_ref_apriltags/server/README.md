# UR3 Robot Arm Camera Server (Pi Zero 2W)

Lightweight camera server for Pi Zero 2W that captures photos and serves them over the network.

## Features

- **Minimal dependencies** - Only camera and network libraries
- **Configurable camera settings** - Focus, transforms, exposure
- **Network photo serving** - TCP-based photo transfer
- **Threading support** - Multiple client connections
- **Clean logging** - Configurable log levels

## Quick Setup

### 1. Install Dependencies
```bash
./setup.sh
```

### 2. Configure (Optional)
Edit `config.yaml` to customize:
- Camera settings (focus mode, transforms)
- Network settings (port, buffer sizes)
- File paths and logging

### 3. Start Server
```bash
python3 camera_server.py
```

## Configuration

The server uses `config.yaml` for all settings:

```yaml
# Network Settings
network:
  server_port: 2222
  hostname: "ur3-picam-apriltag"

# Camera Settings  
camera:
  focus_mode: "continuous"  # auto, continuous, manual
  horizontal_flip: true
  vertical_flip: true

# File Settings
files:
  photo_directory: "photos"
```

## System Requirements

- **Hardware:** Pi Zero 2W with camera module
- **OS:** Raspberry Pi OS
- **Python:** 3.7+
- **System packages:** python3-picamera2, python3-libcamera

## Network Access

The server binds to `0.0.0.0:2222` and is accessible via:
- Pi IP address: `192.168.1.x:2222`
- Pi hostname: `ur3-picam-apriltag:2222`

## File Structure

```
server/
├── camera_server.py      # Main camera server
├── config.yaml          # Configuration
├── config_manager.py    # Config handling
├── network_utils.py     # Network utilities
├── requirements.txt     # Dependencies
├── setup.sh            # Installation script
└── photos/             # Captured photos (created automatically)
```

## Troubleshooting

**Camera not detected:**
```bash
# Enable camera interface
sudo raspi-config
# Interface Options > Camera > Enable
```

**Permission errors:**
```bash
# Add user to video group
sudo usermod -a -G video $USER
# Reboot required
```

**Port already in use:**
```bash
# Check what's using the port
sudo netstat -tulpn | grep 2222
# Kill process or change port in config.yaml
```

## Client Connection

From client machines, connect using:
```python
from camera_client import CameraClient
client = CameraClient()
photo = client.request_photo()
```

Or test with simple socket connection:
```bash
telnet ur3-picam-apriltag 2222
# Send: TAKE_PHOTO
```
