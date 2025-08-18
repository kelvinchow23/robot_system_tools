#!/usr/bin/env python3
"""
Camera Client for Pi Camera Server
Connects to the camera server running on Raspberry Pi
"""
import socket
import argparse
import os
from datetime import datetime

class CameraClient:
    def __init__(self, server_ip, server_port=2222):
        self.server_ip = server_ip
        self.server_port = server_port
    
    def connect(self):
        """Establish connection to the camera server"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(30)  # 30 second timeout
            self.sock.connect((self.server_ip, self.server_port))
            return True
        except Exception as e:
            print(f"Failed to connect to {self.server_ip}:{self.server_port}")
            print(f"Error: {e}")
            return False
    
    def test_connection(self):
        """Test if the camera server is responding"""
        if not self.connect():
            return False
        
        try:
            # Send TEST command
            self.sock.send(b"TEST")
            response = self.sock.recv(1024).decode().strip()
            
            if response.startswith("OK"):
                print(f"✅ Camera server is responding")
                print(f"Server says: {response}")
                return True
            else:
                print(f"❌ Unexpected response: {response}")
                return False
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
        finally:
            self.sock.close()
    
    def capture_photo(self, save_path=None):
        """Capture a photo from the camera"""
        if not self.connect():
            return False
        
        try:
            # Send CAPTURE command
            self.sock.send(b"CAPTURE")
            
            # Read response header
            response_line = b""
            while b"\n" not in response_line:
                chunk = self.sock.recv(1)
                if not chunk:
                    break
                response_line += chunk
            
            response = response_line.decode().strip()
            
            if response.startswith("OK"):
                # Parse the response to get photo size
                parts = response.split()
                if len(parts) >= 2:
                    photo_size = int(parts[1])
                    print(f"📷 Receiving photo ({photo_size} bytes)...")
                    
                    # Receive the photo data
                    photo_data = b""
                    while len(photo_data) < photo_size:
                        chunk = self.sock.recv(min(4096, photo_size - len(photo_data)))
                        if not chunk:
                            break
                        photo_data += chunk
                    
                    # Save the photo
                    if save_path is None:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        save_path = f"capture_{timestamp}.jpg"
                    
                    with open(save_path, 'wb') as f:
                        f.write(photo_data)
                    
                    print(f"✅ Photo saved: {save_path}")
                    print(f"📁 File size: {len(photo_data)} bytes")
                    return True
                else:
                    print(f"❌ Invalid response format: {response}")
                    return False
            else:
                print(f"❌ Capture failed: {response}")
                return False
                
        except Exception as e:
            print(f"❌ Capture failed: {e}")
            return False
        finally:
            self.sock.close()

def main():
    parser = argparse.ArgumentParser(description="Camera Client for Pi Camera Server")
    parser.add_argument("server_ip", help="IP address of the camera server")
    parser.add_argument("--port", type=int, default=2222, help="Server port (default: 2222)")
    parser.add_argument("--test", action="store_true", help="Test connection to server")
    parser.add_argument("--capture", action="store_true", help="Capture a photo")
    parser.add_argument("--output", "-o", help="Output filename for captured photo")
    
    args = parser.parse_args()
    
    if not args.test and not args.capture:
        print("Please specify --test or --capture")
        parser.print_help()
        return
    
    client = CameraClient(args.server_ip, args.port)
    
    if args.test:
        print(f"🔍 Testing connection to {args.server_ip}:{args.port}...")
        success = client.test_connection()
        if not success:
            exit(1)
    
    if args.capture:
        print(f"📷 Capturing photo from {args.server_ip}:{args.port}...")
        success = client.capture_photo(args.output)
        if not success:
            exit(1)

if __name__ == "__main__":
    main()
