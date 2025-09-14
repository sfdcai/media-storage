#!/usr/bin/env python3
"""
PM2 Dashboard Startup Script
Starts the PM2 web dashboard on port 9615
"""

import subprocess
import time
import socket

def check_port(port):
    """Check if a port is listening"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('127.0.0.1', port))
            return result == 0
    except:
        return False

def start_pm2_dashboard():
    """Start PM2 dashboard"""
    print("🔧 Starting PM2 dashboard...")
    
    try:
        # Check if PM2 dashboard is already running
        if check_port(9615):
            print("  ✅ PM2 dashboard is already running on port 9615")
            return True
        
        # Start PM2 dashboard
        result = subprocess.run([
            'pm2', 'serve', '/opt/media-pipeline', '9615', '--name', 'pm2-dashboard'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("  ✅ PM2 dashboard started successfully")
            
            # Wait a moment and check if it's listening
            time.sleep(3)
            if check_port(9615):
                print("  ✅ PM2 dashboard is now listening on port 9615")
                return True
            else:
                print("  ⚠️ PM2 dashboard started but port 9615 is not listening")
                return False
        else:
            print(f"  ❌ Failed to start PM2 dashboard: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error starting PM2 dashboard: {e}")
        return False

def main():
    """Main function"""
    print("🚀 PM2 Dashboard Startup")
    print("=" * 30)
    
    success = start_pm2_dashboard()
    
    if success:
        print("\n✅ PM2 dashboard is now available at:")
        print("   http://your-ip:9615")
        print("   http://your-ip/pm2/ (via nginx)")
    else:
        print("\n❌ Failed to start PM2 dashboard")
        print("You can manually start it with:")
        print("   pm2 serve /opt/media-pipeline 9615 --name pm2-dashboard")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
