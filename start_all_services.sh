#!/bin/bash

# Start All Services Script for LXC
# This script starts all services without systemctl

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Starting All Media Pipeline Services ===${NC}"

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

# Create log directory
mkdir -p /var/log/media-pipeline
chown -R "$SERVICE_USER:$SERVICE_USER" /var/log/media-pipeline

echo -e "${BLUE}=== Step 1: Install Required Packages ===${NC}"

# Install required packages
echo -e "${GREEN}Installing required packages...${NC}"
apt update
apt install -y net-tools curl wget nginx python3-pip

# Install Python packages
echo -e "${GREEN}Installing Python packages...${NC}"
pip3 install flask flask-socketio requests

echo -e "${GREEN}✓ Required packages installed${NC}"

echo ""
echo -e "${BLUE}=== Step 2: Start Status Dashboard ===${NC}"

# Start status dashboard
echo -e "${GREEN}Starting status dashboard...${NC}"
cd "$PROJECT_DIR"
su -s /bin/bash "$SERVICE_USER" -c "nohup python3 web_status_dashboard.py > /var/log/media-pipeline/status_dashboard.log 2>&1 &"
sleep 3

# Check if it's running
if pgrep -f "web_status_dashboard.py" > /dev/null; then
    echo -e "${GREEN}✓ Status dashboard started${NC}"
else
    echo -e "${RED}✗ Failed to start status dashboard${NC}"
fi

echo ""
echo -e "${BLUE}=== Step 3: Start Configuration Interface ===${NC}"

# Start configuration interface
echo -e "${GREEN}Starting configuration interface...${NC}"
cd "$PROJECT_DIR"
su -s /bin/bash "$SERVICE_USER" -c "nohup python3 web_config_interface.py > /var/log/media-pipeline/config_interface.log 2>&1 &"
sleep 3

# Check if it's running
if pgrep -f "web_config_interface.py" > /dev/null; then
    echo -e "${GREEN}✓ Configuration interface started${NC}"
else
    echo -e "${RED}✗ Failed to start configuration interface${NC}"
fi

echo ""
echo -e "${BLUE}=== Step 4: Start Media Pipeline Web UI ===${NC}"

# Check if web UI script exists and start it
if [ -f "$PROJECT_DIR/web_ui.py" ]; then
    echo -e "${GREEN}Starting media pipeline web UI...${NC}"
    cd "$PROJECT_DIR"
    su -s /bin/bash "$SERVICE_USER" -c "source venv/bin/activate && nohup python web_ui.py > /var/log/media-pipeline/web_ui.log 2>&1 &"
    sleep 3
    
    # Check if it's running
    if pgrep -f "web_ui.py" > /dev/null; then
        echo -e "${GREEN}✓ Media pipeline web UI started${NC}"
    else
        echo -e "${RED}✗ Failed to start media pipeline web UI${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Media pipeline web UI script not found${NC}"
fi

echo ""
echo -e "${BLUE}=== Step 5: Start Syncthing ===${NC}"

# Check if Syncthing is installed
if command -v syncthing >/dev/null 2>&1; then
    echo -e "${GREEN}Starting Syncthing...${NC}"
    cd /home/media-pipeline
    su -s /bin/bash "$SERVICE_USER" -c "nohup syncthing -gui-address=0.0.0.0:8384 > /var/log/media-pipeline/syncthing.log 2>&1 &"
    sleep 3
    
    # Check if it's running
    if pgrep -f "syncthing" > /dev/null; then
        echo -e "${GREEN}✓ Syncthing started${NC}"
    else
        echo -e "${RED}✗ Failed to start Syncthing${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Syncthing not found, installing...${NC}"
    
    # Install Syncthing
    curl -s https://syncthing.net/release-key.txt | apt-key add -
    echo "deb https://apt.syncthing.net/ syncthing stable" > /etc/apt/sources.list.d/syncthing.list
    apt update
    apt install -y syncthing
    
    # Start Syncthing
    echo -e "${GREEN}Starting Syncthing...${NC}"
    cd /home/media-pipeline
    su -s /bin/bash "$SERVICE_USER" -c "nohup syncthing -gui-address=0.0.0.0:8384 > /var/log/media-pipeline/syncthing.log 2>&1 &"
    sleep 3
    
    # Check if it's running
    if pgrep -f "syncthing" > /dev/null; then
        echo -e "${GREEN}✓ Syncthing installed and started${NC}"
    else
        echo -e "${RED}✗ Failed to start Syncthing${NC}"
    fi
