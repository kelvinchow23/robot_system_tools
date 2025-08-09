#!/usr/bin/env python3
"""
Pi Camera Server - Standalone Application
Minimal camera server for Raspberry Pi deployment
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add parent src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from camera.core import CameraServer, CameraConfig
except ImportError:
    print("❌ Cannot import camera module")
    print("   Make sure you're running from the correct directory")
    print("   Expected structure: pi_cam_server/ with ../src/camera/")
    sys.exit(1)

def setup_logging(log_level: str = "INFO"):
    """Setup logging for Pi deployment"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "camera_server.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_config() -> CameraConfig:
    """Load configuration for Pi server"""
    config_paths = [
        "camera_config.yaml",
        "../camera_config.yaml",
        "/etc/camera_server/config.yaml"
    ]
    
    for config_path in config_paths:
        if os.path.exists(config_path):
            print(f"📝 Loading config from: {config_path}")
            return CameraConfig.from_yaml(config_path)
    
    print("📝 Using default configuration")
    return CameraConfig()

def main():
    """Main Pi camera server application"""
    parser = argparse.ArgumentParser(description="Pi Camera Server for Robot System")
    parser.add_argument("--port", type=int, default=2222, help="Server port")
    parser.add_argument("--log-level", default="INFO", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Logging level")
    parser.add_argument("--daemon", action="store_true", 
                       help="Run as daemon (systemd service)")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        config = load_config()
        if args.port != 2222:
            config.server_port = args.port
        
        # Create and start server
        server = CameraServer(config)
        
        if not args.daemon:
            print("🎥 Pi Camera Server Starting")
            print("=" * 40)
            print(f"📡 Port: {config.server_port}")
            print(f"📁 Photos: {config.photo_directory}")
            print(f"🔧 Focus: {config.focus_mode}")
            print("📸 Ready to serve camera captures")
            print("Press Ctrl+C to stop")
            print()
        
        logger.info(f"Starting camera server on port {config.server_port}")
        server.start_server()
        
    except KeyboardInterrupt:
        if not args.daemon:
            print("\n👋 Camera server stopped by user")
        logger.info("Camera server stopped by user")
    except Exception as e:
        error_msg = f"Camera server error: {e}"
        if not args.daemon:
            print(f"❌ {error_msg}")
        logger.error(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
