#!/usr/bin/env python3
"""
Complete Robot Vision System Test
Tests camera connection, calibration, and AprilTag detection workflow
"""

import sys
import os
from pathlib import Path

def test_camera_connection():
    """Test Pi camera connection"""
    print("📡 Testing camera connection...")
    
    try:
        from picam import PiCam, PiCamConfig
        
        if not os.path.exists("client_config.yaml"):
            print("❌ client_config.yaml not found")
            print("   Create config file first with your Pi's IP address")
            return False
        
        config = PiCamConfig.from_yaml("client_config.yaml")
        camera = PiCam(config)
        
        if camera.test_connection():
            print("✅ Camera connection successful")
            
            # Test photo capture
            photo_path = camera.capture_photo()
            if photo_path and os.path.exists(photo_path):
                file_size = os.path.getsize(photo_path)
                print(f"✅ Photo captured: {photo_path} ({file_size} bytes)")
                return True
            else:
                print("❌ Failed to capture photo")
                return False
        else:
            print("❌ Cannot connect to camera server")
            print("   Check Pi IP address and ensure server is running")
            return False
            
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
        return False

def test_calibration_files():
    """Check if calibration files are available"""
    print("\n� Checking calibration resources...")
    
    chessboard_path = Path("camera calibration/Calibration chessboard (US Letter).pdf")
    calibration_script = Path("calibrate_camera.py")
    
    if chessboard_path.exists():
        print("✅ Calibration chessboard PDF found")
    else:
        print("❌ Calibration chessboard PDF missing")
        return False
    
    if calibration_script.exists():
        print("✅ Calibration script available")
    else:
        print("❌ calibrate_camera.py missing")
        return False
    
    # Check for existing calibration
    calib_file = Path("camera_calibration/camera_calibration.yaml")
    if calib_file.exists():
        print("✅ Camera calibration file exists")
        try:
            import yaml
            with open(calib_file, 'r') as f:
                calib_data = yaml.safe_load(f)
            if 'camera_matrix' in calib_data:
                print("✅ Valid calibration data found")
                return True
        except Exception as e:
            print(f"⚠️  Calibration file exists but may be invalid: {e}")
    else:
        print("⚠️  No camera calibration found")
        print("   Run: cd camera_calibration && python capture_calibration_photos.py")
        print("   Then: python calculate_camera_intrinsics.py")
    
    return True

def test_apriltag_detection():
    """Test AprilTag detection capabilities"""
    print("\n🏷️  Testing AprilTag detection...")
    
    try:
        from pupil_apriltags import Detector
        print("✅ pupil-apriltags library available")
        
        # Test detector initialization
        detector = Detector(families='tag36h11')
        print("✅ AprilTag detector initialized")
        
        apriltag_script = Path("test_apriltag_detection.py")
        if apriltag_script.exists():
            print("✅ AprilTag detection script available")
        else:
            print("❌ test_apriltag_detection.py missing")
            return False
            
        return True
        
    except ImportError:
        print("❌ pupil-apriltags library not installed")
        print("   Install with: pip install pupil-apriltags")
        return False
    except Exception as e:
        print(f"❌ AprilTag test failed: {e}")
        return False

def test_dependencies():
    """Test required dependencies"""
    print("\n📦 Checking dependencies...")
    
    required_modules = [
        ('cv2', 'opencv-python'),
        ('numpy', 'numpy'),
        ('yaml', 'pyyaml'),
        ('requests', 'requests'),
    ]
    
    missing = []
    for module, package in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} (install: pip install {package})")
            missing.append(package)
    
    if missing:
        print(f"\n� Install missing packages:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    return True

def run_apriltag_detection_test():
    """Run a quick AprilTag detection test"""
    print("\n🎯 Running AprilTag detection test...")
    
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, "test_apriltag_detection.py", "--help"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ AprilTag detection script executable")
            return True
        else:
            print("❌ AprilTag detection script has issues")
            if result.stderr:
                print(f"   Error: {result.stderr.strip()}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to test AprilTag script: {e}")
        return False

def main():
    """Run complete system test"""
    print("🤖 Robot Vision System Test")
    print("=" * 50)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Camera Connection", test_camera_connection),
        ("Calibration Resources", test_calibration_files),
        ("AprilTag Detection", test_apriltag_detection),
        ("AprilTag Script Test", run_apriltag_detection_test),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} test crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("� Test Results:")
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! System ready for robot vision.")
        print("\nNext steps:")
        print("1. Calibrate camera: cd camera_calibration && python capture_calibration_photos.py")
        print("2. Calculate intrinsics: python calculate_camera_intrinsics.py")
        print("3. Test AprilTag detection: python ../test_apriltag_detection.py")
        print("4. Print AprilTags and test pose estimation")
    else:
        print("⚠️  Some tests failed. Please address the issues above.")
        print("\nQuick fixes:")
        print("- Install dependencies: pip install -r requirements.txt")
        print("- Check Pi connection: edit client_config.yaml")
        print("- Ensure Pi server is running: sudo systemctl status pi-camera-server")
        print("- Calibrate camera: cd camera_calibration && python capture_calibration_photos.py")

if __name__ == "__main__":
    main()
