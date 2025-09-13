#!/bin/bash

# Create Portable Media Pipeline Package
# This script creates a completely self-contained package that can be deployed anywhere

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Creating Portable Media Pipeline Package ===${NC}"

# Configuration
PACKAGE_NAME="media-pipeline-portable"
PACKAGE_VERSION="1.0.0"
PACKAGE_DIR="${PACKAGE_NAME}-${PACKAGE_VERSION}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create package directory
echo -e "${GREEN}Creating package directory: $PACKAGE_DIR${NC}"
rm -rf "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR"

# Copy all project files
echo -e "${GREEN}Copying project files...${NC}"
cp -r common "$PACKAGE_DIR/"
cp -r templates "$PACKAGE_DIR/"
cp *.py "$PACKAGE_DIR/"
cp *.yaml "$PACKAGE_DIR/"
cp *.txt "$PACKAGE_DIR/"
cp *.md "$PACKAGE_DIR/"
cp *.sh "$PACKAGE_DIR/"

# Create offline dependencies directory
echo -e "${GREEN}Creating offline dependencies directory...${NC}"
mkdir -p "$PACKAGE_DIR/offline_deps"

# Download Python packages for offline installation
echo -e "${GREEN}Downloading Python packages for offline installation...${NC}"
cd "$PACKAGE_DIR/offline_deps"

# Create a temporary requirements file with exact versions
cat > requirements_offline.txt << 'EOF'
# Media Pipeline Dependencies - Offline Installation
# Core dependencies
PyYAML==6.0.1
Pillow==10.0.1
python-dateutil==2.8.2
requests==2.31.0

# iCloud integration
pyicloud==0.10.3

# Web UI dependencies
Flask==2.3.3
Flask-CORS==4.0.0
Flask-SocketIO==5.3.6
python-socketio==5.8.0
eventlet==0.33.3

# System monitoring
psutil==5.9.6

# Telegram integration
python-telegram-bot==20.7

# Enhanced logging
colorlog==6.7.0

# Scheduling
schedule==1.2.0

# Additional dependencies
Werkzeug==2.3.7
Jinja2==3.1.2
MarkupSafe==2.1.3
itsdangerous==2.1.2
click==8.1.7
blinker==1.6.3
six==1.16.0
certifi==2023.7.22
charset-normalizer==3.3.2
idna==3.4
urllib3==2.0.7
python-engineio==4.7.1
dnspython==2.4.2
greenlet==2.0.2
typing-extensions==4.8.0
h11==0.14.0
sniffio==1.3.0
anyio==3.7.1
trio==0.22.2
trio-websocket==0.10.4
wsproto==1.2.0
cryptography==41.0.7
cffi==1.16.0
pycparser==2.21
EOF

# Download packages
echo -e "${GREEN}Downloading Python packages...${NC}"
pip download -r requirements_offline.txt --dest . --no-deps

# Download dependencies for each package
echo -e "${GREEN}Downloading package dependencies...${NC}"
pip download -r requirements_offline.txt --dest . --deps

cd ../..

# Create system packages directory
echo -e "${GREEN}Creating system packages directory...${NC}"
mkdir -p "$PACKAGE_DIR/system_packages"

# Create system packages download script
cat > "$PACKAGE_DIR/system_packages/download_system_packages.sh" << 'EOF'
#!/bin/bash

# Download system packages for offline installation
# Run this on a system with internet access

set -e

echo "Downloading system packages for offline installation..."

# Create download directory
mkdir -p downloaded_packages

# Download essential packages
apt-get update
apt-get download \
    curl \
    wget \
    git \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    build-essential \
    python3-dev \
    python3-pip \
    python3-venv \
    python3-setuptools \
    ffmpeg \
    sqlite3 \
    nginx \
    supervisor \
    systemd \
    cron \
    rsync \
    htop \
    nano \
    vim \
    python3.11 \
    python3.11-dev \
    python3.11-venv

# Download Syncthing
wget -O syncthing-release-key.gpg https://syncthing.net/release-key.txt
gpg --dearmor -o syncthing-archive-keyring.gpg syncthing-release-key.gpg

echo "System packages downloaded to downloaded_packages/"
echo "Copy this directory to your offline system for installation."
EOF

chmod +x "$PACKAGE_DIR/system_packages/download_system_packages.sh"

# Create offline installation script
cat > "$PACKAGE_DIR/install_offline.sh" << 'EOF'
#!/bin/bash

