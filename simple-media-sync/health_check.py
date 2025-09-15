"""
Health check system for all components
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, List


class HealthChecker:
    """System health checker"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
    
    def check_all(self) -> Dict[str, bool]:
        """Check all system components"""
        checks = {
            'config': self.check_config(),
            'folders': self.check_folders(),
            'dependencies': self.check_dependencies(),
            'syncthing': self.check_syncthing(),
            'ffmpeg': self.check_ffmpeg(),
            'icloudpd': self.check_icloudpd(),
            'supabase': self.check_supabase()
        }
        
        return checks
    
    def check_config(self) -> bool:
        """Check configuration file"""
        try:
            config_file = Path('config.json')
            if not config_file.exists():
                self.logger.error("Config file not found")
                return False
            
            # Check required fields
            required_fields = [
                'supabase.url',
                'supabase.key',
                'icloud.username',
                'syncthing.api_key'
            ]
            
            for field in required_fields:
                if not self.config.get(field):
                    self.logger.error(f"Missing config field: {field}")
                    return False
            
            return True
        except Exception as e:
            self.logger.error(f"Config check failed: {e}")
            return False
    
    def check_folders(self) -> bool:
        """Check workflow folders"""
        try:
            folders = [
                self.config.get('workflow.incoming_folder', './incoming'),
                self.config.get('workflow.pixel_sync_folder', './pixel_sync'),
                self.config.get('workflow.nas_archive_folder', './nas_archive'),
                self.config.get('workflow.processing_folder', './processing'),
                self.config.get('workflow.icloud_delete_folder', './icloud_delete')
            ]
            
            for folder in folders:
                folder_path = Path(folder)
                if not folder_path.exists():
                    folder_path.mkdir(parents=True, exist_ok=True)
                    self.logger.info(f"Created folder: {folder}")
                
                # Check write permissions
                test_file = folder_path / '.test_write'
                try:
                    test_file.write_text('test')
                    test_file.unlink()
                except Exception:
                    self.logger.error(f"No write permission for folder: {folder}")
                    return False
            
            return True
        except Exception as e:
            self.logger.error(f"Folder check failed: {e}")
            return False
    
    def check_dependencies(self) -> bool:
        """Check Python dependencies"""
        try:
            import supabase
            import requests
            from PIL import Image
            import ffmpeg
            return True
        except ImportError as e:
            self.logger.error(f"Missing dependency: {e}")
            return False
    
    def check_syncthing(self) -> bool:
        """Check Syncthing connection"""
        try:
            from syncthing_client import SyncthingClient
            client = SyncthingClient(self.config, self.logger)
            return client.test_connection()
        except Exception as e:
            self.logger.error(f"Syncthing check failed: {e}")
            return False
    
    def check_ffmpeg(self) -> bool:
        """Check FFmpeg installation"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except Exception:
            self.logger.error("FFmpeg not found or not working")
            return False
    
    def check_icloudpd(self) -> bool:
        """Check icloudpd installation"""
        try:
            result = subprocess.run(['icloudpd', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except Exception:
            self.logger.error("icloudpd not found or not working")
            return False
    
    def check_supabase(self) -> bool:
        """Check Supabase connection"""
        try:
            from supabase_client import SupabaseClient
            client = SupabaseClient(self.config)
            return client.test_connection()
        except Exception as e:
            self.logger.error(f"Supabase check failed: {e}")
            return False
    
    def print_health_report(self):
        """Print health check report"""
        checks = self.check_all()
        
        print("\n" + "="*50)
        print("SYSTEM HEALTH CHECK")
        print("="*50)
        
        for component, status in checks.items():
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {component.upper()}: {'OK' if status else 'FAILED'}")
        
        all_healthy = all(checks.values())
        print("="*50)
        print(f"Overall Status: {'HEALTHY' if all_healthy else 'ISSUES DETECTED'}")
        print("="*50)
        
        return all_healthy
