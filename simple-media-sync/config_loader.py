"""
Simple configuration loader for JSON config file
"""

import json
from pathlib import Path


class Config:
    """Simple configuration class for JSON config"""
    
    def __init__(self, config_file='config.json'):
        self.config_file = Path(config_file)
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from JSON file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                return self.get_default_config()
        else:
            return self.get_default_config()
    
    def get_default_config(self):
        """Get default configuration"""
        return {
            "supabase": {"url": "", "key": "", "table_name": "media_files"},
            "icloud": {"username": "", "password": "", "download_dir": ""},
            "workflow": {
                "incoming_folder": "./incoming",
                "pixel_sync_folder": "./pixel_sync",
                "nas_archive_folder": "./nas_archive",
                "processing_folder": "./processing",
                "icloud_delete_folder": "./icloud_delete",
                "pixel_batch_size": 5
            },
            "syncthing": {
                "api_url": "http://localhost:8384",
                "api_key": "",
                "pixel_folder_id": ""
            },
            "compression": {"enabled": True, "strategy": "balanced"}
        }
    
    def get(self, key_path, default=None):
        """Get configuration value using dot notation"""
        keys = key_path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def save(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def show(self):
        """Show current configuration"""
        print("=== Current Configuration ===")
        print(f"Config file: {self.config_file}")
        print(json.dumps(self.config, indent=2))
