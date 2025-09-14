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

# Configuration
PROJECT_DIR="/opt/media-pipeline"
SERVICE_USER="media-pipeline"
CONTAINER_IP=$(hostname -I | awk '{print $1}')

echo -e "${GREEN}Container IP: $CONTAINER_IP${NC}"
echo ""

echo -e "${BLUE}=== Step 1: Install System Packages ===${NC}"

# Install system packages
echo -e "${GREEN}Installing system packages...${NC}"
apt update
apt install -y nginx python3-pip python3-venv net-tools curl wget sqlite3

echo -e "${GREEN}✓ System packages installed${NC}"

echo ""
echo -e "${BLUE}=== Step 2: Install Node.js and PM2 ===${NC}"

# Install Node.js
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

echo ""
echo -e "${BLUE}=== Step 3: Install Syncthing ===${NC}"

# Install Syncthing
echo -e "${GREEN}Installing Syncthing...${NC}"
# Use modern GPG key management instead of deprecated apt-key
curl -s https://syncthing.net/release-key.txt | gpg --dearmor -o /usr/share/keyrings/syncthing-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/syncthing-archive-keyring.gpg] https://apt.syncthing.net/ syncthing stable" > /etc/apt/sources.list.d/syncthing.list
apt update
apt install -y syncthing

echo -e "${GREEN}✓ Syncthing installed${NC}"

echo ""
echo -e "${BLUE}=== Step 4: Setup Python Virtual Environment ===${NC}"

# Create virtual environment
echo -e "${GREEN}Creating Python virtual environment...${NC}"
python3 -m venv "$PROJECT_DIR/venv"

# Install Python packages
echo -e "${GREEN}Installing Python packages...${NC}"
"$PROJECT_DIR/venv/bin/pip" install flask flask-socketio requests icloudpd

echo -e "${GREEN}✓ Python virtual environment created${NC}"

echo ""
echo -e "${BLUE}=== Step 5: Create Required Directories ===${NC}"

# Create required directories
echo -e "${GREEN}Creating required directories...${NC}"
mkdir -p /var/log/media-pipeline
mkdir -p /mnt/wd_all_pictures/incoming
mkdir -p /mnt/wd_all_pictures/processed
mkdir -p "$PROJECT_DIR/templates"

# Set ownership
chown -R "$SERVICE_USER:$SERVICE_USER" /var/log/media-pipeline
chown -R "$SERVICE_USER:$SERVICE_USER" /mnt/wd_all_pictures
chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR"

echo -e "${GREEN}✓ Required directories created${NC}"

echo ""
echo -e "${BLUE}=== Step 6: Copy Application Files ===${NC}"

# Copy application files to project directory
echo -e "${GREEN}Copying application files...${NC}"

# Copy database viewer
if [ -f "db_viewer.py" ]; then
    cp db_viewer.py "$PROJECT_DIR/"
chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/db_viewer.py"
chmod +x "$PROJECT_DIR/db_viewer.py"
    echo -e "${GREEN}✓ Database viewer copied${NC}"
else
    echo -e "${YELLOW}⚠ db_viewer.py not found, skipping${NC}"
fi

# Copy PM2 ecosystem config
if [ -f "ecosystem.config.js" ]; then
    cp ecosystem.config.js "$PROJECT_DIR/"
chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/ecosystem.config.js"
    echo -e "${GREEN}✓ PM2 ecosystem config copied${NC}"
else
    echo -e "${YELLOW}⚠ ecosystem.config.js not found, skipping${NC}"
fi

# Copy templates
if [ -d "templates" ]; then
    cp -r templates/* "$PROJECT_DIR/templates/"
    chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/templates/"
    echo -e "${GREEN}✓ Templates copied${NC}"
else
    echo -e "${YELLOW}⚠ templates directory not found, skipping${NC}"
fi

echo -e "${GREEN}✓ Application files copied${NC}"

# Configure Nginx
echo -e "${GREEN}Configuring Nginx...${NC}"

# Copy nginx configuration
if [ -f "nginx-media-pipeline.conf" ]; then
    cp nginx-media-pipeline.conf /etc/nginx/sites-available/media-pipeline
    echo -e "${GREEN}✓ Nginx configuration copied${NC}"
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
fi

# Enable the site
ln -sf /etc/nginx/sites-available/media-pipeline /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and start Nginx
nginx -t
service nginx start

echo -e "${GREEN}✓ Nginx configured and started${NC}"

echo ""
echo -e "${BLUE}=== Step 9: Create Environment File ===${NC}"

# Create .env file
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

echo ""
echo -e "${BLUE}=== Step 10: Start PM2 Applications ===${NC}"

# Start PM2 applications
echo -e "${GREEN}Starting PM2 applications...${NC}"
pm2 start "$PROJECT_DIR/ecosystem.config.js"

# Save PM2 configuration
pm2 save

echo -e "${GREEN}✓ PM2 applications started${NC}"

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
