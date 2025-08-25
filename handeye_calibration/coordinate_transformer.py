#!/usr/bin/env python3
"""
Coordinate Transformer for Hand-Eye Calibrated Robot System
Transforms AprilTag poses from camera frame to robot base frame
"""

import numpy as np
import yaml
import argparse
from pathlib import Path
from scipy.spatial.transform import Rotation as R

class CoordinateTransformer:
    """Transform coordinates between camera and robot frames using hand-eye calibration"""
    
    def __init__(self, handeye_calibration_file):
        """
        Initialize coordinate transformer
        
        Args:
            handeye_calibration_file: Path to hand-eye calibration YAML file
        """
        self.handeye_calibration_file = handeye_calibration_file
        self.calibration = None
        self.T_camera_to_robot = None
        
        self.load_calibration()
    
    def load_calibration(self):
        """Load hand-eye calibration from file"""
        print(f"📂 Loading hand-eye calibration from: {self.handeye_calibration_file}")
        
        with open(self.handeye_calibration_file, 'r') as f:
            self.calibration = yaml.safe_load(f)
        
        if not self.calibration.get('success', False):
            raise ValueError("Calibration file indicates unsuccessful calibration")
        
        # Extract transformation matrix
        if 'camera_to_robot_matrix' in self.calibration:
            self.T_camera_to_robot = np.array(self.calibration['camera_to_robot_matrix'])
        else:
            # Construct from rotation and translation
            R_cam_to_robot = np.array(self.calibration['camera_to_robot_R'])
            t_cam_to_robot = np.array(self.calibration['camera_to_robot_t'])
            
            self.T_camera_to_robot = np.eye(4)
            self.T_camera_to_robot[:3, :3] = R_cam_to_robot
            self.T_camera_to_robot[:3, 3] = t_cam_to_robot
        
        print(f"✅ Hand-eye calibration loaded")
        print(f"   Method: {self.calibration.get('method', 'Unknown')}")
        print(f"   Calibration date: {self.calibration.get('calibration_date', 'Unknown')}")
        print(f"   Data points used: {self.calibration.get('num_data_points', 'Unknown')}")
    
    def transform_pose_camera_to_robot(self, camera_pose, robot_tcp_pose):
        """
        Transform pose from camera frame to robot base frame
        
        Args:
            camera_pose: Pose in camera frame [x, y, z, rx, ry, rz] or transformation matrix
            robot_tcp_pose: Current robot TCP pose [x, y, z, rx, ry, rz]
            
        Returns:
            np.array: Pose in robot base frame [x, y, z, rx, ry, rz]
        """
        # Convert camera pose to transformation matrix if needed
        if camera_pose.shape == (6,):
            T_camera_to_object = self.pose_to_matrix(camera_pose)
        elif camera_pose.shape == (4, 4):
            T_camera_to_object = camera_pose
        else:
            raise ValueError("Invalid camera pose format")
        
        # Convert robot TCP pose to transformation matrix
        T_base_to_tcp = self.pose_to_matrix(robot_tcp_pose)
        
        # Transform: Base -> TCP -> Camera -> Object
        T_base_to_object = T_base_to_tcp @ self.T_camera_to_robot @ T_camera_to_object
        
        # Convert back to pose format
        return self.matrix_to_pose(T_base_to_object)
    
    def transform_point_camera_to_robot(self, camera_point, robot_tcp_pose):
        """
        Transform 3D point from camera frame to robot base frame
        
        Args:
            camera_point: 3D point in camera frame [x, y, z]
            robot_tcp_pose: Current robot TCP pose [x, y, z, rx, ry, rz]
            
        Returns:
            np.array: 3D point in robot base frame [x, y, z]
        """
        # Convert to homogeneous coordinates
        camera_point_homo = np.append(camera_point, 1.0)
        
        # Convert robot TCP pose to transformation matrix
        T_base_to_tcp = self.pose_to_matrix(robot_tcp_pose)
        
        # Transform: Base -> TCP -> Camera -> Point
        T_base_to_camera = T_base_to_tcp @ self.T_camera_to_robot
        
        # Transform point
        base_point_homo = T_base_to_camera @ camera_point_homo
        
        return base_point_homo[:3]
    
    def transform_apriltag_detection(self, apriltag_detection, robot_tcp_pose):
        """
        Transform AprilTag detection from camera frame to robot base frame
        
        Args:
            apriltag_detection: AprilTag detection dictionary with pose information
            robot_tcp_pose: Current robot TCP pose [x, y, z, rx, ry, rz]
            
        Returns:
            dict: AprilTag detection with pose in robot base frame
        """
        if apriltag_detection.get('pose') is None:
            print("⚠️  No pose information in AprilTag detection")
            return apriltag_detection
        
        pose_data = apriltag_detection['pose']
        
        # Extract camera-frame pose
        camera_translation = np.array(pose_data['translation_vector'])
        camera_rotation_vec = np.array(pose_data['rotation_vector'])
        
        # Create transformation matrix
        camera_rotation_mat = R.from_rotvec(camera_rotation_vec).as_matrix()
        T_camera_to_tag = np.eye(4)
        T_camera_to_tag[:3, :3] = camera_rotation_mat
        T_camera_to_tag[:3, 3] = camera_translation
        
        # Transform to robot base frame
        robot_pose = self.transform_pose_camera_to_robot(T_camera_to_tag, robot_tcp_pose)
        
        # Create enhanced detection result
        result = apriltag_detection.copy()
        result['robot_frame_pose'] = {
            'translation_vector': robot_pose[:3].tolist(),
            'rotation_vector': robot_pose[3:].tolist(),
            'robot_tcp_pose': robot_tcp_pose.tolist(),
            'transformation_matrix': self.pose_to_matrix(robot_pose).tolist()
        }
        
        # Calculate distance in robot frame
        robot_distance = np.linalg.norm(robot_pose[:3])
        result['robot_frame_distance_m'] = float(robot_distance)
        
        return result
    
    def pose_to_matrix(self, pose):
        """
        Convert pose [x, y, z, rx, ry, rz] to 4x4 transformation matrix
        
        Args:
            pose: Pose as [x, y, z, rx, ry, rz]
            
        Returns:
            np.array: 4x4 transformation matrix
        """
        translation = pose[:3]
        rotation_vector = pose[3:]
        
        rotation_matrix = R.from_rotvec(rotation_vector).as_matrix()
        
        transform = np.eye(4)
        transform[:3, :3] = rotation_matrix
        transform[:3, 3] = translation
        
        return transform
    
    def matrix_to_pose(self, transform_matrix):
        """
        Convert 4x4 transformation matrix to pose [x, y, z, rx, ry, rz]
        
        Args:
            transform_matrix: 4x4 transformation matrix
            
        Returns:
            np.array: Pose as [x, y, z, rx, ry, rz]
        """
        translation = transform_matrix[:3, 3]
        rotation_matrix = transform_matrix[:3, :3]
        rotation_vector = R.from_matrix(rotation_matrix).as_rotvec()
        
        return np.concatenate([translation, rotation_vector])
    
    def get_calibration_info(self):
        """
        Get information about the loaded calibration
        
        Returns:
            dict: Calibration information
        """
        if self.calibration is None:
            return None
        
        return {
            'method': self.calibration.get('method', 'Unknown'),
            'calibration_date': self.calibration.get('calibration_date', 'Unknown'),
            'num_data_points': self.calibration.get('num_data_points', 'Unknown'),
            'camera_to_robot_pose': self.calibration.get('camera_to_robot_pose', None),
            'success': self.calibration.get('success', False)
        }
    
    def print_calibration_summary(self):
        """Print summary of loaded calibration"""
        info = self.get_calibration_info()
        if info is None:
            print("❌ No calibration loaded")
            return
        
        print("📊 Hand-Eye Calibration Summary:")
        print(f"   Method: {info['method']}")
        print(f"   Date: {info['calibration_date']}")
        print(f"   Data points: {info['num_data_points']}")
        print(f"   Status: {'✅ Success' if info['success'] else '❌ Failed'}")
        
        if info['camera_to_robot_pose']:
            pose = np.array(info['camera_to_robot_pose'])
            print(f"   Camera to Robot:")
            print(f"     Translation: [{pose[0]:.4f}, {pose[1]:.4f}, {pose[2]:.4f}] m")
            print(f"     Rotation: [{np.degrees(pose[3]):.2f}, {np.degrees(pose[4]):.2f}, {np.degrees(pose[5]):.2f}] degrees")

