#!/bin/bash

# Media Pipeline Solution Validation Script
# This script validates that all components are ready for deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Media Pipeline Solution Validation ===${NC}"
echo ""

# Validation counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Function to run a check
check() {
    local description="$1"
    local command="$2"
    local expected_result="${3:-0}"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -n "Checking: $description... "
    
    if eval "$command" &>/dev/null; then
        if [ $? -eq $expected_result ]; then
            echo -e "${GREEN}✓ PASS${NC}"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
        else
            echo -e "${RED}✗ FAIL${NC}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        fi
    else
        echo -e "${RED}✗ FAIL${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
}

# Function to check file exists and is readable
check_file() {
    local file="$1"
    local description="$2"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -n "Checking: $description... "
    
    if [ -f "$file" ] && [ -r "$file" ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "${RED}✗ FAIL${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
}

# Function to check file is executable
check_executable() {
    local file="$1"
    local description="$2"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -n "Checking: $description... "
    
    if [ -f "$file" ] && [ -x "$file" ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "${RED}✗ FAIL${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
}

echo -e "${BLUE}=== Core Files Validation ===${NC}"

# Check core Python files
check_file "pipeline_orchestrator.py" "Main pipeline orchestrator"
check_file "web_ui.py" "Web UI application"
check_file "media_db.py" "Database module"
check_file "sync_icloud.py" "iCloud sync module"
check_file "sync_pixel.py" "Pixel sync module"
check_file "compress_media.py" "Media compression module"
check_file "telegram_notifier.py" "Telegram notification module"

# Check common modules
check_file "common/__init__.py" "Common module init"
check_file "common/config.py" "Configuration module"
check_file "common/database.py" "Database utilities"
check_file "common/logger.py" "Logging utilities"
check_file "common/auth.py" "Authentication module"

# Check configuration files
check_file "config.yaml" "Main configuration file"
check_file "requirements.txt" "Python dependencies"
check_file ".env.template" "Environment template"

# Check web templates
check_file "templates/index.html" "Web UI template"

echo ""
echo -e "${BLUE}=== Installation Scripts Validation ===${NC}"

# Check installation scripts
check_file "install.sh" "Original installation script"
check_file "install_self_contained.sh" "Self-contained installation script"
check_file "install_offline.sh" "Offline installation script"
check_file "create_portable_package.sh" "Portable package creation script"
check_file "deploy_anywhere.sh" "Universal deployment script"

# Check utility scripts
check_file "run_install_debug.sh" "Debug installation wrapper"
check_file "setup_ssh_lxc.sh" "SSH setup script"
check_file "install_vscode_server.sh" "VS Code Server installation"

echo ""
echo -e "${BLUE}=== Documentation Validation ===${NC}"

# Check documentation
check_file "README.md" "Main README"
check_file "README_PORTABLE.md" "Portable deployment README"
check_file "DEPLOYMENT_GUIDE.md" "Deployment guide"
check_file "HEADLESS_DEVELOPMENT_GUIDE.md" "Headless development guide"
check_file "SETUP_GUIDE.md" "Setup guide"
check_file "RECOMMENDATIONS.md" "Recommendations"

echo ""
echo -e "${BLUE}=== Script Permissions Validation ===${NC}"

# Check if scripts are executable (or can be made executable)
check_executable "install.sh" "Original install script executable"
check_executable "install_self_contained.sh" "Self-contained install script executable"
check_executable "deploy_anywhere.sh" "Universal deployment script executable"
check_executable "create_portable_package.sh" "Package creation script executable"

echo ""
echo -e "${BLUE}=== Python Code Validation ===${NC}"

# Check Python syntax
check "Python syntax - pipeline_orchestrator.py" "python3 -m py_compile pipeline_orchestrator.py"
check "Python syntax - web_ui.py" "python3 -m py_compile web_ui.py"
check "Python syntax - media_db.py" "python3 -m py_compile media_db.py"
check "Python syntax - sync_icloud.py" "python3 -m py_compile sync_icloud.py"
check "Python syntax - sync_pixel.py" "python3 -m py_compile sync_pixel.py"
check "Python syntax - compress_media.py" "python3 -m py_compile compress_media.py"
check "Python syntax - telegram_notifier.py" "python3 -m py_compile telegram_notifier.py"

# Check common modules
check "Python syntax - common/config.py" "python3 -m py_compile common/config.py"
check "Python syntax - common/database.py" "python3 -m py_compile common/database.py"
check "Python syntax - common/logger.py" "python3 -m py_compile common/logger.py"
check "Python syntax - common/auth.py" "python3 -m py_compile common/auth.py"

echo ""
echo -e "${BLUE}=== Configuration Validation ===${NC}"

# Check YAML syntax
check "YAML syntax - config.yaml" "python3 -c 'import yaml; yaml.safe_load(open(\"config.yaml\"))'"

# Check requirements.txt format
check "Requirements.txt format" "python3 -c 'import pkg_resources; [pkg_resources.Requirement.parse(line.strip()) for line in open(\"requirements.txt\") if line.strip() and not line.startswith(\"#\")]'"

echo ""
echo -e "${BLUE}=== Deployment Readiness Validation ===${NC}"

# Check if all required files are present for deployment
check "All core files present" "[ -f pipeline_orchestrator.py ] && [ -f web_ui.py ] && [ -f config.yaml ] && [ -f requirements.txt ]"
check "Installation scripts present" "[ -f install_self_contained.sh ] && [ -f deploy_anywhere.sh ]"
check "Documentation present" "[ -f README_PORTABLE.md ] && [ -f DEPLOYMENT_GUIDE.md ]"

echo ""
echo -e "${BLUE}=== Summary ===${NC}"
echo -e "${GREEN}Total Checks: $TOTAL_CHECKS${NC}"
echo -e "${GREEN}Passed: $PASSED_CHECKS${NC}"
echo -e "${RED}Failed: $FAILED_CHECKS${NC}"

if [ $FAILED_CHECKS -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 ALL CHECKS PASSED! 🎉${NC}"
    echo -e "${GREEN}Your media pipeline solution is ready for deployment!${NC}"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo -e "${YELLOW}1. Make scripts executable: chmod +x *.sh${NC}"
    echo -e "${YELLOW}2. Deploy: ./deploy_anywhere.sh${NC}"
    echo -e "${YELLOW}3. Or create package: ./create_portable_package.sh${NC}"
    echo ""
    echo -e "${GREEN}✅ Solution is complete and ready!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}❌ SOME CHECKS FAILED! ❌${NC}"
    echo -e "${RED}Please fix the failed checks before deployment.${NC}"
    echo ""
    echo -e "${YELLOW}Common fixes:${NC}"
    echo -e "${YELLOW}- Make scripts executable: chmod +x *.sh${NC}"
    echo -e "${YELLOW}- Check file permissions${NC}"
    echo -e "${YELLOW}- Verify all files are present${NC}"
    exit 1
fi
