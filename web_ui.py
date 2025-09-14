#!/usr/bin/env python3
"""
Media Pipeline Web UI
Provides a comprehensive web interface for monitoring and controlling the media pipeline
"""

import os
import json
import time
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import psutil
from common import config_manager, db_manager, get_logger
from telegram_notifier import telegram_notifier

# Setup logging
logger = get_logger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables for real-time updates
pipeline_status = {
    'running': False,
    'current_stage': None,
    'start_time': None,
    'progress': 0,
    'last_update': None
}

class WebUIManager:
    """Manages the web UI functionality"""
    
    def __init__(self):
        self.config = config_manager
        self.db = db_manager
        self.telegram = telegram_notifier
        self.start_time = datetime.now()
    
    def get_system_info(self):
        """Get system information"""
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Storage directory info
            storage_path = "/mnt/wd_all_pictures"
            storage_info = {}
            if os.path.exists(storage_path):
                storage_disk = psutil.disk_usage(storage_path)
                storage_info = {
                    'total': storage_disk.total,
                    'used': storage_disk.used,
                    'free': storage_disk.free,
                    'percent': (storage_disk.used / storage_disk.total) * 100
                }
            
            return {
                'cpu_percent': cpu_percent,
                'memory': {
                    'total': memory.total,
                    'used': memory.used,
                    'free': memory.free,
                    'percent': memory.percent
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                },
                'storage': storage_info,
                'uptime': str(datetime.now() - self.start_time),
                'hostname': os.uname().nodename
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {}
    
    def get_pipeline_stats(self):
        """Get pipeline statistics"""
        try:
            stats = self.db.get_pipeline_stats()
            return stats
        except Exception as e:
            logger.error(f"Error getting pipeline stats: {e}")
            return {}
    
    def get_recent_logs(self, lines=100):
        """Get recent log entries"""
        try:
            log_file = os.path.join(config_manager.get_logging_config().log_dir, 
                                  config_manager.get_logging_config().log_file)
            
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    all_lines = f.readlines()
                    return all_lines[-lines:] if len(all_lines) > lines else all_lines
            return []
        except Exception as e:
            logger.error(f"Error reading logs: {e}")
            return []
    
    def get_service_status(self):
        """Get status of all services"""
        try:
            import subprocess
            
            services = {
                'syncthing': 'syncthing@media-pipeline',
                'media_pipeline': 'media-pipeline',
                'media_pipeline_web': 'media-pipeline-web',
                'nginx': 'nginx'
            }
            
            status = {}
            for name, service in services.items():
                try:
                    result = subprocess.run(['systemctl', 'is-active', service], 
                                          capture_output=True, text=True)
                    status[name] = {
                        'active': result.stdout.strip() == 'active',
                        'status': result.stdout.strip()
                    }
                except:
                    status[name] = {'active': False, 'status': 'unknown'}
            
            return status
        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return {}
    
    def get_directory_info(self):
        """Get information about pipeline directories"""
        try:
            dir_config = self.config.get_directory_config()
            directories = ['incoming', 'backup', 'compress', 'delete_pending', 'processed']
            
            info = {}
            for dir_name in directories:
                dir_path = getattr(dir_config, dir_name)
                if os.path.exists(dir_path):
                    # Count files
                    file_count = 0
                    total_size = 0
                    
                    for root, dirs, files in os.walk(dir_path):
                        file_count += len(files)
                        for file in files:
                            try:
                                file_path = os.path.join(root, file)
                                total_size += os.path.getsize(file_path)
                            except:
                                pass
                    
                    info[dir_name] = {
                        'path': dir_path,
                        'exists': True,
                        'file_count': file_count,
                        'total_size': total_size,
                        'size_mb': total_size / (1024 * 1024)
                    }
                else:
                    info[dir_name] = {
                        'path': dir_path,
                        'exists': False,
                        'file_count': 0,
                        'total_size': 0,
                        'size_mb': 0
                    }
            
            return info
        except Exception as e:
            logger.error(f"Error getting directory info: {e}")
            return {}

# Initialize Web UI Manager
web_manager = WebUIManager()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """API endpoint for system status"""
    return jsonify({
        'system': web_manager.get_system_info(),
        'pipeline': web_manager.get_pipeline_stats(),
        'services': web_manager.get_service_status(),
        'directories': web_manager.get_directory_info(),
        'pipeline_status': pipeline_status,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/logs')
def api_logs():
    """API endpoint for recent logs"""
    lines = request.args.get('lines', 100, type=int)
    logs = web_manager.get_recent_logs(lines)
    return jsonify({
        'logs': logs,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/pipeline/run', methods=['POST'])
def api_run_pipeline():
    """API endpoint to run pipeline"""
    try:
        data = request.get_json()
        stages = data.get('stages', [])
        dry_run = data.get('dry_run', False)
        
        # Start pipeline in background thread
        def run_pipeline():
            try:
                global pipeline_status
                pipeline_status['running'] = True
                pipeline_status['start_time'] = datetime.now()
                pipeline_status['current_stage'] = 'Starting...'
                pipeline_status['progress'] = 0
                
                socketio.emit('pipeline_update', pipeline_status)
                
                # Import and run pipeline
                from pipeline_orchestrator import PipelineOrchestrator
                orchestrator = PipelineOrchestrator()
                
                if stages:
                    results = orchestrator.run_pipeline(stages, dry_run)
                else:
                    results = orchestrator.run_pipeline(dry_run=dry_run)
                
                pipeline_status['running'] = False
                pipeline_status['current_stage'] = 'Completed'
                pipeline_status['progress'] = 100
                pipeline_status['last_update'] = datetime.now()
                
                socketio.emit('pipeline_complete', {
                    'status': pipeline_status,
                    'results': results
                })
                
            except Exception as e:
                logger.error(f"Pipeline execution error: {e}")
                pipeline_status['running'] = False
                pipeline_status['current_stage'] = f'Error: {str(e)}'
                socketio.emit('pipeline_error', {
                    'status': pipeline_status,
                    'error': str(e)
                })
        
        thread = threading.Thread(target=run_pipeline)
        thread.daemon = True
        thread.start()
        
        return jsonify({'status': 'started', 'message': 'Pipeline execution started'})
        
    except Exception as e:
        logger.error(f"Error starting pipeline: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/pipeline/stop', methods=['POST'])
def api_stop_pipeline():
    """API endpoint to stop pipeline"""
    try:
        global pipeline_status
        pipeline_status['running'] = False
        pipeline_status['current_stage'] = 'Stopped'
        pipeline_status['last_update'] = datetime.now()
        
        socketio.emit('pipeline_stopped', pipeline_status)
        
        return jsonify({'status': 'stopped', 'message': 'Pipeline stopped'})
        
    except Exception as e:
        logger.error(f"Error stopping pipeline: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/telegram/test', methods=['POST'])
def api_test_telegram():
    """API endpoint to test Telegram connection"""
    try:
        success = telegram_notifier.send_test_message()
        return jsonify({
            'status': 'success' if success else 'error',
            'message': 'Test message sent' if success else 'Failed to send test message'
        })
    except Exception as e:
        logger.error(f"Error testing Telegram: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/services/<service_name>/<action>', methods=['POST'])
def api_service_control(service_name, action):
    """API endpoint to control services"""
    try:
        import subprocess
        
        service_map = {
            'syncthing': 'syncthing@media-pipeline',
            'media_pipeline': 'media-pipeline',
            'media_pipeline_web': 'media-pipeline-web',
            'nginx': 'nginx'
        }
        
        if service_name not in service_map:
            return jsonify({'status': 'error', 'message': 'Unknown service'}), 400
        
        service = service_map[service_name]
        
        if action in ['start', 'stop', 'restart']:
            result = subprocess.run(['sudo', 'systemctl', action, service], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                return jsonify({'status': 'success', 'message': f'Service {action}ed successfully'})
            else:
                return jsonify({'status': 'error', 'message': result.stderr}), 500
        else:
            return jsonify({'status': 'error', 'message': 'Invalid action'}), 400
            
    except Exception as e:
        logger.error(f"Error controlling service: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('Client connected to WebSocket')
    emit('connected', {'message': 'Connected to Media Pipeline WebSocket'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected from WebSocket')

@socketio.on('request_status')
def handle_status_request():
    """Handle status request from client"""
    emit('status_update', {
        'system': web_manager.get_system_info(),
        'pipeline': web_manager.get_pipeline_stats(),
        'services': web_manager.get_service_status(),
        'directories': web_manager.get_directory_info(),
        'pipeline_status': pipeline_status,
        'timestamp': datetime.now().isoformat()
    })

def broadcast_status_update():
    """Broadcast status update to all connected clients"""
    socketio.emit('status_update', {
        'system': web_manager.get_system_info(),
        'pipeline': web_manager.get_pipeline_stats(),
        'services': web_manager.get_service_status(),
        'directories': web_manager.get_directory_info(),
        'pipeline_status': pipeline_status,
        'timestamp': datetime.now().isoformat()
    })

# Background thread for periodic updates
def status_broadcaster():
    """Background thread to broadcast status updates"""
    while True:
        try:
            broadcast_status_update()
            time.sleep(30)  # Update every 30 seconds
        except Exception as e:
            logger.error(f"Error in status broadcaster: {e}")
            time.sleep(60)  # Wait longer on error

# Start background thread
status_thread = threading.Thread(target=status_broadcaster)
status_thread.daemon = True
status_thread.start()

if __name__ == '__main__':
    # Get configuration
    web_config = config_manager.get_logging_config()  # Using logging config for now
    host = '127.0.0.1'
    port = 8080
    
    # Check for PORT environment variable first (PM2 override)
    if 'PORT' in os.environ:
        port = int(os.environ['PORT'])
    else:
        # Try to get web UI specific config
        try:
            config_data = config_manager._config_data
            web_ui_config = config_data.get('web_ui', {})
            host = web_ui_config.get('host', host)
            port = web_ui_config.get('port', port)
        except:
            pass
    
    logger.info(f"Starting Media Pipeline Web UI on {host}:{port}")
    socketio.run(app, host=host, port=port, debug=False)
