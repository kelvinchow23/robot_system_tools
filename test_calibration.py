#!/usr/bin/env python3
"""
Test Camera Calibration
Load calibration results and test by undistorting captured images.
"""

import cv2
import numpy as np
import yaml
import argparse
from pathlib import Path
from picam import PiCam, PiCamConfig

def load_calibration(filename):
    """Load camera calibration from YAML file"""
    with open(filename, 'r') as f:
        calib = yaml.safe_load(f)
    
    camera_matrix = np.array(calib['camera_matrix'])
    dist_coeffs = np.array(calib['distortion_coefficients'])
    
    return camera_matrix, dist_coeffs, calib

def test_calibration_with_new_image(camera, camera_matrix, dist_coeffs):
    """Capture new image and show original vs undistorted"""
    print("📸 Capturing test image...")
    photo_path = camera.capture_photo()
    
    if not photo_path:
        print("❌ Failed to capture test image")
        return
    
    # Load image
    img = cv2.imread(photo_path)
    if img is None:
        print("❌ Failed to load captured image")
        return
    
    h, w = img.shape[:2]
    
    # Get optimal new camera matrix
    new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(
        camera_matrix, dist_coeffs, (w, h), 1, (w, h)
    )
    
    # Undistort image
    undistorted = cv2.undistort(img, camera_matrix, dist_coeffs, None, new_camera_matrix)
    
    # Crop the image based on ROI
    x, y, w_roi, h_roi = roi
    undistorted_cropped = undistorted[y:y+h_roi, x:x+w_roi]
    
    # Save comparison images
    output_dir = Path("calibration_test")
    output_dir.mkdir(exist_ok=True)
    
    original_path = output_dir / "original.jpg"
    undistorted_path = output_dir / "undistorted.jpg"
    undistorted_cropped_path = output_dir / "undistorted_cropped.jpg"
    
    cv2.imwrite(str(original_path), img)
    cv2.imwrite(str(undistorted_path), undistorted)
    cv2.imwrite(str(undistorted_cropped_path), undistorted_cropped)
    
    print(f"✅ Test images saved:")
    print(f"   Original: {original_path}")
    print(f"   Undistorted: {undistorted_path}")
    print(f"   Undistorted (cropped): {undistorted_cropped_path}")
    
    return original_path, undistorted_path, undistorted_cropped_path

def print_calibration_info(calib_data):
    """Print calibration information"""
    print("📊 Calibration Information:")
    print(f"   Date: {calib_data.get('calibration_date', 'Unknown')}")
    print(f"   Images used: {calib_data.get('num_images_used', 'Unknown')}")
    print(f"   Reprojection error: {calib_data.get('reprojection_error', 'Unknown'):.3f} pixels")
    print(f"   Image size: {calib_data.get('image_size', 'Unknown')}")
    print(f"   Checkerboard: {calib_data.get('checkerboard_size', 'Unknown')} corners")
    print(f"   Square size: {calib_data.get('square_size_mm', 'Unknown')}mm")
    print("")
    print("📐 Camera Parameters:")
    print(f"   Focal length: fx={calib_data.get('focal_length_x', 0):.1f}, fy={calib_data.get('focal_length_y', 0):.1f}")
    print(f"   Principal point: ({calib_data.get('principal_point_x', 0):.1f}, {calib_data.get('principal_point_y', 0):.1f})")
    print("")

def test_existing_image(image_path, camera_matrix, dist_coeffs):
    """Test calibration on existing image"""
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Failed to load image: {image_path}")
        return
    
    h, w = img.shape[:2]
    
    # Get optimal new camera matrix
    new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(
        camera_matrix, dist_coeffs, (w, h), 1, (w, h)
    )
    
    # Undistort image
    undistorted = cv2.undistort(img, camera_matrix, dist_coeffs, None, new_camera_matrix)
    
    # Save result
    input_path = Path(image_path)
    output_path = input_path.parent / f"{input_path.stem}_undistorted{input_path.suffix}"
    cv2.imwrite(str(output_path), undistorted)
    
    print(f"✅ Undistorted image saved: {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Test Camera Calibration')
    parser.add_argument('--calibration', default='camera_calibration.yaml',
                       help='Camera calibration file')
    parser.add_argument('--config', default='client_config.yaml',
                       help='Pi camera config file')
    parser.add_argument('--test-image', type=str,
                       help='Test calibration on existing image')
    parser.add_argument('--capture-new', action='store_true',
                       help='Capture new image to test calibration')
    
    args = parser.parse_args()
    
    print("🔍 Camera Calibration Test")
    print("=" * 40)
    
    # Load calibration
    try:
        camera_matrix, dist_coeffs, calib_data = load_calibration(args.calibration)
        print(f"📖 Loaded calibration: {args.calibration}")
    except Exception as e:
        print(f"❌ Failed to load calibration: {e}")
        print("   Run calibrate_camera.py first to create calibration file")
        return
    
    print_calibration_info(calib_data)
    
    if args.test_image:
        # Test on existing image
        print(f"🖼️  Testing on existing image: {args.test_image}")
        test_existing_image(args.test_image, camera_matrix, dist_coeffs)
        
    elif args.capture_new:
        # Capture new image and test
        print("📡 Connecting to Pi camera...")
        config = PiCamConfig.from_yaml(args.config)
        camera = PiCam(config)
        
        if not camera.test_connection():
            print("❌ Failed to connect to camera server")
            return
        
        print("✅ Connected to camera server")
        test_calibration_with_new_image(camera, camera_matrix, dist_coeffs)
        
    else:
        print("ℹ️  Use --capture-new to test with new image or --test-image <path> to test existing image")

if __name__ == "__main__":
    main()
