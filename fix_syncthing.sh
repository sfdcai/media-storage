#!/bin/bash

# Fix Syncthing Script
# This script fixes Syncthing configuration and access issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Fixing Syncthing Configuration ===${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}This script must be run as root${NC}"
    echo "Please run: sudo $0"
    exit 1
fi

echo -e "${GREEN}Checking Syncthing status...${NC}"

# Check if Syncthing service is running
if systemctl is-active --quiet syncthing@media-pipeline; then
    echo -e "${GREEN}✓ Syncthing service is running${NC}"
else
    echo -e "${YELLOW}⚠ Syncthing service is not running, starting it...${NC}"
    systemctl start syncthing@media-pipeline
    sleep 3
fi

# Check if port 8384 is listening
if netstat -tlnp | grep -q ":8384 "; then
    echo -e "${GREEN}✓ Syncthing is listening on port 8384${NC}"
else
    echo -e "${RED}✗ Syncthing is not listening on port 8384${NC}"
    echo -e "${YELLOW}Checking Syncthing configuration...${NC}"
fi

# Get container IP
CONTAINER_IP=$(hostname -I | awk '{print $1}')

echo -e "${GREEN}Syncthing should be accessible at: http://$CONTAINER_IP:8384${NC}"

# Check Syncthing configuration
SYNCTHING_CONFIG_DIR="/home/media-pipeline/.config/syncthing"
SYNCTHING_CONFIG_FILE="$SYNCTHING_CONFIG_DIR/config.xml"

if [ -f "$SYNCTHING_CONFIG_FILE" ]; then
    echo -e "${GREEN}✓ Syncthing config file exists${NC}"
    
    # Check if GUI address is configured to listen on all interfaces
    if grep -q "0.0.0.0:8384" "$SYNCTHING_CONFIG_FILE"; then
        echo -e "${GREEN}✓ Syncthing is configured to listen on all interfaces${NC}"
    else
        echo -e "${YELLOW}⚠ Syncthing may not be configured to listen on all interfaces${NC}"
        echo -e "${YELLOW}Current GUI address configuration:${NC}"
        grep -A 1 -B 1 "gui" "$SYNCTHING_CONFIG_FILE" | grep "address"
    fi
else
    echo -e "${RED}✗ Syncthing config file not found${NC}"
    echo -e "${YELLOW}This might be the first time Syncthing is starting${NC}"
fi

# Check Syncthing logs
echo -e "${GREEN}Recent Syncthing logs:${NC}"
journalctl -u syncthing@media-pipeline --no-pager -n 10

echo ""
echo -e "${BLUE}=== Syncthing Troubleshooting ===${NC}"

# Test if we can connect to Syncthing
echo -e "${GREEN}Testing Syncthing connection...${NC}"
if curl -s --connect-timeout 5 "http://127.0.0.1:8384" > /dev/null; then
    echo -e "${GREEN}✓ Syncthing is responding locally${NC}"
else
    echo -e "${RED}✗ Syncthing is not responding locally${NC}"
fi

# Check if we can connect from outside
if curl -s --connect-timeout 5 "http://$CONTAINER_IP:8384" > /dev/null; then
    echo -e "${GREEN}✓ Syncthing is accessible from outside${NC}"
else
    echo -e "${YELLOW}⚠ Syncthing may not be accessible from outside${NC}"
    echo -e "${YELLOW}This could be due to firewall or network configuration${NC}"
fi

echo ""
echo -e "${BLUE}=== Syncthing Configuration Fix ===${NC}"

# Create a script to reconfigure Syncthing if needed
cat > /tmp/fix_syncthing_config.py << 'EOF'
#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import os
import shutil

config_file = "/home/media-pipeline/.config/syncthing/config.xml"
backup_file = "/home/media-pipeline/.config/syncthing/config.xml.backup"

if os.path.exists(config_file):
    # Backup original config
    shutil.copy2(config_file, backup_file)
    print("Backed up original config to:", backup_file)
    
    # Parse config
    tree = ET.parse(config_file)
    root = tree.getroot()
    
    # Find GUI element
    gui = root.find('gui')
    if gui is not None:
        # Update address to listen on all interfaces
        gui.set('address', '0.0.0.0:8384')
        print("Updated GUI address to 0.0.0.0:8384")
        
        # Save config
        tree.write(config_file)
        print("Configuration updated successfully")
    else:
        print("GUI element not found in config")
else:
    print("Config file not found:", config_file)
EOF

# Run the configuration fix
echo -e "${GREEN}Updating Syncthing configuration...${NC}"
python3 /tmp/fix_syncthing_config.py

# Restart Syncthing to apply changes
echo -e "${GREEN}Restarting Syncthing...${NC}"
systemctl restart syncthing@media-pipeline

# Wait for service to start
sleep 5

# Check status again
if systemctl is-active --quiet syncthing@media-pipeline; then
    echo -e "${GREEN}✓ Syncthing restarted successfully${NC}"
else
    echo -e "${RED}✗ Failed to restart Syncthing${NC}"
    echo -e "${YELLOW}Error details:${NC}"
    journalctl -u syncthing@media-pipeline --no-pager -n 5
fi

# Check port again
if netstat -tlnp | grep -q ":8384 "; then
    echo -e "${GREEN}✓ Syncthing is now listening on port 8384${NC}"
else
    echo -e "${RED}✗ Syncthing is still not listening on port 8384${NC}"
fi

echo ""
echo -e "${GREEN}=== Syncthing Fix Complete ===${NC}"
echo ""
echo -e "${BLUE}Access URLs:${NC}"
echo -e "${YELLOW}Syncthing: http://$CONTAINER_IP:8384${NC}"
echo -e "${YELLOW}Status Dashboard: http://$CONTAINER_IP:8082${NC}"
echo ""
echo -e "${BLUE}If Syncthing still doesn't work:${NC}"
echo -e "${YELLOW}1. Check firewall: ufw status${NC}"
echo -e "${YELLOW}2. Check logs: journalctl -u syncthing@media-pipeline -f${NC}"
echo -e "${YELLOW}3. Check config: cat /home/media-pipeline/.config/syncthing/config.xml${NC}"
echo ""
echo -e "${GREEN}🎉 Syncthing configuration updated! 🎉${NC}"

# Clean up
rm -f /tmp/fix_syncthing_config.py
