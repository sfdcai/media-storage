#!/usr/bin/env python3
"""
Telegram Notification Module
Sends notifications to Telegram about pipeline status and events
"""

import os
import logging
import requests
import json
from typing import Dict, Any, Optional
from datetime import datetime
from common import config_manager, get_logger

logger = get_logger(__name__)

class TelegramNotifier:
    """Handles Telegram notifications for the media pipeline"""
    
    def __init__(self):
        self.config = self._get_telegram_config()
        self.bot_token = self.config.get('bot_token') or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = self.config.get('chat_id') or os.getenv('TELEGRAM_CHAT_ID')
        self.enabled = self.config.get('enabled', True)
        
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram credentials not configured. Notifications disabled.")
            self.enabled = False
        else:
            logger.info("Telegram notifier initialized")
    
    def _get_telegram_config(self) -> Dict[str, Any]:
        """Get Telegram configuration from config file"""
        try:
            # Try to get from config file
            config_data = config_manager._config_data
            return config_data.get('telegram', {})
        except:
            return {}
    
    def _send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """Send a message to Telegram"""
        if not self.enabled:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            
            logger.debug("Telegram message sent successfully")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram message: {e}")
            return False
    
    def send_pipeline_start(self, stages: list) -> bool:
        """Send notification when pipeline starts"""
        if not self.config.get('notify_on_start', True):
            return True
        
        message = f"""
🚀 <b>Media Pipeline Started</b>

📅 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📋 <b>Stages:</b> {', '.join(stages)}
🖥️ <b>Server:</b> {os.uname().nodename}
        """.strip()
        
        return self._send_message(message)
    
    def send_pipeline_complete(self, results: Dict[str, Any]) -> bool:
        """Send notification when pipeline completes"""
        if not self.config.get('notify_on_completion', True):
            return True
        
        success = results.get('overall_success', False)
        duration = results.get('total_duration', 0)
        stages_count = len(results.get('stages', []))
        
        status_emoji = "✅" if success else "❌"
        status_text = "Completed Successfully" if success else "Completed with Errors"
        
        message = f"""
{status_emoji} <b>Media Pipeline {status_text}</b>

📅 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
⏱️ <b>Duration:</b> {duration:.1f} seconds
📊 <b>Stages Executed:</b> {stages_count}
🖥️ <b>Server:</b> {os.uname().nodename}
        """.strip()
        
        # Add stage details
        if results.get('stages'):
            message += "\n\n📋 <b>Stage Results:</b>"
            for stage in results['stages']:
                stage_name = stage.get('stage', 'unknown')
                stage_success = stage.get('success', False)
                stage_duration = stage.get('duration_seconds', 0)
                stage_emoji = "✅" if stage_success else "❌"
                message += f"\n{stage_emoji} {stage_name}: {stage_duration:.1f}s"
        
        return self._send_message(message)
    
    def send_pipeline_error(self, error_message: str, stage: str = None) -> bool:
        """Send notification when pipeline encounters an error"""
        if not self.config.get('notify_on_error', True):
            return True
        
        message = f"""
🚨 <b>Media Pipeline Error</b>

📅 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'📋 <b>Stage:</b> ' + stage if stage else ''}
🖥️ <b>Server:</b> {os.uname().nodename}

❌ <b>Error:</b>
<code>{error_message}</code>
        """.strip()
        
        return self._send_message(message)
    
    def send_stage_complete(self, stage: str, success: bool, duration: float, 
                           files_processed: int = 0, files_failed: int = 0) -> bool:
        """Send notification when a stage completes"""
        status_emoji = "✅" if success else "❌"
        status_text = "Completed" if success else "Failed"
        
        message = f"""
{status_emoji} <b>Stage {status_text}: {stage}</b>

📅 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
⏱️ <b>Duration:</b> {duration:.1f} seconds
📁 <b>Files Processed:</b> {files_processed}
{'❌ <b>Files Failed:</b> ' + str(files_failed) if files_failed > 0 else ''}
        """.strip()
        
        return self._send_message(message)
    
    def send_daily_summary(self, stats: Dict[str, Any]) -> bool:
        """Send daily summary of pipeline activity"""
        total_files = stats.get('total_files', 0)
        synced_google = stats.get('synced_google', 0)
        synced_nas = stats.get('synced_nas', 0)
        compressed = stats.get('compressed', 0)
        deleted = stats.get('deleted_icloud', 0)
        recent_activity = stats.get('recent_activity', 0)
        
        message = f"""
📊 <b>Daily Pipeline Summary</b>

📅 <b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}
🖥️ <b>Server:</b> {os.uname().nodename}

📈 <b>Statistics:</b>
• Total Files: {total_files}
• Synced to Google: {synced_google}
• Synced to NAS: {synced_nas}
• Compressed: {compressed}
• Deleted from iCloud: {deleted}
• Recent Activity (24h): {recent_activity}

💾 <b>Storage Status:</b>
{self._get_storage_info()}
        """.strip()
        
        return self._send_message(message)
    
    def send_system_alert(self, alert_type: str, message: str) -> bool:
        """Send system alert notification"""
        alert_emojis = {
            'disk_space': '💾',
            'service_down': '🔴',
            'high_error_rate': '⚠️',
            'backup_failed': '💥',
            'connection_lost': '🔌'
        }
        
        emoji = alert_emojis.get(alert_type, '🚨')
        
        alert_message = f"""
{emoji} <b>System Alert: {alert_type.replace('_', ' ').title()}</b>

📅 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🖥️ <b>Server:</b> {os.uname().nodename}

{message}
        """.strip()
        
        return self._send_message(alert_message)
    
    def _get_storage_info(self) -> str:
        """Get storage information for the system"""
        try:
            import shutil
            
            # Get disk usage for the main storage directory
            storage_path = "/mnt/wd_all_pictures"
            if os.path.exists(storage_path):
                total, used, free = shutil.disk_usage(storage_path)
                used_gb = used / (1024**3)
                total_gb = total / (1024**3)
                free_gb = free / (1024**3)
                usage_percent = (used / total) * 100
                
                return f"• Used: {used_gb:.1f} GB ({usage_percent:.1f}%)\n• Free: {free_gb:.1f} GB\n• Total: {total_gb:.1f} GB"
            else:
                return "• Storage path not accessible"
                
        except Exception as e:
            logger.error(f"Error getting storage info: {e}")
            return "• Storage info unavailable"
    
    def test_connection(self) -> bool:
        """Test Telegram connection"""
        if not self.enabled:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            bot_info = response.json()
            if bot_info.get('ok'):
                logger.info(f"Telegram connection test successful. Bot: {bot_info['result']['first_name']}")
                return True
            else:
                logger.error("Telegram connection test failed")
                return False
                
        except Exception as e:
            logger.error(f"Telegram connection test error: {e}")
            return False
    
    def send_test_message(self) -> bool:
        """Send a test message to verify configuration"""
        message = f"""
🧪 <b>Test Message</b>

📅 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🖥️ <b>Server:</b> {os.uname().nodename}

✅ Telegram notifications are working correctly!
        """.strip()
        
        return self._send_message(message)

