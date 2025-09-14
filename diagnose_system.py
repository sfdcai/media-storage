#!/usr/bin/env python3
"""
System Diagnostic Script
Comprehensive system health check for the media pipeline
"""

import subprocess
import sys
import os
import socket
from pathlib import Path

# Add current directory to path
sys.path.insert(0, "/opt/media-pipeline")

def check_python_imports():
    """Check if all required Python modules can be imported"""
    print("🔍 Checking Python imports...")
    
    # Check Python modules using system Python
    print("  Checking Python modules...")
    try:
        result = subprocess.run([
            'python3', '-c', '''
import sys
required_modules = [
    "flask", "flask_socketio", "flask_cors", "psutil", "yaml", 
    "requests", "PIL", "sqlite3", "datetime", "pathlib", 
    "threading", "json", "time"
]
missing = []
for module in required_modules:
    try:
        __import__(module)
        print(f"OK:{module}")
    except ImportError as e:
        print(f"FAIL:{module}:{e}")
        missing.append(module)
if missing:
    sys.exit(1)
else:
    sys.exit(0)
'''
        ], capture_output=True, text=True, cwd='/opt/media-pipeline')
        
        missing_modules = []
        for line in result.stdout.strip().split('\n'):
            if line.startswith('OK:'):
                module = line.split(':', 1)[1]
                print(f"  ✅ {module}")
            elif line.startswith('FAIL:'):
                parts = line.split(':', 2)
                module = parts[1]
                error = parts[2] if len(parts) > 2 else "Import failed"
                print(f"  ❌ {module}: {error}")
                missing_modules.append(module)
        
        if result.returncode == 0:
            print("  ✅ All required Python modules available")
            return True
        else:
            print(f"  ❌ Missing Python modules: {missing_modules}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error checking Python modules: {e}")
        return False

def check_local_imports():
    """Check if local modules can be imported"""
    print("\n🔍 Checking local module imports...")
    
    # Check local modules using system Python
    try:
        result = subprocess.run([
            'python3', '-c', '''
import sys
import os
sys.path.insert(0, "/opt/media-pipeline")

local_modules = [
    "common.config",
    "common.database", 
    "common.logger",
    "common.auth",
    "telegram_notifier"
]

missing = []
for module in local_modules:
    try:
        __import__(module)
        print(f"OK:{module}")
    except ImportError as e:
        print(f"FAIL:{module}:{e}")
        missing.append(module)
if missing:
    sys.exit(1)
else:
    sys.exit(0)
'''
        ], capture_output=True, text=True, cwd='/opt/media-pipeline')
        
        missing_modules = []
        for line in result.stdout.strip().split('\n'):
            if line.startswith('OK:'):
                module = line.split(':', 1)[1]
                print(f"  ✅ {module}")
            elif line.startswith('FAIL:'):
                parts = line.split(':', 2)
                module = parts[1]
                error = parts[2] if len(parts) > 2 else "Import failed"
                print(f"  ❌ {module}: {error}")
                missing_modules.append(module)
        
        if result.returncode == 0:
            print("  ✅ All local modules available")
            return True
        else:
            print(f"  ❌ Missing local modules: {missing_modules}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error checking local modules: {e}")
        return False

def check_file_permissions():
    """Check file permissions for key scripts"""
    print("\n🔍 Checking file permissions...")
    
    key_files = [
        'web_ui.py', 'web_status_dashboard.py', 'web_config_interface.py',
        'db_viewer.py', 'sync_icloud.py', 'bulk_icloud_sync.py',
        'pipeline_orchestrator.py'
    ]
    
    all_good = True
    for file in key_files:
        if os.path.exists(file):
            if os.access(file, os.X_OK):
                print(f"  ✅ {file} (executable)")
            else:
                print(f"  ❌ {file} (not executable)")
                all_good = False
        else:
            print(f"  ❌ {file} (not found)")
            all_good = False
    
    return all_good

def check_port_status():
    """Check if required ports are listening"""
    print("\n🔍 Checking port status...")
    
    ports_to_check = [80, 8080, 8081, 8082, 8083, 8084, 8385, 9615]
    listening_ports = []
    
    for port in ports_to_check:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                result = s.connect_ex(('127.0.0.1', port))
                if result == 0:
                    print(f"  ✅ Port {port}: LISTENING")
                    listening_ports.append(port)
                else:
                    print(f"  ❌ Port {port}: NOT LISTENING")
        except Exception as e:
            print(f"  ❌ Port {port}: ERROR - {e}")
    
    return listening_ports

