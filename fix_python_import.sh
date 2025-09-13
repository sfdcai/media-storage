#!/bin/bash

# Quick Fix Script for Python Import Error
# This script fixes the missing Dict import in test_pipeline.py

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Fixing Python Import Error ===${NC}"

# Configuration
PROJECT_DIR="/opt/media-pipeline"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}This script must be run as root${NC}"
    echo "Please run: sudo $0"
    exit 1
fi

echo -e "${GREEN}Fixing Python import error in test_pipeline.py...${NC}"

# Check if the file exists
if [ ! -f "$PROJECT_DIR/test_pipeline.py" ]; then
    echo -e "${RED}test_pipeline.py not found at $PROJECT_DIR${NC}"
    exit 1
fi

# Create a backup
cp "$PROJECT_DIR/test_pipeline.py" "$PROJECT_DIR/test_pipeline.py.backup"

# Fix the import issue
sed -i '12a from typing import Dict' "$PROJECT_DIR/test_pipeline.py"

echo -e "${GREEN}✓ Added missing Dict import${NC}"

# Test the fix
echo -e "${GREEN}Testing the fix...${NC}"

if sudo -u media-pipeline "$PROJECT_DIR/venv/bin/python" "$PROJECT_DIR/test_pipeline.py"; then
    echo -e "${GREEN}✓ Python import error fixed successfully!${NC}"
    echo -e "${GREEN}✓ Database initialization completed!${NC}"
else
    echo -e "${RED}✗ Fix failed${NC}"
    echo -e "${YELLOW}Restoring backup...${NC}"
    mv "$PROJECT_DIR/test_pipeline.py.backup" "$PROJECT_DIR/test_pipeline.py"
    exit 1
fi

echo -e "${GREEN}✓ Python import error fixed successfully!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "${YELLOW}1. Edit $PROJECT_DIR/.env with your credentials${NC}"
echo -e "${YELLOW}2. Run: $PROJECT_DIR/complete_setup.sh${NC}"
echo -e "${YELLOW}3. Access Web UI at: http://\$(hostname -I | awk '{print \$1}'):8081${NC}"
echo ""
echo -e "${GREEN}🎉 Your media pipeline is ready to use! 🎉${NC}"
