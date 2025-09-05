#!/usr/bin/env python3
"""
Hand-Eye Calibration Data Collection for UR Robot
Collects robot pose + AprilTag detection pairs for eye-in-hand calibration
"""

import numpy as np
import cv2
import yaml
import json
import time
import argparse
from datetime import datetime
from pathlib import Path
import sys
import os

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'robots', 'ur'))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'camera', 'picam'))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tests'))

# Force reload of URRobotInterface to pick up any recent changes
import importlib
import ur_robot_interface
importlib.reload(ur_robot_interface)

from ur_robot_interface import URRobotInterface
from picam import PiCam, PiCamConfig
from test_apriltag_detection import AprilTagDetector

class HandEyeDataCollector:
    """Collect hand-eye calibration data for UR robot with wrist-mounted camera"""
    
    def __init__(self, robot_ip, camera_config_file, apriltag_config):
        """
        Initialize data collector
        
        Args:
            robot_ip: IP address of UR robot
            camera_config_file: Path to camera configuration
            apriltag_config: AprilTag detection configuration
        """
        self.robot_ip = robot_ip
        self.apriltag_config = apriltag_config
        
        # Initialize robot in read-only mode (no remote control needed)
        print("🤖 Initializing UR robot...")
        self.robot = URRobotInterface(robot_ip, read_only=True)
        
        # Initialize camera
        print("📷 Initializing camera...")
        camera_config = PiCamConfig.from_yaml(camera_config_file)
        self.camera = PiCam(camera_config)
        
        if not self.camera.test_connection():
            raise RuntimeError("Failed to connect to camera server")
        
        # Initialize AprilTag detector
        print("🏷️  Initializing AprilTag detector...")
        self.detector = AprilTagDetector(
            tag_family=apriltag_config['tag_family'],
            tag_size_mm=apriltag_config['tag_size_mm'],
            calibration_file=apriltag_config.get('calibration_file')
        )
        
        # Data storage
        self.calibration_data = {
            'robot_poses': [],      # Robot TCP poses in base frame
            'camera_poses': [],     # AprilTag poses in camera frame
            'timestamps': [],       # Collection timestamps
            'robot_ip': robot_ip,
            'apriltag_config': apriltag_config,
            'collection_date': datetime.now().isoformat()
        }
        
        print("✅ Hand-eye data collector initialized")
    
    def detect_apriltag_in_image(self, image_path):
        """
        Detect AprilTag in captured image
        
        Args:
            image_path: Path to captured image
            
        Returns:
            dict: AprilTag detection result or None
        """
        image = cv2.imread(image_path)
        if image is None:
            print(f"❌ Failed to load image: {image_path}")
            return None
        
        detections = self.detector.detect_tags(image, estimate_pose=True)
        
        if not detections:
            print("❌ No AprilTag detected")
            return None
        
        if len(detections) > 1:
            print(f"⚠️  Multiple tags detected ({len(detections)}), using first one")
        
        detection = detections[0]
        
        if detection['pose'] is None:
            print("❌ AprilTag detected but pose estimation failed")
            return None
        
        print(f"✅ AprilTag {detection['tag_id']} detected with pose")
        print(f"   Quality: {detection['decision_margin']:.2f}")
        print(f"   Distance: {detection.get('distance_mm', 0):.1f}mm")
        
        return detection
    
    def collect_data_point(self, pose_index, total_poses):
        """
        Collect single calibration data point
        
        Args:
            pose_index: Current pose index
            total_poses: Total number of poses
            
        Returns:
            bool: True if data point collected successfully
        """
        print(f"\n📸 Collecting data point {pose_index + 1}/{total_poses}")
        
        # Get current robot pose
        robot_pose = self.robot.get_tcp_pose()
        print(f"🤖 Robot TCP pose: {self.robot.format_pose(robot_pose)}")
        
        # Capture image
        print("📷 Capturing image...")
        image_path = self.camera.capture_photo()
        if not image_path:
            print("❌ Failed to capture image")
            return False
        
        # Wait for camera to stabilize
        time.sleep(0.5)
        
        # Detect AprilTag
        print("🔍 Detecting AprilTag...")
        detection = self.detect_apriltag_in_image(image_path)
        
        if detection is None:
            print("❌ AprilTag detection failed")
            return False
        
        # Extract camera-to-tag transformation
        pose_data = detection['pose']
        camera_to_tag_t = np.array(pose_data['translation_vector'])
        camera_to_tag_r = np.array(pose_data['rotation_vector'])
        
        # Store data point
        timestamp = datetime.now().isoformat()
        
        self.calibration_data['robot_poses'].append(robot_pose.tolist())
        self.calibration_data['camera_poses'].append({
            'translation': camera_to_tag_t.tolist(),
            'rotation_vector': camera_to_tag_r.tolist(),
            'tag_id': detection['tag_id'],
            'quality': detection['decision_margin'],
            'image_path': str(image_path)
        })
        self.calibration_data['timestamps'].append(timestamp)
        
        print(f"✅ Data point {pose_index + 1} collected successfully")
        return True
    
    def interactive_collection(self):
        """
        Interactive data collection mode (manual only for read-only mode)
        """
        print("\n🎯 Interactive Hand-Eye Calibration Data Collection")
        print("=" * 60)
        
        # Read-only mode - manual collection only
        print("🖱️  Manual collection mode (read-only)")
        print("   Move robot manually in freedrive and press ENTER to collect data")
        
        print("\n📝 Instructions:")
        print("   - Put robot in FREEDRIVE mode for safety")
        print("   - Manually move robot to diverse poses")
        print("   - Ensure AprilTag is visible from all poses")
        print("   - Vary robot orientation significantly between poses")
        print("   - Collect at least 10 good data points")
        print("   - Press 'q' to quit and save")
        
        input("\nPress ENTER to start collection...")
        
        collected_count = 0
        pose_index = 0
        
        while True:
            print(f"\n📍 Pose {pose_index + 1}")
            print("   - Manually move robot to a new diverse pose")
            print("   - Ensure AprilTag is clearly visible to camera")
            print("   - Make sure robot orientation varies significantly from previous poses")
            print("   - Freedrive mode is recommended for safety")
            
            user_input = input(f"\nPress ENTER to collect data point {pose_index + 1} (or 'q' to quit): ").strip().lower()
            
            if user_input == 'q':
                break
            
            if self.collect_data_point(pose_index, -1):
                collected_count += 1
                pose_index += 1
        
        print(f"\n📊 Collection Summary:")
        print(f"   Total data points collected: {collected_count}")
        print(f"   Minimum recommended: 10")
        
        if collected_count >= 10:
            print("✅ Sufficient data collected for calibration")
        else:
            print("⚠️  More data points recommended for robust calibration")
    
    def save_data(self, output_file="handeye_data.json"):
        """
        Save collected calibration data
        
        Args:
            output_file: Output file path
        """
        # Always save to the handeye_calibration directory
        script_dir = Path(__file__).parent
        output_path = script_dir / output_file
        
        # Add timestamp to filename if not specified
        if output_path.name == "handeye_data.json":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = script_dir / f"handeye_data_{timestamp}.json"
        
        print(f"\n💾 Saving calibration data to: {output_path}")
        
        with open(output_path, 'w') as f:
            json.dump(self.calibration_data, f, indent=2)
        
        print(f"✅ Calibration data saved")
        print(f"   Data points: {len(self.calibration_data['robot_poses'])}")
        print(f"   File size: {output_path.stat().st_size} bytes")
        
        return output_path
    
    def close(self):
        """Clean up resources"""
        if hasattr(self, 'robot'):
            self.robot.close()

