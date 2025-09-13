#!/bin/bash

# Service Diagnosis Script
# This script checks the status of all media pipeline services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Media Pipeline Service Diagnosis ===${NC}"
echo ""

# Configuration
PROJECT_DIR="/opt/media-pipeline"
SERVICE_USER="media-pipeline"
WEB_PORT="8081"
SYNCTHING_PORT="8384"

# Get container IP
CONTAINER_IP=$(hostname -I | awk '{print $1}')

echo -e "${GREEN}System Information:${NC}"
echo -e "${YELLOW}Container IP:${NC} $CONTAINER_IP"
echo -e "${YELLOW}Web UI Port:${NC} $WEB_PORT"
echo -e "${YELLOW}Syncthing Port:${NC} $SYNCTHING_PORT"
echo ""

# Check 1: Service Status
echo -e "${BLUE}=== 1. Service Status ===${NC}"

# Check Media Pipeline service
echo -e "${GREEN}Media Pipeline Service:${NC}"
if systemctl is-active --quiet media-pipeline; then
    echo -e "${GREEN}✓ Status: ACTIVE${NC}"
else
    echo -e "${RED}✗ Status: INACTIVE${NC}"
fi
systemctl status media-pipeline --no-pager -l
echo ""

# Check Media Pipeline Web UI service
echo -e "${GREEN}Media Pipeline Web UI Service:${NC}"
if systemctl is-active --quiet media-pipeline-web; then
    echo -e "${GREEN}✓ Status: ACTIVE${NC}"
else
    echo -e "${RED}✗ Status: INACTIVE${NC}"
fi
systemctl status media-pipeline-web --no-pager -l
echo ""

# Check Syncthing service
echo -e "${GREEN}Syncthing Service:${NC}"
if systemctl is-active --quiet syncthing@$SERVICE_USER; then
    echo -e "${GREEN}✓ Status: ACTIVE${NC}"
else
    echo -e "${RED}✗ Status: INACTIVE${NC}"
fi
systemctl status syncthing@$SERVICE_USER --no-pager -l
echo ""

# Check Nginx service
echo -e "${GREEN}Nginx Service:${NC}"
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Status: ACTIVE${NC}"
else
    echo -e "${RED}✗ Status: INACTIVE${NC}"
fi
systemctl status nginx --no-pager -l
echo ""

# Check 2: Port Listening
echo -e "${BLUE}=== 2. Port Listening Status ===${NC}"

# Check Web UI port
echo -e "${GREEN}Web UI Port ($WEB_PORT):${NC}"
if netstat -tlnp | grep -q ":$WEB_PORT "; then
    echo -e "${GREEN}✓ Port $WEB_PORT is listening${NC}"
    netstat -tlnp | grep ":$WEB_PORT "
else
    echo -e "${RED}✗ Port $WEB_PORT is NOT listening${NC}"
fi
echo ""

# Check Syncthing port
echo -e "${GREEN}Syncthing Port ($SYNCTHING_PORT):${NC}"
if netstat -tlnp | grep -q ":$SYNCTHING_PORT "; then
    echo -e "${GREEN}✓ Port $SYNCTHING_PORT is listening${NC}"
    netstat -tlnp | grep ":$SYNCTHING_PORT "
else
    echo -e "${RED}✗ Port $SYNCTHING_PORT is NOT listening${NC}"
fi
echo ""

# Check 3: Process Status
echo -e "${BLUE}=== 3. Process Status ===${NC}"

# Check Python processes
echo -e "${GREEN}Python Processes:${NC}"
ps aux | grep python | grep -v grep || echo -e "${RED}No Python processes found${NC}"
echo ""

# Check Syncthing processes
echo -e "${GREEN}Syncthing Processes:${NC}"
ps aux | grep syncthing | grep -v grep || echo -e "${RED}No Syncthing processes found${NC}"
echo ""

# Check 4: Log Files
echo -e "${BLUE}=== 4. Recent Logs ===${NC}"

# Check Media Pipeline logs
echo -e "${GREEN}Media Pipeline Logs (last 10 lines):${NC}"
journalctl -u media-pipeline --no-pager -n 10 || echo -e "${RED}No logs found${NC}"
echo ""

# Check Web UI logs
echo -e "${GREEN}Web UI Logs (last 10 lines):${NC}"
journalctl -u media-pipeline-web --no-pager -n 10 || echo -e "${RED}No logs found${NC}"
echo ""

# Check Syncthing logs
echo -e "${GREEN}Syncthing Logs (last 10 lines):${NC}"
journalctl -u syncthing@$SERVICE_USER --no-pager -n 10 || echo -e "${RED}No logs found${NC}"
echo ""

