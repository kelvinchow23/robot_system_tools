# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Confirmed working UR robot interface with RTDE library (2025-08-26)
- Robot configuration YAML file for UR robot settings (2025-08-26)
- Python package structure with __init__.py files for all modules (2025-08-26)
- Development practices documentation (2025-08-26)
- UR robot interface with real ur_rtde support (2025-08-25)
- Hand-eye calibration system for UR robots (2025-08-25)
- Command-line arguments for camera test scripts (2025-08-25)
- AprilTag detection with pose estimation (2025-08-25)
- Camera calibration workflow (2025-08-25)

### Fixed
- RTDE library compatibility issues resolved using system Python environment (2025-08-26)
- Robot movement commands now working with proper RTDE authentication (2025-08-26)

### Removed
- Temporary troubleshooting files and interfaces (2025-08-26)

### Changed
- Reorganized repository structure with proper directory hierarchy (2025-08-26)
  - Development practices moved to .github/copilot-instructions.md
  - Documentation moved to documentation/ directory
  - PiCam module and setup script moved to camera/picam/
  - UR robot interface moved to robots/ur/
  - All test scripts moved to tests/ directory
  - setup_client.sh renamed to setup_picam_client.sh
- Cleaned up duplicate if __name__ == "__main__" blocks in camera_server.py (2025-08-26)
- Removed mock interface fallback from UR robot interface (2025-08-26)
- Fixed PiCam constructor usage in test scripts (2025-08-25)

### Removed
- Empty and unused files: calibrate_camera.py, check_pi_leds.py, generate_checkerboard.py, pi_led_controller.py, test_calibration.py, test_camera_with_config.py, ur_robot_interface_mock.py, pi_cam_server/blink_act_led.py, pi_cam_server/pi_led_controller.py (2025-08-26)
- Mock UR robot interface file (2025-08-26)
