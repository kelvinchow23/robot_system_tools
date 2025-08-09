#!/usr/bin/env python3
"""
Camera Calibration Script
Simple script to calibrate camera parameters for AprilTag detection
"""

import cv2
import numpy as np
import argparse
from pathlib import Path

def create_chessboard_calibration():
    """Interactive chessboard calibration"""
    print("📐 Camera Calibration - Chessboard Method")
    print("=" * 50)
    print("Instructions:")
    print("1. Print a chessboard pattern (9x6 corners)")
    print("2. Take 10-20 photos from different angles")
    print("3. Place images in calibration_images/ directory")
    print("4. Run this script")
    
    # Chessboard parameters
    CHESSBOARD_SIZE = (9, 6)
    
    # Prepare object points
    objp = np.zeros((CHESSBOARD_SIZE[0] * CHESSBOARD_SIZE[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:CHESSBOARD_SIZE[0], 0:CHESSBOARD_SIZE[1]].T.reshape(-1, 2)
    
    # Arrays to store object points and image points
    objpoints = []
    imgpoints = []
    
    # Find calibration images
    cal_dir = Path("calibration_images")
    if not cal_dir.exists():
        print(f"❌ Create {cal_dir}/ directory and add chessboard images")
        return None
    
    image_files = list(cal_dir.glob("*.jpg")) + list(cal_dir.glob("*.png"))
    if len(image_files) < 5:
        print(f"❌ Need at least 5 calibration images, found {len(image_files)}")
        return None
    
    print(f"🔍 Processing {len(image_files)} calibration images...")
    
    successful_images = 0
    
    for img_file in image_files:
        img = cv2.imread(str(img_file))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Find chessboard corners
        ret, corners = cv2.findChessboardCorners(gray, CHESSBOARD_SIZE, None)
        
        if ret:
            objpoints.append(objp)
            
            # Refine corners
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            imgpoints.append(corners2)
            
            successful_images += 1
            print(f"   ✅ {img_file.name} - corners found")
        else:
            print(f"   ❌ {img_file.name} - no corners")
    
    if successful_images < 5:
        print(f"❌ Need at least 5 successful images, got {successful_images}")
        return None
    
    print(f"📊 Calibrating camera with {successful_images} images...")
    
    # Calibrate camera
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
        objpoints, imgpoints, gray.shape[::-1], None, None
    )
    
    if ret:
        # Extract camera parameters
        fx, fy = mtx[0, 0], mtx[1, 1]
        cx, cy = mtx[0, 2], mtx[1, 2]
        
        camera_params = np.array([fx, fy, cx, cy])
        
        # Save parameters
        np.save("camera_params.npy", camera_params)
        
        print("✅ Camera calibration successful!")
        print(f"   fx: {fx:.1f}")
        print(f"   fy: {fy:.1f}")
        print(f"   cx: {cx:.1f}")
        print(f"   cy: {cy:.1f}")
        print(f"   📁 Saved to: camera_params.npy")
        
        return camera_params
    else:
        print("❌ Camera calibration failed")
        return None

def create_apriltag_calibration():
    """Simple AprilTag-based calibration"""
    print("📐 Camera Calibration - AprilTag Method")
    print("=" * 50)
    print("Instructions:")
    print("1. Place a known-size AprilTag at a measured distance")
    print("2. Take a photo with the camera")
    print("3. Measure the tag size in pixels")
    print("4. Calculate focal length")
    
    # Get user input
    try:
        real_distance_cm = float(input("Enter real distance to tag (cm): "))
        real_size_mm = float(input("Enter real tag size (mm): "))
        
        print("\nTake a photo and measure the tag size in pixels...")
        pixel_size = float(input("Enter tag size in pixels: "))
        
        # Calculate focal length
        # focal_length = (pixel_size * real_distance_cm * 10) / real_size_mm
        focal_length = (pixel_size * real_distance_cm) / (real_size_mm / 10)
        
        # Assume square pixels and centered principal point
        # These are approximations for quick calibration
        image_width = int(input("Enter image width (pixels): "))
        image_height = int(input("Enter image height (pixels): "))
        
        fx = fy = focal_length
        cx = image_width / 2
        cy = image_height / 2
        
        camera_params = np.array([fx, fy, cx, cy])
        
        # Save parameters
        np.save("camera_params.npy", camera_params)
        
        print("\n✅ Quick calibration complete!")
        print(f"   fx, fy: {focal_length:.1f}")
        print(f"   cx: {cx:.1f}")
        print(f"   cy: {cy:.1f}")
        print(f"   📁 Saved to: camera_params.npy")
        print("⚠️  Note: This is a rough calibration, use chessboard method for accuracy")
        
        return camera_params
        
    except ValueError:
        print("❌ Invalid input")
        return None

def main():
    """Camera calibration main function"""
    parser = argparse.ArgumentParser(description="Calibrate camera for AprilTag detection")
    parser.add_argument("--method", choices=["chessboard", "apriltag"], default="chessboard",
                       help="Calibration method")
    
    args = parser.parse_args()
    
    print("🎥 Camera Calibration for Robot Vision")
    print("=" * 50)
    
    if args.method == "chessboard":
        params = create_chessboard_calibration()
    else:
        params = create_apriltag_calibration()
    
    if params is not None:
        print("\n🎯 Calibration complete! You can now use:")
        print("   python detect_apriltags.py --latest")

if __name__ == "__main__":
    main()
