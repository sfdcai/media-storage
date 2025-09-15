#!/bin/bash
# Alpine Linux setup script for Media Sync Workflow

set -e

echo "=== Alpine Linux Media Sync Setup ==="

# Update package index
echo "Updating package index..."
apk update

# Install system dependencies
echo "Installing system dependencies..."
apk add --no-cache \
    python3 \
    python3-dev \
    py3-pip \
    ffmpeg \
    git \
    curl \
    bash \
    tzdata \
    jpeg-dev \
    zlib-dev \
    freetype-dev \
    lcms2-dev \
    openjpeg-dev \
    tiff-dev \
    tk-dev \
    tcl-dev

# Install Syncthing
echo "Installing Syncthing..."
apk add --no-cache syncthing

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv /opt/media-sync-env
source /opt/media-sync-env/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --no-cache-dir -r requirements.txt

# Install icloudpd
echo "Installing icloudpd..."
pip install --no-cache-dir icloudpd

# Create workflow directories
echo "Creating workflow directories..."
mkdir -p incoming pixel_sync nas_archive processing icloud_delete backups

# Set permissions
echo "Setting permissions..."
chmod +x setup.py test_setup.py workflow_orchestrator.py
chmod +x steps/*.py
chmod +x run_media_sync.sh

# Create systemd service for Syncthing (optional)
echo "Creating Syncthing service..."
cat > /etc/systemd/system/syncthing.service << EOF
[Unit]
Description=Syncthing
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/syncthing -no-browser -no-restart -logflags=0
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Enable Syncthing service
systemctl enable syncthing

# Install Media Sync service
echo "Installing Media Sync service..."
cp media-sync.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable media-sync

echo "✅ Alpine Linux setup complete!"
echo ""
echo "Next steps:"
echo "1. Run: ./run_media_sync.sh python3 setup.py"
echo "2. Run: ./run_media_sync.sh python3 test_setup.py"
echo "3. Start Syncthing: systemctl start syncthing"
echo "4. Run workflow: ./run_media_sync.sh python3 workflow_orchestrator.py --workflow"
echo ""
echo "Service management:"
echo "- Start service: systemctl start media-sync"
echo "- Stop service: systemctl stop media-sync"
echo "- View logs: journalctl -u media-sync -f"
echo ""
echo "Or activate virtual environment manually:"
echo "source /opt/media-sync-env/bin/activate"
echo "python3 setup.py"
