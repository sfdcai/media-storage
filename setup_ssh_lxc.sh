#!/bin/bash

# SSH Setup Script for LXC Container
# This script sets up SSH access for remote debugging

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== SSH Setup for LXC Container ===${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}This script must be run as root${NC}"
    echo "Please run: sudo $0"
    exit 1
fi

# Install SSH server
echo -e "${GREEN}Installing OpenSSH server...${NC}"
apt update
apt install -y openssh-server

# Configure SSH
echo -e "${GREEN}Configuring SSH...${NC}"
cat > /etc/ssh/sshd_config << 'EOF'
# SSH Configuration for LXC Container
Port 22
Protocol 2
HostKey /etc/ssh/ssh_host_rsa_key
HostKey /etc/ssh/ssh_host_ecdsa_key
HostKey /etc/ssh/ssh_host_ed25519_key

# Authentication
PermitRootLogin yes
PasswordAuthentication yes
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys

# Security
X11Forwarding no
PrintMotd no
AcceptEnv LANG LC_*
Subsystem sftp /usr/lib/openssh/sftp-server

# Logging
SyslogFacility AUTH
LogLevel INFO
EOF

# Set root password if not set
if ! passwd -S root | grep -q "P"; then
    echo -e "${YELLOW}Setting root password...${NC}"
    echo "Please set a root password:"
    passwd root
fi

# Start and enable SSH service
echo -e "${GREEN}Starting SSH service...${NC}"
systemctl enable ssh
systemctl start ssh

# Get container IP
CONTAINER_IP=$(hostname -I | awk '{print $1}')

echo -e "${GREEN}=== SSH Setup Complete ===${NC}"
echo -e "${GREEN}SSH server is now running on port 22${NC}"
echo -e "${GREEN}Container IP: $CONTAINER_IP${NC}"
echo ""
echo -e "${BLUE}To connect from your host machine:${NC}"
echo -e "${YELLOW}ssh root@$CONTAINER_IP${NC}"
echo ""
echo -e "${BLUE}To connect from Windows using PowerShell:${NC}"
echo -e "${YELLOW}ssh root@$CONTAINER_IP${NC}"
echo ""
echo -e "${BLUE}To connect from Windows using PuTTY:${NC}"
echo -e "${YELLOW}Host: $CONTAINER_IP${NC}"
echo -e "${YELLOW}Port: 22${NC}"
echo -e "${YELLOW}Username: root${NC}"
echo ""
echo -e "${GREEN}SSH is now ready for remote access!${NC}"
