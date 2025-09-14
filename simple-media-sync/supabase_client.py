"""
Simple Supabase client for media sync
"""

import hashlib
from datetime import datetime
from typing import Dict, List, Optional
from supabase import create_client, Client


class SupabaseClient:
    """Simple Supabase client wrapper"""
    
    def __init__(self, config):
        self.config = config
        self.client: Optional[Client] = None
        self.table_name = config.get('supabase.table_name', 'media_files')
        self._connect()
    
    def _connect(self):
        """Connect to Supabase"""
        url = self.config.get('supabase.url')
        key = self.config.get('supabase.key')
        
        if not url or not key:
            raise ValueError("Supabase URL and key must be configured")
        
        try:
            self.client = create_client(url, key)
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Supabase: {e}")
    
    def test_connection(self) -> bool:
        """Test Supabase connection"""
        try:
            # Try to query the table
            result = self.client.table(self.table_name).select('*').limit(1).execute()
            return True
        except Exception:
            return False
    
    def get_file_hash(self, file_path: str) -> str:
        """Get SHA256 hash of file"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return ""
    
    def record_file(self, file_path: str, file_size: int, file_hash: str) -> bool:
        """Record file in database"""
        try:
            data = {
                'file_path': file_path,
                'file_size': file_size,
                'file_hash': file_hash,
                'last_modified': datetime.now().isoformat(),
                'sync_status': 'synced'
            }
            
            # Check if file already exists
            existing = self.client.table(self.table_name).select('*').eq('file_path', file_path).execute()
            
            if existing.data:
                # Update existing record
                self.client.table(self.table_name).update(data).eq('file_path', file_path).execute()
            else:
                # Insert new record
                self.client.table(self.table_name).insert(data).execute()
            
            return True
        except Exception as e:
            print(f"Error recording file {file_path}: {e}")
            return False
    
    def get_synced_files(self) -> List[Dict]:
        """Get list of synced files"""
        try:
            result = self.client.table(self.table_name).select('*').execute()
            return result.data
        except Exception:
            return []
    
    def get_sync_status(self) -> Dict:
        """Get overall sync status"""
        try:
            # Get count of synced files
            result = self.client.table(self.table_name).select('last_modified', count='exact').execute()
            
            # Get latest sync time
            latest = self.client.table(self.table_name).select('last_modified').order('last_modified', desc=True).limit(1).execute()
            
            return {
                'files_count': result.count or 0,
                'last_sync': latest.data[0]['last_modified'] if latest.data else None
            }
        except Exception:
            return {'files_count': 0, 'last_sync': None}
    
    def is_file_synced(self, file_path: str, file_hash: str) -> bool:
        """Check if file is already synced with same hash"""
        try:
            result = self.client.table(self.table_name).select('file_hash').eq('file_path', file_path).execute()
            if result.data:
                return result.data[0]['file_hash'] == file_hash
            return False
        except Exception:
            return False
