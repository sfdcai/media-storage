#!/usr/bin/env python3
"""
Test setup and configuration
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.append('.')

from config_loader import Config
from logger import setup_logger
from icloud_manager import iCloudManager


def test_config():
    """Test configuration loading"""
    print("Testing configuration...")
    
    try:
        config = Config()
        print("✅ Config loaded successfully")
        
        # Test key configurations
        supabase_url = config.get('supabase.url')
        icloud_username = config.get('icloud.username')
        syncthing_api = config.get('syncthing.api_key')
        
        if supabase_url:
            print("✅ Supabase URL configured")
        else:
            print("⚠️ Supabase URL not configured")
        
        if icloud_username:
            print("✅ iCloud username configured")
            trusted_device = config.get('icloud.trusted_device', False)
            if trusted_device:
                print("✅ iCloud device is trusted (2FA setup complete)")
            else:
                print("⚠️ iCloud device not trusted (2FA setup needed)")
        else:
            print("⚠️ iCloud username not configured")
        
        if syncthing_api:
            print("✅ Syncthing API key configured")
        else:
            print("⚠️ Syncthing API key not configured")
        
        return True
        
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False


def test_imports():
    """Test importing all modules"""
    print("\nTesting module imports...")
    
    modules = [
        'syncthing_client',
        'file_manager', 
        'workflow_tracker',
        'supabase_client',
        'compression',
        'icloud_manager'
    ]
    
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module} imported successfully")
        except Exception as e:
            print(f"❌ {module} import failed: {e}")
            return False
    
    return True


def test_step_files():
    """Test step files exist"""
    print("\nTesting step files...")
    
    steps_dir = Path('steps')
    if not steps_dir.exists():
        print("❌ Steps directory not found")
        return False
    
    step_files = [
        'step1_icloud_download.py',
        'step2_pixel_sync.py', 
        'step3_pixel_verification.py',
        'step4_nas_archive.py',
        'step5_processing.py',
        'step6_compression.py',
        'step7_icloud_delete.py',
        'step8_cleanup.py'
    ]
    
    for step_file in step_files:
        step_path = steps_dir / step_file
        if step_path.exists():
            print(f"✅ {step_file} exists")
        else:
            print(f"❌ {step_file} not found")
            return False
    
    return True


def test_icloud_2fa():
    """Test iCloud 2FA setup"""
    print("Testing iCloud 2FA setup...")
    
    try:
        config = Config()
        logger = setup_logger()
        icloud = iCloudManager(config, logger)
        
        # Check if iCloud is configured
        if not config.get('icloud.username'):
            print("⚠️ iCloud username not configured - skipping 2FA test")
            return True
        
        # Check if device is trusted
        if config.get('icloud.trusted_device', False):
            print("✅ iCloud device is already trusted")
            
            # Test connection
            if icloud.test_icloud_connection():
                print("✅ iCloud connection test successful")
                return True
            else:
                print("❌ iCloud connection test failed")
                return False
        else:
            print("⚠️ iCloud device not trusted - 2FA setup needed")
            print("Run: python3 setup_icloud_2fa.py")
            return False
            
    except Exception as e:
        print(f"❌ iCloud 2FA test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=== Media Sync Workflow Test ===")
    
    tests = [
        test_config,
        test_imports,
        test_step_files,
        test_icloud_2fa
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 All tests passed! Setup is ready.")
        print("\nYou can now run:")
        print("  python workflow_orchestrator.py --workflow")
        print("  python steps/step1_icloud_download.py")
    else:
        print("❌ Some tests failed. Please check the setup.")
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
