#!/usr/bin/env python3
"""
Alpine Linux specific health check
"""

import os
import subprocess
import sys
from pathlib import Path


def check_alpine_system():
    """Check Alpine Linux system requirements"""
    print("=== Alpine Linux System Check ===")
    
    # Check if running on Alpine
    try:
        with open('/etc/os-release', 'r') as f:
            os_info = f.read()
            if 'alpine' not in os_info.lower():
                print("⚠️ Not running on Alpine Linux")
                return False
            else:
                print("✅ Running on Alpine Linux")
    except Exception:
        print("❌ Cannot determine OS")
        return False
    
    # Check Python version
    python_version = sys.version_info
    if python_version >= (3, 7):
        print(f"✅ Python {python_version.major}.{python_version.minor} is compatible")
    else:
        print(f"❌ Python {python_version.major}.{python_version.minor} is too old (need 3.7+)")
        return False
    
    return True


def check_alpine_packages():
    """Check required Alpine packages"""
    print("\n=== Alpine Package Check ===")
    
    required_packages = [
        'python3',
        'py3-pip', 
        'ffmpeg',
        'syncthing',
        'jpeg-dev',
        'zlib-dev',
        'freetype-dev'
    ]
    
    all_installed = True
    
    for package in required_packages:
        try:
            result = subprocess.run(['apk', 'info', package], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ {package} is installed")
            else:
                print(f"❌ {package} is not installed")
                all_installed = False
        except Exception as e:
            print(f"❌ Error checking {package}: {e}")
            all_installed = False
    
    return all_installed


def check_python_packages():
    """Check Python packages"""
    print("\n=== Python Package Check ===")
    
    required_packages = [
        'supabase',
        'Pillow',
        'ffmpeg-python',
        'requests',
        'icloudpd'
    ]
    
    all_installed = True
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is not installed")
            all_installed = False
    
    return all_installed


def check_syncthing_service():
    """Check Syncthing service status"""
    print("\n=== Syncthing Service Check ===")
    
    try:
        # Check if Syncthing is running
        result = subprocess.run(['pgrep', 'syncthing'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ Syncthing process is running")
        else:
            print("❌ Syncthing process is not running")
            return False
        
        # Check if Syncthing web interface is accessible
        import requests
        try:
            response = requests.get('http://localhost:8384', timeout=5)
            if response.status_code == 200:
                print("✅ Syncthing web interface is accessible")
            else:
                print("❌ Syncthing web interface is not accessible")
                return False
        except Exception:
            print("❌ Cannot connect to Syncthing web interface")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Syncthing check failed: {e}")
        return False


def check_ffmpeg():
    """Check FFmpeg installation"""
    print("\n=== FFmpeg Check ===")
    
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ FFmpeg is working")
            return True
        else:
            print("❌ FFmpeg is not working")
            return False
    except Exception as e:
        print(f"❌ FFmpeg check failed: {e}")
        return False


def main():
    """Run all Alpine-specific health checks"""
    print("Alpine Linux Media Sync Health Check")
    print("=" * 50)
    
    checks = [
        check_alpine_system,
        check_alpine_packages,
        check_python_packages,
        check_syncthing_service,
        check_ffmpeg
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All Alpine Linux checks passed!")
        print("Your system is ready for the media sync workflow.")
    else:
        print("❌ Some checks failed.")
        print("Please run: bash alpine_setup.sh")
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
