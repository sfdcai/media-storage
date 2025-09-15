#!/bin/bash
# Quick fix for Alpine Python externally-managed-environment error

echo "=== Fixing Alpine Python Environment ==="

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv /opt/media-sync-env

# Activate virtual environment
echo "Activating virtual environment..."
source /opt/media-sync-env/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --no-cache-dir -r requirements.txt

# Install icloudpd
echo "Installing icloudpd..."
pip install --no-cache-dir icloudpd

echo "✅ Virtual environment setup complete!"
echo ""
echo "To use the virtual environment:"
echo "1. Activate: source /opt/media-sync-env/bin/activate"
echo "2. Or use wrapper: ./run_media_sync.sh python3 setup.py"
