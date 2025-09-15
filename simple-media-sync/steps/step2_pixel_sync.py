#!/usr/bin/env python3
"""
Step 2: Pixel Sync
Selects files from incoming folder and moves them to pixel sync folder
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
from supabase_client import SupabaseClient


def main():
    """Execute Step 2: Pixel Sync"""
    logger = setup_logger()
    config = Config()
    
    # Initialize components
    tracker = WorkflowTracker(config, logger)
    file_manager = FileManager(config, logger)
    supabase = SupabaseClient(config)
    
    # Start workflow tracking
    tracker.start_workflow()
    tracker.start_step(2, {'description': 'Move files to Pixel sync folder'})
    
    try:
        logger.info("=== Step 2: Pixel Sync ===")
        
        # Get batch size from config
        batch_size = config.get('workflow.pixel_batch_size', 5)
        
        # Select files for Pixel sync
        logger.info(f"Selecting {batch_size} files for Pixel sync...")
        selected_files = file_manager.select_files_for_pixel_sync(batch_size)
        
        if not selected_files:
            logger.info("No files available for Pixel sync")
            tracker.complete_step(2, success=True, result_data={'files_selected': 0})
            return True
        
        logger.info(f"Selected {len(selected_files)} files for Pixel sync")
        
        # Move files to pixel sync folder
        moved_files = []
        for file_path in selected_files:
            try:
                # Move file with workflow prefix
                moved_file = file_manager.move_file_with_prefix(
                    file_path, file_manager.pixel_sync_folder, 'pixel_sync', 2
                )
                
                if moved_file:
                    moved_files.append(moved_file)
                    
                    # Update database
                    file_info = file_manager.get_file_info(moved_file)
                    file_hash = supabase.get_file_hash(str(moved_file))
                    supabase.update_workflow_stage(
                        str(moved_file), 
                        'pixel_sync_ready',
                        {'step': 2, 'original_path': str(file_path)}
                    )
                    
                    # Add to workflow tracking
                    tracker.add_file_tracking(str(moved_file), 2, 'moved_to_pixel_sync', file_info)
                    
                    logger.info(f"✅ Moved {file_path.name} to Pixel sync folder")
                else:
                    logger.error(f"❌ Failed to move {file_path.name}")
                    tracker.add_file_tracking(str(file_path), 2, 'failed', {'error': 'Move failed'})
                    
            except Exception as e:
                logger.error(f"❌ Error processing {file_path.name}: {e}")
                tracker.add_file_tracking(str(file_path), 2, 'failed', {'error': str(e)})
        
        # Update progress
        tracker.update_step_progress(2, len(moved_files), len(selected_files))
        
        # Complete step
        result_data = {
            'files_selected': len(selected_files),
            'files_moved': len(moved_files),
            'pixel_sync_folder': str(file_manager.pixel_sync_folder),
            'batch_size': batch_size
        }
        
        tracker.complete_step(2, success=True, result_data=result_data)
        
        logger.info(f"✅ Step 2 completed: {len(moved_files)} files ready for Syncthing")
        return True
        
    except Exception as e:
        error_msg = f"Step 2 failed: {e}"
        logger.error(error_msg)
        tracker.complete_step(2, success=False, error_message=error_msg)
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