# Offline Media Pipeline Installation Script
# This script installs the media pipeline without requiring internet access

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Offline Media Pipeline Installation ===${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}This script must be run as root${NC}"
    echo "Please run: sudo $0"
    exit 1
fi

# Configuration variables
PYTHON_VERSION="3.11"
PROJECT_DIR="/opt/media-pipeline"
SERVICE_USER="media-pipeline"
LOG_DIR="/var/log/media-pipeline"
CONFIG_DIR="/etc/media-pipeline"
WEB_PORT="8081"
SYNCTHING_PORT="8384"

# Check prerequisites
echo -e "${GREEN}Checking prerequisites...${NC}"
if ! command -v systemctl &> /dev/null; then
    echo -e "${RED}systemd is required but not found.${NC}"
    exit 1
fi

# Install system packages from local files
echo -e "${GREEN}Installing system packages from local files...${NC}"
if [ -d "system_packages/downloaded_packages" ]; then
    cd system_packages/downloaded_packages
    dpkg -i *.deb || apt-get install -f -y
    cd ../..
else
    echo -e "${YELLOW}No offline system packages found. Installing from repositories...${NC}"
    apt update
    apt install -y \
        curl \
        wget \
        git \
        unzip \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release \
        build-essential \
        python3-dev \
        python3-pip \
        python3-venv \
        python3-setuptools \
        ffmpeg \
        sqlite3 \
        nginx \
        supervisor \
        systemd \
        cron \
        rsync \
        htop \
        nano \
        vim
fi

# Create service user
echo -e "${GREEN}Creating service user: $SERVICE_USER${NC}"
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd -r -s /bin/bash -d "$PROJECT_DIR" -m "$SERVICE_USER"
fi

# Create directories
echo -e "${GREEN}Creating project directories...${NC}"
mkdir -p "$PROJECT_DIR"
mkdir -p "$LOG_DIR"
mkdir -p "$CONFIG_DIR"
chown "$SERVICE_USER:$SERVICE_USER" "$CONFIG_DIR"
chmod 755 "$CONFIG_DIR"
mkdir -p "/mnt/wd_all_pictures/incoming"
mkdir -p "/mnt/wd_all_pictures/backup"
mkdir -p "/mnt/wd_all_pictures/compress"
mkdir -p "/mnt/wd_all_pictures/delete_pending"
mkdir -p "/mnt/wd_all_pictures/processed"

# Set permissions
chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR"
chown -R "$SERVICE_USER:$SERVICE_USER" "$LOG_DIR"
chown -R "$SERVICE_USER:$SERVICE_USER" "/mnt/wd_all_pictures"
chmod 755 "$PROJECT_DIR"
chmod 755 "$LOG_DIR"

# Copy project files
echo -e "${GREEN}Copying project files...${NC}"
cp -r . "$PROJECT_DIR/"
chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR"

# Create Python virtual environment
echo -e "${GREEN}Setting up Python virtual environment...${NC}"
sudo -u "$SERVICE_USER" python3.11 -m venv "$PROJECT_DIR/venv"
sudo -u "$SERVICE_USER" "$PROJECT_DIR/venv/bin/pip" install --upgrade pip

# Install Python packages from offline files
echo -e "${GREEN}Installing Python packages from offline files...${NC}"
if [ -d "offline_deps" ]; then
    sudo -u "$SERVICE_USER" "$PROJECT_DIR/venv/bin/pip" install --no-index --find-links offline_deps -r requirements_offline.txt
else
    echo -e "${YELLOW}No offline Python packages found. Installing from PyPI...${NC}"
    sudo -u "$SERVICE_USER" "$PROJECT_DIR/venv/bin/pip" install -r requirements.txt
fi

# Install Syncthing (if not already installed)
echo -e "${GREEN}Installing Syncthing...${NC}"
if ! command -v syncthing &> /dev/null; then
    if [ -f "system_packages/syncthing-archive-keyring.gpg" ]; then
        cp system_packages/syncthing-archive-keyring.gpg /etc/apt/keyrings/
        echo "deb [signed-by=/etc/apt/keyrings/syncthing-archive-keyring.gpg] https://apt.syncthing.net/ syncthing stable" | tee /etc/apt/sources.list.d/syncthing.list
        apt update
        apt install -y syncthing
    else
        echo -e "${YELLOW}Syncthing keyring not found. Please install Syncthing manually.${NC}"
    fi
