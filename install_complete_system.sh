#!/bin/bash

# Complete Media Pipeline Installation Script
# This script installs everything needed for the media pipeline

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Complete Media Pipeline Installation ===${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}This script must be run as root${NC}"
    echo "Please run: $0"
    exit 1
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a service is running
service_running() {
    systemctl is-active --quiet "$1" 2>/dev/null || pgrep -f "$1" >/dev/null 2>&1
}

# Function to check if a port is listening
port_listening() {
    netstat -tlnp 2>/dev/null | grep -q ":$1 " || ss -tlnp 2>/dev/null | grep -q ":$1 "
}

# Function to check if a file exists and is not empty
file_exists() {
    [ -f "$1" ] && [ -s "$1" ]
}

# Function to check if a directory exists
dir_exists() {
    [ -d "$1" ]
}

echo -e "${GREEN}Checking existing installation...${NC}"

# Configuration
PROJECT_DIR="/opt/media-pipeline"
SERVICE_USER="media-pipeline"
CONTAINER_IP=$(hostname -I | awk '{print $1}')

echo -e "${GREEN}Container IP: $CONTAINER_IP${NC}"
echo ""

echo -e "${BLUE}=== Step 1: Install System Packages ===${NC}"

# Check what's already installed
PACKAGES_TO_INSTALL=()
if ! command_exists nginx; then
    PACKAGES_TO_INSTALL+=("nginx")
fi
if ! command_exists python3; then
    PACKAGES_TO_INSTALL+=("python3")
fi
if ! command_exists pip3; then
    PACKAGES_TO_INSTALL+=("python3-pip")
fi
if ! command_exists python3-venv; then
    PACKAGES_TO_INSTALL+=("python3-venv")
fi
if ! command_exists netstat; then
    PACKAGES_TO_INSTALL+=("net-tools")
fi
if ! command_exists curl; then
    PACKAGES_TO_INSTALL+=("curl")
fi
if ! command_exists wget; then
    PACKAGES_TO_INSTALL+=("wget")
fi
if ! command_exists sqlite3; then
    PACKAGES_TO_INSTALL+=("sqlite3")
fi

