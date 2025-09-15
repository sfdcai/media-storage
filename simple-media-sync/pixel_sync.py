"""
Google Pixel device synchronization utilities
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional


class PixelSync:
    """Handle synchronization with Google Pixel devices"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.pixel_enabled = config.get('pixel_sync.enabled', False)
        self.pixel_device_path = config.get('pixel_sync.device_path', '')
        self.pixel_sync_folder = config.get('pixel_sync.sync_folder', 'DCIM')
        self.delete_after_sync = config.get('pixel_sync.delete_after_sync', False)
    
    def sync_to_pixel(self, file_path: str, dry_run: bool = False) -> bool:
        """Sync file to Pixel device"""
        if not self.pixel_enabled:
            self.logger.debug("Pixel sync is disabled")
            return True  # Not an error, just skipped
        
        if not self.pixel_device_path:
            self.logger.error("Pixel device path not configured")
            return False
        
        if not Path(self.pixel_device_path).exists():
            self.logger.error(f"Pixel device path does not exist: {self.pixel_device_path}")
            return False
        
        source_path = Path(file_path)
        if not source_path.exists():
            self.logger.error(f"Source file does not exist: {file_path}")
            return False
        
        # Create destination path on Pixel device
        pixel_dest = Path(self.pixel_device_path) / self.pixel_sync_folder / source_path.name
        
        if dry_run:
            self.logger.info(f"[DRY RUN] Would copy {file_path} to {pixel_dest}")
            return True
        
        try:
            # Ensure destination directory exists
            pixel_dest.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file to Pixel device
            shutil.copy2(file_path, pixel_dest)
            
            # Verify copy was successful
            if pixel_dest.exists() and pixel_dest.stat().st_size == source_path.stat().st_size:
                self.logger.info(f"Successfully synced to Pixel: {source_path.name}")
                
                # Delete from Pixel if configured
                if self.delete_after_sync:
                    self.logger.info(f"Deleting from Pixel after sync: {source_path.name}")
                    pixel_dest.unlink()
                
                return True
            else:
                self.logger.error(f"Pixel sync verification failed: {source_path.name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to sync to Pixel: {e}")
            return False
    
    def get_pixel_files(self) -> List[str]:
        """Get list of files on Pixel device"""
        if not self.pixel_enabled or not self.pixel_device_path:
            return []
        
        pixel_path = Path(self.pixel_device_path) / self.pixel_sync_folder
        if not pixel_path.exists():
            return []
        
        files = []
        for file_path in pixel_path.rglob('*'):
            if file_path.is_file():
                files.append(str(file_path))
        
        return files
    
    def is_file_on_pixel(self, filename: str) -> bool:
        """Check if file exists on Pixel device"""
        if not self.pixel_enabled or not self.pixel_device_path:
            return False
        
        pixel_path = Path(self.pixel_device_path) / self.pixel_sync_folder / filename
        return pixel_path.exists()
    
    def get_pixel_usage(self) -> dict:
        """Get Pixel device storage usage statistics"""
        if not self.pixel_enabled or not self.pixel_device_path:
            return {'total_files': 0, 'total_size': 0}
        
        pixel_path = Path(self.pixel_device_path) / self.pixel_sync_folder
        if not pixel_path.exists():
            return {'total_files': 0, 'total_size': 0}
        
        total_files = 0
        total_size = 0
        
        for file_path in pixel_path.rglob('*'):
            if file_path.is_file():
                total_files += 1
                total_size += file_path.stat().st_size
        
        return {
            'total_files': total_files,
            'total_size': total_size,
            'total_size_mb': total_size / (1024 * 1024)
        }
    
    def test_pixel_connection(self) -> bool:
        """Test Pixel device connection"""
        if not self.pixel_enabled:
            return False
        
        if not self.pixel_device_path:
            return False
        
        try:
            pixel_path = Path(self.pixel_device_path)
            if not pixel_path.exists():
                return False
            
            # Try to access the sync folder
            sync_path = pixel_path / self.pixel_sync_folder
            sync_path.mkdir(parents=True, exist_ok=True)
            
            # Test write access
            test_file = sync_path / '.test_write'
            test_file.write_text('test')
            test_file.unlink()
            
            return True
        except Exception:
            return False
    
    def get_pixel_status(self) -> dict:
        """Get Pixel device status"""
        return {
            'enabled': self.pixel_enabled,
            'device_path_configured': bool(self.pixel_device_path),
            'device_path_exists': Path(self.pixel_device_path).exists() if self.pixel_device_path else False,
            'connection_ok': self.test_pixel_connection(),
            'delete_after_sync': self.delete_after_sync
        }
