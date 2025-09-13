# Media Pipeline - Portable Deployment Solution

## 🎯 **Complete Self-Contained Solution**

This is a **completely portable, self-contained media pipeline** that can be deployed on any Ubuntu LXC container without depending on external repositories or services.

## ✨ **Key Features**

- ✅ **100% Portable** - Deploy anywhere, anytime
- ✅ **Offline Capable** - Works without internet access
- ✅ **Self-Contained** - All dependencies included
- ✅ **Future-Proof** - No external dependencies to break
- ✅ **One-Command Deploy** - Simple installation process
- ✅ **Production Ready** - Systemd services, logging, monitoring

## 🚀 **Quick Start**

### Option 1: Universal Deployment (Recommended)
```bash
# Copy your project to any LXC container
scp -r media-storage/ root@your-container-ip:/root/

# SSH into container
ssh root@your-container-ip

# Deploy automatically
cd media-storage/
chmod +x deploy_anywhere.sh
./deploy_anywhere.sh
```

### Option 2: Create Portable Package
```bash
# Create a portable package
chmod +x create_portable_package.sh
./create_portable_package.sh

# This creates: media-pipeline-portable-1.0.0-YYYYMMDD_HHMMSS.tar.gz
# Copy this file anywhere and deploy
```

### Option 3: Direct Installation
```bash
# For online systems
chmod +x install_self_contained.sh
./install_self_contained.sh

# For offline systems
chmod +x install_offline.sh
./install_offline.sh
```

## 📦 **Package Contents**

### Core Files
- **Source Code**: All Python scripts and modules
- **Configuration**: YAML configs and templates
- **Web UI**: HTML templates and Flask application
- **Database**: SQLite database with schema

### Installation Scripts
- **`deploy_anywhere.sh`** - Universal deployment script
- **`install_self_contained.sh`** - Online installation
- **`install_offline.sh`** - Offline installation
- **`create_portable_package.sh`** - Package creation

### Dependencies
- **`offline_deps/`** - Python packages for offline installation
- **`system_packages/`** - System packages download scripts
- **`requirements.txt`** - Python dependencies list

### Documentation
- **`README_PORTABLE.md`** - This file
- **`DEPLOYMENT_GUIDE.md`** - Detailed deployment guide
- **`HEADLESS_DEVELOPMENT_GUIDE.md`** - Development setup

## 🔧 **Installation Modes**

### 1. Online Mode (Internet Available)
- Downloads packages from repositories
- Installs latest versions
- Includes Syncthing and all dependencies
- **Use when**: You have internet access

### 2. Offline Mode (No Internet)
- Uses pre-downloaded packages
- Installs from local files
- Completely self-contained
- **Use when**: No internet access or air-gapped systems

### 3. Auto Mode (Recommended)
- Automatically detects internet availability
- Chooses appropriate installation method
- Falls back gracefully
- **Use when**: You want the script to decide

## 🎛️ **Configuration**

### Environment Variables
Edit `/opt/media-pipeline/.env`:
```bash
# iCloud Credentials
ICLOUD_USERNAME=your_email@icloud.com
ICLOUD_PASSWORD=your_password

# Syncthing Configuration
SYNCTHING_API_KEY=your_api_key

# Telegram Bot (Optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### Configuration File
Edit `/etc/media-pipeline/config.yaml` for advanced settings:
- Database configuration
- Directory paths
- Compression settings
- Logging configuration

## 🌐 **Access Points**

After installation, access your services at:

- **Web UI**: `http://your-container-ip:8080`
- **Syncthing**: `http://your-container-ip:8384`
- **Logs**: `/var/log/media-pipeline/`

## 🔄 **Services**

The installation creates these systemd services:

- **`media-pipeline.service`** - Main processing service
- **`media-pipeline-web.service`** - Web UI service
- **`syncthing@media-pipeline.service`** - File synchronization
- **`media-pipeline-daily.timer`** - Scheduled execution

## 📋 **Deployment Scenarios**

### Scenario 1: Fresh LXC Container
```bash
# 1. Copy project to container
scp -r media-storage/ root@new-container:/root/

# 2. Deploy
ssh root@new-container
cd media-storage/
./deploy_anywhere.sh

# 3. Configure and start
nano /opt/media-pipeline/.env
/opt/media-pipeline/complete_setup.sh
```

