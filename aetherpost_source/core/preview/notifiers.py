"""Notification systems for content preview delivery."""

import asyncio
import logging
import json
import aiohttp
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import logging
from aetherpost.core.preview.generator import PreviewSession, ContentPreviewGenerator

logger = logging.getLogger(__name__)

@dataclass
class NotificationChannel:
    """Notification channel configuration."""
    name: str
    type: str  # slack, discord, teams, email, webhook
    webhook_url: Optional[str] = None
    email_recipients: Optional[List[str]] = None
    channel_id: Optional[str] = None
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.type,
            "webhook_url": self.webhook_url,
            "email_recipients": self.email_recipients,
            "channel_id": self.channel_id,
            "enabled": self.enabled
        }

class SlackNotifier:
    """Slack notification handler."""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.preview_generator = ContentPreviewGenerator()
    
    async def send_preview(self, session: PreviewSession, channel: NotificationChannel) -> Dict[str, Any]:
        """Send preview to Slack channel."""
        try:
            blocks = self.preview_generator.generate_slack_blocks(session)
            
            payload = {
                "channel": channel.channel_id or "#general",
                "username": "AetherPost",
                "icon_emoji": ":rocket:",
                "text": f"Content Preview Ready: {session.campaign_name}",
                "blocks": blocks
            }
            
            async with aiohttp.ClientSession() as session_http:
                async with session_http.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        logger.info(f"Slack notification sent successfully to {channel.name}")
                        return {"status": "success", "message": "Notification sent"}
                    else:
                        error_text = await response.text()
                        logger.error(f"Slack notification failed: {response.status} - {error_text}")
                        return {"status": "error", "message": f"HTTP {response.status}: {error_text}"}
        
        except Exception as e:
            logger.error(f"Exception sending Slack notification: {e}")
            return {"status": "error", "message": str(e)}
    
    async def send_approval_response(self, session_id: str, action: str, user: str, notes: str = "") -> Dict[str, Any]:
        """Send approval response notification."""
        try:
            color_map = {
                "approved": "good",
                "rejected": "danger", 
                "changes_requested": "warning"
            }
            
            attachment = {
                "color": color_map.get(action, "good"),
                "title": f"Campaign {action.replace('_', ' ').title()}",
                "fields": [
                    {
                        "title": "Session ID",
                        "value": session_id,
                        "short": True
                    },
                    {
                        "title": "Reviewed by",
                        "value": user,
                        "short": True
                    }
                ],
                "footer": "AetherPost Approval System",
                "ts": int(datetime.now().timestamp())
            }
            
            if notes:
                attachment["fields"].append({
                    "title": "Notes",
                    "value": notes,
                    "short": False
                })
            
            payload = {
                "text": f"Campaign {session_id} has been {action.replace('_', ' ')}",
                "attachments": [attachment]
            }
            
            async with aiohttp.ClientSession() as session_http:
                async with session_http.post(self.webhook_url, json=payload) as response:
                    return {"status": "success" if response.status == 200 else "error"}
        
        except Exception as e:
            logger.error(f"Error sending approval response: {e}")
            return {"status": "error", "message": str(e)}

class DiscordNotifier:
    """Discord notification handler."""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.preview_generator = ContentPreviewGenerator()
    
    async def send_preview(self, session: PreviewSession, channel: NotificationChannel) -> Dict[str, Any]:
        """Send preview to Discord channel."""
        try:
            embed = self.preview_generator.generate_discord_embed(session)
            
            payload = {
                "username": "AetherPost",
                "avatar_url": "https://via.placeholder.com/128/0099ff/ffffff?text=AP",
                "content": f"🚀 **Content Preview Ready**\nCampaign: {session.campaign_name}",
                "embeds": [embed]
            }
            
            async with aiohttp.ClientSession() as session_http:
                async with session_http.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status in [200, 204]:
                        logger.info(f"Discord notification sent successfully to {channel.name}")
                        return {"status": "success", "message": "Notification sent"}
                    else:
                        error_text = await response.text()
                        logger.error(f"Discord notification failed: {response.status} - {error_text}")
                        return {"status": "error", "message": f"HTTP {response.status}: {error_text}"}
        
        except Exception as e:
            logger.error(f"Exception sending Discord notification: {e}")
            return {"status": "error", "message": str(e)}

