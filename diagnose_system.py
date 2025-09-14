#!/usr/bin/env python3
"""
Comprehensive System Diagnostic Script
Checks all components of the media pipeline system
"""

import os
import sys
import subprocess
import importlib
import socket
from pathlib import Path

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
            
            return missing_modules
            
        except Exception as e:
            print(f"  ❌ Error checking virtual environment imports: {e}")
            return ['virtual_env_check_failed']
    else:
        print("  ⚠️ Virtual environment not found, checking system Python...")
        required_modules = [
            'flask', 'flask_socketio', 'flask_cors', 'psutil', 'yaml',
            'requests', 'PIL', 'sqlite3', 'datetime', 'pathlib',
            'threading', 'json', 'time'
        ]
        
        missing_modules = []
        for module in required_modules:
            try:
                importlib.import_module(module)
                print(f"  ✅ {module}")
            except ImportError as e:
                print(f"  ❌ {module}: {e}")
                missing_modules.append(module)
        
        return missing_modules

def check_local_imports():
    """Check if local modules can be imported"""
    print("\n🔍 Checking local module imports...")
    
    # Check if we're in the virtual environment
    system_python = 'python3'
    if False:  # Disabled virtual environment check
        print("  Using virtual environment Python for local import checks...")
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
            
            missing_local = []
            for line in result.stdout.strip().split('\n'):
                if line.startswith('OK:'):
                    module = line.split(':', 1)[1]
                    print(f"  ✅ {module}")
                elif line.startswith('FAIL:'):
                    parts = line.split(':', 2)
                    module = parts[1]
                    error = parts[2] if len(parts) > 2 else "Import failed"
                    print(f"  ❌ {module}: {error}")
                    missing_local.append(module)
            
            return missing_local
            
        except Exception as e:
            print(f"  ❌ Error checking virtual environment local imports: {e}")
            return ['local_import_check_failed']
    else:
        print("  ⚠️ Virtual environment not found, checking system Python...")
        # Add current directory to path
        current_dir = Path(__file__).parent
        sys.path.insert(0, str(current_dir))
        
        local_modules = [
            'common.config',
            'common.database', 
            'common.logger',
            'common.auth',
            'telegram_notifier'
        ]
        
        missing_local = []
        for module in local_modules:
            try:
                importlib.import_module(module)
                print(f"  ✅ {module}")
            except ImportError as e:
                print(f"  ❌ {module}: {e}")
                missing_local.append(module)
        
        return missing_local

def check_file_permissions():
    """Check if Python scripts are executable"""
    print("\n🔍 Checking file permissions...")
    
    scripts = [
        'web_ui.py',
        'web_status_dashboard.py',
        'web_config_interface.py', 
        'db_viewer.py',
        'sync_icloud.py',
        'bulk_icloud_sync.py',
        'pipeline_orchestrator.py'
    ]
    
    missing_files = []
    for script in scripts:
        script_path = Path(script)
        if script_path.exists():
            if os.access(script_path, os.X_OK):
                print(f"  ✅ {script} (executable)")
            else:
                print(f"  ⚠️ {script} (not executable)")
                os.chmod(script_path, 0o755)
                print(f"    → Made executable")
        else:
            print(f"  ❌ {script} (missing)")
            missing_files.append(script)
    
    return missing_files

def check_ports():
    """Check which ports are listening"""
    print("\n🔍 Checking port status...")
    
    ports_to_check = [80, 8080, 8081, 8082, 8083, 8084, 8385, 9615]
    
    listening_ports = []
    for port in ports_to_check:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
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
            
            # Parse PM2 output to find failed apps
            lines = result.stdout.split('\n')
            failed_apps = []
            for line in lines:
                if 'errored' in line or 'stopped' in line:
                    parts = line.split()
                    if len(parts) > 1:
                        app_name = parts[1]
                        status = parts[4] if len(parts) > 4 else 'unknown'
                        failed_apps.append((app_name, status))
                        print(f"  ❌ {app_name}: {status}")
            
            return failed_apps
        else:
            print(f"  ❌ PM2 command failed: {result.stderr}")
            return []
    except FileNotFoundError:
        print("  ❌ PM2 not found")
        return []
    except Exception as e:
        print(f"  ❌ PM2 check failed: {e}")
        return []

