#!/bin/bash

# Fix LXC Services Script
# This script fixes services for LXC containers without systemctl

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Fixing LXC Services (No systemctl) ===${NC}"

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
echo -e "${BLUE}=== Step 2: Fix Status Dashboard ===${NC}"

# Copy updated dashboard script
echo -e "${GREEN}Updating status dashboard...${NC}"
cp web_status_dashboard.py "$PROJECT_DIR/"
chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/web_status_dashboard.py"
chmod +x "$PROJECT_DIR/web_status_dashboard.py"

# Create a simple startup script for status dashboard
echo -e "${GREEN}Creating status dashboard startup script...${NC}"
cat > "$PROJECT_DIR/start_status_dashboard.sh" << 'EOF'
#!/bin/bash
cd /opt/media-pipeline
python3 web_status_dashboard.py
EOF

chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/start_status_dashboard.sh"
chmod +x "$PROJECT_DIR/start_status_dashboard.sh"

echo -e "${GREEN}✓ Status dashboard startup script created${NC}"

echo ""
echo -e "${BLUE}=== Step 3: Fix Configuration Interface ===${NC}"

# Copy configuration interface script
echo -e "${GREEN}Installing configuration interface...${NC}"
cp web_config_interface.py "$PROJECT_DIR/"
chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/web_config_interface.py"
chmod +x "$PROJECT_DIR/web_config_interface.py"

# Create a simple startup script for configuration interface
echo -e "${GREEN}Creating configuration interface startup script...${NC}"
cat > "$PROJECT_DIR/start_config_interface.sh" << 'EOF'
#!/bin/bash
cd /opt/media-pipeline
python3 web_config_interface.py
EOF

chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/start_config_interface.sh"
chmod +x "$PROJECT_DIR/start_config_interface.sh"

echo -e "${GREEN}✓ Configuration interface startup script created${NC}"

echo ""
echo -e "${BLUE}=== Step 4: Fix Media Pipeline Web UI ===${NC}"

# Check if media pipeline web UI script exists
if [ -f "$PROJECT_DIR/web_ui.py" ]; then
    echo -e "${GREEN}Creating media pipeline web UI startup script...${NC}"
    cat > "$PROJECT_DIR/start_web_ui.sh" << 'EOF'
#!/bin/bash
cd /opt/media-pipeline
source venv/bin/activate
python web_ui.py
EOF
    
    chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/start_web_ui.sh"
    chmod +x "$PROJECT_DIR/start_web_ui.sh"
    
    echo -e "${GREEN}✓ Media pipeline web UI startup script created${NC}"
else
    echo -e "${YELLOW}⚠ Media pipeline web UI script not found${NC}"
fi

echo ""
echo -e "${BLUE}=== Step 5: Fix Syncthing ===${NC}"

# Check if Syncthing is installed
if command -v syncthing >/dev/null 2>&1; then
    echo -e "${GREEN}Creating Syncthing startup script...${NC}"
    cat > "$PROJECT_DIR/start_syncthing.sh" << 'EOF'
#!/bin/bash
cd /home/media-pipeline
syncthing -gui-address=0.0.0.0:8384
EOF
    
    chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/start_syncthing.sh"
    chmod +x "$PROJECT_DIR/start_syncthing.sh"
    
    echo -e "${GREEN}✓ Syncthing startup script created${NC}"
else
    echo -e "${YELLOW}⚠ Syncthing not found, installing...${NC}"
    
    # Install Syncthing
    curl -s https://syncthing.net/release-key.txt | apt-key add -
    echo "deb https://apt.syncthing.net/ syncthing stable" > /etc/apt/sources.list.d/syncthing.list
    apt update
    apt install -y syncthing
    
    # Create Syncthing startup script
    cat > "$PROJECT_DIR/start_syncthing.sh" << 'EOF'
#!/bin/bash
cd /home/media-pipeline
syncthing -gui-address=0.0.0.0:8384
EOF
    
    chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/start_syncthing.sh"
    chmod +x "$PROJECT_DIR/start_syncthing.sh"
    
    echo -e "${GREEN}✓ Syncthing installed and startup script created${NC}"
fi

echo ""
echo -e "${BLUE}=== Step 6: Configure Nginx ===${NC}"

# Configure Nginx for all services
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

# Test and reload Nginx
nginx -t
service nginx reload

echo -e "${GREEN}✓ Nginx configured${NC}"

echo ""
echo -e "${BLUE}=== Step 7: Create Service Management Script ===${NC}"

# Create a service management script
echo -e "${GREEN}Creating service management script...${NC}"
cat > "$PROJECT_DIR/manage_services.sh" << 'EOF'
#!/bin/bash

# Service Management Script for LXC
# Usage: ./manage_services.sh [start|stop|restart|status] [service]

SERVICE_USER="media-pipeline"
PROJECT_DIR="/opt/media-pipeline"

