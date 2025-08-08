# UR3 Robot Arm Camera Client

Computer vision client for requesting photos from camera server and performing AprilTag detection.

## Features

- **Photo requests** - Connect to camera server and request photos
- **AprilTag detection** - Full 3D pose estimation with pupil-apriltags
- **Camera calibration** - Checkerboard-based camera calibration
- **Complete workflow** - Integrated calibration, capture, and detection
- **Flexible input** - Live capture, latest photo, or file-based detection

## Quick Setup

### 1. Install Dependencies
```bash
./setup.sh
```

### 2. Configure Server Connection
Edit `config.yaml`:
```yaml
network:
  hostname: "ur3-picam-apriltag"  # Your Pi hostname/IP
  server_port: 2222
```

### 3. Run Workflow
```bash
python robot_vision_workflow.py
```

## Available Scripts

### Camera Client
```bash
# Request a photo from server
python camera_client.py
```

### Camera Calibration  
```bash
# Calibrate camera for accurate pose estimation
python calibrate_camera.py
```

### AprilTag Detection
```bash
# Detect AprilTags with 3D pose estimation
python detect_apriltags.py
```

### Complete Workflow
```bash
# Interactive menu for all functions
python robot_vision_workflow.py
```

## AprilTag Detection Results

The detector provides:
- **Tag ID** and center position
- **3D pose** (translation and rotation)
- **Distance** from camera in centimeters
- **Euler angles** (roll, pitch, yaw) in degrees
- **Annotated images** with detected tags

Example output:
```
🏷️  Tag ID: 42
   📍 Center: (640.2, 480.1) pixels
   📏 Distance: 25.3 cm
   🔄 Rotation: (2.1°, -5.4°, 12.7°)
   📐 Translation: (0.123, -0.045, 0.253) m
```

## Camera Calibration

For accurate pose estimation, calibrate your camera:

1. **Print checkerboard pattern** (8x5 inner corners, 23mm squares)
2. **Capture 10-20 images** at different angles and distances
3. **Run calibration:**
   ```bash
   python calibrate_camera.py
   ```
4. **Parameters saved** to `camera_params.npy`

## Robot Integration

### Basic Usage
```python
from camera_client import CameraClient
from detect_apriltags import AprilTagDetector

# Setup
client = CameraClient()
detector = AprilTagDetector()

# Capture and detect
results = detector.capture_and_detect()

# Process results
for detection in results['detections']:
    tag_id = detection['tag_id']
    distance = detection['distance_cm']
    position = detection['pose_translation']
    print(f"Tag {tag_id} at {distance:.1f}cm")
```

### Advanced Integration
```python
# For robot control loops
def get_target_pose():
    results = detector.capture_and_detect()
    if results and len(results['detections']) > 0:
        # Find specific tag
        for det in results['detections']:
            if det['tag_id'] == TARGET_TAG_ID:
                return {
                    'position': det['pose_translation'],
                    'orientation': det['euler_degrees'],
                    'distance': det['distance_cm']
                }
    return None

# Use in robot control
target = get_target_pose()
if target:
    robot.move_to_relative_pose(target['position'])
```

## File Structure

```
client/
├── camera_client.py          # Photo request client
├── detect_apriltags.py       # AprilTag detection
├── calibrate_camera.py       # Camera calibration
├── robot_vision_workflow.py  # Complete workflow
├── config.yaml              # Configuration
├── config_manager.py        # Config handling  
├── network_utils.py         # Network utilities
├── requirements.txt         # Dependencies
├── setup.sh                # Installation
├── downloaded_photos/       # Received photos
└── checkerboard_images/     # Calibration images
```

## Configuration

### AprilTag Settings
```yaml
# In detect_apriltags.py, modify:
families = "tagStandard41h12"  # Tag family
tagsize_mm = 13               # Physical tag size
```

### Detection Parameters
```python
# Fine-tune detection in AprilTagDetector.__init__():
self.detector = Detector(
    families=self.families,
    nthreads=1,              # CPU threads
    quad_decimate=1.0,       # Speed vs accuracy
    quad_sigma=0.0,          # Blur sigma
    refine_edges=1,          # Edge refinement
    decode_sharpening=0.25   # Sharpening
)
```

## Troubleshooting

**Cannot connect to server:**
- Check Pi is running: `ssh pi@ur3-picam-apriltag`
- Verify server: `python3 camera_server.py`
- Test network: `ping ur3-picam-apriltag`

**No AprilTags detected:**
- Check lighting conditions
- Verify tag size in code matches physical tags
- Ensure camera is calibrated
- Try different detection parameters

**Poor pose estimation:**
- Run camera calibration with more images
- Use high-quality checkerboard pattern
- Ensure tag size is accurate in millimeters
- Check for camera distortion
