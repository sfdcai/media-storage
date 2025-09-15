"""
iCloud file management utilities with 2FA support
"""

import os
import subprocess
import time
import getpass
from pathlib import Path
from typing import List, Optional


class iCloudManager:
    """Handle iCloud file operations with 2FA support"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.icloud_username = config.get('icloud.username', '')
        self.icloud_password = config.get('icloud.password', '')
        self.icloud_download_dir = config.get('icloud.download_dir', '')
        self.icloudpd_path = config.get('icloud.icloudpd_path', 'icloudpd')
        self.trusted_device = config.get('icloud.trusted_device', False)
        self.cookie_directory = config.get('icloud.cookie_directory', '~/.pyiCloud')
    
    def download_from_icloud(self, dry_run: bool = False, interactive: bool = True) -> List[str]:
        """Download files from iCloud using icloudpd with 2FA support"""
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
            # Build icloudpd command with 2FA support
            cmd = [
                self.icloudpd_path,
                '--username', self.icloud_username,
                '--directory', self.icloud_download_dir,
                '--download-only',
                '--skip-videos',  # Skip videos by default, can be configured
                '--auto-delete',  # Auto-delete after download
                '--folder-structure', 'none'  # Flat structure
            ]
            
            # Add cookie directory for session persistence
            if self.cookie_directory:
                cmd.extend(['--cookie-directory', os.path.expanduser(self.cookie_directory)])
            
            # Add password if provided (for non-interactive mode)
            if self.icloud_password and not interactive:
                cmd.extend(['--password', self.icloud_password])
            
            self.logger.info("Downloading files from iCloud...")
            
            if interactive:
                # Interactive mode - let icloudpd handle 2FA prompts
                self.logger.info("Running in interactive mode - you may be prompted for 2FA code")
                result = subprocess.run(cmd, timeout=600)  # 10 minutes timeout for 2FA
            else:
                # Non-interactive mode - capture output
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.logger.info("iCloud download completed successfully")
                return self._get_downloaded_files()
            else:
                if interactive:
                    self.logger.error("iCloud download failed - check output above")
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
    
    def setup_2fa_authentication(self) -> bool:
        """Setup 2FA authentication for iCloud"""
        if not self.icloud_username:
            self.logger.error("iCloud username not configured")
            return False
        
        try:
            self.logger.info("Setting up 2FA authentication for iCloud...")
            self.logger.info("This will prompt you for your password and 2FA code")
            
            # First run to trigger 2FA setup
            cmd = [
                self.icloudpd_path,
                '--username', self.icloud_username,
                '--list-albums',
                '--cookie-directory', os.path.expanduser(self.cookie_directory)
            ]
            
            self.logger.info("Running initial authentication...")
            result = subprocess.run(cmd, timeout=300)  # 5 minutes for 2FA setup
            
            if result.returncode == 0:
                self.logger.info("✅ 2FA authentication setup successful")
                self.trusted_device = True
                return True
            else:
                self.logger.error("❌ 2FA authentication setup failed")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("2FA setup timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error setting up 2FA: {e}")
            return False
    
    def test_icloud_connection(self) -> bool:
        """Test iCloud connection"""
        if not self.icloud_username:
            return False
        
        try:
            cmd = [
                self.icloudpd_path,
                '--username', self.icloud_username,
                '--list-albums',
                '--cookie-directory', os.path.expanduser(self.cookie_directory)
            ]
            
            # Add password only if not using cookies
            if self.icloud_password and not self.trusted_device:
                cmd.extend(['--password', self.icloud_password])
            
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
            'trusted_device': self.trusted_device,
            'cookie_directory': self.cookie_directory,
            'connection_ok': self.test_icloud_connection()
        }
