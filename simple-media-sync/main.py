#!/usr/bin/env python3
"""
Simple Media Sync - CLI tool for syncing media files
"""

import argparse
import sys
import os
from pathlib import Path

from logger import setup_logger
from config import Config
from supabase_client import SupabaseClient
from sync_manager import SyncManager
from compression import MediaCompressor
from nas_sync import NASSync
from icloud_manager import iCloudManager
from pixel_sync import PixelSync


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Simple Media Sync - Sync media files with external services"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Configure settings')
    config_parser.add_argument('--setup', action='store_true', help='Run initial setup')
    config_parser.add_argument('--show', action='store_true', help='Show current config')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync media files')
    sync_parser.add_argument('--source', help='Source directory path')
    sync_parser.add_argument('--dry-run', action='store_true', help='Show what would be synced without doing it')
    sync_parser.add_argument('--full-workflow', action='store_true', help='Run full workflow: download, compress, sync to NAS, sync to Pixel, delete from iCloud')
    sync_parser.add_argument('--skip-compression', action='store_true', help='Skip compression step')
    sync_parser.add_argument('--skip-nas', action='store_true', help='Skip NAS sync step')
    sync_parser.add_argument('--skip-pixel', action='store_true', help='Skip Pixel sync step')
    sync_parser.add_argument('--skip-icloud-delete', action='store_true', help='Skip iCloud deletion step')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show sync status')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test connections')
    test_parser.add_argument('--supabase', action='store_true', help='Test Supabase connection')
    test_parser.add_argument('--icloud', action='store_true', help='Test iCloud connection')
    test_parser.add_argument('--nas', action='store_true', help='Test NAS connection')
    test_parser.add_argument('--pixel', action='store_true', help='Test Pixel connection')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Setup logger
    logger = setup_logger()
    
    try:
        if args.command == 'config':
            handle_config(args, logger)
        elif args.command == 'sync':
            handle_sync(args, logger)
        elif args.command == 'status':
            handle_status(args, logger)
        elif args.command == 'test':
            handle_test(args, logger)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


def handle_config(args, logger):
    """Handle config commands"""
    config = Config()
    
    if args.setup:
        logger.info("Running initial setup...")
        config.setup()
    elif args.show:
        config.show()
    else:
        logger.info("Use --setup to configure or --show to view current config")


def handle_sync(args, logger):
    """Handle sync commands"""
    config = Config()
    supabase = SupabaseClient(config)
    sync_manager = SyncManager(config, supabase, logger)
    
    if args.dry_run:
        logger.info("Dry run mode - no files will be modified")
    
    if args.full_workflow:
        # Run full workflow: download from iCloud, compress, sync to NAS, sync to Pixel, delete from iCloud
        run_full_workflow(config, logger, args)
    else:
        # Regular sync
        sync_manager.sync(args.source, dry_run=args.dry_run)


def handle_status(args, logger):
    """Handle status commands"""
    config = Config()
    supabase = SupabaseClient(config)
    
    # Show sync status from Supabase
    status = supabase.get_sync_status()
    workflow_status = supabase.get_workflow_status()
    
    logger.info("=== Sync Status ===")
    logger.info(f"Last sync: {status.get('last_sync', 'Never')}")
    logger.info(f"Files synced: {status.get('files_count', 0)}")
    
    logger.info("\n=== Workflow Status ===")
    logger.info(f"Total files processed: {workflow_status.get('total_files', 0)}")
    logger.info(f"Files compressed: {workflow_status.get('compressed_files', 0)}")
    logger.info(f"Total size saved: {workflow_status.get('total_size_saved_mb', 0):.1f} MB")
    
    stages = workflow_status.get('workflow_stages', {})
    if stages:
        logger.info("\n=== Files by Stage ===")
        for stage, count in stages.items():
            logger.info(f"  {stage}: {count} files")


def handle_test(args, logger):
    """Handle test commands"""
    config = Config()
    
    if args.supabase:
        logger.info("Testing Supabase connection...")
        supabase = SupabaseClient(config)
        if supabase.test_connection():
            logger.info("✅ Supabase connection successful")
        else:
            logger.error("❌ Supabase connection failed")
    
    if args.icloud:
        logger.info("Testing iCloud connection...")
        icloud = iCloudManager(config, logger)
        if icloud.test_icloud_connection():
            logger.info("✅ iCloud connection successful")
        else:
            logger.error("❌ iCloud connection failed")
    
    if args.nas:
        logger.info("Testing NAS connection...")
        nas = NASSync(config, logger)
        if nas.nas_mount_path and Path(nas.nas_mount_path).exists():
            usage = nas.get_nas_usage()
            logger.info(f"✅ NAS connection successful - {usage['total_files']} files, {usage['total_size_mb']:.1f} MB")
        else:
            logger.error("❌ NAS connection failed")
    
    if args.pixel:
        logger.info("Testing Pixel connection...")
        pixel = PixelSync(config, logger)
        if pixel.test_pixel_connection():
            usage = pixel.get_pixel_usage()
            logger.info(f"✅ Pixel connection successful - {usage['total_files']} files, {usage['total_size_mb']:.1f} MB")
        else:
            logger.error("❌ Pixel connection failed")


