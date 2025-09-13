#!/usr/bin/env python3
"""
Enhanced Bulk Pixel Sync Module
Tracks Syncthing synchronization to Pixel device and Google Photos backup
"""

import os
import time
from typing import List, Dict, Any
from common import config_manager, db_manager, setup_module_logger, auth_manager

# Setup module-specific logger
logger = setup_module_logger(__name__)


class PixelSyncManager:
    """Manages Pixel device synchronization operations"""
    
    def __init__(self):
        self.config = config_manager.get_syncthing_config()
        self.db = db_manager
        self.max_retries = self.config.max_retries
        self.retry_delay = 5  # seconds
    
    def validate_syncthing_connection(self) -> bool:
        """Validate Syncthing connection"""
        return auth_manager.test_syncthing_connection()
    
    def get_fully_synced_files(self) -> List[str]:
        """Get list of fully synced files from Syncthing"""
        return auth_manager.get_syncthing_fully_synced_files(self.config.folder_id)
    
    def mark_files_synced(self, synced_files: List[str]) -> Dict[str, int]:
        """Mark files as synced to Google Photos in database"""
        results = {
            'total_files': len(synced_files),
            'updated_count': 0,
            'not_found_count': 0,
            'already_synced_count': 0
        }
        
        for filename in synced_files:
            try:
                # Find the file in database by filename
                files = self.db.get_media_by_status('downloaded')
                matching_file = None
                
                for file_info in files:
                    if file_info['filename'] == filename:
                        matching_file = file_info
                        break
                
                if matching_file:
                    if matching_file.get('synced_google') == 'yes':
                        results['already_synced_count'] += 1
                        logger.debug(f"File already synced: {filename}")
                    else:
                        if self.db.mark_synced_google(matching_file['icloud_id']):
                            results['updated_count'] += 1
                            logger.info(f"Marked as synced: {filename}")
                        else:
                            logger.error(f"Failed to update database for: {filename}")
                else:
                    results['not_found_count'] += 1
                    logger.warning(f"File not found in database: {filename}")
                    
            except Exception as e:
                logger.error(f"Error processing file {filename}: {e}")
        
        return results
    
    def cleanup_local_pixel_files(self, synced_files: List[str]) -> Dict[str, int]:
        """Clean up local Pixel files after successful sync"""
        if not self.config.delete_local_pixel:
            logger.info("Local Pixel cleanup disabled in configuration")
            return {'total': 0, 'deleted': 0, 'errors': 0}
        
        results = {
            'total': len(synced_files),
            'deleted': 0,
            'errors': 0,
            'not_found': 0
        }
        
        logger.info("Starting local Pixel cleanup...")
        
        for filename in synced_files:
            try:
                pixel_path = os.path.join(self.config.pixel_local_folder, filename)
                
                if os.path.exists(pixel_path):
                    os.remove(pixel_path)
                    results['deleted'] += 1
                    logger.info(f"Deleted local Pixel file: {filename}")
                else:
                    results['not_found'] += 1
                    logger.debug(f"Local Pixel file not found: {filename}")
                    
            except Exception as e:
                results['errors'] += 1
                logger.error(f"Failed to delete {filename} locally: {e}")
        
        return results
    
    def get_sync_stats(self) -> Dict[str, Any]:
        """Get Pixel sync statistics"""
        try:
            stats = self.db.get_pipeline_stats()
            sync_stats = {
                'total_files': stats.get('total', 0),
                'synced_to_google': stats.get('synced_google', 0),
                'pending_google_sync': stats.get('total', 0) - stats.get('synced_google', 0),
                'syncthing_connected': self.validate_syncthing_connection(),
                'folder_id': self.config.folder_id,
                'delete_local_enabled': self.config.delete_local_pixel
            }
            return sync_stats
        except Exception as e:
            logger.error(f"Error getting sync stats: {e}")
            return {}
    
    def sync_batch(self) -> Dict[str, Any]:
        """Perform batch synchronization check and update"""
        results = {
            'syncthing_connected': False,
            'synced_files_count': 0,
            'database_updates': {},
            'cleanup_results': {},
            'success': False
        }
        
        # Validate Syncthing connection
        if not self.validate_syncthing_connection():
            logger.error("Syncthing connection validation failed")
            return results
        
        results['syncthing_connected'] = True
        
        # Get fully synced files
        try:
            synced_files = self.get_fully_synced_files()
            results['synced_files_count'] = len(synced_files)
            logger.info(f"Found {len(synced_files)} fully synced files in Syncthing")
        except Exception as e:
            logger.error(f"Error fetching Syncthing folder status: {e}")
            return results
        
        if not synced_files:
            logger.info("No fully synced files found")
            results['success'] = True
            return results
        
        # Update database
        db_results = self.mark_files_synced(synced_files)
        results['database_updates'] = db_results
        logger.info(f"Database updates: {db_results}")
        
        # Clean up local Pixel files
        cleanup_results = self.cleanup_local_pixel_files(synced_files)
        results['cleanup_results'] = cleanup_results
        logger.info(f"Cleanup results: {cleanup_results}")
        
        results['success'] = True
        return results

def main():
    """Main Pixel synchronization pipeline"""
    logger.info("Starting bulk Pixel sync pipeline...")
    
    # Validate configuration
    if not config_manager.validate_config():
        logger.error("Configuration validation failed")
        return False
    
    # Initialize database
    db_manager.init_database()
    
    # Create sync manager
    sync_manager = PixelSyncManager()
    
    # Perform batch sync
    results = sync_manager.sync_batch()
    
    # Log results
    logger.info(f"Pixel sync completed:")
    logger.info(f"  Syncthing connected: {results['syncthing_connected']}")
    logger.info(f"  Synced files found: {results['synced_files_count']}")
    logger.info(f"  Database updates: {results['database_updates']}")
    logger.info(f"  Cleanup results: {results['cleanup_results']}")
    
    # Get and log statistics
    stats = sync_manager.get_sync_stats()
    logger.info(f"Pixel sync statistics: {stats}")
    
    success = results['success']
    if success:
        logger.info("✅ Bulk Pixel sync pipeline completed successfully")
    else:
        logger.error("❌ Bulk Pixel sync pipeline failed")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
