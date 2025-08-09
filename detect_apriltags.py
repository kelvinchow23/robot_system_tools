#!/usr/bin/env python3
"""
Simple AprilTag Detection Script
Detects AprilTags in images - single purpose script
"""

import cv2
import numpy as np
import os
import argparse
from pathlib import Path

try:
    from pupil_apriltags import Detector
    from scipy.spatial.transform import Rotation as R
    import matplotlib.pyplot as plt
    VISION_AVAILABLE = True
except ImportError:
    print("❌ Vision dependencies not installed")
    print("   Install with: pip install pupil-apriltags opencv-python scipy matplotlib")
    VISION_AVAILABLE = False

class SimpleAprilTagDetector:
    """Simple AprilTag detector - focused on detection only"""
    
    def __init__(self, tag_family="tag36h11", tag_size_mm=30):
        self.tag_family = tag_family
        self.tag_size_mm = tag_size_mm
        self.tag_size_meters = tag_size_mm / 1000
        
        # Initialize detector
        self.detector = Detector(
            families=tag_family,
            nthreads=1,
            quad_decimate=1.0,
            quad_sigma=0.0,
            refine_edges=1,
            decode_sharpening=0.25,
            debug=0
        )
        
        # Load camera parameters
        self.camera_params = self._load_camera_params()
        
        print(f"AprilTag detector initialized: {tag_family}, {tag_size_mm}mm tags")
    
    def _load_camera_params(self):
        """Load camera calibration parameters"""
        param_files = [
            "camera_params.npy",
            "pi_cam_server/camera_params.npy", 
            "archive/apriltag_experiments/camera_params.npy"
        ]
        
        for param_file in param_files:
            if os.path.exists(param_file):
                params = np.load(param_file)
                print(f"✅ Loaded camera parameters from {param_file}")
                return params
        
        print("⚠️  Using default camera parameters (may be inaccurate)")
        return np.array([3280, 3280, 1640, 1232])  # Pi Camera v2 defaults
    
    def detect_in_image(self, image_path):
        """Detect AprilTags in an image file"""
        if not os.path.exists(image_path):
            print(f"❌ Image not found: {image_path}")
            return None
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            print(f"❌ Failed to load image: {image_path}")
            return None
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        print(f"🔍 Analyzing {os.path.basename(image_path)} ({gray.shape[1]}x{gray.shape[0]})")
        
        # Detect AprilTags
        detections = self.detector.detect(
            gray,
            estimate_tag_pose=True,
            camera_params=self.camera_params,
            tag_size=self.tag_size_meters
        )
        
        print(f"   Found {len(detections)} AprilTag(s)")
        
        if len(detections) == 0:
            print(f"   No {self.tag_family} tags detected")
            return {"image": image, "detections": []}
        
        # Process detections
        results = []
        annotated_image = image.copy()
        
        for det in detections:
            result = self._process_detection(det, annotated_image)
            results.append(result)
        
        return {"image": annotated_image, "detections": results}
    
    def _process_detection(self, det, image):
        """Process a single detection"""
        tag_id = det.tag_id
        center = det.center.astype(int)
        corners = det.corners.astype(int)
        
        # Draw detection
        cv2.polylines(image, [corners], True, (0, 255, 0), 2)
        cv2.circle(image, tuple(center), 5, (0, 0, 255), -1)
        cv2.putText(image, str(tag_id), (center[0]-10, center[1]-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Process pose
        result = {"tag_id": tag_id, "center": center}
        
        if det.pose_t is not None and det.pose_R is not None:
            t = det.pose_t.flatten()
            distance_cm = np.linalg.norm(t) * 100
            euler = R.from_matrix(det.pose_R).as_euler('xyz', degrees=True)
            
            result.update({
                "distance_cm": distance_cm,
                "position": t,
                "rotation_deg": euler
            })
            
            print(f"   🏷️  Tag {tag_id}: {distance_cm:.1f}cm, rotation: ({euler[0]:.1f}°, {euler[1]:.1f}°, {euler[2]:.1f}°)")
        else:
            print(f"   🏷️  Tag {tag_id}: detected (no pose)")
        
        return result
    
    def show_results(self, results):
        """Display results with matplotlib"""
        if results and results["image"] is not None:
            image_rgb = cv2.cvtColor(results["image"], cv2.COLOR_BGR2RGB)
            
            plt.figure(figsize=(10, 8))
            plt.imshow(image_rgb)
            plt.title(f"AprilTag Detection - {len(results['detections'])} tag(s) found")
            plt.axis('off')
            plt.show()

def find_latest_photo():
    """Find the latest photo in the photos directory"""
    photos_dir = Path("photos")
    if not photos_dir.exists():
        return None
    
    photo_files = list(photos_dir.glob("*.jpg")) + list(photos_dir.glob("*.jpeg"))
    if not photo_files:
        return None
    
    latest = max(photo_files, key=os.path.getctime)
    return str(latest)

def main():
    """Simple AprilTag detection"""
    if not VISION_AVAILABLE:
        return
    
    parser = argparse.ArgumentParser(description="Detect AprilTags in images")
    parser.add_argument("image", nargs="?", help="Image file path")
    parser.add_argument("--latest", action="store_true", help="Use latest photo")
    parser.add_argument("--family", default="tag36h11", help="AprilTag family")
    parser.add_argument("--size", type=float, default=30, help="Tag size in mm")
    parser.add_argument("--show", action="store_true", help="Show annotated image")
    
    args = parser.parse_args()
    
    # Determine image path
    image_path = None
    if args.latest:
        image_path = find_latest_photo()
        if not image_path:
            print("❌ No photos found in photos/ directory")
            return
    elif args.image:
        image_path = args.image
    else:
        print("❌ Specify an image file or use --latest")
        return
    
    # Detect AprilTags
    detector = SimpleAprilTagDetector(args.family, args.size)
    results = detector.detect_in_image(image_path)
    
    if results and args.show:
        detector.show_results(results)

if __name__ == "__main__":
    main()
