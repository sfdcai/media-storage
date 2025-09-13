Full Media Backup & Compression Pipeline
1️⃣ Overview / Goal
Goal:
Automate backup, compression, and storage optimization for iPhone media while minimizing iCloud storage usage.
Devices / Systems:
•	Primary iPhones (64GB) → taking photos/videos
•	iCloud → current backup (over 500GB)
•	NAS (1TB) → central storage
•	Pixel 1 → unlimited Google Photos storage
•	Proxmox Server / Home Assistant → runs automation scripts
•	Spare iPhone 6 → optional for syncing iCloud if needed
Objectives:
1.	Reduce iCloud storage usage.
2.	Ensure all media is safely backed up on NAS and Pixel.
3.	Maintain metadata, compression history, sync status.
4.	Automate deletion from iCloud after sync/compression.
5.	Keep modular, auditable logs and database history.
________________________________________
2️⃣ Folder & DB Structure
Folder Layout (on NAS/Proxmox):
/mnt/wd_all_pictures/
    incoming/           # freshly downloaded from iCloud
    processed/          # after Pixel sync + compression
    delete_pending/     # after folder movement, ready for iCloud deletion
    logs/               # all logs per module
Database (media.db) – SQLite:
Column	Description
id	Primary key
filename	File name
icloud_id	Unique iCloud ID
created_date	Original creation date
local_path	Full path in NAS
status	downloaded / processed / error
synced_google	yes/no
compressed	yes/no
initial_size	File size at download
current_size	Updated size after compression
last_compressed	Timestamp of last compression
deleted_icloud	yes/no
album_moved	0/1
last_updated	Auto timestamp
________________________________________
3️⃣ Scripts & Pipeline
Step	Script	Function
0	sync_icloud.py	Download iCloud media → insert metadata into DB.
1	sync_pixel.py	Sync to Pixel / Google Photos → mark synced_google='yes'.
2	compress_media.py	Tiered compression based on file age → update current_size & last_compressed.
3	cleanup_icloud.py	Move files to processed/ → delete_pending/ → add to iCloud album → mark album_moved=1.
4	delete_icloud.py	Delete files from delete_pending/ and iCloud album → mark deleted_icloud='yes'.
5	Optional	report_db.py → generate summary / CSV of DB for auditing.
Flow:
iPhone → iCloud → NAS/incoming
           │
           ▼
      sync_pixel.py
           │
           ▼
 compress_media.py (tiered)
           │
           ▼
 cleanup_icloud.py
           │
           ▼
 delete_icloud.py
________________________________________
4️⃣ Master / Main Script
You can create a run_pipeline.py to execute all modules sequentially:
import subprocess
import logging

LOG_FILE = "logs/main_pipeline.log"
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()])
logger = logging.getLogger("main_pipeline")

modules = [
    "sync_icloud.py",
    "sync_pixel.py",
    "compress_media.py",
    "cleanup_icloud.py",
    "delete_icloud.py"
]

def run_module(module):
    logger.info(f"--- Running {module} ---")
    result = subprocess.run(["python3", module])
    if result.returncode != 0:
        logger.error(f"{module} failed! Return code: {result.returncode}")
    else:
        logger.info(f"{module} completed successfully.")

def main():
    for mod in modules:
        run_module(mod)
    logger.info("✅ Full pipeline complete.")

if __name__ == "__main__":
    main()
This gives a single entry point for the entire workflow and keeps each module independent.
________________________________________
5️⃣ AI-Friendly Prompt / Description
Prompt for AI Assistance:
“I am building a modular media backup pipeline for iPhones using iCloud, NAS, and a Pixel phone.
The pipeline includes: downloading iCloud media, syncing to Pixel, tiered compression by file age, folder organization, and automated deletion from iCloud.
Each step updates a SQLite DB (media.db) with metadata, compression size, sync status, album movement, and deletion flags.
Logs are kept separate for each module (logs/).
Scripts are modular (sync_icloud.py, sync_pixel.py, compress_media.py, cleanup_icloud.py, delete_icloud.py) and a master script (run_pipeline.py) executes them sequentially.
Please provide recommendations, improvements, or code for missing steps while ensuring database integrity, compression strategy, and automated deletion are safely implemented.”
________________________________________
6️⃣ Recommendations / Next Steps
1.	Automation & Scheduling
o	Use cron or systemd timers on Proxmox / Home Assistant to run run_pipeline.py nightly or hourly.
o	Ensure each script logs success/failure independently.
2.	Monitoring & Dashboard
o	Connect sqlite-web or DB Browser for visualizing media.db.
o	Optionally, integrate Home Assistant dashboard for storage usage, compression stats, and sync status.
3.	Error Handling & Recovery
o	If any module fails, run_pipeline.py logs error; can send alert (email/notification).
o	Retry strategy for iCloud / Pixel network errors.
4.	Tiered Compression
o	Already implemented; consider adding adjustable parameters (light/medium/aggressive).
o	Can also implement archival tier: older than X years → archive to cold storage, delete from main NAS.
5.	Testing
o	Run scripts manually first on small batch of files to ensure DB updates, compression, folder moves, and deletion all work correctly.
o	Keep backups of NAS before testing deletions.
6.	Security & 2FA
o	Store iCloud credentials securely (environment variables or keyring).
o	Handle 2FA tokens safely to avoid repeated prompts.
7.	Extensions for AI / Automation
o	AI can recommend: automated compression settings, storage alerts, backup verification, and even smart deletion rules based on file age/duplicates.
o	AI can also help generate reports from media.db in CSV/Excel/PDF formats for auditing.
________________________________________
✅ Summary
•	All scripts are modular → safe, auditable, extendable.
•	Database tracks everything → compression, sync, deletion.
•	Master script allows full sequential execution.
•	Folder structure + logs maintain clarity and reduce human errors.
•	AI can take over optimization, report generation, or advanced automation

