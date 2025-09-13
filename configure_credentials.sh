#!/bin/bash

# Configure Credentials Script
# This script helps configure all necessary credentials and environment variables

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Media Pipeline Credentials Configuration ===${NC}"

# Configuration
PROJECT_DIR="/opt/media-pipeline"
ENV_FILE="$PROJECT_DIR/.env"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}This script must be run as root${NC}"
    echo "Please run: sudo $0"
    exit 1
fi

echo -e "${GREEN}This script will help you configure all necessary credentials.${NC}"
echo -e "${YELLOW}Press Enter to skip any optional configuration.${NC}"
echo ""

# Create .env file if it doesn't exist
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${GREEN}Creating .env file...${NC}"
    touch "$ENV_FILE"
    chown media-pipeline:media-pipeline "$ENV_FILE"
    chmod 600 "$ENV_FILE"
fi

echo -e "${BLUE}=== iCloud Configuration ===${NC}"
echo -e "${YELLOW}iCloud credentials are required for downloading photos from iCloud.${NC}"
echo ""

# iCloud Username
read -p "Enter your iCloud email address (or press Enter to skip): " ICLOUD_USERNAME
if [ ! -z "$ICLOUD_USERNAME" ]; then
    # Remove existing ICLOUD_USERNAME line if it exists
    sed -i '/^ICLOUD_USERNAME=/d' "$ENV_FILE"
    echo "ICLOUD_USERNAME=$ICLOUD_USERNAME" >> "$ENV_FILE"
    echo -e "${GREEN}✓ iCloud username configured${NC}"
fi

# iCloud Password
read -p "Enter your iCloud password (or press Enter to skip): " ICLOUD_PASSWORD
if [ ! -z "$ICLOUD_PASSWORD" ]; then
    # Remove existing ICLOUD_PASSWORD line if it exists
    sed -i '/^ICLOUD_PASSWORD=/d' "$ENV_FILE"
    echo "ICLOUD_PASSWORD=$ICLOUD_PASSWORD" >> "$ENV_FILE"
    echo -e "${GREEN}✓ iCloud password configured${NC}"
fi

echo ""
echo -e "${BLUE}=== Syncthing Configuration ===${NC}"
echo -e "${YELLOW}Syncthing API key is required for the media pipeline to communicate with Syncthing.${NC}"
echo ""

# Get Syncthing API key
echo -e "${GREEN}To get your Syncthing API key:${NC}"
echo -e "${YELLOW}1. Open Syncthing web UI: http://$(hostname -I | awk '{print $1}'):8384${NC}"
echo -e "${YELLOW}2. Go to Actions → Settings → GUI${NC}"
echo -e "${YELLOW}3. Copy the API Key${NC}"
echo ""

read -p "Enter your Syncthing API key (or press Enter to skip): " SYNCTHING_API_KEY
if [ ! -z "$SYNCTHING_API_KEY" ]; then
    # Remove existing SYNCTHING_API_KEY line if it exists
    sed -i '/^SYNCTHING_API_KEY=/d' "$ENV_FILE"
    echo "SYNCTHING_API_KEY=$SYNCTHING_API_KEY" >> "$ENV_FILE"
    echo -e "${GREEN}✓ Syncthing API key configured${NC}"
fi

echo ""
echo -e "${BLUE}=== Telegram Notifications (Optional) ===${NC}"
echo -e "${YELLOW}Telegram notifications are optional but useful for monitoring.${NC}"
echo ""

# Telegram Bot Token
read -p "Enter your Telegram bot token (or press Enter to skip): " TELEGRAM_BOT_TOKEN
if [ ! -z "$TELEGRAM_BOT_TOKEN" ]; then
    # Remove existing TELEGRAM_BOT_TOKEN line if it exists
    sed -i '/^TELEGRAM_BOT_TOKEN=/d' "$ENV_FILE"
    echo "TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN" >> "$ENV_FILE"
    echo -e "${GREEN}✓ Telegram bot token configured${NC}"
fi

# Telegram Chat ID
read -p "Enter your Telegram chat ID (or press Enter to skip): " TELEGRAM_CHAT_ID
if [ ! -z "$TELEGRAM_CHAT_ID" ]; then
    # Remove existing TELEGRAM_CHAT_ID line if it exists
    sed -i '/^TELEGRAM_CHAT_ID=/d' "$ENV_FILE"
    echo "TELEGRAM_CHAT_ID=$TELEGRAM_CHAT_ID" >> "$ENV_FILE"
    echo -e "${GREEN}✓ Telegram chat ID configured${NC}"
fi

echo ""
echo -e "${BLUE}=== Directory Configuration ===${NC}"
echo -e "${YELLOW}Configure the directories where media will be stored.${NC}"
echo ""

# Incoming directory
read -p "Enter incoming directory path (default: /mnt/wd_all_pictures/incoming): " INCOMING_DIR
if [ -z "$INCOMING_DIR" ]; then
    INCOMING_DIR="/mnt/wd_all_pictures/incoming"
fi
# Remove existing INCOMING_DIR line if it exists
sed -i '/^INCOMING_DIR=/d' "$ENV_FILE"
echo "INCOMING_DIR=$INCOMING_DIR" >> "$ENV_FILE"
echo -e "${GREEN}✓ Incoming directory: $INCOMING_DIR${NC}"

# Processed directory
read -p "Enter processed directory path (default: /mnt/wd_all_pictures/processed): " PROCESSED_DIR
if [ -z "$PROCESSED_DIR" ]; then
    PROCESSED_DIR="/mnt/wd_all_pictures/processed"
fi
# Remove existing PROCESSED_DIR line if it exists
sed -i '/^PROCESSED_DIR=/d' "$ENV_FILE"
echo "PROCESSED_DIR=$PROCESSED_DIR" >> "$ENV_FILE"
echo -e "${GREEN}✓ Processed directory: $PROCESSED_DIR${NC}"

# Create directories if they don't exist
echo -e "${GREEN}Creating directories...${NC}"
mkdir -p "$INCOMING_DIR" "$PROCESSED_DIR"
chown -R media-pipeline:media-pipeline "$INCOMING_DIR" "$PROCESSED_DIR"
chmod 755 "$INCOMING_DIR" "$PROCESSED_DIR"

echo ""
echo -e "${BLUE}=== Final Configuration ===${NC}"

# Set file permissions
chown media-pipeline:media-pipeline "$ENV_FILE"
chmod 600 "$ENV_FILE"

echo -e "${GREEN}✓ Environment file configured: $ENV_FILE${NC}"
echo -e "${GREEN}✓ File permissions set${NC}"

echo ""
echo -e "${GREEN}=== Configuration Complete! ===${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "${YELLOW}1. Restart services: systemctl restart media-pipeline${NC}"
echo -e "${YELLOW}2. Check status: systemctl status media-pipeline${NC}"
echo -e "${YELLOW}3. View logs: journalctl -u media-pipeline -f${NC}"
echo ""
echo -e "${BLUE}Access URLs:${NC}"
echo -e "${YELLOW}Status Dashboard: http://$(hostname -I | awk '{print $1}'):8082${NC}"
echo -e "${YELLOW}Syncthing: http://$(hostname -I | awk '{print $1}'):8384${NC}"
echo -e "${YELLOW}Media Pipeline Web UI: http://$(hostname -I | awk '{print $1}'):8081${NC}"
echo ""
echo -e "${GREEN}🎉 Configuration completed successfully! 🎉${NC}"