def main():
    parser = argparse.ArgumentParser(description='Coordinate Transformer Test')
    parser.add_argument('--calibration', required=True,
                       help='Hand-eye calibration file (YAML)')
    parser.add_argument('--test-pose', nargs=6, type=float,
                       metavar=('x', 'y', 'z', 'rx', 'ry', 'rz'),
                       help='Test camera pose to transform')
    parser.add_argument('--robot-pose', nargs=6, type=float,
                       metavar=('x', 'y', 'z', 'rx', 'ry', 'rz'),
                       default=[0.3, 0.0, 0.5, 0.0, 3.14159, 0.0],
                       help='Robot TCP pose')
    
    args = parser.parse_args()
    
    print("🔄 Coordinate Transformer Test")
    print("=" * 50)
    
    try:
        # Initialize transformer
        transformer = CoordinateTransformer(args.calibration)
        transformer.print_calibration_summary()
        
        if args.test_pose:
            print(f"\n🧪 Testing coordinate transformation:")
            
            camera_pose = np.array(args.test_pose)
            robot_tcp_pose = np.array(args.robot_pose)
            
            print(f"   Camera pose: [{camera_pose[0]:.4f}, {camera_pose[1]:.4f}, {camera_pose[2]:.4f}, {np.degrees(camera_pose[3]):.2f}°, {np.degrees(camera_pose[4]):.2f}°, {np.degrees(camera_pose[5]):.2f}°]")
            print(f"   Robot TCP pose: [{robot_tcp_pose[0]:.4f}, {robot_tcp_pose[1]:.4f}, {robot_tcp_pose[2]:.4f}, {np.degrees(robot_tcp_pose[3]):.2f}°, {np.degrees(robot_tcp_pose[4]):.2f}°, {np.degrees(robot_tcp_pose[5]):.2f}°]")
            
            # Transform pose
            robot_pose = transformer.transform_pose_camera_to_robot(camera_pose, robot_tcp_pose)
            
            print(f"   ➡️  Robot base pose: [{robot_pose[0]:.4f}, {robot_pose[1]:.4f}, {robot_pose[2]:.4f}, {np.degrees(robot_pose[3]):.2f}°, {np.degrees(robot_pose[4]):.2f}°, {np.degrees(robot_pose[5]):.2f}°]")
            
            # Transform just the position
            camera_point = camera_pose[:3]
            robot_point = transformer.transform_point_camera_to_robot(camera_point, robot_tcp_pose)
            
            print(f"   Point transformation:")
            print(f"     Camera: [{camera_point[0]:.4f}, {camera_point[1]:.4f}, {camera_point[2]:.4f}] m")
            print(f"     Robot:  [{robot_point[0]:.4f}, {robot_point[1]:.4f}, {robot_point[2]:.4f}] m")
        
        print("\n✅ Coordinate transformer test completed")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
