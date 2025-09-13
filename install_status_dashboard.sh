#!/bin/bash

# Install Status Dashboard Script
# This script installs the standalone status dashboard

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Installing Media Pipeline Status Dashboard ===${NC}"

# Configuration
PROJECT_DIR="/opt/media-pipeline"
SERVICE_USER="media-pipeline"
DASHBOARD_PORT="8082"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}This script must be run as root${NC}"
    echo "Please run: sudo $0"
    exit 1
fi

echo -e "${GREEN}Installing status dashboard...${NC}"

# Install required Python packages
echo -e "${GREEN}Installing Python packages...${NC}"
if [ -f "$PROJECT_DIR/venv/bin/pip" ]; then
    sudo -u "$SERVICE_USER" "$PROJECT_DIR/venv/bin/pip" install flask flask-socketio
else
    pip3 install flask flask-socketio
fi

# Copy dashboard script
echo -e "${GREEN}Installing dashboard script...${NC}"
cp web_status_dashboard.py "$PROJECT_DIR/"
chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/web_status_dashboard.py"
chmod +x "$PROJECT_DIR/web_status_dashboard.py"

# Create systemd service for status dashboard
echo -e "${GREEN}Creating systemd service...${NC}"
cat > /etc/systemd/system/media-pipeline-status.service << EOF
[Unit]
Description=Media Pipeline Status Dashboard
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/web_status_dashboard.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$PROJECT_DIR $LOG_DIR

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
echo -e "${GREEN}Enabling status dashboard service...${NC}"
systemctl daemon-reload
systemctl enable media-pipeline-status

# Start the status dashboard
echo -e "${GREEN}Starting status dashboard...${NC}"
systemctl start media-pipeline-status

# Wait for service to start
sleep 3

# Check if service is running
if systemctl is-active --quiet media-pipeline-status; then
    echo -e "${GREEN}✓ Status dashboard started successfully${NC}"
else
    echo -e "${RED}✗ Failed to start status dashboard${NC}"
    echo -e "${YELLOW}Error details:${NC}"
    journalctl -u media-pipeline-status --no-pager -n 5
    exit 1
fi

# Check if port is listening
if netstat -tlnp | grep -q ":$DASHBOARD_PORT "; then
    echo -e "${GREEN}✓ Status dashboard is listening on port $DASHBOARD_PORT${NC}"
else
    echo -e "${YELLOW}⚠ Status dashboard port not detected${NC}"
fi

# Get container IP
CONTAINER_IP=$(hostname -I | awk '{print $1}')

echo ""
echo -e "${GREEN}=== Status Dashboard Installed Successfully! ===${NC}"
echo ""
echo -e "${BLUE}Access URLs:${NC}"
echo -e "${YELLOW}Status Dashboard:${NC} http://$CONTAINER_IP:$DASHBOARD_PORT"
echo -e "${YELLOW}VS Code Server:${NC} http://$CONTAINER_IP:8080"
echo -e "${YELLOW}Media Pipeline Web UI:${NC} http://$CONTAINER_IP:8081"
echo -e "${YELLOW}Syncthing:${NC} http://$CONTAINER_IP:8384"
echo ""
echo -e "${BLUE}Service Management:${NC}"
echo -e "${YELLOW}Check status:${NC} systemctl status media-pipeline-status"
echo -e "${YELLOW}View logs:${NC} journalctl -u media-pipeline-status -f"
echo -e "${YELLOW}Restart:${NC} systemctl restart media-pipeline-status"
echo ""
echo -e "${GREEN}🎉 Status Dashboard is ready! 🎉${NC}"
echo -e "${GREEN}You can now monitor all services even when they're not running!${NC}"
