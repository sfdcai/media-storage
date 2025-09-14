#!/usr/bin/env python3
"""
Fix PM2 Port Issues Script
Fixes PM2 applications that are running but not listening on correct ports
"""

import subprocess
import os
import time
import socket

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

def check_port(port):
    """Check if a port is listening"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('127.0.0.1', port))
            return result == 0
    except:
        return False

def fix_pm2_applications():
    """Fix PM2 applications"""
    print("🔧 Fixing PM2 Applications")
    print("=" * 40)
    
    # Change to project directory
    os.chdir('/opt/media-pipeline')
    
    # Stop all PM2 processes
    print("🛑 Stopping all PM2 processes...")
    run_command('pm2 stop all', 'Stopping all PM2 processes')
    run_command('pm2 delete all', 'Deleting all PM2 processes')
    
    # Wait a moment
    time.sleep(3)
    
    # Start PM2 applications fresh
    print("🚀 Starting PM2 applications...")
    if run_command('pm2 start ecosystem.config.js', 'Starting PM2 applications'):
        # Wait for applications to start
        print("⏳ Waiting for applications to start...")
        time.sleep(10)
        
        # Check PM2 status
        print("📊 Checking PM2 status...")
        run_command('pm2 list', 'Checking PM2 status')
        
        # Save PM2 configuration
        run_command('pm2 save', 'Saving PM2 configuration')
        
        return True
    else:
        return False

def fix_web_ui_binding():
    """Fix web UI binding issues"""
    print("\n🔧 Fixing Web UI Binding Issues")
    print("=" * 40)
    
    # Check if web_ui.py binds to 0.0.0.0
    web_ui_path = '/opt/media-pipeline/web_ui.py'
    if os.path.exists(web_ui_path):
        with open(web_ui_path, 'r') as f:
            content = f.read()
        
        # Check if it's binding to 0.0.0.0
        if 'host = \'0.0.0.0\'' in content:
            print("  ✅ Web UI already binds to 0.0.0.0")
        else:
            print("  ⚠️ Web UI may not be binding to 0.0.0.0")
            print("  📝 This could cause external access issues")
    
    return True

def start_pm2_dashboard():
    """Start PM2 dashboard"""
    print("\n🔧 Starting PM2 Dashboard")
    print("=" * 40)
    
    # Start PM2 dashboard
    if run_command('pm2 start pm2_dashboard_config.js', 'Starting PM2 dashboard'):
        time.sleep(5)
        return True
    else:
        return False

def test_ports():
    """Test all ports after fixes"""
    print("\n🔧 Testing Ports After Fixes")
    print("=" * 40)
    
    ports = [80, 8080, 8081, 8082, 8083, 8084, 8385, 9615]
    listening_ports = []
    
    for port in ports:
        if check_port(port):
            print(f"  ✅ Port {port}: LISTENING")
            listening_ports.append(port)
        else:
            print(f"  ❌ Port {port}: NOT LISTENING")
    
    return listening_ports

def main():
    """Main function"""
    print("🚀 Fixing PM2 Port Issues")
    print("=" * 50)
    
    # Fix PM2 applications
    pm2_ok = fix_pm2_applications()
    
    # Fix web UI binding
    web_ui_ok = fix_web_ui_binding()
    
    # Start PM2 dashboard
    dashboard_ok = start_pm2_dashboard()
    
    # Test ports
    listening_ports = test_ports()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 FIX SUMMARY")
    print("=" * 50)
    
    print(f"✅ PM2 applications: {'Fixed' if pm2_ok else 'Failed'}")
    print(f"✅ Web UI binding: {'OK' if web_ui_ok else 'Issues'}")
    print(f"✅ PM2 dashboard: {'Started' if dashboard_ok else 'Failed'}")
    print(f"✅ Ports listening: {len(listening_ports)}/8")
    
    if len(listening_ports) >= 6:
        print("\n🎉 Most services are now working!")
        print("\n📋 Next steps:")
        print("1. Test web interfaces in your browser")
        print("2. Check PM2 logs: pm2 logs")
        print("3. Run system diagnostic: python3 diagnose_system.py")
    else:
        print(f"\n⚠️ Still having issues with {8 - len(listening_ports)} ports")
        print("\n🔧 Additional troubleshooting:")
        print("1. Check PM2 logs: pm2 logs")
        print("2. Check system logs: journalctl -u media-pipeline.service")
        print("3. Check Nginx: systemctl status nginx")
    
    return 0 if len(listening_ports) >= 6 else 1

if __name__ == "__main__":
    exit(main())
