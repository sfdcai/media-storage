#!/usr/bin/env python3
"""
Step 6: Compression
Compresses media files in the processing folder
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
from compression import MediaCompressor
from supabase_client import SupabaseClient


def main():
    """Execute Step 6: Compression"""
    logger = setup_logger()
    config = Config()
    
    # Initialize components
    tracker = WorkflowTracker(config, logger)
    file_manager = FileManager(config, logger)
    compressor = MediaCompressor(config, logger)
    supabase = SupabaseClient(config)
    
    # Start workflow tracking
    tracker.start_workflow()
    tracker.start_step(6, {'description': 'Compress media files'})
    
    try:
        logger.info("=== Step 6: Compression ===")
        
        # Check if compression is enabled
        if not config.get('compression.enabled', True):
            logger.info("Compression is disabled, skipping step")
            tracker.complete_step(6, success=True, result_data={'compression_disabled': True})
            return True
        
        # Get files in processing folder
        processing_files = file_manager.get_files_in_folder(file_manager.processing_folder)
        
        if not processing_files:
            logger.info("No files in processing folder to compress")
            tracker.complete_step(6, success=True, result_data={'files_compressed': 0})
            return True
        
        logger.info(f"Compressing {len(processing_files)} files in processing folder")
        
        # Compress files
        compressed_files = []
        skipped_files = []
        failed_files = []
        
        for file_path in processing_files:
            try:
                # Check if file should be compressed
                if not compressor.should_compress_file(str(file_path)):
                    skipped_files.append(file_path)
                    logger.info(f"⏭️ Skipped compression for {file_path.name}")
                    
                    # Update database
                    supabase.update_workflow_stage(
                        str(file_path), 
                        'compression_skipped',
                        {'step': 6, 'reason': 'Does not meet compression criteria'}
                    )
                    
                    # Add to workflow tracking
                    tracker.add_file_tracking(str(file_path), 6, 'skipped', {'reason': 'Does not meet criteria'})
                    continue
                
                # Get original file info
                original_info = file_manager.get_file_info(file_path)
                original_size = original_info['size']
                
                # Compress file
                logger.info(f"Compressing {file_path.name}...")
                compressed_path = compressor.compress_file(str(file_path))
                
                if compressed_path != str(file_path):
                    # File was compressed
                    compressed_file = Path(compressed_path)
                    compressed_files.append(compressed_file)
                    
                    # Get compressed file info
                    compressed_info = file_manager.get_file_info(compressed_file)
                    compressed_size = compressed_info['size']
                    compression_ratio = (1 - compressed_size / original_size)
                    
                    # Update database with compression metadata
                    compression_metadata = {
                        'original_size': original_size,
                        'compressed_size': compressed_size,
                        'compression_ratio': compression_ratio,
                        'quality_settings': {
                            'strategy': config.get('compression.strategy', 'balanced'),
                            'image_quality': compressor.image_quality,
                            'video_quality': compressor.video_quality
                        }
                    }
                    
                    supabase.record_compression(
                        str(file_path), original_size, compressed_size, 
                        compression_ratio, compression_metadata['quality_settings']
                    )
                    
                    supabase.update_workflow_stage(
                        str(compressed_file), 
                        'compressed',
                        compression_metadata
                    )
                    
                    # Add to workflow tracking
                    tracker.add_file_tracking(str(compressed_file), 6, 'compressed', {
                        'original_size': original_size,
                        'compressed_size': compressed_size,
                        'compression_ratio': compression_ratio
                    })
                    
                    logger.info(f"✅ Compressed {file_path.name} ({compression_ratio*100:.1f}% size reduction)")
                    
                    # Remove original file if compression was successful
                    try:
                        file_path.unlink()
                        logger.info(f"🗑️ Removed original file: {file_path.name}")
                    except Exception as e:
                        logger.warning(f"Could not remove original file {file_path.name}: {e}")
                        
                else:
                    # File was not compressed (didn't meet criteria)
                    skipped_files.append(file_path)
                    logger.info(f"⏭️ {file_path.name} not compressed (didn't meet criteria)")
                    
                    # Update database
                    supabase.update_workflow_stage(
                        str(file_path), 
                        'compression_skipped',
                        {'step': 6, 'reason': 'Compression did not meet criteria'}
                    )
                    
                    # Add to workflow tracking
                    tracker.add_file_tracking(str(file_path), 6, 'skipped', {'reason': 'Did not meet criteria'})
                    
            except Exception as e:
                logger.error(f"❌ Error compressing {file_path.name}: {e}")
                failed_files.append(file_path)
                
                # Update database
                supabase.update_workflow_stage(
                    str(file_path), 
                    'compression_failed',
                    {'step': 6, 'error': str(e)}
                )
                
                # Add to workflow tracking
                tracker.add_file_tracking(str(file_path), 6, 'failed', {'error': str(e)})
        
        # Update progress
        total_processed = len(compressed_files) + len(skipped_files) + len(failed_files)
        tracker.update_step_progress(6, total_processed, len(processing_files))
        
        # Check if we have any failed compressions
        if failed_files:
            error_msg = f"{len(failed_files)} files failed to compress"
            logger.error(error_msg)
            tracker.complete_step(6, success=False, error_message=error_msg)
            return False
        
        # Complete step
        result_data = {
            'files_compressed': len(compressed_files),
            'files_skipped': len(skipped_files),
            'files_failed': len(failed_files),
            'total_size_saved_mb': sum(
                (f.stat().st_size * 0.3) for f in compressed_files  # Estimate 30% average savings
            ) / (1024 * 1024)
        }
        
        tracker.complete_step(6, success=True, result_data=result_data)
        
        logger.info(f"✅ Step 6 completed: {len(compressed_files)} files compressed, {len(skipped_files)} skipped")
        return True
        
    except Exception as e:
        error_msg = f"Step 6 failed: {e}"
        logger.error(error_msg)
        tracker.complete_step(6, success=False, error_message=error_msg)
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
