"""
Real-time workflow tracking and monitoring system
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from threading import Thread, Lock


class WorkflowTracker:
    """Real-time workflow tracking with progress monitoring"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.tracking_data = {}
        self.lock = Lock()
        self.start_time = None
        self.current_step = None
        self.step_start_time = None
        
        # Workflow steps definition
        self.workflow_steps = {
            1: {'name': 'iCloud Download', 'description': 'Download files from iCloud'},
            2: {'name': 'Pixel Sync', 'description': 'Move files to Pixel sync folder'},
            3: {'name': 'Pixel Verification', 'description': 'Verify files synced to Pixel via Syncthing'},
            4: {'name': 'NAS Archive', 'description': 'Copy files to NAS archive'},
            5: {'name': 'Processing', 'description': 'Move files to processing folder'},
            6: {'name': 'Compression', 'description': 'Compress media files'},
            7: {'name': 'iCloud Delete', 'description': 'Move files to iCloud delete folder'},
            8: {'name': 'Cleanup', 'description': 'Clean up temporary files'}
        }
    
    def start_workflow(self, workflow_id: str = None):
        """Start tracking a new workflow"""
        if not workflow_id:
            workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with self.lock:
            self.start_time = datetime.now()
            self.tracking_data = {
                'workflow_id': workflow_id,
                'start_time': self.start_time.isoformat(),
                'status': 'running',
                'current_step': None,
                'steps': {},
                'files_processed': 0,
                'total_files': 0,
                'errors': [],
                'progress_percentage': 0
            }
        
        self.logger.info(f"🚀 Started workflow: {workflow_id}")
    
    def start_step(self, step_number: int, step_data: Dict = None):
        """Start tracking a workflow step"""
        with self.lock:
            self.current_step = step_number
            self.step_start_time = datetime.now()
            
            step_info = self.workflow_steps.get(step_number, {})
            self.tracking_data['current_step'] = step_number
            self.tracking_data['steps'][step_number] = {
                'name': step_info.get('name', f'Step {step_number}'),
                'description': step_info.get('description', ''),
                'start_time': self.step_start_time.isoformat(),
                'status': 'running',
                'files_processed': 0,
                'total_files': 0,
                'progress_percentage': 0,
                'data': step_data or {}
            }
        
        self.logger.info(f"📋 Step {step_number}: {step_info.get('name', 'Unknown')} - Started")
    
    def update_step_progress(self, step_number: int, files_processed: int, total_files: int = None, 
                           progress_data: Dict = None):
        """Update progress for current step"""
        with self.lock:
            if step_number in self.tracking_data['steps']:
                step = self.tracking_data['steps'][step_number]
                step['files_processed'] = files_processed
                
                if total_files:
                    step['total_files'] = total_files
                    step['progress_percentage'] = (files_processed / total_files) * 100
                
                if progress_data:
                    step['data'].update(progress_data)
                
                # Update overall progress
                self._update_overall_progress()
                
                # Log progress
                if total_files:
                    self.logger.info(f"📊 Step {step_number}: {files_processed}/{total_files} files processed ({step['progress_percentage']:.1f}%)")
                else:
                    self.logger.info(f"📊 Step {step_number}: {files_processed} files processed")
    
    def complete_step(self, step_number: int, success: bool = True, error_message: str = None, 
                     result_data: Dict = None):
        """Mark a step as completed"""
        with self.lock:
            if step_number in self.tracking_data['steps']:
                step = self.tracking_data['steps'][step_number]
                step['status'] = 'completed' if success else 'failed'
                step['end_time'] = datetime.now().isoformat()
                
                if self.step_start_time:
                    step['duration_seconds'] = (datetime.now() - self.step_start_time).total_seconds()
                
                if error_message:
                    step['error_message'] = error_message
                    self.tracking_data['errors'].append({
                        'step': step_number,
                        'error': error_message,
                        'timestamp': datetime.now().isoformat()
                    })
                
                if result_data:
                    step['result_data'] = result_data
                
                # Update overall progress
                self._update_overall_progress()
                
                if success:
                    self.logger.info(f"✅ Step {step_number}: {step['name']} - Completed")
                else:
                    self.logger.error(f"❌ Step {step_number}: {step['name']} - Failed: {error_message}")
    
    def add_file_tracking(self, file_path: str, step_number: int, status: str, 
                         metadata: Dict = None):
        """Track individual file processing"""
        with self.lock:
            if 'file_tracking' not in self.tracking_data:
                self.tracking_data['file_tracking'] = {}
            
            file_id = Path(file_path).name
            if file_id not in self.tracking_data['file_tracking']:
                self.tracking_data['file_tracking'][file_id] = {
                    'path': file_path,
                    'steps': {}
                }
            
            self.tracking_data['file_tracking'][file_id]['steps'][step_number] = {
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
    
    def complete_workflow(self, success: bool = True, summary: Dict = None):
        """Complete the workflow"""
        with self.lock:
            self.tracking_data['status'] = 'completed' if success else 'failed'
            self.tracking_data['end_time'] = datetime.now().isoformat()
            
            if self.start_time:
                self.tracking_data['total_duration_seconds'] = (datetime.now() - self.start_time).total_seconds()
            
            if summary:
                self.tracking_data['summary'] = summary
            
            # Final progress update
            self._update_overall_progress()
            
            if success:
                self.logger.info(f"🎉 Workflow completed successfully in {self.tracking_data.get('total_duration_seconds', 0):.1f} seconds")
            else:
                self.logger.error(f"💥 Workflow failed after {self.tracking_data.get('total_duration_seconds', 0):.1f} seconds")
    
    def _update_overall_progress(self):
        """Update overall workflow progress"""
        total_steps = len(self.workflow_steps)
        completed_steps = sum(1 for step in self.tracking_data['steps'].values() 
                            if step['status'] == 'completed')
        
        self.tracking_data['progress_percentage'] = (completed_steps / total_steps) * 100
        self.tracking_data['files_processed'] = sum(step.get('files_processed', 0) 
                                                  for step in self.tracking_data['steps'].values())
    
    def get_status(self) -> Dict:
        """Get current workflow status"""
        with self.lock:
            return self.tracking_data.copy()
    
    def get_step_status(self, step_number: int) -> Dict:
        """Get status of a specific step"""
        with self.lock:
            return self.tracking_data['steps'].get(step_number, {})
    
    def get_file_status(self, file_path: str) -> Dict:
        """Get tracking status of a specific file"""
        with self.lock:
            file_id = Path(file_path).name
            return self.tracking_data.get('file_tracking', {}).get(file_id, {})
    
    def print_status(self):
        """Print current status to console"""
        status = self.get_status()
        
        print("\n" + "="*60)
        print(f"WORKFLOW STATUS: {status.get('workflow_id', 'Unknown')}")
        print("="*60)
        print(f"Status: {status.get('status', 'Unknown')}")
        print(f"Progress: {status.get('progress_percentage', 0):.1f}%")
        print(f"Current Step: {status.get('current_step', 'None')}")
        print(f"Files Processed: {status.get('files_processed', 0)}")
        
        if status.get('start_time'):
            start_time = datetime.fromisoformat(status['start_time'])
            elapsed = datetime.now() - start_time
            print(f"Elapsed Time: {elapsed}")
        
        print("\nStep Details:")
        for step_num, step_info in status.get('steps', {}).items():
            status_icon = "✅" if step_info['status'] == 'completed' else "❌" if step_info['status'] == 'failed' else "🔄"
            print(f"  {status_icon} Step {step_num}: {step_info['name']} ({step_info['status']})")
            if step_info.get('files_processed', 0) > 0:
                print(f"    Files: {step_info['files_processed']}/{step_info.get('total_files', '?')}")
            if step_info.get('duration_seconds'):
                print(f"    Duration: {step_info['duration_seconds']:.1f}s")
        
        if status.get('errors'):
            print(f"\nErrors ({len(status['errors'])}):")
            for error in status['errors']:
                print(f"  ❌ Step {error['step']}: {error['error']}")
        
        print("="*60)
    
    def save_status(self, file_path: str = None):
        """Save current status to file"""
        if not file_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = f"workflow_status_{timestamp}.json"
        
        try:
            with open(file_path, 'w') as f:
                json.dump(self.get_status(), f, indent=2)
            self.logger.info(f"Status saved to {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to save status: {e}")
    
    def start_real_time_monitoring(self, interval: int = 10):
        """Start real-time monitoring in a separate thread"""
        def monitor():
            while self.tracking_data.get('status') == 'running':
                self.print_status()
                time.sleep(interval)
        
        monitor_thread = Thread(target=monitor, daemon=True)
        monitor_thread.start()
        return monitor_thread
