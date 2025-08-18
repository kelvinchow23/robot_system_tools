#!/usr/bin/env python3
"""Quick test script for Pi camera server"""
import socket
import sys

def test_camera_server(pi_ip, port=2222):
    try:
        # Connect to the server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((pi_ip, port))
        
        # Send TEST command
        sock.send(b"TEST")
        response = sock.recv(1024).decode()
        
        print(f"✅ Connected to Pi camera server at {pi_ip}:{port}")
        print(f"Server response: {response.strip()}")
        
        sock.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect to {pi_ip}:{port}")
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_client.py <PI_IP>")
        sys.exit(1)
    
    pi_ip = sys.argv[1]
    test_camera_server(pi_ip)
