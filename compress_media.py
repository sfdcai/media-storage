# compress_media.py
# Tiered Compression Pipeline

from datetime import datetime
from dateutil import parser
import os
import sqlite3
import logging
from PIL import Image
import subprocess

# --- Logging ---
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "compression.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
logger = logging.getLogger("compression")

DB_FILE = "media.db"

def get_connection():
    return sqlite3.connect(DB_FILE)

# --- Compression Helpers ---
def compress_image(file_path, quality):
    try:
        img = Image.open(file_path)
        img.save(file_path, optimize=True, quality=quality)
        size = os.path.getsize(file_path)
        logger.info(f"Compressed image {file_path} → {size} bytes (quality={quality})")
        return size
    except Exception as e:
        logger.error(f"Image compression failed for {file_path}: {e}")
        return None

def compress_video(file_path, crf):
    tmp = file_path + ".tmp.mp4"
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", file_path,
            "-vcodec", "libx264", "-crf", str(crf),
            "-preset", "slow", tmp
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.replace(tmp, file_path)
        size = os.path.getsize(file_path)
        logger.info(f"Compressed video {file_path} → {size} bytes (crf={crf})")
        return size
    except Exception as e:
        logger.error(f"Video compression failed for {file_path}: {e}")
        if os.path.exists(tmp):
            os.remove(tmp)
        return None

def compress_file(file_path, age_years):
    ext = file_path.lower().split('.')[-1]
    if age_years < 1:
        img_quality, vid_crf = 85, 26
    elif 1 <= age_years <= 3:
        img_quality, vid_crf = 75, 28
    else:
        img_quality, vid_crf = 65, 30

    if ext in ["jpg", "jpeg", "png", "webp"]:
        return compress_image(file_path, img_quality)
    elif ext in ["mp4", "mov", "avi", "mkv"]:
        return compress_video(file_path, vid_crf)
    else:
        logger.warning(f"Unsupported file type: {file_path}")
        return None

# --- DB Functions ---
def get_files_to_compress():
    conn = get_connection()
    cur = conn.cursor()
    # Only compress files that are synced to Google
    cur.execute("""
        SELECT id, filename, local_path, created_date
        FROM media
        WHERE status='downloaded' AND synced_google='yes'
    """)
    files = cur.fetchall()
    conn.close()
    return files

def update_db(media_id, new_size):
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute("""
        UPDATE media
        SET current_size=?, last_compressed=?
        WHERE id=?
    """, (new_size, now, media_id))
    conn.commit()
    conn.close()

def set_initial_size(media_id, file_path):
    size = os.path.getsize(file_path)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE media
        SET initial_size=COALESCE(initial_size, ?)
        WHERE id=?
    """, (size, media_id))
    conn.commit()
    conn.close()

# --- Main Pipeline ---
def main():
    files = get_files_to_compress()
    if not files:
        logger.info("No files ready for compression.")
        return

    for row in files:
        media_id, filename, path, created_date = row
        if not os.path.exists(path):
            logger.warning(f"Missing file: {path}")
            continue

        set_initial_size(media_id, path)
        age_years = (datetime.utcnow() - parser.parse(created_date)).days / 365
        new_size = compress_file(path, age_years)
        if new_size:
            update_db(media_id, new_size)

    logger.info("Compression pipeline finished.")

if __name__ == "__main__":
    main()
