#!/bin/bash

# Complete Setup Script - Fixed Version
# This script addresses all the issues and provides a complete setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Media Pipeline Complete Setup - Fixed Version ===${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}This script must be run as root${NC}"
    echo "Please run: $0"
    exit 1
fi

# Configuration
PROJECT_DIR="/opt/media-pipeline"
SERVICE_USER="media-pipeline"
CONTAINER_IP=$(hostname -I | awk '{print $1}')

echo -e "${GREEN}Container IP: $CONTAINER_IP${NC}"
echo ""

echo -e "${BLUE}=== Step 1: Install Required Packages ===${NC}"

# Install systemd and other required packages
echo -e "${GREEN}Installing required packages...${NC}"
apt update
apt install -y systemd systemd-sysv net-tools curl wget

# Install Python packages for web interfaces
echo -e "${GREEN}Installing Python packages...${NC}"
if [ -f "$PROJECT_DIR/venv/bin/pip" ]; then
    $PROJECT_DIR/venv/bin/pip install flask flask-socketio requests
else
    pip3 install flask flask-socketio requests
fi

echo -e "${GREEN}✓ Required packages installed${NC}"

echo ""
echo -e "${BLUE}=== Step 2: Fix Status Dashboard ===${NC}"

# Copy updated dashboard script
echo -e "${GREEN}Updating status dashboard...${NC}"
cp web_status_dashboard.py "$PROJECT_DIR/"
chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/web_status_dashboard.py"
chmod +x "$PROJECT_DIR/web_status_dashboard.py"

# Create systemd service for status dashboard
echo -e "${GREEN}Creating status dashboard service...${NC}"
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
ReadWritePaths=$PROJECT_DIR /var/log/media-pipeline

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
systemctl daemon-reload
systemctl enable media-pipeline-status
systemctl start media-pipeline-status

echo -e "${GREEN}✓ Status dashboard service created and started${NC}"

echo ""
echo -e "${BLUE}=== Step 3: Create Web Configuration Interface ===${NC}"

# Copy configuration interface script
echo -e "${GREEN}Installing configuration interface...${NC}"
cp web_config_interface.py "$PROJECT_DIR/"
chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/web_config_interface.py"
chmod +x "$PROJECT_DIR/web_config_interface.py"

# Create systemd service for configuration interface
echo -e "${GREEN}Creating configuration interface service...${NC}"
cat > /etc/systemd/system/media-pipeline-config.service << EOF
[Unit]
Description=Media Pipeline Configuration Interface
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/web_config_interface.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$PROJECT_DIR /var/log/media-pipeline

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
systemctl daemon-reload
systemctl enable media-pipeline-config
systemctl start media-pipeline-config

echo -e "${GREEN}✓ Configuration interface service created and started${NC}"

echo ""
echo -e "${BLUE}=== Step 4: Configure Syncthing ===${NC}"

# Check if Syncthing is running
if systemctl is-active --quiet syncthing@media-pipeline; then
    echo -e "${GREEN}✓ Syncthing service is running${NC}"
else
    echo -e "${YELLOW}⚠ Starting Syncthing service...${NC}"
    systemctl start syncthing@media-pipeline
    sleep 3
fi

# Fix Syncthing configuration to listen on all interfaces
echo -e "${GREEN}Configuring Syncthing to listen on all interfaces...${NC}"
SYNCTHING_CONFIG_DIR="/home/media-pipeline/.config/syncthing"
SYNCTHING_CONFIG_FILE="$SYNCTHING_CONFIG_DIR/config.xml"

if [ -f "$SYNCTHING_CONFIG_FILE" ]; then
    # Backup original config
    cp "$SYNCTHING_CONFIG_FILE" "$SYNCTHING_CONFIG_FILE.backup"
    
    # Update GUI address to listen on all interfaces
    sed -i 's/address="127.0.0.1:8384"/address="0.0.0.0:8384"/g' "$SYNCTHING_CONFIG_FILE"
    
    # Restart Syncthing to apply changes
    systemctl restart syncthing@media-pipeline
    sleep 3
    
    echo -e "${GREEN}✓ Syncthing configured to listen on all interfaces${NC}"
else
    echo -e "${YELLOW}⚠ Syncthing config file not found, it will be created on first run${NC}"
fi

echo ""
echo -e "${BLUE}=== Step 5: Create Environment File Template ===${NC}"

# Create .env file template
echo -e "${GREEN}Creating environment file template...${NC}"
cat > "$PROJECT_DIR/.env" << EOF
# Media Pipeline Environment Configuration
# Generated on $(date)

