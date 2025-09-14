"""
NAS synchronization utilities
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional


class NASSync:
    """Handle synchronization with NAS storage"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.nas_mount_path = config.get('nas.mount_path', '')
        self.nas_media_folder = config.get('nas.media_folder', 'media')
    
    def sync_to_nas(self, file_path: str, dry_run: bool = False) -> bool:
        """Sync file to NAS"""
        if not self.nas_mount_path:
            self.logger.error("NAS mount path not configured")
            return False
        
        if not Path(self.nas_mount_path).exists():
            self.logger.error(f"NAS mount path does not exist: {self.nas_mount_path}")
            return False
        
        source_path = Path(file_path)
        if not source_path.exists():
            self.logger.error(f"Source file does not exist: {file_path}")
            return False
        
        # Create destination path on NAS
        nas_dest = Path(self.nas_mount_path) / self.nas_media_folder / source_path.name
        
        if dry_run:
            self.logger.info(f"[DRY RUN] Would copy {file_path} to {nas_dest}")
            return True
        
        try:
            # Ensure destination directory exists
            nas_dest.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file to NAS
            shutil.copy2(file_path, nas_dest)
            
            # Verify copy was successful
            if nas_dest.exists() and nas_dest.stat().st_size == source_path.stat().st_size:
                self.logger.info(f"Successfully synced to NAS: {source_path.name}")
                return True
            else:
                self.logger.error(f"NAS sync verification failed: {source_path.name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to sync to NAS: {e}")
            return False
    
    def get_nas_files(self) -> List[str]:
        """Get list of files on NAS"""
        if not self.nas_mount_path:
            return []
        
        nas_path = Path(self.nas_mount_path) / self.nas_media_folder
        if not nas_path.exists():
            return []
        
        files = []
        for file_path in nas_path.rglob('*'):
            if file_path.is_file():
                files.append(str(file_path))
        
        return files
    
    def is_file_on_nas(self, filename: str) -> bool:
        """Check if file exists on NAS"""
        if not self.nas_mount_path:
            return False
        
        nas_path = Path(self.nas_mount_path) / self.nas_media_folder / filename
        return nas_path.exists()
    
    def get_nas_usage(self) -> dict:
        """Get NAS storage usage statistics"""
        if not self.nas_mount_path:
            return {'total_files': 0, 'total_size': 0}
        
        nas_path = Path(self.nas_mount_path) / self.nas_media_folder
        if not nas_path.exists():
            return {'total_files': 0, 'total_size': 0}
        
        total_files = 0
        total_size = 0
        
        for file_path in nas_path.rglob('*'):
            if file_path.is_file():
                total_files += 1
                total_size += file_path.stat().st_size
        
        return {
            'total_files': total_files,
            'total_size': total_size,
            'total_size_mb': total_size / (1024 * 1024)
        }
