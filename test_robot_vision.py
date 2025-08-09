#!/usr/bin/env python3
"""
Robot Vision Workflow Test
Simple test script that demonstrates the complete robot vision workflow:
1. Capture photo from Pi camera
2. Detect AprilTags  
3. Show results

This is the simple workflow script you wanted - just like before!
"""

import subprocess
import sys
import os
from pathlib import Path
from picam import PiCam, PiCamConfig

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - Success")
            return True
        else:
            print(f"❌ {description} - Failed")
            if result.stderr:
                print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} - Error: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    try:
        import cv2
        import numpy as np
        print("   ✅ OpenCV and NumPy")
    except ImportError:
        print("   ❌ Install OpenCV: pip install opencv-python numpy")
        return False
    
    try:
        import pupil_apriltags
        import scipy
        import matplotlib
        print("   ✅ AprilTag detection libraries")
    except ImportError:
        print("   ❌ Install vision libs: pip install pupil-apriltags scipy matplotlib")
        return False
    
    return True

def test_camera_connection(hostname=None):
    """Test camera server connection using PiCam class"""
    print("🔍 Testing camera server connection...")
    
    if os.path.exists("camera_config.yaml"):
        config = PiCamConfig.from_yaml("camera_config.yaml")
    else:
        config = PiCamConfig()
    
    if hostname:
        config.hostname = hostname
    
    camera = PiCam(config)
    
    if camera.test_connection():
        print(f"✅ Camera server accessible at {config.hostname}:{config.port}")
        return True
    else:
        print(f"❌ Cannot connect to camera server at {config.hostname}:{config.port}")
        return False

def capture_photo_direct(hostname=None):
    """Capture photo directly using PiCam class"""
    print("📸 Capturing photo...")
    
    if os.path.exists("camera_config.yaml"):
        config = PiCamConfig.from_yaml("camera_config.yaml")
    else:
        config = PiCamConfig()
    
    if hostname:
        config.hostname = hostname
    
    camera = PiCam(config)
    photo_path = camera.capture_photo()
    
    if photo_path:
        file_size = os.path.getsize(photo_path)
        print(f"✅ Photo captured: {os.path.basename(photo_path)} ({file_size} bytes)")
        return True
    else:
        print("❌ Failed to capture photo")
        return False

def detect_apriltags():
    """Detect AprilTags in the latest photo"""
    return run_command("python detect_apriltags.py --latest --show", "Detecting AprilTags")

def robot_vision_workflow(hostname=None):
    """Run the complete robot vision workflow"""
    print("🤖 Robot Vision Workflow Test")
    print("=" * 50)
    
    # Step 1: Check dependencies
    if not check_dependencies():
        print("\n❌ Dependencies missing - install them first")
        return False
    
    # Step 2: Test camera connection
    print(f"\n📡 Step 1: Test Camera Connection")
    if not test_camera_connection(hostname):
        print("   💡 Make sure Pi camera server is running")
        if hostname:
            print(f"   💡 Check if {hostname} is accessible")
        return False
    
    # Step 3: Capture photo directly
    print(f"\n📸 Step 2: Capture Photo")
    if not capture_photo_direct(hostname):
        print("   💡 Check camera server and network connection")
        return False
    
    # Step 4: Detect AprilTags
    print(f"\n🎯 Step 3: Detect AprilTags")
    if not detect_apriltags():
        print("   💡 Make sure you have AprilTags visible in the photo")
        print("   💡 Check camera calibration with: python calibrate_camera.py")
        return False
    
    print(f"\n✅ Robot Vision Workflow Complete!")
    print("   📸 Photo captured from Pi camera")
    print("   🎯 AprilTags detected and annotated")
    print("   📊 Results displayed")
    
    return True

def main():
    """Main function - simple robot vision workflow"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Robot Vision Workflow Test")
    parser.add_argument("hostname", nargs="?", help="Pi hostname/IP (optional)")
    parser.add_argument("--loop", action="store_true", help="Run continuously")
    
    args = parser.parse_args()
    
    if args.loop:
        print("🔄 Continuous robot vision testing (Ctrl+C to stop)")
        try:
            while True:
                print("\n" + "="*60)
                input("Press Enter to run workflow (Ctrl+C to exit)...")
                robot_vision_workflow(args.hostname)
        except KeyboardInterrupt:
            print("\n\n👋 Testing stopped by user")
    else:
        # Single run
        success = robot_vision_workflow(args.hostname)
        if not success:
            print("\n🔧 Troubleshooting tips:")
            print("   1. Install dependencies: pip install pupil-apriltags scipy matplotlib opencv-python")
            print("   2. Start Pi camera server: ssh pi@[IP] 'python /home/pi/robot_camera/camera_server.py'")
            print("   3. Test camera: python camera_client.py [IP] --test")
            print("   4. Calibrate camera: python calibrate_camera.py")
            sys.exit(1)

if __name__ == "__main__":
    main()
