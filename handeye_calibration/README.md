# Hand-Eye Calibration for UR Robot

Complete hand-eye calibration system for Universal Robots with wrist-mounted camera.

## Overview

This system performs **eye-in-hand** calibration to determine the transformation between the robot's TCP (Tool Center Point) and the camera coordinate frame. Once calibrated, AprilTag detections can be transformed from camera coordinates to robot base coordinates for accurate manipulation.

## Architecture

```
Robot Base Frame
    ↓ (Known: robot kinematics)
Robot TCP Frame  
    ↓ (Unknown: hand-eye calibration determines this)
Camera Frame
    ↓ (Known: AprilTag detection)
AprilTag Frame
```

## Files

- **`collect_handeye_data.py`** - Interactive data collection
- **`calculate_handeye_calibration.py`** - Solve calibration problem  
- **`coordinate_transformer.py`** - Runtime coordinate transformation
- **`../ur_robot_interface.py`** - UR robot communication interface

## Prerequisites

### Hardware
- Universal Robots arm (UR3, UR5, UR10, etc.)
- Wrist-mounted camera (Raspberry Pi camera)
- AprilTag printed on rigid surface
- Network connection between robot and computer

### Software
```bash
pip install ur_rtde numpy opencv-python scipy pyyaml
```

### Robot Setup
1. Enable external control on UR robot
2. Note robot IP address
3. Ensure TCP is configured correctly

## Quick Start

### Step 1: Data Collection

Place an AprilTag in the robot workspace where it will be visible from multiple angles.

```bash
# Automatic pose generation (recommended)
python collect_handeye_data.py \
    --robot-ip 192.168.1.100 \
    --auto-poses \
    --num-poses 15 \
    --hemisphere-radius 0.15

# Manual pose collection
python collect_handeye_data.py \
    --robot-ip 192.168.1.100 \
    --camera-config ../client_config.yaml
```

**Data Collection Tips:**
- Collect 10-15 data points minimum
- Vary robot orientation significantly 
- Keep AprilTag visible in all poses
- Ensure good lighting conditions
- Move around a hemisphere for optimal coverage

### Step 2: Calculate Calibration

```bash
python calculate_handeye_calibration.py \
    --input handeye_data_20250825_143022.json \
    --method tsai \
    --validate
```

**Available Methods:**
- `tsai` - Tsai and Lenz (recommended)
- `park` - Park and Martin
- `horaud` - Horaud and Dornaika  
- `andreff` - Andreff and Horaud
- `daniilidis` - Daniilidis

### Step 3: Use Calibration

```python
from coordinate_transformer import CoordinateTransformer
from ur_robot_interface import URRobotInterface

# Initialize
transformer = CoordinateTransformer('handeye_calibration_20250825_143055.yaml')
robot = URRobotInterface('192.168.1.100')

# Get current robot pose
robot_pose = robot.get_tcp_pose()

# Transform AprilTag detection to robot frame
robot_detection = transformer.transform_apriltag_detection(
    apriltag_detection, robot_pose
)

# Extract position in robot base frame
tag_position = robot_detection['robot_frame_pose']['translation_vector']
print(f"AprilTag position in robot frame: {tag_position}")
```

## Detailed Workflow

### 1. Data Collection Process

The data collection script guides you through capturing robot pose + camera observation pairs:

```bash
python collect_handeye_data.py --robot-ip YOUR_ROBOT_IP --auto-poses
```

**What happens:**
1. Robot moves to generated poses around a hemisphere
2. At each pose, captures image and detects AprilTag
3. Records robot TCP pose and AprilTag pose in camera frame
4. Saves data as JSON file for calibration

**Manual Collection Alternative:**
```bash
python collect_handeye_data.py --robot-ip YOUR_ROBOT_IP
```
- Move robot manually using teach pendant
- Press ENTER at each desired pose to collect data
- More flexible but requires good pose selection

### 2. Calibration Calculation

Solves the hand-eye calibration problem **AX = XB** where:
- **A** = Robot base to TCP transformations
- **B** = Camera to AprilTag transformations  
- **X** = Camera to TCP transformation (unknown)

