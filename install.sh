#!/bin/bash

# Media Pipeline Installation Script for Ubuntu LXC Container
# This script installs all dependencies and sets up the complete media pipeline

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   warning "This script should not be run as root for security reasons"
fi

# Configuration variables
PYTHON_VERSION="3.11"
PROJECT_DIR="/opt/media-pipeline"
SERVICE_USER="media-pipeline"
LOG_DIR="/var/log/media-pipeline"
CONFIG_DIR="/etc/media-pipeline"
WEB_PORT="8080"
SYNCTHING_PORT="8384"

log "Starting Media Pipeline Installation..."

# Update system packages
log "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install essential packages
log "Installing essential packages..."
sudo apt install -y \
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

# Install Python 3.11 if not available
log "Setting up Python $PYTHON_VERSION..."
if ! command -v python3.11 &> /dev/null; then
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt update
    sudo apt install -y python3.11 python3.11-venv python3.11-dev
fi

# Create service user
log "Creating service user: $SERVICE_USER"
if ! id "$SERVICE_USER" &>/dev/null; then
    sudo useradd -r -s /bin/bash -d "$PROJECT_DIR" -m "$SERVICE_USER"
    sudo usermod -aG sudo "$SERVICE_USER"
fi

# Create directories
log "Creating project directories..."
sudo mkdir -p "$PROJECT_DIR"
sudo mkdir -p "$LOG_DIR"
sudo mkdir -p "$CONFIG_DIR"
sudo mkdir -p "/mnt/wd_all_pictures/incoming"
sudo mkdir -p "/mnt/wd_all_pictures/backup"
sudo mkdir -p "/mnt/wd_all_pictures/compress"
sudo mkdir -p "/mnt/wd_all_pictures/delete_pending"
sudo mkdir -p "/mnt/wd_all_pictures/processed"

# Set permissions
sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR"
sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$LOG_DIR"
sudo chown -R "$SERVICE_USER:$SERVICE_USER" "/mnt/wd_all_pictures"
sudo chmod 755 "$PROJECT_DIR"
sudo chmod 755 "$LOG_DIR"

# Install Syncthing
log "Installing Syncthing..."
if ! command -v syncthing &> /dev/null; then
    curl -s https://syncthing.net/release-key.txt | sudo apt-key add -
    echo "deb https://apt.syncthing.net/ syncthing stable" | sudo tee /etc/apt/sources.list.d/syncthing.list
    sudo apt update
    sudo apt install -y syncthing
fi

# Install icloudpd
log "Installing icloudpd..."
sudo pip3 install icloudpd

# Install additional Python packages
log "Installing Python dependencies..."
sudo pip3 install \
    PyYAML \
    Pillow \
    python-dateutil \
    requests \
    pyicloud \
    flask \
    flask-cors \
    flask-socketio \
    python-socketio \
    eventlet \
    psutil \
    colorlog \
    schedule \
    python-telegram-bot

# Copy project files
log "Copying project files..."
sudo cp -r . "$PROJECT_DIR/"
sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR"

# Create Python virtual environment
log "Setting up Python virtual environment..."
sudo -u "$SERVICE_USER" python3.11 -m venv "$PROJECT_DIR/venv"
sudo -u "$SERVICE_USER" "$PROJECT_DIR/venv/bin/pip" install --upgrade pip
sudo -u "$SERVICE_USER" "$PROJECT_DIR/venv/bin/pip" install -r "$PROJECT_DIR/requirements.txt"

# Create systemd service for Syncthing
log "Creating Syncthing systemd service..."
sudo tee /etc/systemd/system/syncthing@$SERVICE_USER.service > /dev/null <<EOF
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

# Create systemd service for Media Pipeline
log "Creating Media Pipeline systemd service..."
sudo tee /etc/systemd/system/media-pipeline.service > /dev/null <<EOF
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

# Create systemd service for Web UI
log "Creating Web UI systemd service..."
sudo tee /etc/systemd/system/media-pipeline-web.service > /dev/null <<EOF
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

# Create cron job for regular pipeline execution
log "Setting up cron job..."
sudo -u "$SERVICE_USER" crontab -l 2>/dev/null | { cat; echo "0 2 * * * cd $PROJECT_DIR && $PROJECT_DIR/venv/bin/python $PROJECT_DIR/pipeline_orchestrator.py >> $LOG_DIR/cron.log 2>&1"; } | sudo -u "$SERVICE_USER" crontab -

# Configure Nginx for Web UI
log "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/media-pipeline > /dev/null <<EOF
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:$WEB_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /socket.io/ {
        proxy_pass http://127.0.0.1:$WEB_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/media-pipeline /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Create default configuration
log "Creating default configuration..."
sudo -u "$SERVICE_USER" tee "$CONFIG_DIR/config.yaml" > /dev/null <<EOF
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

# Create environment file template
log "Creating environment file template..."
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
    warn "Please edit $PROJECT_DIR/.env with your actual credentials"
fi

# Reload systemd and start services
log "Reloading systemd and starting services..."
sudo systemctl daemon-reload
sudo systemctl enable syncthing@$SERVICE_USER
sudo systemctl enable media-pipeline
sudo systemctl enable media-pipeline-web
sudo systemctl enable nginx

# Start services
sudo systemctl start syncthing@$SERVICE_USER
sleep 5  # Wait for Syncthing to start
sudo systemctl start nginx

# Initialize database
log "Initializing database..."
sudo -u "$SERVICE_USER" "$PROJECT_DIR/venv/bin/python" "$PROJECT_DIR/test_pipeline.py"

# Create setup completion script
log "Creating setup completion script..."
sudo -u "$SERVICE_USER" tee "$PROJECT_DIR/complete_setup.sh" > /dev/null <<EOF
#!/bin/bash
# Complete setup script - run this after configuring credentials

echo "Completing Media Pipeline setup..."

# Load environment variables
if [ -f "$PROJECT_DIR/.env" ]; then
    export \$(cat "$PROJECT_DIR/.env" | grep -v '^#' | xargs)
fi

# Start all services
sudo systemctl start media-pipeline
sudo systemctl start media-pipeline-web

# Check service status
echo "Service Status:"
sudo systemctl status syncthing@$SERVICE_USER --no-pager -l
sudo systemctl status media-pipeline --no-pager -l
sudo systemctl status media-pipeline-web --no-pager -l
sudo systemctl status nginx --no-pager -l

echo "Setup complete!"
echo "Web UI available at: http://$(hostname -I | awk '{print $1}')"
echo "Syncthing Web UI available at: http://$(hostname -I | awk '{print $1}'):$SYNCTHING_PORT"
EOF

sudo chmod +x "$PROJECT_DIR/complete_setup.sh"

# Final status check
log "Installation completed successfully!"
info "Next steps:"
info "1. Edit $PROJECT_DIR/.env with your credentials"
info "2. Run: sudo -u $SERVICE_USER $PROJECT_DIR/complete_setup.sh"
info "3. Access Web UI at: http://$(hostname -I | awk '{print $1}')"
info "4. Access Syncthing at: http://$(hostname -I | awk '{print $1}'):$SYNCTHING_PORT"

log "Installation script completed!"
