#!/bin/bash

# Service Restart Script
# This script restarts all media pipeline services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Restarting Media Pipeline Services ===${NC}"

# Configuration
SERVICE_USER="media-pipeline"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}This script must be run as root${NC}"
    echo "Please run: sudo $0"
    exit 1
fi

echo -e "${GREEN}Stopping all services...${NC}"

# Stop all services
systemctl stop media-pipeline 2>/dev/null || true
systemctl stop media-pipeline-web 2>/dev/null || true
systemctl stop syncthing@$SERVICE_USER 2>/dev/null || true
systemctl stop nginx 2>/dev/null || true

echo -e "${GREEN}Waiting for services to stop...${NC}"
sleep 3

echo -e "${GREEN}Starting all services...${NC}"

# Start services in order
echo -e "${GREEN}1. Starting Syncthing...${NC}"
if systemctl start syncthing@$SERVICE_USER; then
    echo -e "${GREEN}✓ Syncthing started${NC}"
    sleep 5  # Wait for Syncthing to initialize
else
    echo -e "${RED}✗ Failed to start Syncthing${NC}"
fi

echo -e "${GREEN}2. Starting Nginx...${NC}"
if systemctl start nginx; then
    echo -e "${GREEN}✓ Nginx started${NC}"
else
    echo -e "${RED}✗ Failed to start Nginx${NC}"
fi

echo -e "${GREEN}3. Starting Media Pipeline...${NC}"
if systemctl start media-pipeline; then
    echo -e "${GREEN}✓ Media Pipeline started${NC}"
else
    echo -e "${RED}✗ Failed to start Media Pipeline${NC}"
fi

echo -e "${GREEN}4. Starting Web UI...${NC}"
if systemctl start media-pipeline-web; then
    echo -e "${GREEN}✓ Web UI started${NC}"
else
    echo -e "${RED}✗ Failed to start Web UI${NC}"
fi

echo -e "${GREEN}Waiting for services to initialize...${NC}"
sleep 5

# Check service status
echo -e "${GREEN}Checking service status...${NC}"
echo ""

# Check each service
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

echo ""

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
    echo -e "${RED}✗ Port 8384 (Syncthing) is NOT listening${NC}"
fi

# Get container IP
CONTAINER_IP=$(hostname -I | awk '{print $1}')

echo ""
echo -e "${GREEN}=== Service Restart Complete ===${NC}"
echo ""
echo -e "${BLUE}Access URLs:${NC}"
echo -e "${YELLOW}Web UI:${NC} http://$CONTAINER_IP:8081"
echo -e "${YELLOW}Syncthing:${NC} http://$CONTAINER_IP:8384"
echo ""
echo -e "${BLUE}If services are still not working:${NC}"
echo -e "${YELLOW}1. Check logs: journalctl -u media-pipeline -f${NC}"
echo -e "${YELLOW}2. Check configuration: nano /opt/media-pipeline/.env${NC}"
echo -e "${YELLOW}3. Test locally: curl http://127.0.0.1:8081${NC}"
