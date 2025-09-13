# 🚀 Media Pipeline Complete Setup Guide

## 📋 Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+ (LTS recommended)
- **RAM**: Minimum 2GB, Recommended 4GB+
- **Storage**: Minimum 20GB free space
- **Network**: Stable internet connection
- **Container**: Proxmox LXC container (recommended)

### Proxmox LXC Setup
```bash
# Create LXC container with these settings:
# - Template: Ubuntu 22.04
# - Memory: 2GB+
# - Storage: 20GB+
# - Network: Bridge with internet access

# Mount NAS storage (run on Proxmox host)
pct set 113 -mp0 /mnt/wd_all_pictures,mp=/mnt/wd_all_pictures

# Start container
pct start 113
```

## 🔧 Installation Steps

### 1. Download and Run Installation Script

```bash
# Connect to your LXC container
pct enter 113

# Download the project (or copy files)
git clone <your-repo-url> /tmp/media-pipeline
cd /tmp/media-pipeline

# Make installation script executable
chmod +x install.sh

# Run installation (this will take 10-15 minutes)
./install.sh
```

### 2. Configure Credentials

```bash
# Edit the environment file
sudo nano /opt/media-pipeline/.env

# Fill in your credentials:
ICLOUD_USERNAME=your_icloud_email@example.com
ICLOUD_PASSWORD=your_icloud_password
SYNCTHING_API_KEY=your_syncthing_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

### 3. Complete Setup

```bash
# Run the completion script
sudo -u media-pipeline /opt/media-pipeline/complete_setup.sh
```

### 4. Access Web Interfaces

- **Media Pipeline Dashboard**: `http://your-container-ip`
- **Syncthing Web UI**: `http://your-container-ip:8384`

## 📱 Telegram Bot Setup

### 1. Create Telegram Bot
1. Message `@BotFather` on Telegram
2. Send `/newbot`
3. Choose a name and username for your bot
4. Save the bot token

### 2. Get Chat ID
1. Add your bot to a chat or message it directly
2. Send a message to your bot
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Find your chat ID in the response

### 3. Configure Notifications
The system will automatically send notifications for:
- Pipeline start/completion
- Stage completion
- Errors and failures
- Daily summaries
- System alerts

## 🔧 Configuration Options

### Pipeline Stages
You can run specific stages or the complete pipeline:

```bash
# Run complete pipeline
python /opt/media-pipeline/pipeline_orchestrator.py

# Run specific stages
python /opt/media-pipeline/pipeline_orchestrator.py --stages icloud_sync pixel_sync

# Dry run (test mode)
python /opt/media-pipeline/pipeline_orchestrator.py --dry-run
```

### Compression Settings
Adjust compression quality in `/etc/media-pipeline/config.yaml`:

```yaml
compression:
  enabled: true
  light_quality: 85    # < 1 year old files
  medium_quality: 75   # 1-3 years old files
  heavy_quality: 65    # > 3 years old files
```

### Directory Structure
The system uses these directories:
- `/mnt/wd_all_pictures/incoming` - New downloads from iCloud
- `/mnt/wd_all_pictures/backup` - Files ready for sync
- `/mnt/wd_all_pictures/compress` - Files ready for compression
- `/mnt/wd_all_pictures/delete_pending` - Files ready for deletion
- `/mnt/wd_all_pictures/processed` - Intermediate processing

## 🔄 Automation

### Cron Job
The system automatically runs daily at 2 AM:
```bash
# View cron job
sudo -u media-pipeline crontab -l

# Edit cron job
sudo -u media-pipeline crontab -e
```

### Systemd Services
All services are managed by systemd:
```bash
# Check service status
sudo systemctl status media-pipeline
sudo systemctl status media-pipeline-web
sudo systemctl status syncthing@media-pipeline

# Start/stop services
sudo systemctl start media-pipeline
sudo systemctl stop media-pipeline
```

## 📊 Monitoring

### Web Dashboard
Access the dashboard at `http://your-container-ip` to monitor:
- System resources (CPU, memory, disk)
- Pipeline statistics
- Service status
- Directory information
- Real-time logs
- Pipeline execution

