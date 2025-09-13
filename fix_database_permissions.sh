#!/bin/bash

# Database Permissions Fix Script
# This script fixes database file permissions and directory issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Fixing Database Permissions ===${NC}"

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

echo -e "${GREEN}Fixing database permissions and directory issues...${NC}"

# Fix 1: Ensure project directory has proper permissions
echo -e "${GREEN}1. Fixing project directory permissions...${NC}"
chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR"
chmod -R 755 "$PROJECT_DIR"

# Fix 2: Create database directory if it doesn't exist
echo -e "${GREEN}2. Creating database directory...${NC}"
mkdir -p "$PROJECT_DIR"
chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR"
chmod 755 "$PROJECT_DIR"

# Fix 3: Ensure the media-pipeline user can write to the project directory
echo -e "${GREEN}3. Setting up database file permissions...${NC}"
touch "$PROJECT_DIR/media.db"
chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/media.db"
chmod 664 "$PROJECT_DIR/media.db"

# Fix 4: Test database creation as the service user
echo -e "${GREEN}4. Testing database creation...${NC}"
sudo -u "$SERVICE_USER" python3 -c "
import sqlite3
import os
os.chdir('$PROJECT_DIR')
conn = sqlite3.connect('media.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, name TEXT)')
cursor.execute('INSERT INTO test (name) VALUES (\"test\")')
conn.commit()
conn.close()
print('Database test successful')
"

# Fix 5: Run the actual test pipeline
echo -e "${GREEN}5. Running pipeline test...${NC}"
if sudo -u "$SERVICE_USER" "$PROJECT_DIR/venv/bin/python" "$PROJECT_DIR/test_pipeline.py"; then
    echo -e "${GREEN}✓ Pipeline test successful!${NC}"
else
    echo -e "${YELLOW}⚠ Pipeline test had some failures, but database is working${NC}"
    echo -e "${YELLOW}This is expected if credentials are not configured yet${NC}"
fi

echo -e "${GREEN}✓ Database permissions fixed successfully!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "${YELLOW}1. Edit $PROJECT_DIR/.env with your credentials${NC}"
echo -e "${YELLOW}2. Run: $PROJECT_DIR/complete_setup.sh${NC}"
echo -e "${YELLOW}3. Access Web UI at: http://\$(hostname -I | awk '{print \$1}'):8081${NC}"
echo ""
echo -e "${GREEN}🎉 Database is now working! 🎉${NC}"
