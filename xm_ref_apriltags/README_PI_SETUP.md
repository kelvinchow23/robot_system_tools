# Pi Zero 2W Setup Instructions

## Prerequisites
- Raspberry Pi Zero 2W with Raspberry Pi OS (64-bit recommended)
- Pi Camera module connected via CSI
- Python 3.8+ (comes with Raspberry Pi OS)
- Internet connection for package installation

## System Dependencies

First, update your system and install required system packages:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies for camera and image processing
sudo apt install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    libcamera-dev \
    libcamera-apps \
    python3-libcamera \
    python3-kms++ \
    python3-pyqt5 \
    python3-prctl \
    libatlas-base-dev \
    libjpeg-dev \
    libtiff5-dev \
    libpng-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libgtk2.0-dev \
    libcanberra-gtk-module \
    libxvidcore-dev \
    libx264-dev \
    python3-opencv

# Enable camera interface
sudo raspi-config
# Navigate to: Interface Options -> Camera -> Enable
```

## Python Virtual Environment Setup

```bash
# Navigate to your project directory
cd /home/pi/xm_ref_apriltags

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python requirements
pip install -r requirements.txt
```

## Camera Testing

Test your camera setup:

```bash
# Test camera with libcamera (should work without errors)
libcamera-hello --timeout 2000

# Test camera with Python
python3 -c "from picamera2 import Picamera2; cam = Picamera2(); print('Camera OK')"
```

## Running the Server

```bash
# Activate virtual environment
source venv/bin/activate

# Run the camera server
python3 solid_dosing_server
```

## Network Configuration

The server will automatically detect its IP address. Make note of the IP shown in the logs for client configuration.

## Troubleshooting

### Common Issues:

1. **Camera not detected:**
   ```bash
   # Check camera connection
   libcamera-hello --list-cameras
   ```

2. **Permission errors:**
   ```bash
   # Add user to video group
   sudo usermod -a -G video $USER
   # Logout and login again
   ```

3. **Memory issues on Pi Zero 2W:**
   ```bash
   # Increase GPU memory split
   sudo raspi-config
   # Advanced Options -> Memory Split -> Set to 128
   ```

4. **OpenCV installation issues:**
   ```bash
   # If OpenCV fails to install, try system package
   sudo apt install python3-opencv
   ```

5. **NumPy/SciPy compilation errors:**
   ```bash
   # Install pre-compiled versions
   pip install --only-binary=all numpy scipy
   ```

## Performance Optimization

For better performance on Pi Zero 2W:

```bash
# Increase swap size if needed
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Set CONF_SWAPSIZE=1024
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

## Auto-start Service (Optional)

To run the camera server automatically on boot:

```bash
# Create systemd service
sudo nano /etc/systemd/system/camera-server.service
```

Add this content:
```ini
[Unit]
Description=Pi Camera Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/xm_ref_apriltags
Environment=PATH=/home/pi/xm_ref_apriltags/venv/bin
ExecStart=/home/pi/xm_ref_apriltags/venv/bin/python solid_dosing_server
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable camera-server.service
sudo systemctl start camera-server.service

# Check status
sudo systemctl status camera-server.service
```
