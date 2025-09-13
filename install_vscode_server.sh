#!/bin/bash

# VS Code Server Installation Script for Headless LXC Container
# This provides a web-based VS Code experience - PERFECT for headless containers!

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== VS Code Server Installation for Headless LXC ===${NC}"
echo -e "${GREEN}This is the PERFECT solution for headless containers!${NC}"
echo -e "${GREEN}Access VS Code through your web browser from any device.${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}This script must be run as root${NC}"
    echo "Please run: sudo $0"
    exit 1
fi

# Install VS Code Server
echo -e "${GREEN}Installing VS Code Server...${NC}"

# Download and install VS Code Server
curl -fsSL https://code-server.dev/install.sh | sh

# Create systemd service for VS Code Server
echo -e "${GREEN}Creating VS Code Server systemd service...${NC}"
cat > /etc/systemd/system/code-server.service << 'EOF'
[Unit]
Description=VS Code Server
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/root
Environment=PASSWORD=your_password_here
ExecStart=/usr/bin/code-server --bind-addr 0.0.0.0:8080 --auth password
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Get container IP
CONTAINER_IP=$(hostname -I | awk '{print $1}')

echo -e "${GREEN}=== VS Code Server Setup Complete ===${NC}"
echo -e "${GREEN}VS Code Server will be available at: http://$CONTAINER_IP:8080${NC}"
echo ""
echo -e "${BLUE}🎉 PERFECT for Headless LXC! 🎉${NC}"
echo -e "${GREEN}✅ No GUI required - runs in your web browser${NC}"
echo -e "${GREEN}✅ Access from any device (Windows, Mac, Linux, mobile)${NC}"
echo -e "${GREEN}✅ Full VS Code experience with extensions${NC}"
echo -e "${GREEN}✅ Terminal access built-in${NC}"
echo ""
echo -e "${YELLOW}IMPORTANT: Before starting the service, edit the password:${NC}"
echo -e "${YELLOW}1. Edit /etc/systemd/system/code-server.service${NC}"
echo -e "${YELLOW}2. Change 'your_password_here' to your desired password${NC}"
echo -e "${YELLOW}3. Run: systemctl daemon-reload${NC}"
echo -e "${YELLOW}4. Run: systemctl enable code-server${NC}"
echo -e "${YELLOW}5. Run: systemctl start code-server${NC}"
echo ""
echo -e "${BLUE}Quick Setup Commands:${NC}"
echo -e "${YELLOW}nano /etc/systemd/system/code-server.service${NC}"
echo -e "${YELLOW}systemctl daemon-reload && systemctl enable code-server && systemctl start code-server${NC}"
echo ""
echo -e "${BLUE}Then access from your browser:${NC}"
echo -e "${GREEN}http://$CONTAINER_IP:8080${NC}"
