#!/usr/bin/env python3
"""
Robot Camera System - Core Module
Camera functionality for robot_system_tools

This module provides camera capture and networking capabilities for robotic systems.
Supports both server-side (Pi) and client-side (PC) camera operations.
"""

import cv2
import numpy as np
import os
import socket
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CameraConfig:
    """Camera system configuration"""
    # Network settings
    hostname: str = "ur3-picam-apriltag"
    server_port: int = 2222
    buffer_size: int = 2048
    chunk_size: int = 1024
    connection_timeout: int = 10
    
    # Camera settings
    focus_mode: str = "continuous"
    manual_focus_position: int = 400
    horizontal_flip: bool = True
    vertical_flip: bool = True
    exposure_settle_time: float = 3.0
    
    # File settings
    photo_directory: str = "photos"
    download_directory: str = "downloaded_photos"
    photo_filename_prefix: str = "capture"
    
    @classmethod
    def from_yaml(cls, config_path: str) -> 'CameraConfig':
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            return cls(
                hostname=config_data.get('network', {}).get('hostname', cls.hostname),
                server_port=config_data.get('network', {}).get('server_port', cls.server_port),
                buffer_size=config_data.get('network', {}).get('buffer_size', cls.buffer_size),
                chunk_size=config_data.get('network', {}).get('chunk_size', cls.chunk_size),
                focus_mode=config_data.get('camera', {}).get('focus_mode', cls.focus_mode),
                manual_focus_position=config_data.get('camera', {}).get('manual_focus_position', cls.manual_focus_position),
                horizontal_flip=config_data.get('camera', {}).get('horizontal_flip', cls.horizontal_flip),
                vertical_flip=config_data.get('camera', {}).get('vertical_flip', cls.vertical_flip),
                exposure_settle_time=config_data.get('camera', {}).get('exposure_settle_time', cls.exposure_settle_time),
                photo_directory=config_data.get('files', {}).get('photo_directory', cls.photo_directory),
                download_directory=config_data.get('client', {}).get('download_directory', cls.download_directory),
                photo_filename_prefix=config_data.get('files', {}).get('photo_filename_prefix', cls.photo_filename_prefix),
                connection_timeout=config_data.get('client', {}).get('connection_timeout', cls.connection_timeout),
            )
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return cls()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return cls()

