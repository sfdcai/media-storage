#!/usr/bin/env python3
"""
Step 4: NAS Archive
Copies files from pixel sync folder to NAS archive folder
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
    """Execute Step 4: NAS Archive"""
    logger = setup_logger()
    config = Config()
    
    # Initialize components
    tracker = WorkflowTracker(config, logger)
    file_manager = FileManager(config, logger)
    supabase = SupabaseClient(config)
    
    # Start workflow tracking
    tracker.start_workflow()
    tracker.start_step(4, {'description': 'Copy files to NAS archive'})
    
    try:
        logger.info("=== Step 4: NAS Archive ===")
        
        # Get files in pixel sync folder (these should be verified files)
        pixel_sync_files = file_manager.get_files_in_folder(file_manager.pixel_sync_folder)
        
        if not pixel_sync_files:
            logger.info("No files in Pixel sync folder to archive")
            tracker.complete_step(4, success=True, result_data={'files_archived': 0})
            return True
        
        logger.info(f"Archiving {len(pixel_sync_files)} files to NAS")
        
        # Copy files to NAS archive
        archived_files = []
        for file_path in pixel_sync_files:
            try:
                # Copy file with workflow prefix
                archived_file = file_manager.copy_file_with_prefix(
                    file_path, file_manager.nas_archive_folder, 'nas_archive', 4
                )
                
                if archived_file:
                    archived_files.append(archived_file)
                    
                    # Verify file integrity
                    if file_manager.verify_file_integrity(file_path, archived_file):
                        # Update database
                        file_info = file_manager.get_file_info(archived_file)
                        file_hash = supabase.get_file_hash(str(archived_file))
                        supabase.record_file(
                            str(archived_file), 
                            file_info['size'], 
                            file_hash, 
                            'nas_archived',
                            {'step': 4, 'source_file': str(file_path)}
                        )
                        
                        # Add to workflow tracking
                        tracker.add_file_tracking(str(archived_file), 4, 'archived', file_info)
                        
                        logger.info(f"✅ Archived {file_path.name} to NAS")
                    else:
                        logger.error(f"❌ File integrity check failed for {file_path.name}")
                        tracker.add_file_tracking(str(file_path), 4, 'failed', {'error': 'Integrity check failed'})
                        
                        # Remove the corrupted copy
                        if archived_file.exists():
                            archived_file.unlink()
                        
                else:
                    logger.error(f"❌ Failed to archive {file_path.name}")
                    tracker.add_file_tracking(str(file_path), 4, 'failed', {'error': 'Copy failed'})
                    
            except Exception as e:
                logger.error(f"❌ Error archiving {file_path.name}: {e}")
                tracker.add_file_tracking(str(file_path), 4, 'failed', {'error': str(e)})
        
        # Update progress
        tracker.update_step_progress(4, len(archived_files), len(pixel_sync_files))
        
        # Check if we have any failed archives
        failed_count = len(pixel_sync_files) - len(archived_files)
        if failed_count > 0:
            error_msg = f"{failed_count} files failed to archive to NAS"
            logger.error(error_msg)
            tracker.complete_step(4, success=False, error_message=error_msg)
            return False
        
        # Complete step
        result_data = {
            'files_archived': len(archived_files),
            'files_failed': failed_count,
            'nas_archive_folder': str(file_manager.nas_archive_folder),
            'total_size_mb': sum(f.stat().st_size for f in archived_files) / (1024 * 1024)
        }
        
        tracker.complete_step(4, success=True, result_data=result_data)
        
        logger.info(f"✅ Step 4 completed: {len(archived_files)} files archived to NAS")
        return True
        
    except Exception as e:
        error_msg = f"Step 4 failed: {e}"
        logger.error(error_msg)
        tracker.complete_step(4, success=False, error_message=error_msg)
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
