# Media Sync Workflow - Simple Version

A clean, modular media sync workflow system.

## Quick Start

### 1. Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run setup
python setup.py

# Test setup
python test_setup.py
```

### 2. Run Workflow

**Option A: Run individual steps**
```bash
python steps/step1_icloud_download.py
python steps/step2_pixel_sync.py
python steps/step3_pixel_verification.py
# ... etc
```

**Option B: Run complete workflow**
```bash
python workflow_orchestrator.py --workflow
```

**Option C: Run specific steps**
```bash
python workflow_orchestrator.py --workflow --start 1 --end 4
```

## Project Structure

```
simple-media-sync/
├── config.json              # Configuration file
├── setup.py                 # Setup script
├── test_setup.py           # Test script
├── workflow_orchestrator.py # Main orchestrator
├── steps/                   # Individual workflow steps
│   ├── step1_icloud_download.py
│   ├── step2_pixel_sync.py
│   ├── step3_pixel_verification.py
│   ├── step4_nas_archive.py
│   ├── step5_processing.py
│   ├── step6_compression.py
│   ├── step7_icloud_delete.py
│   └── step8_cleanup.py
└── Core modules:
    ├── config_loader.py     # Simple config loader
    ├── syncthing_client.py  # Syncthing API client
    ├── file_manager.py      # File operations
    ├── workflow_tracker.py  # Progress tracking
    ├── supabase_client.py   # Database client
    ├── compression.py       # Media compression
    ├── icloud_manager.py    # iCloud operations
    └── logger.py           # Logging
```

## Workflow Steps

1. **Download** - Download files from iCloud
2. **Pixel Sync** - Move 5 files to Pixel sync folder
3. **Verification** - Verify files synced via Syncthing
4. **NAS Archive** - Copy files to NAS
5. **Processing** - Move files to processing folder
6. **Compression** - Compress media files
7. **iCloud Delete** - Move files for deletion
8. **Cleanup** - Clean up temporary files

## Configuration

Edit `config.json` directly or run `python setup.py` to configure:

- Supabase credentials
- iCloud settings
- Syncthing API settings
- Workflow folders
- Compression settings

## Requirements

- Python 3.7+
- Supabase account
- iCloud account
- Syncthing installed and running
- FFmpeg (for video compression)

## Installation

```bash
# Install Python packages
pip install -r requirements.txt

# Install external tools
# Ubuntu/Debian:
sudo apt install syncthing ffmpeg

# Or use package managers for your OS
```

## Usage Examples

```bash
# Run complete workflow
python workflow_orchestrator.py --workflow

# Run with dry-run
python workflow_orchestrator.py --workflow --dry-run

# Run specific step
python workflow_orchestrator.py --step 2

# Show status
python workflow_orchestrator.py --status

# List available steps
python workflow_orchestrator.py --list-steps
```

## Direct Step Execution

You can run any step directly:

```bash
python steps/step1_icloud_download.py
python steps/step2_pixel_sync.py
python steps/step3_pixel_verification.py
```

Each step is independent and can be run separately for testing or debugging.
