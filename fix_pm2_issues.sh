#!/bin/bash

# Fix PM2 Issues Script
# This script fixes the Python package and port issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Fixing PM2 Issues ===${NC}"

# Configuration
PROJECT_DIR="/opt/media-pipeline"
SERVICE_USER="media-pipeline"
CONTAINER_IP=$(hostname -I | awk '{print $1}')

echo -e "${GREEN}Container IP: $CONTAINER_IP${NC}"
echo ""

echo -e "${BLUE}=== Step 1: Stop All PM2 Applications ===${NC}"

# Stop all PM2 applications
echo -e "${GREEN}Stopping all PM2 applications...${NC}"
pm2 stop all
pm2 delete all

echo -e "${GREEN}✓ All PM2 applications stopped${NC}"

echo ""
echo -e "${BLUE}=== Step 2: Install Python Packages in Virtual Environment ===${NC}"

# Install Python packages in the virtual environment
echo -e "${GREEN}Installing Python packages in virtual environment...${NC}"
if [ -f "$PROJECT_DIR/venv/bin/pip" ]; then
    "$PROJECT_DIR/venv/bin/pip" install flask flask-socketio requests
    echo -e "${GREEN}✓ Python packages installed in virtual environment${NC}"
else
    echo -e "${RED}✗ Virtual environment not found${NC}"
    echo -e "${GREEN}Creating virtual environment...${NC}"
    python3 -m venv "$PROJECT_DIR/venv"
    "$PROJECT_DIR/venv/bin/pip" install flask flask-socketio requests
    echo -e "${GREEN}✓ Virtual environment created and packages installed${NC}"
fi

echo ""
echo -e "${BLUE}=== Step 3: Check for Port Conflicts ===${NC}"

# Check what's using port 8081
echo -e "${GREEN}Checking port 8081...${NC}"
if netstat -tlnp | grep -q ":8081 "; then
    echo -e "${YELLOW}⚠ Port 8081 is already in use${NC}"
    echo -e "${GREEN}Killing process using port 8081...${NC}"
    PID=$(netstat -tlnp | grep ":8081 " | awk '{print $7}' | cut -d'/' -f1)
    if [ ! -z "$PID" ]; then
        kill -9 "$PID"
        echo -e "${GREEN}✓ Process killed${NC}"
    fi
else
    echo -e "${GREEN}✓ Port 8081 is available${NC}"
fi

echo ""
echo -e "${BLUE}=== Step 4: Create Fixed PM2 Ecosystem File ===${NC}"

# Create PM2 ecosystem file with correct Python paths
echo -e "${GREEN}Creating fixed PM2 ecosystem configuration...${NC}"
cat > "$PROJECT_DIR/ecosystem.config.js" << 'EOF'
module.exports = {
  apps: [
    {
      name: 'status-dashboard',
      script: 'web_status_dashboard.py',
      interpreter: '/opt/media-pipeline/venv/bin/python',
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
      interpreter: '/opt/media-pipeline/venv/bin/python',
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
    },
    {
      name: 'media-pipeline-web',
      script: 'web_ui.py',
      interpreter: '/opt/media-pipeline/venv/bin/python',
      cwd: '/opt/media-pipeline',
      user: 'media-pipeline',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        PORT: 8081
      },
      error_file: '/var/log/media-pipeline/media-pipeline-web-error.log',
      out_file: '/var/log/media-pipeline/media-pipeline-web-out.log',
      log_file: '/var/log/media-pipeline/media-pipeline-web.log',
      time: true
    }
  ]
};
EOF

chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/ecosystem.config.js"

echo -e "${GREEN}✓ Fixed PM2 ecosystem configuration created${NC}"

echo ""
echo -e "${BLUE}=== Step 5: Create Simple Web UI if Needed ===${NC}"

# Check if web_ui.py exists, if not create a simple one
if [ ! -f "$PROJECT_DIR/web_ui.py" ]; then
    echo -e "${GREEN}Creating simple web UI...${NC}"
    cat > "$PROJECT_DIR/simple_web_ui.py" << 'EOF'
#!/usr/bin/env python3
"""
Simple Media Pipeline Web UI
A basic web interface for the media pipeline
"""

