#!/bin/bash

# Fix PM2 Setup Script
# This script fixes the PM2 setup and starts all applications

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Fixing PM2 Setup ===${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}This script must be run as root${NC}"
    echo "Please run: $0"
    exit 1
fi

# Configuration
PROJECT_DIR="/opt/media-pipeline"
SERVICE_USER="media-pipeline"
CONTAINER_IP=$(hostname -I | awk '{print $1}')

echo -e "${GREEN}Container IP: $CONTAINER_IP${NC}"
echo ""

echo -e "${BLUE}=== Step 1: Check PM2 Status ===${NC}"

# Check PM2 status
echo -e "${GREEN}Checking PM2 status...${NC}"
su -s /bin/bash "$SERVICE_USER" -c "pm2 status"

echo ""
echo -e "${BLUE}=== Step 2: Install Required Python Packages ===${NC}"

# Install Python packages
echo -e "${GREEN}Installing Python packages...${NC}"
pip3 install flask flask-socketio requests

echo -e "${GREEN}✓ Python packages installed${NC}"

echo ""
echo -e "${BLUE}=== Step 3: Create PM2 Ecosystem File ===${NC}"

# Create PM2 ecosystem file
echo -e "${GREEN}Creating PM2 ecosystem configuration...${NC}"
cat > "$PROJECT_DIR/ecosystem.config.js" << 'EOF'
module.exports = {
  apps: [
    {
      name: 'status-dashboard',
      script: 'web_status_dashboard.py',
      interpreter: 'python3',
      cwd: '/opt/media-pipeline',
      user: 'media-pipeline',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        PORT: 8082
      },
      error_file: '/var/log/media-pipeline/status-dashboard-error.log',
      out_file: '/var/log/media-pipeline/status-dashboard-out.log',
      log_file: '/var/log/media-pipeline/status-dashboard.log',
      time: true
    },
    {
      name: 'config-interface',
      script: 'web_config_interface.py',
      interpreter: 'python3',
      cwd: '/opt/media-pipeline',
      user: 'media-pipeline',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        PORT: 8083
      },
      error_file: '/var/log/media-pipeline/config-interface-error.log',
      out_file: '/var/log/media-pipeline/config-interface-out.log',
      log_file: '/var/log/media-pipeline/config-interface.log',
      time: true
    }
  ]
};
EOF

chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/ecosystem.config.js"

echo -e "${GREEN}✓ PM2 ecosystem configuration created${NC}"

echo ""
echo -e "${BLUE}=== Step 4: Create Required Directories ===${NC}"

# Create required directories
echo -e "${GREEN}Creating required directories...${NC}"
mkdir -p /var/log/media-pipeline
mkdir -p /mnt/wd_all_pictures/incoming
mkdir -p /mnt/wd_all_pictures/processed

# Set ownership
chown -R "$SERVICE_USER:$SERVICE_USER" /var/log/media-pipeline
chown -R "$SERVICE_USER:$SERVICE_USER" /mnt/wd_all_pictures

echo -e "${GREEN}✓ Required directories created${NC}"

echo ""
echo -e "${BLUE}=== Step 5: Create Environment File ===${NC}"

# Create .env file
echo -e "${GREEN}Creating environment file...${NC}"
cat > "$PROJECT_DIR/.env" << EOF
# Media Pipeline Environment Configuration
# Generated on $(date)

# iCloud Configuration
ICLOUD_USERNAME=
ICLOUD_PASSWORD=

# Syncthing Configuration
SYNCTHING_URL=http://$CONTAINER_IP:8384/rest
SYNCTHING_API_KEY=

# Telegram Notifications (Optional)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Directory Configuration
INCOMING_DIR=/mnt/wd_all_pictures/incoming
PROCESSED_DIR=/mnt/wd_all_pictures/processed
EOF

chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/.env"
chmod 600 "$PROJECT_DIR/.env"

echo -e "${GREEN}✓ Environment file created${NC}"

echo ""
echo -e "${BLUE}=== Step 6: Start PM2 Applications ===${NC}"

# Start PM2 applications
echo -e "${GREEN}Starting PM2 applications...${NC}"
su -s /bin/bash "$SERVICE_USER" -c "cd $PROJECT_DIR && pm2 start ecosystem.config.js"

# Save PM2 configuration
su -s /bin/bash "$SERVICE_USER" -c "pm2 save"

echo -e "${GREEN}✓ PM2 applications started${NC}"

echo ""
echo -e "${BLUE}=== Step 7: Install and Start Syncthing ===${NC}"

