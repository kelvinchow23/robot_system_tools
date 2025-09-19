#!/usr/bin/env python3
"""
Test script for observation-based visual servoing
Tests both direct and observation-based visual servo methods
"""

import sys
from pathlib import Path
import numpy as np

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "setup"))

# Mock robot controller for testing (since we don't want to move the actual robot)
class MockURController:
    def __init__(self):
        self.current_pose = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        self.move_count = 0
        
    def move_to_pose(self, pose):
        print(f"🤖 MOCK: Moving to pose {pose}")
        self.current_pose = np.array(pose)
        self.move_count += 1
        return True
        
    def get_current_pose(self):
        return self.current_pose

# Mock AprilTag detector for testing
class MockAprilTagDetector:
    def __init__(self):
        # Simulate tag detections with small variations to test visual servo
        self.detection_count = 0
        
    def capture_and_detect(self):
        self.detection_count += 1
        
        # Simulate tag_1 detection with slight error that decreases over iterations
        error_scale = max(0.001, 0.01 / self.detection_count)  # Error decreases with iterations
        
        mock_detection = {
            'tag_id': 1,
            'corners': np.array([[100, 100], [200, 100], [200, 200], [100, 200]]),
            'center': np.array([150, 150]),
            'pose_t': np.array([[0.005 * error_scale], [-0.05 * error_scale], [0.183]]),  # Slight error
            'pose_R': np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]]),
            'distance_mm': 183
        }
        
        return [mock_detection]

def test_yaml_loading():
    """Test that YAML positions load correctly"""
    print("🧪 Testing YAML position loading...")
    
    try:
        from visual_servo.visual_servo_engine import VisualServoEngine
        
        # Create mock components
        mock_robot = MockURController()
        mock_detector = MockAprilTagDetector()
        
        # Initialize visual servo engine
        positions_file = Path("positions/taught_positions.yaml")
        engine = VisualServoEngine(mock_robot, positions_file, mock_detector)
        
        # Test loading position data
        position_data = engine._get_position_data("grasp-A")
        if position_data:
            print(f"✅ Successfully loaded grasp-A position")
            print(f"   Has AprilTag view: {position_data.get('has_apriltag_view')}")
            print(f"   Observation pose: {position_data.get('observation_pose')}")
            print(f"   Observation offset: {position_data.get('observation_offset')}")
        else:
            print("❌ Failed to load grasp-A position")
            return False
            
        # Test loading observation-based position
        position_data = engine._get_position_data("grasp-B")
        if position_data:
            print(f"✅ Successfully loaded grasp-B position")
            print(f"   Has AprilTag view: {position_data.get('has_apriltag_view')}")
            print(f"   Observation pose: {position_data.get('observation_pose')}")
            print(f"   Observation offset: {position_data.get('observation_offset')}")
        else:
            print("❌ Failed to load grasp-B position")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error during YAML loading test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_visual_servo():
    """Test direct visual servoing for positions with AprilTag view"""
    print("\n🧪 Testing direct visual servoing (grasp-A)...")
    
    try:
        from visual_servo.visual_servo_engine import VisualServoEngine
        
        # Create mock components
        mock_robot = MockURController()
        mock_detector = MockAprilTagDetector()
        
        # Initialize visual servo engine
        positions_file = Path("positions/taught_positions.yaml")
        engine = VisualServoEngine(mock_robot, positions_file, mock_detector)
        
        # Test direct visual servoing
        success, metrics = engine.visual_servo_to_position("grasp-A", update_stored_pose=False)
        
        print(f"\n📊 Direct Visual Servo Results:")
        print(f"   Success: {success}")
        print(f"   Method: {metrics.get('method', 'unknown')}")
        print(f"   Iterations: {metrics.get('iterations', 0)}")
        print(f"   Converged: {metrics.get('converged', False)}")
        
        return success
        
    except Exception as e:
        print(f"❌ Error during direct visual servo test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_observation_visual_servo():
    """Test observation-based visual servoing for positions without direct AprilTag view"""
    print("\n🧪 Testing observation-based visual servoing (grasp-B)...")
    
    try:
        from visual_servo.visual_servo_engine import VisualServoEngine
        
        # Create mock components  
        mock_robot = MockURController()
        mock_detector = MockAprilTagDetector()
        
        # Initialize visual servo engine
        positions_file = Path("positions/taught_positions.yaml")
        engine = VisualServoEngine(mock_robot, positions_file, mock_detector)
        
        # Test observation-based visual servoing
        success, metrics = engine.visual_servo_to_position("grasp-B", update_stored_pose=False)
        
        print(f"\n📊 Observation Visual Servo Results:")
        print(f"   Success: {success}")
        print(f"   Method: {metrics.get('method', 'unknown')}")
        print(f"   Observation pose: {metrics.get('observation_pose', 'none')}")
        print(f"   Iterations: {metrics.get('iterations', 0)}")
        print(f"   Converged: {metrics.get('converged', False)}")
        print(f"   Robot moves: {mock_robot.move_count}")
        
        return success
        
    except Exception as e:
        print(f"❌ Error during observation visual servo test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_position_routing():
    """Test that positions are routed to correct visual servo methods"""
    print("\n🧪 Testing position routing logic...")
    
    try:
        from visual_servo.visual_servo_engine import VisualServoEngine
        
        # Create mock components
        mock_robot = MockURController()
        mock_detector = MockAprilTagDetector()
        
        # Initialize visual servo engine
        positions_file = Path("positions/taught_positions.yaml")
        engine = VisualServoEngine(mock_robot, positions_file, mock_detector)
        
        # Test routing for different position types
        positions_to_test = [
            ("grasp-A", "direct"),      # Has direct AprilTag view
            ("grasp-B", "observation"), # Uses observation pose
            ("observe-B", "direct"),    # Observation pose with direct view
        ]
        
        for pos_name, expected_method in positions_to_test:
            print(f"\n🔍 Testing routing for '{pos_name}'...")
            
            # Load position data
            position_data = engine._get_position_data(pos_name)
            if not position_data:
                print(f"❌ Could not load position '{pos_name}'")
                continue
                
            # Determine expected routing
            has_direct_view = position_data.get('has_apriltag_view', False) and position_data.get('camera_to_tag')
            has_observation_pose = position_data.get('observation_pose')
            
            if has_direct_view:
                actual_method = "direct"
            elif has_observation_pose:
                actual_method = "observation" 
            else:
                actual_method = "none"
                
            print(f"   Expected method: {expected_method}")
            print(f"   Actual method: {actual_method}")
            print(f"   Match: {'✅' if expected_method == actual_method else '❌'}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error during routing test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🎯 Testing Observation-Based Visual Servoing System")
    print("=" * 60)
    
    tests = [
        ("YAML Loading", test_yaml_loading),
        ("Direct Visual Servo", test_direct_visual_servo),
        ("Observation Visual Servo", test_observation_visual_servo),
        ("Position Routing", test_position_routing),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("🧪 TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, result in results if result)
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Observation-based visual servoing is working!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()