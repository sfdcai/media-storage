#!/usr/bin/env python3
"""
Step 8: Cleanup
Cleans up temporary files and folders
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
    """Execute Step 8: Cleanup"""
    logger = setup_logger()
    config = Config()
    
    # Initialize components
    tracker = WorkflowTracker(config, logger)
    file_manager = FileManager(config, logger)
    supabase = SupabaseClient(config)
    
    # Start workflow tracking
    tracker.start_workflow()
    tracker.start_step(8, {'description': 'Clean up temporary files and folders'})
    
    try:
        logger.info("=== Step 8: Cleanup ===")
        
        # Get cleanup settings
        cleanup_hours = config.get('workflow.cleanup_after_hours', 24)
        
        # Clean up each workflow folder
        cleanup_results = {}
        total_cleaned = 0
        
        folders_to_clean = {
            'pixel_sync': file_manager.pixel_sync_folder,
            'processing': file_manager.processing_folder,
            'icloud_delete': file_manager.icloud_delete_folder
        }
        
        for folder_name, folder_path in folders_to_clean.items():
            try:
                cleaned_count = file_manager.cleanup_folder(folder_path, cleanup_hours)
                cleanup_results[folder_name] = cleaned_count
                total_cleaned += cleaned_count
                
                if cleaned_count > 0:
                    logger.info(f"✅ Cleaned {cleaned_count} old files from {folder_name} folder")
                else:
                    logger.info(f"ℹ️ No old files to clean in {folder_name} folder")
                    
            except Exception as e:
                logger.error(f"❌ Error cleaning {folder_name} folder: {e}")
                cleanup_results[folder_name] = -1  # Error indicator
        
        # Get final workflow status
        workflow_status = file_manager.get_workflow_status()
        
        # Update progress
        tracker.update_step_progress(8, total_cleaned, total_cleaned)
        
        # Complete step
        result_data = {
            'files_cleaned': total_cleaned,
            'cleanup_results': cleanup_results,
            'cleanup_hours': cleanup_hours,
            'final_workflow_status': workflow_status
        }
        
        tracker.complete_step(8, success=True, result_data=result_data)
        
        # Complete the entire workflow
        tracker.complete_workflow(success=True, summary={
            'total_files_cleaned': total_cleaned,
            'workflow_duration': tracker.tracking_data.get('total_duration_seconds', 0),
            'final_status': workflow_status
        })
        
        logger.info(f"✅ Step 8 completed: {total_cleaned} files cleaned up")
        logger.info("🎉 Workflow completed successfully!")
        
        # Print final status
        tracker.print_status()
        
        return True
        
    except Exception as e:
        error_msg = f"Step 8 failed: {e}"
        logger.error(error_msg)
        tracker.complete_step(8, success=False, error_message=error_msg)
        tracker.complete_workflow(success=False, summary={'error': error_msg})
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
