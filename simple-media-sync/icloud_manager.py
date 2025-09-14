"""
iCloud file management utilities
"""

import os
import subprocess
from pathlib import Path
from typing import List, Optional


class iCloudManager:
    """Handle iCloud file operations"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.icloud_username = config.get('icloud.username', '')
        self.icloud_password = config.get('icloud.password', '')
        self.icloud_download_dir = config.get('icloud.download_dir', '')
        self.icloudpd_path = config.get('icloud.icloudpd_path', 'icloudpd')
    
    def download_from_icloud(self, dry_run: bool = False) -> List[str]:
        """Download files from iCloud using icloudpd"""
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
            # Build icloudpd command
            cmd = [
                self.icloudpd_path,
                '--username', self.icloud_username,
                '--password', self.icloud_password,
                '--directory', self.icloud_download_dir,
                '--download-only',
                '--skip-videos'  # Skip videos by default, can be configured
            ]
            
            self.logger.info("Downloading files from iCloud...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.logger.info("iCloud download completed successfully")
                return self._get_downloaded_files()
            else:
                self.logger.error(f"iCloud download failed: {result.stderr}")
                return []
                
        except subprocess.TimeoutExpired:
            self.logger.error("iCloud download timed out")
            return []
        except Exception as e:
            self.logger.error(f"Error downloading from iCloud: {e}")
            return []
    
    def delete_from_icloud(self, file_path: str, dry_run: bool = False) -> bool:
        """Delete file from iCloud (requires icloudpd with delete capability)"""
        if not self.icloud_username:
            self.logger.error("iCloud credentials not configured")
            return False
        
        if dry_run:
            self.logger.info(f"[DRY RUN] Would delete from iCloud: {file_path}")
            return True
        
        try:
            # Note: This requires icloudpd with delete functionality
            # You might need to use a different approach or tool
            cmd = [
                self.icloudpd_path,
                '--username', self.icloud_username,
                '--password', self.icloud_password,
                '--delete-photos',
                '--photo', file_path
            ]
            
            self.logger.info(f"Deleting from iCloud: {file_path}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.logger.info(f"Successfully deleted from iCloud: {file_path}")
                return True
            else:
                self.logger.error(f"Failed to delete from iCloud: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deleting from iCloud: {e}")
            return False
    
    def _get_downloaded_files(self) -> List[str]:
        """Get list of recently downloaded files"""
        if not self.icloud_download_dir:
            return []
        
        download_path = Path(self.icloud_download_dir)
        if not download_path.exists():
            return []
        
        # Get files modified in the last hour (recently downloaded)
        import time
        current_time = time.time()
        recent_files = []
        
        for file_path in download_path.rglob('*'):
            if file_path.is_file():
                # Check if file was modified in the last hour
                if current_time - file_path.stat().st_mtime < 3600:
                    recent_files.append(str(file_path))
        
        return recent_files
    
    def test_icloud_connection(self) -> bool:
        """Test iCloud connection"""
        if not self.icloud_username or not self.icloud_password:
            return False
        
        try:
            cmd = [
                self.icloudpd_path,
                '--username', self.icloud_username,
                '--password', self.icloud_password,
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
