#!/usr/bin/env python3
"""
Simple setup script for media sync workflow
"""

import json
import os
from pathlib import Path


def setup_config():
    """Interactive setup for configuration"""
    print("=== Media Sync Workflow Setup ===")
    
    config = {
        "supabase": {
            "url": input("Supabase URL: ").strip(),
            "key": input("Supabase API Key: ").strip(),
            "table_name": "media_files"
        },
        "icloud": {
            "username": input("iCloud username: ").strip(),
            "password": input("iCloud password: ").strip(),
            "download_dir": input("iCloud download directory: ").strip(),
            "icloudpd_path": "icloudpd",
            "trusted_device": False,
            "cookie_directory": "~/.pyiCloud",
            "interactive_mode": True
        },
        "workflow": {
            "incoming_folder": input("Incoming folder (default: ./incoming): ").strip() or "./incoming",
            "pixel_sync_folder": input("Pixel sync folder (default: ./pixel_sync): ").strip() or "./pixel_sync",
            "nas_archive_folder": input("NAS archive folder (default: ./nas_archive): ").strip() or "./nas_archive",
            "processing_folder": input("Processing folder (default: ./processing): ").strip() or "./processing",
            "icloud_delete_folder": input("iCloud delete folder (default: ./icloud_delete): ").strip() or "./icloud_delete",
            "pixel_batch_size": int(input("Pixel batch size (default: 5): ").strip() or "5")
        },
        "syncthing": {
            "api_url": input("Syncthing API URL (default: http://localhost:8384): ").strip() or "http://localhost:8384",
            "api_key": input("Syncthing API Key: ").strip(),
            "pixel_folder_id": input("Syncthing Pixel folder ID: ").strip(),
            "timeout_seconds": int(input("Sync timeout in seconds (default: 300): ").strip() or "300")
        },
        "compression": {
            "enabled": input("Enable compression? (y/n, default: y): ").strip().lower() != 'n',
            "strategy": "balanced",
            "compress_images": True,
            "compress_videos": True,
            "image_quality": 85,
            "video_quality": 28
        }
    }
    
    # Save configuration
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("\n✅ Configuration saved to config.json")
    return config


def create_folders():
    """Create workflow folders"""
    folders = [
        "./incoming",
        "./pixel_sync", 
        "./nas_archive",
        "./processing",
        "./icloud_delete"
    ]
    
    for folder in folders:
        Path(folder).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created folder: {folder}")


def main():
    """Main setup function"""
    print("Setting up Media Sync Workflow...")
    
    # Create folders
    print("\n1. Creating workflow folders...")
    create_folders()
    
    # Setup configuration
    print("\n2. Configuration setup...")
    config = setup_config()
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Test configuration: python test_setup.py")
    print("3. Run workflow: python workflow_orchestrator.py --workflow")


if __name__ == '__main__':
    main()
