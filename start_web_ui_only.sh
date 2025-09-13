#!/bin/bash

# Start Web UI Only Script
# This script starts just the web UI without the main pipeline

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Starting Web UI Only ===${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}This script must be run as root${NC}"
    echo "Please run: sudo $0"
    exit 1
fi

echo -e "${GREEN}Starting web UI services...${NC}"

# Stop the failing media pipeline service
echo -e "${GREEN}Stopping media pipeline service...${NC}"
systemctl stop media-pipeline 2>/dev/null || true

# Start the web UI service
echo -e "${GREEN}Starting web UI service...${NC}"
if systemctl start media-pipeline-web; then
    echo -e "${GREEN}✓ Web UI started successfully${NC}"
else
    echo -e "${RED}✗ Failed to start Web UI${NC}"
    echo -e "${YELLOW}Error details:${NC}"
    journalctl -u media-pipeline-web --no-pager -n 5
    exit 1
fi

# Start Nginx if available
echo -e "${GREEN}Starting Nginx...${NC}"
if systemctl start nginx; then
    echo -e "${GREEN}✓ Nginx started successfully${NC}"
else
    echo -e "${YELLOW}⚠ Nginx not available or failed to start${NC}"
fi

# Start Syncthing if available
echo -e "${GREEN}Starting Syncthing...${NC}"
if systemctl start syncthing@media-pipeline; then
    echo -e "${GREEN}✓ Syncthing started successfully${NC}"
else
    echo -e "${YELLOW}⚠ Syncthing not available or failed to start${NC}"
fi

# Wait for services to start
echo -e "${GREEN}Waiting for services to initialize...${NC}"
sleep 3

# Check service status
echo -e "${GREEN}Checking service status...${NC}"
echo ""

if systemctl is-active --quiet media-pipeline-web; then
    echo -e "${GREEN}✓ Web UI: ACTIVE${NC}"
else
    echo -e "${RED}✗ Web UI: INACTIVE${NC}"
fi

if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Nginx: ACTIVE${NC}"
else
    echo -e "${YELLOW}⚠ Nginx: INACTIVE${NC}"
fi

if systemctl is-active --quiet syncthing@media-pipeline; then
    echo -e "${GREEN}✓ Syncthing: ACTIVE${NC}"
else
    echo -e "${YELLOW}⚠ Syncthing: INACTIVE${NC}"
fi

# Check ports
echo -e "${GREEN}Checking ports...${NC}"
if netstat -tlnp | grep -q ":8081 "; then
    echo -e "${GREEN}✓ Port 8081 (Web UI) is listening${NC}"
else
    echo -e "${RED}✗ Port 8081 (Web UI) is NOT listening${NC}"
fi

if netstat -tlnp | grep -q ":8384 "; then
    echo -e "${GREEN}✓ Port 8384 (Syncthing) is listening${NC}"
else
    echo -e "${YELLOW}⚠ Port 8384 (Syncthing) is NOT listening${NC}"
fi

# Get container IP
CONTAINER_IP=$(hostname -I | awk '{print $1}')

echo ""
echo -e "${GREEN}=== Web UI Started Successfully! ===${NC}"
echo ""
echo -e "${BLUE}Access URLs:${NC}"
echo -e "${YELLOW}Web UI:${NC} http://$CONTAINER_IP:8081"
echo -e "${YELLOW}Syncthing:${NC} http://$CONTAINER_IP:8384"
echo ""
echo -e "${BLUE}Service Management:${NC}"
echo -e "${YELLOW}Check Web UI status:${NC} systemctl status media-pipeline-web"
echo -e "${YELLOW}View Web UI logs:${NC} journalctl -u media-pipeline-web -f"
echo -e "${YELLOW}Restart Web UI:${NC} systemctl restart media-pipeline-web"
echo ""
echo -e "${BLUE}To start the full pipeline later:${NC}"
echo -e "${YELLOW}1. Configure credentials: nano /opt/media-pipeline/.env${NC}"
echo -e "${YELLOW}2. Start pipeline: systemctl start media-pipeline${NC}"
echo ""
echo -e "${GREEN}🎉 Web UI is ready to use! 🎉${NC}"
