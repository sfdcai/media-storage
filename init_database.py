#!/usr/bin/env python3
"""
Database Initialization Script
Creates all required tables for the media pipeline system
"""

import sqlite3
import os
from pathlib import Path

def init_database():
    """Initialize the media pipeline database with all required tables"""
    
    db_path = '/opt/media-pipeline/media.db'
    
    print(f"🔧 Initializing database: {db_path}")
    
    # Create database connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create media table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL UNIQUE,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                initial_size INTEGER,
                current_size INTEGER,
                status TEXT DEFAULT 'downloaded',
                synced_google TEXT DEFAULT 'no',
                synced_nas TEXT DEFAULT 'no',
                deleted_icloud TEXT DEFAULT 'no',
                album_moved INTEGER DEFAULT 0,
                date_created TEXT,
                date_downloaded TEXT,
                last_compressed TEXT,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("  ✅ Created media table")
        
        # Create sync_logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation TEXT NOT NULL,
                filename TEXT,
                status TEXT NOT NULL,
                message TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("  ✅ Created sync_logs table")
        
        # Create pipeline_stats table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pipeline_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stat_name TEXT NOT NULL UNIQUE,
                stat_value TEXT NOT NULL,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("  ✅ Created pipeline_stats table")
        
        # Create configuration table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS configuration (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT NOT NULL UNIQUE,
                config_value TEXT,
                description TEXT,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("  ✅ Created configuration table")
        
        # Insert initial pipeline stats
        initial_stats = [
            ('total_files', '0', 'Total number of media files'),
            ('downloaded_files', '0', 'Number of downloaded files'),
            ('synced_google_files', '0', 'Number of files synced to Google Photos'),
            ('synced_nas_files', '0', 'Number of files synced to NAS'),
            ('compressed_files', '0', 'Number of compressed files'),
            ('deleted_files', '0', 'Number of deleted files'),
            ('total_size_downloaded', '0', 'Total size of downloaded files'),
            ('total_size_compressed', '0', 'Total size after compression'),
            ('last_sync_time', '', 'Last synchronization time'),
            ('last_compression_time', '', 'Last compression time')
        ]
        
        for stat_name, stat_value, description in initial_stats:
            cursor.execute('''
                INSERT OR REPLACE INTO pipeline_stats (stat_name, stat_value)
                VALUES (?, ?)
            ''', (stat_name, stat_value))
        
        print("  ✅ Inserted initial pipeline stats")
        
        # Insert default configuration
        default_config = [
            ('icloud_username', '', 'iCloud username'),
            ('icloud_password', '', 'iCloud password'),
            ('download_directory', '/mnt/wd_all_pictures/incoming', 'Download directory'),
            ('processed_directory', '/mnt/wd_all_pictures/processed', 'Processed directory'),
            ('compression_enabled', 'true', 'Enable compression'),
            ('auto_delete_enabled', 'false', 'Enable auto-delete from iCloud'),
            ('telegram_enabled', 'false', 'Enable Telegram notifications'),
            ('telegram_bot_token', '', 'Telegram bot token'),
            ('telegram_chat_id', '', 'Telegram chat ID')
        ]
        
        for config_key, config_value, description in default_config:
            cursor.execute('''
                INSERT OR REPLACE INTO configuration (config_key, config_value, description)
                VALUES (?, ?, ?)
            ''', (config_key, config_value, description))
        
        print("  ✅ Inserted default configuration")
        
        # Commit changes
        conn.commit()
        
        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"  ✅ Database initialized with {len(tables)} tables:")
        for table in tables:
            print(f"    - {table[0]}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error initializing database: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

def main():
    """Main function"""
    print("🚀 Media Pipeline Database Initialization")
    print("=" * 50)
    
    success = init_database()
    
    if success:
        print("\n✅ Database initialization completed successfully!")
        print("🎉 The media pipeline system is now fully operational!")
    else:
        print("\n❌ Database initialization failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
