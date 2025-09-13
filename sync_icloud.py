import os
import subprocess
import yaml
import logging
import datetime
import media_db

# --- Logging Setup ---
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


def load_config(config_file="config.yaml"):
    with open(config_file, "r") as f:
        return yaml.safe_load(f)


def run_icloudpd(cfg):
    """
    Run icloudpd command to download files.
    """
    cmd = [
        "icloudpd",
        "--username", cfg["icloud"]["username"],
        "--directory", cfg["icloud"]["directory"]
    ]

    if cfg["icloud"].get("days", 0) > 0:
        cmd.extend(["--recent", str(cfg["icloud"]["days"])])
    elif cfg["icloud"].get("recent", 0) > 0:
        cmd.extend(["--recent", str(cfg["icloud"]["recent"])])

    if cfg["icloud"].get("auto_delete", False):
        cmd.append("--auto-delete")

    logger.info(f"▶️ Running icloudpd: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        logger.info("✅ iCloud download finished.")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ icloudpd failed: {e}")


def scan_and_update_db(cfg):
    """
    After download, scan the target folder and insert new media into DB.
    """
    base_dir = cfg["icloud"]["directory"]
    logger.info(f"🔍 Scanning {base_dir} for new media...")

    for root, dirs, files in os.walk(base_dir):
        for fname in files:
            full_path = os.path.join(root, fname)
            created_date = datetime.datetime.fromtimestamp(
                os.path.getctime(full_path)
            ).isoformat()

            icloud_id = fname  # Simplified: use filename as ID (icloudpd doesn’t expose real ID)
            media_db.add_media_record(
                filename=fname,
                icloud_id=icloud_id,
                created_date=created_date,
                local_path=full_path,
                status="downloaded"
            )


def main():
    cfg = load_config()
    media_db.init_db()
    run_icloudpd(cfg)
    scan_and_update_db(cfg)
    logger.info("🎉 Sync complete!")


if __name__ == "__main__":
    main()
