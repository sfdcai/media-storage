#!/usr/bin/env python3
"""
Enhanced Bulk iCloud Sync Module
Performs bulk iCloud synchronization operations and manages large-scale downloads
"""

import os
import time
import subprocess
from typing import List, Dict, Any
from common import config_manager, db_manager, setup_module_logger, auth_manager

# Setup module-specific logger
logger = setup_module_logger(__name__)


class BulkICloudSyncManager:
    """Manages bulk iCloud synchronization operations"""
    
    def __init__(self):
        self.config = config_manager.get_icloud_config()
        self.db = db_manager
        self.max_retries = self.config.max_retries if hasattr(self.config, 'max_retries') else 3
        self.retry_delay = 5  # seconds
    
    def validate_icloud_connection(self) -> bool:
        """Validate iCloud connection"""
        return auth_manager.test_icloud_connection()
    
    def run_bulk_icloudpd(self, batch_size: int = 100, max_days: int = 0) -> bool:
        """Run icloudpd command for bulk downloads with batching"""
        try:
            cmd = [
                "icloudpd",
                "--username", self.config.username,
                "--directory", self.config.directory,
                "--batch-size", str(batch_size)
            ]

            if max_days > 0:
                cmd.extend(["--recent", str(max_days)])
            elif hasattr(self.config, 'days') and self.config.days > 0:
                cmd.extend(["--recent", str(self.config.days)])
            elif hasattr(self.config, 'recent') and self.config.recent > 0:
                cmd.extend(["--recent", str(self.config.recent)])

            if hasattr(self.config, 'auto_delete') and self.config.auto_delete:
                cmd.append("--auto-delete")

            logger.info(f"▶️ Running bulk icloudpd: {' '.join(cmd)}")
            
            # Run with extended timeout for bulk operations
            result = subprocess.run(
                cmd, 
                check=True, 
                capture_output=True, 
                text=True,
                timeout=7200  # 2 hour timeout for bulk operations
            )
            
            logger.info("✅ Bulk iCloud download finished successfully")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("❌ Bulk icloudpd timed out after 2 hours")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Bulk icloudpd failed with return code {e.returncode}")
            logger.error(f"Error output: {e.stderr}")
            return False
        except FileNotFoundError:
            logger.error("❌ icloudpd command not found. Please install icloudpd")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error running bulk icloudpd: {e}")
            return False
    
    def scan_and_update_db_bulk(self) -> Dict[str, int]:
        """Scan download directory and update database with new media in bulk"""
        results = {
            'total_files': 0,
            'new_files': 0,
            'existing_files': 0,
            'errors': 0
        }
        
        try:
            download_dir = Path(self.config.directory)
            if not download_dir.exists():
                logger.error(f"Download directory does not exist: {download_dir}")
                return results
            
            # Get all media files
            media_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', 
                              '.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm'}
            
            all_files = []
            for ext in media_extensions:
                all_files.extend(download_dir.rglob(f"*{ext}"))
                all_files.extend(download_dir.rglob(f"*{ext.upper()}"))
            
            results['total_files'] = len(all_files)
            logger.info(f"Found {results['total_files']} media files in download directory")
            
            # Process files in batches
            batch_size = 100
            for i in range(0, len(all_files), batch_size):
                batch = all_files[i:i + batch_size]
                batch_results = self._process_file_batch(batch)
                
                results['new_files'] += batch_results['new_files']
                results['existing_files'] += batch_results['existing_files']
                results['errors'] += batch_results['errors']
                
                logger.info(f"Processed batch {i//batch_size + 1}: "
                          f"{batch_results['new_files']} new, "
                          f"{batch_results['existing_files']} existing, "
                          f"{batch_results['errors']} errors")
            
        except Exception as e:
            logger.error(f"Error scanning download directory: {e}")
            results['errors'] += 1
        
        return results
    
    def _process_file_batch(self, files: List[Path]) -> Dict[str, int]:
        """Process a batch of files for database updates"""
        batch_results = {
            'new_files': 0,
            'existing_files': 0,
            'errors': 0
        }
        
        for file_path in files:
            try:
                # Get file info
                stat = file_path.stat()
                file_size = stat.st_size
                file_mtime = datetime.fromtimestamp(stat.st_mtime)
                
                # Check if file already exists in database
                existing = self.db.get_media_by_filename(file_path.name)
                
                if existing:
                    # Update existing record
                    self.db.update_media_file(
                        file_path.name,
                        current_size=file_size,
                        last_updated=datetime.now().isoformat()
                    )
                    batch_results['existing_files'] += 1
                else:
                    # Add new record
                    self.db.add_media_file(
                        filename=file_path.name,
                        file_path=str(file_path),
                        file_size=file_size,
                        status='downloaded',
                        date_created=file_mtime.isoformat(),
                        last_updated=datetime.now().isoformat()
                    )
                    batch_results['new_files'] += 1
                    
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                batch_results['errors'] += 1
        
        return batch_results
    
    def get_bulk_sync_stats(self) -> Dict[str, Any]:
        """Get bulk synchronization statistics"""
        try:
            stats = {
                'total_downloaded': self.db.count_media_by_status('downloaded'),
                'total_synced_google': self.db.count_media_by_sync_status('synced_google', 'yes'),
                'total_synced_nas': self.db.count_media_by_sync_status('synced_nas', 'yes'),
                'total_compressed': self.db.count_media_by_compression_status(),
                'total_deleted': self.db.count_media_by_sync_status('deleted_icloud', 'yes'),
                'total_size_downloaded': self.db.get_total_size_by_status('downloaded'),
                'total_size_compressed': self.db.get_total_compressed_size()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting bulk sync statistics: {e}")
            return {}
    
    def run_bulk_sync(self, batch_size: int = 100, max_days: int = 0) -> bool:
        """Run complete bulk iCloud synchronization"""
        logger.info("Starting bulk iCloud synchronization...")
        
        # Validate configuration
        if not config_manager.validate_config():
            logger.error("Configuration validation failed")
            return False
        
        # Initialize database
        self.db.init_database()
        
        # Validate iCloud connection
        if not self.validate_icloud_connection():
            logger.warning("iCloud connection validation failed, but continuing with download attempt")
        
        # Run bulk icloudpd download
        if not self.run_bulk_icloudpd(batch_size, max_days):
            logger.error("Bulk iCloud download failed")
            return False
        
        # Scan and update database
        scan_results = self.scan_and_update_db_bulk()
        
        # Log results
        logger.info(f"Bulk iCloud sync completed:")
        logger.info(f"  Total files found: {scan_results['total_files']}")
        logger.info(f"  New files added: {scan_results['new_files']}")
        logger.info(f"  Existing files: {scan_results['existing_files']}")
        logger.info(f"  Errors: {scan_results['errors']}")
        
        # Get and log statistics
        stats = self.get_bulk_sync_stats()
        logger.info(f"Bulk iCloud sync statistics: {stats}")
        
        success = scan_results['errors'] == 0
        if success:
            logger.info("✅ Bulk iCloud synchronization completed successfully")
        else:
            logger.warning(f"⚠️ Bulk iCloud synchronization completed with {scan_results['errors']} errors")
        
        return success


def main():
    """Main bulk iCloud synchronization pipeline"""
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description='Bulk iCloud Synchronization')
    parser.add_argument('--batch-size', type=int, default=100, 
                       help='Batch size for processing (default: 100)')
    parser.add_argument('--max-days', type=int, default=0,
                       help='Maximum days to download (0 = all, default: 0)')
    parser.add_argument('--stats-only', action='store_true',
                       help='Only show statistics, do not download')
    
    args = parser.parse_args()
    
    logger.info("Starting bulk iCloud synchronization pipeline...")
    
    # Create bulk sync manager
    bulk_sync_manager = BulkICloudSyncManager()
    
    if args.stats_only:
        # Show statistics only
        stats = bulk_sync_manager.get_bulk_sync_stats()
        logger.info(f"Current bulk sync statistics: {stats}")
        return True
    
    # Run bulk synchronization
    success = bulk_sync_manager.run_bulk_sync(
        batch_size=args.batch_size,
        max_days=args.max_days
    )
    
    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
