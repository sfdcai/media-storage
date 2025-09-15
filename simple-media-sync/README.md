# Simple Media Sync

A comprehensive CLI tool for complete media workflow: download from iCloud, sync to NAS, sync to Pixel, compress, and delete from iCloud with comprehensive database tracking.

## Features

- **Complete Workflow**: Download → Sync to NAS → Sync to Pixel → Compress → Delete from iCloud
- **Advanced Compression**: Configurable compression strategies with year-based criteria
- **Multi-Device Sync**: Sync to NAS storage and Google Pixel devices
- **iCloud Management**: Download and delete files from iCloud
- **Comprehensive Tracking**: Track all workflow stages and compression metadata in Supabase
- **Flexible Configuration**: Choose compression strategies, quality settings, and file criteria
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
- **Compression Strategy**: Choose from Aggressive, Balanced, Conservative, or Custom
- **Compression Options**: Configure image/video compression, year-based criteria
- **Pixel Sync**: Optional Google Pixel device synchronization

### 4. Test Connections

Test your connections:

```bash
# Test Supabase
python main.py test --supabase

# Test iCloud
python main.py test --icloud

# Test NAS
python main.py test --nas

# Test Pixel
python main.py test --pixel
```

## Usage

### Full Workflow (Recommended)

Run the complete workflow: download from iCloud → sync to NAS → sync to Pixel → compress → delete from iCloud:

```bash
# Full workflow with dry run
python main.py sync --full-workflow --dry-run

# Full workflow (actual execution)
python main.py sync --full-workflow

# Skip compression
python main.py sync --full-workflow --skip-compression

# Skip NAS sync
python main.py sync --full-workflow --skip-nas

# Skip Pixel sync
python main.py sync --full-workflow --skip-pixel

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

View comprehensive sync and workflow status:
```bash
python main.py status
```

This shows:
- Total files processed
- Files compressed and space saved
- Files by workflow stage (downloaded, nas_synced, pixel_synced, compressed, completed, etc.)

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
   - `workflow_stage` (text) - tracks current stage in workflow
   - `compression_metadata` (jsonb) - stores compression statistics and settings

3. Get your project URL and API key from the Supabase dashboard

## Supported File Types

- Images: jpg, jpeg, png, gif, bmp, tiff, tif
- Videos: mp4, avi, mov, wmv, flv, webm, mkv
- Audio: mp3, wav, flac, aac, ogg, m4a

## Architecture

- `main.py` - CLI interface and complete workflow orchestration
- `config.py` - Configuration management with compression strategies
- `logger.py` - Simple logging
- `supabase_client.py` - Supabase integration with workflow tracking
- `sync_manager.py` - Basic file sync logic
- `compression.py` - Advanced media compression with configurable strategies
- `nas_sync.py` - NAS synchronization
- `pixel_sync.py` - Google Pixel device synchronization
- `icloud_manager.py` - iCloud download and deletion

## Workflow

1. **Download**: Use icloudpd to download files from iCloud
2. **Sync to NAS**: Copy files to network-attached storage
3. **Sync to Pixel**: Copy files to Google Pixel device (optional)
4. **Compress**: Compress images and videos based on configured strategy
5. **Track**: Record all workflow stages and compression metadata in Supabase
6. **Delete**: Remove original files from iCloud (only after successful sync)

## Compression Strategies

### Aggressive
- Maximum compression with lower quality
- Image quality: 60, Video CRF: 35
- Best for storage optimization

### Balanced (Default)
- Good compression with reasonable quality
- Image quality: 85, Video CRF: 28
- Best for most use cases

### Conservative
- Minimal compression with high quality
- Image quality: 95, Video CRF: 20
- Best for quality preservation

### Custom
- User-defined quality settings
- Configurable image quality (1-100) and video CRF (0-51)
- Advanced control over compression

### Year-Based Criteria
- Compress files older than specified years
- Use aggressive compression for very old files
- Skip compression for recent files

## Dependencies

- **Python packages**: supabase, Pillow, ffmpeg-python, icloudpd
- **External tools**: FFmpeg, icloudpd
- **Services**: Supabase (database), NAS storage, iCloud account, Google Pixel device (optional)

## Configuration Examples

### Compression Configuration
```json
{
  "compression": {
    "enabled": true,
    "strategy": "balanced",
    "compress_images": true,
    "compress_videos": true,
    "image_quality": 85,
    "video_quality": 28,
    "year_criteria": {
      "enabled": true,
      "compress_older_than_years": 2,
      "aggressive_compression_after_years": 5
    }
  }
}
```

### Pixel Sync Configuration
```json
{
  "pixel_sync": {
    "enabled": true,
    "device_path": "/media/pixel",
    "sync_folder": "DCIM",
    "delete_after_sync": false
  }
}
```
