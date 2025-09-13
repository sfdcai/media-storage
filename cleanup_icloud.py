#!/usr/bin/env python3
"""
iCloud Cleanup & Folder Management Pipeline
- Moves files after sync/compression
- Adds files to iCloud album
- Marks DB
"""

import os
import shutil
import logging
from pyicloud import PyiCloudService
from pyicloud.exceptions import PyiCloudAPIResponseException
import sqlite3

# --- Config ---
DB_FILE = "media.db"
INCOMING_DIR = "/mnt/wd_all_pictures/incoming"
PROCESSED_DIR = "/mnt/wd_all_pictures/processed"
DELETE_PENDING_DIR = "/mnt/wd_all_pictures/delete_pending"
ICLOUD_USERNAME = "tworedzebras@icloud.com"
ICLOUD_PASSWORD = ""  # or set via environment variable
ALBUM_NAME = "DeletePending"

# --- Logging ---
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "cleanup.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
logger = logging.getLogger("cleanup")

# --- DB Functions ---
def get_files_ready_for_cleanup():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, filename, local_path
        FROM media
        WHERE status='downloaded' AND synced_google='yes' AND album_moved=0
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def mark_album_moved(media_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("UPDATE media SET album_moved=1 WHERE id=?", (media_id,))
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

def get_or_create_album(api, album_name):
    albums = api.photos.albums
    for a in albums.values():
        if a.title == album_name:
            return a
    logger.info(f"Creating album: {album_name}")
    return api.photos.create_album(album_name)

# --- File Movement ---
def move_file(src, dst_folder):
    os.makedirs(dst_folder, exist_ok=True)
    dst = os.path.join(dst_folder, os.path.basename(src))
    shutil.move(src, dst)
    return dst

# --- Main Pipeline ---
def main():
    files = get_files_ready_for_cleanup()
    if not files:
        logger.info("No files ready for cleanup/moving.")
        return

    try:
        icloud_api = login_icloud(ICLOUD_USERNAME, ICLOUD_PASSWORD)
    except Exception as e:
        logger.error(f"iCloud login failed: {e}")
        return

    album = get_or_create_album(icloud_api, ALBUM_NAME)

    for media_id, filename, path in files:
        if not os.path.exists(path):
            logger.warning(f"File missing: {path}")
            continue

        # Move file to processed folder first
        processed_path = move_file(path, PROCESSED_DIR)
        logger.info(f"Moved {filename} → processed folder")

        # Then move to delete_pending folder
        delete_path = move_file(processed_path, DELETE_PENDING_DIR)
        logger.info(f"Moved {filename} → delete_pending folder")

        # Add to iCloud album
        try:
            album.add(delete_path)
            logger.info(f"Added {filename} to iCloud album {ALBUM_NAME}")
        except PyiCloudAPIResponseException as e:
            logger.error(f"Failed to add {filename} to iCloud album: {e}")

        # Update DB
        mark_album_moved(media_id)

    logger.info("✅ Cleanup and album assignment complete.")


if __name__ == "__main__":
    main()
