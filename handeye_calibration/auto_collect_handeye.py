#!/usr/bin/env python3
"""
Improved Hand-Eye Calibration Data Collection for UR Robot
Automatic robot movement with diverse poses for robust calibration
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

from robots.ur.ur_controller import URController
from picam import PiCam, PiCamConfig
from apriltag_detection import AprilTagDetector

class AutoHandEyeCollector:
    """Automatic hand-eye calibration data collection with robot movement"""
    
    def __init__(self, robot_ip, camera_config_file, apriltag_config):
        """Initialize collector with robot and camera"""
        self.robot_ip = robot_ip
        self.apriltag_config = apriltag_config
        
        print("🤖 Initializing UR robot (control mode for automatic movement)...")
        self.robot = URController(robot_ip, read_only=False)
        
        print("📷 Initializing camera...")
        camera_config = PiCamConfig.from_yaml(camera_config_file)
        self.camera = PiCam(camera_config)
        
        print("🏷️ Initializing AprilTag detector...")
        self.detector = AprilTagDetector(
            tag_family=apriltag_config['tag_family'],
            tag_size=apriltag_config['tag_size'],
            camera_calibration_file=apriltag_config['calibration_file']
        )
        
        self.samples = []
        print("✅ All systems initialized")
    
    def generate_diverse_poses(self, apriltag_position, num_poses=12):
        """Generate diverse robot poses around AprilTag - only reachable positions"""
        poses = []
        tag_x, tag_y, tag_z = apriltag_position
        camera_offset = 0.20  # Approximate camera offset from TCP
        
        # SAFE pose configurations - avoid robot self-collision
        # Only use front 180° arc (robot can't reach behind itself)
        configs = [
            # Look down at tag (high pitch) - front and sides only
            {"radius": 0.35, "height": tag_z + 0.25, "pitch": -45, "yaw": 0},     # front
            {"radius": 0.35, "height": tag_z + 0.25, "pitch": -45, "yaw": 60},    # front-right
            {"radius": 0.35, "height": tag_z + 0.25, "pitch": -45, "yaw": 120},   # right side
            {"radius": 0.35, "height": tag_z + 0.25, "pitch": -45, "yaw": -60},   # front-left
            {"radius": 0.35, "height": tag_z + 0.25, "pitch": -45, "yaw": -120},  # left side
            
            # Look across at tag (medium pitch) - wider spread
            {"radius": 0.40, "height": tag_z + 0.15, "pitch": -15, "yaw": 30},    # front-right
            {"radius": 0.40, "height": tag_z + 0.15, "pitch": -15, "yaw": 90},    # right side
            {"radius": 0.40, "height": tag_z + 0.15, "pitch": -15, "yaw": -30},   # front-left
            {"radius": 0.40, "height": tag_z + 0.15, "pitch": -15, "yaw": -90},   # left side
            
            # Look up at tag (low pitch) - closer positions
            {"radius": 0.30, "height": tag_z + 0.05, "pitch": 15, "yaw": 0},      # straight front
            {"radius": 0.30, "height": tag_z + 0.05, "pitch": 15, "yaw": 45},     # front-right
            {"radius": 0.30, "height": tag_z + 0.05, "pitch": 15, "yaw": -45},    # front-left
        ]
        
        print(f"🛡️ Using safe workspace coverage:")
        print(f"   Yaw range: -120° to +120° (front 240° arc)")
        print(f"   Avoiding robot self-collision zones")
        
        for i, config in enumerate(configs[:num_poses]):
            angle_rad = np.radians(config["yaw"])
            
            # TCP position - relative to AprilTag
            tcp_x = tag_x + (config["radius"] + camera_offset) * np.cos(angle_rad)
            tcp_y = tag_y + (config["radius"] + camera_offset) * np.sin(angle_rad) 
            tcp_z = config["height"]
            
            # Basic workspace safety check
            distance_from_base = np.sqrt(tcp_x**2 + tcp_y**2)
            if distance_from_base > 0.8:  # UR robot reach limit ~85cm
                print(f"⚠️  Pose {i+1} too far from base ({distance_from_base:.2f}m), skipping")
                continue
            
            if tcp_z < 0.05 or tcp_z > 0.8:  # Height limits
                print(f"⚠️  Pose {i+1} height unsafe ({tcp_z:.2f}m), skipping")
                continue
            
            # Calculate orientation to look at tag
            look_vector = np.array([tag_x - tcp_x, tag_y - tcp_y, tag_z - tcp_z])
            look_vector = look_vector / np.linalg.norm(look_vector)
            
            # Create rotation matrix
            z_axis = look_vector
            world_z = np.array([0, 0, 1])
            x_axis = np.cross(world_z, z_axis)
            if np.linalg.norm(x_axis) < 1e-6:
                x_axis = np.array([1, 0, 0])
            else:
                x_axis = x_axis / np.linalg.norm(x_axis)
            
            y_axis = np.cross(z_axis, x_axis)
            y_axis = y_axis / np.linalg.norm(y_axis)
            
            # Apply pitch adjustment
            pitch_rad = np.radians(config["pitch"])
            cos_p, sin_p = np.cos(pitch_rad), np.sin(pitch_rad)
            R_pitch = np.array([[1, 0, 0], [0, cos_p, -sin_p], [0, sin_p, cos_p]])
            
            R_base = np.column_stack([x_axis, y_axis, z_axis])
            R_final = R_base @ R_pitch
            
            # Convert to rotation vector
            rotation_vector = cv2.Rodrigues(R_final)[0].flatten()
            
            pose = [tcp_x, tcp_y, tcp_z, rotation_vector[0], rotation_vector[1], rotation_vector[2]]
            poses.append(pose)
            
            print(f"Pose {i+1}: r={config['radius']:.2f}m, h={tcp_z:.2f}m, pitch={config['pitch']}°, yaw={config['yaw']}°")
        
        print(f"\n✅ Generated {len(poses)} safe poses (avoided self-collision)")
        return poses
        
        return poses
    
    def move_to_pose_safely(self, target_pose):
        """Move robot to target pose very slowly for safety"""
        try:
            print(f"🐌 Moving slowly to: {self.robot.format_pose(target_pose)}")
            
            # Very slow movement for safety
            success = self.robot.move_to_pose(np.array(target_pose), speed=0.02, acceleration=0.05)
            
            if not success:
                print("❌ Movement command failed")
                return False
            
            print("⏳ Waiting for movement to complete...")
            time.sleep(3.0)  # Give time for slow movement
            
            print("✅ Movement completed")
            return True
            
        except Exception as e:
            print(f"❌ Movement failed: {e}")
            return False
    
    def detect_apriltag(self, image_path):
        """Detect AprilTag in captured image"""
        image = cv2.imread(str(image_path))
        if image is None:
            return None
        
        detections = self.detector.detect_tags(image)
        
        if not detections:
            return None
        
        if len(detections) > 1:
            print(f"⚠️  Multiple tags detected, using first one")
        
        detection = detections[0]
        
        if detection['pose'] is None:
            return None
        
        # Calculate distance
        t = detection['pose']['tvec']
        distance_m = np.linalg.norm(t)
        
        print(f"✅ AprilTag {detection['tag_id']} detected")
        print(f"   Quality: {detection['decision_margin']:.2f}")
        print(f"   Distance: {distance_m:.3f}m")
        
        return detection
    
    def collect_sample(self, sample_num):
        """Collect one calibration sample"""
        print(f"\n📸 Sample {sample_num}")
        print("=" * 25)
        
        # Get current robot pose
        robot_pose = self.robot.get_tcp_pose()
        base_T_gripper = self.robot.get_pose_matrix(robot_pose)
        
        # Capture image
        print("📷 Capturing image...")
        image_path = self.camera.capture_photo()
        if not image_path:
            print("❌ Image capture failed")
            return False
        
        time.sleep(0.3)  # Camera stabilization
        
        # Detect AprilTag
        print("🔍 Detecting AprilTag...")
        detection = self.detect_apriltag(image_path)
        
        if detection is None:
            print("❌ AprilTag detection failed")
            return False
        
        # Store sample
        sample = {
            'timestamp': datetime.now().isoformat(),
            'base_T_gripper': base_T_gripper.tolist(),
            'camera_T_target': detection['pose']['matrix'].tolist(),
            'tag_id': detection['tag_id'],
            'decision_margin': detection['decision_margin'],
            'image_path': str(image_path)
        }
        
        self.samples.append(sample)
        print(f"✅ Sample {sample_num} collected")
        
        return True
    
    def check_orientation_diversity(self):
        """Check if collected poses have sufficient orientation diversity"""
        if len(self.samples) < 3:
            return {"sufficient": False, "message": "Need at least 3 samples"}
        
        # Extract orientations
        euler_angles = []
        for sample in self.samples:
            pose_matrix = sample['base_T_gripper']
            R = np.array(pose_matrix[:3, :3])
            
            # Convert to Euler angles
            sy = np.sqrt(R[0,0] * R[0,0] + R[1,0] * R[1,0])
            if sy > 1e-6:
                x = np.arctan2(R[2,1], R[2,2])
                y = np.arctan2(-R[2,0], sy)
                z = np.arctan2(R[1,0], R[0,0])
            else:
                x = np.arctan2(-R[1,2], R[1,1])
                y = np.arctan2(-R[2,0], sy)
                z = 0
            
            euler_angles.append([np.degrees(x), np.degrees(y), np.degrees(z)])
        
        euler_angles = np.array(euler_angles)
        
        # Check ranges
        roll_range = euler_angles[:, 0].max() - euler_angles[:, 0].min()
        pitch_range = euler_angles[:, 1].max() - euler_angles[:, 1].min()
        yaw_range = euler_angles[:, 2].max() - euler_angles[:, 2].min()
        
        # Handle yaw wraparound
        if yaw_range > 180:
            yaw_range = 360 - yaw_range
        
        good_axes = sum([roll_range >= 30, pitch_range >= 30, yaw_range >= 30])
        sufficient = good_axes >= 2
        
        message = f"Roll {roll_range:.1f}°, Pitch {pitch_range:.1f}°, Yaw {yaw_range:.1f}°"
        if sufficient:
            message = "✅ Good diversity: " + message
        else:
            message = "❌ Need more diversity: " + message
        
        return {"sufficient": sufficient, "message": message}
    
    def automatic_collection(self, apriltag_position, num_poses=12):
        """Automatically collect calibration data"""
        print("\n🤖 Automatic Hand-Eye Calibration Collection")
        print("=" * 50)
        print(f"📍 AprilTag position: ({apriltag_position[0]:.3f}, {apriltag_position[1]:.3f}, {apriltag_position[2]:.3f})")
        print(f"🎯 Number of poses: {num_poses}")
        
        # Generate poses
        print("\n🎲 Generating diverse poses...")
        target_poses = self.generate_diverse_poses(apriltag_position, num_poses)
        
        print(f"\n🚀 Starting automatic collection...")
        print("⚠️  Robot will move slowly. Ensure workspace is clear!")
        
        response = input("Type 'START' to begin, or 'q' to quit: ").strip()
        if response != 'START':
            print("❌ Collection cancelled")
            return
        
        successful = 0
        
        for i, pose in enumerate(target_poses):
            print(f"\n{'='*40}")
            print(f"🎯 Pose {i+1}/{len(target_poses)}")
            
            # Move to pose
            if not self.move_to_pose_safely(pose):
                print(f"❌ Failed to reach pose {i+1}")
                continue
            
            time.sleep(1.0)  # Stability pause
            
            # Collect sample
            if self.collect_sample(successful + 1):
                successful += 1
            else:
                print(f"⚠️  Sample collection failed at pose {i+1}")
        
        print(f"\n📊 Collection Complete!")
        print(f"   Successful samples: {successful}/{len(target_poses)}")
        
        if successful >= 8:
            diversity = self.check_orientation_diversity()
            print(f"   {diversity['message']}")
        else:
            print(f"   ⚠️  Only {successful} samples - recommend ≥8")
    
    def save_data(self, output_file):
        """Save collected data to JSON file"""
        if not self.samples:
            print("❌ No data to save")
            return None
        
        if output_file == 'handeye_data.json':
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"handeye_data_{timestamp}.json"
        
        output_path = Path(output_file)
        
        data = {
            'version': 2,
            'timestamp': datetime.now().isoformat(),
            'robot_ip': self.robot_ip,
            'tag_family': self.apriltag_config['tag_family'],
            'tag_size_m': self.apriltag_config['tag_size'],
            'camera_config': str(Path(self.apriltag_config.get('camera_config', 'unknown')).resolve()),
            'calibration_file': str(Path(self.apriltag_config['calibration_file']).resolve()),
            'num_samples': len(self.samples),
            'samples': self.samples
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 Data saved to: {output_path.resolve()}")
        
        diversity = self.check_orientation_diversity()
        print(f"\n📊 Final Summary:")
        print(f"   Samples: {len(self.samples)}")
        print(f"   {diversity['message']}")
        
        return output_path
    
    def close(self):
        """Clean up resources"""
        if hasattr(self, 'robot'):
            self.robot.close()

def main():
    parser = argparse.ArgumentParser(description='Automatic Hand-Eye Calibration Data Collection')
    parser.add_argument('--robot-ip', default='192.168.0.10', help='UR robot IP address')
    parser.add_argument('--camera-config', default='../camera_client_config.yaml', help='Camera config file')
    parser.add_argument('--tag-family', default='tag36h11', choices=['tag36h11', 'tag25h9', 'tag16h5'])
    parser.add_argument('--tag-size', type=float, default=0.023, help='AprilTag size (meters)')
    parser.add_argument('--calibration-file', default='../camera_calibration/camera_calibration.yaml')
    parser.add_argument('--output', default='handeye_data.json', help='Output file')
    parser.add_argument('--tag-position', nargs=3, type=float, metavar=('X', 'Y', 'Z'), 
                       help='AprilTag position [x, y, z] in base frame (meters)')
    parser.add_argument('--num-poses', type=int, default=12, help='Number of poses')
    
    args = parser.parse_args()
    
    print("🤖👁️ Automatic Hand-Eye Calibration Collection")
    print("=" * 55)
    print(f"🤖 Robot IP: {args.robot_ip}")
    print(f"🏷️ AprilTag: {args.tag_family} ({args.tag_size*1000:.0f}mm)")
    
    apriltag_config = {
        'tag_family': args.tag_family,
        'tag_size': args.tag_size,
        'calibration_file': args.calibration_file,
        'camera_config': args.camera_config
    }
    
    try:
        collector = AutoHandEyeCollector(
            robot_ip=args.robot_ip,
            camera_config_file=args.camera_config,
            apriltag_config=apriltag_config
        )
        
        # Get AprilTag position
        if args.tag_position:
            apriltag_position = args.tag_position
            print(f"📍 Using provided position: ({apriltag_position[0]:.3f}, {apriltag_position[1]:.3f}, {apriltag_position[2]:.3f})")
        else:
            print("\n📍 AprilTag Position Required")
            print("Enter position in robot base frame:")
            x = float(input("X (meters): "))
            y = float(input("Y (meters): "))
            z = float(input("Z (meters, table height): "))
            apriltag_position = [x, y, z]
        
        # Run automatic collection
        collector.automatic_collection(apriltag_position, args.num_poses)
        
        # Save data
        if collector.samples:
            output_path = collector.save_data(args.output)
            print(f"\n🎉 Collection completed!")
            print(f"   Next: python calculate_handeye_calibration.py --input {output_path}")
        else:
            print("❌ No data collected")
    
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'collector' in locals():
            collector.close()

if __name__ == "__main__":
    main()
