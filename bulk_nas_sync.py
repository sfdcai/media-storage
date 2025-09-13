#!/usr/bin/env python3
"""
NAS Synchronization Module
Syncs media files to NAS for local archival backup
"""

import os
import shutil
import logging
import time
from pathlib import Path
from typing import List, Dict, Any
from common import config_manager, db_manager, setup_module_logger, auth_manager

# Setup module-specific logger
logger = setup_module_logger(__name__)

class NASSyncManager:
    """Manages NAS synchronization operations"""
    
    def __init__(self):
        self.config = config_manager.get_nas_config()
        self.dir_config = config_manager.get_directory_config()
        self.db = db_manager
        self.max_retries = 3
        self.retry_delay = 5  # seconds
    
    def validate_nas_connection(self) -> bool:
        """Validate NAS mount and accessibility"""
        try:
            if not os.path.exists(self.config.mount_path):
                logger.error(f"NAS mount path does not exist: {self.config.mount_path}")
                return False
            
            # Test write access
            test_file = os.path.join(self.config.mount_path, ".nas_test")
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                logger.info("✅ NAS connection validated")
                return True
            except Exception as e:
                logger.error(f"NAS write test failed: {e}")
                return False
                
        except Exception as e:
            logger.error(f"NAS validation error: {e}")
            return False
    
    def get_files_ready_for_nas_sync(self) -> List[Dict[str, Any]]:
        """Get files ready for NAS synchronization"""
        return self.db.get_media_ready_for_nas_sync()
    
    def sync_file_to_nas(self, file_info: Dict[str, Any]) -> bool:
        """Sync a single file to NAS"""
        try:
            local_path = file_info['local_path']
            filename = file_info['filename']
            icloud_id = file_info['icloud_id']
            
            if not os.path.exists(local_path):
                logger.warning(f"Source file not found: {local_path}")
                return False
            
            # Create NAS directory structure (organize by date)
            created_date = file_info.get('created_date', '')
            if created_date:
                try:
                    from datetime import datetime
                    date_obj = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                    year_month = date_obj.strftime('%Y/%m')
                except:
                    year_month = 'unknown'
            else:
                year_month = 'unknown'
            
            nas_dir = os.path.join(self.config.mount_path, year_month)
            os.makedirs(nas_dir, exist_ok=True)
            
            nas_path = os.path.join(nas_dir, filename)
            
            # Check if file already exists on NAS
            if os.path.exists(nas_path):
                # Verify file integrity
                if self._verify_file_integrity(local_path, nas_path):
                    logger.info(f"File already exists on NAS: {filename}")
                    return True
                else:
                    logger.warning(f"File exists on NAS but integrity check failed: {filename}")
            
            # Copy file to NAS
            logger.info(f"Syncing {filename} to NAS...")
            shutil.copy2(local_path, nas_path)
            
            # Verify the copy
            if self._verify_file_integrity(local_path, nas_path):
                logger.info(f"✅ Successfully synced {filename} to NAS")
                return True
            else:
                logger.error(f"File integrity check failed after NAS sync: {filename}")
                # Clean up failed copy
                if os.path.exists(nas_path):
                    os.remove(nas_path)
                return False
                
        except Exception as e:
            logger.error(f"Error syncing {file_info.get('filename', 'unknown')} to NAS: {e}")
            return False
    
    def _verify_file_integrity(self, source_path: str, target_path: str) -> bool:
        """Verify file integrity between source and target"""
        try:
            source_size = os.path.getsize(source_path)
            target_size = os.path.getsize(target_path)
            
            if source_size != target_size:
                logger.warning(f"File size mismatch: {source_size} vs {target_size}")
                return False
            
            # Optional: Add checksum verification for critical files
            # For now, size comparison is sufficient
            return True
            
        except Exception as e:
            logger.error(f"File integrity check error: {e}")
            return False
    
    def cleanup_local_file(self, file_info: Dict[str, Any]) -> bool:
        """Clean up local file after successful NAS sync (if configured)"""
        if not self.config.delete_after_sync:
            return True
        
        try:
            local_path = file_info['local_path']
            if os.path.exists(local_path):
                os.remove(local_path)
                logger.info(f"Cleaned up local file: {local_path}")
                return True
        except Exception as e:
            logger.error(f"Error cleaning up local file {local_path}: {e}")
            return False
    
    def sync_batch_to_nas(self, files: List[Dict[str, Any]]) -> Dict[str, int]:
        """Sync a batch of files to NAS"""
        results = {
            'total': len(files),
            'successful': 0,
            'failed': 0,
            'skipped': 0
        }
        
        for file_info in files:
            filename = file_info['filename']
            icloud_id = file_info['icloud_id']
            
            # Check if already synced
            if file_info.get('synced_nas') == 'yes':
                results['skipped'] += 1
                continue
            
            success = False
            for attempt in range(self.max_retries):
                try:
                    if self.sync_file_to_nas(file_info):
                        # Mark as synced in database
                        if self.db.mark_synced_nas(icloud_id):
                            results['successful'] += 1
                            success = True
                            
                            # Clean up local file if configured
                            if self.config.delete_after_sync:
                                self.cleanup_local_file(file_info)
                            break
                        else:
                            logger.error(f"Failed to update database for {filename}")
                    else:
                        logger.warning(f"NAS sync failed for {filename} (attempt {attempt + 1})")
                        
                except Exception as e:
                    logger.error(f"Error during NAS sync attempt {attempt + 1} for {filename}: {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
            
            if not success:
                results['failed'] += 1
                # Increment error count in database
                self.db.increment_error_count(icloud_id, f"NAS sync failed after {self.max_retries} attempts")
        
        return results
    
    def get_nas_sync_stats(self) -> Dict[str, Any]:
        """Get NAS synchronization statistics"""
        try:
            stats = self.db.get_pipeline_stats()
            nas_stats = {
                'total_files': stats.get('total', 0),
                'synced_to_nas': stats.get('synced_nas', 0),
                'pending_nas_sync': stats.get('total', 0) - stats.get('synced_nas', 0),
                'nas_mount_path': self.config.mount_path,
                'nas_accessible': self.validate_nas_connection()
            }
            return nas_stats
        except Exception as e:
            logger.error(f"Error getting NAS sync stats: {e}")
            return {}

def main():
    """Main NAS synchronization pipeline"""
    logger.info("Starting NAS synchronization pipeline...")
    
    # Validate configuration
    if not config_manager.validate_config():
        logger.error("Configuration validation failed")
        return False
    
    # Initialize database
    db_manager.init_database()
    
    # Create NAS sync manager
    nas_sync = NASSyncManager()
    
    # Validate NAS connection
    if not nas_sync.validate_nas_connection():
        logger.error("NAS connection validation failed")
        return False
    
    # Get files ready for NAS sync
    files = nas_sync.get_files_ready_for_nas_sync()
    
    if not files:
        logger.info("No files ready for NAS synchronization")
        return True
    
    logger.info(f"Found {len(files)} files ready for NAS sync")
    
    # Sync files to NAS
    results = nas_sync.sync_batch_to_nas(files)
    
    # Log results
    logger.info(f"NAS sync completed:")
    logger.info(f"  Total files: {results['total']}")
    logger.info(f"  Successful: {results['successful']}")
    logger.info(f"  Failed: {results['failed']}")
    logger.info(f"  Skipped: {results['skipped']}")
    
    # Get and log statistics
    stats = nas_sync.get_nas_sync_stats()
    logger.info(f"NAS sync statistics: {stats}")
    
    success = results['failed'] == 0
    if success:
        logger.info("✅ NAS synchronization pipeline completed successfully")
    else:
        logger.warning(f"⚠️ NAS synchronization completed with {results['failed']} failures")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
