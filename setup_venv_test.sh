#!/bin/bash
# Virtual Environment Setup Script for Robot System Tools (Test Version)
# This script creates a Python virtual environment using system Python and installs all dependencies

set -e  # Exit on any error

PROJECT_NAME="robot_system_tools"
VENV_NAME="venv_test"
PYTHON_VERSION="/usr/bin/python3"  # Use system Python explicitly

echo "🤖 Robot System Tools - Virtual Environment Setup (Test)"
echo "========================================================"

# Check if Python 3 is available
if ! command -v $PYTHON_VERSION &> /dev/null; then
    echo "❌ Error: $PYTHON_VERSION not found. Please install Python 3."
    exit 1
fi

echo "✅ Found Python: $PYTHON_VERSION"
echo "   Version: $($PYTHON_VERSION --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_NAME" ]; then
    echo "📦 Creating virtual environment: $VENV_NAME"
    $PYTHON_VERSION -m venv $VENV_NAME
else
    echo "📦 Virtual environment already exists: $VENV_NAME"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source $VENV_NAME/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install core requirements first
echo "📥 Installing core requirements..."
pip install numpy scipy matplotlib PyYAML opencv-python

# Install robot-specific packages
echo "🤖 Installing robot control packages..."
pip install ur-rtde

# Install vision packages
echo "👁️  Installing vision packages..."
pip install pupil-apriltags transforms3d

# Install development packages
echo "🔧 Installing development packages..."
pip install pytest pytest-cov click

# Verify installation
echo "🔍 Verifying critical packages..."

python -c "import numpy; print(f'✅ NumPy: {numpy.__version__}')" || echo "❌ NumPy failed"
python -c "import cv2; print(f'✅ OpenCV: {cv2.__version__}')" || echo "❌ OpenCV failed"
python -c "import yaml; print('✅ PyYAML: OK')" || echo "❌ PyYAML failed"
python -c "import pupil_apriltags; print('✅ AprilTags: OK')" || echo "❌ AprilTags failed"
python -c "import scipy; print(f'✅ SciPy: {scipy.__version__}')" || echo "❌ SciPy failed"

# Test RTDE specifically
echo "🤖 Testing UR RTDE..."
python -c "import rtde_control, rtde_receive; print('✅ UR RTDE: Import successful')" || echo "❌ UR RTDE: Import failed"

echo ""
echo "🎉 Virtual environment setup complete!"
echo ""
echo "To activate the environment:"
echo "   source $VENV_NAME/bin/activate"
echo ""
echo "To test robot connection:"
echo "   source $VENV_NAME/bin/activate"
echo "   python tests/test_ur_robot.py --robot-ip 192.168.0.10"
echo ""
