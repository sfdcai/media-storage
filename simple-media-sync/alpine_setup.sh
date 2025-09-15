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

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install --no-cache-dir -r requirements.txt

# Install icloudpd
echo "Installing icloudpd..."
pip3 install --no-cache-dir icloudpd

# Create workflow directories
echo "Creating workflow directories..."
mkdir -p incoming pixel_sync nas_archive processing icloud_delete backups

# Set permissions
echo "Setting permissions..."
chmod +x setup.py test_setup.py workflow_orchestrator.py
chmod +x steps/*.py

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

echo "✅ Alpine Linux setup complete!"
echo ""
echo "Next steps:"
echo "1. Run: python3 setup.py"
echo "2. Run: python3 test_setup.py"
echo "3. Start Syncthing: systemctl start syncthing"
echo "4. Run workflow: python3 workflow_orchestrator.py --workflow"
