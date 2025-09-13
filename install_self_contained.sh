#!/bin/bash

# Self-Contained Media Pipeline Installation Script
# This script installs the media pipeline with minimal external dependencies

set -e

# Enhanced debugging and logging
DEBUG_MODE=${DEBUG_MODE:-false}
LOG_FILE="/tmp/install_$(date +%Y%m%d_%H%M%S).log"

# Function to log with timestamp
log_to_file() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Enhanced error handling
handle_error() {
    local exit_code=$?
    local line_number=$1
    error "Script failed at line $line_number with exit code $exit_code"
    error "Check log file: $LOG_FILE"
    error "Last 10 lines of log:"
    tail -10 "$LOG_FILE" | while read line; do
        echo "  $line"
    done
    exit $exit_code
}

# Set up error trap
trap 'handle_error $LINENO' ERR

# Log script start
log_to_file "=== Self-Contained Media Pipeline Installation Started ==="
log_to_file "Debug mode: $DEBUG_MODE"
log_to_file "Log file: $LOG_FILE"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Enhanced logging functions
log() {
    local message="[$(date +'%Y-%m-%d %H:%M:%S')] $1"
    echo -e "${GREEN}$message${NC}"
    log_to_file "LOG: $1"
}

warn() {
    local message="[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1"
    echo -e "${YELLOW}$message${NC}"
    log_to_file "WARN: $1"
}

error() {
    local message="[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1"
    echo -e "${RED}$message${NC}"
    log_to_file "ERROR: $1"
}

info() {
    local message="[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1"
    echo -e "${BLUE}$message${NC}"
    log_to_file "INFO: $1"
}

debug() {
    if [ "$DEBUG_MODE" = "true" ]; then
        local message="[$(date +'%Y-%m-%d %H:%M:%S')] DEBUG: $1"
        echo -e "${BLUE}$message${NC}"
        log_to_file "DEBUG: $1"
    fi
}

# Check if running as root and adjust sudo usage
if [[ $EUID -eq 0 ]]; then
   warn "Running as root - will use su for user switching"
   SUDO_CMD=""
   SU_CMD="su -s /bin/bash"
else
   SUDO_CMD="sudo"
   SU_CMD="sudo -u"
fi

# Configuration variables
PYTHON_VERSION="3.11"
PROJECT_DIR="/opt/media-pipeline"
SERVICE_USER="media-pipeline"
LOG_DIR="/var/log/media-pipeline"
CONFIG_DIR="/etc/media-pipeline"
WEB_PORT="8081"
SYNCTHING_PORT="8384"

log "Starting Self-Contained Media Pipeline Installation..."

# Log system information
info "System Information:"
info "  OS: $(lsb_release -d | cut -f2)"
info "  Kernel: $(uname -r)"
info "  Architecture: $(uname -m)"
info "  Memory: $(free -h | grep '^Mem:' | awk '{print $2}')"
info "  Disk: $(df -h / | tail -1 | awk '{print $4 " available"}')"
info "  User: $(whoami)"
info "  Working Directory: $(pwd)"

# Enhanced LXC/Container detection
info "Container Detection:"
if [ -f /.dockerenv ]; then
    info "  Environment: Docker container detected"
elif [ -f /run/.containerenv ]; then
    info "  Environment: Podman container detected"
elif grep -q "container=lxc" /proc/1/environ 2>/dev/null; then
    info "  Environment: LXC container detected"
elif [ -d /proc/vz ] && [ ! -d /proc/bc ]; then
    info "  Environment: OpenVZ container detected"
else
    info "  Environment: Regular system (not containerized)"
fi

# Check prerequisites
log "Checking prerequisites..."
if ! command -v systemctl &> /dev/null; then
    error "systemd is required but not found. This script is designed for systemd-based systems."
    exit 1
fi

if ! command -v python3.11 &> /dev/null && ! command -v python3 &> /dev/null; then
    error "Python 3 is required but not found."
    exit 1
fi

log "Prerequisites check passed."

# Update system packages (only if internet is available)
log "Checking internet connectivity..."
if ping -c 1 8.8.8.8 &> /dev/null; then
    info "Internet connection available - updating packages"
    debug "Running: $SUDO_CMD apt update"
    if ! $SUDO_CMD apt update; then
        error "Failed to update package lists"
        exit 1
    fi

    debug "Running: $SUDO_CMD apt upgrade -y"
    if ! $SUDO_CMD apt upgrade -y; then
        warn "Package upgrade failed, continuing with installation..."
    fi
else
    warn "No internet connection detected - skipping package updates"
    info "Proceeding with offline installation"
fi

# Install essential packages (with fallback for offline)
log "Installing essential packages..."
debug "Installing packages: curl wget git unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release build-essential python3-dev python3-pip python3-venv python3-setuptools ffmpeg sqlite3 nginx supervisor systemd cron rsync htop nano vim"

