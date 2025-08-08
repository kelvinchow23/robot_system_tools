#!/usr/bin/env python3
"""
AprilTag Detection for UR3 Robot Arm Camera System
Integrated with camera server and configuration system
"""

import cv2
import numpy as np
import os
from pupil_apriltags import Detector
from scipy.spatial.transform import Rotation as R
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional, List, Dict, Any

from config_manager import CameraConfig
from camera_client import CameraClient

class AprilTagDetector:
    """AprilTag detection integrated with camera system"""
    
    def __init__(self):
        self.config = CameraConfig()
        self.camera_client = CameraClient()
        
        # Detection parameters (configurable)
        self.families = "tagStandard41h12"
        self.tagsize_mm = 13
        self.tagsize_meters = self.tagsize_mm / 1000
        
        # Initialize detector
        self.detector = Detector(
            families=self.families,
            nthreads=1,
            quad_decimate=1.0,
            quad_sigma=0.0,
            refine_edges=1,
            decode_sharpening=0.25,
            debug=0
        )
        
        # Load camera parameters
        self.camera_params = self._load_camera_params()
        
    def _load_camera_params(self) -> np.ndarray:
        """Load camera calibration parameters"""
        try:
            params = np.load("camera_params.npy")
            print(f"✓ Loaded camera parameters: fx={params[0]:.1f}, fy={params[1]:.1f}, cx={params[2]:.1f}, cy={params[3]:.1f}")
            return params
        except FileNotFoundError:
            print("❌ Camera parameters not found! Run calibrate_camera.py first")
            print("   Using default parameters (may be inaccurate)")
            # Default parameters for Pi Camera v2
            return np.array([3280, 3280, 1640, 1232])
    
    def capture_and_detect(self) -> Optional[Dict[str, Any]]:
        """Capture a photo from camera server and detect AprilTags"""
        print("📸 Requesting photo from camera server...")
        
        photo_path = self.camera_client.request_photo()
        if not photo_path:
            print("❌ Failed to capture photo from server")
            return None
        
        print(f"✓ Photo received: {photo_path}")
        return self.detect_from_image(photo_path)
    
    def detect_from_latest_photo(self) -> Optional[Dict[str, Any]]:
        """Detect AprilTags from the latest photo in the photos directory"""
        photos_dir = Path(self.config.photo_directory)
        
        if not photos_dir.exists():
            print(f"❌ Photos directory not found: {photos_dir}")
            return None
        
        # Find latest photo
        photo_files = list(photos_dir.glob("*.jpg"))
        if not photo_files:
            print(f"❌ No photos found in {photos_dir}")
            return None
        
        latest_photo = max(photo_files, key=os.path.getctime)
        print(f"📷 Using latest photo: {latest_photo}")
        
        return self.detect_from_image(str(latest_photo))
    
    def detect_from_image(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Detect AprilTags from an image file
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with detection results or None if failed
        """
        # Load image
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            print(f"❌ Failed to load image: {image_path}")
            return None
        
        print(f"🔍 Detecting AprilTags in {os.path.basename(image_path)}...")
        
        # Detect AprilTags
        detections = self.detector.detect(
            image,
            estimate_tag_pose=True,
            camera_params=self.camera_params,
            tag_size=self.tagsize_meters
        )
        
        print(f"🎯 Found {len(detections)} AprilTag(s)")
        
        if len(detections) == 0:
            return {"image_path": image_path, "detections": [], "annotated_image": image}
        
        # Process detections
        results = {
            "image_path": image_path,
            "detections": [],
            "annotated_image": image.copy()
        }
        
        for det in detections:
            tag_result = self._process_detection(det, results["annotated_image"])
            results["detections"].append(tag_result)
        
        return results
    
    def _process_detection(self, det, image: np.ndarray) -> Dict[str, Any]:
        """Process a single AprilTag detection"""
        tag_id = det.tag_id
        center = det.center
        corners = det.corners.astype(int)
        
        # Draw on image
        cv2.polylines(image, [corners], True, 255, 2)
        cx, cy = map(int, center)
        cv2.circle(image, (cx, cy), 4, 255, -1)
        cv2.putText(image, str(tag_id), (cx, cy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 255, 2)
        
        # Prepare result
        result = {
            "tag_id": tag_id,
            "center": center.tolist(),
            "corners": det.corners.tolist(),
            "pose_translation": None,
            "pose_rotation": None,
            "distance_cm": None,
            "euler_degrees": None
        }
        
        # Process pose if available
        if det.pose_t is not None and det.pose_R is not None:
            t = det.pose_t.flatten()
            result["pose_translation"] = t.tolist()
            result["pose_rotation"] = det.pose_R.tolist()
            
            # Calculate distance
            distance_cm = np.linalg.norm(t) * 100
            result["distance_cm"] = distance_cm
            
            # Calculate Euler angles
            euler = R.from_matrix(det.pose_R).as_euler('xyz', degrees=True)
            result["euler_degrees"] = euler.tolist()
            
            print(f"\n🏷️  Tag ID: {tag_id}")
            print(f"   📍 Center: ({center[0]:.1f}, {center[1]:.1f}) pixels")
            print(f"   📏 Distance: {distance_cm:.1f} cm")
            print(f"   🔄 Rotation (roll, pitch, yaw): ({euler[0]:.1f}°, {euler[1]:.1f}°, {euler[2]:.1f}°)")
            print(f"   📐 Translation (x, y, z): ({t[0]:.3f}, {t[1]:.3f}, {t[2]:.3f}) m")
        else:
            print(f"\n🏷️  Tag ID: {tag_id}")
            print(f"   📍 Center: ({center[0]:.1f}, {center[1]:.1f}) pixels")
            print("   ❌ No pose estimation available")
        
        return result
    
    def show_results(self, results: Dict[str, Any], save_annotated: bool = True):
        """Display detection results"""
        if not results:
            return
        
        image = results["annotated_image"]
        
        # Save annotated image
        if save_annotated:
            base_name = Path(results["image_path"]).stem
            annotated_path = f"annotated_{base_name}.jpg"
            cv2.imwrite(annotated_path, image)
            print(f"💾 Saved annotated image: {annotated_path}")
        
        # Display image
        plt.figure(figsize=(12, 8))
        plt.imshow(image, cmap='gray')
        plt.title(f"AprilTag Detection - {len(results['detections'])} tags found")
        plt.axis('off')
        plt.show()

def main():
    """Main detection function"""
    detector = AprilTagDetector()
    
    print("🎯 UR3 Robot Arm AprilTag Detection")
    print("=" * 40)
    
    # Choose detection mode
    print("Detection options:")
    print("  1. Capture new photo from camera server")
    print("  2. Use latest photo from photos directory")
    print("  3. Specify image file path")
    
    choice = input("\nChoose option (1-3): ").strip()
    
    results = None
    
    if choice == "1":
        results = detector.capture_and_detect()
    elif choice == "2":
        results = detector.detect_from_latest_photo()
    elif choice == "3":
        image_path = input("Enter image path: ").strip()
        if os.path.exists(image_path):
            results = detector.detect_from_image(image_path)
        else:
            print(f"❌ Image not found: {image_path}")
    else:
        print("❌ Invalid choice")
        return
    
    if results:
        print(f"\n✅ Detection completed!")
        print(f"   Found {len(results['detections'])} AprilTag(s)")
        detector.show_results(results)
        
        # Print summary
        for i, det in enumerate(results['detections']):
            print(f"\n📋 Tag {i+1} Summary:")
            print(f"   ID: {det['tag_id']}")
            if det['distance_cm']:
                print(f"   Distance: {det['distance_cm']:.1f} cm")
                euler = det['euler_degrees']
                print(f"   Orientation: roll={euler[0]:.1f}°, pitch={euler[1]:.1f}°, yaw={euler[2]:.1f}°")
    else:
        print("❌ Detection failed")

if __name__ == "__main__":
    main()
