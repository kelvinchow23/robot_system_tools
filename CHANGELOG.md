# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Comprehensive AprilTag pick-and-place workflow documentation in README
- TCP pose reading accuracy verification utility (`robots/ur/test_robot_pose.py`)
- Sign correction for UR robot TCP pose reading to match teach pendant convention
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