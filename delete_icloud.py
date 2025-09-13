#!/usr/bin/env python3
"""
Final iCloud Deletion Pipeline
- Deletes files from local delete_pending folder
- Deletes files from iCloud album
- Updates DB: deleted_icloud='yes'
"""

import os
import logging
import sqlite3
from pyicloud import PyiCloudService
from pyicloud.exceptions import PyiCloudAPIResponseException

# --- Config ---
DB_FILE = "media.db"
DELETE_PENDING_DIR = "/mnt/wd_all_pictures/delete_pending"
ICLOUD_USERNAME = "tworedzebras@icloud.com"
ICLOUD_PASSWORD = ""  # or set via env variable
ALBUM_NAME = "DeletePending"

# --- Logging ---
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "delete_icloud.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
logger = logging.getLogger("delete_icloud")

# --- DB Functions ---
def get_files_to_delete():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, filename, local_path
        FROM media
        WHERE album_moved=1 AND deleted_icloud IS NULL
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def mark_deleted(media_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("UPDATE media SET deleted_icloud='yes' WHERE id=?", (media_id,))
    conn.commit()
    conn.close()

# --- iCloud Functions ---
def login_icloud(username, password):
    api = PyiCloudService(username, password)
    if api.requires_2fa:
        logger.warning("iCloud 2FA required. Complete on device.")
        code = input("Enter 2FA code: ")
        result = api.validate_2fa_code(code)
        if not result:
            raise Exception("2FA failed")
    return api

def get_album(api, album_name):
    albums = api.photos.albums
    for a in albums.values():
        if a.title == album_name:
            return a
    logger.warning(f"Album {album_name} not found.")
    return None

# --- Main Pipeline ---
def main():
    files = get_files_to_delete()
    if not files:
        logger.info("No files to delete from iCloud.")
        return

    try:
        icloud_api = login_icloud(ICLOUD_USERNAME, ICLOUD_PASSWORD)
    except Exception as e:
        logger.error(f"iCloud login failed: {e}")
        return

    album = get_album(icloud_api, ALBUM_NAME)
    if not album:
        logger.warning("iCloud album missing, will only delete locally.")

    for media_id, filename, path in files:
        # Delete from iCloud album
        if album:
            try:
                # Match by filename in album
                for photo in album.photos:
                    if photo.filename == filename:
                        photo.delete()
                        logger.info(f"Deleted {filename} from iCloud album {ALBUM_NAME}")
                        break
            except PyiCloudAPIResponseException as e:
                logger.error(f"Failed to delete {filename} from iCloud: {e}")

        # Delete local file
        if os.path.exists(path):
            try:
                os.remove(path)
                logger.info(f"Deleted local file: {path}")
            except Exception as e:
                logger.error(f"Failed to delete local file {path}: {e}")

        # Update DB
        mark_deleted(media_id)

    logger.info("✅ iCloud deletion pipeline complete.")


if __name__ == "__main__":
    main()
