#!/bin/bash
# Fix picamera2 libcamera issue in ur3_cam_env

echo "=== Fixing picamera2 libcamera issue ==="

# Activate virtual environment
source ur3_cam_env/bin/activate

echo "Uninstalling pip-installed picamera2..."
pip uninstall -y picamera2 || echo "picamera2 not installed via pip"

echo "Ensuring system picamera2 is available..."
sudo apt install -y python3-picamera2 python3-libcamera

echo "Checking installed packages..."
dpkg -l | grep -E "(picamera|libcamera)" || echo "No picamera/libcamera packages found"

echo "Checking Python package locations..."
python3 -c "
import site
print('Site packages:')
for path in site.getsitepackages():
    print(f'  {path}')
print()
print('User site packages:', site.getusersitepackages())
"

echo "Testing imports with system packages..."
python3 -c "
import sys
# Add system packages to Python path
sys.path.insert(0, '/usr/lib/python3/dist-packages')

print('Python path:')
for p in sys.path:
    print(f'  {p}')
print()

# Check if picamera2 files exist
import os
picamera2_paths = [
    '/usr/lib/python3/dist-packages/picamera2',
    '/usr/lib/python3.11/dist-packages/picamera2',
    '/usr/local/lib/python3.11/dist-packages/picamera2'
]

print('Checking picamera2 locations:')
for path in picamera2_paths:
    exists = os.path.exists(path)
    print(f'  {path}: {\"exists\" if exists else \"not found\"}')
print()

try:
    import libcamera
    print('✓ libcamera import successful')
except ImportError as e:
    print(f'✗ libcamera import failed: {e}')
    exit(1)

try:
    from picamera2 import Picamera2
    print('✓ picamera2 import successful')
except ImportError as e:
    print(f'✗ picamera2 import failed: {e}')
    print('Trying alternative paths...')
    
    # Try adding more paths
    sys.path.insert(0, '/usr/lib/python3.11/dist-packages')
    sys.path.insert(0, '/usr/local/lib/python3.11/dist-packages')
    
    try:
        from picamera2 import Picamera2
        print('✓ picamera2 import successful with alternative path')
    except ImportError as e2:
        print(f'✗ picamera2 still failed: {e2}')
        exit(1)

try:
    import yaml
    print('✓ yaml import successful')
except ImportError as e:
    print(f'✗ yaml import failed: {e}')
    exit(1)

print('✓ All critical imports working!')
"

echo ""
echo "=== Fix completed ==="
echo "The solid_dosing_server should now work with system picamera2"
echo "Run: python solid_dosing_server"
