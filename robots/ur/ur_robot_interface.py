#!/usr/bin/env python3
"""
Universal Robots Interface for Robot Vision Applications
Provides clean interface for UR robot control via RTDE
"""

import numpy as np
import time
import rtde_control
import rtde_receive
import yaml
import os
from pathlib import Path
from scipy.spatial.transform import Rotation as R

# Import centralized configuration
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from config_manager import config

class URRobotInterface:
    """Universal Robots interface using RTDE"""
    
    def __init__(self, robot_ip=None, speed=None, acceleration=None, read_only=False):
        """
        Initialize UR robot interface
        
        Args:
            robot_ip: IP address of UR robot (overrides config if provided)
            speed: Default linear speed (m/s) (overrides config if provided)
            acceleration: Default acceleration (m/s²) (overrides config if provided)
            read_only: If True, only connect receive interface (no remote control needed)
        """
        self.robot_ip = robot_ip or config.get('robot.ip_address', '192.168.0.10')
        self.speed = speed or config.get('robot.default_speed', 0.05)
        self.acceleration = acceleration or config.get('robot.default_acceleration', 0.2)
        self.read_only = read_only
        
        print(f"🤖 Connecting to UR robot at {self.robot_ip}...")
        print(f"📋 Using config: speed={self.speed}m/s, accel={self.acceleration}m/s²")
        
        try:
            if not read_only:
                self.rtde_c = rtde_control.RTDEControlInterface(self.robot_ip)
            else:
                self.rtde_c = None
            self.rtde_r = rtde_receive.RTDEReceiveInterface(self.robot_ip)
            print("✅ Connected to UR robot")
        except Exception as e:
            print(f"❌ Failed to connect to robot: {e}")
            raise
        
        # Get initial position for reference
        self.home_pose = self.get_tcp_pose()
        print(f"📍 Current TCP pose: {self.format_pose(self.home_pose)}")
    
    def set_calibration_speed(self):
        """Set safe speeds for calibration movements to prevent protective stop"""
        self.speed = config.get('robot.calibration_speed', 0.02)
        self.acceleration = config.get('robot.calibration_acceleration', 0.1)
        print(f"🐌 Calibration speeds set: {self.speed*1000:.0f}mm/s, {self.acceleration*1000:.0f}mm/s²")
    
    def get_tcp_pose(self):
        """
        Get current TCP pose in base frame
        
        Returns:
            np.array: [x, y, z, rx, ry, rz] in meters and radians
        """
        pose = np.array(self.rtde_r.getActualTCPPose())
        return pose
    
    def get_joint_positions(self):
        """
        Get current joint positions
        
        Returns:
            np.array: Joint angles in radians
        """
        return np.array(self.rtde_r.getActualQ())
    
    def joints_to_pose(self, joint_positions):
        """
        Convert joint positions to TCP pose (forward kinematics)
        
        Args:
            joint_positions: Joint angles in radians [j0, j1, j2, j3, j4, j5]
            
        Returns:
            np.array: TCP pose [x, y, z, rx, ry, rz] in meters and radians
        """
        if self.rtde_c is None:
            print("❌ Forward kinematics requires control interface (read_only=False)")
            return None
            
        try:
            pose = np.array(self.rtde_c.getForwardKinematics(joint_positions.tolist()))
            return pose
        except Exception as e:
            print(f"❌ Forward kinematics failed: {e}")
            return None
    
    def pose_to_joints(self, pose, current_joints=None):
        """
        Convert TCP pose to joint positions (inverse kinematics)
        
        Args:
            pose: TCP pose [x, y, z, rx, ry, rz] in meters and radians
            current_joints: Current joint positions for closest solution (optional)
            
        Returns:
            np.array: Joint angles in radians, or None if no solution
        """
        if self.rtde_c is None:
            print("❌ Inverse kinematics requires control interface (read_only=False)")
            return None
            
        try:
            if current_joints is None:
                current_joints = self.get_joint_positions()
            
            joints = self.rtde_c.getInverseKinematics(pose.tolist(), current_joints.tolist())
            
            if joints is None:
                print("❌ No inverse kinematics solution found")
                return None
                
            return np.array(joints)
        except Exception as e:
            print(f"❌ Inverse kinematics failed: {e}")
            return None
    
    def move_to_pose(self, pose, speed=None, acceleration=None, wait=True):
        """
        Move robot to specified TCP pose
        
        Args:
            pose: Target pose [x, y, z, rx, ry, rz]
            speed: Linear speed (m/s), uses default if None
            acceleration: Acceleration (m/s²), uses default if None
            wait: Whether to wait for movement completion
        
        Returns:
            bool: True if move was successful
        """
        if speed is None:
            speed = self.speed
        if acceleration is None:
            acceleration = self.acceleration
        
        try:
            self.rtde_c.moveL(pose.tolist(), speed, acceleration, not wait)
            if wait:
                time.sleep(0.1)  # Small delay for stability
            return True
        except Exception as e:
            print(f"❌ Failed to move to pose: {e}")
            return False
    
    def move_to_joints(self, joint_positions, speed=None, acceleration=None, wait=True):
        """
        Move robot to specified joint positions
        
        Args:
            joint_positions: Target joint angles in radians
            speed: Joint speed (rad/s), uses default if None
            acceleration: Joint acceleration (rad/s²), uses default if None
            wait: Whether to wait for movement completion
        
        Returns:
            bool: True if move was successful
        """
        if speed is None:
            speed = self.speed * 2  # Joint moves typically faster
        if acceleration is None:
            acceleration = self.acceleration * 2
        
        try:
            self.rtde_c.moveJ(joint_positions.tolist(), speed, acceleration, not wait)
            if wait:
                time.sleep(0.1)  # Small delay for stability
            return True
        except Exception as e:
            print(f"❌ Failed to move to joints: {e}")
            return False
    
    def get_pose_matrix(self, pose=None):
        """
        Convert pose to 4x4 transformation matrix
        
        Args:
            pose: [x, y, z, rx, ry, rz] pose, uses current if None
            
        Returns:
            np.array: 4x4 transformation matrix
        """
        if pose is None:
            pose = self.get_tcp_pose()
        
        # Extract translation and rotation
        translation = pose[:3]
        rotation_vector = pose[3:]
        
        # Create transformation matrix
        rotation_matrix = R.from_rotvec(rotation_vector).as_matrix()
        
        transform = np.eye(4)
        transform[:3, :3] = rotation_matrix
        transform[:3, 3] = translation
        
        return transform
    
    def matrix_to_pose(self, transform_matrix):
        """
        Convert 4x4 transformation matrix to pose
        
        Args:
            transform_matrix: 4x4 transformation matrix
            
        Returns:
            np.array: [x, y, z, rx, ry, rz] pose
        """
        translation = transform_matrix[:3, 3]
        rotation_matrix = transform_matrix[:3, :3]
        rotation_vector = R.from_matrix(rotation_matrix).as_rotvec()
        
        return np.concatenate([translation, rotation_vector])
    
    def is_at_pose(self, target_pose, position_tolerance=None, rotation_tolerance=None):
        """
        Check if robot is at target pose within tolerance
        
        Args:
            target_pose: Target pose [x, y, z, rx, ry, rz]
            position_tolerance: Position tolerance in meters (uses config default if None)
            rotation_tolerance: Rotation tolerance in radians (uses config default if None)
            
        Returns:
            bool: True if at target pose
        """
        if position_tolerance is None:
            position_tolerance = config.get('robot.position_tolerance', 0.001)
        if rotation_tolerance is None:
            rotation_tolerance = config.get('robot.rotation_tolerance', 0.01)
            
        current_pose = self.get_tcp_pose()
        
        position_diff = np.linalg.norm(current_pose[:3] - target_pose[:3])
        rotation_diff = np.linalg.norm(current_pose[3:] - target_pose[3:])
        
        return (position_diff < position_tolerance and 
                rotation_diff < rotation_tolerance)
    
    def stop_motion(self):
        """Emergency stop robot motion"""
        try:
            self.rtde_c.stopL()
            print("🛑 Robot motion stopped")
            return True
        except Exception as e:
            print(f"❌ Failed to stop robot: {e}")
            return False
    
    def go_home(self):
        """Return robot to home pose"""
        print("🏠 Returning to home pose...")
        return self.move_to_pose(self.home_pose)
    
    def test_connection(self):
        """
        Test robot connection and basic functionality
        
        Returns:
            bool: True if connection is working
        """
        try:
            pose = self.get_tcp_pose()
            joints = self.get_joint_positions()
            
            print("🔍 Connection test:")
            print(f"   TCP Pose: {self.format_pose(pose)}")
            print(f"   Joints: {np.degrees(joints).round(1)} degrees")
            
            return True
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
    
    def format_pose(self, pose):
        """Format pose for nice printing"""
        return (f"[{pose[0]:.3f}, {pose[1]:.3f}, {pose[2]:.3f}, "
                f"{pose[3]:.3f}, {pose[4]:.3f}, {pose[5]:.3f}]")
    
    def close(self):
        """Close robot connection"""
        try:
            self.rtde_c.disconnect()
            self.rtde_r.disconnect()
            print("🔌 Disconnected from robot")
        except:
            pass

    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

def main():
    """Test the UR robot interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='UR Robot Interface Test')
    parser.add_argument('--robot-ip', default=None,
                       help='Robot IP address (overrides config)')
    parser.add_argument('--test-move', action='store_true',
                       help='Perform small test movement')
    
    args = parser.parse_args()
    
    print("🤖 UR Robot Interface Test")
    print("=" * 50)
    
    try:
        robot_ip = args.robot_ip or config.get('robot.ip_address', '192.168.0.10')
        
        with URRobotInterface(robot_ip) as robot:
            if not robot.test_connection():
                return
            
            if args.test_move:
                print("\n🔄 Performing test movement...")
                
                current_pose = robot.get_tcp_pose()
                test_pose = current_pose.copy()
                test_pose[2] += 0.01
                
                print(f"Moving to: {robot.format_pose(test_pose)}")
                if robot.move_to_pose(test_pose):
                    time.sleep(1)
                    
                    print("Returning to original position...")
                    robot.move_to_pose(current_pose)
                    print("✅ Test movement completed")
                else:
                    print("❌ Test movement failed")
            
            print("\n🎉 UR Robot interface test completed!")
    
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    main()
