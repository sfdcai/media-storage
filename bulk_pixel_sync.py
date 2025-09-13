#!/usr/bin/env python3
"""
Bulk Syncthing → Pixel / Google Photos Sync Tracker
- Checks all files in Syncthing folder
- Updates media.db with synced_google='yes'
- Optionally deletes local Pixel copy to free storage
"""

import requests
import sqlite3
import os
import logging

# --- Config ---
API_KEY = "AvjcSavWbypiKuT2E4mHu5DxMuLAbpx7"
BASE_URL = "http://192.168.1.118:8384//rest"
FOLDER_ID = "default"  # Syncthing folder ID on Pixel
PIXEL_LOCAL_FOLDER = "/storage/emulated/0/DCIM/Syncthing"  # local folder on Pixel if cleanup desired
DB_FILE = "media.db"
DELETE_LOCAL_PIXEL = True  # Set False if you want to keep local copies

# --- Logging ---
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "bulk_pixel_sync.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
logger = logging.getLogger("bulk_pixel_sync")


# --- Syncthing API Functions ---
def get_folder_status(folder_id):
    url = f"{BASE_URL}/db/file?folder={folder_id}&recursive=true"
    headers = {"X-API-Key": API_KEY}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json()  # list of all files with version info
    else:
        raise Exception(f"Syncthing API request failed: {r.status_code}")


def get_fully_synced_files(folder_id):
    files = get_folder_status(folder_id)
    synced_files = []
    for f in files:
        if f.get("globalVersion") == f.get("localVersion"):
            synced_files.append(f["name"])
    return synced_files


# --- DB Functions ---
def mark_files_synced(synced_files):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    updated_count = 0
    for filename in synced_files:
        cur.execute("UPDATE media SET synced_google='yes' WHERE filename=? AND synced_google IS NULL", (filename,))
        updated_count += cur.rowcount
    conn.commit()
    conn.close()
    return updated_count


# --- Pixel Local Cleanup ---
def delete_local_pixel_file(filename):
    path = os.path.join(PIXEL_LOCAL_FOLDER, filename)
    if os.path.exists(path):
        try:
            os.remove(path)
            logger.info(f"Deleted local Pixel file: {filename}")
        except Exception as e:
            logger.error(f"Failed to delete {filename} locally: {e}")
    else:
        logger.warning(f"Local Pixel file not found: {filename}")


# --- Main Pipeline ---
def main():
    logger.info("Starting bulk Pixel sync check...")
    try:
        synced_files = get_fully_synced_files(FOLDER_ID)
        logger.info(f"Total fully synced files in Syncthing: {len(synced_files)}")
    except Exception as e:
        logger.error(f"Error fetching Syncthing folder status: {e}")
        return

    updated_count = mark_files_synced(synced_files)
    logger.info(f"Updated DB records: {updated_count}")

    if DELETE_LOCAL_PIXEL:
        logger.info("Starting local Pixel cleanup...")
        for f in synced_files:
            delete_local_pixel_file(f)

    logger.info("✅ Bulk Pixel sync & cleanup completed.")


if __name__ == "__main__":
    main()
