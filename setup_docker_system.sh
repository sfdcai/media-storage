#!/bin/bash

# Docker-Based Media Pipeline Setup
# This script sets up a robust, containerized system using Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Setting up Docker-Based Media Pipeline System ===${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}This script must be run as root${NC}"
    echo "Please run: $0"
    exit 1
fi

# Configuration
PROJECT_DIR="/opt/media-pipeline"
CONTAINER_IP=$(hostname -I | awk '{print $1}')

echo -e "${GREEN}Container IP: $CONTAINER_IP${NC}"
echo ""

echo -e "${BLUE}=== Step 1: Install Docker and Docker Compose ===${NC}"

# Install Docker
echo -e "${GREEN}Installing Docker...${NC}"
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
echo -e "${GREEN}Installing Docker Compose...${NC}"
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Add current user to docker group
usermod -aG docker $USER

echo -e "${GREEN}✓ Docker and Docker Compose installed${NC}"

echo ""
echo -e "${BLUE}=== Step 2: Create Dockerfiles ===${NC}"

# Create Dockerfile for status dashboard
echo -e "${GREEN}Creating Dockerfile for status dashboard...${NC}"
cat > "$PROJECT_DIR/Dockerfile.status" << 'EOF'
FROM python:3.9-slim

WORKDIR /opt/media-pipeline

# Install system dependencies
RUN apt-get update && apt-get install -y \
    net-tools \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install flask flask-socketio requests

# Copy application files
COPY web_status_dashboard.py .
COPY templates/ ./templates/

# Create log directory
RUN mkdir -p /var/log/media-pipeline

# Expose port
EXPOSE 8082

# Run the application
CMD ["python", "web_status_dashboard.py"]
EOF

# Create Dockerfile for configuration interface
echo -e "${GREEN}Creating Dockerfile for configuration interface...${NC}"
cat > "$PROJECT_DIR/Dockerfile.config" << 'EOF'
FROM python:3.9-slim

WORKDIR /opt/media-pipeline

# Install system dependencies
RUN apt-get update && apt-get install -y \
    net-tools \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install flask flask-socketio requests

# Copy application files
COPY web_config_interface.py .
COPY templates/ ./templates/

# Create log directory
RUN mkdir -p /var/log/media-pipeline

# Expose port
EXPOSE 8083

# Run the application
CMD ["python", "web_config_interface.py"]
EOF

# Create Dockerfile for media pipeline
echo -e "${GREEN}Creating Dockerfile for media pipeline...${NC}"
cat > "$PROJECT_DIR/Dockerfile.pipeline" << 'EOF'
FROM python:3.9-slim

WORKDIR /opt/media-pipeline

# Install system dependencies
RUN apt-get update && apt-get install -y \
    net-tools \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install flask flask-socketio requests

# Copy application files
COPY . .

# Create virtual environment and install dependencies
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt

# Create log directory
RUN mkdir -p /var/log/media-pipeline

# Expose port
EXPOSE 8081

# Run the application
CMD ["venv/bin/python", "web_ui.py"]
EOF

echo -e "${GREEN}✓ Dockerfiles created${NC}"

echo ""
echo -e "${BLUE}=== Step 3: Create Nginx Configuration ===${NC}"