def check_nginx_config():
    """Check nginx configuration"""
    print("\n🔍 Checking nginx configuration...")
    
    try:
        # Check if nginx config is valid
        result = subprocess.run(['nginx', '-t'], capture_output=True, text=True)
        if result.returncode == 0:
            print("  ✅ Nginx configuration is valid")
        else:
            print(f"  ❌ Nginx configuration error: {result.stderr}")
            return False
        
        # Check if our site is enabled
        sites_enabled = Path('/etc/nginx/sites-enabled/media-pipeline')
        if sites_enabled.exists():
            print("  ✅ Media pipeline site is enabled")
        else:
            print("  ❌ Media pipeline site is not enabled")
            return False
        
        return True
    except Exception as e:
        print(f"  ❌ Nginx check failed: {e}")
        return False

def check_directories():
    """Check if required directories exist"""
    print("\n🔍 Checking directories...")
    
    required_dirs = [
        '/opt/media-pipeline',
        '/opt/media-pipeline/venv',
        '/opt/media-pipeline/templates',
        '/opt/media-pipeline/common',
        '/var/log/media-pipeline',
        '/mnt/wd_all_pictures/incoming',
        '/mnt/wd_all_pictures/processed'
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"  ✅ {dir_path}")
        else:
            print(f"  ❌ {dir_path} (missing)")
            missing_dirs.append(dir_path)
    
    return missing_dirs

def check_database():
    """Check if database exists and is accessible"""
    print("\n🔍 Checking database...")
    
    db_path = '/opt/media-pipeline/media.db'
    if Path(db_path).exists():
        print(f"  ✅ Database exists: {db_path}")
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"  ✅ Database accessible, {len(tables)} tables found")
            conn.close()
            return True
        except Exception as e:
            print(f"  ❌ Database error: {e}")
            return False
    else:
        print(f"  ❌ Database missing: {db_path}")
        return False

def main():
    """Run comprehensive system diagnostic"""
    print("🚀 Media Pipeline System Diagnostic")
    print("=" * 50)
    
    # Run all checks
    missing_modules = check_python_imports()
    missing_local = check_local_imports()
    missing_files = check_file_permissions()
    listening_ports = check_ports()
    failed_apps = check_pm2_status()
    nginx_ok = check_nginx_config()
    missing_dirs = check_directories()
    db_ok = check_database()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    if missing_modules:
        print(f"❌ Missing Python modules: {', '.join(missing_modules)}")
    else:
        print("✅ All Python modules available")
    
    if missing_local:
        print(f"❌ Missing local modules: {', '.join(missing_local)}")
    else:
        print("✅ All local modules available")
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
    else:
        print("✅ All required files present")
    
    if missing_dirs:
        print(f"❌ Missing directories: {', '.join(missing_dirs)}")
    else:
        print("✅ All required directories present")
    
    if not db_ok:
        print("❌ Database issues detected")
    else:
        print("✅ Database is working")
    
    if not nginx_ok:
        print("❌ Nginx configuration issues")
    else:
        print("✅ Nginx configuration is valid")
    
    expected_ports = [80, 8080, 8081, 8082, 8083, 8084, 8385, 9615]
    missing_ports = [p for p in expected_ports if p not in listening_ports]
    if missing_ports:
        print(f"❌ Missing ports: {missing_ports}")
    else:
        print("✅ All expected ports are listening")
    
    if failed_apps:
        print(f"❌ Failed PM2 apps: {[app[0] for app in failed_apps]}")
    else:
        print("✅ All PM2 applications are running")
    
    # Recommendations
    print("\n🔧 RECOMMENDATIONS:")
    if missing_modules or missing_local:
        print("1. Install missing Python dependencies")
    if missing_files:
        print("2. Ensure all Python scripts are present and executable")
    if missing_dirs:
        print("3. Create missing directories")
    if failed_apps:
        print("4. Restart failed PM2 applications")
    if missing_ports:
        print("5. Start services on missing ports")
    
    return len(missing_modules) + len(missing_local) + len(missing_files) + len(missing_dirs) + len(failed_apps) + len(missing_ports)

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
