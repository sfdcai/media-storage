# Simple Media Sync

A minimal CLI tool for complete media workflow: download from iCloud, compress, sync to NAS, and delete from iCloud using Supabase for tracking.

## Features

- **Complete Workflow**: Download → Compress → Sync to NAS → Delete from iCloud
- **Media Compression**: Automatic compression of images and videos
- **NAS Integration**: Sync files to network-attached storage
- **iCloud Management**: Download and delete files from iCloud
- **Supabase Tracking**: Track all processed files in database
- **Dry-run Mode**: Test workflow without making changes
- **Modular Design**: Skip any step in the workflow
- **Simple CLI**: Easy-to-use command-line interface

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install External Tools

- **FFmpeg**: For video compression
- **icloudpd**: For iCloud file management
- **Syncthing**: For file synchronization (optional)

### 3. Configure

Run the initial setup:

```bash
python main.py config --setup
```

This will prompt you for:
- Supabase URL and API key
- Source directories to sync
- iCloud credentials and download directory
- NAS mount path and media folder
- Compression settings

### 4. Test Connections

Test your connections:

```bash
# Test Supabase
python main.py test --supabase

# Test iCloud
python main.py test --icloud

# Test NAS
python main.py test --nas
```

## Usage

### Full Workflow (Recommended)

Run the complete workflow: download from iCloud → compress → sync to NAS → delete from iCloud:

```bash
# Full workflow with dry run
python main.py sync --full-workflow --dry-run

# Full workflow (actual execution)
python main.py sync --full-workflow

# Skip compression
python main.py sync --full-workflow --skip-compression

# Skip NAS sync
python main.py sync --full-workflow --skip-nas

# Skip iCloud deletion
python main.py sync --full-workflow --skip-icloud-delete
```

### Basic Sync

Sync files from local directories:

```bash
# Sync all configured directories
python main.py sync

# Sync a specific directory
python main.py sync --source /path/to/media

# Dry run (see what would be synced)
python main.py sync --dry-run
```

### Check Status

View sync status:
```bash
python main.py status
```

### View Configuration

Show current configuration:
```bash
python main.py config --show
```

## Supabase Setup

1. Create a new Supabase project
2. Create a table called `media_files` with these columns:
   - `id` (bigint, primary key, auto-increment)
   - `file_path` (text, unique)
   - `file_size` (bigint)
   - `file_hash` (text)
   - `last_modified` (timestamp)
   - `sync_status` (text)

3. Get your project URL and API key from the Supabase dashboard

## Supported File Types

- Images: jpg, jpeg, png, gif, bmp, tiff, tif
- Videos: mp4, avi, mov, wmv, flv, webm, mkv
- Audio: mp3, wav, flac, aac, ogg, m4a

## Architecture

- `main.py` - CLI interface and full workflow orchestration
- `config.py` - Configuration management
- `logger.py` - Simple logging
- `supabase_client.py` - Supabase integration for tracking
- `sync_manager.py` - Basic file sync logic
- `compression.py` - Media compression (images/videos)
- `nas_sync.py` - NAS synchronization
- `icloud_manager.py` - iCloud download and deletion

## Workflow

1. **Download**: Use icloudpd to download files from iCloud
2. **Compress**: Compress images (JPEG quality) and videos (H.264)
3. **Sync**: Copy compressed files to NAS storage
4. **Track**: Record file info in Supabase database
5. **Delete**: Remove original files from iCloud

## Dependencies

- **Python packages**: supabase, Pillow, ffmpeg-python
- **External tools**: FFmpeg, icloudpd
- **Services**: Supabase (database), NAS storage, iCloud account