# Try to install packages, with graceful fallback
if ! $SUDO_CMD apt install -y \
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
    vim 2>/dev/null; then
    warn "Some packages failed to install - continuing with available packages"
    # Try to install core packages individually
    $SUDO_CMD apt install -y python3 python3-pip python3-venv sqlite3 nano vim || true
fi

log "Essential packages installation completed"

# Install Python 3.11 if not available (only if internet is available)
log "Setting up Python $PYTHON_VERSION..."
if ! command -v python3.11 &> /dev/null; then
    if ping -c 1 8.8.8.8 &> /dev/null; then
        info "Installing Python 3.11 from repository"
        $SUDO_CMD add-apt-repository ppa:deadsnakes/ppa -y
        $SUDO_CMD apt update
        $SUDO_CMD apt install -y python3.11 python3.11-venv python3.11-dev
    else
        warn "No internet connection - using system Python 3"
        PYTHON_VERSION="3"
    fi
fi

# Create service user
log "Creating service user: $SERVICE_USER"
if ! id "$SERVICE_USER" &>/dev/null; then
    $SUDO_CMD useradd -r -s /bin/bash -d "$PROJECT_DIR" -m "$SERVICE_USER"
fi

# Create directories
log "Creating project directories..."
$SUDO_CMD mkdir -p "$PROJECT_DIR"
$SUDO_CMD mkdir -p "$LOG_DIR"
$SUDO_CMD mkdir -p "$CONFIG_DIR"
$SUDO_CMD chown "$SERVICE_USER:$SERVICE_USER" "$CONFIG_DIR"
$SUDO_CMD chmod 755 "$CONFIG_DIR"
$SUDO_CMD mkdir -p "/mnt/wd_all_pictures/incoming"
$SUDO_CMD mkdir -p "/mnt/wd_all_pictures/backup"
$SUDO_CMD mkdir -p "/mnt/wd_all_pictures/compress"
$SUDO_CMD mkdir -p "/mnt/wd_all_pictures/delete_pending"
$SUDO_CMD mkdir -p "/mnt/wd_all_pictures/processed"

# Set permissions
$SUDO_CMD chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR"
$SUDO_CMD chown -R "$SERVICE_USER:$SERVICE_USER" "$LOG_DIR"
$SUDO_CMD chown -R "$SERVICE_USER:$SERVICE_USER" "/mnt/wd_all_pictures"
$SUDO_CMD chmod 755 "$PROJECT_DIR"
$SUDO_CMD chmod 755 "$LOG_DIR"

# Install Syncthing (only if internet is available)
log "Installing Syncthing..."
if ! command -v syncthing &> /dev/null; then
    if ping -c 1 8.8.8.8 &> /dev/null; then
        info "Installing Syncthing from repository"
        # Use modern GPG key installation method
        $SUDO_CMD mkdir -p /etc/apt/keyrings
        
        # Remove old keyring if it exists
        $SUDO_CMD rm -f /etc/apt/keyrings/syncthing-archive-keyring.gpg
        $SUDO_CMD rm -f /etc/apt/sources.list.d/syncthing.list
        
        # Add new keyring
        curl -s https://syncthing.net/release-key.txt | $SUDO_CMD gpg --dearmor -o /etc/apt/keyrings/syncthing-archive-keyring.gpg
        echo "deb [signed-by=/etc/apt/keyrings/syncthing-archive-keyring.gpg] https://apt.syncthing.net/ syncthing stable" | $SUDO_CMD tee /etc/apt/sources.list.d/syncthing.list
        
        # Update package lists
        $SUDO_CMD apt update
        
        # Install Syncthing
        $SUDO_CMD apt install -y syncthing
        log "Syncthing installed successfully"
    else
        warn "No internet connection - skipping Syncthing installation"
        info "You can install Syncthing manually later if needed"
    fi
else
    log "Syncthing is already installed"
fi

# Copy project files
log "Copying project files..."
$SUDO_CMD cp -r . "$PROJECT_DIR/"
$SUDO_CMD chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR"

# Create Python virtual environment
log "Setting up Python virtual environment..."
# Verify service user exists
if ! id "$SERVICE_USER" &>/dev/null; then
    error "Service user $SERVICE_USER does not exist. Cannot continue."
    exit 1
fi

# Use available Python version
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
else
    PYTHON_CMD="python3"
fi

$SU_CMD "$SERVICE_USER" -c "$PYTHON_CMD -m venv $PROJECT_DIR/venv"
$SU_CMD "$SERVICE_USER" -c "$PROJECT_DIR/venv/bin/pip install --upgrade pip"

# Install Python packages in virtual environment
log "Installing Python packages in virtual environment..."

