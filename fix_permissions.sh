#!/bin/bash

# Quick Fix Script for Permission Issues
# This script fixes the permission issues in the current installation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Fixing Permission Issues ===${NC}"

# Configuration
PROJECT_DIR="/opt/media-pipeline"
SERVICE_USER="media-pipeline"
LOG_DIR="/var/log/media-pipeline"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}This script must be run as root${NC}"
    echo "Please run: sudo $0"
    exit 1
fi

echo -e "${GREEN}Fixing log directory permissions...${NC}"

# Create log directory with proper permissions
mkdir -p "$LOG_DIR"
chown "$SERVICE_USER:$SERVICE_USER" "$LOG_DIR"
chmod 755 "$LOG_DIR"

echo -e "${GREEN}Updating configuration file...${NC}"

# Update the config.yaml to use absolute path
sed -i 's|log_dir: "logs"|log_dir: "/var/log/media-pipeline"|g' "$PROJECT_DIR/config.yaml"

echo -e "${GREEN}Fixing project directory permissions...${NC}"

# Ensure all project files have correct ownership
chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR"
chmod -R 755 "$PROJECT_DIR"

echo -e "${GREEN}Testing database initialization...${NC}"

# Try to initialize the database again
if sudo -u "$SERVICE_USER" "$PROJECT_DIR/venv/bin/python" "$PROJECT_DIR/test_pipeline.py"; then
    echo -e "${GREEN}✓ Database initialization successful!${NC}"
else
    echo -e "${RED}✗ Database initialization failed${NC}"
    echo -e "${YELLOW}Please check the error messages above${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Permission issues fixed successfully!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "${YELLOW}1. Edit $PROJECT_DIR/.env with your credentials${NC}"
echo -e "${YELLOW}2. Run: $PROJECT_DIR/complete_setup.sh${NC}"
echo -e "${YELLOW}3. Access Web UI at: http://\$(hostname -I | awk '{print \$1}'):8081${NC}"
echo ""
echo -e "${GREEN}🎉 Your media pipeline is ready to use! 🎉${NC}"
