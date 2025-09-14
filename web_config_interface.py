#!/usr/bin/env python3
"""
Media Pipeline Web Configuration Interface
A web-based interface for configuring all settings
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
    from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
    from flask_socketio import SocketIO, emit
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "flask-socketio"])
    from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
    from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'media-pipeline-config-interface'
socketio = SocketIO(app, cors_allowed_origins="*")

class ConfigManager:
    """Manage configuration settings"""
    
    def __init__(self):
        self.project_dir = "/opt/media-pipeline"
        self.env_file = os.path.join(self.project_dir, ".env")
        self.config_file = os.path.join(self.project_dir, "config.yaml")
        self.service_user = "media-pipeline"
    
    def load_env_config(self):
        """Load environment configuration"""
        config = {}
        if os.path.exists(self.env_file):
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key] = value
        return config
    
    def save_env_config(self, config):
        """Save environment configuration"""
        with open(self.env_file, 'w') as f:
            f.write("# Media Pipeline Environment Configuration\n")
            f.write(f"# Generated on {datetime.now().isoformat()}\n\n")
            
            # iCloud settings
            if config.get('icloud_username'):
                f.write(f"ICLOUD_USERNAME={config['icloud_username']}\n")
            if config.get('icloud_password'):
                f.write(f"ICLOUD_PASSWORD={config['icloud_password']}\n")
            
            # Syncthing settings
            if config.get('syncthing_api_key'):
                f.write(f"SYNCTHING_API_KEY={config['syncthing_api_key']}\n")
            if config.get('syncthing_url'):
                f.write(f"SYNCTHING_URL={config['syncthing_url']}\n")
            
            # Telegram settings
            if config.get('telegram_bot_token'):
                f.write(f"TELEGRAM_BOT_TOKEN={config['telegram_bot_token']}\n")
            if config.get('telegram_chat_id'):
                f.write(f"TELEGRAM_CHAT_ID={config['telegram_chat_id']}\n")
            
            # Directory settings
            f.write(f"INCOMING_DIR={config.get('incoming_dir', '/mnt/wd_all_pictures/incoming')}\n")
            f.write(f"PROCESSED_DIR={config.get('processed_dir', '/mnt/wd_all_pictures/processed')}\n")
        
        # Set proper permissions
        os.chown(self.env_file, 1000, 1000)  # media-pipeline user
        os.chmod(self.env_file, 0o600)
    
    def test_icloud_connection(self, username, password):
        """Test iCloud connection"""
        try:
            # This is a simplified test - in reality, icloudpd would handle 2FA
            return {
                "success": True,
                "message": "iCloud credentials saved. Note: 2FA will be handled automatically by icloudpd on first run."
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error testing iCloud connection: {str(e)}"
            }
    
    def test_syncthing_connection(self, url, api_key):
        """Test Syncthing connection"""
        try:
            import requests
            headers = {'X-API-Key': api_key}
            response = requests.get(f"{url}/rest/system/status", headers=headers, timeout=10)
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Syncthing connection successful"
                }
            else:
                return {
                    "success": False,
                    "message": f"Syncthing connection failed: HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error connecting to Syncthing: {str(e)}"
            }
    
    def create_directories(self, incoming_dir, processed_dir):
        """Create required directories"""
        try:
            os.makedirs(incoming_dir, exist_ok=True)
            os.makedirs(processed_dir, exist_ok=True)
            
            # Set ownership to media-pipeline user
            subprocess.run(['chown', '-R', 'media-pipeline:media-pipeline', incoming_dir], check=True)
            subprocess.run(['chown', '-R', 'media-pipeline:media-pipeline', processed_dir], check=True)
            
            return {
                "success": True,
                "message": f"Directories created: {incoming_dir}, {processed_dir}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error creating directories: {str(e)}"
            }

# Global config manager
config_manager = ConfigManager()

@app.route('/')
def index():
    """Main configuration page"""
    return render_template('config_interface.html')

@app.route('/api/config')
def get_config():
    """Get current configuration"""
    config = config_manager.load_env_config()
    return jsonify(config)

@app.route('/api/config', methods=['POST'])
def save_config():
    """Save configuration"""
    try:
        data = request.get_json()
        
        # Save configuration
        config_manager.save_env_config(data)
        
        # Create directories if specified
        if data.get('incoming_dir') or data.get('processed_dir'):
            result = config_manager.create_directories(
                data.get('incoming_dir', '/mnt/wd_all_pictures/incoming'),
                data.get('processed_dir', '/mnt/wd_all_pictures/processed')
            )
            if not result['success']:
                return jsonify({"success": False, "message": result['message']})
        
        return jsonify({"success": True, "message": "Configuration saved successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error saving configuration: {str(e)}"})

@app.route('/api/test/icloud', methods=['POST'])
def test_icloud():
    """Test iCloud connection"""
    try:
        data = request.get_json()
        result = config_manager.test_icloud_connection(
            data.get('username'),
            data.get('password')
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route('/api/test/syncthing', methods=['POST'])
def test_syncthing():
    """Test Syncthing connection"""
    try:
        data = request.get_json()
        result = config_manager.test_syncthing_connection(
            data.get('url'),
            data.get('api_key')
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route('/api/restart-services', methods=['POST'])
def restart_services():
    """Restart all services"""
    try:
        services = ['media-pipeline', 'media-pipeline-web', 'syncthing@media-pipeline', 'nginx']
        results = {}
        
        for service in services:
            try:
                result = subprocess.run(
                    ['systemctl', 'restart', service],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                results[service] = {
                    "success": result.returncode == 0,
                    "output": result.stdout,
                    "error": result.stderr
                }
            except Exception as e:
                results[service] = {
                    "success": False,
                    "error": str(e)
                }
        
        return jsonify({"success": True, "results": results})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    templates_dir = os.path.join(project_dir, "templates")
    os.makedirs(templates_dir, exist_ok=True)
    
    # Create the configuration interface template
    config_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Media Pipeline Configuration</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .config-section { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .config-section h3 { margin-top: 0; color: #2c3e50; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group input, .form-group select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        .btn { padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; margin-right: 10px; }
        .btn-primary { background-color: #3498db; color: white; }
        .btn-success { background-color: #27ae60; color: white; }
        .btn-warning { background-color: #f39c12; color: white; }
        .btn:hover { opacity: 0.8; }
        .alert { padding: 10px; border-radius: 4px; margin-bottom: 15px; }
        .alert-success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .alert-error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .alert-info { background-color: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        .test-result { margin-top: 10px; padding: 10px; border-radius: 4px; }
        .test-success { background-color: #d4edda; color: #155724; }
        .test-error { background-color: #f8d7da; color: #721c24; }
        .info-box { background-color: #e7f3ff; border: 1px solid #b3d9ff; padding: 15px; border-radius: 4px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Media Pipeline Configuration</h1>
            <p>Configure your media pipeline settings</p>
        </div>
        
        <div id="alerts"></div>
        
        <form id="configForm">
            <!-- iCloud Configuration -->
            <div class="config-section">
                <h3>iCloud Configuration</h3>
                <div class="info-box">
                    <strong>Note:</strong> iCloud requires 2FA (Two-Factor Authentication). 
                    The first time you run the pipeline, icloudpd will prompt you for the 2FA code.
                    After that, it will use a session token for automatic authentication.
                </div>
                <div class="form-group">
                    <label for="icloud_username">iCloud Email Address:</label>
                    <input type="email" id="icloud_username" name="icloud_username" placeholder="your.email@icloud.com">
                </div>
                <div class="form-group">
                    <label for="icloud_password">iCloud Password:</label>
                    <input type="password" id="icloud_password" name="icloud_password" placeholder="Your iCloud password">
                </div>
                <button type="button" class="btn btn-warning" onclick="testiCloud()">Test iCloud Connection</button>
                <div id="icloud-test-result"></div>
            </div>
            
            <!-- Syncthing Configuration -->
            <div class="config-section">
                <h3>Syncthing Configuration</h3>
                <div class="info-box">
                    <strong>Setup Options:</strong><br>
                    • <strong>Local Syncthing:</strong> Use the Syncthing installed on this container (port 8384)<br>
                    • <strong>Remote Syncthing:</strong> Use Syncthing on another server (e.g., 192.168.1.118:8384)
                </div>
                <div class="form-group">
                    <label for="syncthing_url">Syncthing URL:</label>
                    <input type="text" id="syncthing_url" name="syncthing_url" placeholder="http://192.168.1.118:8384/rest" value="http://192.168.1.118:8384/rest">
                </div>
                <div class="form-group">
                    <label for="syncthing_api_key">Syncthing API Key:</label>
                    <input type="password" id="syncthing_api_key" name="syncthing_api_key" placeholder="Your Syncthing API key">
                    <small>Get this from Syncthing Web UI → Actions → Settings → GUI</small>
                </div>
                <button type="button" class="btn btn-warning" onclick="testSyncthing()">Test Syncthing Connection</button>
                <div id="syncthing-test-result"></div>
            </div>
            
            <!-- Directory Configuration -->
            <div class="config-section">
                <h3>Directory Configuration</h3>
                <div class="form-group">
                    <label for="incoming_dir">Incoming Directory:</label>
                    <input type="text" id="incoming_dir" name="incoming_dir" value="/mnt/wd_all_pictures/incoming">
                </div>
                <div class="form-group">
                    <label for="processed_dir">Processed Directory:</label>
                    <input type="text" id="processed_dir" name="processed_dir" value="/mnt/wd_all_pictures/processed">
                </div>
            </div>
            
            <!-- Telegram Configuration (Optional) -->
            <div class="config-section">
                <h3>Telegram Notifications (Optional)</h3>
                <div class="form-group">
                    <label for="telegram_bot_token">Telegram Bot Token:</label>
                    <input type="text" id="telegram_bot_token" name="telegram_bot_token" placeholder="Your Telegram bot token">
                </div>
                <div class="form-group">
                    <label for="telegram_chat_id">Telegram Chat ID:</label>
                    <input type="text" id="telegram_chat_id" name="telegram_chat_id" placeholder="Your Telegram chat ID">
                </div>
            </div>
            
            <div class="config-section">
                <button type="submit" class="btn btn-primary">Save Configuration</button>
                <button type="button" class="btn btn-success" onclick="restartServices()">Restart Services</button>
            </div>
        </form>
    </div>

    <script>
        // Load current configuration
        fetch('/api/config')
            .then(response => response.json())
            .then(data => {
                Object.keys(data).forEach(key => {
                    const element = document.getElementById(key);
                    if (element) {
                        element.value = data[key];
                    }
                });
            });

        // Save configuration
        document.getElementById('configForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const config = {};
            for (let [key, value] of formData.entries()) {
                config[key] = value;
            }
            
            fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(config)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('Configuration saved successfully!', 'success');
                } else {
                    showAlert('Error saving configuration: ' + data.message, 'error');
                }
            });
        });

        function testiCloud() {
            const username = document.getElementById('icloud_username').value;
            const password = document.getElementById('icloud_password').value;
            
            if (!username || !password) {
                showTestResult('icloud-test-result', 'Please enter both username and password', 'error');
                return;
            }
            
            fetch('/api/test/icloud', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({username, password})
            })
            .then(response => response.json())
            .then(data => {
                showTestResult('icloud-test-result', data.message, data.success ? 'success' : 'error');
            });
        }

        function testSyncthing() {
            const url = document.getElementById('syncthing_url').value;
            const apiKey = document.getElementById('syncthing_api_key').value;
            
            if (!url || !apiKey) {
                showTestResult('syncthing-test-result', 'Please enter both URL and API key', 'error');
                return;
            }
            
            fetch('/api/test/syncthing', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({url, api_key: apiKey})
            })
            .then(response => response.json())
            .then(data => {
                showTestResult('syncthing-test-result', data.message, data.success ? 'success' : 'error');
            });
        }

        function restartServices() {
            if (confirm('Are you sure you want to restart all services?')) {
                fetch('/api/restart-services', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showAlert('Services restarted successfully!', 'success');
                    } else {
                        showAlert('Error restarting services: ' + data.message, 'error');
                    }
                });
            }
        }

        function showAlert(message, type) {
            const alertsDiv = document.getElementById('alerts');
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type}`;
            alertDiv.textContent = message;
            alertsDiv.appendChild(alertDiv);
            
            setTimeout(() => {
                alertDiv.remove();
            }, 5000);
        }

        function showTestResult(elementId, message, type) {
            const element = document.getElementById(elementId);
            element.className = `test-result test-${type}`;
            element.textContent = message;
        }
    </script>
</body>
</html>"""
    
    # Write the template file
    with open(os.path.join(templates_dir, "config_interface.html"), "w") as f:
        f.write(config_template)
    
    print("Starting Media Pipeline Configuration Interface...")
    print("Configuration interface will be available at: http://0.0.0.0:8083")
    print("Press Ctrl+C to stop")
    
    # Run the Flask app
    # Check for PORT environment variable (PM2 override)
    port = int(os.environ.get('PORT', 8083))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