def main():
    parser = argparse.ArgumentParser(description='Hand-Eye Calibration Data Collection')
    parser.add_argument('--robot-ip', default='192.168.0.10',
                       help='UR robot IP address')
    parser.add_argument('--camera-config', default='camera_../client_config.yaml',
                       help='Camera configuration file')
    parser.add_argument('--tag-family', default='tag36h11',
                       choices=['tag36h11', 'tag25h9', 'tag16h5'],
                       help='AprilTag family')
    parser.add_argument('--tag-size', type=float, default=23.0,
                       help='AprilTag size in millimeters')
    parser.add_argument('--calibration-file', default='../camera_calibration/camera_calibration.yaml',
                       help='Camera calibration file')
    parser.add_argument('--output', default='handeye_data.json',
                       help='Output data file')
    
    args = parser.parse_args()
    
    print("🤖👁️ UR Robot Hand-Eye Calibration Data Collection")
    print("=" * 60)
    
    # AprilTag configuration
    apriltag_config = {
        'tag_family': args.tag_family,
        'tag_size_mm': args.tag_size,
        'calibration_file': args.calibration_file
    }
    
    try:
        collector = HandEyeDataCollector(
            robot_ip=args.robot_ip,
            camera_config_file=args.camera_config,
            apriltag_config=apriltag_config
        )
        
        # Collect calibration data (manual mode only in read-only)
        collector.interactive_collection()
        
        # Save data
        if len(collector.calibration_data['robot_poses']) > 0:
            output_path = collector.save_data(args.output)
            print(f"\n🎉 Data collection completed!")
            print(f"   Next step: python calculate_handeye_calibration.py --input {output_path}")
        else:
            print("❌ No data collected")
    
    except KeyboardInterrupt:
        print("\n🛑 Data collection interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'collector' in locals():
            collector.close()

if __name__ == "__main__":
    main()
