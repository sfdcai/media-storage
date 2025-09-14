"""
Simple configuration management
"""

import os
import json
from pathlib import Path


class Config:
    """Simple configuration class"""
    
    def __init__(self):
        self.config_file = Path.home() / '.media_sync_config.json'
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from file or create default"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return self.get_default_config()
        else:
            return self.get_default_config()
    
    def get_default_config(self):
        """Get default configuration"""
        return {
            'supabase': {
                'url': '',
                'key': '',
                'table_name': 'media_files'
            },
            'sync': {
                'source_dirs': [],
                'exclude_patterns': ['.DS_Store', 'Thumbs.db', '*.tmp']
            },
            'icloud': {
                'username': '',
                'password': '',
                'download_dir': '',
                'icloudpd_path': 'icloudpd'
            },
            'nas': {
                'mount_path': '',
                'media_folder': 'media'
            },
            'compression': {
                'enabled': True,
                'image_quality': 85,
                'video_quality': 28,
                'compress_before_sync': True
            }
        }
    
    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def setup(self):
        """Interactive setup for configuration"""
        print("=== Media Sync Configuration Setup ===")
        
        # Supabase configuration
        print("\n1. Supabase Configuration:")
        self.config['supabase']['url'] = input("Supabase URL: ").strip()
        self.config['supabase']['key'] = input("Supabase API Key: ").strip()
        
        # Sync directories
        print("\n2. Sync Directories:")
        print("Enter source directories (one per line, empty line to finish):")
        dirs = []
        while True:
            directory = input("Directory: ").strip()
            if not directory:
                break
            if Path(directory).exists():
                dirs.append(directory)
            else:
                print(f"Warning: Directory {directory} does not exist")
        self.config['sync']['source_dirs'] = dirs
        
        # iCloud configuration (optional)
        print("\n3. iCloud Configuration (optional):")
        self.config['icloud']['username'] = input("iCloud username (optional): ").strip()
        self.config['icloud']['download_dir'] = input("iCloud download directory (optional): ").strip()
        
        # NAS configuration (optional)
        print("\n4. NAS Configuration (optional):")
        self.config['nas']['mount_path'] = input("NAS mount path (optional): ").strip()
        self.config['nas']['media_folder'] = input("NAS media folder name (default: media): ").strip() or "media"
        
        # Compression settings
        print("\n5. Compression Settings:")
        compress_enabled = input("Enable compression? (y/n, default: y): ").strip().lower()
        self.config['compression']['enabled'] = compress_enabled != 'n'
        
        self.save_config()
        print(f"\nConfiguration saved to {self.config_file}")
    
    def show(self):
        """Show current configuration"""
        print("=== Current Configuration ===")
        print(f"Config file: {self.config_file}")
        print(f"Supabase URL: {self.config['supabase']['url']}")
        print(f"Supabase Key: {'*' * len(self.config['supabase']['key']) if self.config['supabase']['key'] else 'Not set'}")
        print(f"Source directories: {self.config['sync']['source_dirs']}")
        print(f"iCloud username: {self.config['icloud']['username'] or 'Not set'}")
    
    def get(self, key_path, default=None):
        """Get configuration value using dot notation (e.g., 'supabase.url')"""
        keys = key_path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def set(self, key_path, value):
        """Set configuration value using dot notation"""
        keys = key_path.split('.')
        config = self.config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
