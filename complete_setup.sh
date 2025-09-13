#!/bin/bash

# Complete Media Pipeline Setup Script
# This script completes the setup and starts all services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Completing Media Pipeline Setup ===${NC}"

# Configuration
PROJECT_DIR="/opt/media-pipeline"
SERVICE_USER="media-pipeline"
SYNCTHING_PORT="8384"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}This script must be run as root${NC}"
    echo "Please run: sudo $0"
    exit 1
fi

echo -e "${GREEN}Completing Media Pipeline setup...${NC}"

# Load environment variables
if [ -f "$PROJECT_DIR/.env" ]; then
    echo -e "${GREEN}Loading environment variables...${NC}"
    export $(cat "$PROJECT_DIR/.env" | grep -v '^#' | xargs)
else
    echo -e "${YELLOW}Warning: .env file not found at $PROJECT_DIR/.env${NC}"
    echo -e "${YELLOW}Please create and configure the .env file first${NC}"
    echo -e "${YELLOW}You can copy from: $PROJECT_DIR/.env.template${NC}"
    exit 1
fi

# Start all services
echo -e "${GREEN}Starting all services...${NC}"

# Start Syncthing if available
if command -v syncthing &> /dev/null; then
    echo -e "${GREEN}Starting Syncthing...${NC}"
    systemctl start syncthing@$SERVICE_USER
    sleep 5  # Wait for Syncthing to start
    echo -e "${GREEN}✓ Syncthing started${NC}"
else
    echo -e "${YELLOW}⚠ Syncthing not available, skipping...${NC}"
fi

# Start Nginx if available
if command -v nginx &> /dev/null; then
    echo -e "${GREEN}Starting Nginx...${NC}"
    systemctl start nginx
    echo -e "${GREEN}✓ Nginx started${NC}"
else
    echo -e "${YELLOW}⚠ Nginx not available, skipping...${NC}"
fi

# Start Media Pipeline services
echo -e "${GREEN}Starting Media Pipeline services...${NC}"
systemctl start media-pipeline
systemctl start media-pipeline-web
echo -e "${GREEN}✓ Media Pipeline services started${NC}"

# Start scheduled execution (timer or cron)
echo -e "${GREEN}Starting scheduled execution...${NC}"
if systemctl list-timers | grep -q "media-pipeline-daily.timer"; then
    echo -e "${GREEN}Starting systemd timer...${NC}"
    systemctl start media-pipeline-daily.timer
    echo -e "${GREEN}✓ Systemd timer started${NC}"
else
    echo -e "${YELLOW}Using cron for scheduled execution${NC}"
fi

# Check service status
echo -e "${GREEN}Checking service status...${NC}"
echo ""

# Check Syncthing status
if command -v syncthing &> /dev/null; then
    echo -e "${BLUE}Syncthing Status:${NC}"
    systemctl status syncthing@$SERVICE_USER --no-pager -l
    echo ""
fi

# Check Media Pipeline status
echo -e "${BLUE}Media Pipeline Status:${NC}"
systemctl status media-pipeline --no-pager -l
echo ""

echo -e "${BLUE}Media Pipeline Web UI Status:${NC}"
systemctl status media-pipeline-web --no-pager -l
echo ""

# Check Nginx status
if command -v nginx &> /dev/null; then
    echo -e "${BLUE}Nginx Status:${NC}"
    systemctl status nginx --no-pager -l
    echo ""
fi

# Check timer status if using systemd timer
if systemctl list-timers | grep -q "media-pipeline-daily.timer"; then
    echo -e "${BLUE}Timer Status:${NC}"
    systemctl status media-pipeline-daily.timer --no-pager -l
    echo ""
    echo -e "${BLUE}Active Timers:${NC}"
    systemctl list-timers | grep media-pipeline
    echo ""
fi

# Get container IP
CONTAINER_IP=$(hostname -I | awk '{print $1}')

echo -e "${GREEN}=== Setup Complete! ===${NC}"
echo ""
echo -e "${GREEN}🎉 Media Pipeline is now running! 🎉${NC}"
echo ""
echo -e "${BLUE}Access URLs:${NC}"
echo -e "${YELLOW}VS Code Server:${NC}     http://$CONTAINER_IP:8080"
echo -e "${YELLOW}Media Pipeline Web UI:${NC} http://$CONTAINER_IP:8081"
if command -v syncthing &> /dev/null; then
    echo -e "${YELLOW}Syncthing:${NC}          http://$CONTAINER_IP:$SYNCTHING_PORT"
fi
echo ""
echo -e "${BLUE}Service Management:${NC}"
echo -e "${YELLOW}Check status:${NC}    systemctl status media-pipeline"
echo -e "${YELLOW}View logs:${NC}       journalctl -u media-pipeline -f"
echo -e "${YELLOW}Restart:${NC}         systemctl restart media-pipeline"
echo ""
echo -e "${GREEN}Your media pipeline is ready to use!${NC}"
