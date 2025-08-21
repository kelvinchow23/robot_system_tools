#!/usr/bin/env python3
"""
Simple Pi Camera Test with Config File
Tests connection and captures a photo using client_config.yaml
"""

from picam import PiCam, PiCamConfig

def main():
    print("🍓 Pi Camera Client Test")
    print("========================")
    
    # Load config from file
    print("📝 Loading config from client_config.yaml...")
    config = PiCamConfig.from_yaml("client_config.yaml")
    
    print(f"🔗 Connecting to: {config.hostname}:{config.port}")
    print(f"📁 Photos will be saved to: {config.download_dir}")
    
    # Initialize camera
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
