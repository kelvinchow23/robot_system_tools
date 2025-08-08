#!/usr/bin/env python3
"""
Camera Focus Calibration Script
This script helps you find the optimal LensPosition value for your camera setup.
"""

import time
from picamera2 import Picamera2, controls
from libcamera import Transform

def test_focus_values():
    """Test different focus values and save images for comparison"""
    
    cam = Picamera2(0)
    config = cam.create_still_configuration(transform=Transform(hflip=1, vflip=1))
    cam.configure(config)
    
    # Test different focus values
    focus_values = [100, 200, 300, 400, 500, 600, 800, 1000]
    
    print("Testing different focus values...")
    print("Place an AprilTag or object at your typical working distance")
    print("Press Enter to start testing...")
    input()
    
    for focus_val in focus_values:
        print(f"Testing LensPosition: {focus_val}")
        
        # Set focus
        if 'AfMode' in cam.camera_controls:
            cam.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": focus_val})
        
        # Start camera if not already started
        if not cam.started:
            cam.start()
        
        # Wait for camera to adjust
        time.sleep(2)
        
        # Capture image
        filename = f"focus_test_{focus_val}.jpg"
        cam.capture_file(filename)
        print(f"Saved: {filename}")
        
        # Small delay between captures
        time.sleep(1)
    
    cam.stop()
    print("\nFocus test complete!")
    print("Review the images and find which LensPosition value gives the sharpest image.")
    print("Then update that value in your solid_dosing_server script.")

if __name__ == "__main__":
    test_focus_values()
