#!/usr/bin/env python3
"""
Media Pipeline Status Dashboard
A comprehensive web UI for monitoring, debugging, and troubleshooting the media pipeline
"""

import os
import sys
import json
import subprocess
import socket
import time
import psutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

# Add the project directory to Python path
project_dir = "/opt/media-pipeline"
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

try:
    from flask import Flask, render_template, jsonify, request
    from flask_socketio import SocketIO, emit
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "flask-socketio", "psutil"])
    from flask import Flask, render_template, jsonify, request
    from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'media-pipeline-status-dashboard'
socketio = SocketIO(app, cors_allowed_origins="*")

class ServiceStatusChecker:
    """Check the status of various services and components with comprehensive monitoring"""
    
    def __init__(self):
        self.project_dir = "/opt/media-pipeline"
        self.service_user = "media-pipeline"
        self.log_dir = "/var/log/media-pipeline"
        self.db_path = "/opt/media-pipeline/media.db"
        
        # Troubleshooting guides
        self.troubleshooting_guides = {
            "nodejs_not_found": {
                "title": "Node.js Not Found",
                "symptoms": ["Node.js command not found", "NPM not available"],
                "solutions": [
                    "Install Node.js via NVM: curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash",
                    "Source NVM: source ~/.bashrc",
                    "Install Node.js: nvm install 18 && nvm use 18",
                    "Or install via apt: apt install -y nodejs npm"
                ]
            },
            "syncthing_connection_failed": {
                "title": "Syncthing Connection Failed",
                "symptoms": ["Cannot connect to Syncthing", "Port 8385 not accessible"],
                "solutions": [
                    "Check if Syncthing is running: systemctl status syncthing@media-pipeline",
                    "Start Syncthing: systemctl start syncthing@media-pipeline",
                    "Check firewall: ufw status",
                    "Verify port: netstat -tlnp | grep 8385"
                ]
            },
            "database_corrupted": {
                "title": "Database Issues",
                "symptoms": ["Database locked", "SQLite errors", "Cannot read database"],
                "solutions": [
                    "Check database permissions: ls -la /opt/media-pipeline/media.db",
                    "Repair database: sqlite3 /opt/media-pipeline/media.db '.recover'",
                    "Backup and recreate: cp media.db media.db.backup && rm media.db"
                ]
            },
            "disk_space_low": {
                "title": "Low Disk Space",
                "symptoms": ["Disk usage > 90%", "Cannot write files", "Out of space errors"],
                "solutions": [
                    "Check disk usage: df -h",
                    "Clean old logs: find /var/log -name '*.log' -mtime +7 -delete",
                    "Clean package cache: apt clean",
                    "Remove old media files if safe to do so"
                ]
            },
            "memory_high": {
                "title": "High Memory Usage",
                "symptoms": ["Memory usage > 90%", "System slow", "Out of memory errors"],
                "solutions": [
                    "Check memory usage: free -h",
                    "Restart services: pm2 restart all",
                    "Check for memory leaks in logs",
                    "Consider increasing container memory"
                ]
            }
        }
    
    def check_systemctl_service(self, service_name):
        """Check if a systemd service is active"""
        try:
            # Try systemctl first
            result = subprocess.run(
                ["systemctl", "is-active", service_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            return {
                "status": "active" if result.returncode == 0 else "inactive",
                "running": result.returncode == 0,
                "output": result.stdout.strip()
            }
        except FileNotFoundError:
            # systemctl not available, check processes instead
            try:
                # Map service names to process names
                process_map = {
                    "media-pipeline": "pipeline_orchestrator.py",
                    "media-pipeline-web": "web_ui.py",
                    "syncthing@media-pipeline": "syncthing",
                    "nginx": "nginx"
                }
                
                process_name = process_map.get(service_name, service_name)
                result = subprocess.run(
                    ["pgrep", "-f", process_name],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                is_running = result.returncode == 0
                return {
                    "status": "active" if is_running else "inactive",
                    "running": is_running,
                    "output": "Process found" if is_running else "Process not found"
                }
            except Exception as e:
                return {
                    "status": "error",
                    "running": False,
                    "output": f"Error checking process: {str(e)}"
                }
        except Exception as e:
            return {
                "status": "error",
                "running": False,
                "output": str(e)
            }
    
    def check_port_listening(self, port):
        """Check if a port is listening"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def check_process_running(self, process_name):
        """Check if a process is running"""
        try:
            result = subprocess.run(
                ["pgrep", "-f", process_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def get_system_info(self):
        """Get system information"""
        try:
            # Get container IP - try multiple methods
            container_ip = "unknown"
            try:
                result = subprocess.run(
                    ["hostname", "-I"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    container_ip = result.stdout.strip().split()[0]
            except:
                pass
            
            # Try alternative method for IP
            if container_ip == "unknown":
                try:
                    result = subprocess.run(
                        ["ip", "route", "get", "1"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        container_ip = result.stdout.split()[6]
                except:
                    pass
            
            # Get uptime
            uptime = "unknown"
            try:
                with open('/proc/uptime', 'r') as f:
                    uptime_seconds = float(f.readline().split()[0])
                    uptime = str(int(uptime_seconds // 3600)) + "h " + str(int((uptime_seconds % 3600) // 60)) + "m"
            except:
                pass
            
            # Get memory info
            total_mem = "unknown"
            available_mem = "unknown"
            try:
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                    total_line = [line for line in meminfo.split('\n') if 'MemTotal' in line]
                    available_line = [line for line in meminfo.split('\n') if 'MemAvailable' in line]
                    
                    if total_line:
                        total_mem = f"{int(total_line[0].split()[1]) // 1024} MB"
                    if available_line:
                        available_mem = f"{int(available_line[0].split()[1]) // 1024} MB"
            except:
                pass
            
            # Get disk usage
            disk_usage = "unknown"
            try:
                result = subprocess.run(
                    ["df", "-h", "/"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        disk_usage = lines[1].split()[4]
            except:
                pass
            
            return {
                "container_ip": container_ip,
                "uptime": uptime,
                "total_memory": total_mem,
                "available_memory": available_mem,
                "disk_usage": disk_usage
            }
        except Exception as e:
            return {
                "container_ip": "unknown",
                "uptime": "unknown",
                "total_memory": "unknown",
                "available_memory": "unknown",
                "disk_usage": "unknown",
                "error": str(e)
            }
    
    def get_service_logs(self, service_name, lines=10):
        """Get recent logs for a service"""
        try:
            # Try journalctl first
            result = subprocess.run(
                ["journalctl", "-u", service_name, "--no-pager", "-n", str(lines)],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                # Fallback to systemctl status
                result = subprocess.run(
                    ["systemctl", "status", service_name, "--no-pager", "-l"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return result.stdout.strip() if result.returncode == 0 else "No logs available"
        except FileNotFoundError:
            # journalctl/systemctl not available, try log files
            try:
                # Map service names to log files
                log_map = {
                    "media-pipeline": "/var/log/media-pipeline/media_pipeline.log",
                    "media-pipeline-web": "/var/log/media-pipeline/web_ui.log",
                    "syncthing@media-pipeline": "/var/log/media-pipeline/syncthing.log",
                    "nginx": "/var/log/nginx/error.log"
                }
                
                log_file = log_map.get(service_name)
                if log_file and os.path.exists(log_file):
                    # Get last N lines from log file
                    result = subprocess.run(
                        ["tail", "-n", str(lines), log_file],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    return result.stdout.strip() if result.returncode == 0 else "Error reading log file"
                else:
                    return f"Log file not found: {log_file}"
            except Exception as e:
                return f"Logs not available: {str(e)}"
        except Exception as e:
            return f"Error getting logs: {str(e)}"
    
    def get_detailed_system_info(self):
        """Get detailed system information using psutil"""
        try:
            # CPU information
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory information
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk information
            disk = psutil.disk_usage('/')
            
            # Network information
            network = psutil.net_io_counters()
            
            # Load average
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
            
            return {
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "load_avg": load_avg
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "percent": memory.percent,
                    "swap_total": swap.total,
                    "swap_used": swap.used,
                    "swap_percent": swap.percent
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                }
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_database_stats(self):
        """Get database statistics and health"""
        try:
            if not os.path.exists(self.db_path):
                return {"error": "Database file not found"}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get table information
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            table_stats = {}
            total_records = 0
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                table_stats[table] = count
                total_records += count
            
            # Get database size
            db_size = os.path.getsize(self.db_path)
            
            # Check for recent activity (last 24 hours)
            recent_activity = 0
            try:
                cursor.execute("SELECT COUNT(*) FROM media_files WHERE created_at > datetime('now', '-1 day')")
                recent_activity = cursor.fetchone()[0]
            except:
                pass
            
            conn.close()
            
            return {
                "tables": table_stats,
                "total_records": total_records,
                "database_size": db_size,
                "recent_activity_24h": recent_activity,
                "health": "good" if total_records > 0 else "empty"
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_pm2_status(self):
        """Get PM2 process status"""
        try:
            result = subprocess.run(
                ["pm2", "jlist"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                pm2_data = json.loads(result.stdout)
                return {
                    "status": "running",
                    "processes": pm2_data
                }
            else:
                return {"status": "error", "message": result.stderr}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_network_connectivity(self):
        """Test network connectivity to external services"""
        connectivity_tests = {
            "google_dns": {"host": "8.8.8.8", "port": 53, "status": False},
            "cloudflare_dns": {"host": "1.1.1.1", "port": 53, "status": False},
            "nodesource": {"host": "deb.nodesource.com", "port": 443, "status": False},
            "syncthing_apt": {"host": "apt.syncthing.net", "port": 443, "status": False}
        }
        
        for test_name, test_info in connectivity_tests.items():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((test_info["host"], test_info["port"]))
                connectivity_tests[test_name]["status"] = result == 0
                sock.close()
            except:
                connectivity_tests[test_name]["status"] = False
        
        return connectivity_tests
    
    def detect_issues(self, status_data):
        """Detect potential issues and provide troubleshooting suggestions"""
        issues = []
        
        # Check disk space
        if "system" in status_data and "disk_usage" in status_data["system"]:
            disk_usage = status_data["system"]["disk_usage"]
            if disk_usage and "%" in disk_usage:
                usage_percent = int(disk_usage.replace("%", ""))
                if usage_percent > 90:
                    issues.append({
                        "type": "disk_space_low",
                        "severity": "high",
                        "message": f"Disk usage is {usage_percent}%",
                        "guide": self.troubleshooting_guides["disk_space_low"]
                    })
        
        # Check memory usage
        if "detailed_system" in status_data:
            memory_percent = status_data["detailed_system"].get("memory", {}).get("percent", 0)
            if memory_percent > 90:
                issues.append({
                    "type": "memory_high",
                    "severity": "high",
                    "message": f"Memory usage is {memory_percent}%",
                    "guide": self.troubleshooting_guides["memory_high"]
                })
        
        # Check Node.js availability
        if not self.check_process_running("node") and not self.check_process_running("npm"):
            issues.append({
                "type": "nodejs_not_found",
                "severity": "critical",
                "message": "Node.js/NPM not found",
                "guide": self.troubleshooting_guides["nodejs_not_found"]
            })
        
        # Check database health
        db_stats = self.get_database_stats()
        if "error" in db_stats:
            issues.append({
                "type": "database_corrupted",
                "severity": "high",
                "message": f"Database error: {db_stats['error']}",
                "guide": self.troubleshooting_guides["database_corrupted"]
            })
        
        # Check Syncthing connectivity
        if not self.check_port_listening(8385):
            issues.append({
                "type": "syncthing_connection_failed",
                "severity": "medium",
                "message": "Syncthing not accessible on port 8385",
                "guide": self.troubleshooting_guides["syncthing_connection_failed"]
            })
        
        return issues
    
    def get_all_status(self):
        """Get comprehensive status of all services and components"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "system": self.get_system_info(),
            "detailed_system": self.get_detailed_system_info(),
            "services": {},
            "ports": {},
            "processes": {},
            "files": {},
            "logs": {},
            "database": self.get_database_stats(),
            "pm2": self.get_pm2_status(),
            "network_connectivity": self.get_network_connectivity(),
            "issues": []
        }
        
        # Check systemd services
        services_to_check = [
            "media-pipeline",
            "media-pipeline-web", 
            "syncthing@media-pipeline",
            "nginx"
        ]
        
        for service in services_to_check:
            status["services"][service] = self.check_systemctl_service(service)
            status["logs"][service] = self.get_service_logs(service, 5)
        
        # Check ports
        ports_to_check = [8080, 8081, 8082, 8083, 8084, 8384, 8385, 9615]
        for port in ports_to_check:
            status["ports"][f"port_{port}"] = {
                "listening": self.check_port_listening(port),
                "port": port
            }
        
        # Check processes
        processes_to_check = ["python", "syncthing", "nginx", "node", "pm2"]
        for process in processes_to_check:
            status["processes"][process] = {
                "running": self.check_process_running(process)
            }
        
        # Check important files
        files_to_check = [
            "/opt/media-pipeline/.env",
            "/opt/media-pipeline/config.yaml",
            "/opt/media-pipeline/media.db",
            "/opt/media-pipeline/ecosystem.config.js",
            "/var/log/media-pipeline/media_pipeline.log"
        ]
        
        for file_path in files_to_check:
            status["files"][file_path] = {
                "exists": os.path.exists(file_path),
                "readable": os.access(file_path, os.R_OK) if os.path.exists(file_path) else False,
                "size": os.path.getsize(file_path) if os.path.exists(file_path) else 0
            }
        
        # Detect issues
        status["issues"] = self.detect_issues(status)
        
        return status

# Global status checker
status_checker = ServiceStatusChecker()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('status_dashboard.html')

@app.route('/api/status')
def get_status():
    """API endpoint to get current status"""
    return jsonify(status_checker.get_all_status())

@app.route('/api/service/<service_name>/logs')
def get_service_logs(service_name):
    """API endpoint to get service logs"""
    lines = request.args.get('lines', 20, type=int)
    logs = status_checker.get_service_logs(service_name, lines)
    return jsonify({"logs": logs})

@app.route('/api/service/<service_name>/restart', methods=['POST'])
def restart_service(service_name):
    """API endpoint to restart a service"""
    try:
        result = subprocess.run(
            ["systemctl", "restart", service_name],
            capture_output=True,
            text=True,
            timeout=30
        )
        return jsonify({
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/service/<service_name>/start', methods=['POST'])
def start_service(service_name):
    """API endpoint to start a service"""
    try:
        result = subprocess.run(
            ["systemctl", "start", service_name],
            capture_output=True,
            text=True,
            timeout=30
        )
        return jsonify({
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/service/<service_name>/stop', methods=['POST'])
def stop_service(service_name):
    """API endpoint to stop a service"""
    try:
        result = subprocess.run(
            ["systemctl", "stop", service_name],
            capture_output=True,
            text=True,
            timeout=30
        )
        return jsonify({
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/logs/<log_type>')
def get_logs(log_type):
    """API endpoint to get various types of logs"""
    lines = request.args.get('lines', 50, type=int)
    
    log_files = {
        'system': '/var/log/syslog',
        'nginx': '/var/log/nginx/error.log',
        'media_pipeline': '/var/log/media-pipeline/media_pipeline.log',
        'pm2': '/var/log/media-pipeline/pm2.log',
        'syncthing': '/var/log/media-pipeline/syncthing.log'
    }
    
    if log_type not in log_files:
        return jsonify({"error": "Invalid log type"})
    
    log_file = log_files[log_type]
    if not os.path.exists(log_file):
        return jsonify({"error": "Log file not found"})
    
    try:
        result = subprocess.run(
            ["tail", "-n", str(lines), log_file],
            capture_output=True,
            text=True,
            timeout=10
        )
        return jsonify({
            "logs": result.stdout,
            "file": log_file,
            "lines": lines
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/execute_command', methods=['POST'])
def execute_command():
    """API endpoint to execute system commands (with restrictions)"""
    data = request.get_json()
    command = data.get('command', '')
    
    # Whitelist of safe commands
    allowed_commands = [
        'df -h',
        'free -h',
        'uptime',
        'ps aux',
        'netstat -tlnp',
        'systemctl status',
        'pm2 status',
        'pm2 logs',
        'pm2 restart all',
        'pm2 stop all',
        'pm2 start all'
    ]
    
    if command not in allowed_commands:
        return jsonify({"error": "Command not allowed"})
    
    try:
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            timeout=30
        )
        return jsonify({
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr,
            "command": command
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "command": command
        })

@app.route('/api/troubleshooting/<issue_type>')
def get_troubleshooting_guide(issue_type):
    """API endpoint to get troubleshooting guide for specific issue"""
    if issue_type in status_checker.troubleshooting_guides:
        return jsonify(status_checker.troubleshooting_guides[issue_type])
    else:
        return jsonify({"error": "Troubleshooting guide not found"})

@app.route('/api/database/query', methods=['POST'])
def execute_database_query():
    """API endpoint to execute database queries"""
    data = request.get_json()
    query = data.get('query', '')
    
    # Only allow SELECT queries for safety
    if not query.strip().upper().startswith('SELECT'):
        return jsonify({"error": "Only SELECT queries are allowed"})
    
    try:
        conn = sqlite3.connect(status_checker.db_path)
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        conn.close()
        
        return jsonify({
            "success": True,
            "columns": columns,
            "rows": rows,
            "count": len(rows)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    emit('status', status_checker.get_all_status())

@socketio.on('request_status')
def handle_status_request():
    """Handle status update request"""
    emit('status', status_checker.get_all_status())

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    templates_dir = os.path.join(project_dir, "templates")
    os.makedirs(templates_dir, exist_ok=True)
    
    # Create the status dashboard template
    dashboard_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Media Pipeline Status Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .status-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .status-card h3 { margin-top: 0; color: #2c3e50; }
        .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
        .status-active { background-color: #27ae60; }
        .status-inactive { background-color: #e74c3c; }
        .status-error { background-color: #f39c12; }
        .service-item { display: flex; justify-content: space-between; align-items: center; padding: 10px; border-bottom: 1px solid #eee; }
        .service-item:last-child { border-bottom: none; }
        .service-actions { display: flex; gap: 10px; }
        .btn { padding: 5px 10px; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; }
        .btn-start { background-color: #27ae60; color: white; }
        .btn-stop { background-color: #e74c3c; color: white; }
        .btn-restart { background-color: #3498db; color: white; }
        .btn:hover { opacity: 0.8; }
        .logs { background-color: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 4px; font-family: monospace; font-size: 12px; max-height: 200px; overflow-y: auto; white-space: pre-wrap; }
        .timestamp { color: #7f8c8d; font-size: 12px; }
        .refresh-btn { background-color: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin-bottom: 20px; }
        .refresh-btn:hover { background-color: #2980b9; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Media Pipeline Status Dashboard</h1>
            <p class="timestamp">Last updated: <span id="last-updated">Loading...</span></p>
        </div>
        
        <button class="refresh-btn" onclick="requestStatus()">Refresh Status</button>
        
        <div class="status-grid">
            <div class="status-card">
                <h3>System Information</h3>
                <div id="system-info">Loading...</div>
            </div>
            
            <div class="status-card">
                <h3>Services Status</h3>
                <div id="services-status">Loading...</div>
            </div>
            
            <div class="status-card">
                <h3>Port Status</h3>
                <div id="ports-status">Loading...</div>
            </div>
            
            <div class="status-card">
                <h3>Process Status</h3>
                <div id="processes-status">Loading...</div>
            </div>
            
            <div class="status-card">
                <h3>File Status</h3>
                <div id="files-status">Loading...</div>
            </div>
            
            <div class="status-card">
                <h3>Service Logs</h3>
                <div id="logs-status">Loading...</div>
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        
        socket.on('connect', function() {
            console.log('Connected to server');
            requestStatus();
        });
        
        socket.on('status', function(data) {
            updateDashboard(data);
        });
        
        function requestStatus() {
            socket.emit('request_status');
        }
        
        function updateDashboard(data) {
            document.getElementById('last-updated').textContent = new Date(data.timestamp).toLocaleString();
            
            // Update system info
            const systemInfo = document.getElementById('system-info');
            systemInfo.innerHTML = `
                <p><strong>Container IP:</strong> ${data.system.container_ip}</p>
                <p><strong>Uptime:</strong> ${data.system.uptime}</p>
                <p><strong>Memory:</strong> ${data.system.available_memory} / ${data.system.total_memory}</p>
                <p><strong>Disk Usage:</strong> ${data.system.disk_usage}</p>
            `;
            
            // Update services status
            const servicesStatus = document.getElementById('services-status');
            let servicesHtml = '';
            for (const [service, status] of Object.entries(data.services)) {
                const statusClass = status.running ? 'status-active' : 'status-inactive';
                servicesHtml += `
                    <div class="service-item">
                        <div>
                            <span class="status-indicator ${statusClass}"></span>
                            <strong>${service}</strong>
                        </div>
                        <div class="service-actions">
                            <button class="btn btn-start" onclick="controlService('${service}', 'start')">Start</button>
                            <button class="btn btn-stop" onclick="controlService('${service}', 'stop')">Stop</button>
                            <button class="btn btn-restart" onclick="controlService('${service}', 'restart')">Restart</button>
                        </div>
                    </div>
                `;
            }
            servicesStatus.innerHTML = servicesHtml;
            
            // Update ports status
            const portsStatus = document.getElementById('ports-status');
            let portsHtml = '';
            for (const [portName, status] of Object.entries(data.ports)) {
                const statusClass = status.listening ? 'status-active' : 'status-inactive';
                portsHtml += `
                    <div class="service-item">
                        <div>
                            <span class="status-indicator ${statusClass}"></span>
                            <strong>Port ${status.port}</strong>
                        </div>
                        <div>${status.listening ? 'Listening' : 'Not Listening'}</div>
                    </div>
                `;
            }
            portsStatus.innerHTML = portsHtml;
            
            // Update processes status
            const processesStatus = document.getElementById('processes-status');
            let processesHtml = '';
            for (const [process, status] of Object.entries(data.processes)) {
                const statusClass = status.running ? 'status-active' : 'status-inactive';
                processesHtml += `
                    <div class="service-item">
                        <div>
                            <span class="status-indicator ${statusClass}"></span>
                            <strong>${process}</strong>
                        </div>
                        <div>${status.running ? 'Running' : 'Not Running'}</div>
                    </div>
                `;
            }
            processesStatus.innerHTML = processesHtml;
            
            // Update files status
            const filesStatus = document.getElementById('files-status');
            let filesHtml = '';
            for (const [file, status] of Object.entries(data.files)) {
                const statusClass = status.exists ? 'status-active' : 'status-inactive';
                filesHtml += `
                    <div class="service-item">
                        <div>
                            <span class="status-indicator ${statusClass}"></span>
                            <strong>${file.split('/').pop()}</strong>
                        </div>
                        <div>${status.exists ? `${(status.size / 1024).toFixed(1)} KB` : 'Missing'}</div>
                    </div>
                `;
            }
            filesStatus.innerHTML = filesHtml;
            
            // Update logs
            const logsStatus = document.getElementById('logs-status');
            let logsHtml = '';
            for (const [service, logs] of Object.entries(data.logs)) {
                logsHtml += `
                    <h4>${service}</h4>
                    <div class="logs">${logs}</div>
                `;
            }
            logsStatus.innerHTML = logsHtml;
        }
        
        function controlService(service, action) {
            fetch(`/api/service/${service}/${action}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(`${action} ${service} successful`);
                    setTimeout(requestStatus, 1000);
                } else {
                    alert(`Failed to ${action} ${service}: ${data.error}`);
                }
            })
            .catch(error => {
                alert(`Error: ${error}`);
            });
        }
        
        // Auto-refresh every 30 seconds
        setInterval(requestStatus, 30000);
    </script>
</body>
</html>"""
    
    # Write the template file
    with open(os.path.join(templates_dir, "status_dashboard.html"), "w") as f:
        f.write(dashboard_template)
    
    print("Starting Media Pipeline Status Dashboard...")
    print("Dashboard will be available at: http://0.0.0.0:8082")
    print("Press Ctrl+C to stop")
    
    # Run the Flask app
    # Check for PORT environment variable (PM2 override)
    port = int(os.environ.get('PORT', 8082))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