fi

echo ""
echo -e "${BLUE}=== Step 6: Configure and Start Nginx ===${NC}"

# Configure Nginx
echo -e "${GREEN}Configuring Nginx...${NC}"
cat > /etc/nginx/sites-available/media-pipeline << EOF
server {
    listen 80;
    server_name _;
    
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
    
    # Media Pipeline Web UI
    location /pipeline/ {
        proxy_pass http://127.0.0.1:8081/;
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
echo -e "${BLUE}=== Step 7: Verify Services ===${NC}"

# Check service status
echo -e "${GREEN}Checking service status...${NC}"
echo "Status Dashboard: $(pgrep -f 'web_status_dashboard.py' > /dev/null && echo 'RUNNING' || echo 'STOPPED')"
echo "Config Interface: $(pgrep -f 'web_config_interface.py' > /dev/null && echo 'RUNNING' || echo 'STOPPED')"
echo "Web UI: $(pgrep -f 'web_ui.py' > /dev/null && echo 'RUNNING' || echo 'STOPPED')"
echo "Syncthing: $(pgrep -f 'syncthing' > /dev/null && echo 'RUNNING' || echo 'STOPPED')"
echo "Nginx: $(pgrep -f 'nginx' > /dev/null && echo 'RUNNING' || echo 'STOPPED')"

# Check ports
echo -e "${GREEN}Checking ports...${NC}"
ports=("80" "8080" "8081" "8082" "8083" "8384")
for port in "${ports[@]}"; do
    if netstat -tlnp | grep -q ":$port "; then
        echo -e "${GREEN}✓ Port $port: LISTENING${NC}"
    else
        echo -e "${YELLOW}⚠ Port $port: NOT LISTENING${NC}"
    fi
done

echo ""
echo -e "${GREEN}=== All Services Started! ===${NC}"
echo ""
echo -e "${BLUE}Access URLs:${NC}"
echo -e "${YELLOW}Status Dashboard:${NC} http://$CONTAINER_IP/status/"
echo -e "${YELLOW}Configuration Interface:${NC} http://$CONTAINER_IP/config/"
echo -e "${YELLOW}Media Pipeline Web UI:${NC} http://$CONTAINER_IP/pipeline/"
echo -e "${YELLOW}Syncthing:${NC} http://$CONTAINER_IP/syncthing/"
echo -e "${YELLOW}VS Code Server:${NC} http://$CONTAINER_IP/vscode/"
echo ""
echo -e "${BLUE}Direct Access URLs:${NC}"
echo -e "${YELLOW}Status Dashboard:${NC} http://$CONTAINER_IP:8082"
echo -e "${YELLOW}Configuration Interface:${NC} http://$CONTAINER_IP:8083"
echo -e "${YELLOW}Media Pipeline Web UI:${NC} http://$CONTAINER_IP:8081"
echo -e "${YELLOW}Syncthing:${NC} http://$CONTAINER_IP:8384"
echo -e "${YELLOW}VS Code Server:${NC} http://$CONTAINER_IP:8080"
echo ""
echo -e "${BLUE}Service Management:${NC}"
echo -e "${YELLOW}Check logs:${NC} tail -f /var/log/media-pipeline/*.log"
echo -e "${YELLOW}Stop services:${NC} pkill -f 'web_status_dashboard.py|web_config_interface.py|web_ui.py|syncthing'"
echo -e "${YELLOW}Restart services:${NC} $0"
echo ""
echo -e "${GREEN}🎉 All services are now running! 🎉${NC}"
echo -e "${GREEN}Use the Configuration Interface to set up your credentials!${NC}"
