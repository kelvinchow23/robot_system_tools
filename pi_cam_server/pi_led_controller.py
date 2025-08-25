#!/usr/bin/env python3
"""
Pi LED Controller for Camera Server Status
Control onboard LEDs to indicate camera server status.
"""

import os
import time
from pathlib import Path

class PiLEDController:
    """Control Pi onboard LEDs for status indication"""
    
    def __init__(self):
        self.led_paths = {
            'act': Path('/sys/class/leds/ACT'),           # Activity LED (green)
            'pwr': Path('/sys/class/leds/PWR'),           # Power LED (red) 
            'led0': Path('/sys/class/leds/led0'),         # Alternative names
            'led1': Path('/sys/class/leds/led1'),
        }
        
        # Find available LEDs
        self.available_leds = {}
        for name, path in self.led_paths.items():
            if path.exists():
                self.available_leds[name] = path
                
        # Common LED mappings
        self.status_led = None  # Green activity LED
        self.error_led = None   # Red power LED
        
        self._setup_leds()
    
    def _setup_leds(self):
        """Setup LED mappings based on available LEDs"""
        # Try to find activity (green) LED
        if 'ACT' in self.available_leds:
            self.status_led = 'ACT'
        elif 'act' in self.available_leds:
            self.status_led = 'act'
        elif 'led0' in self.available_leds:
            self.status_led = 'led0'
            
        # For error indication, try to use a different LED
        # Pi Zero 2W might not have a separate red LED
        if 'PWR' in self.available_leds:
            self.error_led = 'PWR'
        elif 'pwr' in self.available_leds:
            self.error_led = 'pwr'
        elif 'led1' in self.available_leds:
            self.error_led = 'led1'
        elif 'mmc0' in self.available_leds:
            self.error_led = 'mmc0'  # Use SD card LED for error indication
        elif 'default-on' in self.available_leds:
            self.error_led = 'default-on'  # Use power LED for error indication
    
    def _write_led(self, led_name, value):
        """Write value to LED control file"""
        if led_name not in self.available_leds:
            return False
            
        try:
            trigger_path = self.available_leds[led_name] / 'trigger'
            brightness_path = self.available_leds[led_name] / 'brightness'
            
            # Set trigger to 'none' for manual control
            with open(trigger_path, 'w') as f:
                f.write('none')
            
            # Set brightness (0=off, 1=on for binary LEDs)
            with open(brightness_path, 'w') as f:
                f.write(str(value))
            
            return True
        except (OSError, IOError, PermissionError):
            return False
    
    def set_status_led(self, state):
        """
        Set status LED (green activity LED)
        
        Args:
            state: 'on', 'off', or 'blink'
        """
        if not self.status_led:
            return False
            
        if state == 'on':
            return self._write_led(self.status_led, 1)
        elif state == 'off':
            return self._write_led(self.status_led, 0)
        elif state == 'blink':
            # Set to heartbeat trigger for blinking
            try:
                trigger_path = self.available_leds[self.status_led] / 'trigger'
                with open(trigger_path, 'w') as f:
                    f.write('heartbeat')
                return True
            except (OSError, IOError, PermissionError):
                return False
        
        return False
    
    def set_error_led(self, state):
        """
        Set error LED (red power LED)
        
        Args:
            state: 'on', 'off', or 'blink'
        """
        if not self.error_led:
            return False
            
        if state == 'on':
            return self._write_led(self.error_led, 1)
        elif state == 'off':
            return self._write_led(self.error_led, 0)
        elif state == 'blink':
            # Set to timer trigger for blinking
            try:
                trigger_path = self.available_leds[self.error_led] / 'trigger'
                with open(trigger_path, 'w') as f:
                    f.write('timer')
                return True
            except (OSError, IOError, PermissionError):
                return False
        
        return False
    
    def indicate_server_starting(self):
        """LED pattern for server starting"""
        print("💡 LED: Server starting (blinking green)")
        self.set_status_led('blink')
        self.set_error_led('off')
    
    def indicate_server_running(self):
        """LED pattern for server running normally"""
        print("💡 LED: Server running (steady green)")
        self.set_status_led('on')
        self.set_error_led('off')
    
    def indicate_server_error(self):
        """LED pattern for server error"""
        print("💡 LED: Server error (blinking red)")
        self.set_status_led('off')
        self.set_error_led('blink')
    
    def indicate_camera_capture(self):
        """Brief LED indication during photo capture"""
        print("💡 LED: Camera capture (flash)")
        # Quick flash pattern
        self.set_status_led('off')
        time.sleep(0.1)
        self.set_status_led('on')
    
    def restore_default(self):
        """Restore LEDs to default system behavior"""
        print("💡 LED: Restoring default behavior")
        for led_name in self.available_leds:
            try:
                trigger_path = self.available_leds[led_name] / 'trigger'
                with open(trigger_path, 'w') as f:
                    # Restore appropriate default triggers based on LED name
                    if led_name in ['ACT', 'act', 'led0']:
                        f.write('actpwr')  # Pi Zero 2W uses actpwr for activity
                    elif led_name in ['PWR', 'pwr', 'led1']:
                        f.write('input')  # Default power trigger
                    elif led_name == 'mmc0':
                        f.write('mmc0')  # SD card activity
                    elif led_name == 'default-on':
                        f.write('default-on')  # Always on power indicator
                    else:
                        f.write('none')  # Safe default
            except (OSError, IOError, PermissionError):
                pass
    
    def get_status(self):
        """Get current LED status"""
        status = {
            'available_leds': list(self.available_leds.keys()),
            'status_led': self.status_led,
            'error_led': self.error_led,
        }
        
        for led_name in self.available_leds:
            try:
                brightness_path = self.available_leds[led_name] / 'brightness'
                trigger_path = self.available_leds[led_name] / 'trigger'
                
                with open(brightness_path, 'r') as f:
                    brightness = f.read().strip()
                
                with open(trigger_path, 'r') as f:
                    trigger = f.read().strip()
                
                status[f'{led_name}_brightness'] = brightness
                status[f'{led_name}_trigger'] = trigger
                
            except (OSError, IOError, PermissionError):
                status[f'{led_name}_brightness'] = 'unknown'
                status[f'{led_name}_trigger'] = 'unknown'
        
        return status

def main():
    """Test LED controller"""
    print("🔦 Pi LED Controller Test")
    print("=" * 30)
    
    controller = PiLEDController()
    status = controller.get_status()
    
    print("Available LEDs:")
    for led in status['available_leds']:
        brightness = status.get(f'{led}_brightness', 'unknown')
        trigger = status.get(f'{led}_trigger', 'unknown')
        print(f"  {led}: brightness={brightness}, trigger={trigger}")
    
    print(f"\nStatus LED: {status['status_led']}")
    print(f"Error LED: {status['error_led']}")
    
    if not status['available_leds']:
        print("❌ No controllable LEDs found")
        return
    
    print("\n🧪 Testing LED patterns...")
    
    try:
        print("Server starting...")
        controller.indicate_server_starting()
        time.sleep(3)
        
        print("Server running...")
        controller.indicate_server_running()
        time.sleep(2)
        
        print("Camera capture...")
        controller.indicate_camera_capture()
        time.sleep(1)
        
        print("Server error...")
        controller.indicate_server_error()
        time.sleep(3)
        
        print("Restoring defaults...")
        controller.restore_default()
        
    except KeyboardInterrupt:
        print("\nRestoring defaults...")
        controller.restore_default()

if __name__ == "__main__":
    main()
