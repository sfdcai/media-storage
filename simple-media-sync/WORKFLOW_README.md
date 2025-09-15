# Media Sync Workflow System

A comprehensive, modular media sync workflow system with real-time monitoring and Syncthing integration.

## Workflow Overview

```
iCloud Download → Pixel Sync → Pixel Verification → NAS Archive → Processing → Compression → iCloud Delete → Cleanup
```

## Architecture

### Core Components

- **`workflow_orchestrator.py`** - Main orchestrator for running workflows
- **`syncthing_client.py`** - Syncthing REST API integration
- **`file_manager.py`** - File operations with workflow prefixes
- **`workflow_tracker.py`** - Real-time progress tracking
- **`steps/`** - Individual workflow step modules

### Workflow Steps

| Step | Module | Description |
|------|--------|-------------|
| 1 | `step1_icloud_download.py` | Download files from iCloud to incoming folder |
| 2 | `step2_pixel_sync.py` | Move 5 files to Pixel sync folder |
| 3 | `step3_pixel_verification.py` | Verify files synced to Pixel via Syncthing |
| 4 | `step4_nas_archive.py` | Copy files to NAS archive |
| 5 | `step5_processing.py` | Move files to processing folder |
| 6 | `step6_compression.py` | Compress media files |
| 7 | `step7_icloud_delete.py` | Move files to iCloud delete folder |
| 8 | `step8_cleanup.py` | Clean up temporary files |

## Folder Structure

```
workflow/
├── incoming/           # iCloud downloads
├── pixel_sync/         # Files for Pixel sync (5 files)
├── nas_archive/        # Files copied to NAS
├── processing/         # Files being processed
└── icloud_delete/      # Files ready for iCloud deletion
```

## File Naming Convention

Files are renamed with workflow prefixes:
```
step02_pixel_sync_20250115_143022_IMG_1234.jpg
step04_nas_archive_20250115_143045_IMG_1234.jpg
step06_compressed_20250115_143102_IMG_1234.jpg
```

## Usage

### 1. Configuration Setup

```bash
python main.py config --setup
```

Configure:
- Supabase credentials
- iCloud settings
- NAS settings
- Compression strategies
- Workflow folders
- Syncthing API settings

### 2. Run Complete Workflow

```bash
# Run all steps
python workflow_orchestrator.py --workflow

# Run with dry-run mode
python workflow_orchestrator.py --workflow --dry-run

# Run specific range of steps
python workflow_orchestrator.py --workflow --start 1 --end 4
```

### 3. Run Individual Steps

```bash
# Run specific step
python workflow_orchestrator.py --step 1

# Run step 2 (Pixel sync)
python workflow_orchestrator.py --step 2
```

### 4. Monitor Workflow

```bash
# Show current status
python workflow_orchestrator.py --status

# List available steps
python workflow_orchestrator.py --list-steps

# Run without real-time monitoring
python workflow_orchestrator.py --workflow --no-monitoring
```

### 5. Direct Step Execution

```bash
# Run steps directly
python steps/step1_icloud_download.py
python steps/step2_pixel_sync.py
python steps/step3_pixel_verification.py
```

## Syncthing Integration

### Setup

1. Install Syncthing on your system
2. Configure API access in Syncthing settings
3. Get your API key and folder ID
4. Configure in the setup process

### API Endpoints Used

- `GET /rest/system/ping` - Test connection
- `GET /rest/system/connections` - Check device connections
- `GET /rest/db/status` - Get folder sync status
- `GET /rest/db/file` - Get specific file status
- `GET /rest/db/completion` - Get sync completion percentage

### Verification Process

1. Check if Pixel device is connected
2. Wait for files to sync (configurable timeout)
3. Verify each file is synced to all devices
4. Report sync status for each file

## Real-Time Monitoring

The workflow tracker provides:

- **Progress Tracking**: Real-time progress for each step
- **File Tracking**: Individual file status through workflow
- **Error Reporting**: Detailed error information
- **Performance Metrics**: Duration and throughput statistics
- **Status Display**: Console output with progress bars

### Monitoring Output

