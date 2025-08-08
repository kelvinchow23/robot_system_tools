#!/bin/bash
# Setup script for CLIENT computer (Windows/Linux/Robot Controller)
# Installs full computer vision stack for AprilTag detection

echo "Setting up UR3 Camera Client with Computer Vision..."

# Install Python dependencies for computer vision
echo "Installing computer vision dependencies..."
pip install -r requirements_client.txt

echo "Client setup complete!"
echo ""
echo "📝 This computer is configured as a CAMERA CLIENT with AprilTag detection"
echo ""
echo "🚀 Usage:"
echo "   Request photo:           python camera_client.py"
echo "   Complete workflow:       python robot_vision_workflow.py" 
echo "   Camera calibration:      python calibrate_camera.py"
echo "   AprilTag detection:      python detect_apriltags.py"
echo ""
echo "🔧 Make sure camera server is running on Pi:"
echo "   ssh pi@ur3-picam-apriltag"
echo "   python3 camera_server.py"
