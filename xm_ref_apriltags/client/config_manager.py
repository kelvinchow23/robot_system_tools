"""
Configuration manager for UR3 Robot Arm Camera System
Handles loading and validating configuration from YAML file
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any

class CameraConfig:
    """Configuration manager for camera system"""
    
    def __init__(self, config_file: str = "config.yaml"):
        self.script_dir = Path(__file__).resolve().parent
        self.config_file = self.script_dir / config_file
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
                return config
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}")
    
    # Network settings
    @property
    def server_port(self) -> int:
        return self.config['network']['server_port']
    
    @property
    def buffer_size(self) -> int:
        return self.config['network']['buffer_size']
    
    @property
    def chunk_size(self) -> int:
        return self.config['network']['chunk_size']
    
    @property
    def hostname(self) -> str:
        return self.config['network']['hostname']
    
    # Camera settings
    @property
    def focus_mode(self) -> str:
        return self.config['camera']['focus_mode']
    
    @property
    def manual_focus_position(self) -> int:
        return self.config['camera']['manual_focus_position']
    
    @property
    def horizontal_flip(self) -> bool:
        return self.config['camera']['horizontal_flip']
    
    @property
    def vertical_flip(self) -> bool:
        return self.config['camera']['vertical_flip']
    
    @property
    def exposure_settle_time(self) -> int:
        return self.config['camera']['exposure_settle_time']
    
    # File settings
    @property
    def photo_directory(self) -> str:
        return self.config['files']['photo_directory']
    
    @property
    def photo_filename_prefix(self) -> str:
        return self.config['files']['photo_filename_prefix']
    
    # Logging settings
    @property
    def log_level(self) -> str:
        return self.config['logging']['level']
    
    @property
    def log_format(self) -> str:
        return self.config['logging']['format']
    
    # Client settings
    @property
    def download_directory(self) -> str:
        return self.config['client']['download_directory']
    
    @property
    def connection_timeout(self) -> int:
        return self.config['client']['connection_timeout']
    
    def get_logging_level(self) -> int:
        """Convert string log level to logging constant"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR
        }
        return level_map.get(self.log_level.upper(), logging.INFO)
