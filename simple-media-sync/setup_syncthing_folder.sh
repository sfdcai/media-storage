#!/bin/bash
# Setup Syncthing folder with proper permissions

set -e

echo "=== Setting up Syncthing folder ==="

# Create the Syncthing directory
echo "📁 Creating Syncthing directory..."
sudo mkdir -p /var/lib/syncthing/pixel_sync

# Set proper ownership (Syncthing usually runs as syncthing user)
echo "🔧 Setting ownership..."
sudo chown -R syncthing:syncthing /var/lib/syncthing/pixel_sync

# Set proper permissions
echo "🔐 Setting permissions..."
sudo chmod -R 755 /var/lib/syncthing/pixel_sync

# Create the .stfolder marker (Syncthing needs this)
echo "📌 Creating Syncthing folder marker..."
sudo touch /var/lib/syncthing/pixel_sync/.stfolder
sudo chown syncthing:syncthing /var/lib/syncthing/pixel_sync/.stfolder

echo "✅ Syncthing folder setup complete!"
echo ""
echo "Folder location: /var/lib/syncthing/pixel_sync"
echo "Owner: syncthing:syncthing"
echo "Permissions: 755"
echo ""
echo "Now configure Syncthing to use this folder:"
echo "Folder Path: /var/lib/syncthing/pixel_sync"
echo "Folder ID: pixel_sync (or whatever you prefer)"