fi

# Create systemd services (same as original install.sh)
echo -e "${GREEN}Creating systemd services...${NC}"

# Syncthing service
tee /etc/systemd/system/syncthing@$SERVICE_USER.service > /dev/null <<EOF
[Unit]
Description=Syncthing - Open Source Continuous File Synchronization for %i
Documentation=man:syncthing(1)
After=network.target
Wants=syncthing-inotify@%i.service

[Service]
User=%i
Group=%i
Type=simple
ExecStart=/usr/bin/syncthing -no-browser -no-restart -logflags=0
Restart=on-failure
RestartSec=5
SuccessExitStatus=3 4
RestartForceExitStatus=3 4

# Hardening
ProtectSystem=full
ProtectHome=read-only
PrivateTmp=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
EOF

# Media Pipeline service
tee /etc/systemd/system/media-pipeline.service > /dev/null <<EOF
[Unit]
Description=Media Pipeline Service
After=network.target syncthing@$SERVICE_USER.service
Wants=syncthing@$SERVICE_USER.service

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/pipeline_orchestrator.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$PROJECT_DIR $LOG_DIR /mnt/wd_all_pictures

[Install]
WantedBy=multi-user.target
EOF

# Web UI service
tee /etc/systemd/system/media-pipeline-web.service > /dev/null <<EOF
[Unit]
Description=Media Pipeline Web UI
After=network.target media-pipeline.service
Wants=media-pipeline.service

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
Environment=FLASK_APP=web_ui.py
Environment=FLASK_ENV=production
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/web_ui.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$PROJECT_DIR $LOG_DIR

[Install]
WantedBy=multi-user.target
EOF

# Create default configuration
echo -e "${GREEN}Creating default configuration...${NC}"
tee "$CONFIG_DIR/config.yaml" > /dev/null <<EOF
# Media Pipeline Configuration
database:
  file_path: "$PROJECT_DIR/media.db"
  backup_enabled: true
  backup_interval_hours: 24

icloud:
  username: ""  # Set via environment variable ICLOUD_USERNAME
  password: ""  # Set via environment variable ICLOUD_PASSWORD
  directory: "/mnt/wd_all_pictures/incoming"
  days: 0
  recent: 0
  auto_delete: false
  album_name: "DeletePending"

syncthing:
  api_key: ""  # Set via environment variable SYNCTHING_API_KEY
  base_url: "http://127.0.0.1:$SYNCTHING_PORT/rest"
  folder_id: "default"
  pixel_local_folder: "/storage/emulated/0/DCIM/Syncthing"
  delete_local_pixel: true
  timeout_seconds: 30
  max_retries: 3

nas:
  mount_path: "/mnt/wd_all_pictures"
  sync_enabled: true
  delete_after_sync: false

compression:
  enabled: true
  light_quality: 85
  medium_quality: 75
  heavy_quality: 65
  light_crf: 26
  medium_crf: 28
  heavy_crf: 30

logging:
  level: "INFO"
  log_dir: "$LOG_DIR"
  log_file: "media_pipeline.log"
  max_file_size_mb: 10
  backup_count: 5
  format: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

directories:
  incoming: "/mnt/wd_all_pictures/incoming"
  backup: "/mnt/wd_all_pictures/backup"
  compress: "/mnt/wd_all_pictures/compress"
  delete_pending: "/mnt/wd_all_pictures/delete_pending"
  processed: "/mnt/wd_all_pictures/processed"

telegram:
  bot_token: ""  # Set via environment variable TELEGRAM_BOT_TOKEN
  chat_id: ""    # Set via environment variable TELEGRAM_CHAT_ID
  enabled: true
  notify_on_completion: true
  notify_on_error: true
  notify_on_start: true

web_ui:
  host: "127.0.0.1"
  port: $WEB_PORT
  debug: false
  auto_reload: false
EOF

# Set proper ownership of config file
chown "$SERVICE_USER:$SERVICE_USER" "$CONFIG_DIR/config.yaml"
chmod 644 "$CONFIG_DIR/config.yaml"

# Create environment file template
echo -e "${GREEN}Creating environment file template...${NC}"
sudo -u "$SERVICE_USER" tee "$PROJECT_DIR/.env.template" > /dev/null <<EOF
# Media Pipeline Environment Variables
# Copy this file to .env and fill in your values

