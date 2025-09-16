#!/usr/bin/env python3
"""
Debug AprilTag pose estimation
Take a single photo and analyze the detected pose
"""

import cv2
import numpy as np
import sys
import os
sys.path.append('..')
from apriltag_detection import AprilTagDetector
from pathlib import Path

def debug_apriltag_pose():
    """Debug a single AprilTag detection"""
    
    print("🔍 AprilTag Pose Debugging")
    print("=" * 30)
    
    # Initialize detector
    detector = AprilTagDetector(
        camera_calib_file="../camera_calibration/camera_calibration.yaml",
        tag_size=0.023  # 23mm tag
    )
    
    # Use one of your calibration photos
    test_image = "photos/capture_20250911_170450.jpg"
    
    if not Path(test_image).exists():
        print(f"❌ Test image not found: {test_image}")
        print("Please provide path to an AprilTag photo:")
        return
        
    print(f"📸 Analyzing: {test_image}")
    
    # Load and detect
    image = cv2.imread(test_image)
    if image is None:
        print(f"❌ Failed to load image")
        return
        
    detections = detector.detect_tags(image, estimate_pose=True)
    
    if not detections:
        print("❌ No AprilTags detected")
        return
        
    detection = detections[0]
    print(f"✅ Detected tag ID: {detection['id']}")
    print(f"📏 Quality score: {detection['quality']:.1f}")
    
    # Analyze pose
    pose = detection['pose']
    translation = np.array(pose['translation_vector'])
    rotation = np.array(pose['rotation_vector'])
    
    print(f"\n📍 Detected Pose:")
    print(f"   Translation: [{translation[0]:.4f}, {translation[1]:.4f}, {translation[2]:.4f}] m")
    print(f"   Distance: {np.linalg.norm(translation):.3f}m ({np.linalg.norm(translation)*1000:.0f}mm)")
    print(f"   Rotation: [{rotation[0]:.4f}, {rotation[1]:.4f}, {rotation[2]:.4f}] rad")
    
    # Expected vs actual analysis
    print(f"\n🤔 Does this make sense?")
    print(f"   • Is {np.linalg.norm(translation)*1000:.0f}mm distance realistic?")
    print(f"   • Translation direction: {translation/np.linalg.norm(translation)}")
    print(f"   • Positive Z = away from camera")
    print(f"   • Positive X = right in image")
    print(f"   • Positive Y = down in image")
    
    # Show image with detection
    cv2.imshow("AprilTag Detection Debug", image)
    print(f"\n💡 Press any key to close image window")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    debug_apriltag_pose()
