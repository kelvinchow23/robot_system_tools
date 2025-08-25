#!/usr/bin/env python3
"""
Mock UR Robot Interface for Development and Testing
Simulates ur_rtde functionality when actual robot is not available
"""

import numpy as np
import time
from scipy.spatial.transform import Rotation as R

# Mock RTDE availability
RTDE_AVAILABLE = False
print("⚠️  Using Mock UR Robot Interface (ur_rtde not available)")
print("   This interface simulates robot behavior for development")

class MockRTDEControlInterface:
    """Mock RTDE Control Interface"""
    
    def __init__(self, robot_ip):
        self.robot_ip = robot_ip
        print(f"🔧 Mock RTDE Control connected to {robot_ip}")
        self.current_pose = np.array([0.3, 0.0, 0.5, 0.0, 3.14159, 0.0])
        self.current_joints = np.array([0.0, -1.57, 1.57, -1.57, -1.57, 0.0])
    
    def moveL(self, pose, speed, acceleration, asynchronous=False):
        """Mock linear movement"""
        print(f"🤖 Mock moveL to {pose} (speed: {speed}, accel: {acceleration})")
        # Simulate movement time
        if not asynchronous:
            time.sleep(0.1)  # Simulate movement delay
        # Update internal pose
        self.current_pose = np.array(pose)
        return True
    
    def moveJ(self, joints, speed, acceleration, asynchronous=False):
        """Mock joint movement"""
        print(f"🤖 Mock moveJ to {joints} (speed: {speed}, accel: {acceleration})")
        if not asynchronous:
            time.sleep(0.1)
        self.current_joints = np.array(joints)
        return True
    
    def stopL(self):
        """Mock stop motion"""
        print("🛑 Mock stopL called")
        return True
    
    def disconnect(self):
        """Mock disconnect"""
        print("🔌 Mock RTDE Control disconnected")

class MockRTDEReceiveInterface:
    """Mock RTDE Receive Interface"""
    
    def __init__(self, robot_ip):
        self.robot_ip = robot_ip
        print(f"📡 Mock RTDE Receive connected to {robot_ip}")
        # Simulate realistic robot pose
        self.current_pose = np.array([0.3, 0.0, 0.5, 0.0, 3.14159, 0.0])
        self.current_joints = np.array([0.0, -1.57, 1.57, -1.57, -1.57, 0.0])
        # Add some noise to simulate real robot
        self.pose_noise = 0.0001  # 0.1mm noise
        self.joint_noise = 0.001   # Small joint noise
    
    def getActualTCPPose(self):
        """Mock get TCP pose with small noise"""
        noise = np.random.normal(0, self.pose_noise, 6)
        noise[3:] *= 0.1  # Less noise on rotation
        return self.current_pose + noise
    
    def getActualQ(self):
        """Mock get joint positions with small noise"""
        noise = np.random.normal(0, self.joint_noise, 6)
        return self.current_joints + noise
    
    def disconnect(self):
        """Mock disconnect"""
        print("🔌 Mock RTDE Receive disconnected")

# Replace imports with mock classes
rtde_control = type('MockModule', (), {
    'RTDEControlInterface': MockRTDEControlInterface
})()

rtde_receive = type('MockModule', (), {
    'RTDEReceiveInterface': MockRTDEReceiveInterface
})()

class URRobotInterface:
    """Universal Robots interface using Mock RTDE for development"""
    
    def __init__(self, robot_ip, speed=0.03, acceleration=0.08):
        """
        Initialize UR robot interface (Mock version)
        
        Args:
            robot_ip: IP address of UR robot (simulated)
            speed: Default linear speed (m/s)
            acceleration: Default acceleration (m/s²)
        """
        self.robot_ip = robot_ip
        self.speed = speed
        self.acceleration = acceleration
        
        print(f"🤖 Connecting to UR robot at {robot_ip} (MOCK MODE)...")
        
        try:
            self.rtde_c = rtde_control.RTDEControlInterface(robot_ip)
            self.rtde_r = rtde_receive.RTDEReceiveInterface(robot_ip)
            print("✅ Connected to UR robot (MOCK)")
        except Exception as e:
            print(f"❌ Failed to connect to robot: {e}")
            raise
        
        # Get initial position for reference
        self.home_pose = self.get_tcp_pose()
        print(f"📍 Current TCP pose: {self.format_pose(self.home_pose)}")
    
    def get_tcp_pose(self):
        """
        Get current TCP pose in base frame
        
        Returns:
            np.array: [x, y, z, rx, ry, rz] in meters and radians
        """
        return np.array(self.rtde_r.getActualTCPPose())
    
    def get_joint_positions(self):
        """
        Get current joint positions
        
        Returns:
            np.array: Joint angles in radians
        """
        return np.array(self.rtde_r.getActualQ())
    
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
        Convert 4x4 transformation matrix to pose [x, y, z, rx, ry, rz]
        
        Args:
            transform_matrix: 4x4 transformation matrix
            
        Returns:
            np.array: [x, y, z, rx, ry, rz] pose
        """
        translation = transform_matrix[:3, 3]
        rotation_matrix = transform_matrix[:3, :3]
        rotation_vector = R.from_matrix(rotation_matrix).as_rotvec()
        
        return np.concatenate([translation, rotation_vector])
    
    def is_at_pose(self, target_pose, position_tolerance=0.001, rotation_tolerance=0.01):
        """
        Check if robot is at target pose within tolerance
        
        Args:
            target_pose: Target pose [x, y, z, rx, ry, rz]
            position_tolerance: Position tolerance in meters
            rotation_tolerance: Rotation tolerance in radians
            
        Returns:
            bool: True if at target pose
        """
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
            
            print("🔍 Connection test (MOCK):")
            print(f"   TCP Pose: {self.format_pose(pose)}")
            print(f"   Joints: {np.degrees(joints).round(1)} degrees")
            print("   ⚠️  Note: This is simulated data for development")
            
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
            print("🔌 Disconnected from robot (MOCK)")
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
    
    parser = argparse.ArgumentParser(description='UR Robot Interface Test (Mock)')
    parser.add_argument('--robot-ip', default='192.168.1.100',
                       help='Robot IP address (simulated)')
    parser.add_argument('--test-move', action='store_true',
                       help='Perform small test movement (simulated)')
    
    args = parser.parse_args()
    
    print("🤖 UR Robot Interface Test (MOCK MODE)")
    print("=" * 50)
    
    try:
        with URRobotInterface(args.robot_ip) as robot:
            if not robot.test_connection():
                return
            
            if args.test_move:
                print("\n🔄 Performing test movement (simulated)...")
                
                # Small relative movement
                current_pose = robot.get_tcp_pose()
                test_pose = current_pose.copy()
                test_pose[2] += 0.01  # Move up 1cm
                
                print(f"Moving to: {robot.format_pose(test_pose)}")
                if robot.move_to_pose(test_pose):
                    time.sleep(1)
                    
                    print("Returning to original position...")
                    robot.move_to_pose(current_pose)
                    print("✅ Test movement completed (simulated)")
                else:
                    print("❌ Test movement failed")
            
            print("\n🎉 UR Robot interface test completed (MOCK)!")
            print("💡 Install ur_rtde for real robot communication")
    
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    main()
