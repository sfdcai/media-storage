#!/bin/bash

# Complete Setup Guide Script
# This script provides a complete setup guide for the media pipeline

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Media Pipeline Complete Setup Guide ===${NC}"

# Get container IP
CONTAINER_IP=$(hostname -I | awk '{print $1}')

echo -e "${GREEN}Welcome to the Media Pipeline Setup Guide!${NC}"
echo -e "${YELLOW}This guide will help you configure everything step by step.${NC}"
echo ""

echo -e "${BLUE}=== Current Status ===${NC}"
echo -e "${GREEN}✓ Status Dashboard: http://$CONTAINER_IP:8082${NC}"
echo -e "${GREEN}✓ VS Code Server: http://$CONTAINER_IP:8080${NC}"
echo -e "${YELLOW}⚠ Media Pipeline Web UI: http://$CONTAINER_IP:8081${NC}"
echo -e "${YELLOW}⚠ Syncthing: http://$CONTAINER_IP:8384${NC}"
echo ""

echo -e "${BLUE}=== Step 1: Configure Credentials ===${NC}"
echo -e "${YELLOW}Run the credentials configuration script:${NC}"
echo -e "${GREEN}sudo ./configure_credentials.sh${NC}"
echo ""
echo -e "${YELLOW}This will configure:${NC}"
echo -e "${YELLOW}• iCloud username and password${NC}"
echo -e "${YELLOW}• Syncthing API key${NC}"
echo -e "${YELLOW}• Telegram notifications (optional)${NC}"
echo -e "${YELLOW}• Directory paths${NC}"
echo ""

echo -e "${BLUE}=== Step 2: Fix Syncthing ===${NC}"
echo -e "${YELLOW}Run the Syncthing fix script:${NC}"
echo -e "${GREEN}sudo ./fix_syncthing.sh${NC}"
echo ""
echo -e "${YELLOW}This will:${NC}"
echo -e "${YELLOW}• Check Syncthing status${NC}"
echo -e "${YELLOW}• Fix configuration issues${NC}"
echo -e "${YELLOW}• Ensure it's accessible from outside${NC}"
echo ""

echo -e "${BLUE}=== Step 3: Start All Services ===${NC}"
echo -e "${YELLOW}Start all media pipeline services:${NC}"
echo -e "${GREEN}sudo systemctl start media-pipeline${NC}"
echo -e "${GREEN}sudo systemctl start media-pipeline-web${NC}"
echo -e "${GREEN}sudo systemctl start syncthing@media-pipeline${NC}"
echo -e "${GREEN}sudo systemctl start nginx${NC}"
echo ""

echo -e "${BLUE}=== Step 4: Verify Everything Works ===${NC}"
echo -e "${YELLOW}Check service status:${NC}"
echo -e "${GREEN}sudo systemctl status media-pipeline${NC}"
echo -e "${GREEN}sudo systemctl status media-pipeline-web${NC}"
echo -e "${GREEN}sudo systemctl status syncthing@media-pipeline${NC}"
echo -e "${GREEN}sudo systemctl status nginx${NC}"
echo ""

echo -e "${BLUE}=== Step 5: Access Your Dashboards ===${NC}"
echo -e "${GREEN}Status Dashboard: http://$CONTAINER_IP:8082${NC}"
echo -e "${GREEN}Syncthing: http://$CONTAINER_IP:8384${NC}"
echo -e "${GREEN}Media Pipeline Web UI: http://$CONTAINER_IP:8081${NC}"
echo -e "${GREEN}VS Code Server: http://$CONTAINER_IP:8080${NC}"
echo ""

echo -e "${BLUE}=== Troubleshooting ===${NC}"
echo -e "${YELLOW}If something doesn't work:${NC}"
echo ""
echo -e "${YELLOW}1. Check logs:${NC}"
echo -e "${GREEN}journalctl -u media-pipeline -f${NC}"
echo -e "${GREEN}journalctl -u syncthing@media-pipeline -f${NC}"
echo ""
echo -e "${YELLOW}2. Check ports:${NC}"
echo -e "${GREEN}netstat -tlnp | grep -E ':(8080|8081|8082|8384)'${NC}"
echo ""
echo -e "${YELLOW}3. Restart services:${NC}"
echo -e "${GREEN}sudo systemctl restart media-pipeline${NC}"
echo -e "${GREEN}sudo systemctl restart syncthing@media-pipeline${NC}"
echo ""
echo -e "${YELLOW}4. Use the status dashboard:${NC}"
echo -e "${GREEN}http://$CONTAINER_IP:8082${NC}"
echo ""

echo -e "${BLUE}=== Quick Commands ===${NC}"
echo -e "${YELLOW}Configure credentials:${NC}"
echo -e "${GREEN}sudo ./configure_credentials.sh${NC}"
echo ""
echo -e "${YELLOW}Fix Syncthing:${NC}"
echo -e "${GREEN}sudo ./fix_syncthing.sh${NC}"
echo ""
echo -e "${YELLOW}Start all services:${NC}"
echo -e "${GREEN}sudo systemctl start media-pipeline media-pipeline-web syncthing@media-pipeline nginx${NC}"
echo ""
echo -e "${YELLOW}Check all services:${NC}"
echo -e "${GREEN}sudo systemctl status media-pipeline media-pipeline-web syncthing@media-pipeline nginx${NC}"
echo ""

echo -e "${GREEN}=== Setup Guide Complete! ===${NC}"
echo -e "${YELLOW}Follow the steps above to configure your media pipeline.${NC}"
echo -e "${YELLOW}Use the status dashboard to monitor everything!${NC}"
echo ""
echo -e "${GREEN}🎉 Happy media syncing! 🎉${NC}"
