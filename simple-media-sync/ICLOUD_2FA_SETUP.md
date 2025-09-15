# iCloud 2FA Setup Guide

This guide explains how to set up Two-Factor Authentication (2FA) for iCloud integration with the Media Sync Workflow.

## Overview

iCloud requires 2FA for security. The workflow supports both interactive and non-interactive modes:

- **Interactive Mode**: Prompts for 2FA codes when needed (recommended for initial setup)
- **Non-Interactive Mode**: Uses saved authentication cookies (for headless/automated runs)

## Initial Setup

### 1. Configure iCloud Credentials

```bash
# Run the setup script
python3 setup.py
```

Enter your iCloud username and password when prompted.

### 2. Setup 2FA Authentication

```bash
# Run the 2FA setup script
python3 setup_icloud_2fa.py
```

This will:
1. Prompt for your iCloud password
2. Prompt for a 2FA code from your trusted device
3. Save authentication cookies for future use
4. Mark your device as trusted in the configuration

### 3. Test the Setup

```bash
# Run the test script
python3 test_setup.py
```

Look for:
- ✅ iCloud device is already trusted
- ✅ iCloud connection test successful

## Configuration Options

### config.json

```json
{
  "icloud": {
    "username": "your@email.com",
    "password": "your_password",
    "download_dir": "./incoming",
    "icloudpd_path": "icloudpd",
    "trusted_device": true,
    "cookie_directory": "~/.pyiCloud",
    "interactive_mode": true
  }
}
```

### Key Settings:

- **`trusted_device`**: Set to `true` after successful 2FA setup
- **`cookie_directory`**: Where authentication cookies are stored
- **`interactive_mode`**: 
  - `true`: Prompts for 2FA codes (for manual runs)
  - `false`: Uses saved cookies (for automated/headless runs)

## Usage Modes

### Interactive Mode (Manual Runs)

```bash
# Run workflow manually
python3 workflow_orchestrator.py --workflow

# Run individual steps
python3 steps/step1_icloud_download.py
```

- Prompts for 2FA codes when needed
- Good for testing and manual runs
- Requires user interaction

### Non-Interactive Mode (Automated Runs)

```bash
# Set interactive_mode to false in config.json
# Then run headless
python3 headless_runner.py --once
```

- Uses saved authentication cookies
- No user interaction required
- Good for automated/scheduled runs

## Troubleshooting

### Common Issues

1. **"2FA setup failed"**
   - Check your password
   - Verify 2FA code is correct
   - Ensure network connectivity
   - Check if iCloud account is locked

2. **"iCloud connection test failed"**
   - Re-run 2FA setup: `python3 setup_icloud_2fa.py`
   - Check cookie directory permissions
   - Verify iCloud credentials

3. **"Device not trusted"**
   - Run 2FA setup again
   - Check `trusted_device` is set to `true` in config.json

### Reset 2FA Setup

```bash
# Delete cookies and reset
rm -rf ~/.pyiCloud
# Edit config.json: set "trusted_device": false
# Run setup again
python3 setup_icloud_2fa.py
```

## Security Notes

- Authentication cookies are stored locally in `~/.pyiCloud`
- Cookies contain session tokens, not your password
- Keep your config.json secure (contains password)
- Consider using environment variables for passwords in production

## Alpine Linux / Docker

For headless environments:

```bash
# Use non-interactive mode
# Set in config.headless.json:
{
  "icloud": {
    "interactive_mode": false,
    "trusted_device": true
  }
}
```

## Advanced Configuration

### Custom Cookie Directory

```json
{
  "icloud": {
    "cookie_directory": "/custom/path/.pyiCloud"
  }
}
```

### Environment Variables

```bash
export ICLOUD_USERNAME="your@email.com"
export ICLOUD_PASSWORD="your_password"
```

Then use in config:
```json
{
  "icloud": {
    "username": "${ICLOUD_USERNAME}",
    "password": "${ICLOUD_PASSWORD}"
  }
}
```

## Support

If you encounter issues:

1. Check the logs in `logs/` directory
2. Run `python3 test_setup.py` for diagnostics
3. Verify iCloud account status
4. Check network connectivity
5. Review icloudpd documentation: https://github.com/icloud-photos-downloader/icloud_photos_downloader
