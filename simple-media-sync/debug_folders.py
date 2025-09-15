#!/usr/bin/env python3
"""
Debug script to check folder contents
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.append('.')

from config_loader import Config

def main():
    """Check folder contents"""
    config = Config()
    
    print("=== Folder Contents Debug ===")
    
    # Check incoming folder
    incoming_folder = config.get('workflow.incoming_folder', './incoming')
    incoming_path = Path(incoming_folder)
    
    print(f"\nIncoming folder: {incoming_path}")
    print(f"Exists: {incoming_path.exists()}")
    
    if incoming_path.exists():
        files = list(incoming_path.glob('*'))
        print(f"Files found: {len(files)}")
        for file_path in files[:10]:  # Show first 10 files
            print(f"  - {file_path.name} ({file_path.stat().st_size} bytes)")
        if len(files) > 10:
            print(f"  ... and {len(files) - 10} more files")
    else:
        print("Incoming folder does not exist!")
    
    # Check pixel sync folder
    pixel_sync_folder = config.get('workflow.pixel_sync_folder', './pixel_sync')
    pixel_sync_path = Path(pixel_sync_folder)
    
    print(f"\nPixel sync folder: {pixel_sync_path}")
    print(f"Exists: {pixel_sync_path.exists()}")
    
    if pixel_sync_path.exists():
        files = list(pixel_sync_path.glob('*'))
        print(f"Files found: {len(files)}")
        for file_path in files[:10]:
            print(f"  - {file_path.name}")
    
    # Check iCloud download directory
    icloud_download_dir = config.get('icloud.download_dir', '')
    if icloud_download_dir:
        icloud_path = Path(icloud_download_dir)
        print(f"\niCloud download directory: {icloud_path}")
        print(f"Exists: {icloud_path.exists()}")
        
        if icloud_path.exists():
            files = list(icloud_path.glob('*'))
            print(f"Files found: {len(files)}")
            for file_path in files[:10]:
                print(f"  - {file_path.name} ({file_path.stat().st_size} bytes)")

if __name__ == '__main__':
    main()
