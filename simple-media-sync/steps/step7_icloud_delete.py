#!/usr/bin/env python3
"""
Step 7: iCloud Delete
Moves files to iCloud delete folder for album creation and deletion
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config import Config
from logger import setup_logger
from file_manager import FileManager
from workflow_tracker import WorkflowTracker
from supabase_client import SupabaseClient


def main():
    """Execute Step 7: iCloud Delete"""
    logger = setup_logger()
    config = Config()
    
    # Initialize components
    tracker = WorkflowTracker(config, logger)
    file_manager = FileManager(config, logger)
    supabase = SupabaseClient(config)
    
    # Start workflow tracking
    tracker.start_workflow()
    tracker.start_step(7, {'description': 'Move files to iCloud delete folder'})
    
    try:
        logger.info("=== Step 7: iCloud Delete ===")
        
        # Get files in processing folder (these should be compressed files)
        processing_files = file_manager.get_files_in_folder(file_manager.processing_folder)
        
        if not processing_files:
            logger.info("No files in processing folder to move for deletion")
            tracker.complete_step(7, success=True, result_data={'files_moved_for_deletion': 0})
            return True
        
        logger.info(f"Moving {len(processing_files)} files to iCloud delete folder")
        
        # Move files to iCloud delete folder
        deleted_files = []
        for file_path in processing_files:
            try:
                # Move file with workflow prefix
                deleted_file = file_manager.move_file_with_prefix(
                    file_path, file_manager.icloud_delete_folder, 'icloud_delete', 7
                )
                
                if deleted_file:
                    deleted_files.append(deleted_file)
                    
                    # Update database
                    file_info = file_manager.get_file_info(deleted_file)
                    file_hash = supabase.get_file_hash(str(deleted_file))
                    supabase.update_workflow_stage(
                        str(deleted_file), 
                        'icloud_delete_ready',
                        {'step': 7, 'source_file': str(file_path), 'ready_for_album_creation': True}
                    )
                    
                    # Add to workflow tracking
                    tracker.add_file_tracking(str(deleted_file), 7, 'moved_for_deletion', file_info)
                    
                    logger.info(f"✅ Moved {file_path.name} to iCloud delete folder")
                else:
                    logger.error(f"❌ Failed to move {file_path.name}")
                    tracker.add_file_tracking(str(file_path), 7, 'failed', {'error': 'Move failed'})
                    
            except Exception as e:
                logger.error(f"❌ Error moving {file_path.name}: {e}")
                tracker.add_file_tracking(str(file_path), 7, 'failed', {'error': str(e)})
        
        # Update progress
        tracker.update_step_progress(7, len(deleted_files), len(processing_files))
        
        # Check if we have any failed moves
        failed_count = len(processing_files) - len(deleted_files)
        if failed_count > 0:
            error_msg = f"{failed_count} files failed to move to iCloud delete folder"
            logger.error(error_msg)
            tracker.complete_step(7, success=False, error_message=error_msg)
            return False
        
        # Complete step
        result_data = {
            'files_moved_for_deletion': len(deleted_files),
            'files_failed': failed_count,
            'icloud_delete_folder': str(file_manager.icloud_delete_folder),
            'total_size_mb': sum(f.stat().st_size for f in deleted_files) / (1024 * 1024),
            'ready_for_album_creation': True
        }
        
        tracker.complete_step(7, success=True, result_data=result_data)
        
        logger.info(f"✅ Step 7 completed: {len(deleted_files)} files ready for iCloud deletion")
        logger.info("📝 Next: Create 'To Delete' album in iCloud and move files to it")
        return True
        
    except Exception as e:
        error_msg = f"Step 7 failed: {e}"
        logger.error(error_msg)
        tracker.complete_step(7, success=False, error_message=error_msg)
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