# Install requirements from requirements.txt if it exists
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    log "Installing requirements from requirements.txt..."
    if ! $SU_CMD "$SERVICE_USER" -c "$PROJECT_DIR/venv/bin/pip install -r $PROJECT_DIR/requirements.txt"; then
        warn "Some Python packages failed to install - continuing with available packages"
        # Try to install core packages individually
        $SU_CMD "$SERVICE_USER" -c "$PROJECT_DIR/venv/bin/pip install PyYAML Pillow requests Flask" || true
    fi
fi

# Install icloudpd (not in requirements.txt) - only if internet is available
if ping -c 1 8.8.8.8 &> /dev/null; then
    log "Installing icloudpd..."
    $SU_CMD "$SERVICE_USER" -c "$PROJECT_DIR/venv/bin/pip install icloudpd" || warn "Failed to install icloudpd"
else
    warn "No internet connection - skipping icloudpd installation"
fi

# Create systemd service for Syncthing (only if Syncthing is installed)
if command -v syncthing &> /dev/null; then
    log "Creating Syncthing systemd service..."
    $SUDO_CMD tee /etc/systemd/system/syncthing@$SERVICE_USER.service > /dev/null <<EOF
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
fi

# Create systemd service for Media Pipeline
log "Creating Media Pipeline systemd service..."
$SUDO_CMD tee /etc/systemd/system/media-pipeline.service > /dev/null <<EOF
[Unit]
Description=Media Pipeline Service
After=network.target
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
$SUDO_CMD tee /etc/systemd/system/media-pipeline-web.service > /dev/null <<EOF
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

# Set up scheduled execution (cron or systemd timer)
log "Setting up scheduled execution..."

# Detect if we're in an LXC container
if [ -f /.dockerenv ] || [ -f /run/.containerenv ] || grep -q "container=lxc" /proc/1/environ 2>/dev/null || [ -d /proc/vz ] && [ ! -d /proc/bc ]; then
    warn "Detected LXC/container environment. Using systemd timer instead of cron."
    USE_SYSTEMD_TIMER=true
else
    USE_SYSTEMD_TIMER=false
fi

if [ "$USE_SYSTEMD_TIMER" = true ]; then
    # Use systemd timer for LXC containers
    log "Creating systemd timer for LXC container..."
    
    # Create a one-shot service for the pipeline
    $SUDO_CMD tee /etc/systemd/system/media-pipeline-run.service > /dev/null <<EOF
[Unit]
Description=Run Media Pipeline (One-shot)
After=network.target

[Service]
Type=oneshot
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/pipeline_orchestrator.py
StandardOutput=journal
StandardError=journal

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$PROJECT_DIR $LOG_DIR /mnt/wd_all_pictures
EOF

    # Create the timer
    $SUDO_CMD tee /etc/systemd/system/media-pipeline-daily.timer > /dev/null <<EOF
[Unit]
Description=Run Media Pipeline daily at 2 AM
Requires=media-pipeline-run.service

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
EOF

    $SUDO_CMD systemctl daemon-reload
    $SUDO_CMD systemctl enable media-pipeline-daily.timer
    log "Systemd timer created successfully for LXC container"
    
else
    # Use traditional cron for regular systems
    log "Setting up cron job for regular system..."
    
    # Ensure cron service is running
    $SUDO_CMD systemctl enable cron
    $SUDO_CMD systemctl start cron

    # Ensure cron directory has proper permissions
    $SUDO_CMD mkdir -p /var/spool/cron/crontabs
    $SUDO_CMD chown root:crontab /var/spool/cron/crontabs
    $SUDO_CMD chmod 755 /var/spool/cron/crontabs
    $SUDO_CMD chmod 1777 /var/spool/cron

    # Create cron job using a more robust method
    CRON_TEMP="/tmp/media_pipeline_cron_$$"
    echo "0 2 * * * cd $PROJECT_DIR && $PROJECT_DIR/venv/bin/python $PROJECT_DIR/pipeline_orchestrator.py >> $LOG_DIR/cron.log 2>&1" > "$CRON_TEMP"
    $SUDO_CMD chown "$SERVICE_USER:$SERVICE_USER" "$CRON_TEMP"
    $SU_CMD "$SERVICE_USER" -c "crontab $CRON_TEMP"
    $SUDO_CMD rm -f "$CRON_TEMP"

    # Verify cron job was created
    if $SU_CMD "$SERVICE_USER" -c "crontab -l" | grep -q "pipeline_orchestrator.py"; then
        log "Cron job created successfully"
    else
        warn "Failed to create cron job. Falling back to systemd timer..."
        USE_SYSTEMD_TIMER=true
    fi
fi