# Check 5: Configuration Files
echo -e "${BLUE}=== 5. Configuration Check ===${NC}"

# Check if .env file exists
echo -e "${GREEN}Environment File:${NC}"
if [ -f "$PROJECT_DIR/.env" ]; then
    echo -e "${GREEN}✓ .env file exists${NC}"
    echo -e "${YELLOW}First few lines:${NC}"
    head -5 "$PROJECT_DIR/.env"
else
    echo -e "${RED}✗ .env file missing${NC}"
fi
echo ""

# Check if config.yaml exists
echo -e "${GREEN}Configuration File:${NC}"
if [ -f "$PROJECT_DIR/config.yaml" ]; then
    echo -e "${GREEN}✓ config.yaml exists${NC}"
    echo -e "${YELLOW}Web UI port in config:${NC}"
    grep -A 3 "web_ui:" "$PROJECT_DIR/config.yaml" || echo -e "${RED}Web UI config not found${NC}"
else
    echo -e "${RED}✗ config.yaml missing${NC}"
fi
echo ""

# Check 6: Network Connectivity
echo -e "${BLUE}=== 6. Network Connectivity ===${NC}"

# Test local connectivity
echo -e "${GREEN}Local Connectivity Test:${NC}"
if curl -s --connect-timeout 5 http://127.0.0.1:$WEB_PORT > /dev/null; then
    echo -e "${GREEN}✓ Web UI responds on localhost:$WEB_PORT${NC}"
else
    echo -e "${RED}✗ Web UI does not respond on localhost:$WEB_PORT${NC}"
fi

if curl -s --connect-timeout 5 http://127.0.0.1:$SYNCTHING_PORT > /dev/null; then
    echo -e "${GREEN}✓ Syncthing responds on localhost:$SYNCTHING_PORT${NC}"
else
    echo -e "${RED}✗ Syncthing does not respond on localhost:$SYNCTHING_PORT${NC}"
fi
echo ""

# Check 7: File Permissions
echo -e "${BLUE}=== 7. File Permissions ===${NC}"

echo -e "${GREEN}Project Directory Permissions:${NC}"
ls -la "$PROJECT_DIR" | head -5
echo ""

echo -e "${GREEN}Log Directory Permissions:${NC}"
ls -la "/var/log/media-pipeline" 2>/dev/null || echo -e "${RED}Log directory not found${NC}"
echo ""

# Summary and Recommendations
echo -e "${BLUE}=== Summary and Recommendations ===${NC}"

# Count active services
ACTIVE_SERVICES=0
if systemctl is-active --quiet media-pipeline; then ACTIVE_SERVICES=$((ACTIVE_SERVICES + 1)); fi
if systemctl is-active --quiet media-pipeline-web; then ACTIVE_SERVICES=$((ACTIVE_SERVICES + 1)); fi
if systemctl is-active --quiet syncthing@$SERVICE_USER; then ACTIVE_SERVICES=$((ACTIVE_SERVICES + 1)); fi
if systemctl is-active --quiet nginx; then ACTIVE_SERVICES=$((ACTIVE_SERVICES + 1)); fi

echo -e "${GREEN}Active Services: $ACTIVE_SERVICES/4${NC}"

if [ $ACTIVE_SERVICES -eq 4 ]; then
    echo -e "${GREEN}🎉 All services are running!${NC}"
    echo -e "${YELLOW}If you still can't access the web UI, check firewall settings.${NC}"
elif [ $ACTIVE_SERVICES -eq 0 ]; then
    echo -e "${RED}❌ No services are running. Try restarting them.${NC}"
    echo -e "${YELLOW}Run: systemctl restart media-pipeline media-pipeline-web syncthing@$SERVICE_USER nginx${NC}"
else
    echo -e "${YELLOW}⚠ Some services are not running. Check the logs above for details.${NC}"
fi

echo ""
echo -e "${BLUE}Quick Fix Commands:${NC}"
echo -e "${YELLOW}Restart all services:${NC} systemctl restart media-pipeline media-pipeline-web syncthing@$SERVICE_USER nginx"
echo -e "${YELLOW}Check logs:${NC} journalctl -u media-pipeline -f"
echo -e "${YELLOW}Test web UI:${NC} curl http://127.0.0.1:$WEB_PORT"
echo -e "${YELLOW}Test Syncthing:${NC} curl http://127.0.0.1:$SYNCTHING_PORT"
echo ""
echo -e "${GREEN}Access URLs:${NC}"
echo -e "${YELLOW}Web UI:${NC} http://$CONTAINER_IP:$WEB_PORT"
echo -e "${YELLOW}Syncthing:${NC} http://$CONTAINER_IP:$SYNCTHING_PORT"
