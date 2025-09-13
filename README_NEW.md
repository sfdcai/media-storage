# Media Pipeline - Complete System

A comprehensive media management and synchronization pipeline for handling photos and videos from multiple sources with PM2 process management and database web viewer.

## 🚀 Quick Start

1. **Install the complete system:**
   ```bash
   chmod +x install_complete_system.sh
   sudo ./install_complete_system.sh
   ```

2. **Configure credentials:**
   ```bash
   # Edit the environment file
   sudo nano /opt/media-pipeline/.env
   
   # Add your credentials:
   ICLOUD_USERNAME=your.email@icloud.com
   ICLOUD_PASSWORD=your_password
   SYNCTHING_API_KEY=your_syncthing_api_key
   ```

3. **Test iCloud connection:**
   ```bash
   cd /opt/media-pipeline
   source .env
   /opt/media-pipeline/venv/bin/icloudpd --username $ICLOUD_USERNAME --directory /mnt/wd_all_pictures/incoming --download-only --recent 5
   ```

4. **Run the pipeline:**
   ```bash
   cd /opt/media-pipeline
   source .env
   /opt/media-pipeline/venv/bin/python pipeline_orchestrator.py
   ```

## 🌐 Web Interfaces

Access the following web interfaces:

- **PM2 Dashboard**: `http://your-server-ip:9615` - Monitor and manage all processes
- **Status Dashboard**: `http://your-server-ip:8082` - System status and monitoring
- **Configuration Interface**: `http://your-server-ip:8083` - Configure settings
- **Database Viewer**: `http://your-server-ip:8084` - View and query database
- **Syncthing**: `http://your-server-ip:8385` - File synchronization
- **VS Code Server**: `http://your-server-ip:8080` - Code editing

### Via Nginx (Clean URLs)

- **PM2 Dashboard**: `http://your-server-ip/pm2/`
- **Status Dashboard**: `http://your-server-ip/status/`
- **Configuration Interface**: `http://your-server-ip/config/`
- **Database Viewer**: `http://your-server-ip/db/`
- **Syncthing**: `http://your-server-ip/syncthing/`
- **VS Code Server**: `http://your-server-ip/vscode/`

## 🔧 PM2 Management

```bash
# Check status of all processes
pm2 status

# View logs
pm2 logs

# Restart all processes
pm2 restart all

# Stop all processes
pm2 stop all

# Monitor in real-time
pm2 monit

# Save current configuration
pm2 save
```

## 💻 CLI Usage

```bash
# Test the pipeline
cd /opt/media-pipeline
source .env
/opt/media-pipeline/venv/bin/python test_pipeline.py

# Run the full pipeline
/opt/media-pipeline/venv/bin/python pipeline_orchestrator.py

# Test iCloud connection
/opt/media-pipeline/venv/bin/icloudpd --username $ICLOUD_USERNAME --directory /mnt/wd_all_pictures/incoming --download-only --recent 5

# View database
sqlite3 /opt/media-pipeline/media.db
```

## 📊 Database Web Viewer

The database web viewer provides:
- **Table browsing**: View all database tables
- **Data exploration**: Browse table data with pagination
- **Custom queries**: Execute SQL queries
- **Real-time updates**: See data changes as they happen

Access at: `http://your-server-ip:8084` or `http://your-server-ip/db/`

## ⚙️ Configuration

Edit `/opt/media-pipeline/.env` to configure:
- iCloud credentials
- Syncthing API key and URL
- Directory paths
- Telegram notifications

## 🏗️ Architecture

The pipeline consists of several stages:

1. **iCloud Sync**: Downloads photos/videos from iCloud
2. **Pixel Sync**: Syncs photos from Google Pixel devices
3. **NAS Sync**: Synchronizes media to NAS
4. **Compression**: Compresses large media files
5. **Cleanup**: Removes duplicates and unwanted files
6. **Deletion**: Manages iCloud photo deletion

## 🗄️ Database

The system uses SQLite to track:
- Downloaded files
- Processing status
- File metadata
- Sync operations

## 📈 Monitoring

- **PM2 Dashboard**: Monitor all processes
- **Status Dashboard**: System status and health
- **Logs**: Check `/var/log/media-pipeline/`
- **Database Viewer**: Explore data visually

## 🔍 Troubleshooting

1. **Check PM2 status:**
   ```bash
   pm2 status
   pm2 logs
   ```

2. **Verify configuration:**
   ```bash
   cat /opt/media-pipeline/.env
   ```

3. **Test connections:**
   ```bash
   /opt/media-pipeline/venv/bin/python test_pipeline.py
   ```

4. **Check database:**
   ```bash
   sqlite3 /opt/media-pipeline/media.db
   ```

## 🧹 File Cleanup

To remove unnecessary installation files:

```bash
chmod +x cleanup_files.sh
./cleanup_files.sh
```

This will keep only the essential files for the media pipeline system.

## 📋 Features

- **iCloud Integration**: Download photos and videos from iCloud
- **Google Pixel Sync**: Sync photos from Google Pixel devices
- **NAS Synchronization**: Sync media to Network Attached Storage
- **Media Compression**: Compress large media files
- **Automated Cleanup**: Remove duplicate and unwanted files
- **PM2 Process Management**: Robust process management with auto-restart
- **Database Web Viewer**: View and query the media pipeline database
- **Web Interfaces**: Multiple web interfaces for management
- **Database Tracking**: Track all media operations in SQLite database
- **Telegram Notifications**: Get notified of pipeline status

## 📁 Directory Structure

- `/mnt/wd_all_pictures/incoming`: Landing zone for new files from iCloud
- `/mnt/wd_all_pictures/processed`: Processed files ready for sync
- `/opt/media-pipeline/`: Main application directory
- `/var/log/media-pipeline/`: Log files
- `/opt/media-pipeline/media.db`: SQLite database

## 🔐 Security

- Environment variables for sensitive data
- Proper file permissions
- User isolation with dedicated service user
- Secure API key management

## 📝 License

MIT License
