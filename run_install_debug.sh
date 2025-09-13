#!/bin/bash

# Debug wrapper script for Media Pipeline Installation
# This script runs the installation with enhanced debugging and monitoring

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Media Pipeline Installation Debug Wrapper ===${NC}"
echo -e "${BLUE}This script will run the installation with enhanced debugging${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "install.sh" ]; then
    echo -e "${RED}Error: install.sh not found in current directory${NC}"
    echo "Please run this script from the directory containing install.sh"
    exit 1
fi

# Check if we have the required permissions
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}Warning: Not running as root. Some operations may fail.${NC}"
    echo "Consider running with: sudo $0"
    echo ""
fi

# Set debug mode
export DEBUG_MODE=true

# Create a unique log directory
LOG_DIR="/tmp/media_pipeline_install_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"

echo -e "${GREEN}Debug Information:${NC}"
echo "  Log Directory: $LOG_DIR"
echo "  Debug Mode: $DEBUG_MODE"
echo "  User: $(whoami)"
echo "  Working Directory: $(pwd)"
echo "  System: $(uname -a)"
echo ""

# Function to monitor system resources
monitor_resources() {
    local log_file="$LOG_DIR/resources.log"
    while true; do
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%, Memory: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}'), Disk: $(df / | tail -1 | awk '{print $5}')" >> "$log_file"
        sleep 30
    done
}

# Start resource monitoring in background
monitor_resources &
MONITOR_PID=$!

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    kill $MONITOR_PID 2>/dev/null || true
    echo -e "${GREEN}Installation logs saved to: $LOG_DIR${NC}"
    echo -e "${GREEN}Main log file: $LOG_DIR/install.log${NC}"
    echo -e "${GREEN}Resource monitoring: $LOG_DIR/resources.log${NC}"
}

# Set up cleanup trap
trap cleanup EXIT

# Run the installation with output captured
echo -e "${GREEN}Starting installation...${NC}"
echo ""

# Run install.sh and capture both stdout and stderr
if bash -x install.sh 2>&1 | tee "$LOG_DIR/install.log"; then
    echo -e "\n${GREEN}=== Installation Completed Successfully ===${NC}"
    echo -e "${GREEN}Check the logs in: $LOG_DIR${NC}"
else
    echo -e "\n${RED}=== Installation Failed ===${NC}"
    echo -e "${RED}Check the logs in: $LOG_DIR${NC}"
    echo -e "${RED}Last 20 lines of log:${NC}"
    tail -20 "$LOG_DIR/install.log"
    exit 1
fi

# Show final status
echo -e "\n${BLUE}=== Installation Summary ===${NC}"
echo -e "${GREEN}✓ Installation completed${NC}"
echo -e "${GREEN}✓ Logs saved to: $LOG_DIR${NC}"
echo -e "${GREEN}✓ Next steps:${NC}"
echo "  1. Edit /opt/media-pipeline/.env with your credentials"
echo "  2. Run: /opt/media-pipeline/complete_setup.sh"
echo "  3. Access Web UI at: http://$(hostname -I | awk '{print $1}')"
echo "  4. Access Syncthing at: http://$(hostname -I | awk '{print $1}'):8384"