```
============================================================
WORKFLOW STATUS: workflow_20250115_143000
============================================================
Status: running
Progress: 37.5%
Current Step: 3
Files Processed: 15

Step Details:
  ✅ Step 1: iCloud Download (completed)
  ✅ Step 2: Pixel Sync (completed)
  🔄 Step 3: Pixel Verification (running)
    Files: 5/5
    Duration: 45.2s
============================================================
```

## Error Handling

### Halt on Error Strategy

- **Step Failure**: Workflow halts immediately on step failure
- **File Failure**: Individual file failures are logged but don't halt workflow
- **Critical Errors**: Connection failures, missing configurations halt workflow
- **Recovery**: Manual intervention required for failed workflows

### Error Types

1. **Configuration Errors**: Missing credentials, invalid paths
2. **Connection Errors**: Syncthing API, iCloud, NAS connectivity
3. **File Operation Errors**: Permission issues, disk space
4. **Sync Errors**: Timeout, device disconnection

## Database Tracking

### Supabase Schema

```sql
-- Enhanced media_files table
ALTER TABLE media_files ADD COLUMN workflow_stage VARCHAR(50);
ALTER TABLE media_files ADD COLUMN pixel_synced BOOLEAN DEFAULT FALSE;
ALTER TABLE media_files ADD COLUMN nas_archived BOOLEAN DEFAULT FALSE;
ALTER TABLE media_files ADD COLUMN compressed BOOLEAN DEFAULT FALSE;
ALTER TABLE media_files ADD COLUMN icloud_delete_ready BOOLEAN DEFAULT FALSE;
ALTER TABLE media_files ADD COLUMN compression_metadata JSONB;
```

### Workflow Stages

- `downloaded` - File downloaded from iCloud
- `pixel_sync_ready` - File ready for Pixel sync
- `pixel_verified` - File verified as synced to Pixel
- `nas_archived` - File archived to NAS
- `processing_ready` - File ready for processing
- `compressed` - File compressed
- `icloud_delete_ready` - File ready for iCloud deletion
- `completed` - Workflow completed

## Configuration

### Workflow Settings

```json
{
  "workflow": {
    "incoming_folder": "./incoming",
    "pixel_sync_folder": "./pixel_sync",
    "nas_archive_folder": "./nas_archive",
    "processing_folder": "./processing",
    "icloud_delete_folder": "./icloud_delete",
    "pixel_batch_size": 5,
    "sync_timeout_seconds": 300,
    "cleanup_after_hours": 24
  }
}
```

### Syncthing Settings

```json
{
  "syncthing": {
    "api_url": "http://localhost:8384",
    "api_key": "your_api_key",
    "pixel_folder_id": "folder_id",
    "timeout_seconds": 300
  }
}
```

## Testing

### Test Individual Components

```bash
# Test Syncthing connection
python -c "from syncthing_client import SyncthingClient; from config import Config; c=SyncthingClient(Config(), None); print(c.test_connection())"

# Test file manager
python -c "from file_manager import FileManager; from config import Config; fm=FileManager(Config(), None); print(fm.get_workflow_status())"
```

### Dry Run Testing

```bash
# Test complete workflow without changes
python workflow_orchestrator.py --workflow --dry-run
```

## Troubleshooting

### Common Issues

1. **Syncthing Connection Failed**
   - Check if Syncthing is running
   - Verify API URL and key
   - Check firewall settings

2. **Pixel Device Not Connected**
   - Ensure Pixel device is connected to Syncthing
   - Check device ID in Syncthing
   - Verify folder sharing settings

3. **File Sync Timeout**
   - Increase timeout in configuration
   - Check network connectivity
   - Verify file sizes aren't too large

4. **Permission Errors**
   - Check folder permissions
   - Ensure write access to all workflow folders
   - Run with appropriate user privileges

### Logs and Debugging

- All operations are logged with timestamps
- Real-time monitoring shows current status
- Database tracks all file operations
- Error messages include detailed context

## Performance Considerations

- **Batch Size**: Configurable Pixel sync batch size (default: 5)
- **Timeouts**: Configurable sync timeouts
- **Cleanup**: Automatic cleanup of old files
- **Monitoring**: Real-time progress tracking
- **Error Recovery**: Manual intervention for failures

## Security

- API keys stored in configuration file
- File operations use secure paths
- Database connections use authentication
- No sensitive data in logs
