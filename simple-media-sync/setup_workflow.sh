#!/bin/bash
# Setup workflow for media sync

set -e

echo "=== Media Sync Workflow Setup ==="

# Check if config exists
if [ ! -f "config.json" ]; then
    echo "❌ config.json not found. Please run setup first:"
    echo "python3 setup.py"
    exit 1
fi

# Create workflow directories
echo "📁 Creating workflow directories..."
mkdir -p incoming pixel_sync nas_archive processing icloud_delete backups

# Set permissions
echo "🔧 Setting permissions..."
chmod +x setup.py test_setup.py workflow_orchestrator.py
chmod +x steps/*.py
chmod +x update_from_git.sh

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Test setup: python3 test_setup.py"
echo "2. Run Step 1: python3 steps/step1_icloud_download.py"
echo "3. Run Step 2: python3 steps/step2_pixel_sync.py"
echo "4. Or run full workflow: python3 workflow_orchestrator.py --workflow"
