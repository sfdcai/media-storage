"""
File management utilities with workflow prefixes and tracking
"""

import os
import shutil
import time
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class FileManager:
    """Manages file operations with workflow tracking and prefixes"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.workflow_config = config.get('workflow', {})
        
        # Define workflow folders
        self.incoming_folder = Path(self.workflow_config.get('incoming_folder', './incoming'))
        self.pixel_sync_folder = Path(self.workflow_config.get('pixel_sync_folder', './pixel_sync'))
        self.nas_archive_folder = Path(self.workflow_config.get('nas_archive_folder', './nas_archive'))
        self.processing_folder = Path(self.workflow_config.get('processing_folder', './processing'))
        self.icloud_delete_folder = Path(self.workflow_config.get('icloud_delete_folder', './icloud_delete'))
        
        # Create all folders
        self._ensure_folders_exist()
    
    def _ensure_folders_exist(self):
        """Ensure all workflow folders exist"""
        folders = [
            self.incoming_folder,
            self.pixel_sync_folder,
            self.nas_archive_folder,
            self.processing_folder,
            self.icloud_delete_folder
        ]
        
        for folder in folders:
            try:
                folder.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"Ensured folder exists: {folder}")
            except PermissionError:
                self.logger.warning(f"Permission denied creating folder: {folder}")
                self.logger.info(f"Please run: sudo mkdir -p {folder} && sudo chown -R syncthing:syncthing {folder}")
            except Exception as e:
                self.logger.error(f"Error creating folder {folder}: {e}")
    
    def add_workflow_prefix(self, file_path: Path, stage: str, step_number: int) -> Path:
        """Add workflow prefix to filename"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = f"step{step_number:02d}_{stage}_{timestamp}"
        
        # Create new filename with prefix
        new_name = f"{prefix}_{file_path.name}"
        return file_path.parent / new_name
    
    def get_files_in_folder(self, folder: Path, extensions: List[str] = None) -> List[Path]:
        """Get all files in a folder, optionally filtered by extensions"""
        if not folder.exists():
            return []
        
        files = []
        for file_path in folder.rglob('*'):
            if file_path.is_file():
                if extensions is None or file_path.suffix.lower() in extensions:
                    files.append(file_path)
        
        return sorted(files, key=lambda x: x.stat().st_mtime)
    
    def move_file_with_prefix(self, source: Path, destination_folder: Path, 
                            stage: str, step_number: int) -> Optional[Path]:
        """Move file to destination folder with workflow prefix"""
        try:
            # Ensure destination folder exists
            destination_folder.mkdir(parents=True, exist_ok=True)
            
            # Add workflow prefix
            new_name = self.add_workflow_prefix(source, stage, step_number)
            destination = destination_folder / new_name.name
            
            # Move file
            shutil.move(str(source), str(destination))
            
            self.logger.info(f"✅ Moved {source.name} to {stage} folder as {destination.name}")
            return destination
            
        except Exception as e:
            self.logger.error(f"❌ Failed to move {source.name} to {stage}: {e}")
            return None
    
    def copy_file_with_prefix(self, source: Path, destination_folder: Path, 
                            stage: str, step_number: int) -> Optional[Path]:
        """Copy file to destination folder with workflow prefix"""
        try:
            # Ensure destination folder exists
            destination_folder.mkdir(parents=True, exist_ok=True)
            
            # Add workflow prefix
            new_name = self.add_workflow_prefix(source, stage, step_number)
            destination = destination_folder / new_name.name
            
            # Copy file
            shutil.copy2(str(source), str(destination))
            
            self.logger.info(f"✅ Copied {source.name} to {stage} folder as {destination.name}")
            return destination
            
        except Exception as e:
            self.logger.error(f"❌ Failed to copy {source.name} to {stage}: {e}")
            return None
    
    def select_files_for_pixel_sync(self, count: int = 5) -> List[Path]:
        """Select files from incoming folder for Pixel sync"""
        media_extensions = ['.jpg', '.jpeg', '.png', '.mp4', '.mov', '.avi']
        incoming_files = self.get_files_in_folder(self.incoming_folder, media_extensions)
        
        # Select the oldest files (first in the list since they're sorted by mtime)
        selected_files = incoming_files[:count]
        
        self.logger.info(f"Selected {len(selected_files)} files for Pixel sync")
        return selected_files
    
    def move_files_to_pixel_sync(self, files: List[Path]) -> List[Path]:
        """Move files to pixel sync folder"""
        moved_files = []
        
        for file_path in files:
            moved_file = self.move_file_with_prefix(
                file_path, self.pixel_sync_folder, 'pixel_sync', 2
            )
            if moved_file:
                moved_files.append(moved_file)
        
        return moved_files
    
    def copy_files_to_nas_archive(self, files: List[Path]) -> List[Path]:
        """Copy files to NAS archive folder"""
        copied_files = []
        
        for file_path in files:
            copied_file = self.copy_file_with_prefix(
                file_path, self.nas_archive_folder, 'nas_archive', 4
            )
            if copied_file:
                copied_files.append(copied_file)
        
        return copied_files
    
    def move_files_to_processing(self, files: List[Path]) -> List[Path]:
        """Move files to processing folder"""
        moved_files = []
        
        for file_path in files:
            moved_file = self.move_file_with_prefix(
                file_path, self.processing_folder, 'processing', 5
            )
            if moved_file:
                moved_files.append(moved_file)
        
        return moved_files
    
    def move_files_to_icloud_delete(self, files: List[Path]) -> List[Path]:
        """Move files to iCloud delete folder"""
        moved_files = []
        
        for file_path in files:
            moved_file = self.move_file_with_prefix(
                file_path, self.icloud_delete_folder, 'icloud_delete', 7
            )
            if moved_file:
                moved_files.append(moved_file)
        
        return moved_files
    
    def get_file_info(self, file_path: Path) -> Dict:
        """Get comprehensive file information"""
        try:
            stat = file_path.stat()
            return {
                'path': str(file_path),
                'name': file_path.name,
                'size': stat.st_size,
                'size_mb': stat.st_size / (1024 * 1024),
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'extension': file_path.suffix.lower(),
                'is_media': file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.mp4', '.mov', '.avi']
            }
        except Exception as e:
            self.logger.error(f"Error getting file info for {file_path}: {e}")
            return {}
    
    def cleanup_folder(self, folder: Path, keep_recent_hours: int = 24) -> int:
        """Clean up old files in a folder"""
        if not folder.exists():
            return 0
        
        cutoff_time = time.time() - (keep_recent_hours * 3600)
        cleaned_count = 0
        
        for file_path in folder.rglob('*'):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    cleaned_count += 1
                    self.logger.debug(f"Cleaned up old file: {file_path.name}")
                except Exception as e:
                    self.logger.error(f"Failed to clean up {file_path.name}: {e}")
        
        if cleaned_count > 0:
            self.logger.info(f"Cleaned up {cleaned_count} old files from {folder.name}")
        
        return cleaned_count
    
    def get_workflow_status(self) -> Dict:
        """Get status of all workflow folders"""
        status = {}
        
        folders = {
            'incoming': self.incoming_folder,
            'pixel_sync': self.pixel_sync_folder,
            'nas_archive': self.nas_archive_folder,
            'processing': self.processing_folder,
            'icloud_delete': self.icloud_delete_folder
        }
        
        for name, folder in folders.items():
            files = self.get_files_in_folder(folder)
            total_size = sum(f.stat().st_size for f in files)
            
            status[name] = {
                'file_count': len(files),
                'total_size_mb': total_size / (1024 * 1024),
                'folder_path': str(folder)
            }
        
        return status
    
    def verify_file_integrity(self, source: Path, destination: Path) -> bool:
        """Verify that a file was copied/moved correctly"""
        try:
            if not source.exists() or not destination.exists():
                return False
            
            # Compare file sizes
            source_size = source.stat().st_size
            destination_size = destination.stat().st_size
            
            if source_size != destination_size:
                self.logger.error(f"File size mismatch: {source.name} ({source_size} vs {destination_size})")
                return False
            
            # For critical files, you might want to add hash comparison here
            return True
            
        except Exception as e:
            self.logger.error(f"Error verifying file integrity: {e}")
            return False
