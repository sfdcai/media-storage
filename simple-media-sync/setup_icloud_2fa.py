#!/usr/bin/env python3
"""
iCloud 2FA Setup Script
This script helps you set up 2FA authentication for iCloud
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.append('.')

from config_loader import Config
from logger import setup_logger
from icloud_manager import iCloudManager


def main():
    """Setup iCloud 2FA authentication"""
    logger = setup_logger()
    config = Config()
    
    logger.info("=== iCloud 2FA Setup ===")
    
    # Check if iCloud is configured
    if not config.get('icloud.username'):
        logger.error("iCloud username not configured in config.json")
        logger.info("Please run: python3 setup.py")
        return False
    
    # Initialize iCloud manager
    icloud = iCloudManager(config, logger)
    
    logger.info(f"Setting up 2FA for: {config.get('icloud.username')}")
    logger.info("This will:")
    logger.info("1. Prompt you for your iCloud password")
    logger.info("2. Prompt you for a 2FA code from your trusted device")
    logger.info("3. Save authentication cookies for future use")
    logger.info("")
    
    # Confirm setup
    try:
        confirm = input("Continue with 2FA setup? (y/N): ").strip().lower()
        if confirm != 'y':
            logger.info("2FA setup cancelled")
            return False
    except KeyboardInterrupt:
        logger.info("\n2FA setup cancelled")
        return False
    
    # Setup 2FA
    logger.info("Starting 2FA setup...")
    success = icloud.setup_2fa_authentication()
    
    if success:
        logger.info("✅ 2FA setup completed successfully!")
        logger.info("Your device is now trusted and you won't need to enter 2FA codes again")
        
        # Update config to mark device as trusted
        try:
            import json
            config_file = Path('config.json')
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                config_data['icloud']['trusted_device'] = True
                
                with open(config_file, 'w') as f:
                    json.dump(config_data, f, indent=2)
                
                logger.info("✅ Updated config.json to mark device as trusted")
        except Exception as e:
            logger.warning(f"Could not update config.json: {e}")
            logger.info("You may need to manually set 'trusted_device': true in config.json")
        
        return True
    else:
        logger.error("❌ 2FA setup failed")
        logger.info("Common issues:")
        logger.info("- Wrong password")
        logger.info("- Wrong 2FA code")
        logger.info("- Network connectivity issues")
        logger.info("- iCloud account locked")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