```bash
python calculate_handeye_calibration.py \
    --input handeye_data_20250825_143022.json \
    --output my_calibration.yaml \
    --method tsai \
    --validate
```

**Output:** YAML file containing camera-to-robot transformation

### 3. Runtime Usage

Use the calibration to transform coordinates:

```python
# Transform AprilTag detection to robot coordinates
robot_frame_detection = transformer.transform_apriltag_detection(
    camera_detection, current_robot_pose
)

# Get 3D position in robot base frame
tag_position = robot_frame_detection['robot_frame_pose']['translation_vector']

# Move robot relative to detected tag
target_pose = current_robot_pose.copy()
target_pose[:3] = tag_position
target_pose[2] += 0.05  # 5cm above tag
robot.move_to_pose(target_pose)
```

## Calibration Quality

### Expected Accuracy
- **Excellent**: < 5mm position error
- **Good**: 5-10mm position error  
- **Fair**: 10-20mm position error
- **Poor**: > 20mm position error

### Improving Quality
1. **More data points** - Collect 15-20 poses
2. **Better pose distribution** - Use hemisphere generation
3. **Stable conditions** - Good lighting, fixed AprilTag
4. **Camera calibration** - Ensure accurate intrinsics
5. **Robot precision** - Use slower movements

## Troubleshooting

### "No AprilTag detected"
- Check lighting conditions
- Verify AprilTag is not damaged
- Ensure tag is within camera field of view
- Check camera focus and exposure

### "Poor calibration quality"  
- Collect more data points with better pose variation
- Check that AprilTag was stationary during collection
- Verify camera calibration accuracy
- Ensure robot TCP is configured correctly

### "Robot connection failed"
- Verify robot IP address
- Check network connectivity
- Ensure robot is in remote control mode
- Confirm UR software version compatibility

### "Import errors"
- Install required packages: `pip install ur_rtde numpy opencv-python scipy pyyaml`
- Check Python version compatibility
- Verify camera server is running on Pi

## Integration with Pick and Place

Once calibrated, you can implement precise pick and place:

```python
# 1. Detect AprilTag on object
detection = detect_apriltag_in_workspace()

# 2. Transform to robot coordinates  
robot_detection = transformer.transform_apriltag_detection(detection, robot.get_tcp_pose())

# 3. Calculate grasp pose relative to tag
tag_position = np.array(robot_detection['robot_frame_pose']['translation_vector'])
grasp_position = tag_position + np.array([0, 0, 0.02])  # 2cm above tag

# 4. Execute pick
robot.move_to_pose(np.concatenate([grasp_position, robot.get_tcp_pose()[3:]]))
```

## File Formats

### Data Collection Output (JSON)
```json
{
  "robot_poses": [[x, y, z, rx, ry, rz], ...],
  "camera_poses": [
    {
      "translation": [x, y, z],
      "rotation_vector": [rx, ry, rz], 
      "tag_id": 0,
      "quality": 85.3,
      "image_path": "path/to/image.jpg"
    }, ...
  ],
  "timestamps": ["2025-08-25T14:30:22", ...],
  "robot_ip": "192.168.1.100",
  "apriltag_config": {...}
}
```

### Calibration Output (YAML)
```yaml
success: true
method: "Tsai"
camera_to_robot_R: [[...], [...], [...]]
camera_to_robot_t: [x, y, z]
camera_to_robot_pose: [x, y, z, rx, ry, rz]
camera_to_robot_matrix: [[...], [...], [...], [...]]
calibration_date: "2025-08-25T14:30:55"
num_data_points: 15
```

## Next Steps

After successful hand-eye calibration:

1. **Teach Reference Poses** - Define grasp poses relative to AprilTags
2. **Implement Pick and Place** - Use transformed coordinates for manipulation
3. **Add Error Handling** - Handle missing/poor tag detections
4. **Multi-Tag Systems** - Use multiple tags for complex scenes
5. **Continuous Tracking** - Real-time pose updates during motion

## Support

For issues or questions:
1. Check troubleshooting section above
2. Verify all prerequisites are met
3. Test with simpler poses first
4. Review calibration quality metrics
