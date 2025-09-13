#!/bin/bash

# Port Information Script
# Shows the correct ports for all services

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Media Pipeline Port Information ===${NC}"
echo ""

# Get container IP
CONTAINER_IP=$(hostname -I | awk '{print $1}')

echo -e "${GREEN}Service Ports:${NC}"
echo -e "${YELLOW}VS Code Server:${NC}     http://$CONTAINER_IP:8080"
echo -e "${YELLOW}Media Pipeline Web UI:${NC} http://$CONTAINER_IP:8081"
echo -e "${YELLOW}Syncthing:${NC}          http://$CONTAINER_IP:8384"
echo ""

echo -e "${GREEN}Port Configuration:${NC}"
echo -e "${BLUE}• Port 8080:${NC} VS Code Server (for development)"
echo -e "${BLUE}• Port 8081:${NC} Media Pipeline Web UI (for management)"
echo -e "${BLUE}• Port 8384:${NC} Syncthing (for file synchronization)"
echo ""

echo -e "${GREEN}Access URLs:${NC}"
echo -e "${YELLOW}Development:${NC}  http://$CONTAINER_IP:8080"
echo -e "${YELLOW}Management:${NC}   http://$CONTAINER_IP:8081"
echo -e "${YELLOW}File Sync:${NC}    http://$CONTAINER_IP:8384"
echo ""

echo -e "${GREEN}Notes:${NC}"
echo -e "${BLUE}• VS Code Server runs on port 8080 for development${NC}"
echo -e "${BLUE}• Media Pipeline Web UI runs on port 8081 to avoid conflicts${NC}"
echo -e "${BLUE}• Both services can run simultaneously without issues${NC}"
echo ""

echo -e "${GREEN}🎉 No port conflicts! All services can run together! 🎉${NC}"