# Global notifier instance
telegram_notifier = TelegramNotifier()

def send_pipeline_start(stages: list) -> bool:
    """Convenience function to send pipeline start notification"""
    return telegram_notifier.send_pipeline_start(stages)

def send_pipeline_complete(results: Dict[str, Any]) -> bool:
    """Convenience function to send pipeline completion notification"""
    return telegram_notifier.send_pipeline_complete(results)

def send_pipeline_error(error_message: str, stage: str = None) -> bool:
    """Convenience function to send pipeline error notification"""
    return telegram_notifier.send_pipeline_error(error_message, stage)

def send_stage_complete(stage: str, success: bool, duration: float, 
                       files_processed: int = 0, files_failed: int = 0) -> bool:
    """Convenience function to send stage completion notification"""
    return telegram_notifier.send_stage_complete(stage, success, duration, files_processed, files_failed)

def send_daily_summary(stats: Dict[str, Any]) -> bool:
    """Convenience function to send daily summary"""
    return telegram_notifier.send_daily_summary(stats)

def send_system_alert(alert_type: str, message: str) -> bool:
    """Convenience function to send system alert"""
    return telegram_notifier.send_system_alert(alert_type, message)

def test_telegram_connection() -> bool:
    """Convenience function to test Telegram connection"""
    return telegram_notifier.test_connection()

def send_test_message() -> bool:
    """Convenience function to send test message"""
    return telegram_notifier.send_test_message()
