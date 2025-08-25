#!/usr/bin/env python3
"""
Quick LED test - check what LEDs are available and test them
"""

import os
from pathlib import Path

def check_available_leds():
    """Check what LEDs are available on this system"""
    led_dir = Path("/sys/class/leds")
    
    print("🔦 Checking available LEDs...")
    print("=" * 40)
    
    if not led_dir.exists():
        print("❌ No LED directory found (/sys/class/leds)")
        return []
    
    available_leds = []
    for led_path in led_dir.iterdir():
        if led_path.is_dir():
            led_name = led_path.name
            available_leds.append(led_name)
            
            # Try to read current status
            try:
                brightness_file = led_path / "brightness"
                trigger_file = led_path / "trigger"
                
                brightness = "unknown"
                trigger = "unknown"
                
                if brightness_file.exists():
                    with open(brightness_file, 'r') as f:
                        brightness = f.read().strip()
                
                if trigger_file.exists():
                    with open(trigger_file, 'r') as f:
                        trigger_content = f.read().strip()
                        # Extract current trigger (marked with [])
                        for part in trigger_content.split():
                            if part.startswith('[') and part.endswith(']'):
                                trigger = part[1:-1]
                                break
                        if trigger == "unknown":
                            trigger = trigger_content
                
                print(f"💡 {led_name}:")
                print(f"   Brightness: {brightness}")
                print(f"   Trigger: {trigger}")
                
                # Show available triggers
                if trigger_file.exists():
                    with open(trigger_file, 'r') as f:
                        all_triggers = f.read().strip()
                        print(f"   Available triggers: {all_triggers}")
                
                print()
                
            except (OSError, IOError, PermissionError) as e:
                print(f"💡 {led_name}: (Cannot read status - {e})")
    
    if not available_leds:
        print("❌ No LEDs found")
    else:
        print(f"✅ Found {len(available_leds)} LEDs: {', '.join(available_leds)}")
    
    return available_leds

def pi_model_info():
    """Try to determine Pi model"""
    try:
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read().strip('\x00')
        print(f"🍓 Pi Model: {model}")
    except:
        print("🍓 Pi Model: Unknown")

if __name__ == "__main__":
    print("🔍 Pi LED Status Check")
    print("=" * 30)
    
    pi_model_info()
    print()
    
    leds = check_available_leds()
    
    print("\n💡 LED Colors typically:")
    print("   ACT/led0: Green (activity)")
    print("   PWR/led1: Red (power)")
    print("\n🔧 Manual LED control:")
    print("   Turn on:  echo 1 > /sys/class/leds/ACT/brightness")
    print("   Turn off: echo 0 > /sys/class/leds/ACT/brightness")
    print("   Blink:    echo timer > /sys/class/leds/ACT/trigger")
