#!/bin/bash

# Cleanup Files Script
# This script removes unnecessary files and keeps only the essential ones

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Cleaning Up Media Pipeline Files ===${NC}"

# List of files to keep (essential files)
KEEP_FILES=(
    "install_complete_system.sh"
    "cleanup_files.sh"
    "README.md"
    "config.yaml"
    "requirements.txt"
    "pipeline_orchestrator.py"
    "test_pipeline.py"
    "web_ui.py"
    "web_status_dashboard.py"
    "web_config_interface.py"
    "db_viewer.py"
    "sync_icloud.py"
    "sync_pixel.py"
    "bulk_nas_sync.py"
    "bulk_pixel_sync.py"
    "compress_media.py"
    "delete_icloud.py"
    "cleanup_icloud.py"
    "telegram_notifier.py"
    "media_db.py"
    "common/"
    "templates/"
)

# List of files to remove (installation/fix files)
REMOVE_FILES=(
    "install.sh"
    "install_fixed.sh"
    "install_self_contained.sh"
    "install_status_dashboard.sh"
    "install_vscode_server.sh"
    "setup_ssh_lxc.sh"
    "run_install_debug.sh"
    "create_portable_package.sh"
    "deploy_anywhere.sh"
    "validate_solution.sh"
    "fix_permissions.sh"
    "fix_database_permissions.sh"
    "fix_final.sh"
    "fix_all_issues.sh"
    "fix_python_import.sh"
    "fix_service_issues.sh"
    "fix_syncthing.sh"
    "fix_lxc_services.sh"
    "fix_pm2_setup.sh"
    "fix_pm2_issues.sh"
    "start_web_ui_only.sh"
    "start_all_services.sh"
    "start_remaining_services.sh"
    "run_status_dashboard.sh"
    "complete_setup.sh"
    "complete_setup_fixed.sh"
    "complete_setup_guide.sh"
    "quick_setup.sh"
    "configure_credentials.sh"
    "test_media_pipeline.sh"
    "restart_services.sh"
    "diagnose_services.sh"
    "port_info.sh"
    "simple_web_ui.py"
    "ecosystem.config.js"
    "docker-compose.yml"
    "setup_pm2_system.sh"
    "setup_docker_system.sh"
    "HEADLESS_DEVELOPMENT_GUIDE.md"
    "README_ENHANCED.md"
    "README_PORTABLE.md"
    "SETUP_GUIDE.md"
    "RECOMMENDATIONS.md"
    "PRODUCTION_READY_OPTIONS.md"
)

echo -e "${GREEN}Files to keep:${NC}"
for file in "${KEEP_FILES[@]}"; do
    if [ -e "$file" ]; then
        echo -e "${GREEN}✓ $file${NC}"
    fi
done

echo ""
echo -e "${RED}Files to remove:${NC}"
for file in "${REMOVE_FILES[@]}"; do
    if [ -e "$file" ]; then
        echo -e "${RED}✗ $file${NC}"
    fi
done

echo ""
read -p "Do you want to proceed with cleanup? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Cleanup cancelled${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}=== Removing Files ===${NC}"

# Remove files
for file in "${REMOVE_FILES[@]}"; do
    if [ -e "$file" ]; then
        echo -e "${GREEN}Removing $file...${NC}"
        rm -rf "$file"
    fi
done

echo ""
echo -e "${GREEN}=== Cleanup Complete! ===${NC}"
echo ""
echo -e "${BLUE}Remaining essential files:${NC}"
ls -la

echo ""
echo -e "${GREEN}🎉 Cleanup completed successfully! 🎉${NC}"
echo -e "${GREEN}Only essential files remain for the media pipeline system.${NC}"
