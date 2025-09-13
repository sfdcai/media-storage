import sqlite3
import logging
import os

LOG_FILE = os.getenv("SYNC_LOG_FILE", "sync.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

DB_FILE = "media.db"


def get_connection():
    return sqlite3.connect(DB_FILE)


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            icloud_id TEXT UNIQUE,
            created_date TEXT,
            local_path TEXT,
            status TEXT DEFAULT 'downloaded',
            synced_google TEXT,
            compressed TEXT,
            deleted_icloud TEXT,
            album_moved INTEGER DEFAULT 0,
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_filename ON media(filename);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_icloud_id ON media(icloud_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_status ON media(status);")
    conn.commit()
    conn.close()
    logger.info("✅ Database initialized.")


def add_media_record(filename, icloud_id, created_date, local_path, status="downloaded"):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT OR IGNORE INTO media (filename, icloud_id, created_date, local_path, status)
            VALUES (?, ?, ?, ?, ?)
        """, (filename, icloud_id, created_date, local_path, status))
        conn.commit()
        conn.close()
        logger.info(f"📥 Added/exists: {filename}")
    except Exception as e:
        logger.error(f"❌ Error inserting {filename}: {str(e)}")


def update_status(icloud_id, field, value):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(f"""
            UPDATE media
            SET {field} = ?, last_updated = CURRENT_TIMESTAMP
            WHERE icloud_id = ?
        """, (value, icloud_id))
        conn.commit()
        conn.close()
        logger.info(f"🔄 Updated {icloud_id}: {field} = {value}")
    except Exception as e:
        logger.error(f"❌ Error updating {icloud_id}: {str(e)}")