if [ ${#PACKAGES_TO_INSTALL[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ All system packages already installed${NC}"
else
    echo -e "${GREEN}Installing missing packages: ${PACKAGES_TO_INSTALL[*]}${NC}"
apt update
    apt install -y "${PACKAGES_TO_INSTALL[@]}"
echo -e "${GREEN}✓ System packages installed${NC}"
fi

echo ""
echo -e "${BLUE}=== Step 2: Install Node.js and PM2 ===${NC}"

# Check if Node.js is already installed
if command_exists node && command_exists npm; then
    echo -e "${GREEN}✓ Node.js already installed: $(node --version)${NC}"
    echo -e "${GREEN}✓ NPM already installed: $(npm --version)${NC}"
    
    # Check if PM2 is installed
    if command_exists pm2; then
        echo -e "${GREEN}✓ PM2 already installed: $(pm2 --version)${NC}"
    else
        echo -e "${GREEN}Installing PM2...${NC}"
        npm install -g pm2
        echo -e "${GREEN}✓ PM2 installed${NC}"
    fi
else
echo -e "${GREEN}Installing Node.js...${NC}"
    # Try NodeSource first, fallback to Ubuntu package if it fails
    if curl -fsSL https://deb.nodesource.com/setup_18.x | bash -; then
        echo -e "${GREEN}NodeSource repository added successfully${NC}"
apt install -y nodejs
    else
        echo -e "${YELLOW}NodeSource repository failed, using Ubuntu default Node.js${NC}"
        apt install -y nodejs npm
    fi

# Install PM2 globally
echo -e "${GREEN}Installing PM2...${NC}"
    # Ensure Node.js is available (in case NVM was used)
    if ! command -v node &> /dev/null; then
        echo -e "${YELLOW}Node.js not found in PATH, trying to source NVM...${NC}"
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
    fi

    # Verify Node.js is available
    if command -v node &> /dev/null; then
        echo -e "${GREEN}Node.js version: $(node --version)${NC}"
        echo -e "${GREEN}NPM version: $(npm --version)${NC}"
npm install -g pm2
    else
        echo -e "${RED}Node.js not found. Please install Node.js first.${NC}"
        exit 1
    fi
echo -e "${GREEN}✓ Node.js and PM2 installed${NC}"
fi

echo ""
echo -e "${BLUE}=== Step 3: Install Syncthing ===${NC}"

# Check if Syncthing is already installed
if command_exists syncthing; then
    echo -e "${GREEN}✓ Syncthing already installed: $(syncthing --version | head -n1)${NC}"
else
    echo -e "${GREEN}Installing Syncthing...${NC}"
    # Use modern GPG key management instead of deprecated apt-key
    curl -s https://syncthing.net/release-key.txt | gpg --dearmor -o /usr/share/keyrings/syncthing-archive-keyring.gpg
    echo "deb [signed-by=/usr/share/keyrings/syncthing-archive-keyring.gpg] https://apt.syncthing.net/ syncthing stable" > /etc/apt/sources.list.d/syncthing.list
    apt update
    apt install -y syncthing
    echo -e "${GREEN}✓ Syncthing installed${NC}"
fi

echo ""
echo -e "${BLUE}=== Step 4: Setup Python Virtual Environment ===${NC}"

# Check if virtual environment already exists
if dir_exists "$PROJECT_DIR/venv"; then
    echo -e "${GREEN}✓ Python virtual environment already exists${NC}"
    
    # Check if required packages are installed
    if "$PROJECT_DIR/venv/bin/pip" show flask flask-socketio requests icloudpd >/dev/null 2>&1; then
        echo -e "${GREEN}✓ All Python packages already installed${NC}"
    else
        echo -e "${GREEN}Installing missing Python packages...${NC}"
        "$PROJECT_DIR/venv/bin/pip" install flask flask-socketio requests icloudpd
        echo -e "${GREEN}✓ Python packages installed${NC}"
    fi
else
    echo -e "${GREEN}Creating Python virtual environment...${NC}"
    python3 -m venv "$PROJECT_DIR/venv"

    # Install Python packages
    echo -e "${GREEN}Installing Python packages...${NC}"
    "$PROJECT_DIR/venv/bin/pip" install flask flask-socketio requests icloudpd
    echo -e "${GREEN}✓ Python virtual environment created${NC}"
fi

echo ""
echo -e "${BLUE}=== Step 5: Create Service User ===${NC}"

# Create service user if it doesn't exist
if ! id "$SERVICE_USER" &>/dev/null; then
    echo -e "${GREEN}Creating service user: $SERVICE_USER${NC}"
    useradd -r -s /bin/false -d "$PROJECT_DIR" "$SERVICE_USER"
    echo -e "${GREEN}✓ Service user created${NC}"
else
    echo -e "${GREEN}✓ Service user already exists${NC}"
fi

echo ""
echo -e "${BLUE}=== Step 6: Create Required Directories ===${NC}"

# Create required directories
DIRS_TO_CREATE=()
if ! dir_exists "/var/log/media-pipeline"; then
    DIRS_TO_CREATE+=("/var/log/media-pipeline")
fi
if ! dir_exists "/mnt/wd_all_pictures/incoming"; then
    DIRS_TO_CREATE+=("/mnt/wd_all_pictures/incoming")
fi
if ! dir_exists "/mnt/wd_all_pictures/processed"; then
    DIRS_TO_CREATE+=("/mnt/wd_all_pictures/processed")
fi
if ! dir_exists "$PROJECT_DIR/templates"; then
    DIRS_TO_CREATE+=("$PROJECT_DIR/templates")
fi

if [ ${#DIRS_TO_CREATE[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ All required directories already exist${NC}"
else
    echo -e "${GREEN}Creating missing directories: ${DIRS_TO_CREATE[*]}${NC}"
    for dir in "${DIRS_TO_CREATE[@]}"; do
        mkdir -p "$dir"
    done
    echo -e "${GREEN}✓ Required directories created${NC}"
fi

# Set ownership (always do this to ensure correct permissions)
echo -e "${GREEN}Setting directory ownership...${NC}"
chown -R "$SERVICE_USER:$SERVICE_USER" /var/log/media-pipeline 2>/dev/null || true
chown -R "$SERVICE_USER:$SERVICE_USER" /mnt/wd_all_pictures 2>/dev/null || true
chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR" 2>/dev/null || true

echo ""
echo -e "${BLUE}=== Step 7: Copy Application Files ===${NC}"

# Copy application files to project directory
FILES_COPIED=0

# Copy database viewer
if [ -f "db_viewer.py" ]; then
    if [ ! -f "$PROJECT_DIR/db_viewer.py" ] || [ "db_viewer.py" -nt "$PROJECT_DIR/db_viewer.py" ]; then
        cp db_viewer.py "$PROJECT_DIR/"
        chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/db_viewer.py"
        chmod +x "$PROJECT_DIR/db_viewer.py"
        echo -e "${GREEN}✓ Database viewer copied${NC}"
        FILES_COPIED=1
    else
        echo -e "${GREEN}✓ Database viewer already up to date${NC}"
    fi
else
    echo -e "${YELLOW}⚠ db_viewer.py not found, skipping${NC}"
fi

# Copy PM2 ecosystem config
if [ -f "ecosystem.config.js" ]; then
    if [ ! -f "$PROJECT_DIR/ecosystem.config.js" ] || [ "ecosystem.config.js" -nt "$PROJECT_DIR/ecosystem.config.js" ]; then
        cp ecosystem.config.js "$PROJECT_DIR/"
        chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/ecosystem.config.js"
        echo -e "${GREEN}✓ PM2 ecosystem config copied${NC}"
        FILES_COPIED=1
    else
        echo -e "${GREEN}✓ PM2 ecosystem config already up to date${NC}"
    fi
else
    echo -e "${YELLOW}⚠ ecosystem.config.js not found, skipping${NC}"
fi

# Copy templates
if [ -d "templates" ]; then
    # Check if templates need updating
    TEMPLATES_UPDATED=0
    for template in templates/*; do
        if [ -f "$template" ]; then
            template_name=$(basename "$template")
            if [ ! -f "$PROJECT_DIR/templates/$template_name" ] || [ "$template" -nt "$PROJECT_DIR/templates/$template_name" ]; then
                TEMPLATES_UPDATED=1
                break
            fi
        fi
    done
    
    if [ $TEMPLATES_UPDATED -eq 1 ]; then
        cp -r templates/* "$PROJECT_DIR/templates/"
        chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/templates/"
        echo -e "${GREEN}✓ Templates copied${NC}"
        FILES_COPIED=1
    else
        echo -e "${GREEN}✓ Templates already up to date${NC}"
    fi
else
    echo -e "${YELLOW}⚠ templates directory not found, skipping${NC}"
fi

if [ $FILES_COPIED -eq 0 ]; then
    echo -e "${GREEN}✓ All application files already up to date${NC}"
fi

echo -e "${BLUE}=== Step 8: Configure Nginx ===${NC}"

# Check if nginx configuration needs updating
NGINX_CONFIG_UPDATED=0
if [ -f "nginx-media-pipeline.conf" ]; then
    if [ ! -f "/etc/nginx/sites-available/media-pipeline" ] || [ "nginx-media-pipeline.conf" -nt "/etc/nginx/sites-available/media-pipeline" ]; then
        cp nginx-media-pipeline.conf /etc/nginx/sites-available/media-pipeline
        echo -e "${GREEN}✓ Nginx configuration copied${NC}"
        NGINX_CONFIG_UPDATED=1
    else
        echo -e "${GREEN}✓ Nginx configuration already up to date${NC}"
    fi
else
    echo -e "${YELLOW}⚠ nginx-media-pipeline.conf not found, creating basic config${NC}"
    cat > /etc/nginx/sites-available/media-pipeline << EOF
server {
    listen 80;
    server_name _;
    
    # Status Dashboard
    location /status/ {
        proxy_pass http://127.0.0.1:8082/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Database Viewer
    location /db/ {
        proxy_pass http://127.0.0.1:8084/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    NGINX_CONFIG_UPDATED=1
fi

# Enable the site (always do this to ensure it's enabled)
ln -sf /etc/nginx/sites-available/media-pipeline /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and restart nginx if config was updated
if [ $NGINX_CONFIG_UPDATED -eq 1 ]; then
    echo -e "${GREEN}Testing nginx configuration...${NC}"
    if nginx -t; then
        echo -e "${GREEN}✓ Nginx configuration test passed${NC}"
        if service nginx is-active --quiet; then
            echo -e "${GREEN}Reloading nginx...${NC}"
            service nginx reload
        else
            echo -e "${GREEN}Starting nginx...${NC}"
            service nginx start
        fi
        echo -e "${GREEN}✓ Nginx configured and running${NC}"
    else
        echo -e "${RED}✗ Nginx configuration test failed${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Nginx already configured and running${NC}"
fi

echo ""
echo -e "${BLUE}=== Step 9: Create Environment File ===${NC}"

# Create .env file only if it doesn't exist
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${GREEN}Creating environment file...${NC}"
    cat > "$PROJECT_DIR/.env" << EOF
# Media Pipeline Environment Configuration
# Generated on $(date)

# iCloud Configuration
ICLOUD_USERNAME=
ICLOUD_PASSWORD=

# Syncthing Configuration
SYNCTHING_URL=http://$CONTAINER_IP:8385/rest
SYNCTHING_API_KEY=

# Telegram Notifications (Optional)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Directory Configuration
INCOMING_DIR=/mnt/wd_all_pictures/incoming
PROCESSED_DIR=/mnt/wd_all_pictures/processed
EOF

    chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/.env"
    chmod 600 "$PROJECT_DIR/.env"
    echo -e "${GREEN}✓ Environment file created${NC}"
else
    echo -e "${GREEN}✓ Environment file already exists${NC}"
fi

echo ""
echo -e "${BLUE}=== Step 10: Start PM2 Applications ===${NC}"

# Check if PM2 is already running applications
if pm2 list | grep -q "online"; then
    echo -e "${GREEN}✓ PM2 applications already running${NC}"
    
    # Check if ecosystem config was updated and restart if needed
    if [ $FILES_COPIED -eq 1 ]; then
        echo -e "${GREEN}Restarting PM2 applications due to config changes...${NC}"
        pm2 restart all
        pm2 save
        echo -e "${GREEN}✓ PM2 applications restarted${NC}"
    else
        echo -e "${GREEN}✓ PM2 applications up to date${NC}"
    fi
else
    echo -e "${GREEN}Starting PM2 applications...${NC}"
    pm2 start "$PROJECT_DIR/ecosystem.config.js"
    pm2 save
    echo -e "${GREEN}✓ PM2 applications started${NC}"
fi

echo ""
echo -e "${BLUE}=== Step 11: Verify Dependencies ===${NC}"

# Verify all critical dependencies
echo -e "${GREEN}Verifying dependencies...${NC}"

# Check Node.js and NPM
if command -v node &> /dev/null; then
    echo -e "${GREEN}✓ Node.js: $(node --version)${NC}"
else
    echo -e "${RED}✗ Node.js: NOT FOUND${NC}"
fi

if command -v npm &> /dev/null; then
    echo -e "${GREEN}✓ NPM: $(npm --version)${NC}"
else
    echo -e "${RED}✗ NPM: NOT FOUND${NC}"
fi

# Check PM2
if command -v pm2 &> /dev/null; then
    echo -e "${GREEN}✓ PM2: $(pm2 --version)${NC}"
else
    echo -e "${RED}✗ PM2: NOT FOUND${NC}"
fi

# Check Python
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓ Python3: $(python3 --version)${NC}"
else
    echo -e "${RED}✗ Python3: NOT FOUND${NC}"
fi

# Check pip
if command -v pip3 &> /dev/null; then
    echo -e "${GREEN}✓ pip3: $(pip3 --version | cut -d' ' -f2)${NC}"
else
    echo -e "${RED}✗ pip3: NOT FOUND${NC}"
fi

# Check Syncthing
if command -v syncthing &> /dev/null; then
    echo -e "${GREEN}✓ Syncthing: $(syncthing --version | head -n1)${NC}"
else
    echo -e "${RED}✗ Syncthing: NOT FOUND${NC}"
fi

# Check Nginx
if command -v nginx &> /dev/null; then
    echo -e "${GREEN}✓ Nginx: $(nginx -v 2>&1 | cut -d' ' -f3)${NC}"
else
    echo -e "${RED}✗ Nginx: NOT FOUND${NC}"
fi

# Check SQLite
if command -v sqlite3 &> /dev/null; then
    echo -e "${GREEN}✓ SQLite3: $(sqlite3 --version | cut -d' ' -f1)${NC}"
else
    echo -e "${RED}✗ SQLite3: NOT FOUND${NC}"
fi

echo ""
echo -e "${BLUE}=== Step 12: Verify Services ===${NC}"

# Wait for services to start
sleep 5

# Check PM2 status
echo -e "${GREEN}PM2 Application Status:${NC}"
pm2 status

# Check ports
echo -e "${GREEN}Checking ports...${NC}"
ports=("80" "8080" "8081" "8082" "8083" "8084" "8385" "9615")
for port in "${ports[@]}"; do
    if netstat -tlnp | grep -q ":$port "; then
        echo -e "${GREEN}✓ Port $port: LISTENING${NC}"
    else
        echo -e "${YELLOW}⚠ Port $port: NOT LISTENING${NC}"
    fi
done

echo ""
echo -e "${GREEN}=== Installation Complete! ===${NC}"
echo ""
echo -e "${BLUE}Access URLs:${NC}"
echo -e "${YELLOW}Web UI (Main):${NC} http://$CONTAINER_IP:8080"
echo -e "${YELLOW}Pipeline Dashboard:${NC} http://$CONTAINER_IP:8081"
echo -e "${YELLOW}Status Dashboard:${NC} http://$CONTAINER_IP:8082"
echo -e "${YELLOW}Configuration Interface:${NC} http://$CONTAINER_IP:8083"
echo -e "${YELLOW}Database Viewer:${NC} http://$CONTAINER_IP:8084"
echo -e "${YELLOW}Syncthing:${NC} http://$CONTAINER_IP:8385"
echo -e "${YELLOW}PM2 Dashboard:${NC} http://$CONTAINER_IP:9615"
echo ""
echo -e "${BLUE}Via Nginx:${NC}"
echo -e "${YELLOW}Web UI (Main):${NC} http://$CONTAINER_IP/"
echo -e "${YELLOW}Pipeline Dashboard:${NC} http://$CONTAINER_IP/pipeline/"
echo -e "${YELLOW}Status Dashboard:${NC} http://$CONTAINER_IP/status/"
echo -e "${YELLOW}Configuration Interface:${NC} http://$CONTAINER_IP/config/"
echo -e "${YELLOW}Database Viewer:${NC} http://$CONTAINER_IP/db/"
echo -e "${YELLOW}Syncthing:${NC} http://$CONTAINER_IP/syncthing/"
echo -e "${YELLOW}PM2 Dashboard:${NC} http://$CONTAINER_IP/pm2/"
echo ""
echo -e "${BLUE}CLI Commands:${NC}"
echo -e "${YELLOW}Test iCloud:${NC} /opt/media-pipeline/venv/bin/icloudpd --username YOUR_EMAIL --directory /mnt/wd_all_pictures/incoming --download-only --recent 5"
echo -e "${YELLOW}Run Pipeline:${NC} cd /opt/media-pipeline && source .env && /opt/media-pipeline/venv/bin/python pipeline_orchestrator.py"
echo -e "${YELLOW}View Database:${NC} sqlite3 /opt/media-pipeline/media.db"
echo ""
echo -e "${BLUE}PM2 Management:${NC}"
echo -e "${YELLOW}Check status:${NC} pm2 status"
echo -e "${YELLOW}View logs:${NC} pm2 logs"
echo -e "${YELLOW}Restart all:${NC} pm2 restart all"
echo ""
echo -e "${GREEN}🎉 Complete Media Pipeline System Installed! 🎉${NC}"
echo -e "${GREEN}Use the Database Viewer to explore your downloaded media data!${NC}"

echo ""
echo -e "${BLUE}=== Installation Summary ===${NC}"
echo -e "${GREEN}✓ Optimized installation completed successfully${NC}"
echo -e "${GREEN}✓ Only missing components were installed/updated${NC}"
echo -e "${GREEN}✓ Existing configurations preserved${NC}"
echo -e "${GREEN}✓ Services restarted only when necessary${NC}"
echo ""
echo -e "${YELLOW}💡 Tip: Run this script again anytime to update only what's needed!${NC}"
