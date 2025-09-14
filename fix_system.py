#!/usr/bin/env python3
"""
Comprehensive System Fix Script
Fixes all identified issues with the media pipeline system
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✅ {description} completed")
            return True
        else:
            print(f"  ❌ {description} failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"  ❌ {description} error: {e}")
        return False

def fix_python_dependencies():
    """Install all required Python dependencies"""
    print("\n🔧 Fixing Python dependencies...")
    
    # Ensure we're in the right directory
    os.chdir('/opt/media-pipeline')
    
    # Install from requirements.txt
    if Path('requirements.txt').exists():
        success = run_command(
            'pip3 install -r requirements.txt --upgrade',
            'Installing Python packages from requirements.txt'
        )
    else:
        # Fallback to essential packages
        packages = [
            'flask>=2.3.0',
            'flask-socketio>=5.3.0', 
            'flask-cors>=4.0.0',
            'psutil>=5.9.0',
            'pyicloud>=0.10.0',
            'requests>=2.28.0',
            'PyYAML>=6.0',
            'Pillow>=9.0.0',
            'python-dateutil>=2.8.0',
            'colorlog>=6.7.0',
            'schedule>=1.2.0'
        ]
        
        for package in packages:
            run_command(
                f'pip3 install {package}',
                f'Installing {package}'
            )
    
    return True

def fix_file_permissions():
    """Fix file permissions for all Python scripts"""
    print("\n🔧 Fixing file permissions...")
    
    scripts = [
        'web_ui.py',
        'web_status_dashboard.py',
        'web_config_interface.py',
        'db_viewer.py',
        'sync_icloud.py',
        'bulk_icloud_sync.py',
        'pipeline_orchestrator.py',
        'telegram_notifier.py',
        'test_pipeline.py'
    ]
    
    for script in scripts:
        script_path = Path(f'/opt/media-pipeline/{script}')
        if script_path.exists():
            os.chmod(script_path, 0o755)
            print(f"  ✅ Made {script} executable")
        else:
            print(f"  ⚠️ {script} not found")
    
    return True

def fix_directories():
    """Create missing directories"""
    print("\n🔧 Creating missing directories...")
    
    directories = [
        '/var/log/media-pipeline',
        '/mnt/wd_all_pictures/incoming',
        '/mnt/wd_all_pictures/processed'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        # Set proper ownership
        run_command(f'chown -R media-pipeline:media-pipeline {directory}', f'Setting ownership for {directory}')
        print(f"  ✅ Created/verified {directory}")
    
    return True

def fix_database():
    """Initialize database if missing"""
    print("\n🔧 Fixing database...")
    
    db_path = '/opt/media-pipeline/media.db'
    if not Path(db_path).exists():
        print("  Creating new database...")
    else:
        print("  Database exists, checking tables...")
    
    # Always run database initialization to ensure tables exist
    if Path('/opt/media-pipeline/init_database.py').exists():
        run_command(
            'cd /opt/media-pipeline && python3 init_database.py',
            'Initializing database tables'
        )
    else:
        print("  ⚠️ Database initialization script not found")
        return False
    
    return True

def fix_nginx():
    """Fix nginx configuration"""
    print("\n🔧 Fixing nginx configuration...")
    
    # Ensure our config is in place
    if Path('/etc/nginx/sites-available/media-pipeline').exists():
        print("  ✅ Nginx config exists")
    else:
        print("  ❌ Nginx config missing - this should be copied by install script")
        return False
    
    # Enable the site
    run_command(
        'ln -sf /etc/nginx/sites-available/media-pipeline /etc/nginx/sites-enabled/',
        'Enabling media-pipeline site'
    )
    
    # Remove default site
    run_command(
        'rm -f /etc/nginx/sites-enabled/default',
        'Removing default nginx site'
    )
    
    # Test configuration
    if run_command('nginx -t', 'Testing nginx configuration'):
        run_command('systemctl reload nginx', 'Reloading nginx')
        return True
    else:
        return False

def fix_pm2():
    """Fix PM2 applications"""
    print("\n🔧 Fixing PM2 applications...")
    
    # Stop all PM2 processes
    run_command('pm2 stop all', 'Stopping all PM2 processes')
    run_command('pm2 delete all', 'Deleting all PM2 processes')
    
    # Start fresh
    if run_command('cd /opt/media-pipeline && pm2 start ecosystem.config.js', 'Starting PM2 applications'):
        run_command('pm2 save', 'Saving PM2 configuration')
        
        # Wait a moment for apps to start
        import time
        time.sleep(10)
        
        # Check status
        result = subprocess.run(['pm2', 'list'], capture_output=True, text=True)
        print("PM2 Status after restart:")
        print(result.stdout)
        
        return True
    else:
        return False

def test_ports():
    """Test if all ports are now listening"""
    print("\n🔧 Testing ports...")
    
    import socket
    
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

def main():
    """Run comprehensive system fix"""
    print("🚀 Media Pipeline System Fix")
    print("=" * 50)
    
    # Check if running as root
    if os.geteuid() != 0:
        print("❌ This script must be run as root")
        return 1
    
    # Run all fixes
    fixes = [
        fix_python_dependencies,
        fix_file_permissions,
        fix_directories,
        fix_database,
        fix_nginx,
        fix_pm2
    ]
    
    # Additional fixes
    def fix_pm2_dashboard():
        """Start PM2 dashboard"""
        print("\n🔧 Starting PM2 dashboard...")
        if Path('/opt/media-pipeline/start_pm2_dashboard.py').exists():
            return run_command(
                'cd /opt/media-pipeline && python3 start_pm2_dashboard.py',
                'Starting PM2 dashboard'
            )
        else:
            print("  ⚠️ PM2 dashboard script not found")
            return False
    
    fixes.append(fix_pm2_dashboard)
    
    for fix_func in fixes:
        try:
            fix_func()
        except Exception as e:
            print(f"❌ Error in {fix_func.__name__}: {e}")
    
    # Test results
    print("\n" + "=" * 50)
    print("🧪 TESTING RESULTS")
    print("=" * 50)
    
    listening_ports = test_ports()
    
    expected_ports = [80, 8080, 8081, 8082, 8083, 8084, 8385, 9615]
    missing_ports = [p for p in expected_ports if p not in listening_ports]
    
    if missing_ports:
        print(f"❌ Still missing ports: {missing_ports}")
        print("\n🔧 Additional troubleshooting needed:")
        print("1. Check PM2 logs: pm2 logs")
        print("2. Check nginx logs: tail -f /var/log/nginx/error.log")
        print("3. Check system logs: journalctl -u nginx")
        return 1
    else:
        print("✅ All ports are now listening!")
        print("\n🎉 System fix completed successfully!")
        print("\nAccess URLs:")
        print("  Web UI (Main): http://your-ip/")
        print("  Pipeline Dashboard: http://your-ip/pipeline/")
        print("  Status Dashboard: http://your-ip/status/")
        print("  Configuration Interface: http://your-ip/config/")
        print("  Database Viewer: http://your-ip/db/")
        print("  Syncthing: http://your-ip/syncthing/")
        print("  PM2 Dashboard: http://your-ip/pm2/")
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