# Install Syncthing if not already installed
if ! command -v syncthing >/dev/null 2>&1; then
    echo -e "${GREEN}Installing Syncthing...${NC}"
    curl -s https://syncthing.net/release-key.txt | apt-key add -
    echo "deb https://apt.syncthing.net/ syncthing stable" > /etc/apt/sources.list.d/syncthing.list
    apt update
    apt install -y syncthing
fi

# Start Syncthing with PM2
echo -e "${GREEN}Starting Syncthing with PM2...${NC}"
su -s /bin/bash "$SERVICE_USER" -c "pm2 start syncthing --name syncthing -- -gui-address=0.0.0.0:8384"

# Save PM2 configuration again
su -s /bin/bash "$SERVICE_USER" -c "pm2 save"

echo -e "${GREEN}✓ Syncthing started with PM2${NC}"

echo ""
echo -e "${BLUE}=== Step 8: Configure Nginx ===${NC}"

# Install Nginx if not already installed
if ! command -v nginx >/dev/null 2>&1; then
    echo -e "${GREEN}Installing Nginx...${NC}"
    apt install -y nginx
fi

# Configure Nginx
echo -e "${GREEN}Configuring Nginx...${NC}"
cat > /etc/nginx/sites-available/media-pipeline << EOF
server {
    listen 80;
    server_name _;
    
    # PM2 Dashboard
    location /pm2/ {
        proxy_pass http://127.0.0.1:9615/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Status Dashboard
    location /status/ {
        proxy_pass http://127.0.0.1:8082/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Configuration Interface
    location /config/ {
        proxy_pass http://127.0.0.1:8083/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Syncthing
    location /syncthing/ {
        proxy_pass http://127.0.0.1:8384/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # VS Code Server
    location /vscode/ {
        proxy_pass http://127.0.0.1:8080/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/media-pipeline /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and start Nginx
nginx -t
service nginx start

echo -e "${GREEN}✓ Nginx configured and started${NC}"

echo ""
echo -e "${BLUE}=== Step 9: Verify Services ===${NC}"

# Wait for services to start
sleep 5

# Check PM2 status
echo -e "${GREEN}PM2 Application Status:${NC}"
su -s /bin/bash "$SERVICE_USER" -c "pm2 status"

# Check ports
echo -e "${GREEN}Checking ports...${NC}"
ports=("80" "8080" "8081" "8082" "8083" "8384" "9615")
for port in "${ports[@]}"; do
    if netstat -tlnp | grep -q ":$port "; then
        echo -e "${GREEN}✓ Port $port: LISTENING${NC}"
    else
        echo -e "${YELLOW}⚠ Port $port: NOT LISTENING${NC}"
    fi
done

echo ""
echo -e "${GREEN}=== PM2 Setup Fixed! ===${NC}"
echo ""
echo -e "${BLUE}Access URLs:${NC}"
echo -e "${YELLOW}PM2 Dashboard:${NC} http://$CONTAINER_IP:9615"
echo -e "${YELLOW}Status Dashboard:${NC} http://$CONTAINER_IP:8082"
echo -e "${YELLOW}Configuration Interface:${NC} http://$CONTAINER_IP:8083"
echo -e "${YELLOW}Syncthing:${NC} http://$CONTAINER_IP:8384"
echo -e "${YELLOW}VS Code Server:${NC} http://$CONTAINER_IP:8080"
echo ""
echo -e "${BLUE}Via Nginx:${NC}"
echo -e "${YELLOW}PM2 Dashboard:${NC} http://$CONTAINER_IP/pm2/"
echo -e "${YELLOW}Status Dashboard:${NC} http://$CONTAINER_IP/status/"
echo -e "${YELLOW}Configuration Interface:${NC} http://$CONTAINER_IP/config/"
echo -e "${YELLOW}Syncthing:${NC} http://$CONTAINER_IP/syncthing/"
echo -e "${YELLOW}VS Code Server:${NC} http://$CONTAINER_IP/vscode/"
echo ""
echo -e "${BLUE}PM2 Management Commands:${NC}"
echo -e "${YELLOW}Check status:${NC} su -s /bin/bash media-pipeline -c 'pm2 status'"
echo -e "${YELLOW}View logs:${NC} su -s /bin/bash media-pipeline -c 'pm2 logs'"
echo -e "${YELLOW}Restart all:${NC} su -s /bin/bash media-pipeline -c 'pm2 restart all'"
echo -e "${YELLOW}Stop all:${NC} su -s /bin/bash media-pipeline -c 'pm2 stop all'"
echo -e "${YELLOW}Monitor:${NC} su -s /bin/bash media-pipeline -c 'pm2 monit'"
echo ""
echo -e "${GREEN}🎉 PM2 Setup is now working! 🎉${NC}"
echo -e "${GREEN}Use the PM2 Dashboard to monitor and manage all services!${NC}"
