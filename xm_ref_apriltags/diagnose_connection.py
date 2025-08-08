#!/usr/bin/env python3
# Quick network diagnostic for Pi camera connection

import socket
import sys
from time import sleep

def test_connection(host, port):
    print(f"Testing connection to {host}:{port}...")
    
    try:
        # Test basic TCP connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)  # 5 second timeout
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ SUCCESS: Can connect to {host}:{port}")
            return True
        else:
            print(f"❌ FAILED: Cannot connect to {host}:{port} (Error code: {result})")
            return False
            
    except socket.gaierror as e:
        print(f"❌ DNS/Host error: {e}")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def ping_test(host):
    import subprocess
    import platform
    
    # Determine ping command based on OS
    ping_cmd = ["ping", "-n", "1"] if platform.system().lower() == "windows" else ["ping", "-c", "1"]
    ping_cmd.append(host)
    
    try:
        result = subprocess.run(ping_cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ PING SUCCESS: {host} is reachable")
            return True
        else:
            print(f"❌ PING FAILED: {host} is not reachable")
            return False
    except Exception as e:
        print(f"❌ PING ERROR: {e}")
        return False

if __name__ == "__main__":
    host = "192.168.1.3"
    port = 2222
    
    print("=== Pi Camera Server Connection Diagnostic ===")
    print()
    
    # Test 1: Ping
    print("1. Testing network reachability...")
    ping_ok = ping_test(host)
    print()
    
    # Test 2: Port connection
    print("2. Testing port connection...")
    port_ok = test_connection(host, port)
    print()
    
    # Results
    print("=== RESULTS ===")
    if ping_ok and port_ok:
        print("✅ All tests passed! The Pi server should be reachable.")
        print("If your client still fails, check:")
        print("  - Is the camera server actually running on the Pi?")
        print("  - Are both devices on the same network?")
    elif ping_ok and not port_ok:
        print("⚠️  Pi is reachable but port 2222 is not responding.")
        print("Check:")
        print("  - Is the camera server running? (python3 solid_dosing_server)")
        print("  - Is there a firewall blocking port 2222?")
        print("  - Is the server bound to the correct IP?")
    elif not ping_ok:
        print("❌ Pi is not reachable on the network.")
        print("Check:")
        print("  - Is the Pi connected to WiFi/Ethernet?")
        print("  - Is the IP address correct? (run 'hostname -I' on Pi)")
        print("  - Are both devices on the same network?")
    
    print()
    print("To fix:")
    print(f"  1. On Pi: python3 solid_dosing_server")
    print(f"  2. Verify Pi IP with: hostname -I")
    print(f"  3. Check server logs for any errors")
