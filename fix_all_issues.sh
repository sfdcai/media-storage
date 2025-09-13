#!/bin/bash

# Comprehensive Fix Script for All Installation Issues
# This script fixes all known issues with the media pipeline installation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Comprehensive Media Pipeline Fix ===${NC}"

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

echo -e "${GREEN}Fixing all known installation issues...${NC}"

# Fix 1: Log directory permissions
echo -e "${GREEN}1. Fixing log directory permissions...${NC}"
mkdir -p "$LOG_DIR"
chown "$SERVICE_USER:$SERVICE_USER" "$LOG_DIR"
chmod 755 "$LOG_DIR"

# Fix 2: Update configuration file
echo -e "${GREEN}2. Updating configuration file...${NC}"
if [ -f "$PROJECT_DIR/config.yaml" ]; then
    # Update log directory path
    sed -i 's|log_dir: "logs"|log_dir: "/var/log/media-pipeline"|g' "$PROJECT_DIR/config.yaml"
    
    # Ensure web UI port is 8081
    if ! grep -q "port: 8081" "$PROJECT_DIR/config.yaml"; then
        if grep -q "port: 8080" "$PROJECT_DIR/config.yaml"; then
            sed -i 's|port: 8080|port: 8081|g' "$PROJECT_DIR/config.yaml"
        else
            # Add web UI configuration if missing
            cat >> "$PROJECT_DIR/config.yaml" << 'EOF'

# Web UI configuration
web_ui:
  host: "127.0.0.1"
  port: 8081
  debug: false
  auto_reload: false
EOF
        fi
    fi
fi

# Fix 3: Python import issues
echo -e "${GREEN}3. Fixing Python import issues...${NC}"
if [ -f "$PROJECT_DIR/test_pipeline.py" ]; then
    # Check if Dict import is missing
    if ! grep -q "from typing import Dict" "$PROJECT_DIR/test_pipeline.py"; then
        # Create backup
        cp "$PROJECT_DIR/test_pipeline.py" "$PROJECT_DIR/test_pipeline.py.backup"
        
        # Add the missing import
        sed -i '12a from typing import Dict' "$PROJECT_DIR/test_pipeline.py"
        echo -e "${GREEN}✓ Added missing Dict import to test_pipeline.py${NC}"
    fi
fi

# Fix 4: Project directory permissions
echo -e "${GREEN}4. Fixing project directory permissions...${NC}"
chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR"
chmod -R 755 "$PROJECT_DIR"

# Fix 5: Ensure all required directories exist
echo -e "${GREEN}5. Creating required directories...${NC}"
mkdir -p "/mnt/wd_all_pictures/incoming"
mkdir -p "/mnt/wd_all_pictures/backup"
mkdir -p "/mnt/wd_all_pictures/compress"
mkdir -p "/mnt/wd_all_pictures/delete_pending"
mkdir -p "/mnt/wd_all_pictures/processed"
chown -R "$SERVICE_USER:$SERVICE_USER" "/mnt/wd_all_pictures"

# Fix 6: Test database initialization
echo -e "${GREEN}6. Testing database initialization...${NC}"
if sudo -u "$SERVICE_USER" "$PROJECT_DIR/venv/bin/python" "$PROJECT_DIR/test_pipeline.py"; then
    echo -e "${GREEN}✓ Database initialization successful!${NC}"
else
    echo -e "${RED}✗ Database initialization failed${NC}"
    echo -e "${YELLOW}Please check the error messages above${NC}"
    exit 1
fi

# Fix 7: Update systemd services with correct port
echo -e "${GREEN}7. Updating systemd services...${NC}"
if [ -f "/etc/systemd/system/media-pipeline-web.service" ]; then
    # Update the web service to use port 8081
    sed -i 's|127.0.0.1:8080|127.0.0.1:8081|g' "/etc/systemd/system/media-pipeline-web.service"
    systemctl daemon-reload
fi

# Fix 8: Update nginx configuration
echo -e "${GREEN}8. Updating nginx configuration...${NC}"
if [ -f "/etc/nginx/sites-available/media-pipeline" ]; then
    # Update nginx to proxy to port 8081
    sed -i 's|127.0.0.1:8080|127.0.0.1:8081|g' "/etc/nginx/sites-available/media-pipeline"
    systemctl reload nginx 2>/dev/null || true
fi

echo -e "${GREEN}✓ All issues fixed successfully!${NC}"
echo ""
echo -e "${BLUE}=== Service Ports ===${NC}"
echo -e "${YELLOW}VS Code Server:${NC}     http://\$(hostname -I | awk '{print \$1}'):8080"
echo -e "${YELLOW}Media Pipeline Web UI:${NC} http://\$(hostname -I | awk '{print \$1}'):8081"
echo -e "${YELLOW}Syncthing:${NC}          http://\$(hostname -I | awk '{print \$1}'):8384"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "${YELLOW}1. Edit $PROJECT_DIR/.env with your credentials${NC}"
echo -e "${YELLOW}2. Run: $PROJECT_DIR/complete_setup.sh${NC}"
echo -e "${YELLOW}3. Access Web UI at: http://\$(hostname -I | awk '{print \$1}'):8081${NC}"
echo ""
echo -e "${GREEN}🎉 Your media pipeline is ready to use! 🎉${NC}"
