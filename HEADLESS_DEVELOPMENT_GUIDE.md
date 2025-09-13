# Headless LXC Development Guide

## ❌ Why Cursor AI Won't Work in Headless LXC

**Cursor AI is a desktop application that requires:**
- X11/Wayland display server
- Desktop environment (GNOME, KDE, XFCE, etc.)
- Window manager
- Graphics drivers
- GUI libraries

**Your headless LXC container has:**
- No display server
- No desktop environment
- No graphics capabilities
- Only command-line interface (CLI)

## ✅ Best Alternatives for Headless Development

### 1. VS Code Server (RECOMMENDED) 🌟

**Perfect for headless containers!**

```bash
# Install VS Code Server
chmod +x install_vscode_server.sh
./install_vscode_server.sh

# Set password and start
nano /etc/systemd/system/code-server.service
systemctl daemon-reload
systemctl enable code-server
systemctl start code-server
```

**Access via browser:** `http://your-container-ip:8080`

**Features:**
- ✅ Full VS Code experience in browser
- ✅ Extensions support
- ✅ Integrated terminal
- ✅ Git integration
- ✅ Remote development
- ✅ Access from any device

### 2. SSH + Local Editor

**Use your local machine's editor with SSH:**

```bash
# From Windows with VS Code
code --remote ssh-remote+root@your-container-ip /path/to/project

# From Windows with Cursor
# Install Remote-SSH extension, then connect to your container
```

### 3. Command Line Editors

**For quick edits:**

```bash
# Nano (user-friendly)
nano filename.py

# Vim (powerful)
vim filename.py

# Emacs (if you prefer)
apt install emacs
emacs filename.py
```

### 4. Web-based Terminals

**Access via web browser:**

```bash
# Install ttyd (web terminal)
apt install ttyd
ttyd -p 7681 bash

# Access at: http://your-container-ip:7681
```

## 🚀 Recommended Setup for Your Media Pipeline

### Step 1: Install VS Code Server
```bash
chmod +x install_vscode_server.sh
./install_vscode_server.sh
```

### Step 2: Configure VS Code Server
```bash
# Edit the service file
nano /etc/systemd/system/code-server.service

# Change the password line:
Environment=PASSWORD=your_secure_password_here

# Start the service
systemctl daemon-reload
systemctl enable code-server
systemctl start code-server
```

### Step 3: Access Your Development Environment
1. Open browser: `http://your-container-ip:8080`
2. Enter your password
3. Start coding!

### Step 4: Install Extensions
In VS Code Server, install these useful extensions:
- Python
- GitLens
- Remote Development
- Docker
- YAML
- JSON

## 🔧 Alternative: Remote Development from Windows

If you prefer using Cursor on your Windows machine:

### Option A: VS Code Remote-SSH
1. Install VS Code on Windows
2. Install "Remote - SSH" extension
3. Connect to your LXC container
4. Edit files directly on the container

### Option B: Cursor Remote-SSH
1. Install Cursor on Windows
2. Install "Remote - SSH" extension
3. Connect to your LXC container
4. Use Cursor's AI features on remote files

## 📝 Quick Commands Reference

```bash
# Check container IP
hostname -I

# Check if services are running
systemctl status code-server
systemctl status media-pipeline

# View logs
journalctl -u code-server -f
journalctl -u media-pipeline -f

# Restart services
systemctl restart code-server
systemctl restart media-pipeline
```

## 🎯 Summary

**For your headless LXC container:**
1. ❌ **Don't install Cursor** - it won't work
2. ✅ **Install VS Code Server** - perfect solution
3. ✅ **Access via browser** - works from any device
4. ✅ **Full development experience** - extensions, terminal, git

**VS Code Server gives you:**
- Full VS Code experience in your browser
- Access from Windows, Mac, Linux, or mobile
- No GUI required on the container
- Perfect for headless development
- All the features you need for your media pipeline project

## 🚀 Next Steps

1. Run `./install_vscode_server.sh`
2. Configure password in the service file
3. Start the service
4. Access via browser
5. Start developing your media pipeline!

Your enhanced `install.sh` script will now automatically detect headless systems and skip Cursor installation, recommending VS Code Server instead.