### Scenario 2: Air-Gapped System
```bash
# 1. Create portable package (on internet-connected system)
./create_portable_package.sh

# 2. Transfer package to air-gapped system
scp media-pipeline-portable-*.tar.gz root@air-gapped-system:/root/

# 3. Deploy offline
ssh root@air-gapped-system
tar -xzf media-pipeline-portable-*.tar.gz
cd media-pipeline-portable-*/
./install_offline.sh
```

### Scenario 3: Multiple Deployments
```bash
# 1. Create package once
./create_portable_package.sh

# 2. Deploy on multiple containers
for container in container1 container2 container3; do
    scp media-pipeline-portable-*.tar.gz root@$container:/root/
    ssh root@$container "tar -xzf media-pipeline-portable-*.tar.gz && cd media-pipeline-portable-*/ && ./install_offline.sh"
done
```

## 🛠️ **Troubleshooting**

### Check Service Status
```bash
systemctl status media-pipeline
systemctl status media-pipeline-web
systemctl status syncthing@media-pipeline
```

### View Logs
```bash
journalctl -u media-pipeline -f
journalctl -u media-pipeline-web -f
tail -f /var/log/media-pipeline/media_pipeline.log
```

### Restart Services
```bash
systemctl restart media-pipeline
systemctl restart media-pipeline-web
systemctl restart syncthing@media-pipeline
```

### Reconfigure
```bash
nano /opt/media-pipeline/.env
nano /etc/media-pipeline/config.yaml
systemctl restart media-pipeline
```

## 🔒 **Security Features**

- **User Isolation**: Runs as dedicated `media-pipeline` user
- **Systemd Hardening**: Protected system directories
- **No Root Access**: Services don't run as root
- **Secure Permissions**: Proper file ownership and permissions
- **Environment Variables**: Sensitive data in environment files

## 📊 **Monitoring**

### Built-in Monitoring
- **Systemd Journal**: Service logs and status
- **File Logging**: Rotating log files
- **Web UI**: Real-time status and statistics
- **Health Checks**: Automatic service monitoring

### External Monitoring
- **Telegram Notifications**: Status updates and alerts
- **Log Aggregation**: Centralized logging support
- **Metrics Export**: Prometheus-compatible metrics

## 🎯 **Use Cases**

### Personal Media Backup
- Automatically sync photos from iCloud
- Compress and organize media files
- Backup to NAS or external storage
- Web interface for management

### Small Business
- Centralized media management
- Automated backup processes
- Team collaboration via web UI
- Scheduled maintenance tasks

### Development/Testing
- Isolated environment for testing
- Reproducible deployments
- Version control integration
- CI/CD pipeline support

## 🚀 **Advanced Features**

### Customization
- **Plugin System**: Extensible architecture
- **Custom Scripts**: Add your own processing logic
- **API Integration**: RESTful API for external tools
- **Webhook Support**: Event-driven processing

### Scaling
- **Multi-Container**: Deploy across multiple containers
- **Load Balancing**: Distribute processing load
- **Database Clustering**: High availability setup
- **Storage Federation**: Multiple storage backends

## 📚 **Documentation**

- **`README_PORTABLE.md`** - This overview
- **`DEPLOYMENT_GUIDE.md`** - Detailed deployment instructions
- **`HEADLESS_DEVELOPMENT_GUIDE.md`** - Development setup
- **`SETUP_GUIDE.md`** - Original setup guide
- **`RECOMMENDATIONS.md`** - Best practices and recommendations

## 🤝 **Support**

This is a **completely self-contained solution** that doesn't depend on:
- ❌ External repositories
- ❌ Third-party services
- ❌ Internet connectivity
- ❌ Specific hosting providers

**Everything you need is included in this package!**

## 🎉 **Success!**

Your media pipeline is now:
- ✅ **Portable** - Deploy anywhere
- ✅ **Self-Contained** - No external dependencies
- ✅ **Future-Proof** - Won't break if external services change
- ✅ **Production Ready** - Full monitoring and logging
- ✅ **Easy to Use** - Simple deployment and management

**Enjoy your completely portable media pipeline!** 🚀