# iCloud Credentials
ICLOUD_USERNAME=your_icloud_email@example.com
ICLOUD_PASSWORD=your_icloud_password

# Syncthing Configuration
SYNCTHING_API_KEY=your_syncthing_api_key

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Database
DB_FILE=$PROJECT_DIR/media.db

# Logging
LOG_LEVEL=INFO
LOG_DIR=$LOG_DIR
EOF

# Set up environment file
if [ ! -f "$PROJECT_DIR/.env" ]; then
    sudo -u "$SERVICE_USER" cp "$PROJECT_DIR/.env.template" "$PROJECT_DIR/.env"
    echo -e "${YELLOW}Please edit $PROJECT_DIR/.env with your actual credentials${NC}"
fi

# Reload systemd and enable services
echo -e "${GREEN}Reloading systemd and enabling services...${NC}"
systemctl daemon-reload
systemctl enable syncthing@$SERVICE_USER
systemctl enable media-pipeline
systemctl enable media-pipeline-web
systemctl enable nginx

# Ensure log directory exists and has proper permissions
echo -e "${GREEN}Setting up log directory...${NC}"
mkdir -p "$LOG_DIR"
chown "$SERVICE_USER:$SERVICE_USER" "$LOG_DIR"
chmod 755 "$LOG_DIR"

# Initialize database
echo -e "${GREEN}Initializing database...${NC}"
sudo -u "$SERVICE_USER" "$PROJECT_DIR/venv/bin/python" "$PROJECT_DIR/test_pipeline.py"

# Create setup completion script
echo -e "${GREEN}Creating setup completion script...${NC}"
sudo -u "$SERVICE_USER" tee "$PROJECT_DIR/complete_setup.sh" > /dev/null <<EOF
#!/bin/bash
# Complete setup script - run this after configuring credentials

echo "Completing Media Pipeline setup..."

# Load environment variables
if [ -f "$PROJECT_DIR/.env" ]; then
    export \$(cat "$PROJECT_DIR/.env" | grep -v '^#' | xargs)
fi

# Start all services
systemctl start syncthing@$SERVICE_USER
sleep 5  # Wait for Syncthing to start
systemctl start nginx
systemctl start media-pipeline
systemctl start media-pipeline-web

# Check service status
echo "Service Status:"
systemctl status syncthing@$SERVICE_USER --no-pager -l
systemctl status media-pipeline --no-pager -l
systemctl status media-pipeline-web --no-pager -l
systemctl status nginx --no-pager -l

echo "Setup complete!"
echo "Web UI available at: http://\$(hostname -I | awk '{print \$1}')"
echo "Syncthing Web UI available at: http://\$(hostname -I | awk '{print \$1}'):$SYNCTHING_PORT"
EOF

chmod +x "$PROJECT_DIR/complete_setup.sh"

# Final status
echo -e "${GREEN}=== Offline Installation Completed Successfully! ===${NC}"
echo -e "${GREEN}Next steps:${NC}"
echo -e "${GREEN}1. Edit $PROJECT_DIR/.env with your credentials${NC}"
echo -e "${GREEN}2. Run: $PROJECT_DIR/complete_setup.sh${NC}"
echo -e "${GREEN}3. Access Web UI at: http://\$(hostname -I | awk '{print \$1}')${NC}"
echo -e "${GREEN}4. Access Syncthing at: http://\$(hostname -I | awk '{print \$1}'):$SYNCTHING_PORT${NC}"
EOF

chmod +x "$PACKAGE_DIR/install_offline.sh"

# Create deployment guide
cat > "$PACKAGE_DIR/DEPLOYMENT_GUIDE.md" << 'EOF'
# Media Pipeline - Portable Deployment Guide

## Overview
This is a completely self-contained media pipeline package that can be deployed on any Ubuntu LXC container without requiring internet access.

## Package Contents
- **Source Code**: All Python scripts and configuration files
- **Offline Dependencies**: Python packages downloaded for offline installation
- **System Packages**: Scripts to download system packages for offline installation
- **Installation Scripts**: Automated installation without internet dependency

## Quick Deployment

### 1. Copy Package to Target System
```bash
# Copy the entire package directory to your LXC container
scp -r media-pipeline-portable-1.0.0/ root@your-container-ip:/root/
```

