#!/usr/bin/env python3
"""
Visual Servo Engine
Core visual servoing engine with iterative correction, median filtering, and safety limits
"""

import numpy as np
import time
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
import sys

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "setup"))

from .config import visual_servo_config
from .detection_filter import DetectionFilter
from .pose_history import PoseHistoryManager
from apriltag_detection import AprilTagDetector

class VisualServoEngine:
    """Core visual servoing engine for dynamic pose correction"""
    
    def __init__(self, robot_controller, positions_file: Path, apriltag_detector=None):
        """
        Initialize visual servo engine
        
        Args:
            robot_controller: Robot controller instance (URController)
            positions_file: Path to taught positions file
            apriltag_detector: AprilTag detector instance (optional, will create if None)
        """
        self.robot = robot_controller
        self.config = visual_servo_config
        
        # Initialize AprilTag detector if not provided
        if apriltag_detector is None:
            self.detector = AprilTagDetector()
        else:
            self.detector = apriltag_detector
        
        # Initialize components
        self.detection_filter = DetectionFilter(self.detector, self.config)
        self.pose_history = PoseHistoryManager(positions_file, self.config)
        
        print("🎯 Visual Servo Engine initialized")
        self.config.print_config()
    
    def visual_servo_to_position(self, position_name: str, update_stored_pose: bool = True) -> Tuple[bool, Dict[str, Any]]:
        """
        Perform visual servoing to a taught position with AprilTag reference
        
        Args:
            position_name: Name of the taught position
            update_stored_pose: Whether to update the stored position after correction
            
        Returns:
            (success, metrics) tuple
        """
        print(f"\n🎯 Starting visual servoing to position '{position_name}'")
        
        # Load position data
        position_data = self._get_position_data(position_name)
        if not position_data:
            return False, {'error': 'Position not found'}
        
        # Check if position has AprilTag reference
        if 'tag_reference' not in position_data or not position_data['tag_reference']:
            print(f"❌ Position '{position_name}' has no AprilTag reference for visual servoing")
            return False, {'error': 'No AprilTag reference'}
        
        # Check if position has direct AprilTag view or uses observation pose
        if position_data.get('has_apriltag_view', False) and position_data.get('camera_to_tag'):
            # Direct AprilTag view - standard visual servoing
            return self._visual_servo_direct(position_name, position_data, update_stored_pose)
        elif position_data.get('observation_pose'):
            # Uses observation pose - observation-based visual servoing
            return self._visual_servo_via_observation(position_name, position_data, update_stored_pose)
        else:
            print(f"❌ Position '{position_name}' has no AprilTag view (direct or via observation)")
            return False, {'error': 'No AprilTag view available'}
    
    def _visual_servo_direct(self, position_name: str, position_data: Dict[str, Any], update_stored_pose: bool) -> Tuple[bool, Dict[str, Any]]:
        """
        Perform visual servoing for positions with direct AprilTag view
        
        Args:
            position_name: Name of the taught position
            position_data: Position data from YAML
            update_stored_pose: Whether to update the stored position after correction
            
        Returns:
            (success, metrics) tuple
        """
        print(f"📸 Direct visual servoing for '{position_name}'")
        
        tag_reference = position_data['tag_reference']
        stored_tag_pose = np.array(position_data['camera_to_tag'])
        stored_robot_pose = np.array(position_data['coordinates'])
        
        # Extract tag ID from reference (handle both "tag_123" and "123" formats)
        if isinstance(tag_reference, str) and tag_reference.startswith('tag_'):
            tag_id = int(tag_reference.split('_')[1])
        else:
            tag_id = int(tag_reference)
        
        print(f"🏷️  Using AprilTag {tag_id} as reference")
        
        # Initialize metrics
        metrics = {
            'position_name': position_name,
            'tag_id': tag_id,
            'method': 'direct',
            'iterations': 0,
            'total_correction': np.zeros(6),
            'final_error': None,
            'converged': False,
            'corrections_applied': []
        }
        
        current_robot_pose = stored_robot_pose.copy()
        total_correction = np.zeros(6)
        
        # Iterative correction loop
        for iteration in range(self.config.max_iterations):
            print(f"\n🔄 Iteration {iteration + 1}/{self.config.max_iterations}")
            metrics['iterations'] = iteration + 1
            
            # Move to current estimated pose
            print(f"🤖 Moving to estimated pose...")
            success = self.robot.move_to_pose(current_robot_pose)
            if not success:
                print(f"❌ Failed to move robot to pose")
                return False, metrics
            
            # Detect current AprilTag pose
            current_tag_pose = self.detection_filter.get_filtered_tag_pose(tag_id)
            if current_tag_pose is None:
                print(f"❌ Failed to detect AprilTag {tag_id}")
                return False, metrics
            
            # Calculate pose error
            tag_error = current_tag_pose - stored_tag_pose
            pose_error_magnitude = np.linalg.norm(tag_error)
            
            print(f"📏 Tag pose error magnitude: {pose_error_magnitude:.4f}")
            print(f"   Translation error: [{tag_error[0]:.4f}, {tag_error[1]:.4f}, {tag_error[2]:.4f}]m")
            print(f"   Rotation error: [{tag_error[3]:.4f}, {tag_error[4]:.4f}, {tag_error[5]:.4f}]rad")
            
            # Check convergence
            if (np.linalg.norm(tag_error[:3]) < self.config.position_tolerance and 
                np.linalg.norm(tag_error[3:]) < self.config.rotation_tolerance):
                print(f"✅ Converged within tolerance")
                metrics['converged'] = True
                metrics['final_error'] = pose_error_magnitude
                break
            
            # Calculate robot pose correction
            # For simplicity, apply tag error directly to robot pose
            # In a more sophisticated system, this would involve proper coordinate transformations
            robot_correction = -tag_error  # Negative because we want to counteract the error
            
            # Apply safety limits
            correction_valid, safety_metrics = self._validate_correction(
                robot_correction, total_correction)
            
            if not correction_valid:
                print(f"❌ Correction exceeds safety limits")
                metrics.update(safety_metrics)
                return False, metrics
            
            # Apply correction
            current_robot_pose += robot_correction
            total_correction += robot_correction
            
            correction_magnitude = np.linalg.norm(robot_correction)
            print(f"🔧 Applied correction magnitude: {correction_magnitude:.4f}")
            
            metrics['corrections_applied'].append({
                'iteration': iteration + 1,
                'tag_error': tag_error.tolist(),
                'robot_correction': robot_correction.tolist(),
                'correction_magnitude': correction_magnitude
            })
        
        # Final metrics
        metrics['total_correction'] = total_correction
        metrics['final_robot_pose'] = current_robot_pose.tolist()
        
        if not metrics['converged']:
            print(f"⚠️  Did not converge within {self.config.max_iterations} iterations")
            metrics['final_error'] = pose_error_magnitude
        
        # Record in history
        self.pose_history.record_correction(
            position_name, stored_robot_pose, current_robot_pose,
            stored_tag_pose, current_tag_pose, metrics)
        
        # Update stored pose if requested and converged
        if update_stored_pose and metrics['converged']:
            success = self.pose_history.update_position_pose(
                position_name, current_robot_pose, current_tag_pose)
            metrics['pose_updated'] = success
            
            if success:
                print(f"💾 Updated stored pose for '{position_name}'")
        
        print(f"\n🎯 Direct visual servoing completed for '{position_name}'")
        print(f"   Converged: {metrics['converged']}")
        print(f"   Iterations: {metrics['iterations']}")
        print(f"   Total correction: {np.linalg.norm(total_correction):.4f}")
        
        return metrics['converged'], metrics
    
    def _visual_servo_via_observation(self, position_name: str, position_data: Dict[str, Any], update_stored_pose: bool) -> Tuple[bool, Dict[str, Any]]:
        """
        Perform visual servoing for positions using observation pose with fixed offset
        
        Args:
            position_name: Name of the taught position
            position_data: Position data from YAML
            update_stored_pose: Whether to update the stored position after correction
            
        Returns:
            (success, metrics) tuple
        """
        print(f"👁️  Observation-based visual servoing for '{position_name}'")
        
        observation_pose_name = position_data['observation_pose']
        observation_offset = np.array(position_data.get('observation_offset', [0, 0, 0, 0, 0, 0]))
        
        print(f"🔭 Using observation pose: '{observation_pose_name}'")
        print(f"📐 Observation offset: {observation_offset}")
        
        # Get observation pose data
        observation_data = self._get_position_data(observation_pose_name)
        if not observation_data:
            return False, {'error': f'Observation pose {observation_pose_name} not found'}
        
        if not observation_data.get('has_apriltag_view', False) or not observation_data.get('camera_to_tag'):
            return False, {'error': f'Observation pose {observation_pose_name} has no AprilTag view'}
        
        tag_reference = observation_data['tag_reference']
        stored_obs_tag_pose = np.array(observation_data['camera_to_tag'])
        stored_obs_robot_pose = np.array(observation_data['coordinates'])
        stored_target_pose = np.array(position_data['coordinates'])
        
        # Extract tag ID from reference
        if isinstance(tag_reference, str) and tag_reference.startswith('tag_'):
            tag_id = int(tag_reference.split('_')[1])
        else:
            tag_id = int(tag_reference)
        
        print(f"🏷️  Using AprilTag {tag_id} via observation pose")
        
        # Initialize metrics
        metrics = {
            'position_name': position_name,
            'observation_pose': observation_pose_name,
            'observation_offset': observation_offset.tolist(),
            'tag_id': tag_id,
            'method': 'observation',
            'iterations': 0,
            'total_correction': np.zeros(6),
            'final_error': None,
            'converged': False,
            'corrections_applied': []
        }
        
        # Calculate initial corrected target pose
        current_target_pose = stored_target_pose.copy()
        total_correction = np.zeros(6)
        
        # Iterative correction loop
        for iteration in range(self.config.max_iterations):
            print(f"\n🔄 Iteration {iteration + 1}/{self.config.max_iterations}")
            metrics['iterations'] = iteration + 1
            
            # Step 1: Move to observation pose + corrections
            current_obs_pose = stored_obs_robot_pose + total_correction
            print(f"🔭 Moving to corrected observation pose...")
            success = self.robot.move_to_pose(current_obs_pose)
            if not success:
                print(f"❌ Failed to move robot to observation pose")
                return False, metrics
            
            # Step 2: Detect current AprilTag pose from observation position
            current_obs_tag_pose = self.detection_filter.get_filtered_tag_pose(tag_id)
            if current_obs_tag_pose is None:
                print(f"❌ Failed to detect AprilTag {tag_id} from observation pose")
                return False, metrics
            
            # Step 3: Calculate tag error from observation position
            tag_error = current_obs_tag_pose - stored_obs_tag_pose
            pose_error_magnitude = np.linalg.norm(tag_error)
            
            print(f"📏 Tag pose error magnitude: {pose_error_magnitude:.4f}")
            print(f"   Translation error: [{tag_error[0]:.4f}, {tag_error[1]:.4f}, {tag_error[2]:.4f}]m")
            print(f"   Rotation error: [{tag_error[3]:.4f}, {tag_error[4]:.4f}, {tag_error[5]:.4f}]rad")
            
            # Check convergence
            if (np.linalg.norm(tag_error[:3]) < self.config.position_tolerance and 
                np.linalg.norm(tag_error[3:]) < self.config.rotation_tolerance):
                print(f"✅ Converged within tolerance")
                metrics['converged'] = True
                metrics['final_error'] = pose_error_magnitude
                break
            
            # Step 4: Calculate robot pose correction (same for observation and target poses)
            robot_correction = -tag_error  # Negative because we want to counteract the error
            
            # Apply safety limits
            correction_valid, safety_metrics = self._validate_correction(
                robot_correction, total_correction)
            
            if not correction_valid:
                print(f"❌ Correction exceeds safety limits")
                metrics.update(safety_metrics)
                return False, metrics
            
            # Step 5: Apply correction to target pose (same spatial correction as observation pose)
            current_target_pose += robot_correction
            total_correction += robot_correction
            
            correction_magnitude = np.linalg.norm(robot_correction)
            print(f"🔧 Applied correction magnitude: {correction_magnitude:.4f}")
            
            metrics['corrections_applied'].append({
                'iteration': iteration + 1,
                'tag_error': tag_error.tolist(),
                'robot_correction': robot_correction.tolist(),
                'correction_magnitude': correction_magnitude
            })
        
        # Step 6: Move to final corrected target pose
        if metrics['converged']:
            print(f"🎯 Moving to final corrected target pose...")
            success = self.robot.move_to_pose(current_target_pose)
            if not success:
                print(f"❌ Failed to move robot to final target pose")
                return False, metrics
        
        # Final metrics
        metrics['total_correction'] = total_correction
        metrics['final_robot_pose'] = current_target_pose.tolist()
        metrics['final_obs_pose'] = (stored_obs_robot_pose + total_correction).tolist()
        
        if not metrics['converged']:
            print(f"⚠️  Did not converge within {self.config.max_iterations} iterations")
            metrics['final_error'] = pose_error_magnitude
        
        # Record in history (record for target position)
        self.pose_history.record_correction(
            position_name, stored_target_pose, current_target_pose,
            stored_obs_tag_pose, current_obs_tag_pose, metrics)
        
        # Update stored pose if requested and converged
        if update_stored_pose and metrics['converged']:
            success = self.pose_history.update_position_pose(
                position_name, current_target_pose, None)  # No direct camera_to_tag for target
            metrics['pose_updated'] = success
            
            if success:
                print(f"💾 Updated stored pose for '{position_name}'")
                
            # Also update observation pose
            obs_success = self.pose_history.update_position_pose(
                observation_pose_name, stored_obs_robot_pose + total_correction, current_obs_tag_pose)
            metrics['obs_pose_updated'] = obs_success
        
        print(f"\n🎯 Observation-based visual servoing completed for '{position_name}'")
        print(f"   Converged: {metrics['converged']}")
        print(f"   Iterations: {metrics['iterations']}")
        print(f"   Total correction: {np.linalg.norm(total_correction):.4f}")
        
        return metrics['converged'], metrics
    
    def check_position_drift(self, position_name: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if a position has drifted from its stored location
        
        Args:
            position_name: Name of position to check
            
        Returns:
            (has_drifted, metrics) tuple
        """
        print(f"🔍 Checking position drift for '{position_name}'")
        
        position_data = self._get_position_data(position_name)
        if not position_data or 'tag_reference' not in position_data:
            return False, {'error': 'Position not found or no tag reference'}
        
        tag_id = position_data['tag_reference']
        stored_tag_pose = np.array(position_data['camera_to_tag'])
        
        # Detect current tag pose
        current_tag_pose = self.detection_filter.get_filtered_tag_pose(tag_id)
        if current_tag_pose is None:
            return False, {'error': 'Failed to detect AprilTag'}
        
        # Calculate drift
        drift = current_tag_pose - stored_tag_pose
        translation_drift = np.linalg.norm(drift[:3])
        rotation_drift = np.linalg.norm(drift[3:])
        
        # Determine if significant drift
        has_drifted = (translation_drift > self.config.position_tolerance * 2 or
                      rotation_drift > self.config.rotation_tolerance * 2)
        
        metrics = {
            'position_name': position_name,
            'tag_id': tag_id,
            'translation_drift': translation_drift,
            'rotation_drift': rotation_drift,
            'drift_vector': drift.tolist(),
            'has_drifted': has_drifted,
            'stored_tag_pose': stored_tag_pose.tolist(),
            'current_tag_pose': current_tag_pose.tolist()
        }
        
        print(f"📊 Drift analysis:")
        print(f"   Translation drift: {translation_drift:.4f}m")
        print(f"   Rotation drift: {rotation_drift:.4f}rad") 
        print(f"   Significant drift: {has_drifted}")
        
        return has_drifted, metrics
    
    def _get_position_data(self, position_name: str) -> Optional[Dict[str, Any]]:
        """Get position data from taught positions file"""
        try:
            positions_data = self.pose_history._load_positions()
            return positions_data.get('positions', {}).get(position_name)
        except Exception as e:
            print(f"❌ Failed to load position data: {e}")
            return None
    
    def _validate_correction(self, correction: np.ndarray, total_correction: np.ndarray) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate that correction is within safety limits
        
        Args:
            correction: Proposed correction vector
            total_correction: Cumulative correction so far
            
        Returns:
            (is_valid, metrics) tuple
        """
        translation_magnitude = np.linalg.norm(correction[:3])
        rotation_magnitude = np.linalg.norm(correction[3:])
        total_translation_magnitude = np.linalg.norm(total_correction[:3] + correction[:3])
        
        # Check individual correction limits
        translation_ok = translation_magnitude <= self.config.max_translation_correction
        rotation_ok = rotation_magnitude <= self.config.max_rotation_correction
        total_ok = total_translation_magnitude <= self.config.max_total_correction
        
        is_valid = translation_ok and rotation_ok and total_ok
        
        metrics = {
            'correction_translation': translation_magnitude,
            'correction_rotation': rotation_magnitude,
            'total_translation': total_translation_magnitude,
            'translation_ok': translation_ok,
            'rotation_ok': rotation_ok,
            'total_ok': total_ok,
            'safety_limits': {
                'max_translation': self.config.max_translation_correction,
                'max_rotation': self.config.max_rotation_correction,
                'max_total': self.config.max_total_correction
            }
        }
        
        if not is_valid:
            print(f"⚠️  Safety limit violation:")
            if not translation_ok:
                print(f"   Translation: {translation_magnitude:.4f}m > {self.config.max_translation_correction:.4f}m")
            if not rotation_ok:
                print(f"   Rotation: {rotation_magnitude:.4f}rad > {self.config.max_rotation_correction:.4f}rad")
            if not total_ok:
                print(f"   Total correction: {total_translation_magnitude:.4f}m > {self.config.max_total_correction:.4f}m")
        
        return is_valid, metrics
    
    def setup_position_for_visual_servo(self, position_name: str, tag_id: int, camera_to_tag_transform: np.ndarray) -> bool:
        """
        Setup a position for visual servoing by storing AprilTag association
        
        Args:
            position_name: Name of the taught position
            tag_id: AprilTag ID to associate with this position
            camera_to_tag_transform: 6D pose transform from camera to tag
            
        Returns:
            True if setup successful
        """
        try:
            # Update the position data with visual servo information
            success = self.pose_history.update_position_tag_association(
                position_name, f"tag_{tag_id}", camera_to_tag_transform.tolist())
            
            if success:
                print(f"✅ Position '{position_name}' configured for visual servoing with Tag {tag_id}")
                return True
            else:
                print(f"❌ Failed to configure position '{position_name}' for visual servoing")
                return False
                
        except Exception as e:
            print(f"❌ Error setting up visual servo for position '{position_name}': {e}")
            return False
    
    def get_corrected_pose(self, position_name: str, original_pose: np.ndarray) -> Optional[np.ndarray]:
        """
        Get a corrected pose for a position using visual servoing (without moving the robot)
        
        Args:
            position_name: Name of the taught position
            original_pose: Original pose coordinates
            
        Returns:
            Corrected pose array, or None if correction failed
        """
        print(f"🎯 Computing visual servo correction for position '{position_name}'")
        
        # Load position data
        position_data = self._get_position_data(position_name)
        if not position_data:
            return None
        
        # Check if position has AprilTag reference
        if 'tag_reference' not in position_data or not position_data['tag_reference']:
            print(f"❌ Position '{position_name}' has no AprilTag reference")
            return None
        
        if 'camera_to_tag' not in position_data or not position_data['camera_to_tag']:
            print(f"❌ Position '{position_name}' has no stored camera-to-tag transform")
            return None
        
        tag_reference = position_data['tag_reference']
        stored_tag_pose = np.array(position_data['camera_to_tag'])
        
        # Extract tag ID from reference
        if isinstance(tag_reference, str) and tag_reference.startswith('tag_'):
            tag_id = int(tag_reference.split('_')[1])
        else:
            tag_id = int(tag_reference)
        
        # Detect current AprilTag pose
        current_tag_pose = self.detection_filter.get_filtered_tag_pose(tag_id)
        if current_tag_pose is None:
            print(f"❌ Failed to detect AprilTag {tag_id}")
            return None
        
        # Calculate pose correction
        tag_error = current_tag_pose - stored_tag_pose
        robot_correction = -tag_error  # Negative to counteract the error
        
        # Apply safety limits
        correction_valid, safety_metrics = self._validate_correction(
            robot_correction, np.zeros(6))  # Zero total correction for single-shot calculation
        
        if not correction_valid:
            print(f"❌ Calculated correction exceeds safety limits")
            return None
        
        corrected_pose = original_pose + robot_correction
        
        correction_magnitude = np.linalg.norm(robot_correction)
        print(f"🔧 Calculated correction magnitude: {correction_magnitude:.4f}")
        print(f"   Translation correction: [{robot_correction[0]:.4f}, {robot_correction[1]:.4f}, {robot_correction[2]:.4f}]m")
        print(f"   Rotation correction: [{robot_correction[3]:.4f}, {robot_correction[4]:.4f}, {robot_correction[5]:.4f}]rad")
        
        return corrected_pose
    
    def set_robot_controller(self, robot_controller):
        """Set the robot controller instance"""
        self.robot = robot_controller
        print("🤖 Robot controller set for visual servo engine")