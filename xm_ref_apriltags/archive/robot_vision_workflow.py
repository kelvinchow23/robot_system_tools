#!/usr/bin/env python3
"""
Integrated Camera System Workflow
Complete workflow for camera calibration, photo capture, and AprilTag detection
"""

import os
import sys
from pathlib import Path

from config_manager import CameraConfig
from camera_client import CameraClient

def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "=" * 50)
    print(f"🤖 {title}")
    print("=" * 50)

def check_camera_server():
    """Check if camera server is accessible"""
    print("🔍 Checking camera server connection...")
    try:
        client = CameraClient()
        # Try to connect (will timeout if server not available)
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((client.hostname, client.port))
        sock.close()
        
        if result == 0:
            print(f"✅ Camera server is accessible at {client.hostname}:{client.port}")
            return True
        else:
            print(f"❌ Camera server not accessible at {client.hostname}:{client.port}")
            return False
    except Exception as e:
        print(f"❌ Error checking camera server: {e}")
        return False

def run_calibration():
    """Run camera calibration"""
    print_header("Camera Calibration")
    
    try:
        from calibrate_camera import CameraCalibration
        calibrator = CameraCalibration()
        
        # Check for existing calibration
        if os.path.exists("camera_params.npy"):
            recalibrate = input("Camera parameters exist. Recalibrate? (y/n): ").lower().startswith('y')
            if not recalibrate:
                print("✅ Using existing camera calibration")
                return True
        
        # Get calibration images
        image_paths = calibrator.get_image_paths()
        if not image_paths:
            use_test = input("No calibration images found. Download test images? (y/n): ").lower().startswith('y')
            if use_test:
                calibrator.download_test_images(True)
                image_paths = calibrator.get_image_paths()
            
            if not image_paths:
                print("❌ No calibration images available")
                return False
        
        # Run calibration
        K, params = calibrator.calibrate_camera(image_paths, show_detections=True)
        print("✅ Camera calibration completed")
        return True
        
    except Exception as e:
        print(f"❌ Calibration failed: {e}")
        return False

def capture_and_detect():
    """Capture photo and detect AprilTags"""
    print_header("Photo Capture & AprilTag Detection")
    
    try:
        from detect_apriltags import AprilTagDetector
        detector = AprilTagDetector()
        
        # Capture and detect
        results = detector.capture_and_detect()
        
        if results and len(results['detections']) > 0:
            print(f"✅ Detection successful! Found {len(results['detections'])} tags")
            detector.show_results(results)
            return results
        else:
            print("❌ No AprilTags detected")
            return None
            
    except Exception as e:
        print(f"❌ Detection failed: {e}")
        return None

def main():
    """Main workflow"""
    print_header("UR3 Robot Arm Camera System - Complete Workflow")
    
    config = CameraConfig()
    
    print(f"📋 Configuration:")
    print(f"   Camera focus mode: {config.focus_mode}")
    print(f"   Server: {config.hostname}:{config.server_port}")
    print(f"   Photo directory: {config.photo_directory}")
    
    # Check camera server
    if not check_camera_server():
        print("\n❌ Camera server is not running!")
        print("   Start the server first: python3 camera_server.py")
        return
    
    # Menu loop
    while True:
        print("\n🎯 What would you like to do?")
        print("   1. Run camera calibration")
        print("   2. Capture photo and detect AprilTags")
        print("   3. Detect AprilTags from latest photo")
        print("   4. Test camera capture only")
        print("   5. Exit")
        
        choice = input("\nChoose option (1-5): ").strip()
        
        if choice == "1":
            run_calibration()
            
        elif choice == "2":
            # Check calibration exists
            if not os.path.exists("camera_params.npy"):
                print("⚠️  No camera calibration found!")
                if input("Run calibration first? (y/n): ").lower().startswith('y'):
                    if not run_calibration():
                        continue
                else:
                    print("❌ Cannot detect AprilTags without calibration")
                    continue
            
            capture_and_detect()
            
        elif choice == "3":
            if not os.path.exists("camera_params.npy"):
                print("❌ No camera calibration found! Run calibration first.")
                continue
                
            try:
                from detect_apriltags import AprilTagDetector
                detector = AprilTagDetector()
                results = detector.detect_from_latest_photo()
                if results:
                    detector.show_results(results)
            except Exception as e:
                print(f"❌ Detection failed: {e}")
                
        elif choice == "4":
            print("📸 Testing camera capture...")
            try:
                client = CameraClient()
                photo_path = client.request_photo()
                if photo_path:
                    print(f"✅ Photo captured: {photo_path}")
                else:
                    print("❌ Photo capture failed")
            except Exception as e:
                print(f"❌ Capture failed: {e}")
                
        elif choice == "5":
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()
