#!/bin/bash
# Quick diagnostic for picamera2 installation

echo "=== Pi Camera Diagnostic ==="
echo "Current user: $(whoami)"
echo "Python version: $(python3 --version)"
echo "Virtual env: $VIRTUAL_ENV"
echo ""

echo "=== Checking system packages ==="
dpkg -l | grep -E "(picamera|libcamera)" | head -10

echo ""
echo "=== Checking file system ==="
echo "Checking /usr/lib/python3*/dist-packages for picamera2..."
find /usr/lib -name "*picamera*" 2>/dev/null | head -10

echo ""
echo "=== Python import test ==="
python3 -c "
import sys
print('Python executable:', sys.executable)
print('Python path:')
for i, p in enumerate(sys.path):
    print(f'  {i}: {p}')

print()
print('Testing imports without sys.path modification:')
try:
    import picamera2
    print('✓ picamera2 found naturally')
except ImportError:
    print('✗ picamera2 not found naturally')

print()
print('Adding system paths and testing:')
sys.path.insert(0, '/usr/lib/python3/dist-packages')
sys.path.insert(0, '/usr/lib/python3.11/dist-packages')

try:
    import picamera2
    print('✓ picamera2 found with system paths')
    print('  picamera2 location:', picamera2.__file__)
except ImportError as e:
    print('✗ picamera2 still not found:', e)
"

echo ""
echo "=== Alternative: Install via pip with system site packages ==="
echo "If system package doesn't work, we can try:"
echo "  python3 -m venv --system-site-packages ur3_cam_env_new"
