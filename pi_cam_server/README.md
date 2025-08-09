# Pi Camera Server
Minimal camera server for Raspberry Pi deployment in robot systems.

## Quick Start

1. **Transfer to Pi:**
   ```bash
   # On your PC - copy pi_cam_server directory to Pi
   scp -r pi_cam_server/ pi@your-pi-ip:/home/pi/robot_camera
   ```

2. **Setup on Pi:**
   ```bash
   # SSH to Pi and run setup
   ssh pi@your-pi-ip
   cd /home/pi/robot_camera
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Test manually:**
   ```bash
   # Test the camera server
   python camera_server.py
   ```

4. **Start as service:**
   ```bash
   # Start systemd service (auto-starts on boot)
   sudo systemctl start camera-server
   sudo systemctl status camera-server
   ```

## Files

- `camera_server.py` - Standalone Pi camera server application
- `requirements.txt` - Pi-specific Python requirements
- `setup.sh` - Automated Pi setup script
- `camera-server.service` - Systemd service configuration
- `README.md` - This file

## Configuration

Place `camera_config.yaml` in the same directory for custom settings:

```yaml
server_port: 2222
photo_directory: "photos"
focus_mode: "auto"
image_format: "jpeg"
image_quality: 85
```

## Logging

Logs are written to:
- `logs/camera_server.log` (file)
- systemd journal (service mode)

View service logs:
```bash
sudo journalctl -u camera-server -f
```

## Troubleshooting

1. **Camera not detected:**
   ```bash
   # Check camera hardware
   libcamera-hello --list-cameras
   ```

2. **Port in use:**
   ```bash
   # Check what's using port 2222
   sudo netstat -tlnp | grep 2222
   ```

3. **Service won't start:**
   ```bash
   # Check service status and logs
   sudo systemctl status camera-server
   sudo journalctl -u camera-server -n 20
   ```

4. **Python import errors:**
   ```bash
   # Verify virtual environment and packages
   source venv/bin/activate
   pip list | grep -E "(picamera2|pyyaml)"
   ```