# Create Nginx configuration
echo -e "${GREEN}Creating Nginx configuration...${NC}"
cat > "$PROJECT_DIR/nginx.conf" << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream status_dashboard {
        server status-dashboard:8082;
    }
    
    upstream config_interface {
        server config-interface:8083;
    }
    
    upstream media_pipeline {
        server media-pipeline-web:8081;
    }
    
    upstream syncthing {
        server syncthing:8384;
    }
    
    upstream vscode {
        server vscode:8080;
    }

    server {
        listen 80;
        server_name _;
        
        # Status Dashboard
        location /status/ {
            proxy_pass http://status_dashboard/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Configuration Interface
        location /config/ {
            proxy_pass http://config_interface/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Media Pipeline Web UI
        location /pipeline/ {
            proxy_pass http://media_pipeline/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Syncthing
        location /syncthing/ {
            proxy_pass http://syncthing/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # VS Code Server
        location /vscode/ {
            proxy_pass http://vscode/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF

echo -e "${GREEN}✓ Nginx configuration created${NC}"

echo ""
echo -e "${BLUE}=== Step 4: Create Required Directories ===${NC}"

# Create required directories
echo -e "${GREEN}Creating required directories...${NC}"
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/config"
mkdir -p "$PROJECT_DIR/data/incoming"
mkdir -p "$PROJECT_DIR/data/processed"
mkdir -p "$PROJECT_DIR/syncthing"
mkdir -p "$PROJECT_DIR/vscode"
mkdir -p "$PROJECT_DIR/prometheus-data"
mkdir -p "$PROJECT_DIR/grafana-data"

# Set permissions
chmod 755 "$PROJECT_DIR/logs"
chmod 755 "$PROJECT_DIR/config"
chmod 755 "$PROJECT_DIR/data"
chmod 755 "$PROJECT_DIR/syncthing"
chmod 755 "$PROJECT_DIR/vscode"
chmod 755 "$PROJECT_DIR/prometheus-data"
chmod 755 "$PROJECT_DIR/grafana-data"

echo -e "${GREEN}✓ Required directories created${NC}"

echo ""
echo -e "${BLUE}=== Step 5: Create Environment File ===${NC}"

# Create .env file for Docker Compose
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

# VS Code Password
VSCODE_PASSWORD=your_password_here
EOF

echo -e "${GREEN}✓ Environment file created${NC}"

echo ""
echo -e "${BLUE}=== Step 6: Start Docker Services ===${NC}"

# Start Docker services
echo -e "${GREEN}Starting Docker services...${NC}"
cd "$PROJECT_DIR"
docker-compose up -d

echo -e "${GREEN}✓ Docker services started${NC}"

echo ""
echo -e "${BLUE}=== Step 7: Verify Services ===${NC}"

# Wait for services to start
sleep 10

# Check Docker services
echo -e "${GREEN}Docker Service Status:${NC}"
docker-compose ps

# Check ports
echo -e "${GREEN}Checking ports...${NC}"
ports=("80" "8080" "8081" "8082" "8083" "8384" "3000" "9090")
for port in "${ports[@]}"; do
    if netstat -tlnp | grep -q ":$port "; then
        echo -e "${GREEN}✓ Port $port: LISTENING${NC}"
    else
        echo -e "${YELLOW}⚠ Port $port: NOT LISTENING${NC}"
    fi
done

echo ""
echo -e "${GREEN}=== Docker-Based System Setup Complete! ===${NC}"
echo ""
echo -e "${BLUE}Access URLs:${NC}"
echo -e "${YELLOW}Status Dashboard:${NC} http://$CONTAINER_IP/status/"
echo -e "${YELLOW}Configuration Interface:${NC} http://$CONTAINER_IP/config/"
echo -e "${YELLOW}Media Pipeline Web UI:${NC} http://$CONTAINER_IP/pipeline/"
echo -e "${YELLOW}Syncthing:${NC} http://$CONTAINER_IP/syncthing/"
echo -e "${YELLOW}VS Code Server:${NC} http://$CONTAINER_IP/vscode/"
echo -e "${YELLOW}Grafana Dashboard:${NC} http://$CONTAINER_IP:3000"
echo -e "${YELLOW}Prometheus:${NC} http://$CONTAINER_IP:9090"
echo ""
echo -e "${BLUE}Direct Access URLs:${NC}"
echo -e "${YELLOW}Status Dashboard:${NC} http://$CONTAINER_IP:8082"
echo -e "${YELLOW}Configuration Interface:${NC} http://$CONTAINER_IP:8083"
echo -e "${YELLOW}Media Pipeline Web UI:${NC} http://$CONTAINER_IP:8081"
echo -e "${YELLOW}Syncthing:${NC} http://$CONTAINER_IP:8384"
echo -e "${YELLOW}VS Code Server:${NC} http://$CONTAINER_IP:8080"
echo ""
echo -e "${BLUE}Docker Management Commands:${NC}"
echo -e "${YELLOW}Check status:${NC} docker-compose ps"
echo -e "${YELLOW}View logs:${NC} docker-compose logs -f"
echo -e "${YELLOW}Restart all:${NC} docker-compose restart"
echo -e "${YELLOW}Stop all:${NC} docker-compose down"
echo -e "${YELLOW}Update services:${NC} docker-compose pull && docker-compose up -d"
echo ""
echo -e "${GREEN}🎉 Docker-Based System is now running! 🎉${NC}"
echo -e "${GREEN}Use Docker Compose to manage all services!${NC}"
