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
    
    def record_file(self, file_path: str, file_size: int, file_hash: str, 
                   workflow_stage: str = 'completed', compression_metadata: dict = None) -> bool:
        """Record file in database with workflow stage and compression metadata"""
        try:
            data = {
                'file_path': file_path,
                'file_size': file_size,
                'file_hash': file_hash,
                'last_modified': datetime.now().isoformat(),
                'sync_status': 'synced',
                'workflow_stage': workflow_stage
            }
            
            # Only add compression_metadata if it's provided and column exists
            if compression_metadata:
                data['compression_metadata'] = compression_metadata
            
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
    
    def update_workflow_stage(self, file_path: str, stage: str, metadata: dict = None) -> bool:
        """Update workflow stage for a file"""
        try:
            data = {
                'workflow_stage': stage,
                'last_modified': datetime.now().isoformat()
            }
            
            if metadata:
                data['compression_metadata'] = metadata
            
            self.client.table(self.table_name).update(data).eq('file_path', file_path).execute()
            return True
        except Exception as e:
            print(f"Error updating workflow stage for {file_path}: {e}")
            return False
    
    def record_compression(self, file_path: str, original_size: int, compressed_size: int, 
                          compression_ratio: float, quality_settings: dict) -> bool:
        """Record compression metadata for a file"""
        try:
            compression_metadata = {
                'original_size': original_size,
                'compressed_size': compressed_size,
                'compression_ratio': compression_ratio,
                'quality_settings': quality_settings,
                'compressed_at': datetime.now().isoformat()
            }
            
            # Get existing metadata
            existing = self.client.table(self.table_name).select('compression_metadata').eq('file_path', file_path).execute()
            existing_metadata = existing.data[0].get('compression_metadata', {}) if existing.data else {}
            
            # Merge with existing metadata
            existing_metadata.update(compression_metadata)
            
            data = {
                'compression_metadata': existing_metadata,
                'last_modified': datetime.now().isoformat()
            }
            
            self.client.table(self.table_name).update(data).eq('file_path', file_path).execute()
            return True
        except Exception as e:
            print(f"Error recording compression for {file_path}: {e}")
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
    
    def get_workflow_status(self) -> Dict:
        """Get workflow status statistics"""
        try:
            # Get files by workflow stage
            stages_result = self.client.table(self.table_name).select('workflow_stage', count='exact').execute()
            
            # Get compression statistics
            compression_result = self.client.table(self.table_name).select('compression_metadata').execute()
            
            total_compressed = 0
            total_size_saved = 0
            
            for record in compression_result.data:
                if record.get('compression_metadata'):
                    metadata = record['compression_metadata']
                    if 'original_size' in metadata and 'compressed_size' in metadata:
                        total_compressed += 1
                        total_size_saved += metadata['original_size'] - metadata['compressed_size']
            
            return {
                'total_files': stages_result.count or 0,
                'compressed_files': total_compressed,
                'total_size_saved_mb': total_size_saved / (1024 * 1024) if total_size_saved > 0 else 0,
                'workflow_stages': self._get_stage_counts()
            }
        except Exception:
            return {
                'total_files': 0,
                'compressed_files': 0,
                'total_size_saved_mb': 0,
                'workflow_stages': {}
            }
    
    def _get_stage_counts(self) -> Dict:
        """Get count of files by workflow stage"""
        try:
            result = self.client.table(self.table_name).select('workflow_stage').execute()
            stage_counts = {}
            
            for record in result.data:
                stage = record.get('workflow_stage', 'unknown')
                stage_counts[stage] = stage_counts.get(stage, 0) + 1
            
            return stage_counts
        except Exception:
            return {}
    
    def is_file_synced(self, file_path: str, file_hash: str) -> bool:
        """Check if file is already synced with same hash"""
        try:
            result = self.client.table(self.table_name).select('file_hash').eq('file_path', file_path).execute()
            if result.data:
                return result.data[0]['file_hash'] == file_hash
            return False
        except Exception:
            return False
