#!/bin/bash
# Update from git while preserving local config

set -e

echo "=== Updating from Git ==="

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not in a git repository. Please run this from the project directory."
    exit 1
fi

# Backup current config
echo "📋 Backing up current config..."
cp config.json config.json.backup

# Stash any local changes
echo "📦 Stashing local changes..."
git stash push -m "Local changes before update $(date)"

# Pull latest changes
echo "⬇️ Pulling latest changes..."
git pull origin main

# Restore config
echo "🔄 Restoring config..."
cp config.json.backup config.json

echo "✅ Update complete!"
echo ""
echo "Your config.json has been preserved."
echo "If you had any local changes, they were stashed."
echo "To see stashed changes: git stash list"
echo "To apply stashed changes: git stash pop"
