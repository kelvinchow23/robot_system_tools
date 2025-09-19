#!/usr/bin/env python3
"""
Detection Filter Module
Provides noise filtering and median detection algorithms for visual servoing
"""

import numpy as np
import time
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime

class DetectionFilter:
    """Handles AprilTag detection filtering and noise reduction"""
    
    def __init__(self, apriltag_detector, config):
        """
        Initialize detection filter
        
        Args:
            apriltag_detector: AprilTag detection instance
            config: Visual servo configuration instance
        """
        self.detector = apriltag_detector
        self.config = config
        
    def get_filtered_tag_pose(self, tag_id: int) -> Optional[np.ndarray]:
        """
        Get filtered AprilTag pose using median filtering
        
        Args:
            tag_id: ID of AprilTag to detect
            
        Returns:
            Filtered 6DOF pose [x,y,z,rx,ry,rz] or None if detection fails
        """
        print(f"🔍 Detecting AprilTag {tag_id} with {self.config.detection_samples} samples...")
        
        valid_poses = []
        start_time = time.time()
        
        for sample in range(self.config.detection_samples):
            if time.time() - start_time > self.config.detection_timeout:
                print(f"⚠️  Detection timeout after {time.time() - start_time:.1f}s")
                break
                
            pose = self._single_detection(tag_id)
            if pose is not None:
                valid_poses.append(pose)
                print(f"   Sample {sample+1}: ✅")
            else:
                print(f"   Sample {sample+1}: ❌")
            
            # Brief pause between samples
            time.sleep(0.1)
        
        if not valid_poses:
            print(f"❌ No valid detections for tag {tag_id}")
            return None
        
        # Use median filtering for robustness
        filtered_pose = np.median(valid_poses, axis=0)
        
        # Calculate detection statistics
        poses_array = np.array(valid_poses)
        std_dev = np.std(poses_array, axis=0)
        
        print(f"✅ Filtered detection: {len(valid_poses)}/{self.config.detection_samples} samples")
        print(f"   Position std dev: [{std_dev[0]:.4f}, {std_dev[1]:.4f}, {std_dev[2]:.4f}]m")
        print(f"   Rotation std dev: [{std_dev[3]:.4f}, {std_dev[4]:.4f}, {std_dev[5]:.4f}]rad")
        
        return filtered_pose
    
    def _single_detection(self, tag_id: int) -> Optional[np.ndarray]:
        """
        Perform single AprilTag detection
        
        Args:
            tag_id: ID of AprilTag to detect
            
        Returns:
            6DOF pose [x,y,z,rx,ry,rz] or None if detection fails
        """
        try:
            # Capture image and detect tags
            image = self.detector.camera.capture_image()
            if image is None:
                return None
            
            detections = self.detector.detect_tags(image)
            
            # Find the target tag
            for detection in detections:
                if detection['tag_id'] == tag_id:
                    # Extract pose information
                    pose = np.array([
                        detection['translation'][0],
                        detection['translation'][1], 
                        detection['translation'][2],
                        detection['rotation'][0],
                        detection['rotation'][1],
                        detection['rotation'][2]
                    ])
                    return pose
            
            return None
            
        except Exception as e:
            print(f"⚠️  Detection error: {e}")
            return None
    
    def validate_pose_change(self, old_pose: np.ndarray, new_pose: np.ndarray) -> Tuple[bool, Dict[str, float]]:
        """
        Validate that pose change is within reasonable limits
        
        Args:
            old_pose: Previous pose [x,y,z,rx,ry,rz]
            new_pose: New pose [x,y,z,rx,ry,rz]
            
        Returns:
            (is_valid, metrics) tuple
        """
        if old_pose is None or new_pose is None:
            return True, {}
        
        delta = new_pose - old_pose
        
        # Calculate metrics
        translation_magnitude = np.linalg.norm(delta[:3])
        rotation_magnitude = np.linalg.norm(delta[3:])
        
        metrics = {
            'translation_change': translation_magnitude,
            'rotation_change': rotation_magnitude,
            'max_translation_axis': np.max(np.abs(delta[:3])),
            'max_rotation_axis': np.max(np.abs(delta[3:]))
        }
        
        # Validation checks
        max_expected_translation = 0.5  # 50cm - very large change detection
        max_expected_rotation = 1.57    # 90 degrees - very large change detection
        
        is_valid = (translation_magnitude < max_expected_translation and 
                   rotation_magnitude < max_expected_rotation)
        
        if not is_valid:
            print(f"⚠️  Large pose change detected:")
            print(f"   Translation: {translation_magnitude:.3f}m (max: {max_expected_translation:.3f}m)")
            print(f"   Rotation: {rotation_magnitude:.3f}rad (max: {max_expected_rotation:.3f}rad)")
        
        return is_valid, metrics