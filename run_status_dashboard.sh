#!/bin/bash

# Run Status Dashboard Script
# This script runs the status dashboard manually

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Running Media Pipeline Status Dashboard ===${NC}"

# Configuration
PROJECT_DIR="/opt/media-pipeline"
DASHBOARD_PORT="8082"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}This script must be run as root${NC}"
    echo "Please run: sudo $0"
    exit 1
fi

echo -e "${GREEN}Starting status dashboard...${NC}"

# Install required packages if not already installed
echo -e "${GREEN}Checking Python packages...${NC}"
if [ -f "$PROJECT_DIR/venv/bin/pip" ]; then
    sudo -u media-pipeline "$PROJECT_DIR/venv/bin/pip" install flask flask-socketio 2>/dev/null || true
    PYTHON_CMD="$PROJECT_DIR/venv/bin/python"
else
    pip3 install flask flask-socketio 2>/dev/null || true
    PYTHON_CMD="python3"
fi

# Get container IP
CONTAINER_IP=$(hostname -I | awk '{print $1}')

echo -e "${GREEN}Status Dashboard will be available at:${NC}"
echo -e "${YELLOW}http://$CONTAINER_IP:$DASHBOARD_PORT${NC}"
echo ""
echo -e "${GREEN}Features:${NC}"
echo -e "${YELLOW}✓ Real-time service status monitoring${NC}"
echo -e "${YELLOW}✓ Service control (start/stop/restart)${NC}"
echo -e "${YELLOW}✓ Port status checking${NC}"
echo -e "${YELLOW}✓ Process monitoring${NC}"
echo -e "${YELLOW}✓ File status checking${NC}"
echo -e "${YELLOW}✓ Live log viewing${NC}"
echo -e "${YELLOW}✓ System information${NC}"
echo ""
echo -e "${GREEN}Press Ctrl+C to stop the dashboard${NC}"
echo ""

# Run the dashboard
cd "$PROJECT_DIR"
$PYTHON_CMD web_status_dashboard.py
