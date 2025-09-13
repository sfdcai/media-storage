#!/usr/bin/env python3
"""
Legacy Database Module - DEPRECATED
This module is kept for backward compatibility but should use common.database instead
"""

import warnings
from common import db_manager, get_logger

logger = get_logger(__name__)

# Issue deprecation warning
warnings.warn(
    "media_db.py is deprecated. Use common.database.db_manager instead.",
    DeprecationWarning,
    stacklevel=2
)

# Legacy function wrappers for backward compatibility
def get_connection():
    """Legacy function - use db_manager.get_connection() instead"""
    warnings.warn("get_connection() is deprecated. Use db_manager.get_connection() instead.", DeprecationWarning)
    return db_manager.get_connection()

def init_db():
    """Legacy function - use db_manager.init_database() instead"""
    warnings.warn("init_db() is deprecated. Use db_manager.init_database() instead.", DeprecationWarning)
    return db_manager.init_database()

def add_media_record(filename, icloud_id, created_date, local_path, status="downloaded"):
    """Legacy function - use db_manager.add_media_record() instead"""
    warnings.warn("add_media_record() is deprecated. Use db_manager.add_media_record() instead.", DeprecationWarning)
    return db_manager.add_media_record(filename, icloud_id, created_date, local_path, status)

def update_status(icloud_id, field, value):
    """Legacy function - use db_manager.update_media_field() instead"""
    warnings.warn("update_status() is deprecated. Use db_manager.update_media_field() instead.", DeprecationWarning)
    return db_manager.update_media_field(icloud_id, field, value)
