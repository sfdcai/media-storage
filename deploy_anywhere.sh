#!/bin/bash

# Universal Media Pipeline Deployment Script
# This script can deploy the media pipeline on any Ubuntu LXC container
# Works online or offline, with or without internet access

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Universal Media Pipeline Deployment ===${NC}"
echo -e "${GREEN}This script deploys your media pipeline anywhere!${NC}"
echo ""

# Configuration
DEPLOYMENT_MODE="auto"  # auto, online, offline
PACKAGE_NAME="media-pipeline-portable"
PROJECT_DIR="/opt/media-pipeline"
SERVICE_USER="media-pipeline"

# Function to detect deployment mode
detect_deployment_mode() {
    if ping -c 1 8.8.8.8 &> /dev/null; then
        echo "online"
    else
        echo "offline"
    fi
}

# Function to check if we're in a portable package
is_portable_package() {
    if [ -d "offline_deps" ] && [ -f "install_offline.sh" ]; then
        return 0
    else
        return 1
    fi
}

# Function to create portable package
create_portable_package() {
    echo -e "${GREEN}Creating portable package...${NC}"
    
    if [ -f "create_portable_package.sh" ]; then
        chmod +x create_portable_package.sh
        ./create_portable_package.sh
        echo -e "${GREEN}Portable package created successfully!${NC}"
        return 0
    else
        echo -e "${RED}create_portable_package.sh not found${NC}"
        return 1
    fi
}

# Function to deploy online
deploy_online() {
    echo -e "${GREEN}Deploying in online mode...${NC}"
    
    if [ -f "install_self_contained.sh" ]; then
        chmod +x install_self_contained.sh
        ./install_self_contained.sh
    else
        echo -e "${RED}install_self_contained.sh not found${NC}"
        return 1
    fi
}

# Function to deploy offline
deploy_offline() {
    echo -e "${GREEN}Deploying in offline mode...${NC}"
    
    if [ -f "install_offline.sh" ]; then
        chmod +x install_offline.sh
        ./install_offline.sh
    else
        echo -e "${RED}install_offline.sh not found${NC}"
        echo -e "${YELLOW}Creating portable package first...${NC}"
        if create_portable_package; then
            # Find the created package
            PACKAGE_FILE=$(ls -t ${PACKAGE_NAME}-*.tar.gz 2>/dev/null | head -1)
            if [ -n "$PACKAGE_FILE" ]; then
                echo -e "${GREEN}Extracting portable package...${NC}"
                tar -xzf "$PACKAGE_FILE"
                PACKAGE_DIR=$(tar -tzf "$PACKAGE_FILE" | head -1 | cut -f1 -d"/")
                cd "$PACKAGE_DIR"
                chmod +x install_offline.sh
                ./install_offline.sh
            else
                echo -e "${RED}Failed to find created package${NC}"
                return 1
            fi
        else
            return 1
        fi
    fi
}

# Main deployment logic
main() {
    echo -e "${BLUE}Detecting deployment environment...${NC}"
    
    # Check if we're in a portable package
    if is_portable_package; then
        echo -e "${GREEN}✓ Portable package detected${NC}"
        DEPLOYMENT_MODE="offline"
    else
        echo -e "${YELLOW}⚠ Not in portable package - checking internet connectivity${NC}"
        DEPLOYMENT_MODE=$(detect_deployment_mode)
    fi
    
    echo -e "${BLUE}Deployment mode: $DEPLOYMENT_MODE${NC}"
    
    case $DEPLOYMENT_MODE in
        "online")
            deploy_online
            ;;
        "offline")
            deploy_offline
            ;;
        *)
            echo -e "${RED}Unknown deployment mode: $DEPLOYMENT_MODE${NC}"
            exit 1
            ;;
    esac
    
    # Post-deployment setup
    echo -e "${GREEN}=== Post-Deployment Setup ===${NC}"
    
    # Check if services are installed
    if [ -f "$PROJECT_DIR/complete_setup.sh" ]; then
        echo -e "${GREEN}✓ Media pipeline installed successfully${NC}"
        echo -e "${BLUE}Next steps:${NC}"
        echo -e "${YELLOW}1. Edit $PROJECT_DIR/.env with your credentials${NC}"
        echo -e "${YELLOW}2. Run: $PROJECT_DIR/complete_setup.sh${NC}"
        echo -e "${YELLOW}3. Access Web UI at: http://\$(hostname -I | awk '{print \$1}')${NC}"
        
        # Check if Syncthing is available
        if command -v syncthing &> /dev/null; then
            echo -e "${YELLOW}4. Access Syncthing at: http://\$(hostname -I | awk '{print \$1}'):8384${NC}"
        fi
        
        # Create quick start script
        cat > quick_start.sh << 'EOF'
#!/bin/bash
# Quick start script for media pipeline

echo "Starting Media Pipeline..."

# Check if .env is configured
if [ ! -f /opt/media-pipeline/.env ] || grep -q "your_" /opt/media-pipeline/.env; then
    echo "⚠️  Please configure /opt/media-pipeline/.env first"
    echo "Edit the file and set your actual credentials"
    exit 1
fi

# Start services
/opt/media-pipeline/complete_setup.sh

echo "✅ Media Pipeline started successfully!"
echo "🌐 Web UI: http://$(hostname -I | awk '{print $1}')"
if command -v syncthing &> /dev/null; then
    echo "🔄 Syncthing: http://$(hostname -I | awk '{print $1}'):8384"
fi
EOF
        chmod +x quick_start.sh
        echo -e "${GREEN}✓ Quick start script created: ./quick_start.sh${NC}"
        
    else
        echo -e "${RED}✗ Installation failed - services not found${NC}"
        exit 1
    fi
}

# Handle command line arguments
case "${1:-}" in
    "online")
        DEPLOYMENT_MODE="online"
        ;;
    "offline")
        DEPLOYMENT_MODE="offline"
        ;;
    "package")
        create_portable_package
        exit 0
        ;;
    "help"|"-h"|"--help")
        echo -e "${BLUE}Usage: $0 [mode]${NC}"
        echo -e "${GREEN}Modes:${NC}"
        echo -e "  ${YELLOW}online${NC}  - Deploy with internet access"
        echo -e "  ${YELLOW}offline${NC} - Deploy without internet access"
        echo -e "  ${YELLOW}package${NC} - Create portable package"
        echo -e "  ${YELLOW}help${NC}   - Show this help"
        echo ""
        echo -e "${GREEN}Examples:${NC}"
        echo -e "  ${YELLOW}$0${NC}           # Auto-detect mode"
        echo -e "  ${YELLOW}$0 online${NC}    # Force online mode"
        echo -e "  ${YELLOW}$0 offline${NC}   # Force offline mode"
        echo -e "  ${YELLOW}$0 package${NC}   # Create portable package"
        exit 0
        ;;
esac

# Run main deployment
main

echo -e "${GREEN}🎉 Deployment completed successfully! 🎉${NC}"
