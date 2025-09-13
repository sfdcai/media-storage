#!/bin/bash

# Complete Media Pipeline Installation Script
# This script installs everything needed for the media pipeline

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Complete Media Pipeline Installation ===${NC}"

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

echo -e "${BLUE}=== Step 1: Install System Packages ===${NC}"

# Install system packages
echo -e "${GREEN}Installing system packages...${NC}"
apt update
apt install -y nginx python3-pip python3-venv net-tools curl wget sqlite3

echo -e "${GREEN}✓ System packages installed${NC}"

echo ""
echo -e "${BLUE}=== Step 2: Install Node.js and PM2 ===${NC}"

# Install Node.js
echo -e "${GREEN}Installing Node.js...${NC}"
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Install PM2 globally
echo -e "${GREEN}Installing PM2...${NC}"
npm install -g pm2

echo -e "${GREEN}✓ Node.js and PM2 installed${NC}"

echo ""
echo -e "${BLUE}=== Step 3: Install Syncthing ===${NC}"

# Install Syncthing
echo -e "${GREEN}Installing Syncthing...${NC}"
curl -s https://syncthing.net/release-key.txt | apt-key add -
echo "deb https://apt.syncthing.net/ syncthing stable" > /etc/apt/sources.list.d/syncthing.list
apt update
apt install -y syncthing

echo -e "${GREEN}✓ Syncthing installed${NC}"

echo ""
echo -e "${BLUE}=== Step 4: Setup Python Virtual Environment ===${NC}"

# Create virtual environment
echo -e "${GREEN}Creating Python virtual environment...${NC}"
python3 -m venv "$PROJECT_DIR/venv"

# Install Python packages
echo -e "${GREEN}Installing Python packages...${NC}"
"$PROJECT_DIR/venv/bin/pip" install flask flask-socketio requests icloudpd

echo -e "${GREEN}✓ Python virtual environment created${NC}"

echo ""
echo -e "${BLUE}=== Step 5: Create Required Directories ===${NC}"

# Create required directories
echo -e "${GREEN}Creating required directories...${NC}"
mkdir -p /var/log/media-pipeline
mkdir -p /mnt/wd_all_pictures/incoming
mkdir -p /mnt/wd_all_pictures/processed
mkdir -p "$PROJECT_DIR/templates"

# Set ownership
chown -R "$SERVICE_USER:$SERVICE_USER" /var/log/media-pipeline
chown -R "$SERVICE_USER:$SERVICE_USER" /mnt/wd_all_pictures
chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR"

echo -e "${GREEN}✓ Required directories created${NC}"

echo ""
echo -e "${BLUE}=== Step 6: Create Database Web Viewer ===${NC}"

# Create database web viewer
echo -e "${GREEN}Creating database web viewer...${NC}"
cat > "$PROJECT_DIR/db_viewer.py" << 'EOF'
#!/usr/bin/env python3
"""
Database Web Viewer
A simple web interface to view the media pipeline database
"""

import os
import sys
import sqlite3
import json
from datetime import datetime
from pathlib import Path

# Add the project directory to Python path
project_dir = "/opt/media-pipeline"
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

try:
    from flask import Flask, render_template, jsonify, request
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])
    from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

