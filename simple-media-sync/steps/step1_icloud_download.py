#!/usr/bin/env python3
"""
Step 1: iCloud Download
Downloads files from iCloud to the incoming folder
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config import Config
from logger import setup_logger
from icloud_manager import iCloudManager
from file_manager import FileManager
from workflow_tracker import WorkflowTracker
from supabase_client import SupabaseClient


def main():
    """Execute Step 1: iCloud Download"""
    logger = setup_logger()
    config = Config()
    
    # Initialize components
    tracker = WorkflowTracker(config, logger)
    file_manager = FileManager(config, logger)
    icloud = iCloudManager(config, logger)
    supabase = SupabaseClient(config)
    
    # Start workflow tracking
    tracker.start_workflow()
    tracker.start_step(1, {'description': 'Download files from iCloud'})
    
    try:
        logger.info("=== Step 1: iCloud Download ===")
        
        # Check if iCloud is configured
        if not config.get('icloud.username') or not config.get('icloud.download_dir'):
            error_msg = "iCloud credentials not configured"
            logger.error(error_msg)
            tracker.complete_step(1, success=False, error_message=error_msg)
            return False
        
        # Download files from iCloud
        logger.info("Downloading files from iCloud...")
        downloaded_files = icloud.download_from_icloud(dry_run=False)
        
        if not downloaded_files:
            logger.info("No new files downloaded from iCloud")
            tracker.complete_step(1, success=True, result_data={'files_downloaded': 0})
            return True
        
        logger.info(f"Downloaded {len(downloaded_files)} files from iCloud")
        
        # Move files to incoming folder with tracking
        incoming_files = []
        for file_path in downloaded_files:
            source_path = Path(file_path)
            destination = file_manager.incoming_folder / source_path.name
            
            # Move file to incoming folder
            try:
                destination.parent.mkdir(parents=True, exist_ok=True)
                source_path.rename(destination)
                incoming_files.append(destination)
                
                # Track file in database
                file_info = file_manager.get_file_info(destination)
                file_hash = supabase.get_file_hash(str(destination))
                supabase.record_file(
                    str(destination), 
                    file_info['size'], 
                    file_hash, 
                    'downloaded',
                    {'step': 1, 'source': 'icloud'}
                )
                
                # Add to workflow tracking
                tracker.add_file_tracking(str(destination), 1, 'downloaded', file_info)
                
                logger.info(f"✅ Moved {source_path.name} to incoming folder")
                
            except Exception as e:
                logger.error(f"❌ Failed to move {source_path.name}: {e}")
                tracker.add_file_tracking(str(source_path), 1, 'failed', {'error': str(e)})
        
        # Update progress
        tracker.update_step_progress(1, len(incoming_files), len(downloaded_files))
        
        # Complete step
        result_data = {
            'files_downloaded': len(downloaded_files),
            'files_moved_to_incoming': len(incoming_files),
            'incoming_folder': str(file_manager.incoming_folder)
        }
        
        tracker.complete_step(1, success=True, result_data=result_data)
        
        logger.info(f"✅ Step 1 completed: {len(incoming_files)} files ready for processing")
        return True
        
    except Exception as e:
        error_msg = f"Step 1 failed: {e}"
        logger.error(error_msg)
        tracker.complete_step(1, success=False, error_message=error_msg)
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
