#!/usr/bin/env python3
"""
Port Connectivity Test Script
Tests actual HTTP connectivity to all services
"""

import requests
import socket
import time
from urllib.parse import urljoin

def test_port_connectivity():
    """Test basic port connectivity"""
    print("🔍 Testing port connectivity...")
    
    ports = [80, 8080, 8081, 8082, 8083, 8084, 8385, 9615]
    base_url = "http://192.168.1.15"
    
    for port in ports:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                result = s.connect_ex(('127.0.0.1', port))
                if result == 0:
                    print(f"  ✅ Port {port}: LISTENING")
                else:
                    print(f"  ❌ Port {port}: NOT LISTENING")
        except Exception as e:
            print(f"  ❌ Port {port}: ERROR - {e}")

def test_http_connectivity():
    """Test HTTP connectivity to all services"""
    print("\n🔍 Testing HTTP connectivity...")
    
    services = [
        (80, "/", "Nginx (Main)"),
        (8080, "/", "Web UI (Main)"),
        (8081, "/", "Pipeline Dashboard"),
        (8082, "/", "Status Dashboard"),
        (8083, "/", "Configuration Interface"),
        (8084, "/", "Database Viewer"),
        (8385, "/", "Syncthing"),
        (9615, "/", "PM2 Dashboard")
    ]
    
    base_url = "http://192.168.1.15"
    
    for port, path, name in services:
        url = f"{base_url}:{port}{path}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"  ✅ {name} ({port}): HTTP 200 OK")
            else:
                print(f"  ⚠️ {name} ({port}): HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"  ❌ {name} ({port}): Connection refused")
        except requests.exceptions.Timeout:
            print(f"  ❌ {name} ({port}): Timeout")
        except Exception as e:
            print(f"  ❌ {name} ({port}): Error - {e}")

def test_nginx_proxy():
    """Test nginx proxy functionality"""
    print("\n🔍 Testing nginx proxy...")
    
    proxy_routes = [
        ("/", "Web UI (Main)"),
        ("/pipeline/", "Pipeline Dashboard"),
        ("/status/", "Status Dashboard"),
        ("/config/", "Configuration Interface"),
        ("/db/", "Database Viewer"),
        ("/syncthing/", "Syncthing"),
        ("/pm2/", "PM2 Dashboard")
    ]
    
    base_url = "http://192.168.1.15"
    
    for route, name in proxy_routes:
        url = f"{base_url}{route}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"  ✅ {name}: HTTP 200 OK")
            else:
                print(f"  ⚠️ {name}: HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"  ❌ {name}: Connection refused")
        except requests.exceptions.Timeout:
            print(f"  ❌ {name}: Timeout")
        except Exception as e:
            print(f"  ❌ {name}: Error - {e}")

def main():
    """Main function"""
    print("🚀 Port Connectivity Test")
    print("=" * 40)
    
    test_port_connectivity()
    test_http_connectivity()
    test_nginx_proxy()
    
    print("\n" + "=" * 40)
    print("📊 Test completed!")

if __name__ == "__main__":
    main()
