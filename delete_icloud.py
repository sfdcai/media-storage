#!/usr/bin/env python3
"""
Enhanced iCloud Deletion Module
Performs final deletion of files from iCloud and local storage
"""

import os
import time
from typing import List, Dict, Any
from common import config_manager, db_manager, setup_module_logger, auth_manager

# Setup module-specific logger
logger = setup_module_logger(__name__)

class ICloudDeletionManager:
    """Manages iCloud deletion operations"""
    
    def __init__(self):
        self.config = config_manager.get_icloud_config()
        self.dir_config = config_manager.get_directory_config()
        self.db = db_manager
        self.max_retries = 3
        self.retry_delay = 5  # seconds
    
    def validate_icloud_connection(self) -> bool:
        """Validate iCloud connection"""
        return auth_manager.test_icloud_connection()
    
    def get_files_ready_for_deletion(self) -> List[Dict[str, Any]]:
        """Get files ready for iCloud deletion"""
        return self.db.get_media_ready_for_deletion()
    
    def delete_from_icloud_album(self, filename: str, album_name: str) -> bool:
        """Delete file from iCloud album"""
        try:
            album = auth_manager.get_or_create_icloud_album(album_name)
            if not album:
                logger.warning(f"iCloud album {album_name} not found")
                return False
            
            # Find and delete the photo by filename
            for photo in album.photos:
                if photo.filename == filename:
                    photo.delete()
                    logger.info(f"Deleted {filename} from iCloud album {album_name}")
                    return True
            
            logger.warning(f"Photo {filename} not found in iCloud album {album_name}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete {filename} from iCloud: {e}")
            return False
    
    def delete_local_file(self, file_path: str) -> bool:
        """Delete local file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted local file: {file_path}")
                return True
            else:
                logger.warning(f"Local file not found: {file_path}")
                return True  # Consider it successful if file doesn't exist
        except Exception as e:
            logger.error(f"Failed to delete local file {file_path}: {e}")
            return False
    
    def delete_file(self, file_info: Dict[str, Any]) -> bool:
        """Delete a single file from both iCloud and local storage"""
        filename = file_info['filename']
        local_path = file_info['local_path']
        icloud_id = file_info['icloud_id']
        
        try:
            # Delete from iCloud album
            icloud_success = self.delete_from_icloud_album(filename, self.config.album_name)
            
            # Delete local file
            local_success = self.delete_local_file(local_path)
            
            # Update database if both operations succeeded
            if icloud_success and local_success:
                if self.db.mark_deleted_icloud(icloud_id):
                    logger.info(f"✅ Successfully deleted: {filename}")
                    return True
                else:
                    logger.error(f"Failed to update database for: {filename}")
                    return False
            else:
                logger.error(f"Deletion failed for {filename} (iCloud: {icloud_success}, Local: {local_success})")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting {filename}: {e}")
            self.db.increment_error_count(icloud_id, f"Deletion error: {str(e)}")
            return False
    
    def delete_batch(self) -> Dict[str, int]:
        """Delete a batch of files"""
        results = {
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0
        }
        
        files = self.get_files_ready_for_deletion()
        results['total_files'] = len(files)
        
        if not files:
            logger.info("No files ready for deletion")
            return results
        
        logger.info(f"Found {len(files)} files ready for deletion")
        
        for file_info in files:
            filename = file_info['filename']
            icloud_id = file_info['icloud_id']
            
            # Check if already deleted
            if file_info.get('deleted_icloud') == 'yes':
                results['skipped'] += 1
                continue
            
            success = False
            for attempt in range(self.max_retries):
                try:
                    if self.delete_file(file_info):
                        results['successful'] += 1
                        success = True
                        break
                    else:
                        logger.warning(f"Deletion failed for {filename} (attempt {attempt + 1})")
                        
                except Exception as e:
                    logger.error(f"Error during deletion attempt {attempt + 1} for {filename}: {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
            
            if not success:
                results['failed'] += 1
                self.db.increment_error_count(icloud_id, f"Deletion failed after {self.max_retries} attempts")
        
        return results
    
    def get_deletion_stats(self) -> Dict[str, Any]:
        """Get deletion statistics"""
        try:
            stats = self.db.get_pipeline_stats()
            deletion_stats = {
                'total_files': stats.get('total', 0),
                'deleted_from_icloud': stats.get('deleted_icloud', 0),
                'pending_deletion': stats.get('total', 0) - stats.get('deleted_icloud', 0),
                'icloud_connected': self.validate_icloud_connection(),
                'album_name': self.config.album_name
            }
            return deletion_stats
        except Exception as e:
            logger.error(f"Error getting deletion stats: {e}")
            return {}

def main():
    """Main iCloud deletion pipeline"""
    logger.info("Starting iCloud deletion pipeline...")
    
    # Validate configuration
    if not config_manager.validate_config():
        logger.error("Configuration validation failed")
        return False
    
    # Initialize database
    db_manager.init_database()
    
    # Create deletion manager
    deletion_manager = ICloudDeletionManager()
    
    # Validate iCloud connection
    if not deletion_manager.validate_icloud_connection():
        logger.error("iCloud connection validation failed")
        return False
    
    # Perform batch deletion
    results = deletion_manager.delete_batch()
    
    # Log results
    logger.info(f"iCloud deletion completed:")
    logger.info(f"  Total files: {results['total_files']}")
    logger.info(f"  Successful: {results['successful']}")
    logger.info(f"  Failed: {results['failed']}")
    logger.info(f"  Skipped: {results['skipped']}")
    
    # Get and log statistics
    stats = deletion_manager.get_deletion_stats()
    logger.info(f"iCloud deletion statistics: {stats}")
    
    success = results['failed'] == 0
    if success:
        logger.info("✅ iCloud deletion pipeline completed successfully")
    else:
        logger.warning(f"⚠️ iCloud deletion completed with {results['failed']} failures")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