class TeamsNotifier:
    """Microsoft Teams notification handler."""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.preview_generator = ContentPreviewGenerator()
    
    async def send_preview(self, session: PreviewSession, channel: NotificationChannel) -> Dict[str, Any]:
        """Send preview to Teams channel."""
        try:
            # Teams uses Adaptive Cards format
            card = self._create_teams_card(session)
            
            payload = {
                "type": "message",
                "attachments": [
                    {
                        "contentType": "application/vnd.microsoft.card.adaptive",
                        "content": card
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session_http:
                async with session_http.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        logger.info(f"Teams notification sent successfully to {channel.name}")
                        return {"status": "success", "message": "Notification sent"}
                    else:
                        error_text = await response.text()
                        logger.error(f"Teams notification failed: {response.status} - {error_text}")
                        return {"status": "error", "message": f"HTTP {response.status}: {error_text}"}
        
        except Exception as e:
            logger.error(f"Exception sending Teams notification: {e}")
            return {"status": "error", "message": str(e)}
    
    def _create_teams_card(self, session: PreviewSession) -> Dict[str, Any]:
        """Create Teams Adaptive Card."""
        card = {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.3",
            "body": [
                {
                    "type": "TextBlock",
                    "text": f"📋 Content Preview: {session.campaign_name}",
                    "size": "Large",
                    "weight": "Bolder"
                },
                {
                    "type": "FactSet",
                    "facts": [
                        {
                            "title": "Session ID:",
                            "value": session.session_id
                        },
                        {
                            "title": "Platforms:",
                            "value": str(session.total_platforms)
                        },
                        {
                            "title": "Est. Reach:",
                            "value": f"{session.total_estimated_reach:,}"
                        },
                        {
                            "title": "Status:",
                            "value": session.approval_status.title()
                        }
                    ]
                }
            ]
        }
        
        # Add platform previews (limited for Teams)
        for i, item in enumerate(session.content_items[:3], 1):
            platform_config = self.preview_generator.platform_configs.get(item.platform, {})
            icon = platform_config.get("icon", "📱")
            display_name = platform_config.get("display_name", item.platform.title())
            
            content_preview = item.text[:300] + "..." if len(item.text) > 300 else item.text
            
            card["body"].append({
                "type": "TextBlock",
                "text": f"{i}. {icon} {display_name}",
                "weight": "Bolder",
                "spacing": "Medium"
            })
            
            card["body"].append({
                "type": "TextBlock",
                "text": content_preview,
                "wrap": True,
                "fontType": "Monospace"
            })
            
            card["body"].append({
                "type": "FactSet",
                "facts": [
                    {
                        "title": "Characters:",
                        "value": f"{item.character_count}" + (f"/{item.character_limit}" if item.character_limit else "")
                    },
                    {
                        "title": "Est. Reach:",
                        "value": f"{item.estimated_reach:,}"
                    },
                    {
                        "title": "Engagement:",
                        "value": f"{item.engagement_prediction:.1%}"
                    }
                ]
            })
        
        # Add action buttons
        card["actions"] = [
            {
                "type": "Action.Submit",
                "title": "✅ Approve",
                "style": "positive",
                "data": {
                    "action": "approve",
                    "session_id": session.session_id
                }
            },
            {
                "type": "Action.Submit",
                "title": "✏️ Request Changes",
                "data": {
                    "action": "request_changes",
                    "session_id": session.session_id
                }
            },
            {
                "type": "Action.Submit",
                "title": "❌ Reject",
                "style": "destructive",
                "data": {
                    "action": "reject",
                    "session_id": session.session_id
                }
            }
        ]
        
        return card

class EmailNotifier:
    """Email notification handler."""
    
    def __init__(self, smtp_config: Dict[str, str]):
        self.smtp_config = smtp_config
        self.preview_generator = ContentPreviewGenerator()
    
    async def send_preview(self, session: PreviewSession, channel: NotificationChannel) -> Dict[str, Any]:
        """Send preview via email."""
        try:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            from email.mime.base import MIMEBase
            from email import encoders
            
            # Generate HTML content
            html_content = self.preview_generator.generate_html_email_preview(session)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Content Preview: {session.campaign_name}"
            msg['From'] = self.smtp_config.get('from_email', 'autopromo@noreply.com')
            msg['To'] = ', '.join(channel.email_recipients)
            
            # Add HTML part
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_config['smtp_server'], int(self.smtp_config.get('smtp_port', 587))) as server:
                if self.smtp_config.get('use_tls', True):
                    server.starttls()
                if self.smtp_config.get('username') and self.smtp_config.get('password'):
                    server.login(self.smtp_config['username'], self.smtp_config['password'])
                
                server.send_message(msg)
            
            logger.info(f"Email notification sent successfully to {channel.email_recipients}")
            return {"status": "success", "message": "Email sent"}
        
        except Exception as e:
            logger.error(f"Exception sending email notification: {e}")
            return {"status": "error", "message": str(e)}

class WebhookNotifier:
    """Generic webhook notification handler."""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.preview_generator = ContentPreviewGenerator()
    
    async def send_preview(self, session: PreviewSession, channel: NotificationChannel) -> Dict[str, Any]:
        """Send preview to generic webhook."""
        try:
            payload = {
                "event": "content_preview",
                "session": session.to_dict(),
                "timestamp": datetime.now().isoformat(),
                "channel": channel.to_dict()
            }
            
            async with aiohttp.ClientSession() as session_http:
                async with session_http.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook notification sent successfully to {channel.name}")
                        return {"status": "success", "message": "Webhook called"}
                    else:
                        error_text = await response.text()
                        logger.error(f"Webhook notification failed: {response.status} - {error_text}")
                        return {"status": "error", "message": f"HTTP {response.status}: {error_text}"}
        
        except Exception as e:
            logger.error(f"Exception sending webhook notification: {e}")
            return {"status": "error", "message": str(e)}

class PreviewNotificationManager:
    """Manage all notification channels for preview delivery."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or Path.home() / ".aetherpost" / "notification_config.json"
        self.channels: List[NotificationChannel] = []
        self.preview_generator = ContentPreviewGenerator()
        self.load_configuration()
    
    def load_configuration(self) -> None:
        """Load notification configuration from file."""
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                    self.channels = [
                        NotificationChannel(**channel_data) 
                        for channel_data in config_data.get('channels', [])
                    ]
            else:
                logger.info("No notification configuration found. Using defaults.")
        except Exception as e:
            logger.error(f"Error loading notification configuration: {e}")
            self.channels = []
    
    def save_configuration(self) -> None:
        """Save notification configuration to file."""
        try:
            Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)
            config_data = {
                "channels": [channel.to_dict() for channel in self.channels],
                "updated_at": datetime.now().isoformat()
            }
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            logger.info(f"Notification configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving notification configuration: {e}")
    
    def add_channel(self, channel: NotificationChannel) -> None:
        """Add notification channel."""
        # Remove existing channel with same name
        self.channels = [c for c in self.channels if c.name != channel.name]
        self.channels.append(channel)
        self.save_configuration()
    
    def remove_channel(self, channel_name: str) -> bool:
        """Remove notification channel."""
        original_count = len(self.channels)
        self.channels = [c for c in self.channels if c.name != channel_name]
        if len(self.channels) < original_count:
            self.save_configuration()
            return True
        return False
    
    def get_channel(self, channel_name: str) -> Optional[NotificationChannel]:
        """Get notification channel by name."""
        return next((c for c in self.channels if c.name == channel_name), None)
    
    async def send_preview_to_all(self, session: PreviewSession) -> Dict[str, Any]:
        """Send preview to all enabled notification channels."""
        results = {}
        
        for channel in self.channels:
            if not channel.enabled:
                results[channel.name] = {"status": "skipped", "message": "Channel disabled"}
                continue
            
            try:
                result = await self.send_preview_to_channel(session, channel)
                results[channel.name] = result
            except Exception as e:
                logger.error(f"Error sending to channel {channel.name}: {e}")
                results[channel.name] = {"status": "error", "message": str(e)}
        
        return results
    
    async def send_preview_to_channel(self, session: PreviewSession, channel: NotificationChannel) -> Dict[str, Any]:
        """Send preview to specific notification channel."""
        
        if channel.type == "slack":
            notifier = SlackNotifier(channel.webhook_url)
            return await notifier.send_preview(session, channel)
        
        elif channel.type == "discord":
            notifier = DiscordNotifier(channel.webhook_url)
            return await notifier.send_preview(session, channel)
        
        elif channel.type == "teams":
            notifier = TeamsNotifier(channel.webhook_url)
            return await notifier.send_preview(session, channel)
        
        elif channel.type == "email":
            # Email requires SMTP configuration
            smtp_config = {
                'smtp_server': 'smtp.gmail.com',  # Default, should be configurable
                'smtp_port': 587,
                'use_tls': True,
                'from_email': 'autopromo@noreply.com'
            }
            notifier = EmailNotifier(smtp_config)
            return await notifier.send_preview(session, channel)
        
        elif channel.type == "webhook":
            notifier = WebhookNotifier(channel.webhook_url)
            return await notifier.send_preview(session, channel)
        
        else:
            return {"status": "error", "message": f"Unsupported channel type: {channel.type}"}
    
    def create_markdown_preview_file(self, session: PreviewSession, output_dir: str = "./previews") -> str:
        """Create markdown preview file."""
        output_path = Path(output_dir) / f"preview_{session.session_id}_{session.campaign_name.replace(' ', '_')}"
        return self.preview_generator.save_preview_to_file(session, str(output_path), "markdown")
    
    def create_json_preview_file(self, session: PreviewSession, output_dir: str = "./previews") -> str:
        """Create JSON preview file."""
        output_path = Path(output_dir) / f"preview_{session.session_id}_{session.campaign_name.replace(' ', '_')}"
        return self.preview_generator.save_preview_to_file(session, str(output_path), "json")

# Global instance
notification_manager = PreviewNotificationManager()