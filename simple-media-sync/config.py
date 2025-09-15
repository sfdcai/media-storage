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
                'strategy': 'balanced',  # 'aggressive', 'balanced', 'conservative', 'custom'
                'compress_images': True,
                'compress_videos': True,
                'image_quality': 85,
                'video_quality': 28,
                'compress_before_sync': True,
                'year_criteria': {
                    'enabled': False,
                    'compress_older_than_years': 2,
                    'aggressive_compression_after_years': 5
                },
                'custom_settings': {
                    'image_formats': ['jpg', 'jpeg', 'png', 'bmp', 'tiff'],
                    'video_formats': ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv'],
                    'max_file_size_mb': 100,  # Only compress files larger than this
                    'min_compression_ratio': 0.1  # Minimum 10% size reduction to keep compressed version
                }
            },
            'pixel_sync': {
                'enabled': False,
                'device_path': '',  # Path to mounted Pixel device
                'sync_folder': 'DCIM',
                'delete_after_sync': False
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
        
        if self.config['compression']['enabled']:
            print("\nCompression Strategy Options:")
            print("1. Aggressive - Maximum compression, lower quality")
            print("2. Balanced - Good compression with reasonable quality (default)")
            print("3. Conservative - Minimal compression, high quality")
            print("4. Custom - Configure your own settings")
            
            strategy_choice = input("Choose compression strategy (1-4, default: 2): ").strip()
            strategies = {'1': 'aggressive', '2': 'balanced', '3': 'conservative', '4': 'custom'}
            self.config['compression']['strategy'] = strategies.get(strategy_choice, 'balanced')
            
            # Configure what to compress
            compress_images = input("Compress images? (y/n, default: y): ").strip().lower()
            self.config['compression']['compress_images'] = compress_images != 'n'
            
            compress_videos = input("Compress videos? (y/n, default: y): ").strip().lower()
            self.config['compression']['compress_videos'] = compress_videos != 'n'
            
            # Year-based criteria
            year_criteria = input("Enable year-based compression criteria? (y/n, default: n): ").strip().lower()
            self.config['compression']['year_criteria']['enabled'] = year_criteria == 'y'
            
            if self.config['compression']['year_criteria']['enabled']:
                older_years = input("Compress files older than how many years? (default: 2): ").strip()
                try:
                    self.config['compression']['year_criteria']['compress_older_than_years'] = int(older_years) if older_years else 2
                except ValueError:
                    self.config['compression']['year_criteria']['compress_older_than_years'] = 2
                
                aggressive_years = input("Use aggressive compression for files older than how many years? (default: 5): ").strip()
                try:
                    self.config['compression']['year_criteria']['aggressive_compression_after_years'] = int(aggressive_years) if aggressive_years else 5
                except ValueError:
                    self.config['compression']['year_criteria']['aggressive_compression_after_years'] = 5
            
            # Custom settings for advanced users
            if self.config['compression']['strategy'] == 'custom':
                print("\nCustom Compression Settings:")
                image_quality = input("Image quality (1-100, default: 85): ").strip()
                try:
                    self.config['compression']['image_quality'] = int(image_quality) if image_quality else 85
                except ValueError:
                    self.config['compression']['image_quality'] = 85
                
                video_quality = input("Video quality/CRF (0-51, lower=better quality, default: 28): ").strip()
                try:
                    self.config['compression']['video_quality'] = int(video_quality) if video_quality else 28
                except ValueError:
                    self.config['compression']['video_quality'] = 28
                
                max_size = input("Only compress files larger than (MB, default: 100): ").strip()
                try:
                    self.config['compression']['custom_settings']['max_file_size_mb'] = int(max_size) if max_size else 100
                except ValueError:
                    self.config['compression']['custom_settings']['max_file_size_mb'] = 100
        
        # Pixel sync configuration
        print("\n6. Google Pixel Sync (optional):")
        pixel_enabled = input("Enable Pixel device sync? (y/n, default: n): ").strip().lower()
        self.config['pixel_sync']['enabled'] = pixel_enabled == 'y'
        
        if self.config['pixel_sync']['enabled']:
            self.config['pixel_sync']['device_path'] = input("Pixel device mount path: ").strip()
            self.config['pixel_sync']['sync_folder'] = input("Sync folder on Pixel (default: DCIM): ").strip() or "DCIM"
            delete_after = input("Delete files from Pixel after sync? (y/n, default: n): ").strip().lower()
            self.config['pixel_sync']['delete_after_sync'] = delete_after == 'y'
        
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
        print(f"NAS mount path: {self.config['nas']['mount_path'] or 'Not set'}")
        
        # Compression settings
        print(f"\nCompression Settings:")
        print(f"  Enabled: {self.config['compression']['enabled']}")
        if self.config['compression']['enabled']:
            print(f"  Strategy: {self.config['compression']['strategy']}")
            print(f"  Compress images: {self.config['compression']['compress_images']}")
            print(f"  Compress videos: {self.config['compression']['compress_videos']}")
            print(f"  Image quality: {self.config['compression']['image_quality']}")
            print(f"  Video quality: {self.config['compression']['video_quality']}")
            if self.config['compression']['year_criteria']['enabled']:
                print(f"  Year criteria: Enabled (>{self.config['compression']['year_criteria']['compress_older_than_years']} years)")
                print(f"  Aggressive after: {self.config['compression']['year_criteria']['aggressive_compression_after_years']} years")
        
        # Pixel sync settings
        print(f"\nPixel Sync Settings:")
        print(f"  Enabled: {self.config['pixel_sync']['enabled']}")
        if self.config['pixel_sync']['enabled']:
            print(f"  Device path: {self.config['pixel_sync']['device_path'] or 'Not set'}")
            print(f"  Sync folder: {self.config['pixel_sync']['sync_folder']}")
            print(f"  Delete after sync: {self.config['pixel_sync']['delete_after_sync']}")
    
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
