#!/usr/bin/env python3
"""
Configuration System Test
Demonstrates the unified configuration system usage
"""

from config_manager import (
    config,
    get_robot_ip,
    get_robot_speed, 
    get_camera_host,
    get_camera_port,
    get_apriltag_family,
    get_apriltag_size,
    get_camera_calibration_file,
    get_photos_directory
)

def test_basic_access():
    """Test basic configuration access"""
    print("🔧 Testing Basic Configuration Access")
    print("-" * 40)
    
    # Test dot notation access
    robot_ip = config.get('robot.ip_address')
    camera_host = config.get('camera.server.host')
    tag_size = config.get('apriltag.tag_size')
    
    print(f"Robot IP (dot notation): {robot_ip}")
    print(f"Camera Host (dot notation): {camera_host}")
    print(f"Tag Size (dot notation): {tag_size}")
    
    # Test with defaults
    unknown_setting = config.get('unknown.setting', 'default_value')
    print(f"Unknown setting with default: {unknown_setting}")

def test_convenience_functions():
    """Test convenience functions"""
    print("\n🎯 Testing Convenience Functions")
    print("-" * 40)
    
    print(f"Robot IP: {get_robot_ip()}")
    print(f"Robot Speed: {get_robot_speed()}")
    print(f"Camera Host: {get_camera_host()}")
    print(f"Camera Port: {get_camera_port()}")
    print(f"AprilTag Family: {get_apriltag_family()}")
    print(f"AprilTag Size: {get_apriltag_size()}")

def test_path_resolution():
    """Test path resolution"""
    print("\n📁 Testing Path Resolution")
    print("-" * 40)
    
    calib_file = get_camera_calibration_file()
    photos_dir = get_photos_directory()
    
    print(f"Calibration File: {calib_file}")
    print(f"Photos Directory: {photos_dir}")
    print(f"Calibration File Exists: {calib_file.exists()}")
    print(f"Photos Directory Exists: {photos_dir.exists()}")
    
    # Test custom path resolution
    custom_path = config.resolve_path('documentation/CONFIGURATION_GUIDE.md')
    print(f"Custom Path: {custom_path}")
    print(f"Custom Path Exists: {custom_path.exists()}")

def test_section_access():
    """Test section access"""
    print("\n📋 Testing Section Access")
    print("-" * 40)
    
    robot_section = config.get_section('robot')
    camera_section = config.get_section('camera')
    
    print("Robot Section Keys:", list(robot_section.keys()))
    print("Camera Section Keys:", list(camera_section.keys()))
    
    # Test nested access
    server_config = config.get_section('camera')['server']
    print("Camera Server Config:", server_config)

def test_environment_override():
    """Test environment and override scenarios"""
    print("\n🔄 Testing Override Scenarios")
    print("-" * 40)
    
    # Simulate what modules would do with overrides
    default_ip = config.get('robot.ip_address')
    override_ip = '192.168.1.50'
    
    # What a module constructor would do
    actual_ip = override_ip or default_ip
    print(f"Default IP from config: {default_ip}")
    print(f"Override IP: {override_ip}")
    print(f"Actual IP used: {actual_ip}")
    
    # Test missing config with default
    missing_value = config.get('nonexistent.key', 'fallback')
    print(f"Missing config with fallback: {missing_value}")

def main():
    """Run all configuration tests"""
    print("🧪 Robot System Tools - Configuration Test")
    print("=" * 60)
    
    # Show config file location
    config_path = config.get_config_path()
    print(f"📍 Configuration loaded from: {config_path}")
    print(f"📍 Project root: {config.find_project_root()}")
    print()
    
    # Run tests
    test_basic_access()
    test_convenience_functions() 
    test_path_resolution()
    test_section_access()
    test_environment_override()
    
    print("\n✅ Configuration system test completed!")
    print("\n💡 Usage examples:")
    print("   from config_manager import config, get_robot_ip")
    print("   robot_ip = get_robot_ip()")
    print("   speed = config.get('robot.default_speed')")

if __name__ == "__main__":
    main()