#!/usr/bin/env python3
"""
Test script to verify TCP pose sign corrections
Compare RTDE readings with and without sign flips
"""

import numpy as np
import rtde_receive
import argparse
from ur_robot_interface import URRobotInterface

def test_pose_signs(robot_ip):
    """Test pose readings with and without sign corrections"""
    
    print("🔍 TCP Pose Sign Verification Test")
    print("=" * 50)
    print("This will show you the pose readings with and without sign corrections.")
    print("Compare these values with what you see on the teach pendant.")
    print()
    
    try:
        # Direct RTDE connection (no sign corrections)
        rtde_r = rtde_receive.RTDEReceiveInterface(robot_ip)
        print("✅ Connected to robot via RTDE")
        
        # Get raw pose from RTDE
        raw_pose = np.array(rtde_r.getActualTCPPose())
        
        # Create pose with sign corrections (like in ur_robot_interface.py)
        corrected_pose = raw_pose.copy()
        corrected_pose[4] = -corrected_pose[4]  # Flip Ry sign
        corrected_pose[5] = -corrected_pose[5]  # Flip Rz sign
        
        print("📍 Current TCP Pose Readings:")
        print()
        print("Raw RTDE (no corrections):")
        print(f"  Position: X={raw_pose[0]*1000:.1f}mm, Y={raw_pose[1]*1000:.1f}mm, Z={raw_pose[2]*1000:.1f}mm")
        print(f"  Rotation: Rx={raw_pose[3]:.3f}rad, Ry={raw_pose[4]:.3f}rad, Rz={raw_pose[5]:.3f}rad")
        print(f"  Rotation: Rx={np.degrees(raw_pose[3]):.1f}°, Ry={np.degrees(raw_pose[4]):.1f}°, Rz={np.degrees(raw_pose[5]):.1f}°")
        print()
        
        print("With Sign Corrections (current ur_robot_interface.py):")
        print(f"  Position: X={corrected_pose[0]*1000:.1f}mm, Y={corrected_pose[1]*1000:.1f}mm, Z={corrected_pose[2]*1000:.1f}mm")
        print(f"  Rotation: Rx={corrected_pose[3]:.3f}rad, Ry={corrected_pose[4]:.3f}rad, Rz={corrected_pose[5]:.3f}rad")
        print(f"  Rotation: Rx={np.degrees(corrected_pose[3]):.1f}°, Ry={np.degrees(corrected_pose[4]):.1f}°, Rz={np.degrees(corrected_pose[5]):.1f}°")
        print()
        
        print("🎯 INSTRUCTIONS:")
        print("1. Look at your robot's teach pendant")
        print("2. Find the TCP position display (usually under 'Move' tab)")
        print("3. Compare the teach pendant values with the readings above")
        print("4. The readings that match the teach pendant are the CORRECT ones")
        print()
        print("If the 'Raw RTDE' matches your teach pendant:")
        print("  → Remove the sign corrections (lines 58-59 in ur_robot_interface.py)")
        print()
        print("If the 'With Sign Corrections' matches your teach pendant:")
        print("  → Keep the current sign corrections")
        print()
        print("If neither matches exactly:")
        print("  → You may need different sign corrections")
        
        rtde_r.disconnect()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure:")
        print("- Robot is powered on and in Remote Control mode")
        print("- IP address is correct")
        print("- Network connection is working")

def main():
    parser = argparse.ArgumentParser(description='Test TCP pose sign corrections')
    parser.add_argument('--robot-ip', 
                       help='UR robot IP address (overrides config file)')
    parser.add_argument('--config', default='robot_config.yaml',
                       help='Robot configuration file')
    
    args = parser.parse_args()
    
    # Load robot IP from config if not provided
    if args.robot_ip:
        robot_ip = args.robot_ip
        print(f"🤖 Using command-line IP: {robot_ip}")
    else:
        # Load IP from config file
        try:
            from ur_robot_interface import URRobotInterface
            config = URRobotInterface.load_robot_config(args.config)
            robot_ip = config['robot']['ip_address']
            print(f"🤖 Using IP from config file: {robot_ip}")
        except Exception as e:
            robot_ip = '192.168.0.10'
            print(f"⚠️  Could not load config, using default IP: {robot_ip}")
    
    test_pose_signs(robot_ip)

if __name__ == "__main__":
    main()
