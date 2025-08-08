#!/usr/bin/env python3
# Minimal test server to debug port binding

import socket
import sys

def test_server():
    host = "0.0.0.0"
    port = 2222
    
    print(f"Creating socket...")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        print(f"Attempting to bind to {host}:{port}...")
        server.bind((host, port))
        print(f"✅ Successfully bound to {host}:{port}")
        
        print("Starting to listen...")
        server.listen(5)
        print(f"✅ Server is listening on {host}:{port}")
        
        print("Waiting for connection... (Press Ctrl+C to stop)")
        while True:
            conn, addr = server.accept()
            print(f"✅ Connection from {addr}")
            conn.send(b"Hello from test server!\n")
            conn.close()
            print(f"Connection closed")
            
    except OSError as e:
        print(f"❌ Socket error: {e}")
        if "Address already in use" in str(e):
            print("Port 2222 is already in use by another process")
        elif "Permission denied" in str(e):
            print("Permission denied - try running as sudo or use a port > 1024")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        server.close()
        print("Server socket closed")

if __name__ == "__main__":
    test_server()
