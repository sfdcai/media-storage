#!/usr/bin/env python3
"""
Centralized Configuration Management
Handles all configuration loading, validation, and environment variable management
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration"""
    file_path: str = "media.db"
    backup_enabled: bool = True
    backup_interval_hours: int = 24

@dataclass
class ICloudConfig:
    """iCloud configuration"""
    username: str = ""
    password: str = ""
    directory: str = "/mnt/wd_all_pictures/incoming"
    days: int = 0
    recent: int = 0
    auto_delete: bool = False
    album_name: str = "DeletePending"

@dataclass
class SyncthingConfig:
    """Syncthing configuration"""
    api_key: str = ""
    base_url: str = "http://localhost:8384/rest"
    folder_id: str = "default"
    pixel_local_folder: str = "/storage/emulated/0/DCIM/Syncthing"
    delete_local_pixel: bool = True
    timeout_seconds: int = 30
    max_retries: int = 3

@dataclass
class NASConfig:
    """NAS configuration"""
    mount_path: str = "/mnt/nas_backup"
    sync_enabled: bool = True
    delete_after_sync: bool = False

@dataclass
class CompressionConfig:
    """Compression configuration"""
    enabled: bool = True
    light_quality: int = 85  # < 1 year
    medium_quality: int = 75  # 1-3 years
    heavy_quality: int = 65  # > 3 years
    light_crf: int = 26  # Video CRF for < 1 year
    medium_crf: int = 28  # Video CRF for 1-3 years
    heavy_crf: int = 30  # Video CRF for > 3 years

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    log_dir: str = "logs"
    log_file: str = "media_pipeline.log"
    max_file_size_mb: int = 10
    backup_count: int = 5
    format: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

@dataclass
class DirectoryConfig:
    """Directory structure configuration"""
    incoming: str = "/mnt/wd_all_pictures/incoming"
    backup: str = "/mnt/wd_all_pictures/backup"
    compress: str = "/mnt/wd_all_pictures/compress"
    delete_pending: str = "/mnt/wd_all_pictures/delete_pending"
    processed: str = "/mnt/wd_all_pictures/processed"

