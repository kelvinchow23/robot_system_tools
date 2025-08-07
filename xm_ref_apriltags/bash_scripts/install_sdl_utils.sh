#!/bin/bash
# Install sdl_utils in virtual environment

echo "=== Installing sdl_utils in ur3_cam_env ==="

# Activate virtual environment
source ur3_cam_env/bin/activate

echo "Current directory: $(pwd)"
echo "Looking for sdl_utils..."

# Find sdl_utils directory
SDL_UTILS_PATH=""
if [ -d "sdl_utils" ]; then
    SDL_UTILS_PATH="./sdl_utils"
elif [ -d "../sdl_utils" ]; then
    SDL_UTILS_PATH="../sdl_utils"
elif [ -d "$HOME/sdl_utils" ]; then
    SDL_UTILS_PATH="$HOME/sdl_utils"
else
    echo "Please specify where you cloned sdl_utils:"
    read -p "Enter full path to sdl_utils directory: " SDL_UTILS_PATH
fi

echo "Using sdl_utils at: $SDL_UTILS_PATH"

if [ -d "$SDL_UTILS_PATH" ]; then
    echo "Installing sdl_utils in development mode..."
    cd "$SDL_UTILS_PATH"
    
    # Check if setup.py exists
    if [ -f "setup.py" ]; then
        pip install -e .
        echo "✓ Installed sdl_utils via setup.py"
    else
        # If no setup.py, create a symbolic link
        echo "No setup.py found, creating symbolic link..."
        cd - > /dev/null
        ln -sf "$SDL_UTILS_PATH" ur3_cam_env/lib/python3.11/site-packages/sdl_utils
        echo "✓ Created symbolic link to sdl_utils"
    fi
    
    cd - > /dev/null
else
    echo "✗ sdl_utils directory not found at: $SDL_UTILS_PATH"
    echo "Please ensure you've cloned sdl_utils and specify the correct path"
    exit 1
fi

echo ""
echo "Testing sdl_utils import..."
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