# iCloud Configuration
# Note: 2FA will be handled automatically by icloudpd on first run
ICLOUD_USERNAME=
ICLOUD_PASSWORD=

# Syncthing Configuration
# Use local Syncthing (this container) or remote Syncthing server
SYNCTHING_URL=http://$CONTAINER_IP:8384/rest
SYNCTHING_API_KEY=

# Telegram Notifications (Optional)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Directory Configuration
INCOMING_DIR=/mnt/wd_all_pictures/incoming
PROCESSED_DIR=/mnt/wd_all_pictures/processed
EOF

chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/.env"
chmod 600 "$PROJECT_DIR/.env"

echo -e "${GREEN}✓ Environment file template created${NC}"

echo ""
echo -e "${BLUE}=== Step 6: Create Required Directories ===${NC}"

# Create required directories
echo -e "${GREEN}Creating required directories...${NC}"
mkdir -p /mnt/wd_all_pictures/incoming
mkdir -p /mnt/wd_all_pictures/processed
mkdir -p /var/log/media-pipeline

# Set ownership
chown -R "$SERVICE_USER:$SERVICE_USER" /mnt/wd_all_pictures
chown -R "$SERVICE_USER:$SERVICE_USER" /var/log/media-pipeline

echo -e "${GREEN}✓ Required directories created${NC}"

echo ""
echo -e "${BLUE}=== Step 7: Start All Services ===${NC}"

# Start all services
echo -e "${GREEN}Starting all services...${NC}"
systemctl start media-pipeline-status
systemctl start media-pipeline-config
systemctl start syncthing@media-pipeline
systemctl start nginx

# Wait for services to start
sleep 5

echo -e "${GREEN}✓ All services started${NC}"

echo ""
echo -e "${BLUE}=== Step 8: Verify Services ===${NC}"

# Check service status
echo -e "${GREEN}Checking service status...${NC}"
services=("media-pipeline-status" "media-pipeline-config" "syncthing@media-pipeline" "nginx")
for service in "${services[@]}"; do
    if systemctl is-active --quiet "$service"; then
        echo -e "${GREEN}✓ $service: ACTIVE${NC}"
    else
        echo -e "${RED}✗ $service: INACTIVE${NC}"
    fi
done

# Check ports
echo -e "${GREEN}Checking ports...${NC}"
ports=("8080" "8081" "8082" "8083" "8384")
for port in "${ports[@]}"; do
    if netstat -tlnp | grep -q ":$port "; then
        echo -e "${GREEN}✓ Port $port: LISTENING${NC}"
    else
        echo -e "${YELLOW}⚠ Port $port: NOT LISTENING${NC}"
    fi
done

echo ""
echo -e "${GREEN}=== Setup Complete! ===${NC}"
echo ""
echo -e "${BLUE}Access URLs:${NC}"
echo -e "${YELLOW}Status Dashboard:${NC} http://$CONTAINER_IP:8082"
echo -e "${YELLOW}Configuration Interface:${NC} http://$CONTAINER_IP:8083"
echo -e "${YELLOW}Syncthing:${NC} http://$CONTAINER_IP:8384"
echo -e "${YELLOW}VS Code Server:${NC} http://$CONTAINER_IP:8080"
echo -e "${YELLOW}Media Pipeline Web UI:${NC} http://$CONTAINER_IP:8081"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo -e "${YELLOW}1. Open Configuration Interface: http://$CONTAINER_IP:8083${NC}"
echo -e "${YELLOW}2. Configure iCloud credentials (2FA will be handled automatically)${NC}"
echo -e "${YELLOW}3. Configure Syncthing (local or remote server)${NC}"
echo -e "${YELLOW}4. Use Status Dashboard to monitor everything: http://$CONTAINER_IP:8082${NC}"
echo ""
echo -e "${BLUE}Important Notes:${NC}"
echo -e "${YELLOW}• iCloud 2FA: icloudpd will handle 2FA automatically on first run${NC}"
echo -e "${YELLOW}• Syncthing: You can use local (this container) or remote (192.168.1.118)${NC}"
echo -e "${YELLOW}• Configuration: Use the web interface at port 8083${NC}"
echo -e "${YELLOW}• Monitoring: Use the status dashboard at port 8082${NC}"
echo ""
echo -e "${GREEN}🎉 Setup completed successfully! 🎉${NC}"
echo -e "${GREEN}Use the Configuration Interface to set up your credentials!${NC}"
