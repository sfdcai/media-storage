"""
Media compression utilities
"""

import os
import subprocess
from pathlib import Path
from PIL import Image
import ffmpeg


class MediaCompressor:
    """Handle media compression for images and videos"""
    
    def __init__(self, logger):
        self.logger = logger
        self.image_quality = 85
        self.video_quality = 28  # CRF value for ffmpeg
    
    def compress_file(self, input_path: str, output_path: str = None) -> str:
        """Compress a media file and return the output path"""
        input_path = Path(input_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
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
        
        with Image.open(input_path) as img:
            # Convert to RGB if necessary (for JPEG)
            if output_path.suffix.lower() in ['.jpg', '.jpeg'] and img.mode in ['RGBA', 'P']:
                img = img.convert('RGB')
            
            # Save with compression
            img.save(output_path, quality=self.image_quality, optimize=True)
        
        # Check if compression was beneficial
        original_size = input_path.stat().st_size
        compressed_size = output_path.stat().st_size
        
        if compressed_size < original_size:
            compression_ratio = (1 - compressed_size / original_size) * 100
            self.logger.info(f"Image compressed: {compression_ratio:.1f}% size reduction")
            return str(output_path)
        else:
            self.logger.info("Compression didn't reduce size, keeping original")
            output_path.unlink()  # Remove compressed file
            return str(input_path)
    
    def _compress_video(self, input_path: Path, output_path: Path) -> str:
        """Compress video file using ffmpeg"""
        self.logger.info(f"Compressing video: {input_path.name}")
        
        try:
            # Use ffmpeg to compress video
            (
                ffmpeg
                .input(str(input_path))
                .output(
                    str(output_path),
                    vcodec='libx264',
                    crf=self.video_quality,
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
            
            if compressed_size < original_size:
                compression_ratio = (1 - compressed_size / original_size) * 100
                self.logger.info(f"Video compressed: {compression_ratio:.1f}% size reduction")
                return str(output_path)
            else:
                self.logger.info("Compression didn't reduce size, keeping original")
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