class DatabaseViewer:
    """Database viewer for media pipeline"""
    
    def __init__(self):
        self.db_path = "/opt/media-pipeline/media.db"
        self.project_dir = "/opt/media-pipeline"
    
    def get_tables(self):
        """Get all tables in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            return tables
        except Exception as e:
            return []
    
    def get_table_data(self, table_name, limit=100):
        """Get data from a specific table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            
            # Get data
            cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
            rows = cursor.fetchall()
            
            conn.close()
            
            return {
                "columns": columns,
                "rows": rows,
                "count": len(rows)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_table_count(self, table_name):
        """Get row count for a table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            return 0
    
    def execute_query(self, query):
        """Execute a custom SQL query"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                conn.close()
                return {
                    "columns": columns,
                    "rows": rows,
                    "count": len(rows)
                }
            else:
                conn.commit()
                conn.close()
                return {"message": "Query executed successfully"}
        except Exception as e:
            return {"error": str(e)}

# Global database viewer
db_viewer = DatabaseViewer()

@app.route('/')
def index():
    """Main database viewer page"""
    return render_template('db_viewer.html')

@app.route('/api/tables')
def get_tables():
    """API endpoint to get all tables"""
    tables = db_viewer.get_tables()
    table_info = []
    for table in tables:
        count = db_viewer.get_table_count(table)
        table_info.append({"name": table, "count": count})
    return jsonify(table_info)

@app.route('/api/table/<table_name>')
def get_table_data(table_name):
    """API endpoint to get table data"""
    limit = request.args.get('limit', 100, type=int)
    return jsonify(db_viewer.get_table_data(table_name, limit))

@app.route('/api/query', methods=['POST'])
def execute_query():
    """API endpoint to execute custom queries"""
    data = request.get_json()
    query = data.get('query', '')
    return jsonify(db_viewer.execute_query(query))

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    templates_dir = os.path.join(project_dir, "templates")
    os.makedirs(templates_dir, exist_ok=True)
    
    # Create the database viewer template
    db_viewer_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Database Viewer</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .section { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .table-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .table-item { padding: 15px; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; text-align: center; }
        .table-item:hover { background-color: #f8f9fa; }
        .table-item.active { background-color: #007bff; color: white; }
        .data-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        .data-table th, .data-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .data-table th { background-color: #f2f2f2; }
        .query-section { margin-top: 20px; }
        .query-input { width: 100%; height: 100px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-family: monospace; }
        .btn { padding: 10px 20px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
        .btn:hover { background-color: #0056b3; }
        .btn-success { background-color: #28a745; }
        .btn-success:hover { background-color: #218838; }
        .error { background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 4px; margin: 10px 0; }
        .success { background-color: #d4edda; color: #155724; padding: 10px; border-radius: 4px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Media Pipeline Database Viewer</h1>
            <p>View and query the media pipeline database</p>
        </div>
        
        <div class="section">
            <h3>Database Tables</h3>
            <div id="tables" class="table-list">
                <div>Loading tables...</div>
            </div>
        </div>
        
        <div class="section">
            <h3>Table Data</h3>
            <div id="table-data">
                <p>Select a table to view its data</p>
            </div>
        </div>
        
        <div class="section">
            <h3>Custom Query</h3>
            <div class="query-section">
                <textarea id="query-input" class="query-input" placeholder="Enter SQL query here..."></textarea>
                <br>
                <button class="btn btn-success" onclick="executeQuery()">Execute Query</button>
                <button class="btn" onclick="clearQuery()">Clear</button>
            </div>
            <div id="query-result"></div>
        </div>
    </div>

    <script>
        let currentTable = null;
        
        // Load tables on page load
        fetch('/api/tables')
            .then(response => response.json())
            .then(tables => {
                const tablesDiv = document.getElementById('tables');
                tablesDiv.innerHTML = '';
                
                tables.forEach(table => {
                    const tableDiv = document.createElement('div');
                    tableDiv.className = 'table-item';
                    tableDiv.innerHTML = `
                        <strong>${table.name}</strong><br>
                        <small>${table.count} rows</small>
                    `;
                    tableDiv.onclick = () => loadTableData(table.name);
                    tablesDiv.appendChild(tableDiv);
                });
            });
        
        function loadTableData(tableName) {
            currentTable = tableName;
            
            // Update active table
            document.querySelectorAll('.table-item').forEach(item => {
                item.classList.remove('active');
            });
            event.target.closest('.table-item').classList.add('active');
            
            // Load table data
            fetch(`/api/table/${tableName}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        document.getElementById('table-data').innerHTML = `<div class="error">Error: ${data.error}</div>`;
                        return;
                    }
                    
                    let html = `<h4>Table: ${tableName} (${data.count} rows)</h4>`;
                    
                    if (data.rows.length > 0) {
                        html += '<table class="data-table">';
                        html += '<thead><tr>';
                        data.columns.forEach(column => {
                            html += `<th>${column}</th>`;
                        });
                        html += '</tr></thead><tbody>';
                        
                        data.rows.forEach(row => {
                            html += '<tr>';
                            row.forEach(cell => {
                                html += `<td>${cell || ''}</td>`;
                            });
                            html += '</tr>';
                        });
                        
                        html += '</tbody></table>';
                    } else {
                        html += '<p>No data found</p>';
                    }
                    
                    document.getElementById('table-data').innerHTML = html;
                });
        }
        
        function executeQuery() {
            const query = document.getElementById('query-input').value.trim();
            if (!query) {
                alert('Please enter a query');
                return;
            }
            
            fetch('/api/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({query: query})
            })
            .then(response => response.json())
            .then(data => {
                const resultDiv = document.getElementById('query-result');
                
                if (data.error) {
                    resultDiv.innerHTML = `<div class="error">Error: ${data.error}</div>`;
                    return;
                }
                
                if (data.message) {
                    resultDiv.innerHTML = `<div class="success">${data.message}</div>`;
                    return;
                }
                
                let html = `<h4>Query Result (${data.count} rows)</h4>`;
                
                if (data.rows.length > 0) {
                    html += '<table class="data-table">';
                    html += '<thead><tr>';
                    data.columns.forEach(column => {
                        html += `<th>${column}</th>`;
                    });
                    html += '</tr></thead><tbody>';
                    
                    data.rows.forEach(row => {
                        html += '<tr>';
                        row.forEach(cell => {
                            html += `<td>${cell || ''}</td>`;
                        });
                        html += '</tr>';
                    });
                    
                    html += '</tbody></table>';
                } else {
                    html += '<p>No results found</p>';
                }
                
                resultDiv.innerHTML = html;
            });
        }
        
        function clearQuery() {
            document.getElementById('query-input').value = '';
            document.getElementById('query-result').innerHTML = '';
        }
    </script>
</body>
</html>"""
    
    # Write the template file
    with open(os.path.join(templates_dir, "db_viewer.html"), "w") as f:
        f.write(db_viewer_template)
    
    print("Starting Database Viewer...")
    print("Database Viewer will be available at: http://0.0.0.0:8084")
    print("Press Ctrl+C to stop")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=8084, debug=False)
EOF

chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/db_viewer.py"
chmod +x "$PROJECT_DIR/db_viewer.py"

echo -e "${GREEN}✓ Database web viewer created${NC}"

echo ""
echo -e "${BLUE}=== Step 7: Create PM2 Ecosystem File ===${NC}"

# Create PM2 ecosystem file
echo -e "${GREEN}Creating PM2 ecosystem configuration...${NC}"
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
      name: 'db-viewer',
      script: 'db_viewer.py',
      interpreter: '/opt/media-pipeline/venv/bin/python',
      cwd: '/opt/media-pipeline',
      user: 'media-pipeline',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        PORT: 8084
      },
      error_file: '/var/log/media-pipeline/db-viewer-error.log',
      out_file: '/var/log/media-pipeline/db-viewer-out.log',
      log_file: '/var/log/media-pipeline/db-viewer.log',
      time: true
    },
    {
      name: 'syncthing',
      script: 'syncthing',
      args: '-gui-address=0.0.0.0:8385',
      cwd: '/home/media-pipeline',
      user: 'media-pipeline',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      error_file: '/var/log/media-pipeline/syncthing-error.log',
      out_file: '/var/log/media-pipeline/syncthing-out.log',
      log_file: '/var/log/media-pipeline/syncthing.log',
      time: true
    }
  ]
};
EOF

chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/ecosystem.config.js"

echo -e "${GREEN}✓ PM2 ecosystem configuration created${NC}"

echo ""
echo -e "${BLUE}=== Step 8: Configure Nginx ===${NC}"

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
    
    # Database Viewer
    location /db/ {
        proxy_pass http://127.0.0.1:8084/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Syncthing
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

# Syncthing Configuration
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
echo -e "${BLUE}=== Step 10: Start PM2 Applications ===${NC}"

# Start PM2 applications
echo -e "${GREEN}Starting PM2 applications...${NC}"
pm2 start "$PROJECT_DIR/ecosystem.config.js"

# Save PM2 configuration
pm2 save

echo -e "${GREEN}✓ PM2 applications started${NC}"

echo ""
echo -e "${BLUE}=== Step 11: Verify Services ===${NC}"

# Wait for services to start
sleep 5

# Check PM2 status
echo -e "${GREEN}PM2 Application Status:${NC}"
pm2 status

# Check ports
echo -e "${GREEN}Checking ports...${NC}"
ports=("80" "8080" "8082" "8083" "8084" "8385" "9615")
for port in "${ports[@]}"; do
    if netstat -tlnp | grep -q ":$port "; then
        echo -e "${GREEN}✓ Port $port: LISTENING${NC}"
    else
        echo -e "${YELLOW}⚠ Port $port: NOT LISTENING${NC}"
    fi
done

echo ""
echo -e "${GREEN}=== Installation Complete! ===${NC}"
echo ""
echo -e "${BLUE}Access URLs:${NC}"
echo -e "${YELLOW}PM2 Dashboard:${NC} http://$CONTAINER_IP:9615"
echo -e "${YELLOW}Status Dashboard:${NC} http://$CONTAINER_IP:8082"
echo -e "${YELLOW}Configuration Interface:${NC} http://$CONTAINER_IP:8083"
echo -e "${YELLOW}Database Viewer:${NC} http://$CONTAINER_IP:8084"
echo -e "${YELLOW}Syncthing:${NC} http://$CONTAINER_IP:8385"
echo -e "${YELLOW}VS Code Server:${NC} http://$CONTAINER_IP:8080"
echo ""
echo -e "${BLUE}Via Nginx:${NC}"
echo -e "${YELLOW}PM2 Dashboard:${NC} http://$CONTAINER_IP/pm2/"
echo -e "${YELLOW}Status Dashboard:${NC} http://$CONTAINER_IP/status/"
echo -e "${YELLOW}Configuration Interface:${NC} http://$CONTAINER_IP/config/"
echo -e "${YELLOW}Database Viewer:${NC} http://$CONTAINER_IP/db/"
echo -e "${YELLOW}Syncthing:${NC} http://$CONTAINER_IP/syncthing/"
echo -e "${YELLOW}VS Code Server:${NC} http://$CONTAINER_IP/vscode/"
echo ""
echo -e "${BLUE}CLI Commands:${NC}"
echo -e "${YELLOW}Test iCloud:${NC} /opt/media-pipeline/venv/bin/icloudpd --username YOUR_EMAIL --directory /mnt/wd_all_pictures/incoming --download-only --recent 5"
echo -e "${YELLOW}Run Pipeline:${NC} cd /opt/media-pipeline && source .env && /opt/media-pipeline/venv/bin/python pipeline_orchestrator.py"
echo -e "${YELLOW}View Database:${NC} sqlite3 /opt/media-pipeline/media.db"
echo ""
echo -e "${BLUE}PM2 Management:${NC}"
echo -e "${YELLOW}Check status:${NC} pm2 status"
echo -e "${YELLOW}View logs:${NC} pm2 logs"
echo -e "${YELLOW}Restart all:${NC} pm2 restart all"
echo ""
echo -e "${GREEN}🎉 Complete Media Pipeline System Installed! 🎉${NC}"
echo -e "${GREEN}Use the Database Viewer to explore your downloaded media data!${NC}"