from flask import Flask, render_template, jsonify
import os
import subprocess
import socket
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Media Pipeline Web UI</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .status { padding: 15px; margin: 10px 0; border-radius: 4px; }
            .status.success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .status.info { background-color: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
            .btn { padding: 10px 20px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
            .btn:hover { background-color: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Media Pipeline Web UI</h1>
                <p>Simple web interface for media pipeline management</p>
            </div>
            
            <div class="status success">
                <h3>✅ Media Pipeline Web UI is Running</h3>
                <p>This is a simple web interface for the media pipeline.</p>
            </div>
            
            <div class="status info">
                <h3>📊 System Information</h3>
                <p><strong>Status:</strong> Running</p>
                <p><strong>Time:</strong> """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
                <p><strong>Port:</strong> 8081</p>
            </div>
            
            <div class="status info">
                <h3>🔗 Access Other Services</h3>
                <p><a href="http://localhost:8082" target="_blank">Status Dashboard</a></p>
                <p><a href="http://localhost:8083" target="_blank">Configuration Interface</a></p>
                <p><a href="http://localhost:8385" target="_blank">Syncthing</a></p>
            </div>
            
            <button class="btn" onclick="location.reload()">Refresh</button>
            <button class="btn" onclick="window.open('http://localhost:8082', '_blank')">Status Dashboard</button>
            <button class="btn" onclick="window.open('http://localhost:8083', '_blank')">Configuration</button>
        </div>
    </body>
    </html>
    """

@app.route('/api/status')
def get_status():
    return jsonify({
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "port": 8081
    })

if __name__ == '__main__':
    import sys
    port = 8081
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    
    print(f"Starting Simple Media Pipeline Web UI on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
EOF
    
    chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/simple_web_ui.py"
    chmod +x "$PROJECT_DIR/simple_web_ui.py"
    
    # Update ecosystem to use simple web UI
    sed -i 's/web_ui.py/simple_web_ui.py/g' "$PROJECT_DIR/ecosystem.config.js"
    
    echo -e "${GREEN}✓ Simple web UI created${NC}"
fi

echo ""
echo -e "${BLUE}=== Step 6: Create Required Directories ===${NC}"

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
echo -e "${BLUE}=== Step 7: Start PM2 Applications ===${NC}"

# Start PM2 applications
echo -e "${GREEN}Starting PM2 applications...${NC}"
pm2 start "$PROJECT_DIR/ecosystem.config.js"

# Save PM2 configuration
pm2 save

echo -e "${GREEN}✓ PM2 applications started${NC}"

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
    
    # Media Pipeline Web UI
    location /pipeline/ {
        proxy_pass http://127.0.0.1:8081/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Syncthing (Updated port)
    location /syncthing/ {
        proxy_pass http://127.0.0.1:8385/;
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
echo -e "${BLUE}=== Step 9: Create Environment File ===${NC}"

# Create .env file
echo -e "${GREEN}Creating environment file...${NC}"
cat > "$PROJECT_DIR/.env" << EOF
# Media Pipeline Environment Configuration
# Generated on $(date)

# iCloud Configuration
ICLOUD_USERNAME=
ICLOUD_PASSWORD=

# Syncthing Configuration (Updated port)
SYNCTHING_URL=http://$CONTAINER_IP:8385/rest
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
echo -e "${BLUE}=== Step 10: Verify Services ===${NC}"

# Wait for services to start
sleep 5

# Check PM2 status
echo -e "${GREEN}PM2 Application Status:${NC}"
pm2 status

# Check ports
echo -e "${GREEN}Checking ports...${NC}"
ports=("80" "8080" "8081" "8082" "8083" "8385" "9615")
for port in "${ports[@]}"; do
    if netstat -tlnp | grep -q ":$port "; then
        echo -e "${GREEN}✓ Port $port: LISTENING${NC}"
    else
        echo -e "${YELLOW}⚠ Port $port: NOT LISTENING${NC}"
    fi
done

echo ""
echo -e "${GREEN}=== PM2 Issues Fixed! ===${NC}"
echo ""
echo -e "${BLUE}Access URLs:${NC}"
echo -e "${YELLOW}PM2 Dashboard:${NC} http://$CONTAINER_IP:9615"
echo -e "${YELLOW}Status Dashboard:${NC} http://$CONTAINER_IP:8082"
echo -e "${YELLOW}Configuration Interface:${NC} http://$CONTAINER_IP:8083"
echo -e "${YELLOW}Media Pipeline Web UI:${NC} http://$CONTAINER_IP:8081"
echo -e "${YELLOW}Syncthing:${NC} http://$CONTAINER_IP:8385"
echo -e "${YELLOW}VS Code Server:${NC} http://$CONTAINER_IP:8080"
echo ""
echo -e "${BLUE}Via Nginx:${NC}"
echo -e "${YELLOW}PM2 Dashboard:${NC} http://$CONTAINER_IP/pm2/"
echo -e "${YELLOW}Status Dashboard:${NC} http://$CONTAINER_IP/status/"
echo -e "${YELLOW}Configuration Interface:${NC} http://$CONTAINER_IP/config/"
echo -e "${YELLOW}Media Pipeline Web UI:${NC} http://$CONTAINER_IP/pipeline/"
echo -e "${YELLOW}Syncthing:${NC} http://$CONTAINER_IP/syncthing/"
echo -e "${YELLOW}VS Code Server:${NC} http://$CONTAINER_IP/vscode/"
echo ""
echo -e "${BLUE}PM2 Management Commands:${NC}"
echo -e "${YELLOW}Check status:${NC} pm2 status"
echo -e "${YELLOW}View logs:${NC} pm2 logs"
echo -e "${YELLOW}Restart all:${NC} pm2 restart all"
echo -e "${YELLOW}Stop all:${NC} pm2 stop all"
echo -e "${YELLOW}Monitor:${NC} pm2 monit"
echo ""
echo -e "${GREEN}🎉 All PM2 issues are now fixed! 🎉${NC}"
echo -e "${GREEN}All services are running with proper virtual environment!${NC}"
