#!/usr/bin/env python3
"""
Enhanced iCloud Cleanup Module
Moves files to delete pending album and prepares for deletion
"""

import os
import shutil
import time
from typing import List, Dict, Any
from common import config_manager, db_manager, setup_module_logger, auth_manager

# Setup module-specific logger
logger = setup_module_logger(__name__)

class ICloudCleanupManager:
    """Manages iCloud cleanup operations"""
    
    def __init__(self):
        self.config = config_manager.get_icloud_config()
        self.dir_config = config_manager.get_directory_config()
        self.db = db_manager
        self.max_retries = 3
        self.retry_delay = 5  # seconds
    
    def validate_icloud_connection(self) -> bool:
        """Validate iCloud connection"""
        return auth_manager.test_icloud_connection()
    
    def get_files_ready_for_cleanup(self) -> List[Dict[str, Any]]:
        """Get files ready for iCloud cleanup"""
        return self.db.get_media_ready_for_cleanup()
    
    def move_file(self, src_path: str, dst_folder: str) -> str:
        """Move file to destination folder"""
        os.makedirs(dst_folder, exist_ok=True)
        dst_path = os.path.join(dst_folder, os.path.basename(src_path))
        shutil.move(src_path, dst_path)
        return dst_path
    
    def add_file_to_icloud_album(self, file_path: str, album_name: str) -> bool:
        """Add file to iCloud album"""
        try:
            album = auth_manager.get_or_create_icloud_album(album_name)
            if not album:
                logger.error(f"Failed to get/create iCloud album: {album_name}")
                return False
            
            album.add(file_path)
            logger.info(f"Added {os.path.basename(file_path)} to iCloud album {album_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add file to iCloud album: {e}")
            return False
    
    def cleanup_file(self, file_info: Dict[str, Any]) -> bool:
        """Clean up a single file"""
        filename = file_info['filename']
        local_path = file_info['local_path']
        icloud_id = file_info['icloud_id']
        
        try:
            if not os.path.exists(local_path):
                logger.warning(f"File not found: {local_path}")
                return False
            
            # Move file to processed folder first
            processed_path = self.move_file(local_path, self.dir_config.processed)
            logger.info(f"Moved {filename} → processed folder")
            
            # Then move to delete_pending folder
            delete_path = self.move_file(processed_path, self.dir_config.delete_pending)
            logger.info(f"Moved {filename} → delete_pending folder")
            
            # Add to iCloud album
            if self.add_file_to_icloud_album(delete_path, self.config.album_name):
                # Update database
                if self.db.mark_album_moved(icloud_id):
                    logger.info(f"✅ Successfully cleaned up: {filename}")
                    return True
                else:
                    logger.error(f"Failed to update database for: {filename}")
                    return False
            else:
                logger.error(f"Failed to add {filename} to iCloud album")
                return False
                
        except Exception as e:
            logger.error(f"Error cleaning up {filename}: {e}")
            self.db.increment_error_count(icloud_id, f"Cleanup error: {str(e)}")
            return False
    
    def cleanup_batch(self) -> Dict[str, int]:
        """Clean up a batch of files"""
        results = {
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0
        }
        
        files = self.get_files_ready_for_cleanup()
        results['total_files'] = len(files)
        
        if not files:
            logger.info("No files ready for cleanup")
            return results
        
        logger.info(f"Found {len(files)} files ready for cleanup")
        
        for file_info in files:
            filename = file_info['filename']
            icloud_id = file_info['icloud_id']
            
            # Check if already processed
            if file_info.get('album_moved') == 1:
                results['skipped'] += 1
                continue
            
            success = False
            for attempt in range(self.max_retries):
                try:
                    if self.cleanup_file(file_info):
                        results['successful'] += 1
                        success = True
                        break
                    else:
                        logger.warning(f"Cleanup failed for {filename} (attempt {attempt + 1})")
                        
                except Exception as e:
                    logger.error(f"Error during cleanup attempt {attempt + 1} for {filename}: {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
            
            if not success:
                results['failed'] += 1
                self.db.increment_error_count(icloud_id, f"Cleanup failed after {self.max_retries} attempts")
        
        return results
    
    def get_cleanup_stats(self) -> Dict[str, Any]:
        """Get cleanup statistics"""
        try:
            stats = self.db.get_pipeline_stats()
            cleanup_stats = {
                'total_files': stats.get('total', 0),
                'album_moved': stats.get('album_moved', 0),
                'pending_cleanup': stats.get('total', 0) - stats.get('album_moved', 0),
                'icloud_connected': self.validate_icloud_connection(),
                'album_name': self.config.album_name
            }
            return cleanup_stats
        except Exception as e:
            logger.error(f"Error getting cleanup stats: {e}")
            return {}

def main():
    """Main iCloud cleanup pipeline"""
    logger.info("Starting iCloud cleanup pipeline...")
    
    # Validate configuration
    if not config_manager.validate_config():
        logger.error("Configuration validation failed")
        return False
    
    # Initialize database
    db_manager.init_database()
    
    # Create cleanup manager
    cleanup_manager = ICloudCleanupManager()
    
    # Validate iCloud connection
    if not cleanup_manager.validate_icloud_connection():
        logger.error("iCloud connection validation failed")
        return False
    
    # Perform batch cleanup
    results = cleanup_manager.cleanup_batch()
    
    # Log results
    logger.info(f"iCloud cleanup completed:")
    logger.info(f"  Total files: {results['total_files']}")
    logger.info(f"  Successful: {results['successful']}")
    logger.info(f"  Failed: {results['failed']}")
    logger.info(f"  Skipped: {results['skipped']}")
    
    # Get and log statistics
    stats = cleanup_manager.get_cleanup_stats()
    logger.info(f"iCloud cleanup statistics: {stats}")
    
    success = results['failed'] == 0
    if success:
        logger.info("✅ iCloud cleanup pipeline completed successfully")
    else:
        logger.warning(f"⚠️ iCloud cleanup completed with {results['failed']} failures")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
