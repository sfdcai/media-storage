#!/bin/bash

# Fix Service Issues Script
# This script fixes the service startup issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Fixing Service Issues ===${NC}"

# Configuration
PROJECT_DIR="/opt/media-pipeline"
SERVICE_USER="media-pipeline"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}This script must be run as root${NC}"
    echo "Please run: sudo $0"
    exit 1
fi

echo -e "${GREEN}Fixing service startup issues...${NC}"

# Fix 1: Install net-tools for netstat
echo -e "${GREEN}1. Installing net-tools...${NC}"
apt update
apt install -y net-tools

# Fix 2: Check and fix .env file
echo -e "${GREEN}2. Checking .env file...${NC}"
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cat > "$PROJECT_DIR/.env" << 'EOF'
# Media Pipeline Environment Variables
# Edit these with your actual credentials

# iCloud Credentials
ICLOUD_USERNAME=your_icloud_email@example.com
ICLOUD_PASSWORD=your_icloud_password

# Syncthing Configuration
SYNCTHING_API_KEY=your_syncthing_api_key

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Database
DB_FILE=/opt/media-pipeline/media.db

# Logging
LOG_LEVEL=INFO
LOG_DIR=/var/log/media-pipeline
EOF
    chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/.env"
    echo -e "${GREEN}✓ .env file created${NC}"
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

# Fix 3: Check Python virtual environment
echo -e "${GREEN}3. Checking Python virtual environment...${NC}"
if [ ! -f "$PROJECT_DIR/venv/bin/python" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    sudo -u "$SERVICE_USER" python3 -m venv "$PROJECT_DIR/venv"
    sudo -u "$SERVICE_USER" "$PROJECT_DIR/venv/bin/pip" install --upgrade pip
    sudo -u "$SERVICE_USER" "$PROJECT_DIR/venv/bin/pip" install -r "$PROJECT_DIR/requirements.txt"
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
fi

# Fix 4: Test Python script manually
echo -e "${GREEN}4. Testing Python script manually...${NC}"
cd "$PROJECT_DIR"
if sudo -u "$SERVICE_USER" "$PROJECT_DIR/venv/bin/python" "$PROJECT_DIR/pipeline_orchestrator.py" --help 2>/dev/null; then
    echo -e "${GREEN}✓ Python script runs successfully${NC}"
else
    echo -e "${YELLOW}⚠ Python script has issues, checking logs...${NC}"
    sudo -u "$SERVICE_USER" "$PROJECT_DIR/venv/bin/python" "$PROJECT_DIR/pipeline_orchestrator.py" 2>&1 | head -10
fi

# Fix 5: Check and fix file permissions
echo -e "${GREEN}5. Fixing file permissions...${NC}"
chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR"
chmod -R 755 "$PROJECT_DIR"
chown -R "$SERVICE_USER:$SERVICE_USER" "/var/log/media-pipeline"
chmod -R 755 "/var/log/media-pipeline"

# Fix 6: Check systemd service files
echo -e "${GREEN}6. Checking systemd service files...${NC}"
if [ -f "/etc/systemd/system/media-pipeline.service" ]; then
    echo -e "${GREEN}✓ Media pipeline service file exists${NC}"
    echo -e "${YELLOW}Service file content:${NC}"
    cat "/etc/systemd/system/media-pipeline.service"
else
    echo -e "${RED}✗ Media pipeline service file missing${NC}"
fi

# Fix 7: Reload systemd and restart services
echo -e "${GREEN}7. Reloading systemd and restarting services...${NC}"
systemctl daemon-reload

# Stop services first
systemctl stop media-pipeline 2>/dev/null || true
systemctl stop media-pipeline-web 2>/dev/null || true

# Start services
echo -e "${GREEN}Starting Media Pipeline...${NC}"
if systemctl start media-pipeline; then
    echo -e "${GREEN}✓ Media Pipeline started${NC}"
else
    echo -e "${RED}✗ Media Pipeline failed to start${NC}"
    echo -e "${YELLOW}Error details:${NC}"
    journalctl -u media-pipeline --no-pager -n 5
fi

echo -e "${GREEN}Starting Web UI...${NC}"
if systemctl start media-pipeline-web; then
    echo -e "${GREEN}✓ Web UI started${NC}"
else
    echo -e "${RED}✗ Web UI failed to start${NC}"
    echo -e "${YELLOW}Error details:${NC}"
    journalctl -u media-pipeline-web --no-pager -n 5
fi

# Wait a moment for services to start
sleep 3

# Fix 8: Check service status
echo -e "${GREEN}8. Checking service status...${NC}"
echo ""

services=("media-pipeline" "media-pipeline-web" "syncthing@$SERVICE_USER" "nginx")
for service in "${services[@]}"; do
    if systemctl is-active --quiet "$service"; then
        echo -e "${GREEN}✓ $service: ACTIVE${NC}"
    else
        echo -e "${RED}✗ $service: INACTIVE${NC}"
        echo -e "${YELLOW}Last few log lines:${NC}"
        journalctl -u "$service" --no-pager -n 3
    fi
done

# Fix 9: Check ports
echo -e "${GREEN}9. Checking ports...${NC}"
if netstat -tlnp | grep -q ":8081 "; then
    echo -e "${GREEN}✓ Port 8081 (Web UI) is listening${NC}"
else
    echo -e "${RED}✗ Port 8081 (Web UI) is NOT listening${NC}"
fi

if netstat -tlnp | grep -q ":8384 "; then
    echo -e "${GREEN}✓ Port 8384 (Syncthing) is listening${NC}"
else
    echo -e "${RED}✗ Port 8384 (Syncthing) is NOT listening${NC}"
fi

# Get container IP
CONTAINER_IP=$(hostname -I | awk '{print $1}')

echo ""
echo -e "${GREEN}=== Service Fix Complete ===${NC}"
echo ""
echo -e "${BLUE}Access URLs:${NC}"
echo -e "${YELLOW}Web UI:${NC} http://$CONTAINER_IP:8081"
echo -e "${YELLOW}Syncthing:${NC} http://$CONTAINER_IP:8384"
echo ""
echo -e "${BLUE}If services are still not working:${NC}"
echo -e "${YELLOW}1. Check detailed logs: journalctl -u media-pipeline -f${NC}"
echo -e "${YELLOW}2. Test manually: sudo -u $SERVICE_USER $PROJECT_DIR/venv/bin/python $PROJECT_DIR/pipeline_orchestrator.py${NC}"
echo -e "${YELLOW}3. Check configuration: nano $PROJECT_DIR/.env${NC}"
