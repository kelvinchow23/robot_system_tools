#!/usr/bin/env python3
"""
Simple Pi Camera Test with Config File
Tests connection and captures a photo using client_config.yaml or command-line arguments
"""

import argparse
from picam import PiCam, PiCamConfig

def main():
    parser = argparse.ArgumentParser(description="Test Pi Camera connection and capture")
    parser.add_argument("--host", help="Camera server hostname/IP (overrides config file)")
    parser.add_argument("--port", type=int, default=2222, help="Camera server port (default: 2222)")
    args = parser.parse_args()
    
    print("🍓 Pi Camera Client Test")
    print("========================")
    
    if args.host:
        # Use command-line arguments
        print(f"📝 Using command-line arguments...")
        print(f"🔗 Connecting to: {args.host}:{args.port}")
        cam = PiCam(host=args.host, port=args.port)
    else:
        # Load config from file
        print("📝 Loading config from client_config.yaml...")
        config = PiCamConfig.from_yaml("client_config.yaml")
        print(f"🔗 Connecting to: {config.hostname}:{config.port}")
        cam = PiCam(config)
    
    # Test connection
    print("\n🔍 Testing connection...")
    if cam.test_connection():
        print("✅ Connection successful!")
    else:
        print("❌ Connection failed!")
        print("   Check your Pi's IP address in client_config.yaml")
        print("   Make sure the camera server is running on the Pi")
        return
    
    # Capture photo
    print("\n📸 Capturing photo...")
    photo_path = cam.capture_photo()
    
    if photo_path:
        print(f"✅ Photo captured successfully!")
        print(f"📁 Saved to: {photo_path}")
    else:
        print("❌ Failed to capture photo")

if __name__ == "__main__":
    main()
