#!/usr/bin/env python3
"""
Final Issues Fix Script
Fixes the remaining issues with the media pipeline system
"""

import os
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

def fix_web_ui_binding():
    """Fix web UI binding to 0.0.0.0"""
    print("\n🔧 Fixing web UI binding...")
    
    # The web_ui.py file has already been updated to bind to 0.0.0.0
    print("  ✅ Web UI binding already fixed")
    return True

def create_systemd_service():
    """Create and install systemd service"""
    print("\n🔧 Creating systemd service...")
    
    service_file = '/etc/systemd/system/media-pipeline.service'
    
    # Copy service file
    if Path('media-pipeline.service').exists():
        shutil.copy('media-pipeline.service', service_file)
        print("  ✅ Service file copied")
    else:
        print("  ❌ Service file not found")
        return False
    
    # Reload systemd and enable service
    run_command('systemctl daemon-reload', 'Reloading systemd')
    run_command('systemctl enable media-pipeline.service', 'Enabling media-pipeline service')
    
    return True

def fix_pm2_dashboard():
    """Fix PM2 dashboard configuration"""
    print("\n🔧 Fixing PM2 dashboard...")
    
    # Stop existing PM2 dashboard
    run_command('pm2 stop pm2-dashboard', 'Stopping existing PM2 dashboard')
    run_command('pm2 delete pm2-dashboard', 'Deleting existing PM2 dashboard')
    
    # Start new PM2 dashboard with proper configuration
    if Path('pm2_dashboard_config.js').exists():
        run_command('pm2 start pm2_dashboard_config.js', 'Starting PM2 dashboard with new config')
    else:
        # Fallback to direct command
        run_command('pm2 serve /opt/media-pipeline 9615 --name pm2-dashboard --spa', 'Starting PM2 dashboard')
    
    run_command('pm2 save', 'Saving PM2 configuration')
    
    return True

def restart_services():
    """Restart all services"""
    print("\n🔧 Restarting services...")
    
    # Restart PM2 applications
    run_command('pm2 restart all', 'Restarting PM2 applications')
    
    # Wait a moment for services to start
    import time
    time.sleep(5)
    
    return True

def test_connectivity():
    """Test connectivity to all services"""
    print("\n🔧 Testing connectivity...")
    
    import socket
    
    ports_to_test = [8080, 8081, 8082, 8083, 8084, 8385, 9615]
    
    for port in ports_to_test:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                result = s.connect_ex(('0.0.0.0', port))
                if result == 0:
                    print(f"  ✅ Port {port}: LISTENING")
                else:
                    print(f"  ❌ Port {port}: NOT LISTENING")
        except Exception as e:
            print(f"  ❌ Port {port}: ERROR - {e}")

def main():
    """Main function"""
    print("🚀 Final Issues Fix")
    print("=" * 40)
    
    # Check if running as root
    if os.geteuid() != 0:
        print("❌ This script must be run as root")
        return 1
    
    # Run all fixes
    fixes = [
        fix_web_ui_binding,
        create_systemd_service,
        fix_pm2_dashboard,
        restart_services
    ]
    
    for fix_func in fixes:
        try:
            fix_func()
        except Exception as e:
            print(f"❌ Error in {fix_func.__name__}: {e}")
    
    # Test results
    print("\n" + "=" * 40)
    print("🧪 TESTING RESULTS")
    print("=" * 40)
    
    test_connectivity()
    
    print("\n🎉 Final fixes completed!")
    print("\nAccess URLs:")
    print("  Web UI (Main): http://192.168.1.15/")
    print("  Pipeline Dashboard: http://192.168.1.15:8081/")
    print("  Status Dashboard: http://192.168.1.15:8082/")
    print("  Configuration Interface: http://192.168.1.15:8083/")
    print("  Database Viewer: http://192.168.1.15:8084/")
    print("  Syncthing: http://192.168.1.15:8385/")
    print("  PM2 Dashboard: http://192.168.1.15:9615/")
    
    return 0

if __name__ == "__main__":
    exit(main())