class CameraServer:
    """
    Camera server for Pi Zero 2W
    Handles camera capture and serves photos over network
    """
    
    def __init__(self, config: Optional[CameraConfig] = None):
        self.config = config or CameraConfig()
        self.camera = None
        self._setup_camera()
        self._setup_directories()
        
    def _setup_camera(self):
        """Initialize Pi camera"""
        try:
            from picamera2 import Picamera2
            self.camera = Picamera2()
            
            # Configure camera
            camera_config = self.camera.create_still_configuration(
                main={"size": (4608, 2592)},
                transform=self._get_transform()
            )
            self.camera.configure(camera_config)
            
            # Set focus mode
            if self.config.focus_mode == "manual":
                self.camera.set_controls({
                    "AfMode": 0,  # Manual focus
                    "LensPosition": self.config.manual_focus_position / 1000.0
                })
            elif self.config.focus_mode == "continuous":
                self.camera.set_controls({"AfMode": 2})  # Continuous AF
            else:  # auto
                self.camera.set_controls({"AfMode": 1})  # Auto focus
                
            self.camera.start()
            logger.info("Camera initialized successfully")
            
        except ImportError:
            logger.error("picamera2 not available - run on Pi with camera")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize camera: {e}")
            raise
    
    def _get_transform(self):
        """Get camera transform based on config"""
        from libcamera import Transform
        return Transform(
            hflip=self.config.horizontal_flip,
            vflip=self.config.vertical_flip
        )
    
    def _setup_directories(self):
        """Setup photo storage directories"""
        photos_dir = Path(self.config.photo_directory)
        photos_dir.mkdir(exist_ok=True)
        logger.info(f"Photos directory: {photos_dir.absolute()}")
    
    def capture_photo(self) -> str:
        """Capture a photo and return the file path"""
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"{self.config.photo_filename_prefix}_{timestamp}.jpg"
        filepath = Path(self.config.photo_directory) / filename
        
        try:
            # Wait for auto-exposure to settle
            time.sleep(self.config.exposure_settle_time)
            
            # Capture photo
            self.camera.capture_file(str(filepath))
            logger.info(f"Photo captured: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to capture photo: {e}")
            raise
    
    def start_server(self):
        """Start the camera server"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind(('0.0.0.0', self.config.server_port))
            server_socket.listen(1)
            logger.info(f"Camera server listening on port {self.config.server_port}")
            
            while True:
                try:
                    client_socket, address = server_socket.accept()
                    logger.info(f"Client connected from {address}")
                    self._handle_client(client_socket)
                    
                except KeyboardInterrupt:
                    logger.info("Server shutdown requested")
                    break
                except Exception as e:
                    logger.error(f"Error handling client: {e}")
                    
        finally:
            server_socket.close()
            if self.camera:
                self.camera.stop()
            logger.info("Camera server stopped")
    
    def _handle_client(self, client_socket: socket.socket):
        """Handle client request for photo"""
        try:
            # Receive request
            request = client_socket.recv(self.config.buffer_size).decode('utf-8').strip()
            logger.info(f"Received request: {request}")
            
            if request == "CAPTURE_PHOTO":
                # Capture photo
                photo_path = self.capture_photo()
                
                # Send photo
                self._send_photo(client_socket, photo_path)
                logger.info("Photo sent successfully")
            else:
                error_msg = f"Unknown request: {request}"
                client_socket.send(f"ERROR: {error_msg}".encode('utf-8'))
                logger.warning(error_msg)
                
        except Exception as e:
            error_msg = f"Error processing request: {e}"
            try:
                client_socket.send(f"ERROR: {error_msg}".encode('utf-8'))
            except:
                pass
            logger.error(error_msg)
        finally:
            client_socket.close()
    
    def _send_photo(self, client_socket: socket.socket, photo_path: str):
        """Send photo file to client"""
        try:
            file_size = os.path.getsize(photo_path)
            filename = os.path.basename(photo_path)
            
            # Send file info
            file_info = f"{filename}:{file_size}"
            client_socket.send(file_info.encode('utf-8'))
            
            # Wait for acknowledgment
            ack = client_socket.recv(self.config.buffer_size).decode('utf-8')
            if ack != "ACK":
                raise Exception(f"Expected ACK, got: {ack}")
            
            # Send file data
            with open(photo_path, 'rb') as f:
                bytes_sent = 0
                while bytes_sent < file_size:
                    chunk = f.read(self.config.chunk_size)
                    if not chunk:
                        break
                    client_socket.send(chunk)
                    bytes_sent += len(chunk)
            
            logger.info(f"Sent {bytes_sent} bytes")
            
        except Exception as e:
            logger.error(f"Failed to send photo: {e}")
            raise

class CameraClient:
    """
    Camera client for PC
    Requests photos from camera server
    """
    
    def __init__(self, config: Optional[CameraConfig] = None):
        self.config = config or CameraConfig()
        self._setup_directories()
    
    def _setup_directories(self):
        """Setup download directories"""
        download_dir = Path(self.config.download_directory)
        download_dir.mkdir(exist_ok=True)
        logger.info(f"Download directory: {download_dir.absolute()}")
    
    def test_connection(self) -> bool:
        """Test connection to camera server"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.config.connection_timeout)
            result = sock.connect_ex((self.config.hostname, self.config.server_port))
            sock.close()
            
            if result == 0:
                logger.info(f"Server accessible at {self.config.hostname}:{self.config.server_port}")
                return True
            else:
                logger.error(f"Cannot connect to {self.config.hostname}:{self.config.server_port}")
                return False
                
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def request_photo(self) -> Optional[str]:
        """Request photo from camera server"""
        try:
            # Connect to server
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(self.config.connection_timeout)
            client_socket.connect((self.config.hostname, self.config.server_port))
            
            # Send request
            client_socket.send("CAPTURE_PHOTO".encode('utf-8'))
            
            # Receive file info
            file_info = client_socket.recv(self.config.buffer_size).decode('utf-8')
            
            if file_info.startswith("ERROR:"):
                logger.error(f"Server error: {file_info}")
                return None
            
            filename, file_size = file_info.split(':')
            file_size = int(file_size)
            
            # Send acknowledgment
            client_socket.send("ACK".encode('utf-8'))
            
            # Receive and save file
            download_path = Path(self.config.download_directory) / filename
            
            with open(download_path, 'wb') as f:
                bytes_received = 0
                while bytes_received < file_size:
                    chunk = client_socket.recv(min(self.config.chunk_size, file_size - bytes_received))
                    if not chunk:
                        break
                    f.write(chunk)
                    bytes_received += len(chunk)
            
            client_socket.close()
            
            if bytes_received == file_size:
                logger.info(f"Photo downloaded: {download_path}")
                return str(download_path)
            else:
                logger.error(f"Incomplete download: {bytes_received}/{file_size} bytes")
                return None
                
        except Exception as e:
            logger.error(f"Failed to request photo: {e}")
            return None

# Convenience functions
def create_camera_server(config_path: Optional[str] = None) -> CameraServer:
    """Create camera server with optional config file"""
    config = CameraConfig.from_yaml(config_path) if config_path else CameraConfig()
    return CameraServer(config)

def create_camera_client(config_path: Optional[str] = None) -> CameraClient:
    """Create camera client with optional config file"""
    config = CameraConfig.from_yaml(config_path) if config_path else CameraConfig()
    return CameraClient(config)
