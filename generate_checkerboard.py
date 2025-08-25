#!/usr/bin/env python3
"""
Generate Checkerboard Pattern for Camera Calibration

This script generates a checkerboard pattern that can be printed
and used for camera calibration.
"""

import cv2
import numpy as np
import argparse
from pathlib import Path

def generate_checkerboard(width, height, square_size_pixels=50, filename="checkerboard.png"):
    """
    Generate a checkerboard pattern for camera calibration
    
    Args:
        width: Number of squares horizontally
        height: Number of squares vertically  
        square_size_pixels: Size of each square in pixels
        filename: Output filename
    """
    
    # Calculate image dimensions
    img_width = width * square_size_pixels
    img_height = height * square_size_pixels
    
    # Create checkerboard pattern
    checkerboard = np.zeros((img_height, img_width), dtype=np.uint8)
    
    for i in range(height):
        for j in range(width):
            if (i + j) % 2 == 0:
                y_start = i * square_size_pixels
                y_end = (i + 1) * square_size_pixels
                x_start = j * square_size_pixels
                x_end = (j + 1) * square_size_pixels
                checkerboard[y_start:y_end, x_start:x_end] = 255
    
    # Add border
    border_size = square_size_pixels // 2
    bordered = cv2.copyMakeBorder(checkerboard, border_size, border_size, 
                                border_size, border_size, cv2.BORDER_CONSTANT, 
                                value=255)
    
    # Save pattern
    cv2.imwrite(filename, bordered)
    
    # Calculate real-world dimensions for printing
    # Assume 96 DPI for screen display / 300 DPI for printing
    dpi_screen = 96
    dpi_print = 300
    
    total_width_pixels = bordered.shape[1]
    total_height_pixels = bordered.shape[0]
    
    width_inches_screen = total_width_pixels / dpi_screen
    height_inches_screen = total_height_pixels / dpi_screen
    
    width_inches_print = total_width_pixels / dpi_print
    height_inches_print = total_height_pixels / dpi_print
    
    print(f"✅ Checkerboard pattern generated: {filename}")
    print(f"   Pattern: {width}x{height} squares")
    print(f"   Internal corners: {width-1}x{height-1}")
    print(f"   Image size: {total_width_pixels}x{total_height_pixels} pixels")
    print("")
    print("📏 Print sizes:")
    print(f"   For screen (96 DPI): {width_inches_screen:.1f} x {height_inches_screen:.1f} inches")
    print(f"   For printing (300 DPI): {width_inches_print:.1f} x {height_inches_print:.1f} inches")
    print("")
    print("📋 Calibration usage:")
    print(f"   Use checkerboard size: {width-1} {height-1}")
    print(f"   Measure actual square size after printing")
    print("")
    print("💡 Tips:")
    print("   - Print on flat, rigid surface (mount on cardboard)")
    print("   - Ensure squares are perfectly square after printing")
    print("   - Measure actual square size with ruler")
    print("   - Good lighting is essential for detection")

def main():
    parser = argparse.ArgumentParser(description='Generate Checkerboard Pattern for Calibration')
    parser.add_argument('--width', type=int, default=10,
                       help='Number of squares horizontally (default: 10)')
    parser.add_argument('--height', type=int, default=7,
                       help='Number of squares vertically (default: 7)')
    parser.add_argument('--square-size', type=int, default=50,
                       help='Square size in pixels (default: 50)')
    parser.add_argument('--output', default='checkerboard_pattern.png',
                       help='Output filename (default: checkerboard_pattern.png)')
    
    args = parser.parse_args()
    
    print("🏁 Checkerboard Pattern Generator")
    print("=" * 50)
    
    generate_checkerboard(args.width, args.height, args.square_size, args.output)

if __name__ == "__main__":
    main()
