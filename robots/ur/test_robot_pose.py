#!/usr/bin/env python3
"""
Simple utility to get robot TCP pose or joint angles using URRobotInterface
"""

import argparse
from ur_robot_interface import URRobotInterface

def main():
    parser = argparse.ArgumentParser(description='Get UR robot pose or joint angles')
    parser.add_argument('--robot-ip', default='192.168.0.10',
                       help='UR robot IP address')
    parser.add_argument('--mode', choices=['tcp', 'joints', 'both'], default='tcp',
                       help='What to read: tcp pose, joint angles, or both')
    parser.add_argument('--continuous', action='store_true',
                       help='Continuously read and display values')
    
    args = parser.parse_args()
    
    print(f"🤖 Connecting to UR robot at {args.robot_ip}...")
    
    try:
        robot = URRobotInterface(args.robot_ip, read_only=True)
        
        if args.continuous:
            print("📍 Continuous reading mode (Press Ctrl+C to stop)")
            import time
            while True:
                if args.mode in ['tcp', 'both']:
                    tcp_pose = robot.get_tcp_pose()
                    print(f"TCP: {robot.format_pose(tcp_pose)}")
                
                if args.mode in ['joints', 'both']:
                    joint_angles = robot.get_joint_positions()
                    joint_degrees = [f"{angle*180/3.14159:.1f}°" for angle in joint_angles]
                    print(f"Joints: {joint_degrees}")
                
                if args.mode == 'both':
                    print("-" * 50)
                
                time.sleep(0.5)
        else:
            # Single reading
            if args.mode in ['tcp', 'both']:
                tcp_pose = robot.get_tcp_pose()
                print(f"📍 TCP Pose: {robot.format_pose(tcp_pose)}")
                print(f"   Position: X={tcp_pose[0]*1000:.1f}mm, Y={tcp_pose[1]*1000:.1f}mm, Z={tcp_pose[2]*1000:.1f}mm")
                print(f"   Rotation: Rx={tcp_pose[3]:.3f}rad, Ry={tcp_pose[4]:.3f}rad, Rz={tcp_pose[5]:.3f}rad")
            
            if args.mode in ['joints', 'both']:
                joint_angles = robot.get_joint_positions()
                print(f"🔗 Joint Angles (degrees):")
                for i, angle in enumerate(joint_angles):
                    print(f"   Joint {i+1}: {angle*180/3.14159:.1f}°")
        
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'robot' in locals():
            robot.close()
            print("✅ Disconnected from robot")

if __name__ == "__main__":
    main()
