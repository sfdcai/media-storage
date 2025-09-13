#!/usr/bin/env python3
"""
Enhanced iCloud Sync Module
Downloads media from iCloud and manages database records
"""

import os
import subprocess
import datetime
import time
from pathlib import Path
from typing import List, Dict, Any
from common import config_manager, db_manager, setup_module_logger, auth_manager

# Setup module-specific logger
logger = setup_module_logger(__name__)


class ICloudSyncManager:
    """Manages iCloud synchronization operations"""
    
    def __init__(self):
        self.config = config_manager.get_icloud_config()
        self.db = db_manager
        self.max_retries = 3
        self.retry_delay = 5  # seconds
    
    def validate_icloud_connection(self) -> bool:
        """Validate iCloud connection"""
        return auth_manager.test_icloud_connection()
    
    def run_icloudpd(self) -> bool:
        """Run icloudpd command to download files"""
        try:
            cmd = [
                "icloudpd",
                "--username", self.config.username,
                "--directory", self.config.directory
            ]

            if self.config.days > 0:
                cmd.extend(["--recent", str(self.config.days)])
            elif self.config.recent > 0:
                cmd.extend(["--recent", str(self.config.recent)])

            if self.config.auto_delete:
                cmd.append("--auto-delete")

            logger.info(f"▶️ Running icloudpd: {' '.join(cmd)}")
            
            # Run with timeout and error handling
            result = subprocess.run(
                cmd, 
                check=True, 
                capture_output=True, 
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            logger.info("✅ iCloud download finished successfully")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("❌ icloudpd timed out after 1 hour")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ icloudpd failed with return code {e.returncode}")
            logger.error(f"Error output: {e.stderr}")
            return False
        except FileNotFoundError:
            logger.error("❌ icloudpd command not found. Please install icloudpd")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error running icloudpd: {e}")
            return False
    
    def scan_and_update_db(self) -> Dict[str, int]:
        """Scan download directory and update database with new media"""
        results = {
            'total_files': 0,
            'new_files': 0,
            'existing_files': 0,
            'errors': 0
        }
        
        base_dir = self.config.directory
        logger.info(f"🔍 Scanning {base_dir} for new media...")
        
        if not os.path.exists(base_dir):
            logger.error(f"Download directory does not exist: {base_dir}")
            return results
        
        try:
            for root, dirs, files in os.walk(base_dir):
                for fname in files:
                    results['total_files'] += 1
                    full_path = os.path.join(root, fname)
                    
                    try:
                        # Get file creation time
                        created_timestamp = os.path.getctime(full_path)
                        created_date = datetime.datetime.fromtimestamp(created_timestamp).isoformat()
                        
                        # Use filename as icloud_id (icloudpd doesn't expose real ID)
                        icloud_id = fname
                        
                        # Add to database
                        if self.db.add_media_record(
                            filename=fname,
                            icloud_id=icloud_id,
                            created_date=created_date,
                            local_path=full_path,
                            status="downloaded"
                        ):
                            results['new_files'] += 1
                        else:
                            results['existing_files'] += 1
                            
                    except Exception as e:
                        logger.error(f"Error processing file {fname}: {e}")
                        results['errors'] += 1
            
            logger.info(f"Database scan completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error scanning directory {base_dir}: {e}")
            return results
    
    def get_sync_stats(self) -> Dict[str, Any]:
        """Get iCloud sync statistics"""
        try:
            stats = self.db.get_pipeline_stats()
            sync_stats = {
                'total_files': stats.get('total', 0),
                'downloaded_files': stats.get('total', 0),  # All files are downloaded
                'icloud_connected': self.validate_icloud_connection(),
                'download_directory': self.config.directory,
                'directory_exists': os.path.exists(self.config.directory)
            }
            return sync_stats
        except Exception as e:
            logger.error(f"Error getting sync stats: {e}")
            return {}

def main():
    """Main iCloud synchronization pipeline"""
    logger.info("Starting iCloud synchronization pipeline...")
    
    # Validate configuration
    if not config_manager.validate_config():
        logger.error("Configuration validation failed")
        return False
    
    # Initialize database
    db_manager.init_database()
    
    # Create sync manager
    sync_manager = ICloudSyncManager()
    
    # Validate iCloud connection
    if not sync_manager.validate_icloud_connection():
        logger.warning("iCloud connection validation failed, but continuing with download attempt")
    
    # Run icloudpd download
    if not sync_manager.run_icloudpd():
        logger.error("iCloud download failed")
        return False
    
    # Scan and update database
    scan_results = sync_manager.scan_and_update_db()
    
    # Log results
    logger.info(f"iCloud sync completed:")
    logger.info(f"  Total files found: {scan_results['total_files']}")
    logger.info(f"  New files added: {scan_results['new_files']}")
    logger.info(f"  Existing files: {scan_results['existing_files']}")
    logger.info(f"  Errors: {scan_results['errors']}")
    
    # Get and log statistics
    stats = sync_manager.get_sync_stats()
    logger.info(f"iCloud sync statistics: {stats}")
    
    success = scan_results['errors'] == 0
    if success:
        logger.info("✅ iCloud synchronization pipeline completed successfully")
    else:
        logger.warning(f"⚠️ iCloud synchronization completed with {scan_results['errors']} errors")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
