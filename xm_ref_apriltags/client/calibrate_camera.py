#!/usr/bin/env python3
"""
Camera Calibration for UR3 Robot Arm Camera System
Integrated with the camera server configuration
"""

import os
import sys
import zipfile
import urllib.request
import shutil
import numpy as np
import cv2
from typing import List, Tuple
import matplotlib.pyplot as plt

from config_manager import CameraConfig

class CameraCalibration:
    """Camera calibration integrated with camera system configuration"""
    
    def __init__(self):
        self.config = CameraConfig()
        self.image_dir = "./checkerboard_images"
        os.makedirs(self.image_dir, exist_ok=True)
        
        # Calibration parameters
        self.rows = 5   # inner corners in vertical direction
        self.cols = 8   # inner corners in horizontal direction  
        self.square_size_mm = 23  # size of one square in mm
        
    def download_test_images(self, use_test_images: bool = False):
        """Download test calibration images if needed"""
        if use_test_images:
            zip_url = "https://raw.githubusercontent.com/AccelerationConsortium/ac-training-lab/main/src/ac_training_lab/apriltag_demo/checkerboard_images.zip"
            self._download_and_flatten_unzip(zip_url, self.image_dir)
    
    def _download_and_flatten_unzip(self, url, extract_dir):
        """Download and extract calibration images"""
        zip_path = os.path.join(extract_dir, "checkerboard_images.zip")
        urllib.request.urlretrieve(url, zip_path)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for member in zip_ref.namelist():
                filename = os.path.basename(member)
                if not filename:
                    continue
                source = zip_ref.open(member)
                target_path = os.path.join(extract_dir, filename)
                with open(target_path, "wb") as target:
                    shutil.copyfileobj(source, target)
    
    def get_image_paths(self) -> List[str]:
        """Get all calibration image paths"""
        image_paths = [
            os.path.join(self.image_dir, f)
            for f in sorted(os.listdir(self.image_dir))
            if f.lower().endswith(('.jpg', '.png'))
        ]
        
        print(f"\nFound {len(image_paths)} calibration images:")
        for p in image_paths:
            print(f"  {p}")
        
        return image_paths
    
    def calibrate_camera(self, 
                        image_paths: List[str],
                        show_detections: bool = False,
                        save_to_config: bool = True) -> Tuple[np.ndarray, Tuple[float, float, float, float]]:
        """
        Calibrate camera from checkerboard images
        
        Args:
            image_paths: List of calibration image paths
            show_detections: Whether to show detection visualization
            save_to_config: Whether to save results to camera system
        
        Returns:
            Camera matrix and intrinsic parameters (fx, fy, cx, cy)
        """
        pattern_size = (self.cols, self.rows) if self.rows < self.cols else (self.rows, self.cols)

        # Create object points grid
        x = np.arange(pattern_size[0]) * self.square_size_mm
        y = np.arange(pattern_size[1]) * self.square_size_mm
        xgrid, ygrid = np.meshgrid(x, y)
        zgrid = np.zeros_like(xgrid)
        opoints = np.dstack((xgrid, ygrid, zgrid)).reshape((-1, 1, 3)).astype(np.float32)

        imagesize = None
        ipoints = []

        for filename in image_paths:
            rgb = cv2.imread(filename)
            if rgb is None:
                print(f'Error loading {filename}, skipping.')
                continue

            if imagesize is None:
                imagesize = (rgb.shape[1], rgb.shape[0])
            else:
                assert imagesize == (rgb.shape[1], rgb.shape[0]), "Inconsistent image sizes."

            gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY) if len(rgb.shape) == 3 else rgb
            found, corners = cv2.findChessboardCorners(gray, pattern_size)

            if show_detections:
                display_img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
                cv2.drawChessboardCorners(display_img, pattern_size, corners, found)
                plt.figure(figsize=(8, 6))
                plt.imshow(cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB))
                plt.title(f"Calibration: {os.path.basename(filename)}")
                plt.axis('off')
                plt.pause(0.5)  
                plt.close()

            if found:
                ipoints.append(corners)
                print(f'✓ Corners found in {os.path.basename(filename)}')
            else:
                print(f'✗ No corners found in {os.path.basename(filename)}, skipping.')

        if len(ipoints) < 1:
            raise ValueError("No valid images with detected corners found.")

        print(f"\nUsing {len(ipoints)} images for calibration...")

        # Calibration flags (simplified pinhole model)
        flags = (cv2.CALIB_ZERO_TANGENT_DIST |
                 cv2.CALIB_FIX_K1 |
                 cv2.CALIB_FIX_K2 |
                 cv2.CALIB_FIX_K3 |
                 cv2.CALIB_FIX_K4 |
                 cv2.CALIB_FIX_K5 |
                 cv2.CALIB_FIX_K6)

        retval, K, dcoeffs, rvecs, tvecs = cv2.calibrateCamera(
            [opoints] * len(ipoints),
            ipoints,
            imagesize,
            cameraMatrix=None,
            distCoeffs=np.zeros(5),
            flags=flags
        )

        fx, fy, cx, cy = K[0,0], K[1,1], K[0,2], K[1,2]
        
        # Save results
        if save_to_config:
            save_path = "camera_params.npy"
            np.save(save_path, np.array([fx, fy, cx, cy]))
            print(f'\n✓ Saved camera parameters to {save_path}')

        print(f"\n📷 Camera Calibration Results:")
        print(f"   Image size: {imagesize}")
        print(f"   Reprojection error: {retval:.3f} pixels")
        print(f"\n📐 Camera Intrinsics (pixels):")
        print(f"   fx = {fx:.3f}")
        print(f"   fy = {fy:.3f}")
        print(f"   cx = {cx:.3f}")
        print(f"   cy = {cy:.3f}")
        print(f"\n🐍 Python copy-paste:")
        print(f"   fx, fy, cx, cy = {(fx, fy, cx, cy)}")

        return K, (fx, fy, cx, cy)

def main():
    """Main calibration function"""
    calibrator = CameraCalibration()
    
    print("🎯 UR3 Robot Arm Camera Calibration")
    print("=" * 40)
    
    # Option to download test images
    use_test = input("Download test images? (y/n): ").lower().startswith('y')
    calibrator.download_test_images(use_test)
    
    # Get calibration images
    image_paths = calibrator.get_image_paths()
    
    if not image_paths:
        print("❌ No calibration images found!")
        print(f"   Place checkerboard images in: {calibrator.image_dir}")
        return
    
    # Run calibration
    try:
        K, params = calibrator.calibrate_camera(
            image_paths=image_paths,
            show_detections=True,
            save_to_config=True
        )
        print("\n✅ Calibration completed successfully!")
        
    except Exception as e:
        print(f"❌ Calibration failed: {e}")

if __name__ == "__main__":
    main()
