#!/usr/bin/env python3
"""
UR3 Robot Arm Camera Server
Clean implementation for Pi Zero 2W camera control and photo capture
"""

import os
import sys
import socket
import threading
from datetime import datetime
from pathlib import Path
from time import sleep

# Add system packages path for picamera2 and libcamera
sys.path.insert(0, '/usr/lib/python3/dist-packages')

from picamera2 import Picamera2
from libcamera import controls, Transform

from config_manager import CameraConfig
from network_utils import setup_logger, send_file_name, receive_file_name, send_file_size, receive_file_size, get_local_ip

class CameraServer:
    """Camera server for UR3 robot arm system"""
    
    def __init__(self):
        self.config = CameraConfig()
        self.logger = setup_logger(
            "CameraServer", 
            self.config.get_logging_level(), 
            self.config.log_format
        )
        
        self.host = "0.0.0.0"  # Accept connections from any interface
        self.port = self.config.server_port
        self.server_ip = get_local_ip()
        
        self.cam = self._init_camera()
        self.camera_lock = threading.Lock()
        
        self.logger.info(f"Camera server initialized on {self.server_ip}:{self.port}")
    
    def _init_camera(self) -> Picamera2:
        """Initialize camera with configuration settings"""
        self.logger.info("Initializing camera...")
        
        cam = Picamera2(0)
        config = cam.create_still_configuration(
            transform=Transform(
                hflip=self.config.horizontal_flip,
                vflip=self.config.vertical_flip
            )
        )
        cam.configure(config)
        
        # Configure focus based on settings
        if 'AfMode' in cam.camera_controls:
            focus_mode = self.config.focus_mode.lower()
            
            if focus_mode == "continuous":
                cam.set_controls({"AfMode": controls.AfModeEnum.Continuous})
                self.logger.info("Camera focus set to Continuous Autofocus")
            elif focus_mode == "auto":
                cam.set_controls({"AfMode": controls.AfModeEnum.Auto})
                self.logger.info("Camera focus set to Auto")
            elif focus_mode == "manual":
                cam.set_controls({
                    "AfMode": controls.AfModeEnum.Manual,
                    "LensPosition": self.config.manual_focus_position
                })
                self.logger.info(f"Camera focus set to Manual (position: {self.config.manual_focus_position})")
            else:
                self.logger.warning(f"Unknown focus mode: {focus_mode}, using continuous")
                cam.set_controls({"AfMode": controls.AfModeEnum.Continuous})
        
        cam.start()
        self.logger.info("Camera initialized successfully")
        return cam
    
    def __del__(self):
        """Clean up camera resources"""
        if hasattr(self, 'cam'):
            self.cam.stop()
            self.cam.close()
            self.logger.info("Camera closed")
    
    def take_photo(self) -> str:
        """Take a photo and return the file path"""
        try:
            with self.camera_lock:
                # Create photo directory
                photo_dir = Path.cwd() / self.config.photo_directory
                photo_dir.mkdir(exist_ok=True)
                
                # Generate filename
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                filename = f"{self.config.photo_filename_prefix}_{timestamp}.jpg"
                img_path = photo_dir / filename
                
                # Wait for exposure to settle
                sleep(self.config.exposure_settle_time)
                
                # Capture photo
                self.cam.capture_file(str(img_path))
                self.logger.info(f"Photo captured: {filename}")
                
                return str(img_path)
                
        except Exception as e:
            self.logger.error(f"Photo capture failed: {e}")
            return None
    
    def send_photo(self, conn: socket.socket, img_path: str) -> bool:
        """Send photo to client over socket connection"""
        try:
            # Read image file
            with open(img_path, 'rb') as f:
                image_data = f.read()
            
            img_size = len(image_data)
            img_name = os.path.basename(img_path)
            
            # Send filename
            if not send_file_name(conn, img_name, self.logger):
                return False
            
            # Confirm filename
            echo_name = receive_file_name(conn, self.logger)
            if not echo_name or echo_name != img_name:
                self.logger.error("Filename confirmation failed")
                return False
            
            # Send file size
            if not send_file_size(conn, img_size, self.logger):
                return False
            
            # Confirm file size
            echo_size = receive_file_size(conn, self.logger)
            if echo_size != img_size:
                self.logger.error("File size confirmation failed")
                return False
            
            # Send file data in chunks
            offset = 0
            while offset < img_size:
                end = min(offset + self.config.chunk_size, img_size)
                chunk = image_data[offset:end]
                conn.sendall(chunk)
                offset = end
            
            self.logger.info("Photo sent successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Photo send failed: {e}")
            return False
    
    def handle_client(self, conn: socket.socket, addr: tuple):
        """Handle client connection"""
        self.logger.info(f"Handling client: {addr}")
        
        try:
            while True:
                msg = conn.recv(self.config.buffer_size).decode('utf-8').strip()
                if not msg:
                    break
                
                self.logger.info(f"Received command: {msg}")
                
                if msg == "TAKE_PHOTO":
                    image_path = self.take_photo()
                    if image_path:
                        self.send_photo(conn, image_path)
                    else:
                        self.logger.error("Failed to take photo")
                else:
                    self.logger.warning(f"Unknown command: {msg}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Client handling error: {e}")
        finally:
            conn.close()
            self.logger.info(f"Client {addr} disconnected")
    
    def start_server(self):
        """Start the camera server"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server.bind((self.host, self.port))
            server.listen(5)
            
            self.logger.info(f"Server listening on {self.host}:{self.port}")
            self.logger.info(f"Accessible via {self.server_ip}:{self.port}")
            
            while True:
                conn, addr = server.accept()
                self.logger.info(f"Connection from {addr}")
                
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(conn, addr),
                    daemon=True
                )
                client_thread.start()
                
        except KeyboardInterrupt:
            self.logger.info("Server shutdown requested")
        except Exception as e:
            self.logger.error(f"Server error: {e}")
        finally:
            server.close()
            self.logger.info("Server stopped")

if __name__ == "__main__":
    server = CameraServer()
    server.start_server()