def run_full_workflow(config, logger, args):
    """Run the complete media sync workflow: Download → Sync to NAS → Sync to Pixel → Compress → Delete from iCloud"""
    logger.info("=== Starting Full Media Sync Workflow ===")
    
    # Initialize components
    supabase = SupabaseClient(config)
    icloud = iCloudManager(config, logger)
    compressor = MediaCompressor(config, logger)
    nas = NASSync(config, logger)
    pixel = PixelSync(config, logger)
    
    dry_run = args.dry_run
    
    # Step 1: Download from iCloud
    logger.info("Step 1: Downloading from iCloud...")
    downloaded_files = icloud.download_from_icloud(dry_run=dry_run)
    logger.info(f"Downloaded {len(downloaded_files)} files from iCloud")
    
    if not downloaded_files:
        logger.info("No files downloaded from iCloud. Workflow complete.")
        return
    
    # Step 2: Process each downloaded file
    processed_files = []
    for file_path in downloaded_files:
        logger.info(f"\n--- Processing: {Path(file_path).name} ---")
        
        # Record initial file in database
        if not dry_run:
            file_hash = supabase.get_file_hash(file_path)
            file_size = Path(file_path).stat().st_size
            supabase.record_file(file_path, file_size, file_hash, 'downloaded')
        
        # Step 2a: Sync to NAS (if not skipped)
        nas_success = True
        if not args.skip_nas:
            logger.info("Syncing to NAS...")
            if nas.sync_to_nas(file_path, dry_run=dry_run):
                logger.info("✅ NAS sync successful")
                if not dry_run:
                    supabase.update_workflow_stage(file_path, 'nas_synced')
            else:
                logger.error("❌ NAS sync failed")
                nas_success = False
        else:
            logger.info("Skipping NAS sync")
        
        # Step 2b: Sync to Pixel (if not skipped and NAS was successful)
        pixel_success = True
        if not args.skip_pixel and nas_success:
            logger.info("Syncing to Pixel...")
            if pixel.sync_to_pixel(file_path, dry_run=dry_run):
                logger.info("✅ Pixel sync successful")
                if not dry_run:
                    supabase.update_workflow_stage(file_path, 'pixel_synced')
            else:
                logger.error("❌ Pixel sync failed")
                pixel_success = False
        else:
            logger.info("Skipping Pixel sync")
        
        # Step 2c: Compress (if enabled and not skipped)
        compressed_path = file_path
        compression_metadata = {}
        if not args.skip_compression and config.get('compression.enabled', True):
            logger.info("Compressing file...")
            original_size = Path(file_path).stat().st_size
            compressed_path = compressor.compress_file(file_path)
            
            if compressed_path != file_path:
                logger.info(f"File compressed: {Path(compressed_path).name}")
                compressed_size = Path(compressed_path).stat().st_size
                compression_ratio = (1 - compressed_size / original_size)
                
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
                
                if not dry_run:
                    supabase.record_compression(file_path, original_size, compressed_size, 
                                              compression_ratio, compression_metadata['quality_settings'])
                    supabase.update_workflow_stage(file_path, 'compressed', compression_metadata)
            else:
                logger.info("File not compressed (didn't meet criteria)")
                if not dry_run:
                    supabase.update_workflow_stage(file_path, 'compression_skipped')
        else:
            logger.info("Skipping compression")
            if not dry_run:
                supabase.update_workflow_stage(file_path, 'compression_skipped')
        
        # Step 2d: Delete from iCloud (if not skipped and both NAS and Pixel sync were successful)
        if not args.skip_icloud_delete and nas_success and pixel_success:
            logger.info("Deleting from iCloud...")
            if icloud.delete_from_icloud(file_path, dry_run=dry_run):
                logger.info("✅ iCloud deletion successful")
                if not dry_run:
                    supabase.update_workflow_stage(file_path, 'completed')
            else:
                logger.error("❌ iCloud deletion failed")
                if not dry_run:
                    supabase.update_workflow_stage(file_path, 'icloud_delete_failed')
        else:
            logger.info("Skipping iCloud deletion")
            if not dry_run:
                supabase.update_workflow_stage(file_path, 'icloud_delete_skipped')
        
        processed_files.append(file_path)
    
    # Final summary
    logger.info(f"\n=== Workflow Complete: Processed {len(processed_files)} files ===")
    
    if not dry_run:
        # Show final statistics
        workflow_status = supabase.get_workflow_status()
        logger.info(f"Total files processed: {workflow_status.get('total_files', 0)}")
        logger.info(f"Files compressed: {workflow_status.get('compressed_files', 0)}")
        logger.info(f"Total size saved: {workflow_status.get('total_size_saved_mb', 0):.1f} MB")


if __name__ == '__main__':
    main()
