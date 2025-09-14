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
    sync_parser.add_argument('--full-workflow', action='store_true', help='Run full workflow: download, compress, sync to NAS, delete from iCloud')
    sync_parser.add_argument('--skip-compression', action='store_true', help='Skip compression step')
    sync_parser.add_argument('--skip-nas', action='store_true', help='Skip NAS sync step')
    sync_parser.add_argument('--skip-icloud-delete', action='store_true', help='Skip iCloud deletion step')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show sync status')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test connections')
    test_parser.add_argument('--supabase', action='store_true', help='Test Supabase connection')
    test_parser.add_argument('--icloud', action='store_true', help='Test iCloud connection')
    test_parser.add_argument('--nas', action='store_true', help='Test NAS connection')
    
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
        # Run full workflow: download from iCloud, compress, sync to NAS, delete from iCloud
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
    logger.info(f"Last sync: {status.get('last_sync', 'Never')}")
    logger.info(f"Files synced: {status.get('files_count', 0)}")


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


def run_full_workflow(config, logger, args):
    """Run the complete media sync workflow"""
    logger.info("=== Starting Full Media Sync Workflow ===")
    
    # Initialize components
    supabase = SupabaseClient(config)
    icloud = iCloudManager(config, logger)
    compressor = MediaCompressor(logger)
    nas = NASSync(config, logger)
    
    dry_run = args.dry_run
    
    # Step 1: Download from iCloud
    logger.info("Step 1: Downloading from iCloud...")
    downloaded_files = icloud.download_from_icloud(dry_run=dry_run)
    logger.info(f"Downloaded {len(downloaded_files)} files from iCloud")
    
    # Step 2: Process each downloaded file
    processed_files = []
    for file_path in downloaded_files:
        logger.info(f"Processing: {file_path}")
        
        # Step 2a: Compress (if enabled and not skipped)
        if not args.skip_compression and config.get('compression.enabled', True):
            logger.info("Compressing file...")
            compressed_path = compressor.compress_file(file_path)
            if compressed_path != file_path:
                logger.info(f"File compressed: {compressed_path}")
                file_to_sync = compressed_path
            else:
                file_to_sync = file_path
        else:
            file_to_sync = file_path
        
        # Step 2b: Sync to NAS (if not skipped)
        if not args.skip_nas:
            logger.info("Syncing to NAS...")
            if nas.sync_to_nas(file_to_sync, dry_run=dry_run):
                logger.info("✅ NAS sync successful")
                
                # Step 2c: Record in Supabase
                if not dry_run:
                    file_hash = supabase.get_file_hash(file_to_sync)
                    file_size = Path(file_to_sync).stat().st_size
                    supabase.record_file(file_to_sync, file_size, file_hash)
                
                # Step 2d: Delete from iCloud (if not skipped)
                if not args.skip_icloud_delete:
                    logger.info("Deleting from iCloud...")
                    if icloud.delete_from_icloud(file_path, dry_run=dry_run):
                        logger.info("✅ iCloud deletion successful")
                    else:
                        logger.error("❌ iCloud deletion failed")
                
                processed_files.append(file_path)
            else:
                logger.error("❌ NAS sync failed, skipping iCloud deletion")
        else:
            logger.info("Skipping NAS sync")
            processed_files.append(file_path)
    
    logger.info(f"=== Workflow Complete: Processed {len(processed_files)} files ===")


if __name__ == '__main__':
    main()
