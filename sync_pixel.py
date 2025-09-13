import sqlite3
import logging

DB_FILE = "media.db"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pixel_sync")

def get_files_to_sync():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT id, filename, local_path FROM media WHERE synced_google IS NULL")
    files = cur.fetchall()
    conn.close()
    return files

def mark_synced(media_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("UPDATE media SET synced_google='yes' WHERE id=?", (media_id,))
    conn.commit()
    conn.close()

def main():
    files = get_files_to_sync()
    if not files:
        logger.info("No files to sync with Pixel.")
        return

    for media_id, filename, path in files:
        logger.info(f"Sync {filename} → Pixel (manual or 3rd-party)")
        # Optionally trigger CLI tool here
        mark_synced(media_id)

if __name__ == "__main__":
    main()