def check_pm2_status():
    """Check PM2 application status"""
    print("\n🔍 Checking PM2 status...")
    
    try:
        result = subprocess.run(['pm2', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            print("PM2 Status:")
            print(result.stdout)
            return True
        else:
            print(f"  ❌ PM2 status check failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"  ❌ PM2 check error: {e}")
        return False

def check_nginx_config():
    """Check Nginx configuration"""
    print("\n🔍 Checking nginx configuration...")
    
    try:
        # Test nginx configuration
        result = subprocess.run(['nginx', '-t'], capture_output=True, text=True)
        if result.returncode == 0:
            print("  ✅ Nginx configuration is valid")
        else:
            print(f"  ❌ Nginx configuration error: {result.stderr}")
            return False
        
        # Check if media-pipeline site is enabled
        if os.path.exists('/etc/nginx/sites-enabled/media-pipeline'):
            print("  ✅ Media pipeline site is enabled")
        else:
            print("  ❌ Media pipeline site not enabled")
            return False
        
        return True
    except Exception as e:
        print(f"  ❌ Nginx check error: {e}")
        return False

def check_directories():
    """Check required directories"""
    print("\n🔍 Checking directories...")
    
    required_dirs = [
        '/opt/media-pipeline',
        '/opt/media-pipeline/templates',
        '/opt/media-pipeline/common',
        '/var/log/media-pipeline',
        '/mnt/wd_all_pictures/incoming',
        '/mnt/wd_all_pictures/processed'
    ]
    
    all_good = True
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"  ✅ {directory}")
        else:
            print(f"  ❌ {directory}")
            all_good = False
    
    return all_good

def check_database():
    """Check database accessibility"""
    print("\n🔍 Checking database...")
    
    db_path = '/opt/media-pipeline/media.db'
    if os.path.exists(db_path):
        print(f"  ✅ Database exists: {db_path}")
        
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()
            
            print(f"  ✅ Database accessible, {len(tables)} tables found")
            return True
        except Exception as e:
            print(f"  ❌ Database error: {e}")
            return False
    else:
        print(f"  ❌ Database not found: {db_path}")
        return False

def main():
    """Main diagnostic function"""
    print("🚀 Media Pipeline System Diagnostic")
    print("=" * 50)
    
    # Change to project directory
    os.chdir('/opt/media-pipeline')
    
    # Run all checks
    python_ok = check_python_imports()
    local_ok = check_local_imports()
    files_ok = check_file_permissions()
    ports = check_port_status()
    pm2_ok = check_pm2_status()
    nginx_ok = check_nginx_config()
    dirs_ok = check_directories()
    db_ok = check_database()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    print(f"✅ Python modules: {'OK' if python_ok else 'FAIL'}")
    print(f"✅ Local modules: {'OK' if local_ok else 'FAIL'}")
    print(f"✅ File permissions: {'OK' if files_ok else 'FAIL'}")
    print(f"✅ Ports listening: {len(ports)}/8")
    print(f"✅ PM2 status: {'OK' if pm2_ok else 'FAIL'}")
    print(f"✅ Nginx config: {'OK' if nginx_ok else 'FAIL'}")
    print(f"✅ Directories: {'OK' if dirs_ok else 'FAIL'}")
    print(f"✅ Database: {'OK' if db_ok else 'FAIL'}")
    
    # Recommendations
    print("\n🔧 RECOMMENDATIONS:")
    if not python_ok:
        print("1. Install missing Python dependencies")
    if not local_ok:
        print("2. Check local module imports")
    if not files_ok:
        print("3. Fix file permissions")
    if len(ports) < 8:
        print("4. Start services on missing ports")
    if not pm2_ok:
        print("5. Check PM2 configuration")
    if not nginx_ok:
        print("6. Fix Nginx configuration")
    if not dirs_ok:
        print("7. Create missing directories")
    if not db_ok:
        print("8. Initialize database")
    
    # Overall status
    all_checks = [python_ok, local_ok, files_ok, pm2_ok, nginx_ok, dirs_ok, db_ok]
    passed_checks = sum(all_checks)
    total_checks = len(all_checks)
    
    if passed_checks == total_checks and len(ports) >= 6:
        print(f"\n🎉 System is healthy! ({passed_checks}/{total_checks} checks passed)")
        return 0
    else:
        print(f"\n⚠️ System has issues ({passed_checks}/{total_checks} checks passed)")
        return 1

if __name__ == "__main__":
    exit(main())