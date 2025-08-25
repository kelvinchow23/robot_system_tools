#!/usr/bin/env python3
"""
Hand-Eye Calibration Calculator for UR Robot
Solves the AX=XB hand-eye calibration problem using OpenCV
"""

import numpy as np
import cv2
import json
import yaml
import argparse
from datetime import datetime
from pathlib import Path
from scipy.spatial.transform import Rotation as R

class HandEyeCalibrator:
    """Solve hand-eye calibration problem"""
    
    def __init__(self):
        """Initialize hand-eye calibrator"""
        self.calibration_data = None
        self.result = None
    
    def load_data(self, data_file):
        """
        Load calibration data from JSON file
        
        Args:
            data_file: Path to calibration data file
        """
        print(f"📂 Loading calibration data from: {data_file}")
        
        with open(data_file, 'r') as f:
            self.calibration_data = json.load(f)
        
        num_points = len(self.calibration_data['robot_poses'])
        print(f"✅ Loaded {num_points} calibration data points")
        
        if num_points < 3:
            raise ValueError("At least 3 calibration points required")
        
        print(f"   Collection date: {self.calibration_data['collection_date']}")
        print(f"   Robot IP: {self.calibration_data['robot_ip']}")
        print(f"   AprilTag: {self.calibration_data['apriltag_config']['tag_family']}")
    
    def prepare_calibration_matrices(self):
        """
        Prepare calibration matrices for OpenCV hand-eye calibration
        
        Returns:
            tuple: (robot_to_base_R, robot_to_base_t, camera_to_tag_R, camera_to_tag_t)
        """
        robot_poses = self.calibration_data['robot_poses']
        camera_poses = self.calibration_data['camera_poses']
        
        robot_to_base_R = []
        robot_to_base_t = []
        camera_to_tag_R = []
        camera_to_tag_t = []
        
        print("🔄 Preparing calibration matrices...")
        
        for i, (robot_pose, camera_pose) in enumerate(zip(robot_poses, camera_poses)):
            # Robot pose: [x, y, z, rx, ry, rz]
            robot_pos = np.array(robot_pose[:3])
            robot_rot_vec = np.array(robot_pose[3:])
            
            # Convert robot rotation vector to rotation matrix
            robot_rot_mat = R.from_rotvec(robot_rot_vec).as_matrix()
            
            # Camera pose: translation and rotation vector
            camera_pos = np.array(camera_pose['translation'])
            camera_rot_vec = np.array(camera_pose['rotation_vector'])
            
            # Convert camera rotation vector to rotation matrix
            camera_rot_mat = R.from_rotvec(camera_rot_vec).as_matrix()
            
            # Store for hand-eye calibration
            robot_to_base_R.append(robot_rot_mat)
            robot_to_base_t.append(robot_pos.reshape(3, 1))
            camera_to_tag_R.append(camera_rot_mat)
            camera_to_tag_t.append(camera_pos.reshape(3, 1))
            
            print(f"   Point {i+1}: Robot pos {robot_pos}, Camera dist {np.linalg.norm(camera_pos):.3f}m")
        
        return robot_to_base_R, robot_to_base_t, camera_to_tag_R, camera_to_tag_t
    
    def solve_handeye_calibration(self, method=cv2.CALIB_HAND_EYE_TSAI):
        """
        Solve hand-eye calibration using OpenCV
        
        Args:
            method: OpenCV hand-eye calibration method
            
        Returns:
            dict: Calibration result
        """
        print("🧮 Solving hand-eye calibration...")
        
        # Prepare calibration data
        robot_R, robot_t, camera_R, camera_t = self.prepare_calibration_matrices()
        
        # Available methods
        methods = {
            cv2.CALIB_HAND_EYE_TSAI: "Tsai",
            cv2.CALIB_HAND_EYE_PARK: "Park", 
            cv2.CALIB_HAND_EYE_HORAUD: "Horaud",
            cv2.CALIB_HAND_EYE_ANDREFF: "Andreff",
            cv2.CALIB_HAND_EYE_DANIILIDIS: "Daniilidis"
        }
        
        print(f"   Method: {methods.get(method, 'Unknown')}")
        print(f"   Data points: {len(robot_R)}")
        
        # Solve hand-eye calibration
        # For eye-in-hand: A = robot_to_base, B = camera_to_tag
        # Solves: AX = XB for X (camera-to-robot transform)
        try:
            R_cam_to_robot, t_cam_to_robot = cv2.calibrateHandEye(
                robot_R, robot_t,  # A matrices
                camera_R, camera_t,  # B matrices
                method=method
            )
            
            print("✅ Hand-eye calibration successful!")
            
            # Create result dictionary
            self.result = {
                'success': True,
                'method': methods.get(method, 'Unknown'),
                'camera_to_robot_R': R_cam_to_robot.tolist(),
                'camera_to_robot_t': t_cam_to_robot.flatten().tolist(),
                'calibration_date': datetime.now().isoformat(),
                'num_data_points': len(robot_R),
                'source_data_file': getattr(self, '_source_file', 'unknown')
            }
            
            # Convert to pose format for easier use
            camera_to_robot_rot_vec = R.from_matrix(R_cam_to_robot).as_rotvec()
            camera_to_robot_pose = np.concatenate([t_cam_to_robot.flatten(), camera_to_robot_rot_vec])
            self.result['camera_to_robot_pose'] = camera_to_robot_pose.tolist()
            
            # Calculate transformation matrix
            T_cam_to_robot = np.eye(4)
            T_cam_to_robot[:3, :3] = R_cam_to_robot
            T_cam_to_robot[:3, 3] = t_cam_to_robot.flatten()
            self.result['camera_to_robot_matrix'] = T_cam_to_robot.tolist()
            
            # Print summary
            print(f"📊 Calibration Result:")
            print(f"   Translation: [{t_cam_to_robot[0,0]:.4f}, {t_cam_to_robot[1,0]:.4f}, {t_cam_to_robot[2,0]:.4f}] m")
            print(f"   Rotation (deg): [{np.degrees(camera_to_robot_rot_vec[0]):.2f}, {np.degrees(camera_to_robot_rot_vec[1]):.2f}, {np.degrees(camera_to_robot_rot_vec[2]):.2f}]")
            
            return self.result
            
        except Exception as e:
            print(f"❌ Hand-eye calibration failed: {e}")
            self.result = {
                'success': False,
                'error': str(e),
                'method': methods.get(method, 'Unknown'),
                'calibration_date': datetime.now().isoformat()
            }
            return self.result
    
    def validate_calibration(self):
        """
        Validate calibration by checking reprojection errors
        
        Returns:
            dict: Validation results
        """
        if not self.result or not self.result['success']:
            print("❌ No successful calibration to validate")
            return None
        
        print("🔍 Validating hand-eye calibration...")
        
        R_cam_to_robot = np.array(self.result['camera_to_robot_R'])
        t_cam_to_robot = np.array(self.result['camera_to_robot_t']).reshape(3, 1)
        
        robot_poses = self.calibration_data['robot_poses']
        camera_poses = self.calibration_data['camera_poses']
        
        errors = []
        
        for i, (robot_pose, camera_pose) in enumerate(zip(robot_poses, camera_poses)):
            # Robot pose
            robot_pos = np.array(robot_pose[:3])
            robot_rot_vec = np.array(robot_pose[3:])
            robot_rot_mat = R.from_rotvec(robot_rot_vec).as_matrix()
            
            # Camera observation of tag
            camera_pos = np.array(camera_pose['translation']).reshape(3, 1)
            camera_rot_vec = np.array(camera_pose['rotation_vector'])
            camera_rot_mat = R.from_rotvec(camera_rot_vec).as_matrix()
            
            # Transform tag pose from camera to robot frame
            # T_robot_to_tag = T_robot_to_base * T_base_to_robot * T_robot_to_camera * T_camera_to_tag
            T_robot_to_base = np.eye(4)
            T_robot_to_base[:3, :3] = robot_rot_mat
            T_robot_to_base[:3, 3] = robot_pos
            
            T_camera_to_robot = np.eye(4)
            T_camera_to_robot[:3, :3] = R_cam_to_robot
            T_camera_to_robot[:3, 3] = t_cam_to_robot.flatten()
            
            T_camera_to_tag = np.eye(4)
            T_camera_to_tag[:3, :3] = camera_rot_mat
            T_camera_to_tag[:3, 3] = camera_pos.flatten()
            
            # Predicted tag pose in robot base frame
            T_base_to_tag = T_robot_to_base @ T_camera_to_robot @ T_camera_to_tag
            
            predicted_tag_pos = T_base_to_tag[:3, 3]
            
            # For validation, we check consistency across observations
            # (In practice, you'd compare against known tag position)
            if i == 0:
                reference_tag_pos = predicted_tag_pos
                error = 0.0
            else:
                error = np.linalg.norm(predicted_tag_pos - reference_tag_pos)
            
            errors.append(error)
            
            if i < 5:  # Print first few for debugging
                print(f"   Point {i+1}: Tag position error = {error:.4f} m")
        
        mean_error = np.mean(errors)
        max_error = np.max(errors)
        std_error = np.std(errors)
        
        validation_result = {
            'mean_error': mean_error,
            'max_error': max_error,
            'std_error': std_error,
            'errors': errors,
            'num_points': len(errors)
        }
        
        print(f"📊 Validation Results:")
        print(f"   Mean position error: {mean_error:.4f} m")
        print(f"   Max position error: {max_error:.4f} m")
        print(f"   Std deviation: {std_error:.4f} m")
        
        if mean_error < 0.005:  # 5mm
            print("✅ Excellent calibration quality")
        elif mean_error < 0.01:  # 10mm
            print("✅ Good calibration quality")
        elif mean_error < 0.02:  # 20mm
            print("⚠️  Fair calibration quality")
        else:
            print("❌ Poor calibration quality - consider recalibrating")
        
        return validation_result
    
    def save_calibration(self, output_file="handeye_calibration.yaml"):
        """
        Save calibration result to YAML file
        
        Args:
            output_file: Output file path
        """
        if not self.result:
            print("❌ No calibration result to save")
            return None
        
        output_path = Path(output_file)
        
        # Add timestamp to filename if default
        if output_path.name == "handeye_calibration.yaml":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_path.parent / f"handeye_calibration_{timestamp}.yaml"
        
        print(f"💾 Saving hand-eye calibration to: {output_path}")
        
        with open(output_path, 'w') as f:
            yaml.dump(self.result, f, default_flow_style=False, indent=2)
        
        print(f"✅ Hand-eye calibration saved")
        return output_path

