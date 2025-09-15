#!/usr/bin/env python3
"""
Step 3: Pixel Verification
Verifies that files have been synced to Pixel device via Syncthing
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config_loader import Config
from logger import setup_logger
from file_manager import FileManager
from workflow_tracker import WorkflowTracker
from syncthing_client import SyncthingClient
from supabase_client import SupabaseClient


def main():
    """Execute Step 3: Pixel Verification"""
    logger = setup_logger()
    config = Config()
    
    # Initialize components
    tracker = WorkflowTracker(config, logger)
    file_manager = FileManager(config, logger)
    syncthing = SyncthingClient(config, logger)
    supabase = SupabaseClient(config)
    
    # Start workflow tracking
    tracker.start_workflow()
    tracker.start_step(3, {'description': 'Verify files synced to Pixel via Syncthing'})
    
    try:
        logger.info("=== Step 3: Pixel Verification ===")
        
        # Test Syncthing connection
        if not syncthing.test_connection():
            error_msg = "Cannot connect to Syncthing API"
            logger.error(error_msg)
            tracker.complete_step(3, success=False, error_message=error_msg)
            return False
        
        # Check if Pixel device is connected
        if not syncthing.is_pixel_connected():
            error_msg = "Pixel device is not connected to Syncthing"
            logger.error(error_msg)
            tracker.complete_step(3, success=False, error_message=error_msg)
            return False
        
        # Get files in pixel sync folder
        pixel_sync_files = file_manager.get_files_in_folder(file_manager.pixel_sync_folder)
        
        if not pixel_sync_files:
            logger.info("No files in Pixel sync folder to verify")
            tracker.complete_step(3, success=True, result_data={'files_verified': 0})
            return True
        
        logger.info(f"Verifying {len(pixel_sync_files)} files in Pixel sync folder")
        
        # Get sync timeout from config
        timeout = config.get('syncthing.timeout_seconds', 300)
        
        # Wait for files to sync
        file_paths = [str(f) for f in pixel_sync_files]
        sync_results = syncthing.wait_for_files_sync(file_paths, timeout)
        
        # Process results
        verified_files = []
        failed_files = []
        
        for file_path, synced in sync_results.items():
            file_obj = Path(file_path)
            
            if synced:
                verified_files.append(file_obj)
                
                # Update database
                supabase.update_workflow_stage(
                    str(file_obj), 
                    'pixel_verified',
                    {'step': 3, 'syncthing_verified': True}
                )
                
                # Add to workflow tracking
                tracker.add_file_tracking(str(file_obj), 3, 'verified', {
                    'syncthing_verified': True,
                    'sync_time': timeout
                })
                
                logger.info(f"✅ {file_obj.name} verified as synced to Pixel")
            else:
                failed_files.append(file_obj)
                
                # Update database
                supabase.update_workflow_stage(
                    str(file_obj), 
                    'pixel_verification_failed',
                    {'step': 3, 'syncthing_verified': False, 'error': 'Sync timeout'}
                )
                
                # Add to workflow tracking
                tracker.add_file_tracking(str(file_obj), 3, 'failed', {
                    'syncthing_verified': False,
                    'error': 'Sync timeout'
                })
                
                logger.error(f"❌ {file_obj.name} failed to sync to Pixel")
        
        # Update progress
        tracker.update_step_progress(3, len(verified_files), len(pixel_sync_files))
        
        # Check if we have any failed files
        if failed_files:
            error_msg = f"{len(failed_files)} files failed to sync to Pixel"
            logger.error(error_msg)
            tracker.complete_step(3, success=False, error_message=error_msg)
            return False
        
        # Complete step
        result_data = {
            'files_verified': len(verified_files),
            'files_failed': len(failed_files),
            'sync_timeout': timeout,
            'pixel_connected': True
        }
        
        tracker.complete_step(3, success=True, result_data=result_data)
        
        logger.info(f"✅ Step 3 completed: {len(verified_files)} files verified as synced to Pixel")
        return True
        
    except Exception as e:
        error_msg = f"Step 3 failed: {e}"
        logger.error(error_msg)
        tracker.complete_step(3, success=False, error_message=error_msg)
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
