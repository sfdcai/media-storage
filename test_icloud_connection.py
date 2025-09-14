#!/usr/bin/env python3
"""
Test iCloud Connection Script
Tests iCloud authentication and prompts for 2FA if needed
"""

import os
import sys
from pathlib import Path

# Add the project directory to Python path
sys.path.insert(0, '/opt/media-pipeline')

def test_icloud_connection():
    """Test iCloud connection and handle 2FA"""
    print("🍎 Testing iCloud Connection")
    print("=" * 40)
    
    try:
        from common.config_manager import config_manager
        from common.auth import auth_manager
        
        # Get iCloud configuration
        icloud_config = config_manager.get_icloud_config()
        
        if not icloud_config.username or not icloud_config.password:
            print("❌ iCloud credentials not configured!")
            print("Please configure your iCloud credentials first:")
            print("1. Go to: http://192.168.1.15:8083/")
            print("2. Enter your Apple ID and password")
            print("3. Save the configuration")
            return False
        
        print(f"📧 Testing connection for: {icloud_config.username}")
        
        # Test the connection
        print("🔐 Testing iCloud authentication...")
        success = auth_manager.test_icloud_connection()
        
        if success:
            print("✅ iCloud connection successful!")
            print("🎉 You can now use the iCloud sync features!")
            return True
        else:
            print("❌ iCloud connection failed!")
            print("This might be due to:")
            print("1. Incorrect credentials")
            print("2. 2FA required (check your Apple device)")
            print("3. Network connectivity issues")
            return False
            
    except Exception as e:
        print(f"❌ Error testing iCloud connection: {e}")
        return False

def test_sync_functionality():
    """Test basic sync functionality"""
    print("\n🔄 Testing Sync Functionality")
    print("=" * 40)
    
    try:
        from sync_icloud import ICloudSyncManager
        
        print("📱 Creating sync manager...")
        sync_manager = ICloudSyncManager()
        
        print("🔍 Validating iCloud connection...")
        if sync_manager.validate_icloud_connection():
            print("✅ iCloud connection validated!")
            
            print("📊 Getting sync statistics...")
            stats = sync_manager.get_sync_stats()
            print(f"📈 Current stats: {stats}")
            
            return True
        else:
            print("❌ iCloud connection validation failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error testing sync functionality: {e}")
        return False

def main():
    """Main function"""
    print("🚀 iCloud Connection Test")
    print("=" * 50)
    
    # Test iCloud connection
    connection_ok = test_icloud_connection()
    
    if connection_ok:
        # Test sync functionality
        sync_ok = test_sync_functionality()
        
        if sync_ok:
            print("\n🎉 All tests passed!")
            print("✅ Your iCloud integration is ready to use!")
            print("\n📋 Next steps:")
            print("1. Run a test sync: python3 sync_icloud.py")
            print("2. Monitor progress in the web dashboard")
            print("3. Check the database viewer for results")
        else:
            print("\n⚠️ Connection works but sync functionality has issues")
    else:
        print("\n❌ iCloud connection failed")
        print("Please check your credentials and try again")
    
    return 0 if connection_ok else 1

if __name__ == "__main__":
    exit(main())
