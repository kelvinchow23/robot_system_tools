# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Removed
- handeye_calibration/ directory and all hand-eye calibration scripts: collect_handeye_data.py, calculate_handeye_calibration.py, coordinate_transformer.py, etc.
- handeye_rework/ directory and experimental calibration approaches
- Hand-eye calibration related files from root: handeye_result.yaml, handeye_samples.json, analyze_motion.py, check_distances.py, test_close_distance.py
- Hand-eye calibration sections from README.md, simplified to focus on pure AprilTag detection workflow

### Rationale
- Hand-eye calibration was not producing realistic reslts
- AprilTag detection works effectively without requiring camera-to-robot transformation
- Simplified codebase focuses on core functionality: camera capture, AprilTag detection, and robot control as separate components
- handeye_rework/collect_samples.py: implemented real robot/camera/apriltag hooks using existing interfaces

## [2025-09-12] - Camera Coordinate Frame Correction for Hand-Eye Calibration

### Added
- `tests/test_camera_coordinate_frame.py` - Empirical camera frame mapping test with automatic robot movement
- Coordinate frame correction in `calculate_handeye_calibration.py` 
- Camera-to-robot coordinate transformation matrix based on empirical testing

### Changed
- Updated hand-eye calibration to account for OpenCV camera frame vs robot frame differences
- Robot X+ (RIGHT) → Camera X+, Robot Y+ (BACK) → Camera Z+, Robot Z+ (UP) → Camera Y+
- Applied coordinate transformation: Camera [X,Y,Z] → Robot [X,Z,-Y]

### Fixed
- Hand-eye calibration offset issue (~0.95m → expected 10-30cm) by correcting coordinate frame mismatch
- Camera pose data now properly transformed from OpenCV convention to robot frame before calibration

## [2025-09-11] - Code Organization and Testing Utilities

### Added
- `tests/live_robot_monitor.py` - Real-time robot pose monitoring with quaternion/matrix display
- `tests/rotations_cli.py` - CLI utility for rotation vector analysis and comparison
- `tests/debug_coordinate_frames.py` - Coordinate frame debugging utility

### Changed
- Moved debugging and testing utilities from main directory to `tests/`
- Improved code organization by separating core functionality from testing tools

## [2025-01-20] - TCP Pose Accuracy and Configuration Management

### Added
- Centralized robot configuration via `robots/ur/robot_config.yaml`
- TCP pose sign verification utility (`robots/ur/test_pose_signs.py`)
- Command-line IP override support for all robot scripts
- Configuration loading with fallback to defaults

### Fixed
- Removed incorrect Ry/Rz sign corrections - raw RTDE readings now match teach pendant
- Eliminated hardcoded robot IPs throughout codebase
- TCP pose reading accuracy for reliable hand-eye calibration

### Changed
- `ur_robot_interface.py`: Now loads robot IP and settings from YAML config
- `test_robot_pose.py`: Added config file support with command-line override
- `collect_handeye_data.py`: Added config file support with command-line override
- All robot scripts now use centralized configuration management

### Previous

### Added
- Comprehensive AprilTag pick-and-place workflow documentation in README
- TCP pose reading accuracy verification utility (`robots/ur/test_robot_pose.py`)
- Read-only mode for safer hand-eye calibration data collection
- Improved calibration file path handling to save in proper directories

### Fixed
- Hand-eye calibration TCP pose reading accuracy issues
- Calibration data file paths now save to correct handeye_calibration directory

### Changed
- Hand-eye calibration data collection now uses read-only mode by default
- Updated workflow documentation with immediate testing after each setup step

## [2025-09-05] - Hand-Eye Calibration Improvements

### Summary
- Addressed TCP pose reading accuracy that was affecting hand-eye calibration quality
- Improved safety and workflow for calibration data collection
- Added comprehensive documentation for complete AprilTag workflow

### Next Steps
- Verify TCP pose accuracy using the new test utility
- Re-collect hand-eye calibration data with corrected pose readings
- Continue refinement of calibration quality metrics