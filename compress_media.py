#!/usr/bin/env python3
"""
Enhanced Media Compression Module
Applies tiered compression to media files based on age
"""

import os
import subprocess
import time
from datetime import datetime
from dateutil import parser
from typing import List, Dict, Any, Optional
from PIL import Image
from common import config_manager, db_manager, setup_module_logger

# Setup module-specific logger
logger = setup_module_logger(__name__)

class CompressionManager:
    """Manages media compression operations"""
    
    def __init__(self):
        self.config = config_manager.get_compression_config()
        self.db = db_manager
        self.max_retries = 3
        self.retry_delay = 5  # seconds
    
    def compress_image(self, file_path: str, quality: int) -> Optional[int]:
        """Compress an image file"""
        try:
            # Create backup
            backup_path = file_path + ".backup"
            if not os.path.exists(backup_path):
                import shutil
                shutil.copy2(file_path, backup_path)
            
            img = Image.open(file_path)
            original_size = os.path.getsize(file_path)
            
            # Compress the image
            img.save(file_path, optimize=True, quality=quality)
            new_size = os.path.getsize(file_path)
            
            compression_ratio = (1 - new_size / original_size) * 100
            logger.info(f"Compressed image {os.path.basename(file_path)}: {original_size} → {new_size} bytes ({compression_ratio:.1f}% reduction, quality={quality})")
            
            # Remove backup if compression was successful
            if os.path.exists(backup_path):
                os.remove(backup_path)
            
            return new_size
            
        except Exception as e:
            logger.error(f"Image compression failed for {file_path}: {e}")
            # Restore backup if it exists
            backup_path = file_path + ".backup"
            if os.path.exists(backup_path):
                import shutil
                shutil.move(backup_path, file_path)
                logger.info(f"Restored backup for {file_path}")
            return None
    
    def compress_video(self, file_path: str, crf: int) -> Optional[int]:
        """Compress a video file using ffmpeg"""
        tmp_path = file_path + ".tmp.mp4"
        backup_path = file_path + ".backup"
        
        try:
            # Create backup
            if not os.path.exists(backup_path):
                import shutil
                shutil.copy2(file_path, backup_path)
            
            original_size = os.path.getsize(file_path)
            
            # Compress video
            cmd = [
                "ffmpeg", "-y", "-i", file_path,
                "-vcodec", "libx264", "-crf", str(crf),
                "-preset", "slow", "-movflags", "+faststart",
                tmp_path
            ]
            
            result = subprocess.run(
                cmd, 
                check=True, 
                capture_output=True, 
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            # Replace original with compressed version
            os.replace(tmp_path, file_path)
            new_size = os.path.getsize(file_path)
            
            compression_ratio = (1 - new_size / original_size) * 100
            logger.info(f"Compressed video {os.path.basename(file_path)}: {original_size} → {new_size} bytes ({compression_ratio:.1f}% reduction, crf={crf})")
            
            # Remove backup if compression was successful
            if os.path.exists(backup_path):
                os.remove(backup_path)
            
            return new_size
            
        except subprocess.TimeoutExpired:
            logger.error(f"Video compression timed out for {file_path}")
            self._cleanup_temp_files(tmp_path, backup_path, file_path)
            return None
        except subprocess.CalledProcessError as e:
            logger.error(f"Video compression failed for {file_path}: {e}")
            logger.error(f"ffmpeg stderr: {e.stderr}")
            self._cleanup_temp_files(tmp_path, backup_path, file_path)
            return None
        except FileNotFoundError:
            logger.error("ffmpeg not found. Please install ffmpeg")
            self._cleanup_temp_files(tmp_path, backup_path, file_path)
            return None
        except Exception as e:
            logger.error(f"Unexpected error compressing video {file_path}: {e}")
            self._cleanup_temp_files(tmp_path, backup_path, file_path)
            return None
    
    def _cleanup_temp_files(self, tmp_path: str, backup_path: str, original_path: str):
        """Clean up temporary files and restore backup if needed"""
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            
            if os.path.exists(backup_path):
                import shutil
                shutil.move(backup_path, original_path)
                logger.info(f"Restored backup for {original_path}")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def compress_file(self, file_path: str, age_years: float) -> Optional[int]:
        """Compress a file based on its age"""
        if not self.config.enabled:
            logger.info("Compression is disabled in configuration")
            return None
        
        ext = file_path.lower().split('.')[-1]
        
        # Determine compression settings based on age
        if age_years < 1:
            img_quality = self.config.light_quality
            vid_crf = self.config.light_crf
        elif 1 <= age_years <= 3:
            img_quality = self.config.medium_quality
            vid_crf = self.config.medium_crf
        else:
            img_quality = self.config.heavy_quality
            vid_crf = self.config.heavy_crf
        
        # Compress based on file type
        if ext in ["jpg", "jpeg", "png", "webp"]:
            return self.compress_image(file_path, img_quality)
        elif ext in ["mp4", "mov", "avi", "mkv"]:
            return self.compress_video(file_path, vid_crf)
        else:
            logger.warning(f"Unsupported file type for compression: {file_path}")
            return None
    
    def get_files_ready_for_compression(self) -> List[Dict[str, Any]]:
        """Get files ready for compression"""
        return self.db.get_media_ready_for_compression()
    
    def compress_batch(self) -> Dict[str, int]:
        """Compress a batch of files"""
        results = {
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'unsupported': 0
        }
        
        files = self.get_files_ready_for_compression()
        results['total_files'] = len(files)
        
        if not files:
            logger.info("No files ready for compression")
            return results
        
        logger.info(f"Found {len(files)} files ready for compression")
        
        for file_info in files:
            filename = file_info['filename']
            local_path = file_info['local_path']
            icloud_id = file_info['icloud_id']
            created_date = file_info['created_date']
            
            try:
                if not os.path.exists(local_path):
                    logger.warning(f"File not found: {local_path}")
                    results['skipped'] += 1
                    continue
                
                # Set initial size if not already set
                self.db.set_initial_size(icloud_id, local_path)
                
                # Calculate file age
                try:
                    age_years = (datetime.utcnow() - parser.parse(created_date)).days / 365
                except:
                    age_years = 0  # Default to light compression if date parsing fails
                
                # Compress the file
                new_size = self.compress_file(local_path, age_years)
                
                if new_size:
                    # Update database with compression info
                    if self.db.mark_compressed(icloud_id, new_size):
                        results['successful'] += 1
                        logger.info(f"✅ Successfully compressed: {filename}")
                    else:
                        logger.error(f"Failed to update database for: {filename}")
                        results['failed'] += 1
                else:
                    results['failed'] += 1
                    # Increment error count
                    self.db.increment_error_count(icloud_id, "Compression failed")
                    
            except Exception as e:
                logger.error(f"Error compressing {filename}: {e}")
                results['failed'] += 1
                self.db.increment_error_count(icloud_id, f"Compression error: {str(e)}")
        
        return results
    
    def get_compression_stats(self) -> Dict[str, Any]:
        """Get compression statistics"""
        try:
            stats = self.db.get_pipeline_stats()
            compression_stats = {
                'total_files': stats.get('total', 0),
                'compressed_files': stats.get('compressed', 0),
                'pending_compression': stats.get('total', 0) - stats.get('compressed', 0),
                'compression_enabled': self.config.enabled,
                'light_quality': self.config.light_quality,
                'medium_quality': self.config.medium_quality,
                'heavy_quality': self.config.heavy_quality
            }
            return compression_stats
        except Exception as e:
            logger.error(f"Error getting compression stats: {e}")
            return {}

def main():
    """Main compression pipeline"""
    logger.info("Starting media compression pipeline...")
    
    # Validate configuration
    if not config_manager.validate_config():
        logger.error("Configuration validation failed")
        return False
    
    # Initialize database
    db_manager.init_database()
    
    # Create compression manager
    compression_manager = CompressionManager()
    
    # Perform batch compression
    results = compression_manager.compress_batch()
    
    # Log results
    logger.info(f"Compression completed:")
    logger.info(f"  Total files: {results['total_files']}")
    logger.info(f"  Successful: {results['successful']}")
    logger.info(f"  Failed: {results['failed']}")
    logger.info(f"  Skipped: {results['skipped']}")
    logger.info(f"  Unsupported: {results['unsupported']}")
    
    # Get and log statistics
    stats = compression_manager.get_compression_stats()
    logger.info(f"Compression statistics: {stats}")
    
    success = results['failed'] == 0
    if success:
        logger.info("✅ Media compression pipeline completed successfully")
    else:
        logger.warning(f"⚠️ Media compression completed with {results['failed']} failures")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