# Configure Nginx for Web UI (only if nginx is installed)
if command -v nginx &> /dev/null; then
    log "Configuring Nginx..."
    $SUDO_CMD tee /etc/nginx/sites-available/media-pipeline > /dev/null <<EOF
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

    $SUDO_CMD ln -sf /etc/nginx/sites-available/media-pipeline /etc/nginx/sites-enabled/
    $SUDO_CMD rm -f /etc/nginx/sites-enabled/default
else
    warn "Nginx not installed - skipping web server configuration"
fi

# Create default configuration
log "Creating default configuration..."
$SUDO_CMD tee "$CONFIG_DIR/config.yaml" > /dev/null <<EOF
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
$SUDO_CMD chown "$SERVICE_USER:$SERVICE_USER" "$CONFIG_DIR/config.yaml"
$SUDO_CMD chmod 644 "$CONFIG_DIR/config.yaml"

# Create environment file template
log "Creating environment file template..."
$SU_CMD "$SERVICE_USER" -c "tee $PROJECT_DIR/.env.template > /dev/null" <<EOF
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
    $SU_CMD "$SERVICE_USER" -c "cp $PROJECT_DIR/.env.template $PROJECT_DIR/.env"
    warn "Please edit $PROJECT_DIR/.env with your actual credentials"
fi

# Reload systemd and enable services
log "Reloading systemd and enabling services..."
$SUDO_CMD systemctl daemon-reload

# Enable services (only if they exist)
if command -v syncthing &> /dev/null; then
    $SUDO_CMD systemctl enable syncthing@$SERVICE_USER
fi
$SUDO_CMD systemctl enable media-pipeline
$SUDO_CMD systemctl enable media-pipeline-web
if command -v nginx &> /dev/null; then
    $SUDO_CMD systemctl enable nginx
fi

# Ensure log directory exists and has proper permissions
log "Setting up log directory..."
$SUDO_CMD mkdir -p "$LOG_DIR"
$SUDO_CMD chown "$SERVICE_USER:$SERVICE_USER" "$LOG_DIR"
$SUDO_CMD chmod 755 "$LOG_DIR"

# Initialize database
log "Initializing database..."
$SU_CMD "$SERVICE_USER" -c "$PROJECT_DIR/venv/bin/python $PROJECT_DIR/test_pipeline.py"

# Create setup completion script
log "Creating setup completion script..."
$SU_CMD "$SERVICE_USER" -c "tee $PROJECT_DIR/complete_setup.sh > /dev/null" <<EOF
#!/bin/bash
# Complete setup script - run this after configuring credentials

echo "Completing Media Pipeline setup..."

# Load environment variables
if [ -f "$PROJECT_DIR/.env" ]; then
    export \$(cat "$PROJECT_DIR/.env" | grep -v '^#' | xargs)
fi

# Start all services
if command -v syncthing &> /dev/null; then
    systemctl start syncthing@$SERVICE_USER
    sleep 5  # Wait for Syncthing to start
fi
if command -v nginx &> /dev/null; then
    systemctl start nginx
fi
systemctl start media-pipeline
systemctl start media-pipeline-web

# Start scheduled execution (timer or cron)
if systemctl list-timers | grep -q "media-pipeline-daily.timer"; then
    echo "Starting systemd timer..."
    systemctl start media-pipeline-daily.timer
else
    echo "Using cron for scheduled execution"
fi

# Check service status
echo "Service Status:"
if command -v syncthing &> /dev/null; then
    systemctl status syncthing@$SERVICE_USER --no-pager -l
fi
systemctl status media-pipeline --no-pager -l
systemctl status media-pipeline-web --no-pager -l
if command -v nginx &> /dev/null; then
    systemctl status nginx --no-pager -l
fi

# Check timer status if using systemd timer
if systemctl list-timers | grep -q "media-pipeline-daily.timer"; then
    echo "Timer Status:"
    systemctl status media-pipeline-daily.timer --no-pager -l
    systemctl list-timers | grep media-pipeline
fi

echo "Setup complete!"
echo "Web UI available at: http://\$(hostname -I | awk '{print \$1}')"
if command -v syncthing &> /dev/null; then
    echo "Syncthing Web UI available at: http://\$(hostname -I | awk '{print \$1}'):$SYNCTHING_PORT"
fi
EOF

$SUDO_CMD chmod +x "$PROJECT_DIR/complete_setup.sh"

# Final status check
log "Installation completed successfully!"
info "Next steps:"
info "1. Edit $PROJECT_DIR/.env with your credentials"
info "2. Run: $PROJECT_DIR/complete_setup.sh"
info "3. Access Web UI at: http://$(hostname -I | awk '{print $1}')"
if command -v syncthing &> /dev/null; then
    info "4. Access Syncthing at: http://$(hostname -I | awk '{print $1}'):$SYNCTHING_PORT"
fi

log "Self-contained installation script completed!"
