"""
Backup and recovery system for workflow state
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class BackupManager:
    """Manages workflow state backups"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.backup_dir = Path('./backups')
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, workflow_id: str, state_data: Dict) -> str:
        """Create a backup of workflow state"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"workflow_{workflow_id}_{timestamp}.json"
        backup_path = self.backup_dir / backup_name
        
        try:
            with open(backup_path, 'w') as f:
                json.dump(state_data, f, indent=2)
            
            self.logger.info(f"Backup created: {backup_name}")
            return str(backup_path)
        except Exception as e:
            self.logger.error(f"Backup creation failed: {e}")
            return None
    
    def restore_backup(self, backup_path: str) -> Dict:
        """Restore workflow state from backup"""
        try:
            with open(backup_path, 'r') as f:
                state_data = json.load(f)
            
            self.logger.info(f"Backup restored: {backup_path}")
            return state_data
        except Exception as e:
            self.logger.error(f"Backup restoration failed: {e}")
            return None
    
    def list_backups(self) -> List[str]:
        """List available backups"""
        backups = []
        for backup_file in self.backup_dir.glob('workflow_*.json'):
            backups.append(str(backup_file))
        return sorted(backups, reverse=True)
    
    def cleanup_old_backups(self, keep_days: int = 7):
        """Clean up old backups"""
        cutoff_date = datetime.now().timestamp() - (keep_days * 24 * 3600)
        cleaned_count = 0
        
        for backup_file in self.backup_dir.glob('workflow_*.json'):
            if backup_file.stat().st_mtime < cutoff_date:
                backup_file.unlink()
                cleaned_count += 1
        
        if cleaned_count > 0:
            self.logger.info(f"Cleaned up {cleaned_count} old backups")
    
    def backup_workflow_folders(self, workflow_id: str) -> str:
        """Create a backup of workflow folders"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"folders_{workflow_id}_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        try:
            backup_path.mkdir(exist_ok=True)
            
            # Backup workflow folders
            folders = [
                'incoming',
                'pixel_sync',
                'nas_archive', 
                'processing',
                'icloud_delete'
            ]
            
            for folder in folders:
                source = Path(folder)
                if source.exists():
                    dest = backup_path / folder
                    shutil.copytree(source, dest)
            
            self.logger.info(f"Folder backup created: {backup_name}")
            return str(backup_path)
        except Exception as e:
            self.logger.error(f"Folder backup failed: {e}")
            return None
