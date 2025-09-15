"""
Syncthing REST API client for sync verification
"""

import requests
import time
from typing import Dict, List, Optional
from pathlib import Path


class SyncthingClient:
    """Client for Syncthing REST API"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.api_url = config.get('syncthing.api_url', 'http://localhost:8384')
        self.api_key = config.get('syncthing.api_key', '')
        self.pixel_folder_id = config.get('syncthing.pixel_folder_id', '')
        self.headers = {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def test_connection(self) -> bool:
        """Test connection to Syncthing API"""
        try:
            response = requests.get(f"{self.api_url}/rest/system/ping", headers=self.headers, timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Syncthing connection test failed: {e}")
            return False
    
    def get_system_status(self) -> Dict:
        """Get Syncthing system status"""
        try:
            response = requests.get(f"{self.api_url}/rest/system/status", headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get system status: {response.status_code}")
                return {}
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {}
    
    def get_folder_status(self, folder_id: str = None) -> Dict:
        """Get folder sync status"""
        if not folder_id:
            folder_id = self.pixel_folder_id
        
        try:
            response = requests.get(f"{self.api_url}/rest/db/status", 
                                  params={'folder': folder_id}, 
                                  headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get folder status: {response.status_code}")
                return {}
        except Exception as e:
            self.logger.error(f"Error getting folder status: {e}")
            return {}
    
    def get_file_status(self, file_path: str, folder_id: str = None) -> Dict:
        """Get specific file sync status"""
        if not folder_id:
            folder_id = self.pixel_folder_id
        
        try:
            # Get file information from database
            response = requests.get(f"{self.api_url}/rest/db/file", 
                                  params={'folder': folder_id, 'file': file_path}, 
                                  headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get file status for {file_path}: {response.status_code}")
                return {}
        except Exception as e:
            self.logger.error(f"Error getting file status for {file_path}: {e}")
            return {}
    
    def is_file_synced(self, file_path: str, folder_id: str = None) -> bool:
        """Check if a specific file is synced to all devices"""
        if not folder_id:
            folder_id = self.pixel_folder_id
        
        try:
            file_status = self.get_file_status(file_path, folder_id)
            if not file_status:
                return False
            
            # Check if file is synced to all devices
            # A file is considered synced if it has no pending operations
            return file_status.get('state') == 'synced'
        except Exception as e:
            self.logger.error(f"Error checking sync status for {file_path}: {e}")
            return False
    
    def wait_for_file_sync(self, file_path: str, timeout: int = 300, folder_id: str = None) -> bool:
        """Wait for a file to be synced with timeout"""
        if not folder_id:
            folder_id = self.pixel_folder_id
        
        self.logger.info(f"Waiting for {file_path} to sync (timeout: {timeout}s)")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.is_file_synced(file_path, folder_id):
                self.logger.info(f"✅ {file_path} synced successfully")
                return True
            
            # Check folder status for overall progress
            folder_status = self.get_folder_status(folder_id)
            if folder_status:
                self.logger.debug(f"Folder sync progress: {folder_status}")
            
            time.sleep(5)  # Check every 5 seconds
        
        self.logger.error(f"❌ Timeout waiting for {file_path} to sync")
        return False
    
    def wait_for_files_sync(self, file_paths: List[str], timeout: int = 300, folder_id: str = None) -> Dict[str, bool]:
        """Wait for multiple files to be synced"""
        if not folder_id:
            folder_id = self.pixel_folder_id
        
        results = {}
        self.logger.info(f"Waiting for {len(file_paths)} files to sync (timeout: {timeout}s)")
        
        for file_path in file_paths:
            results[file_path] = self.wait_for_file_sync(file_path, timeout, folder_id)
        
        synced_count = sum(1 for synced in results.values() if synced)
        self.logger.info(f"Sync complete: {synced_count}/{len(file_paths)} files synced")
        
        return results
    
    def get_folder_completion(self, folder_id: str = None) -> Dict:
        """Get folder completion percentage"""
        if not folder_id:
            folder_id = self.pixel_folder_id
        
        try:
            response = requests.get(f"{self.api_url}/rest/db/completion", 
                                  params={'folder': folder_id}, 
                                  headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get folder completion: {response.status_code}")
                return {}
        except Exception as e:
            self.logger.error(f"Error getting folder completion: {e}")
            return {}
    
    def scan_folder(self, folder_id: str = None) -> bool:
        """Trigger a folder scan"""
        if not folder_id:
            folder_id = self.pixel_folder_id
        
        try:
            response = requests.post(f"{self.api_url}/rest/db/scan", 
                                   params={'folder': folder_id}, 
                                   headers=self.headers, timeout=10)
            if response.status_code == 200:
                self.logger.info(f"✅ Folder scan triggered for {folder_id}")
                return True
            else:
                self.logger.error(f"Failed to trigger folder scan: {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"Error triggering folder scan: {e}")
            return False
    
    def get_device_connections(self) -> Dict:
        """Get device connection status"""
        try:
            response = requests.get(f"{self.api_url}/rest/system/connections", 
                                  headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get device connections: {response.status_code}")
                return {}
        except Exception as e:
            self.logger.error(f"Error getting device connections: {e}")
            return {}
    
    def is_pixel_connected(self) -> bool:
        """Check if Pixel device is connected"""
        connections = self.get_device_connections()
        if not connections:
            return False
        
        # Check if any device is connected (you might need to adjust this based on your device ID)
        for device_id, status in connections.get('connections', {}).items():
            if status.get('connected'):
                self.logger.info(f"✅ Device {device_id} is connected")
                return True
        
        self.logger.warning("❌ No devices connected")
        return False
