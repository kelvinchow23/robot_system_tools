#!/usr/bin/env python3
"""
Pi Camera Server - Standalone Application
Minimal camera server for Raspberry Pi deployment
"""

import socket
import threading
import time
import os
import yaml
import logging
import argparse
from pathlib import Path
from datetime import datetime

try:
    from picamera2 import Picamera2
    CAMERA_AVAILABLE = True
except ImportError:
    print("❌ picamera2 not available")
    CAMERA_AVAILABLE = False

class SimpleCameraConfig:
    """Simple camera configuration"""
    def __init__(self):
        self.server_port = 2222
        self.photo_directory = "photos"
        self.focus_mode = "auto"
        self.image_format = "jpeg"
        self.image_quality = 85

    @classmethod
    def from_yaml(cls, config_path):
        """Load config from YAML file"""
        config = cls()
        try:
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)
                if data:
                    for key, value in data.items():
                        if hasattr(config, key):
                            setattr(config, key, value)
        except Exception as e:
            print(f"⚠️  Could not load config from {config_path}: {e}")
        return config

class SimpleCameraServer:
    """Simple camera server for Pi"""
    
    def __init__(self, config=None):
        self.config = config or SimpleCameraConfig()
        self.server_socket = None
        self.running = False
        
        # Ensure photo directory exists
        Path(self.config.photo_directory).mkdir(exist_ok=True)
        
        # Initialize camera
        self.camera = None
        if CAMERA_AVAILABLE:
            try:
                self.camera = Picamera2()
                print("✅ Camera initialized")
            except Exception as e:
                print(f"❌ Camera initialization failed: {e}")
                self.camera = None
        else:
            print("❌ Camera not available")

    def take_photo(self) -> str:
        """Take a photo and return the filename"""
        if not self.camera:
            raise Exception("Camera not available")
        
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"capture_{timestamp}.jpg"
        filepath = Path(self.config.photo_directory) / filename
        
        try:
            # Start camera preview configuration
            config = self.camera.create_still_configuration()
            self.camera.configure(config)
            self.camera.start()
            
            # Capture image
            self.camera.capture_file(str(filepath))
            self.camera.stop()
            
            print(f"📸 Photo captured: {filename}")
            return str(filepath)
            
        except Exception as e:
            print(f"❌ Photo capture failed: {e}")
            raise

    def handle_client(self, client_socket, client_address):
        """Handle client connection"""
        try:
            print(f"📱 Client connected: {client_address}")
            
            # Receive command
            command = client_socket.recv(1024).decode().strip()
            print(f"📋 Command: {command}")
            
            if command == "CAPTURE":
                try:
                    photo_path = self.take_photo()
                    
                    # Send photo file
                    with open(photo_path, 'rb') as f:
                        photo_data = f.read()
                    
                    # Send response header
                    response = f"OK {len(photo_data)}\n".encode()
                    client_socket.send(response)
                    
                    # Send photo data
                    client_socket.send(photo_data)
                    print(f"📤 Sent {len(photo_data)} bytes")
                    
                except Exception as e:
                    error_msg = f"ERROR {str(e)}\n".encode()
                    client_socket.send(error_msg)
                    print(f"❌ Error: {e}")
            
            elif command == "TEST":
                response = "OK Camera server ready\n".encode()
                client_socket.send(response)
                print("✅ Test response sent")
            
            else:
                response = "ERROR Unknown command\n".encode()
                client_socket.send(response)
                print(f"❌ Unknown command: {command}")
                
        except Exception as e:
            print(f"❌ Client handling error: {e}")
        finally:
            client_socket.close()
            print(f"📱 Client disconnected: {client_address}")

    def start_server(self):
        """Start the camera server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.config.server_port))
            self.server_socket.listen(5)
            
            self.running = True
            print(f"🎥 Camera server listening on port {self.config.server_port}")
            print("   Ready for connections...")
            
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except Exception as e:
                    if self.running:
                        print(f"❌ Accept error: {e}")
                        
        except Exception as e:
            print(f"❌ Server start error: {e}")
        finally:
            self.stop_server()

    def stop_server(self):
        """Stop the camera server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        if self.camera:
            self.camera.close()
        print("🛑 Camera server stopped")

def setup_logging(log_level: str = "INFO"):
    """Setup logging for Pi deployment"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "camera_server.log"),
            logging.StreamHandler()
        ]
    )

def load_config():
    """Load configuration for Pi server"""
    config_paths = [
        "camera_config.yaml",
        "../camera_config.yaml",
        "/etc/camera_server/config.yaml"
    ]
    
    for config_path in config_paths:
        if os.path.exists(config_path):
            print(f"📝 Loading config from: {config_path}")
            return SimpleCameraConfig.from_yaml(config_path)
    
    print("📝 Using default configuration")
    return SimpleCameraConfig()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Pi Camera Server")
    parser.add_argument("--port", type=int, default=2222, help="Server port")
    parser.add_argument("--log-level", default="INFO", help="Log level")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Load configuration
    config = load_config()
    if args.port != 2222:
        config.server_port = args.port
    
    # Create and start server
    server = SimpleCameraServer(config)
    
    if not args.daemon:
        print("🎥 Pi Camera Server Starting")
        print("=" * 40)
        print(f"📡 Port: {config.server_port}")
        print(f"📁 Photos: {config.photo_directory}")
        print("📸 Ready to serve camera captures")
        print("Press Ctrl+C to stop")
        print()
    
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\n🛑 Stopping server...")
        server.stop_server()

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
