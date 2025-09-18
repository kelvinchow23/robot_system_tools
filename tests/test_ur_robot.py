#!/usr/bin/env python3
"""
Simple UR Robot Test Script
Tests connection and allows basic joint movement
"""

import numpy as np
import argparse
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'robots', 'ur'))
from robots.ur.ur_controller import URController

def test_ur_robot(robot_ip):
    """
    Test UR robot connection and basic movement
    
    Args:
        robot_ip: IP address of UR robot
    """
    print("🤖 UR Robot Connection Test")
    print("=" * 40)
    
    try:
        # Initialize robot interface
        robot = URController(robot_ip)
        
        # Test connection by getting current state
        print("\n🔍 Testing robot connection...")
        current_joints = robot.get_joint_positions()
        current_pose = robot.get_tcp_pose()
        
        print("✅ Robot connection successful!")
        print(f"\n📊 Current Robot State:")
        print(f"   TCP Pose: {robot.format_pose(current_pose)}")
        print(f"   Joint Angles (degrees): {np.degrees(current_joints).round(1)}")
        
        # Ask for user confirmation before moving
        print(f"\n🔄 Joint Movement Test")
        print(f"   Current joint 6 (wrist): {np.degrees(current_joints[5]):.1f}°")
        print(f"   Will rotate joint 6 by +10° (to {np.degrees(current_joints[5]) + 10:.1f}°)")
        
        user_input = input("\nPress ENTER to perform joint movement test (or 'q' to quit): ").strip().lower()
        
        if user_input == 'q':
            print("🛑 Test cancelled by user")
            return
        
        # Calculate new joint positions (rotate last joint by 10 degrees)
        new_joints = current_joints.copy()
        new_joints[5] += np.radians(10)  # Joint 6 (index 5) + 10 degrees
        
        print(f"\n🚀 Moving joint 6 by +10°...")
        print(f"   From: {np.degrees(current_joints[5]):.1f}° to {np.degrees(new_joints[5]):.1f}°")
        
        # Perform movement
        success = robot.move_to_joints(new_joints, speed=0.5, acceleration=0.5)
        
        if success:
            print("✅ Joint movement completed!")
            
            # Get new position
            final_joints = robot.get_joint_positions()
            print(f"   Final joint 6 position: {np.degrees(final_joints[5]):.1f}°")
            
            # Ask if user wants to return to original position
            user_input = input("\nPress ENTER to return to original position (or 'q' to quit): ").strip().lower()
            
            if user_input != 'q':
                print("🏠 Returning to original position...")
                robot.move_to_joints(current_joints, speed=0.5, acceleration=0.5)
                print("✅ Returned to original position")
        else:
            print("❌ Joint movement failed")
        
        print("\n🎉 UR Robot test completed!")
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("   Check robot IP address and network connection")
        print("   Ensure robot is powered on and in remote control mode")
    finally:
        # Clean up connection
        if 'robot' in locals():
            robot.close()

def main():
    parser = argparse.ArgumentParser(description='UR Robot Connection and Movement Test')
    parser.add_argument('--robot-ip', required=True,
                       help='UR robot IP address (e.g., 192.168.1.100)')
    
    args = parser.parse_args()
    
    # Safety warning
    print("⚠️  SAFETY WARNING:")
    print("   - Ensure robot workspace is clear")
    print("   - Be ready to use emergency stop")
    print("   - Movement will be slow for safety")
    print("   - Only the wrist joint (joint 6) will move 10°")
    
    confirmation = input("\nDo you want to proceed? (y/N): ").strip().lower()
    
    if confirmation != 'y':
        print("🛑 Test cancelled for safety")
        return
    
    test_ur_robot(args.robot_ip)

if __name__ == "__main__":
    main()
