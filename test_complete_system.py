#!/usr/bin/env python3
"""
Complete System Test Script
Tests all components of the media pipeline system
"""

import os
import sys
import requests
import subprocess
import time
from pathlib import Path

def test_web_interfaces():
    """Test all web interfaces"""
    print("🌐 Testing Web Interfaces")
    print("=" * 40)
    
    base_url = "http://192.168.1.15"
    interfaces = [
        ("/", "Main Dashboard"),
        ("/pipeline/", "Pipeline Dashboard"),
        ("/status/", "Status Dashboard"),
        ("/config/", "Configuration Interface"),
        ("/db/", "Database Viewer"),
        ("/syncthing/", "Syncthing"),
        ("/pm2/", "PM2 Dashboard")
    ]
    
    all_working = True
    
    for route, name in interfaces:
        url = f"{base_url}{route}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"  ✅ {name}: Working")
            else:
                print(f"  ⚠️ {name}: HTTP {response.status_code}")
                all_working = False
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            all_working = False
    
    return all_working

def test_direct_ports():
    """Test direct port access"""
    print("\n🔌 Testing Direct Port Access")
    print("=" * 40)
    
    ports = [8080, 8081, 8082, 8083, 8084, 8385, 9615]
    base_url = "http://192.168.1.15"
    
    all_working = True
    
    for port in ports:
        url = f"{base_url}:{port}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"  ✅ Port {port}: Working")
            else:
                print(f"  ⚠️ Port {port}: HTTP {response.status_code}")
        except Exception as e:
            print(f"  ❌ Port {port}: {e}")
            all_working = False
    
    return all_working

def test_pm2_status():
    """Test PM2 application status"""
    print("\n📱 Testing PM2 Applications")
    print("=" * 40)
    
    try:
        result = subprocess.run(['pm2', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            print("  ✅ PM2 status check successful")
            
            # Check for online applications
            lines = result.stdout.split('\n')
            online_count = 0
            for line in lines:
                if 'online' in line:
                    online_count += 1
            
            print(f"  📊 {online_count} applications online")
            return online_count > 0
        else:
            print(f"  ❌ PM2 status check failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"  ❌ PM2 test error: {e}")
        return False

def test_database():
    """Test database functionality"""
    print("\n🗄️ Testing Database")
    print("=" * 40)
    
    try:
        # Add project directory to path
        sys.path.insert(0, '/opt/media-pipeline')
        from common.database import db_manager
        
        # Test database connection
        db_manager.init_database()
        print("  ✅ Database connection successful")
        
        # Test table access
        import sqlite3
        conn = sqlite3.connect('/opt/media-pipeline/media.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
        
        print(f"  📊 {len(tables)} tables found")
        return True
        
    except Exception as e:
        print(f"  ❌ Database test error: {e}")
        return False

def test_icloud_config():
    """Test iCloud configuration"""
    print("\n🍎 Testing iCloud Configuration")
    print("=" * 40)
    
    try:
        sys.path.insert(0, '/opt/media-pipeline')
        from common.config import config_manager
        
        icloud_config = config_manager.get_icloud_config()
        
        if icloud_config.username and icloud_config.password:
            print(f"  ✅ iCloud credentials configured for: {icloud_config.username}")
            print("  📝 Note: Run 'python3 test_icloud_connection.py' to test authentication")
            return True
        else:
            print("  ⚠️ iCloud credentials not configured")
            print("  📝 Please configure at: http://192.168.1.15:8083/")
            return False
            
    except Exception as e:
        print(f"  ❌ iCloud config test error: {e}")
        return False

def test_syncthing():
    """Test Syncthing functionality"""
    print("\n🔄 Testing Syncthing")
    print("=" * 40)
    
    try:
        # Test Syncthing API
        response = requests.get('http://127.0.0.1:8385/rest/system/status', timeout=5)
        if response.status_code == 200:
            print("  ✅ Syncthing API accessible")
            return True
        else:
            print(f"  ⚠️ Syncthing API returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Syncthing test error: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Complete System Test")
    print("=" * 50)
    
    tests = [
        ("Web Interfaces", test_web_interfaces),
        ("Direct Ports", test_direct_ports),
        ("PM2 Applications", test_pm2_status),
        ("Database", test_database),
        ("iCloud Configuration", test_icloud_config),
        ("Syncthing", test_syncthing)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test failed with error: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your system is fully operational!")
        print("\n📋 Next steps:")
        print("1. Configure iCloud credentials at: http://192.168.1.15:8083/")
        print("2. Test iCloud connection: python3 test_icloud_connection.py")
        print("3. Run a test sync: python3 sync_icloud.py")
        print("4. Monitor progress in the web dashboards")
    else:
        print(f"\n⚠️ {total - passed} tests failed. Please check the issues above.")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit(main())
