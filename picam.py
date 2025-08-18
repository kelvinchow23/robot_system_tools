#!/usr/bin/env python3
"""
Simple Pi Camera Class
Focused camera functionality for robot vision scripts
"""

import socket
import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any

class PiCamConfig:
    """Simple camera configuration"""
    def __init__(self, hostname="raspberrypi.local", port=2222, download_dir="photos"):
        self.hostname = hostname
        self.port = port
        self.download_dir = download_dir
        self.timeout = 10
        
        # Create download directory
        Path(self.download_dir).mkdir(exist_ok=True)
    
    @classmethod
    def from_yaml(cls, config_path: str = "pi_cam_server/camera_config.yaml"):
        """Load config from YAML file"""
        if not os.path.exists(config_path):
            return cls()
        
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Extract server config
        server_config = data.get('server', {})
        
        return cls(
            hostname=server_config.get('host', 'raspberrypi.local'),
            port=server_config.get('port', 2222),
            download_dir=data.get('photos', {}).get('directory', 'photos')
        )

class PiCam:
    """
    Simple Pi Camera Client
    
    Provides basic camera operations for robot vision scripts:
    - Connect to Pi camera server
    - Capture photos
    - Test connections
    """
    
    def __init__(self, config: Optional[PiCamConfig] = None):
        """Initialize camera client"""
        self.config = config or PiCamConfig()
        
    def test_connection(self) -> bool:
        """Test if camera server is accessible"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.config.timeout)
            result = sock.connect_ex((self.config.hostname, self.config.port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def capture_photo(self, filename: Optional[str] = None) -> Optional[str]:
        """
        Capture a photo from Pi camera server
        
        Args:
            filename: Optional custom filename
            
        Returns:
            Path to saved photo or None if failed
        """
        try:
            # Connect to server
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.config.timeout)
            sock.connect((self.config.hostname, self.config.port))
            
            # Send photo request
            sock.send("TAKE_PHOTO".encode('utf-8'))
            
            # Receive filename
            filename_length = int.from_bytes(sock.recv(4), byteorder='big')
            received_filename = sock.recv(filename_length).decode('utf-8')
            
            # Send filename confirmation
            sock.send(len(received_filename).to_bytes(4, byteorder='big'))
            sock.send(received_filename.encode('utf-8'))
            
            # Receive file size
            file_size = int.from_bytes(sock.recv(8), byteorder='big')
            
            # Send file size confirmation
            sock.send(file_size.to_bytes(8, byteorder='big'))
            
            # Receive file data
            if filename:
                file_path = Path(self.config.download_dir) / filename
            else:
                file_path = Path(self.config.download_dir) / received_filename
            
            received_size = 0
            with open(file_path, 'wb') as f:
                while received_size < file_size:
                    remaining = file_size - received_size
                    chunk_size = min(2048, remaining)
                    chunk = sock.recv(chunk_size)
                    
                    if not chunk:
                        break
                    
                    f.write(chunk)
                    received_size += len(chunk)
            
            sock.close()
            
            if received_size == file_size:
                return str(file_path)
            else:
                return None
                
        except Exception as e:
            print(f"Photo capture failed: {e}")
            return None
    
    def get_latest_photo(self) -> Optional[str]:
        """Get the path to the latest photo in download directory"""
        photo_dir = Path(self.config.download_dir)
        if not photo_dir.exists():
            return None
        
        photo_files = list(photo_dir.glob("*.jpg")) + list(photo_dir.glob("*.jpeg"))
        if not photo_files:
            return None
        
        latest = max(photo_files, key=os.path.getctime)
        return str(latest)

# Convenience functions for quick usage
def capture_photo(hostname: str = "raspberrypi.local", port: int = 2222) -> Optional[str]:
    """Quick photo capture function"""
    config = PiCamConfig(hostname, port)
    camera = PiCam(config)
    return camera.capture_photo()

def test_camera(hostname: str = "raspberrypi.local", port: int = 2222) -> bool:
    """Quick connection test function"""
    config = PiCamConfig(hostname, port)
    camera = PiCam(config)
    return camera.test_connection()

# Example usage
if __name__ == "__main__":
    # Simple test
    camera = PiCam()
    
    print("Testing camera connection...")
    if camera.test_connection():
        print("✅ Connected to camera server")
        
        print("Capturing photo...")
        photo_path = camera.capture_photo()
        if photo_path:
            print(f"📸 Photo saved: {photo_path}")
        else:
            print("❌ Failed to capture photo")
    else:
        print("❌ Cannot connect to camera server")