class ConfigManager:
    """Centralized configuration manager"""
    
    def __init__(self, config_file: str = "config.yaml"):
        self.config_file = config_file
        self._config_data: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file and environment variables"""
        # Load from YAML file if it exists
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self._config_data = yaml.safe_load(f) or {}
                logger.info(f"Loaded configuration from {self.config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file {self.config_file}: {e}")
                self._config_data = {}
        
        # Override with environment variables
        self._load_env_overrides()
    
    def _load_env_overrides(self):
        """Load configuration overrides from environment variables"""
        env_mappings = {
            'ICLOUD_USERNAME': ['icloud', 'username'],
            'ICLOUD_PASSWORD': ['icloud', 'password'],
            'ICLOUD_DIRECTORY': ['icloud', 'directory'],
            'SYNCTHING_API_KEY': ['syncthing', 'api_key'],
            'SYNCTHING_BASE_URL': ['syncthing', 'base_url'],
            'SYNCTHING_FOLDER_ID': ['syncthing', 'folder_id'],
            'DB_FILE': ['database', 'file_path'],
            'LOG_LEVEL': ['logging', 'level'],
            'LOG_DIR': ['logging', 'log_dir'],
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                self._set_nested_config(config_path, value)
    
    def _set_nested_config(self, path: list, value: str):
        """Set nested configuration value"""
        current = self._config_data
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value
    
    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration"""
        db_config = self._config_data.get('database', {})
        return DatabaseConfig(
            file_path=db_config.get('file_path', 'media.db'),
            backup_enabled=db_config.get('backup_enabled', True),
            backup_interval_hours=db_config.get('backup_interval_hours', 24)
        )
    
    def get_icloud_config(self) -> ICloudConfig:
        """Get iCloud configuration"""
        icloud_config = self._config_data.get('icloud', {})
        return ICloudConfig(
            username=icloud_config.get('username', ''),
            password=icloud_config.get('password', ''),
            directory=icloud_config.get('directory', '/mnt/wd_all_pictures/incoming'),
            days=icloud_config.get('days', 0),
            recent=icloud_config.get('recent', 0),
            auto_delete=icloud_config.get('auto_delete', False),
            album_name=icloud_config.get('album_name', 'DeletePending')
        )
    
    def get_syncthing_config(self) -> SyncthingConfig:
        """Get Syncthing configuration"""
        syncthing_config = self._config_data.get('syncthing', {})
        return SyncthingConfig(
            api_key=syncthing_config.get('api_key', ''),
            base_url=syncthing_config.get('base_url', 'http://localhost:8384/rest'),
            folder_id=syncthing_config.get('folder_id', 'default'),
            pixel_local_folder=syncthing_config.get('pixel_local_folder', '/storage/emulated/0/DCIM/Syncthing'),
            delete_local_pixel=syncthing_config.get('delete_local_pixel', True),
            timeout_seconds=syncthing_config.get('timeout_seconds', 30),
            max_retries=syncthing_config.get('max_retries', 3)
        )
    
    def get_nas_config(self) -> NASConfig:
        """Get NAS configuration"""
        nas_config = self._config_data.get('nas', {})
        return NASConfig(
            mount_path=nas_config.get('mount_path', '/mnt/nas_backup'),
            sync_enabled=nas_config.get('sync_enabled', True),
            delete_after_sync=nas_config.get('delete_after_sync', False)
        )
    
    def get_compression_config(self) -> CompressionConfig:
        """Get compression configuration"""
        compression_config = self._config_data.get('compression', {})
        return CompressionConfig(
            enabled=compression_config.get('enabled', True),
            light_quality=compression_config.get('light_quality', 85),
            medium_quality=compression_config.get('medium_quality', 75),
            heavy_quality=compression_config.get('heavy_quality', 65),
            light_crf=compression_config.get('light_crf', 26),
            medium_crf=compression_config.get('medium_crf', 28),
            heavy_crf=compression_config.get('heavy_crf', 30)
        )
    
    def get_logging_config(self) -> LoggingConfig:
        """Get logging configuration"""
        logging_config = self._config_data.get('logging', {})
        return LoggingConfig(
            level=logging_config.get('level', 'INFO'),
            log_dir=logging_config.get('log_dir', 'logs'),
            log_file=logging_config.get('log_file', 'media_pipeline.log'),
            max_file_size_mb=logging_config.get('max_file_size_mb', 10),
            backup_count=logging_config.get('backup_count', 5),
            format=logging_config.get('format', "%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
    
    def get_directory_config(self) -> DirectoryConfig:
        """Get directory configuration"""
        dir_config = self._config_data.get('directories', {})
        return DirectoryConfig(
            incoming=dir_config.get('incoming', '/mnt/wd_all_pictures/incoming'),
            backup=dir_config.get('backup', '/mnt/wd_all_pictures/backup'),
            compress=dir_config.get('compress', '/mnt/wd_all_pictures/compress'),
            delete_pending=dir_config.get('delete_pending', '/mnt/wd_all_pictures/delete_pending'),
            processed=dir_config.get('processed', '/mnt/wd_all_pictures/processed')
        )
    
    def validate_config(self) -> bool:
        """Validate configuration and create necessary directories"""
        try:
            # Create log directory
            log_config = self.get_logging_config()
            os.makedirs(log_config.log_dir, exist_ok=True)
            
            # Create media directories
            dir_config = self.get_directory_config()
            for attr_name in ['incoming', 'backup', 'compress', 'delete_pending', 'processed']:
                dir_path = getattr(dir_config, attr_name)
                os.makedirs(dir_path, exist_ok=True)
            
            # Validate required configurations
            icloud_config = self.get_icloud_config()
            if not icloud_config.username:
                logger.warning("iCloud username not configured")
            
            syncthing_config = self.get_syncthing_config()
            if not syncthing_config.api_key:
                logger.warning("Syncthing API key not configured")
            
            return True
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False

# Global config instance
config_manager = ConfigManager()
