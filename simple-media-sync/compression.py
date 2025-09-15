"""
Media compression utilities
"""

import os
import subprocess
from pathlib import Path
from PIL import Image
import ffmpeg
from datetime import datetime, timedelta


class MediaCompressor:
    """Handle media compression for images and videos with configurable strategies"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self._load_compression_settings()
    
    def _load_compression_settings(self):
        """Load compression settings from config"""
        self.enabled = self.config.get('compression.enabled', True)
        self.strategy = self.config.get('compression.strategy', 'balanced')
        self.compress_images = self.config.get('compression.compress_images', True)
        self.compress_videos = self.config.get('compression.compress_videos', True)
        self.year_criteria = self.config.get('compression.year_criteria', {})
        self.custom_settings = self.config.get('compression.custom_settings', {})
        
        # Set quality based on strategy
        if self.strategy == 'aggressive':
            self.image_quality = 60
            self.video_quality = 35
        elif self.strategy == 'balanced':
            self.image_quality = self.config.get('compression.image_quality', 85)
            self.video_quality = self.config.get('compression.video_quality', 28)
        elif self.strategy == 'conservative':
            self.image_quality = 95
            self.video_quality = 20
        else:  # custom
            self.image_quality = self.config.get('compression.image_quality', 85)
            self.video_quality = self.config.get('compression.video_quality', 28)
    
    def should_compress_file(self, file_path: str) -> bool:
        """Determine if a file should be compressed based on configuration"""
        if not self.enabled:
            return False
        
        file_path = Path(file_path)
        file_ext = file_path.suffix.lower().lstrip('.')
        
        # Check file type
        if file_ext in self.custom_settings.get('image_formats', ['jpg', 'jpeg', 'png', 'bmp', 'tiff']):
            if not self.compress_images:
                return False
        elif file_ext in self.custom_settings.get('video_formats', ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv']):
            if not self.compress_videos:
                return False
        else:
            return False
        
        # Check file size
        max_size_mb = self.custom_settings.get('max_file_size_mb', 100)
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb < max_size_mb:
            self.logger.debug(f"Skipping compression for {file_path.name}: file too small ({file_size_mb:.1f}MB < {max_size_mb}MB)")
            return False
        
        # Check year criteria
        if self.year_criteria.get('enabled', False):
            file_age = self._get_file_age_years(file_path)
            compress_older_than = self.year_criteria.get('compress_older_than_years', 2)
            
            if file_age < compress_older_than:
                self.logger.debug(f"Skipping compression for {file_path.name}: file too recent ({file_age:.1f} years < {compress_older_than} years)")
                return False
        
        return True
    
    def _get_file_age_years(self, file_path: Path) -> float:
        """Get file age in years"""
        try:
            # Try to get creation time, fallback to modification time
            if hasattr(file_path.stat(), 'st_birthtime'):
                file_time = file_path.stat().st_birthtime
            else:
                file_time = file_path.stat().st_mtime
            
            file_date = datetime.fromtimestamp(file_time)
            current_date = datetime.now()
            age_delta = current_date - file_date
            return age_delta.days / 365.25
        except Exception:
            return 0
    
    def _get_compression_quality(self, file_path: Path) -> tuple:
        """Get compression quality based on file age and strategy"""
        image_quality = self.image_quality
        video_quality = self.video_quality
        
        # Apply aggressive compression for old files if configured
        if self.year_criteria.get('enabled', False):
            file_age = self._get_file_age_years(file_path)
            aggressive_after_years = self.year_criteria.get('aggressive_compression_after_years', 5)
            
            if file_age >= aggressive_after_years:
                # Use more aggressive settings for old files
                image_quality = max(40, image_quality - 20)
                video_quality = min(40, video_quality + 10)
                self.logger.info(f"Using aggressive compression for old file: {file_path.name} ({file_age:.1f} years)")
        
        return image_quality, video_quality
    
    def compress_file(self, input_path: str, output_path: str = None) -> str:
        """Compress a media file and return the output path"""
        input_path = Path(input_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # Check if file should be compressed
        if not self.should_compress_file(str(input_path)):
            self.logger.debug(f"Skipping compression for {input_path.name}")
            return str(input_path)
        
        # Determine output path
        if output_path is None:
            output_path = input_path.parent / f"compressed_{input_path.name}"
        else:
            output_path = Path(output_path)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Get file extension
        ext = input_path.suffix.lower()
        
        try:
            if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']:
                return self._compress_image(input_path, output_path)
            elif ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv']:
                return self._compress_video(input_path, output_path)
            else:
                self.logger.warning(f"Unsupported file type for compression: {ext}")
                return str(input_path)
        except Exception as e:
            self.logger.error(f"Compression failed for {input_path}: {e}")
            return str(input_path)
    
    def _compress_image(self, input_path: Path, output_path: Path) -> str:
        """Compress image file"""
        self.logger.info(f"Compressing image: {input_path.name}")
        
        # Get quality based on file age and strategy
        image_quality, _ = self._get_compression_quality(input_path)
        
        with Image.open(input_path) as img:
            # Convert to RGB if necessary (for JPEG)
            if output_path.suffix.lower() in ['.jpg', '.jpeg'] and img.mode in ['RGBA', 'P']:
                img = img.convert('RGB')
            
            # Save with compression
            img.save(output_path, quality=image_quality, optimize=True)
        
        # Check if compression was beneficial
        original_size = input_path.stat().st_size
        compressed_size = output_path.stat().st_size
        
        min_compression_ratio = self.custom_settings.get('min_compression_ratio', 0.1)
        compression_ratio = (1 - compressed_size / original_size)
        
        if compressed_size < original_size and compression_ratio >= min_compression_ratio:
            self.logger.info(f"Image compressed: {compression_ratio*100:.1f}% size reduction (quality: {image_quality})")
            return str(output_path)
        else:
            self.logger.info(f"Compression didn't meet criteria ({compression_ratio*100:.1f}% < {min_compression_ratio*100:.1f}%), keeping original")
            output_path.unlink()  # Remove compressed file
            return str(input_path)
    
    def _compress_video(self, input_path: Path, output_path: Path) -> str:
        """Compress video file using ffmpeg"""
        self.logger.info(f"Compressing video: {input_path.name}")
        
        # Get quality based on file age and strategy
        _, video_quality = self._get_compression_quality(input_path)
        
        try:
            # Use ffmpeg to compress video
            (
                ffmpeg
                .input(str(input_path))
                .output(
                    str(output_path),
                    vcodec='libx264',
                    crf=video_quality,
                    preset='medium',
                    acodec='aac',
                    audio_bitrate='128k'
                )
                .overwrite_output()
                .run(quiet=True)
            )
            
            # Check if compression was beneficial
            original_size = input_path.stat().st_size
            compressed_size = output_path.stat().st_size
            
            min_compression_ratio = self.custom_settings.get('min_compression_ratio', 0.1)
            compression_ratio = (1 - compressed_size / original_size)
            
            if compressed_size < original_size and compression_ratio >= min_compression_ratio:
                self.logger.info(f"Video compressed: {compression_ratio*100:.1f}% size reduction (CRF: {video_quality})")
                return str(output_path)
            else:
                self.logger.info(f"Compression didn't meet criteria ({compression_ratio*100:.1f}% < {min_compression_ratio*100:.1f}%), keeping original")
                output_path.unlink()  # Remove compressed file
                return str(input_path)
                
        except ffmpeg.Error as e:
            self.logger.error(f"FFmpeg error: {e}")
            return str(input_path)
    
    def get_compression_stats(self, original_path: str, compressed_path: str) -> dict:
        """Get compression statistics"""
        original_size = Path(original_path).stat().st_size
        compressed_size = Path(compressed_path).stat().st_size
        
        return {
            'original_size': original_size,
            'compressed_size': compressed_size,
            'size_reduction': original_size - compressed_size,
            'compression_ratio': (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
        }
