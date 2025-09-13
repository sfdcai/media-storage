#!/usr/bin/env python3
"""
Enhanced Database Management
Provides comprehensive database operations with error handling and connection management
"""

import sqlite3
import logging
import os
import shutil
import datetime
from typing import List, Tuple, Optional, Dict, Any
from contextlib import contextmanager
from pathlib import Path
from common.config import config_manager
from common.logger import get_logger

logger = get_logger(__name__)

class DatabaseManager:
    """Enhanced database manager with connection pooling and error handling"""
    
    def __init__(self):
        self.config = config_manager.get_database_config()
        self.db_path = self.config.file_path
        self._ensure_db_directory()
    
    def _ensure_db_directory(self):
        """Ensure database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def init_database(self):
        """Initialize database with proper schema"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create media table with all required columns
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS media (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filename TEXT NOT NULL,
                        icloud_id TEXT UNIQUE,
                        created_date TEXT,
                        local_path TEXT,
                        status TEXT DEFAULT 'downloaded',
                        synced_google TEXT,
                        synced_nas TEXT,
                        album_moved INTEGER DEFAULT 0,
                        deleted_icloud TEXT,
                        initial_size INTEGER,
                        current_size INTEGER,
                        last_compressed TEXT,
                        last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                        error_count INTEGER DEFAULT 0,
                        last_error TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Create indexes for better performance
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_filename ON media(filename);",
                    "CREATE INDEX IF NOT EXISTS idx_icloud_id ON media(icloud_id);",
                    "CREATE INDEX IF NOT EXISTS idx_status ON media(status);",
                    "CREATE INDEX IF NOT EXISTS idx_synced_google ON media(synced_google);",
                    "CREATE INDEX IF NOT EXISTS idx_synced_nas ON media(synced_nas);",
                    "CREATE INDEX IF NOT EXISTS idx_album_moved ON media(album_moved);",
                    "CREATE INDEX IF NOT EXISTS idx_deleted_icloud ON media(deleted_icloud);",
                    "CREATE INDEX IF NOT EXISTS idx_created_date ON media(created_date);",
                    "CREATE INDEX IF NOT EXISTS idx_last_updated ON media(last_updated);"
                ]
                
                for index_sql in indexes:
                    cursor.execute(index_sql)
                
                # Create pipeline_status table for tracking pipeline execution
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS pipeline_status (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        stage_name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        started_at TEXT,
                        completed_at TEXT,
                        files_processed INTEGER DEFAULT 0,
                        files_failed INTEGER DEFAULT 0,
                        error_message TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Create index for pipeline_status
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_pipeline_stage ON pipeline_status(stage_name);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_pipeline_status ON pipeline_status(status);")
                
                conn.commit()
                logger.info("✅ Database initialized successfully")
                
        except sqlite3.Error as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    def add_media_record(self, filename: str, icloud_id: str, created_date: str, 
                        local_path: str, status: str = "downloaded") -> bool:
        """Add a new media record to the database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO media 
                    (filename, icloud_id, created_date, local_path, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (filename, icloud_id, created_date, local_path, status))
                
                if cursor.rowcount > 0:
                    logger.info(f"📥 Added new media record: {filename}")
                    return True
                else:
                    logger.debug(f"📋 Media record already exists: {filename}")
                    return False
                    
        except sqlite3.Error as e:
            logger.error(f"❌ Error adding media record {filename}: {e}")
            return False
    
    def update_media_field(self, icloud_id: str, field: str, value: Any) -> bool:
        """Update a specific field for a media record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    UPDATE media
                    SET {field} = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE icloud_id = ?
                """, (value, icloud_id))
                
                if cursor.rowcount > 0:
                    logger.info(f"🔄 Updated {icloud_id}: {field} = {value}")
                    return True
                else:
                    logger.warning(f"⚠️ No record found for icloud_id: {icloud_id}")
                    return False
                    
        except sqlite3.Error as e:
            logger.error(f"❌ Error updating {icloud_id}: {e}")
            return False
    
    def get_media_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get all media records with a specific status"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM media WHERE status = ?", (status,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"❌ Error fetching media by status {status}: {e}")
            return []
    
    def get_media_ready_for_sync(self) -> List[Dict[str, Any]]:
        """Get media records ready for Google Photos sync"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM media 
                    WHERE status = 'downloaded' AND synced_google IS NULL
                """)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"❌ Error fetching media ready for sync: {e}")
            return []
    
    def get_media_ready_for_nas_sync(self) -> List[Dict[str, Any]]:
        """Get media records ready for NAS sync"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM media 
                    WHERE status = 'downloaded' AND synced_nas IS NULL
                """)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"❌ Error fetching media ready for NAS sync: {e}")
            return []
    
    def get_media_ready_for_compression(self) -> List[Dict[str, Any]]:
        """Get media records ready for compression"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM media 
                    WHERE status = 'downloaded' 
                    AND synced_google = 'yes' 
                    AND synced_nas = 'yes'
                    AND last_compressed IS NULL
                """)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"❌ Error fetching media ready for compression: {e}")
            return []
    
    def get_media_ready_for_cleanup(self) -> List[Dict[str, Any]]:
        """Get media records ready for iCloud cleanup"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM media 
                    WHERE status = 'downloaded' 
                    AND synced_google = 'yes' 
                    AND synced_nas = 'yes'
                    AND album_moved = 0
                """)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"❌ Error fetching media ready for cleanup: {e}")
            return []
    
    def get_media_ready_for_deletion(self) -> List[Dict[str, Any]]:
        """Get media records ready for iCloud deletion"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM media 
                    WHERE album_moved = 1 
                    AND deleted_icloud IS NULL
                """)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"❌ Error fetching media ready for deletion: {e}")
            return []
    
    def mark_synced_google(self, icloud_id: str) -> bool:
        """Mark media as synced to Google Photos"""
        return self.update_media_field(icloud_id, 'synced_google', 'yes')
    
    def mark_synced_nas(self, icloud_id: str) -> bool:
        """Mark media as synced to NAS"""
        return self.update_media_field(icloud_id, 'synced_nas', 'yes')
    
    def mark_compressed(self, icloud_id: str, new_size: int) -> bool:
        """Mark media as compressed and update size"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE media
                    SET current_size = ?, last_compressed = CURRENT_TIMESTAMP, last_updated = CURRENT_TIMESTAMP
                    WHERE icloud_id = ?
                """, (new_size, icloud_id))
                
                if cursor.rowcount > 0:
                    logger.info(f"🗜️ Marked compressed: {icloud_id} (new size: {new_size})")
                    return True
                return False
        except sqlite3.Error as e:
            logger.error(f"❌ Error marking compressed {icloud_id}: {e}")
            return False
    
    def set_initial_size(self, icloud_id: str, file_path: str) -> bool:
        """Set initial file size if not already set"""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"File not found for size calculation: {file_path}")
                return False
            
            size = os.path.getsize(file_path)
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE media
                    SET initial_size = COALESCE(initial_size, ?)
                    WHERE icloud_id = ?
                """, (size, icloud_id))
                
                if cursor.rowcount > 0:
                    logger.debug(f"📏 Set initial size for {icloud_id}: {size} bytes")
                    return True
                return False
        except Exception as e:
            logger.error(f"❌ Error setting initial size for {icloud_id}: {e}")
            return False
    
    def mark_album_moved(self, icloud_id: str) -> bool:
        """Mark media as moved to delete pending album"""
        return self.update_media_field(icloud_id, 'album_moved', 1)
    
    def mark_deleted_icloud(self, icloud_id: str) -> bool:
        """Mark media as deleted from iCloud"""
        return self.update_media_field(icloud_id, 'deleted_icloud', 'yes')
    
    def increment_error_count(self, icloud_id: str, error_message: str) -> bool:
        """Increment error count for a media record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE media
                    SET error_count = error_count + 1, 
                        last_error = ?, 
                        last_updated = CURRENT_TIMESTAMP
                    WHERE icloud_id = ?
                """, (error_message, icloud_id))
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"❌ Error incrementing error count for {icloud_id}: {e}")
            return False
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get counts by status
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN synced_google = 'yes' THEN 1 ELSE 0 END) as synced_google,
                        SUM(CASE WHEN synced_nas = 'yes' THEN 1 ELSE 0 END) as synced_nas,
                        SUM(CASE WHEN album_moved = 1 THEN 1 ELSE 0 END) as album_moved,
                        SUM(CASE WHEN deleted_icloud = 'yes' THEN 1 ELSE 0 END) as deleted_icloud,
                        SUM(CASE WHEN last_compressed IS NOT NULL THEN 1 ELSE 0 END) as compressed
                    FROM media
                """)
                
                stats = dict(cursor.fetchone())
                
                # Get recent activity
                cursor.execute("""
                    SELECT COUNT(*) as recent_activity
                    FROM media
                    WHERE last_updated > datetime('now', '-24 hours')
                """)
                
                stats['recent_activity'] = cursor.fetchone()['recent_activity']
                
                return stats
        except sqlite3.Error as e:
            logger.error(f"❌ Error getting pipeline stats: {e}")
            return {}
    
    def backup_database(self) -> bool:
        """Create a backup of the database"""
        if not self.config.backup_enabled:
            return True
        
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.db_path}.backup_{timestamp}"
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"💾 Database backed up to: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Database backup failed: {e}")
            return False
    
    def start_pipeline_stage(self, stage_name: str) -> int:
        """Start tracking a pipeline stage"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO pipeline_status (stage_name, status, started_at)
                    VALUES (?, 'running', CURRENT_TIMESTAMP)
                """, (stage_name,))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"❌ Error starting pipeline stage {stage_name}: {e}")
            return -1
    
    def complete_pipeline_stage(self, stage_id: int, files_processed: int = 0, 
                               files_failed: int = 0, error_message: str = None):
        """Complete tracking a pipeline stage"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE pipeline_status
                    SET status = 'completed', 
                        completed_at = CURRENT_TIMESTAMP,
                        files_processed = ?,
                        files_failed = ?,
                        error_message = ?
                    WHERE id = ?
                """, (files_processed, files_failed, error_message, stage_id))
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"❌ Error completing pipeline stage {stage_id}: {e}")

# Global database manager instance
db_manager = DatabaseManager()