### 2. Run Offline Installation
```bash
# SSH into your container
ssh root@your-container-ip

# Navigate to package directory
cd media-pipeline-portable-1.0.0/

# Run offline installation
chmod +x install_offline.sh
./install_offline.sh
```

### 3. Configure and Start
```bash
# Edit configuration
nano /opt/media-pipeline/.env

# Complete setup
/opt/media-pipeline/complete_setup.sh
```

## Preparing Offline Dependencies (Optional)

If you want to prepare system packages for completely offline installation:

### On a system with internet access:
```bash
cd system_packages/
chmod +x download_system_packages.sh
./download_system_packages.sh
```

This will download all required system packages to the `downloaded_packages/` directory.

## Features
- ✅ **Completely Offline**: No internet required for installation
- ✅ **Self-Contained**: All dependencies included
- ✅ **Portable**: Deploy on any Ubuntu LXC container
- ✅ **Automated**: One-command installation
- ✅ **Production Ready**: Systemd services, logging, monitoring
- ✅ **Secure**: Proper user isolation and permissions

## Services Installed
- **Media Pipeline**: Main processing service
- **Web UI**: Browser-based interface
- **Syncthing**: File synchronization
- **Nginx**: Web server and reverse proxy

## Access Points
- **Web UI**: http://container-ip:8080
- **Syncthing**: http://container-ip:8384
- **Logs**: /var/log/media-pipeline/

## Configuration
Edit `/opt/media-pipeline/.env` with your credentials:
- iCloud username/password
- Syncthing API key
- Telegram bot token/chat ID

## Troubleshooting
- Check service status: `systemctl status media-pipeline`
- View logs: `journalctl -u media-pipeline -f`
- Restart services: `systemctl restart media-pipeline`

## Support
This package is completely self-contained and doesn't depend on external repositories or services.
EOF

# Create package archive
echo -e "${GREEN}Creating package archive...${NC}"
tar -czf "${PACKAGE_NAME}-${PACKAGE_VERSION}-${TIMESTAMP}.tar.gz" "$PACKAGE_DIR"

# Create checksums
echo -e "${GREEN}Creating checksums...${NC}"
sha256sum "${PACKAGE_NAME}-${PACKAGE_VERSION}-${TIMESTAMP}.tar.gz" > "${PACKAGE_NAME}-${PACKAGE_VERSION}-${TIMESTAMP}.tar.gz.sha256"
md5sum "${PACKAGE_NAME}-${PACKAGE_VERSION}-${TIMESTAMP}.tar.gz" > "${PACKAGE_NAME}-${PACKAGE_VERSION}-${TIMESTAMP}.tar.gz.md5"

# Display package information
echo -e "${GREEN}=== Package Created Successfully! ===${NC}"
echo -e "${GREEN}Package: ${PACKAGE_NAME}-${PACKAGE_VERSION}-${TIMESTAMP}.tar.gz${NC}"
echo -e "${GREEN}Size: $(du -h "${PACKAGE_NAME}-${PACKAGE_VERSION}-${TIMESTAMP}.tar.gz" | cut -f1)${NC}"
echo -e "${GREEN}Checksum: $(cat "${PACKAGE_NAME}-${PACKAGE_VERSION}-${TIMESTAMP}.tar.gz.sha256")${NC}"
echo ""
echo -e "${BLUE}Package Contents:${NC}"
echo -e "${GREEN}✅ Source code and configuration${NC}"
echo -e "${GREEN}✅ Offline Python dependencies${NC}"
echo -e "${GREEN}✅ System package download scripts${NC}"
echo -e "${GREEN}✅ Automated installation script${NC}"
echo -e "${GREEN}✅ Deployment documentation${NC}"
echo ""
echo -e "${BLUE}To deploy on any LXC container:${NC}"
echo -e "${YELLOW}1. Copy package to container${NC}"
echo -e "${YELLOW}2. Extract: tar -xzf ${PACKAGE_NAME}-${PACKAGE_VERSION}-${TIMESTAMP}.tar.gz${NC}"
echo -e "${YELLOW}3. Install: cd ${PACKAGE_DIR} && ./install_offline.sh${NC}"
echo -e "${YELLOW}4. Configure: edit /opt/media-pipeline/.env${NC}"
echo -e "${YELLOW}5. Start: /opt/media-pipeline/complete_setup.sh${NC}"
echo ""
echo -e "${GREEN}🎉 Your media pipeline is now completely portable and self-contained! 🎉${NC}"
