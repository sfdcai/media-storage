"""
Simple iCloud file management using icloudpd directly
"""

import os
import subprocess
from pathlib import Path
from typing import List


class iCloudManager:
    """Simple iCloud file operations using icloudpd"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.icloud_username = config.get('icloud.username', '')
        self.icloud_password = config.get('icloud.password', '')
        self.icloud_download_dir = config.get('icloud.download_dir', '')
        self.icloudpd_path = config.get('icloud.icloudpd_path', 'icloudpd')
    
    def download_from_icloud(self, dry_run: bool = False, limit: int = 5) -> List[str]:
        """Download files from iCloud using icloudpd directly"""
        if not self.icloud_username or not self.icloud_download_dir:
            self.logger.error("iCloud credentials or download directory not configured")
            return []
        
        if not Path(self.icloud_download_dir).exists():
            self.logger.error(f"iCloud download directory does not exist: {self.icloud_download_dir}")
            return []
        
        if dry_run:
            self.logger.info("[DRY RUN] Would download files from iCloud")
            return []
        
        try:
            # Simple icloudpd command - let it handle 2FA naturally
            cmd = [
                self.icloudpd_path,
                '--username', self.icloud_username,
                '--directory', self.icloud_download_dir,
                '--folder-structure', 'none',
                '--recent', '30',
                '--skip-videos'
            ]
            
            self.logger.info("Downloading files from iCloud...")
            self.logger.info(f"Command: {' '.join(cmd)}")
            
            # Let icloudpd handle everything - it will prompt for 2FA if needed
            result = subprocess.run(cmd, timeout=600)
            
            if result.returncode == 0:
                self.logger.info("iCloud download completed successfully")
                return self._get_downloaded_files(limit)
            else:
                self.logger.error("iCloud download failed")
                return []
                
        except subprocess.TimeoutExpired:
            self.logger.error("iCloud download timed out")
            return []
        except Exception as e:
            self.logger.error(f"Error downloading from iCloud: {e}")
            return []
    
    def delete_from_icloud(self, file_path: str, dry_run: bool = False) -> bool:
        """Delete file from iCloud using icloudpd"""
        if not self.icloud_username:
            self.logger.error("iCloud credentials not configured")
            return False
        
        if dry_run:
            self.logger.info(f"[DRY RUN] Would delete from iCloud: {file_path}")
            return True
        
        try:
            cmd = [
                self.icloudpd_path,
                '--username', self.icloud_username,
                '--delete-photos',
                '--photo', file_path
            ]
            
            self.logger.info(f"Deleting from iCloud: {file_path}")
            result = subprocess.run(cmd, timeout=60)
            
            if result.returncode == 0:
                self.logger.info(f"Successfully deleted from iCloud: {file_path}")
                return True
            else:
                self.logger.error(f"Failed to delete from iCloud")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deleting from iCloud: {e}")
            return False
    
    def _get_downloaded_files(self, limit: int = 5) -> List[str]:
        """Get list of downloaded files (limited for testing)"""
        if not self.icloud_download_dir:
            return []
        
        download_path = Path(self.icloud_download_dir)
        if not download_path.exists():
            return []
        
        # Get all media files (since icloudpd shows "already exists" for existing files)
        media_extensions = ['.jpg', '.jpeg', '.png', '.heic', '.mov', '.mp4', '.avi']
        media_files = []
        
        for file_path in download_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in media_extensions:
                media_files.append(str(file_path))
        
        # Limit to specified number for testing
        return media_files[:limit]
    
    def test_icloud_connection(self) -> bool:
        """Test iCloud connection"""
        if not self.icloud_username:
            return False
        
        try:
            cmd = [
                self.icloudpd_path,
                '--username', self.icloud_username,
                '--list-albums'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0
            
        except Exception:
            return False
    
    def get_icloud_status(self) -> dict:
        """Get iCloud account status"""
        return {
            'username_configured': bool(self.icloud_username),
            'password_configured': bool(self.icloud_password),
            'download_dir_configured': bool(self.icloud_download_dir),
            'connection_ok': self.test_icloud_connection()
        }
