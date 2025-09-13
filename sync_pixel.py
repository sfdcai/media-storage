#!/usr/bin/env python3
"""
Legacy Pixel Sync Module - DEPRECATED
This module is kept for backward compatibility but should use bulk_pixel_sync.py instead
"""

import warnings
from common import get_logger

logger = get_logger(__name__)

# Issue deprecation warning
warnings.warn(
    "sync_pixel.py is deprecated. Use bulk_pixel_sync.py instead.",
    DeprecationWarning,
    stacklevel=2
)

def main():
    """Legacy main function - redirects to bulk_pixel_sync"""
    logger.warning("sync_pixel.py is deprecated. Please use bulk_pixel_sync.py instead.")
    
    try:
        # Import and run the new module
        import bulk_pixel_sync
        return bulk_pixel_sync.main()
    except ImportError:
        logger.error("bulk_pixel_sync.py not found. Please ensure it's available.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