### Log Files
Logs are stored in `/var/log/media-pipeline/`:
- `media_pipeline.log` - Main pipeline log
- `sync_icloud.log` - iCloud operations
- `bulk_pixel_sync.log` - Pixel sync operations
- `bulk_nas_sync.log` - NAS sync operations
- `compress_media.log` - Compression operations
- `cleanup_icloud.log` - Cleanup operations
- `delete_icloud.log` - Deletion operations

### Telegram Notifications
Receive real-time notifications about:
- Pipeline status
- Errors and warnings
- Daily summaries
- System alerts

## 🛠️ Troubleshooting

### Common Issues

#### 1. iCloud Authentication Failed
```bash
# Check credentials
cat /opt/media-pipeline/.env | grep ICLOUD

# Test iCloud connection
python /opt/media-pipeline/test_pipeline.py
```

#### 2. Syncthing Connection Failed
```bash
# Check Syncthing status
sudo systemctl status syncthing@media-pipeline

# Check API key
curl -H "X-API-Key: YOUR_API_KEY" http://localhost:8384/rest/system/status
```

#### 3. Telegram Notifications Not Working
```bash
# Test Telegram connection
python -c "from telegram_notifier import test_telegram_connection; test_telegram_connection()"

# Send test message
python -c "from telegram_notifier import send_test_message; send_test_message()"
```

#### 4. Web UI Not Accessible
```bash
# Check web service status
sudo systemctl status media-pipeline-web

# Check nginx status
sudo systemctl status nginx

# Check port binding
sudo netstat -tlnp | grep :8080
```

### Log Analysis
```bash
# View recent logs
tail -f /var/log/media-pipeline/media_pipeline.log

# Search for errors
grep -i error /var/log/media-pipeline/*.log

# View service logs
sudo journalctl -u media-pipeline -f
```

## 🔒 Security Considerations

### File Permissions
```bash
# Check permissions
ls -la /opt/media-pipeline/
ls -la /mnt/wd_all_pictures/

# Fix permissions if needed
sudo chown -R media-pipeline:media-pipeline /opt/media-pipeline/
sudo chown -R media-pipeline:media-pipeline /mnt/wd_all_pictures/
```

### Firewall (if applicable)
```bash
# Allow web access
sudo ufw allow 80/tcp
sudo ufw allow 8384/tcp

# Allow SSH (if needed)
sudo ufw allow 22/tcp
```

### Credential Security
- Never commit `.env` file to version control
- Use strong passwords
- Regularly rotate API keys
- Monitor access logs

## 📈 Performance Optimization

### System Resources
- Monitor CPU and memory usage
- Ensure adequate disk space
- Use SSD storage for better performance
- Consider RAID for data protection

### Pipeline Optimization
- Adjust compression settings based on storage needs
- Configure appropriate retry limits
- Monitor error rates and adjust timeouts
- Use dry-run mode for testing

### Network Optimization
- Use wired connection for stability
- Monitor bandwidth usage
- Consider QoS settings for iCloud downloads
- Optimize Syncthing settings

## 🔄 Backup and Recovery

### Database Backup
```bash
# Manual backup
cp /opt/media-pipeline/media.db /opt/media-pipeline/media.db.backup.$(date +%Y%m%d)

# Automated backup (already configured)
# Backups are created automatically every 24 hours
```

### Configuration Backup
```bash
# Backup configuration
tar -czf media-pipeline-config-$(date +%Y%m%d).tar.gz /etc/media-pipeline/ /opt/media-pipeline/.env
```

### Recovery
```bash
# Restore database
cp /opt/media-pipeline/media.db.backup.YYYYMMDD /opt/media-pipeline/media.db

# Restore configuration
tar -xzf media-pipeline-config-YYYYMMDD.tar.gz -C /
```

## 📞 Support

### Getting Help
1. Check logs for error messages
2. Review this setup guide
3. Test individual components
4. Check system resources
5. Verify network connectivity

### Useful Commands
```bash
# System status
sudo systemctl status media-pipeline media-pipeline-web syncthing@media-pipeline nginx

# Pipeline status
python /opt/media-pipeline/pipeline_orchestrator.py --status

# Test environment
python /opt/media-pipeline/test_pipeline.py

# View configuration
cat /etc/media-pipeline/config.yaml
```

---

**Note**: This setup provides a production-ready media pipeline with comprehensive monitoring, error handling, and automation. The system is designed to be reliable, secure, and easy to maintain.