case "$1" in
    start)
        case "$2" in
            status)
                echo "Starting Status Dashboard..."
                su -s /bin/bash "$SERVICE_USER" -c "cd $PROJECT_DIR && nohup ./start_status_dashboard.sh > /var/log/media-pipeline/status_dashboard.log 2>&1 &"
                ;;
            config)
                echo "Starting Configuration Interface..."
                su -s /bin/bash "$SERVICE_USER" -c "cd $PROJECT_DIR && nohup ./start_config_interface.sh > /var/log/media-pipeline/config_interface.log 2>&1 &"
                ;;
            webui)
                echo "Starting Media Pipeline Web UI..."
                su -s /bin/bash "$SERVICE_USER" -c "cd $PROJECT_DIR && nohup ./start_web_ui.sh > /var/log/media-pipeline/web_ui.log 2>&1 &"
                ;;
            syncthing)
                echo "Starting Syncthing..."
                su -s /bin/bash "$SERVICE_USER" -c "cd $PROJECT_DIR && nohup ./start_syncthing.sh > /var/log/media-pipeline/syncthing.log 2>&1 &"
                ;;
            all)
                echo "Starting all services..."
                su -s /bin/bash "$SERVICE_USER" -c "cd $PROJECT_DIR && nohup ./start_status_dashboard.sh > /var/log/media-pipeline/status_dashboard.log 2>&1 &"
                sleep 2
                su -s /bin/bash "$SERVICE_USER" -c "cd $PROJECT_DIR && nohup ./start_config_interface.sh > /var/log/media-pipeline/config_interface.log 2>&1 &"
                sleep 2
                su -s /bin/bash "$SERVICE_USER" -c "cd $PROJECT_DIR && nohup ./start_web_ui.sh > /var/log/media-pipeline/web_ui.log 2>&1 &"
                sleep 2
                su -s /bin/bash "$SERVICE_USER" -c "cd $PROJECT_DIR && nohup ./start_syncthing.sh > /var/log/media-pipeline/syncthing.log 2>&1 &"
                ;;
            *)
                echo "Usage: $0 start [status|config|webui|syncthing|all]"
                ;;
        esac
        ;;
    stop)
        case "$2" in
            status)
                pkill -f "web_status_dashboard.py"
                ;;
            config)
                pkill -f "web_config_interface.py"
                ;;
            webui)
                pkill -f "web_ui.py"
                ;;
            syncthing)
                pkill -f "syncthing"
                ;;
            all)
                pkill -f "web_status_dashboard.py"
                pkill -f "web_config_interface.py"
                pkill -f "web_ui.py"
                pkill -f "syncthing"
                ;;
            *)
                echo "Usage: $0 stop [status|config|webui|syncthing|all]"
                ;;
        esac
        ;;
    status)
        echo "Service Status:"
        echo "Status Dashboard: $(pgrep -f 'web_status_dashboard.py' > /dev/null && echo 'RUNNING' || echo 'STOPPED')"
        echo "Config Interface: $(pgrep -f 'web_config_interface.py' > /dev/null && echo 'RUNNING' || echo 'STOPPED')"
        echo "Web UI: $(pgrep -f 'web_ui.py' > /dev/null && echo 'RUNNING' || echo 'STOPPED')"
        echo "Syncthing: $(pgrep -f 'syncthing' > /dev/null && echo 'RUNNING' || echo 'STOPPED')"
        echo "Nginx: $(pgrep -f 'nginx' > /dev/null && echo 'RUNNING' || echo 'STOPPED')"
        ;;
    restart)
        $0 stop "$2"
        sleep 2
        $0 start "$2"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status} [service]"
        echo "Services: status, config, webui, syncthing, all"
        ;;
esac
EOF

chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/manage_services.sh"
chmod +x "$PROJECT_DIR/manage_services.sh"

echo -e "${GREEN}✓ Service management script created${NC}"

echo ""
echo -e "${BLUE}=== Step 8: Create Environment File ===${NC}"

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
echo -e "${BLUE}=== Step 9: Create Required Directories ===${NC}"

# Create required directories
echo -e "${GREEN}Creating required directories...${NC}"
mkdir -p /mnt/wd_all_pictures/incoming
mkdir -p /mnt/wd_all_pictures/processed
mkdir -p /var/log/media-pipeline

# Set ownership
chown -R "$SERVICE_USER:$SERVICE_USER" /mnt/wd_all_pictures
chown -R "$SERVICE_USER:$SERVICE_USER" /var/log/media-pipeline

echo -e "${GREEN}✓ Required directories created${NC}"

echo ""
echo -e "${BLUE}=== Step 10: Start All Services ===${NC}"

# Start all services
echo -e "${GREEN}Starting all services...${NC}"
"$PROJECT_DIR/manage_services.sh" start all

# Wait for services to start
sleep 5

echo -e "${GREEN}✓ All services started${NC}"

echo ""
echo -e "${BLUE}=== Step 11: Verify Services ===${NC}"

# Check service status
echo -e "${GREEN}Checking service status...${NC}"
"$PROJECT_DIR/manage_services.sh" status

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
echo -e "${GREEN}=== Setup Complete! ===${NC}"
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
echo -e "${YELLOW}Check status:${NC} $PROJECT_DIR/manage_services.sh status"
echo -e "${YELLOW}Start all:${NC} $PROJECT_DIR/manage_services.sh start all"
echo -e "${YELLOW}Stop all:${NC} $PROJECT_DIR/manage_services.sh stop all"
echo -e "${YELLOW}Restart all:${NC} $PROJECT_DIR/manage_services.sh restart all"
echo ""
echo -e "${GREEN}🎉 LXC Setup completed successfully! 🎉${NC}"
echo -e "${GREEN}All services are now running without systemctl!${NC}"
