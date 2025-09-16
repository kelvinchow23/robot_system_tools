#!/usr/bin/env python3
"""
Debug script to compare RTDE poses with teach pendant values
"""

import numpy as np
from scipy.spatial.transform import Rotation as R
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'robots', 'ur'))
from ur_robot_interface import URRobotInterface

def convert_rotation_vector_to_euler(rvec):
    """
    Convert rotation vector (from RTDE) to Euler angles (like teach pendant)
    
    Args:
        rvec: Rotation vector [rx, ry, rz] in radians
        
    Returns:
        tuple: (xyz_euler, zyx_euler) in degrees
    """
    # Create rotation object from rotation vector
    r = R.from_rotvec(rvec)
    
    # Convert to different Euler angle conventions
    xyz_euler = r.as_euler('xyz', degrees=True)  # Intrinsic XYZ
    zyx_euler = r.as_euler('zyx', degrees=True)  # Intrinsic ZYX (common for robots)
    
    return xyz_euler, zyx_euler

def analyze_pose():
    """Compare RTDE pose with teach pendant equivalent"""
    
    print("🤖 UR Robot Pose Analysis")
    print("=" * 50)
    
    try:
        # Connect to robot (read-only)
        robot = URRobotInterface(read_only=True)
        
        # Get current pose
        pose = robot.get_tcp_pose()
        
        print(f"\n📍 RTDE Raw Pose:")
        print(f"   Position (m): [{pose[0]:.4f}, {pose[1]:.4f}, {pose[2]:.4f}]")
        print(f"   Rotation Vec: [{pose[3]:.4f}, {pose[4]:.4f}, {pose[5]:.4f}] rad")
        
        # Convert rotation vector to Euler angles
        xyz_euler, zyx_euler = convert_rotation_vector_to_euler(pose[3:6])
        
        print(f"\n🔄 Converted to Euler Angles:")
        print(f"   XYZ Euler (°): [{xyz_euler[0]:.2f}, {xyz_euler[1]:.2f}, {xyz_euler[2]:.2f}]")
        print(f"   XYZ Euler (rad): [{np.radians(xyz_euler[0]):.4f}, {np.radians(xyz_euler[1]):.4f}, {np.radians(xyz_euler[2]):.4f}]")
        print(f"   ZYX Euler (°): [{zyx_euler[0]:.2f}, {zyx_euler[1]:.2f}, {zyx_euler[2]:.2f}]")
        print(f"   ZYX Euler (rad): [{np.radians(zyx_euler[0]):.4f}, {np.radians(zyx_euler[1]):.4f}, {np.radians(zyx_euler[2]):.4f}]")
        
        print(f"\n📱 Check Your Teach Pendant:")
        print(f"   Position should match: [{pose[0]*1000:.1f}, {pose[1]*1000:.1f}, {pose[2]*1000:.1f}] mm")
        print(f"   Orientation might match one of the Euler angle sets above")
        
        # Calculate rotation vector magnitude and axis
        rvec_magnitude = np.linalg.norm(pose[3:6])
        if rvec_magnitude > 0:
            rvec_axis = pose[3:6] / rvec_magnitude
            print(f"\n🔧 Rotation Vector Details:")
            print(f"   Magnitude: {rvec_magnitude:.4f} rad ({np.degrees(rvec_magnitude):.2f}°)")
            print(f"   Axis: [{rvec_axis[0]:.3f}, {rvec_axis[1]:.3f}, {rvec_axis[2]:.3f}]")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 To debug manually, try this:")
        print("   1. Note down teach pendant pose (position + RX,RY,RZ)")
        print("   2. Run this script to see RTDE values")
        print("   3. Compare the converted Euler angles")

if __name__ == "__main__":
    analyze_pose()
