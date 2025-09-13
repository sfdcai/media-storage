#!/usr/bin/env python3
"""
Media Pipeline Status Dashboard
A standalone web UI that shows the status of all services and components
"""

import os
import sys
import json
import subprocess
import socket
import time
from datetime import datetime
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
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "flask-socketio"])
    from flask import Flask, render_template, jsonify, request
    from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'media-pipeline-status-dashboard'
socketio = SocketIO(app, cors_allowed_origins="*")

class ServiceStatusChecker:
    """Check the status of various services and components"""
    
    def __init__(self):
        self.project_dir = "/opt/media-pipeline"
        self.service_user = "media-pipeline"
        self.log_dir = "/var/log/media-pipeline"
    
    def check_systemctl_service(self, service_name):
        """Check if a systemd service is active"""
        try:
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
            # journalctl not available, try alternative methods
            try:
                # Try systemctl status
                result = subprocess.run(
                    ["systemctl", "status", service_name, "--no-pager", "-l"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return result.stdout.strip() if result.returncode == 0 else "No logs available"
            except Exception as e:
                return f"Logs not available: {str(e)}"
        except Exception as e:
            return f"Error getting logs: {str(e)}"
    
    def get_all_status(self):
        """Get comprehensive status of all services and components"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "system": self.get_system_info(),
            "services": {},
            "ports": {},
            "processes": {},
            "files": {},
            "logs": {}
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
        ports_to_check = [8080, 8081, 8384]
        for port in ports_to_check:
            status["ports"][f"port_{port}"] = {
                "listening": self.check_port_listening(port),
                "port": port
            }
        
        # Check processes
        processes_to_check = ["python", "syncthing", "nginx"]
        for process in processes_to_check:
            status["processes"][process] = {
                "running": self.check_process_running(process)
            }
        
        # Check important files
        files_to_check = [
            "/opt/media-pipeline/.env",
            "/opt/media-pipeline/config.yaml",
            "/opt/media-pipeline/media.db",
            "/var/log/media-pipeline/media_pipeline.log"
        ]
        
        for file_path in files_to_check:
            status["files"][file_path] = {
                "exists": os.path.exists(file_path),
                "readable": os.access(file_path, os.R_OK) if os.path.exists(file_path) else False,
                "size": os.path.getsize(file_path) if os.path.exists(file_path) else 0
            }
        
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
    socketio.run(app, host='0.0.0.0', port=8082, debug=False)
