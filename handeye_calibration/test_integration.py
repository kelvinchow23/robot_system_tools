#!/usr/bin/env python3
"""
Test Hand-Eye Calibration Integration
Demonstrates complete workflow from AprilTag detection to robot coordinates
"""

import numpy as np
import argparse
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ur_robot_interface import URRobotInterface
from picam import PiCam, PiCamConfig
from test_apriltag_detection import AprilTagDetector
from coordinate_transformer import CoordinateTransformer

def test_integration(robot_ip, camera_config, calibration_file, apriltag_config):
    """
    Test complete integration: camera -> AprilTag -> robot coordinates
    
    Args:
        robot_ip: Robot IP address
        camera_config: Camera configuration file
        calibration_file: Hand-eye calibration file
        apriltag_config: AprilTag configuration
    """
    print("🤖👁️ Hand-Eye Calibration Integration Test")
    print("=" * 60)
    
    # Initialize components
    print("🔧 Initializing components...")
    
    # Robot interface
    robot = URRobotInterface(robot_ip)
    if not robot.test_connection():
        print("❌ Robot connection failed")
        return False
    
    # Camera
    config = PiCamConfig.from_yaml(camera_config)
    camera = PiCam(config)
    if not camera.test_connection():
        print("❌ Camera connection failed")
        return False
    
    # AprilTag detector
    detector = AprilTagDetector(
        tag_family=apriltag_config['tag_family'],
        tag_size_mm=apriltag_config['tag_size_mm'],
        calibration_file=apriltag_config.get('calibration_file')
    )
    
    # Coordinate transformer
    transformer = CoordinateTransformer(calibration_file)
    transformer.print_calibration_summary()
    
    print("✅ All components initialized")
    
    # Test detection and transformation
    print("\n📸 Testing AprilTag detection and coordinate transformation...")
    
    # Get current robot pose
    robot_pose = robot.get_tcp_pose()
    print(f"🤖 Current robot TCP pose: {robot.format_pose(robot_pose)}")
    
    # Capture image and detect AprilTag
    print("📷 Capturing image...")
    image_path = camera.capture_photo()
    if not image_path:
        print("❌ Failed to capture image")
        return False
    
    # Load and process image
    import cv2
    image = cv2.imread(image_path)
    if image is None:
        print("❌ Failed to load captured image")
        return False
    
    print("🔍 Detecting AprilTags...")
    detections = detector.detect_tags(image, estimate_pose=True)
    
    if not detections:
        print("❌ No AprilTags detected")
        print("   Ensure AprilTag is visible and well-lit")
        return False
    
    print(f"✅ Detected {len(detections)} AprilTag(s)")
    
    # Process each detection
    for i, detection in enumerate(detections):
        print(f"\n🏷️  AprilTag {i+1} (ID: {detection['tag_id']}):")
        print(f"   Quality: {detection['decision_margin']:.2f}")
        print(f"   Hamming: {detection['hamming']}")
        
        if detection['pose'] is None:
            print("   ❌ No pose estimation available")
            continue
        
        # Camera frame pose
        camera_pose = detection['pose']
        camera_pos = np.array(camera_pose['translation_vector'])
        camera_rot = np.array(camera_pose['rotation_vector'])
        
        print(f"   📷 Camera frame pose:")
        print(f"     Position: [{camera_pos[0]:+7.1f}, {camera_pos[1]:+7.1f}, {camera_pos[2]:+7.1f}] mm")
        print(f"     Distance: {detection.get('distance_mm', 0):.1f} mm")
        
        # Transform to robot frame
        robot_detection = transformer.transform_apriltag_detection(detection, robot_pose)
        
        if 'robot_frame_pose' in robot_detection:
            robot_pos = np.array(robot_detection['robot_frame_pose']['translation_vector'])
            robot_rot = np.array(robot_detection['robot_frame_pose']['rotation_vector'])
            
            print(f"   🤖 Robot base frame pose:")
            print(f"     Position: [{robot_pos[0]:+7.3f}, {robot_pos[1]:+7.3f}, {robot_pos[2]:+7.3f}] m")
            print(f"     Distance from origin: {np.linalg.norm(robot_pos):.3f} m")
            print(f"     Rotation: [{np.degrees(robot_rot[0]):+6.1f}, {np.degrees(robot_rot[1]):+6.1f}, {np.degrees(robot_rot[2]):+6.1f}] deg")
            
            # Calculate relative position to robot TCP
            tcp_pos = robot_pose[:3]
            relative_pos = robot_pos - tcp_pos
            print(f"   📐 Relative to TCP: [{relative_pos[0]:+7.3f}, {relative_pos[1]:+7.3f}, {relative_pos[2]:+7.3f}] m")
            
            # Demonstrate potential robot motion
            print(f"   💡 To move TCP to tag position:")
            target_pose = robot_pose.copy()
            target_pose[:3] = robot_pos
            target_pose[2] += 0.05  # 5cm above tag
            print(f"     Target pose: {robot.format_pose(target_pose)}")
            
        else:
            print("   ❌ Failed to transform to robot frame")
    
    print("\n✅ Integration test completed successfully!")
    print("\n📝 Next steps:")
    print("   1. Use robot_detection['robot_frame_pose']['translation_vector'] for robot motion")
    print("   2. Add offset for safe approach poses")
    print("   3. Implement pick and place logic")
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Hand-Eye Calibration Integration Test')
    parser.add_argument('--robot-ip', default='192.168.1.100',
                       help='Robot IP address')
    parser.add_argument('--camera-config', default='../client_config.yaml',
                       help='Camera configuration file')
    parser.add_argument('--calibration', required=True,
                       help='Hand-eye calibration file')
    parser.add_argument('--tag-family', default='tag36h11',
                       help='AprilTag family')
    parser.add_argument('--tag-size', type=float, default=23.0,
                       help='AprilTag size in millimeters')
    parser.add_argument('--camera-calib', default='../camera_calibration/camera_calibration.yaml',
                       help='Camera intrinsics calibration file')
    
    args = parser.parse_args()
    
    apriltag_config = {
        'tag_family': args.tag_family,
        'tag_size_mm': args.tag_size,
        'calibration_file': args.camera_calib
    }
    
    try:
        success = test_integration(
            robot_ip=args.robot_ip,
            camera_config=args.camera_config,
            calibration_file=args.calibration,
            apriltag_config=apriltag_config
        )
        
        if success:
            print("\n🎉 All tests passed!")
        else:
            print("\n❌ Test failed")
            
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
