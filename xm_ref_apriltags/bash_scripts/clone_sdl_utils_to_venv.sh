#!/bin/bash
# Clone sdl_utils directly into virtual environment

echo "=== Cloning sdl_utils into ur3_cam_env ==="

# Activate virtual environment
source ur3_cam_env/bin/activate

# Get the site-packages directory
SITE_PACKAGES=$(python3 -c "import site; print(site.getsitepackages()[0])")
echo "Site packages directory: $SITE_PACKAGES"

# Clone sdl_utils directly into site-packages
echo "Cloning sdl_utils into virtual environment..."
cd "$SITE_PACKAGES"

# Remove existing sdl_utils if it exists
if [ -d "sdl_utils" ]; then
    echo "Removing existing sdl_utils..."
    rm -rf sdl_utils
fi

# Clone the repository
echo "Enter the git URL for sdl_utils:"
read -p "Git URL: " SDL_UTILS_URL

git clone "$SDL_UTILS_URL"

# If the cloned directory has a different name, rename it
if [ -d "sdl-utils" ]; then
    mv sdl-utils sdl_utils
    echo "Renamed sdl-utils to sdl_utils"
fi

echo ""
echo "Testing sdl_utils import..."
cd - > /dev/null
python3 -c "
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')

try:
    from sdl_utils import get_logger, send_file_name, receive_file_name
    print('✓ sdl_utils import successful')
    
    # Test logger creation
    logger = get_logger('TestLogger')
    print('✓ Logger creation successful')
    
except ImportError as e:
    print(f'✗ sdl_utils import failed: {e}')
    exit(1)
except Exception as e:
    print(f'✓ sdl_utils imported but error during use: {e}')
"

echo ""
echo "=== sdl_utils installation complete ==="
echo "You can now run: python3 solid_dosing_server"
