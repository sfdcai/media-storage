#!/bin/bash

# Test Media Pipeline Script
# This script tests the media pipeline manually to identify issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Testing Media Pipeline Manually ===${NC}"

# Configuration
PROJECT_DIR="/opt/media-pipeline"
SERVICE_USER="media-pipeline"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}This script must be run as root${NC}"
    echo "Please run: sudo $0"
    exit 1
fi

echo -e "${GREEN}Testing media pipeline components...${NC}"

# Test 1: Check if files exist
echo -e "${GREEN}1. Checking if files exist...${NC}"
if [ -f "$PROJECT_DIR/pipeline_orchestrator.py" ]; then
    echo -e "${GREEN}✓ pipeline_orchestrator.py exists${NC}"
else
    echo -e "${RED}✗ pipeline_orchestrator.py missing${NC}"
    exit 1
fi

if [ -f "$PROJECT_DIR/venv/bin/python" ]; then
    echo -e "${GREEN}✓ Python virtual environment exists${NC}"
else
    echo -e "${RED}✗ Python virtual environment missing${NC}"
    exit 1
fi

# Test 2: Check Python syntax
echo -e "${GREEN}2. Checking Python syntax...${NC}"
if sudo -u "$SERVICE_USER" "$PROJECT_DIR/venv/bin/python" -m py_compile "$PROJECT_DIR/pipeline_orchestrator.py"; then
    echo -e "${GREEN}✓ Python syntax is correct${NC}"
else
    echo -e "${RED}✗ Python syntax error${NC}"
    exit 1
fi

# Test 3: Check imports
echo -e "${GREEN}3. Checking Python imports...${NC}"
if sudo -u "$SERVICE_USER" "$PROJECT_DIR/venv/bin/python" -c "
import sys
sys.path.insert(0, '$PROJECT_DIR')
try:
    from common import config_manager, db_manager, setup_module_logger, auth_manager
    print('✓ All imports successful')
except ImportError as e:
    print(f'✗ Import error: {e}')
    sys.exit(1)
"; then
    echo -e "${GREEN}✓ All imports successful${NC}"
else
    echo -e "${RED}✗ Import error${NC}"
    exit 1
fi

# Test 4: Test configuration loading
echo -e "${GREEN}4. Testing configuration loading...${NC}"
if sudo -u "$SERVICE_USER" "$PROJECT_DIR/venv/bin/python" -c "
import sys
sys.path.insert(0, '$PROJECT_DIR')
try:
    from common import config_manager
    config = config_manager.get_config()
    print('✓ Configuration loaded successfully')
    print(f'Database path: {config.database.file_path}')
    print(f'Log directory: {config.logging.log_dir}')
except Exception as e:
    print(f'✗ Configuration error: {e}')
    sys.exit(1)
"; then
    echo -e "${GREEN}✓ Configuration loaded successfully${NC}"
else
    echo -e "${RED}✗ Configuration error${NC}"
    exit 1
fi

# Test 5: Test database initialization
echo -e "${GREEN}5. Testing database initialization...${NC}"
if sudo -u "$SERVICE_USER" "$PROJECT_DIR/venv/bin/python" -c "
import sys
sys.path.insert(0, '$PROJECT_DIR')
try:
    from common import db_manager
    db_manager.initialize_database()
    print('✓ Database initialized successfully')
except Exception as e:
    print(f'✗ Database error: {e}')
    sys.exit(1)
"; then
    echo -e "${GREEN}✓ Database initialized successfully${NC}"
else
    echo -e "${RED}✗ Database error${NC}"
    exit 1
fi

# Test 6: Run the actual script
echo -e "${GREEN}6. Testing pipeline orchestrator...${NC}"
echo -e "${YELLOW}Running: sudo -u $SERVICE_USER $PROJECT_DIR/venv/bin/python $PROJECT_DIR/pipeline_orchestrator.py --help${NC}"

if sudo -u "$SERVICE_USER" "$PROJECT_DIR/venv/bin/python" "$PROJECT_DIR/pipeline_orchestrator.py" --help 2>&1; then
    echo -e "${GREEN}✓ Pipeline orchestrator runs successfully${NC}"
else
    echo -e "${YELLOW}⚠ Pipeline orchestrator has issues, but this might be normal${NC}"
fi

# Test 7: Check if script can start without errors
echo -e "${GREEN}7. Testing script startup...${NC}"
echo -e "${YELLOW}Running script for 5 seconds to check for startup errors...${NC}"

timeout 5s sudo -u "$SERVICE_USER" "$PROJECT_DIR/venv/bin/python" "$PROJECT_DIR/pipeline_orchestrator.py" 2>&1 || {
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 124 ]; then
        echo -e "${GREEN}✓ Script started successfully (timeout reached)${NC}"
    else
        echo -e "${RED}✗ Script failed with exit code: $EXIT_CODE${NC}"
        echo -e "${YELLOW}This might indicate a configuration or dependency issue${NC}"
    fi
}

echo ""
echo -e "${GREEN}=== Manual Test Complete ===${NC}"
echo ""
echo -e "${BLUE}If all tests passed, the issue might be:${NC}"
echo -e "${YELLOW}1. Systemd service configuration${NC}"
echo -e "${YELLOW}2. Environment variables${NC}"
echo -e "${YELLOW}3. Working directory issues${NC}"
echo -e "${YELLOW}4. Permission issues${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "${YELLOW}1. Run: ./fix_service_issues.sh${NC}"
echo -e "${YELLOW}2. Check logs: journalctl -u media-pipeline -f${NC}"
echo -e "${YELLOW}3. Test service: systemctl start media-pipeline${NC}"