def main():
    parser = argparse.ArgumentParser(description='Hand-Eye Calibration Calculator')
    parser.add_argument('--input', required=True,
                       help='Input calibration data file (JSON)')
    parser.add_argument('--output', default='handeye_calibration.yaml',
                       help='Output calibration file (YAML)')
    parser.add_argument('--method', default='tsai',
                       choices=['tsai', 'park', 'horaud', 'andreff', 'daniilidis'],
                       help='Calibration method')
    parser.add_argument('--validate', action='store_true',
                       help='Perform calibration validation')
    
    args = parser.parse_args()
    
    print("🧮 UR Robot Hand-Eye Calibration Calculator")
    print("=" * 60)
    
    # Method mapping
    method_map = {
        'tsai': cv2.CALIB_HAND_EYE_TSAI,
        'park': cv2.CALIB_HAND_EYE_PARK,
        'horaud': cv2.CALIB_HAND_EYE_HORAUD,
        'andreff': cv2.CALIB_HAND_EYE_ANDREFF,
        'daniilidis': cv2.CALIB_HAND_EYE_DANIILIDIS
    }
    
    try:
        calibrator = HandEyeCalibrator()
        calibrator._source_file = args.input
        
        # Load calibration data
        calibrator.load_data(args.input)
        
        # Solve hand-eye calibration
        result = calibrator.solve_handeye_calibration(method_map[args.method])
        
        if result['success']:
            # Validate calibration if requested
            if args.validate:
                calibrator.validate_calibration()
            
            # Save calibration
            output_path = calibrator.save_calibration(args.output)
            
            print(f"\n🎉 Hand-eye calibration completed!")
            print(f"   Calibration file: {output_path}")
            print(f"   Next step: Use this calibration for coordinate transformation")
        else:
            print("❌ Hand-eye calibration failed")
    
    except KeyboardInterrupt:
        print("\n🛑 Calibration interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
