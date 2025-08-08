#!/usr/bin/env python3
"""
UR3 Robot Arm Camera Client
Clean implementation for requesting and receiving photos from camera server
"""

import socket
import os
from pathlib import Path

from config_manager import CameraConfig
from network_utils import setup_logger, send_file_name, receive_file_name, send_file_size, receive_file_size

class CameraClient:
    """Client for connecting to camera server"""
    
    def __init__(self):
        self.config = CameraConfig()
        self.logger = setup_logger(
            "CameraClient",
            self.config.get_logging_level(),
            self.config.log_format
        )
        
        self.hostname = self.config.hostname
        self.port = self.config.server_port
        
        # Create download directory
        self.download_dir = Path.cwd() / self.config.download_directory
        self.download_dir.mkdir(exist_ok=True)
        
        self.logger.info(f"Camera client initialized for {self.hostname}:{self.port}")
    
    def connect_to_server(self) -> socket.socket:
        """Establish connection to camera server"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.config.connection_timeout)
            sock.connect((self.hostname, self.port))
            self.logger.info(f"Connected to server {self.hostname}:{self.port}")
            return sock
        except Exception as e:
            self.logger.error(f"Failed to connect to server: {e}")
            return None
    
    def receive_photo(self, conn: socket.socket) -> str:
        """Receive photo from server"""
        try:
            # Receive filename
            filename = receive_file_name(conn, self.logger)
            if not filename:
                self.logger.error("Failed to receive filename")
                return None
            
            # Echo filename back
            if not send_file_name(conn, filename, self.logger):
                return None
            
            # Receive file size
            file_size = receive_file_size(conn, self.logger)
            if file_size is None:
                self.logger.error("Failed to receive file size")
                return None
            
            # Echo file size back
            if not send_file_size(conn, file_size, self.logger):
                return None
            
            # Receive file data
            file_path = self.download_dir / filename
            received_size = 0
            
            with open(file_path, 'wb') as f:
                while received_size < file_size:
                    remaining = file_size - received_size
                    chunk_size = min(self.config.chunk_size, remaining)
                    chunk = conn.recv(chunk_size)
                    
                    if not chunk:
                        break
                    
                    f.write(chunk)
                    received_size += len(chunk)
            
            if received_size == file_size:
                self.logger.info(f"Photo received successfully: {filename}")
                return str(file_path)
            else:
                self.logger.error(f"Incomplete file transfer: {received_size}/{file_size} bytes")
                return None
                
        except Exception as e:
            self.logger.error(f"Photo receive failed: {e}")
            return None
    
    def request_photo(self) -> str:
        """Request a photo from the server and save it locally"""
        conn = self.connect_to_server()
        if not conn:
            return None
        
        try:
            # Send photo request
            conn.send("TAKE_PHOTO".encode('utf-8'))
            self.logger.info("Photo request sent")
            
            # Receive photo
            photo_path = self.receive_photo(conn)
            return photo_path
            
        except Exception as e:
            self.logger.error(f"Photo request failed: {e}")
            return None
        finally:
            conn.close()
            self.logger.info("Connection closed")

def main():
    """Main function for standalone client usage"""
    client = CameraClient()
    
    print(f"Connecting to camera server at {client.hostname}:{client.port}")
    photo_path = client.request_photo()
    
    if photo_path:
        print(f"Photo saved to: {photo_path}")
    else:
        print("Failed to capture photo")

if __name__ == "__main__":
    main()
