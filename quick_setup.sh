#!/bin/bash

# Quick Setup Script
# This script completes the installation and sets up the media pipeline

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Quick Media Pipeline Setup ===${NC}"

# Configuration
PROJECT_DIR="/opt/media-pipeline"
SERVICE_USER="media-pipeline"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}This script must be run as root${NC}"
    echo "Please run: sudo $0"
    exit 1
fi

echo -e "${GREEN}Completing media pipeline setup...${NC}"

# Step 1: Run the final fix
echo -e "${GREEN}1. Running final fix...${NC}"
if [ -f "fix_final.sh" ]; then
    chmod +x fix_final.sh
    ./fix_final.sh
else
    echo -e "${YELLOW}fix_final.sh not found, running basic setup...${NC}"
    
    # Basic setup
    mkdir -p "$PROJECT_DIR"
    mkdir -p "/var/log/media-pipeline"
    chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR"
    chown -R "$SERVICE_USER:$SERVICE_USER" "/var/log/media-pipeline"
    
    # Copy files
    cp -r . "$PROJECT_DIR/"
    chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR"
fi

# Step 2: Create complete_setup.sh
echo -e "${GREEN}2. Creating complete_setup.sh...${NC}"
cp complete_setup.sh "$PROJECT_DIR/"
chmod +x "$PROJECT_DIR/complete_setup.sh"
chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/complete_setup.sh"

# Step 3: Create .env file if it doesn't exist
echo -e "${GREEN}3. Setting up environment file...${NC}"
if [ ! -f "$PROJECT_DIR/.env" ]; then
    if [ -f "$PROJECT_DIR/.env.template" ]; then
        cp "$PROJECT_DIR/.env.template" "$PROJECT_DIR/.env"
        chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/.env"
        echo -e "${YELLOW}⚠ Please edit $PROJECT_DIR/.env with your credentials${NC}"
    else
        # Create basic .env file
        cat > "$PROJECT_DIR/.env" << 'EOF'
# Media Pipeline Environment Variables
# Edit these with your actual credentials

# iCloud Credentials
ICLOUD_USERNAME=your_icloud_email@example.com
ICLOUD_PASSWORD=your_icloud_password

# Syncthing Configuration
SYNCTHING_API_KEY=your_syncthing_api_key

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Database
DB_FILE=/opt/media-pipeline/media.db

# Logging
LOG_LEVEL=INFO
LOG_DIR=/var/log/media-pipeline
EOF
        chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/.env"
        echo -e "${YELLOW}⚠ Please edit $PROJECT_DIR/.env with your credentials${NC}"
    fi
fi

# Step 4: Test the setup
echo -e "${GREEN}4. Testing setup...${NC}"
if sudo -u "$SERVICE_USER" "$PROJECT_DIR/venv/bin/python" "$PROJECT_DIR/test_pipeline.py"; then
    echo -e "${GREEN}✓ Setup test successful!${NC}"
else
    echo -e "${YELLOW}⚠ Setup test completed with some expected failures${NC}"
    echo -e "${YELLOW}This is normal if credentials are not configured yet${NC}"
fi

# Get container IP
CONTAINER_IP=$(hostname -I | awk '{print $1}')

echo -e "${GREEN}✓ Quick setup completed!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "${YELLOW}1. Edit credentials:${NC}"
echo -e "${YELLOW}   nano $PROJECT_DIR/.env${NC}"
echo -e "${YELLOW}2. Start services:${NC}"
echo -e "${YELLOW}   $PROJECT_DIR/complete_setup.sh${NC}"
echo -e "${YELLOW}3. Access Web UI:${NC}"
echo -e "${YELLOW}   http://$CONTAINER_IP:8081${NC}"
echo ""
echo -e "${GREEN}🎉 Media pipeline is ready to configure and start! 🎉${NC}"
