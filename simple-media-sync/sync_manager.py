"""
Simple sync manager for media files
"""

import os
from pathlib import Path
from typing import List, Optional

from supabase_client import SupabaseClient


class SyncManager:
    """Simple sync manager"""
    
    def __init__(self, config, supabase: SupabaseClient, logger):
        self.config = config
        self.supabase = supabase
        self.logger = logger
        self.exclude_patterns = config.get('sync.exclude_patterns', [])
    
    def sync(self, source_dir: Optional[str] = None, dry_run: bool = False):
        """Sync media files"""
        if source_dir:
            source_dirs = [source_dir]
        else:
            source_dirs = self.config.get('sync.source_dirs', [])
        
        if not source_dirs:
            self.logger.error("No source directories configured")
            return
        
        self.logger.info(f"Starting sync (dry_run={dry_run})")
        
        total_files = 0
        synced_files = 0
        
        for source_dir in source_dirs:
            if not Path(source_dir).exists():
                self.logger.warning(f"Source directory does not exist: {source_dir}")
                continue
            
            self.logger.info(f"Scanning directory: {source_dir}")
            files = self._scan_directory(source_dir)
            total_files += len(files)
            
            for file_path in files:
                if self._should_sync_file(file_path):
                    if dry_run:
                        self.logger.info(f"[DRY RUN] Would sync: {file_path}")
                    else:
                        if self._sync_file(file_path):
                            synced_files += 1
                        else:
                            self.logger.error(f"Failed to sync: {file_path}")
                else:
                    self.logger.debug(f"Skipping already synced file: {file_path}")
        
        self.logger.info(f"Sync complete. Total files: {total_files}, Synced: {synced_files}")
    
    def _scan_directory(self, directory: str) -> List[str]:
        """Scan directory for media files"""
        media_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
                          '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv',
                          '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'}
        
        files = []
        for root, dirs, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                file_ext = Path(filename).suffix.lower()
                
                # Check if it's a media file
                if file_ext in media_extensions:
                    # Check exclude patterns
                    if not self._should_exclude_file(filename):
                        files.append(file_path)
        
        return files
    
    def _should_exclude_file(self, filename: str) -> bool:
        """Check if file should be excluded"""
        for pattern in self.exclude_patterns:
            if pattern.startswith('*'):
                if filename.endswith(pattern[1:]):
                    return True
            elif pattern in filename:
                return True
        return False
    
    def _should_sync_file(self, file_path: str) -> bool:
        """Check if file should be synced"""
        try:
            file_hash = self.supabase.get_file_hash(file_path)
            return not self.supabase.is_file_synced(file_path, file_hash)
        except Exception:
            return True
    
    def _sync_file(self, file_path: str) -> bool:
        """Sync individual file"""
        try:
            file_size = os.path.getsize(file_path)
            file_hash = self.supabase.get_file_hash(file_path)
            
            if not file_hash:
                self.logger.error(f"Could not generate hash for: {file_path}")
                return False
            
            # Record in database
            if self.supabase.record_file(file_path, file_size, file_hash):
                self.logger.info(f"Synced: {file_path}")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error syncing {file_path}: {e}")
            return False
