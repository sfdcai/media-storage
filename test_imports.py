#!/usr/bin/env python3
"""
Test Import Script
Tests if all required modules can be imported correctly
"""

import sys
import os

# Add the project directory to Python path
sys.path.insert(0, '/opt/media-pipeline')

def test_imports():
    """Test all required imports"""
    print("🧪 Testing Module Imports")
    print("=" * 40)
    
    # Test basic Python modules
    basic_modules = [
        'requests',
        'yaml', 
        'flask',
        'psutil',
        'sqlite3',
        'datetime',
        'pathlib',
        'threading',
        'json',
        'time'
    ]
    
    print("📦 Testing basic Python modules...")
    for module in basic_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
    
    # Test local modules
    print("\n🏠 Testing local modules...")
    local_modules = [
        'common.config',
        'common.database', 
        'common.logger',
        'common.auth'
    ]
    
    for module in local_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
    
    # Test specific imports
    print("\n🔧 Testing specific imports...")
    try:
        from common.config import config_manager
        print("  ✅ config_manager")
    except ImportError as e:
        print(f"  ❌ config_manager: {e}")
    
    try:
        from common.database import db_manager
        print("  ✅ db_manager")
    except ImportError as e:
        print(f"  ❌ db_manager: {e}")
    
    try:
        from common.auth import auth_manager
        print("  ✅ auth_manager")
    except ImportError as e:
        print(f"  ❌ auth_manager: {e}")
    
    print("\n🎉 Import test complete!")

if __name__ == "__main__":
    test_imports()
