#!/usr/bin/env python3
"""
Authentication Management
Handles authentication for various services (iCloud, Syncthing, etc.)
"""

import os
import logging
import requests
from typing import Optional, Dict, Any
from pyicloud import PyiCloudService
from pyicloud.exceptions import PyiCloudAPIResponseException, PyiCloudFailedLoginException
from common.config import config_manager
from common.logger import get_logger

logger = get_logger(__name__)

class AuthenticationManager:
    """Centralized authentication manager for all services"""
    
    def __init__(self):
        self.icloud_config = config_manager.get_icloud_config()
        self.syncthing_config = config_manager.get_syncthing_config()
        self._icloud_service: Optional[PyiCloudService] = None
        self._syncthing_session: Optional[requests.Session] = None
    
    def get_icloud_service(self) -> Optional[PyiCloudService]:
        """Get authenticated iCloud service"""
        if self._icloud_service is None:
            self._icloud_service = self._authenticate_icloud()
        return self._icloud_service
    
    def _authenticate_icloud(self) -> Optional[PyiCloudService]:
        """Authenticate with iCloud"""
        try:
            username = self.icloud_config.username
            password = self.icloud_config.password or os.getenv('ICLOUD_PASSWORD')
            
            if not username or not password:
                logger.error("iCloud credentials not configured")
                return None
            
            logger.info(f"Authenticating with iCloud for user: {username}")
            api = PyiCloudService(username, password)
            
            # Handle 2FA if required
            if api.requires_2fa:
                logger.warning("iCloud 2FA required. Please complete authentication on your device.")
                code = input("Enter 2FA code: ")
                result = api.validate_2fa_code(code)
                if not result:
                    logger.error("2FA validation failed")
                    return None
                logger.info("2FA validation successful")
            
            # Test the connection
            if hasattr(api, 'photos') and api.photos:
                logger.info("✅ iCloud authentication successful")
                return api
            else:
                logger.error("iCloud authentication failed - no photos access")
                return None
                
        except PyiCloudFailedLoginException as e:
            logger.error(f"iCloud login failed: {e}")
            return None
        except Exception as e:
            logger.error(f"iCloud authentication error: {e}")
            return None
    
    def get_syncthing_session(self) -> Optional[requests.Session]:
        """Get authenticated Syncthing session"""
        if self._syncthing_session is None:
            self._syncthing_session = self._authenticate_syncthing()
        return self._syncthing_session
    
    def _authenticate_syncthing(self) -> Optional[requests.Session]:
        """Authenticate with Syncthing API"""
        try:
            api_key = self.syncthing_config.api_key or os.getenv('SYNCTHING_API_KEY')
            base_url = self.syncthing_config.base_url
            
            if not api_key:
                logger.error("Syncthing API key not configured")
                return None
            
            session = requests.Session()
            session.headers.update({
                'X-API-Key': api_key,
                'Content-Type': 'application/json'
            })
            session.timeout = self.syncthing_config.timeout_seconds
            
            # Test the connection
            test_url = f"{base_url}/rest/system/status"
            response = session.get(test_url)
            
            if response.status_code == 200:
                logger.info("✅ Syncthing authentication successful")
                return session
            else:
                logger.error(f"Syncthing authentication failed: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Syncthing connection error: {e}")
            return None
        except Exception as e:
            logger.error(f"Syncthing authentication error: {e}")
            return None
    
    def test_icloud_connection(self) -> bool:
        """Test iCloud connection"""
        try:
            service = self.get_icloud_service()
            if service and hasattr(service, 'photos'):
                # Try to get albums to test connection
                albums = service.photos.albums
                logger.info(f"iCloud connection test successful - found {len(albums)} albums")
                return True
            return False
        except Exception as e:
            logger.error(f"iCloud connection test failed: {e}")
            return False
    
    def test_syncthing_connection(self) -> bool:
        """Test Syncthing connection"""
        try:
            session = self.get_syncthing_session()
            if session:
                base_url = self.syncthing_config.base_url
                response = session.get(f"{base_url}/rest/system/status")
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Syncthing connection test successful - version: {data.get('version', 'unknown')}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Syncthing connection test failed: {e}")
            return False
    
    def get_or_create_icloud_album(self, album_name: str):
        """Get or create an iCloud album"""
        try:
            service = self.get_icloud_service()
            if not service:
                return None
            
            albums = service.photos.albums
            for album in albums.values():
                if album.title == album_name:
                    logger.info(f"Found existing iCloud album: {album_name}")
                    return album
            
            # Create new album
            logger.info(f"Creating new iCloud album: {album_name}")
            return service.photos.create_album(album_name)
            
        except PyiCloudAPIResponseException as e:
            logger.error(f"iCloud album operation failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Error with iCloud album {album_name}: {e}")
            return None
    
    def get_syncthing_folder_status(self, folder_id: str) -> Optional[Dict[str, Any]]:
        """Get Syncthing folder status"""
        try:
            session = self.get_syncthing_session()
            if not session:
                return None
            
            base_url = self.syncthing_config.base_url
            url = f"{base_url}/rest/db/file?folder={folder_id}&recursive=true"
            
            response = session.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Syncthing folder status request failed: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Syncthing folder status error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting Syncthing folder status: {e}")
            return None
    
    def get_syncthing_fully_synced_files(self, folder_id: str) -> list:
        """Get list of fully synced files from Syncthing"""
        try:
            files_data = self.get_syncthing_folder_status(folder_id)
            if not files_data:
                return []
            
            synced_files = []
            for file_info in files_data:
                if file_info.get("globalVersion") == file_info.get("localVersion"):
                    synced_files.append(file_info["name"])
            
            logger.info(f"Found {len(synced_files)} fully synced files in Syncthing")
            return synced_files
            
        except Exception as e:
            logger.error(f"Error getting fully synced files: {e}")
            return []
    
    def reset_icloud_authentication(self):
        """Reset iCloud authentication (useful for re-authentication)"""
        self._icloud_service = None
        logger.info("iCloud authentication reset")
    
    def reset_syncthing_authentication(self):
        """Reset Syncthing authentication"""
        if self._syncthing_session:
            self._syncthing_session.close()
        self._syncthing_session = None
        logger.info("Syncthing authentication reset")
    
    def validate_all_connections(self) -> Dict[str, bool]:
        """Validate all service connections"""
        results = {
            'icloud': self.test_icloud_connection(),
            'syncthing': self.test_syncthing_connection()
        }
        
        logger.info(f"Connection validation results: {results}")
        return results

# Global authentication manager instance
auth_manager = AuthenticationManager()
