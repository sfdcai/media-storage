#!/usr/bin/env python3
"""
Step 5: Processing
Moves files from pixel sync folder to processing folder
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
    """Execute Step 5: Processing"""
    logger = setup_logger()
    config = Config()
    
    # Initialize components
    tracker = WorkflowTracker(config, logger)
    file_manager = FileManager(config, logger)
    supabase = SupabaseClient(config)
    
    # Start workflow tracking
    tracker.start_workflow()
    tracker.start_step(5, {'description': 'Move files to processing folder'})
    
    try:
        logger.info("=== Step 5: Processing ===")
        
        # Get files in pixel sync folder (these should be verified and archived files)
        pixel_sync_files = file_manager.get_files_in_folder(file_manager.pixel_sync_folder)
        
        if not pixel_sync_files:
            logger.info("No files in Pixel sync folder to process")
            tracker.complete_step(5, success=True, result_data={'files_processed': 0})
            return True
        
        logger.info(f"Moving {len(pixel_sync_files)} files to processing folder")
        
        # Move files to processing folder
        processed_files = []
        for file_path in pixel_sync_files:
            try:
                # Move file with workflow prefix
                processed_file = file_manager.move_file_with_prefix(
                    file_path, file_manager.processing_folder, 'processing', 5
                )
                
                if processed_file:
                    processed_files.append(processed_file)
                    
                    # Update database
                    file_info = file_manager.get_file_info(processed_file)
                    file_hash = supabase.get_file_hash(str(processed_file))
                    supabase.update_workflow_stage(
                        str(processed_file), 
                        'processing_ready',
                        {'step': 5, 'source_file': str(file_path)}
                    )
                    
                    # Add to workflow tracking
                    tracker.add_file_tracking(str(processed_file), 5, 'moved_to_processing', file_info)
                    
                    logger.info(f"✅ Moved {file_path.name} to processing folder")
                else:
                    logger.error(f"❌ Failed to move {file_path.name}")
                    tracker.add_file_tracking(str(file_path), 5, 'failed', {'error': 'Move failed'})
                    
            except Exception as e:
                logger.error(f"❌ Error processing {file_path.name}: {e}")
                tracker.add_file_tracking(str(file_path), 5, 'failed', {'error': str(e)})
        
        # Update progress
        tracker.update_step_progress(5, len(processed_files), len(pixel_sync_files))
        
        # Check if we have any failed moves
        failed_count = len(pixel_sync_files) - len(processed_files)
        if failed_count > 0:
            error_msg = f"{failed_count} files failed to move to processing folder"
            logger.error(error_msg)
            tracker.complete_step(5, success=False, error_message=error_msg)
            return False
        
        # Complete step
        result_data = {
            'files_processed': len(processed_files),
            'files_failed': failed_count,
            'processing_folder': str(file_manager.processing_folder),
            'total_size_mb': sum(f.stat().st_size for f in processed_files) / (1024 * 1024)
        }
        
        tracker.complete_step(5, success=True, result_data=result_data)
        
        logger.info(f"✅ Step 5 completed: {len(processed_files)} files ready for compression")
        return True
        
    except Exception as e:
        error_msg = f"Step 5 failed: {e}"
        logger.error(error_msg)
        tracker.complete_step(5, success=False, error_message=error_msg)
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
