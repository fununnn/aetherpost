"""Content preview generation for multiple output formats."""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import base64
from urllib.parse import quote

import logging

logger = logging.getLogger(__name__)

@dataclass
class PreviewContent:
    """Preview content structure."""
    platform: str
    content_type: str
    title: Optional[str]
    text: str
    hashtags: List[str]
    media_urls: List[str]
    scheduled_time: Optional[datetime]
    character_count: int
    character_limit: Optional[int]
    estimated_reach: Optional[int]
    engagement_prediction: Optional[float]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        if self.scheduled_time:
            data['scheduled_time'] = self.scheduled_time.isoformat()
        return data

@dataclass
class PreviewSession:
    """Preview session containing multiple content pieces."""
    session_id: str
    campaign_name: str
    created_at: datetime
    content_items: List[PreviewContent]
    total_platforms: int
    total_estimated_reach: int
    approval_status: str = "pending"  # pending, approved, rejected, partial
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "campaign_name": self.campaign_name,
            "created_at": self.created_at.isoformat(),
            "content_items": [item.to_dict() for item in self.content_items],
            "total_platforms": self.total_platforms,
            "total_estimated_reach": self.total_estimated_reach,
            "approval_status": self.approval_status
        }

class ContentPreviewGenerator:
    """Generate content previews in multiple formats."""
    
    def __init__(self):
        self.platform_configs = self._load_platform_configs()
    
    def _load_platform_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load platform-specific preview configurations."""
        return {
            "twitter": {
                "character_limit": 280,
                "display_name": "Twitter/X",
                "icon": "🐦",
                "preview_style": "card",
                "supports_media": True,
                "hashtag_color": "#1DA1F2"
            },
            "instagram": {
                "character_limit": 2200,
                "display_name": "Instagram",
                "icon": "📷",
                "preview_style": "visual",
                "supports_media": True,
                "hashtag_color": "#E4405F"
            },
            "reddit": {
                "character_limit": 40000,
                "display_name": "Reddit",
                "icon": "🔴",
                "preview_style": "text",
                "supports_media": True,
                "hashtag_color": "#FF4500"
            },
            "linkedin": {
                "character_limit": 3000,
                "display_name": "LinkedIn",
                "icon": "💼",
                "preview_style": "professional",
                "supports_media": True,
                "hashtag_color": "#0077B5"
            },
            "hackernews": {
                "character_limit": 80,  # Title limit
                "display_name": "Hacker News",
                "icon": "🟠",
                "preview_style": "minimal",
                "supports_media": False,
                "hashtag_color": "#FF6600"
            },
            "youtube": {
                "character_limit": 5000,
                "display_name": "YouTube",
                "icon": "📺",
                "preview_style": "video",
                "supports_media": True,
                "hashtag_color": "#FF0000"
            },
            "tiktok": {
                "character_limit": 300,
                "display_name": "TikTok",
                "icon": "🎵",
                "preview_style": "short_video",
                "supports_media": True,
                "hashtag_color": "#000000"
            }
        }
    
    def create_preview_session(self, campaign_name: str, content_items: List[Dict[str, Any]]) -> PreviewSession:
        """Create a new preview session."""
        import uuid
        
        session_id = str(uuid.uuid4())[:8]
        preview_items = []
        total_reach = 0
        
        for item in content_items:
            platform = item["platform"]
            config = self.platform_configs.get(platform, {})
            
            # Calculate character count
            text = item.get("text", "")
            char_count = len(text)
            char_limit = config.get("character_limit")
            
            # Estimate reach (mock calculation)
            estimated_reach = self._estimate_reach(platform, text)
            total_reach += estimated_reach
            
            # Estimate engagement (mock calculation)
            engagement_prediction = self._predict_engagement(platform, text)
            
            preview_content = PreviewContent(
                platform=platform,
                content_type=item.get("content_type", "announcement"),
                title=item.get("title"),
                text=text,
                hashtags=item.get("hashtags", []),
                media_urls=item.get("media_urls", []),
                scheduled_time=item.get("scheduled_time"),
                character_count=char_count,
                character_limit=char_limit,
                estimated_reach=estimated_reach,
                engagement_prediction=engagement_prediction
            )
            
            preview_items.append(preview_content)
        
        return PreviewSession(
            session_id=session_id,
            campaign_name=campaign_name,
            created_at=datetime.now(),
            content_items=preview_items,
            total_platforms=len(content_items),
            total_estimated_reach=total_reach
        )
    
    def _estimate_reach(self, platform: str, content: str) -> int:
        """Estimate potential reach for content on platform."""
        # Mock calculation - in real implementation, use historical data
        base_reach = {
            "twitter": 1500,
            "instagram": 2000,
            "reddit": 500,
            "linkedin": 800,
            "hackernews": 5000,
            "youtube": 10000,
            "tiktok": 3000
        }
        
        reach = base_reach.get(platform, 1000)
        
        # Adjust based on content quality indicators
        if len(content) > 100:
            reach *= 1.2
        if any(word in content.lower() for word in ["new", "announcing", "launch"]):
            reach *= 1.1
        if content.count("#") > 0:
            reach *= 1.05
            
        return int(reach)
    
    def _predict_engagement(self, platform: str, content: str) -> float:
        """Predict engagement rate for content."""
        # Mock calculation - in real implementation, use ML model
        base_rate = {
            "twitter": 0.045,
            "instagram": 0.018,
            "reddit": 0.08,
            "linkedin": 0.024,
            "hackernews": 0.15,
            "youtube": 0.03,
            "tiktok": 0.06
        }
        
        rate = base_rate.get(platform, 0.03)
        
        # Adjust based on content factors
        if "?" in content:  # Questions tend to get more engagement
            rate *= 1.3
        if len(content.split()) < 20:  # Short content performs better
            rate *= 1.1
        if any(word in content.lower() for word in ["tips", "how to", "guide"]):
            rate *= 1.2
            
        return round(rate, 3)
    
    def generate_markdown_preview(self, session: PreviewSession) -> str:
        """Generate markdown preview for the session."""
        
        # Header
        markdown = f"""# 📋 Content Preview: {session.campaign_name}

**Session ID:** `{session.session_id}`  
**Created:** {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}  
**Total Platforms:** {session.total_platforms}  
**Estimated Total Reach:** {session.total_estimated_reach:,}  
**Status:** {session.approval_status.title()}

---

"""
        
        # Content for each platform
        for i, item in enumerate(session.content_items, 1):
            config = self.platform_configs.get(item.platform, {})
            icon = config.get("icon", "📱")
            display_name = config.get("display_name", item.platform.title())
            
            # Character count with warning
            char_status = ""
            if item.character_limit:
                char_percentage = (item.character_count / item.character_limit) * 100
                if char_percentage > 100:
                    char_status = " ⚠️ **OVER LIMIT**"
                elif char_percentage > 90:
                    char_status = " ⚠️ **Near limit**"
                else:
                    char_status = " ✅"
            
            markdown += f"""## {i}. {icon} {display_name}

**Content Type:** {item.content_type.title()}  
**Character Count:** {item.character_count}"""
            
            if item.character_limit:
                markdown += f"/{item.character_limit}{char_status}"
            
            markdown += f"""  
**Estimated Reach:** {item.estimated_reach:,}  
**Engagement Rate:** {item.engagement_prediction:.1%}  
"""
            
            if item.scheduled_time:
                markdown += f"**Scheduled:** {item.scheduled_time.strftime('%Y-%m-%d %H:%M')}  \n"
            
            # Title (for platforms that support it)
            if item.title:
                markdown += f"""
**Title:**
> {item.title}
"""
            
            # Content
            markdown += f"""
**Content:**
```
{item.text}
```
"""
            
            # Hashtags
            if item.hashtags:
                hashtag_text = " ".join(f"#{tag}" for tag in item.hashtags)
                markdown += f"""
**Hashtags:** {hashtag_text}
"""
            
            # Media
            if item.media_urls:
                markdown += f"""
**Media:** {len(item.media_urls)} file(s)
"""
                for j, url in enumerate(item.media_urls, 1):
                    markdown += f"- Media {j}: {url}\n"
            
            markdown += "\n---\n\n"
        
        # Summary
        total_engagement = sum(item.estimated_reach * item.engagement_prediction for item in session.content_items)
        
        markdown += f"""## 📊 Campaign Summary

- **Total Estimated Reach:** {session.total_estimated_reach:,}
- **Total Estimated Engagement:** {int(total_engagement):,}
- **Average Engagement Rate:** {(total_engagement / session.total_estimated_reach * 100):.1f}%
- **Best Performing Platform:** {max(session.content_items, key=lambda x: x.engagement_prediction).platform.title()}

## ✅ Next Steps

1. Review content for accuracy and brand alignment
2. Verify scheduled times for optimal posting
3. Approve or request changes
4. Execute campaign when ready

---
*Generated by AetherPost Content Preview System*
"""
        
        return markdown
    
    def generate_slack_blocks(self, session: PreviewSession) -> List[Dict[str, Any]]:
        """Generate Slack Block Kit format for rich preview."""
        
        blocks = []
        
        # Header block
        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📋 Content Preview: {session.campaign_name}"
            }
        })
        
        # Summary section
        blocks.append({
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Session ID:*\n`{session.session_id}`"
                },
                {
                    "type": "mrkdwn", 
                    "text": f"*Total Platforms:*\n{session.total_platforms}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Estimated Reach:*\n{session.total_estimated_reach:,}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Status:*\n{session.approval_status.title()}"
                }
            ]
        })
        
        blocks.append({"type": "divider"})
        
        # Content blocks for each platform
        for i, item in enumerate(session.content_items, 1):
            config = self.platform_configs.get(item.platform, {})
            icon = config.get("icon", "📱")
            display_name = config.get("display_name", item.platform.title())
            
            # Character count status
            char_emoji = "✅"
            if item.character_limit and item.character_count > item.character_limit:
                char_emoji = "⚠️"
            elif item.character_limit and item.character_count > item.character_limit * 0.9:
                char_emoji = "⚠️"
            
            # Platform header
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{i}. {icon} {display_name}*"
                }
            })
            
            # Platform details
            char_text = f"{item.character_count}"
            if item.character_limit:
                char_text += f"/{item.character_limit}"
            
            blocks.append({
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Type:* {item.content_type.title()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Characters:* {char_emoji} {char_text}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Est. Reach:* {item.estimated_reach:,}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Engagement:* {item.engagement_prediction:.1%}"
                    }
                ]
            })
            
            # Content preview (truncated for Slack)
            content_preview = item.text
            if len(content_preview) > 500:
                content_preview = content_preview[:500] + "..."
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"```{content_preview}```"
                }
            })
            
            # Hashtags
            if item.hashtags:
                hashtag_text = " ".join(f"#{tag}" for tag in item.hashtags)
                blocks.append({
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Hashtags:* {hashtag_text}"
                        }
                    ]
                })
            
            blocks.append({"type": "divider"})
        
        # Action buttons
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "✅ Approve All"
                    },
                    "style": "primary",
                    "value": f"approve_all_{session.session_id}",
                    "action_id": "approve_all"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "✏️ Request Changes"
                    },
                    "value": f"request_changes_{session.session_id}",
                    "action_id": "request_changes"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "❌ Reject"
                    },
                    "style": "danger",
                    "value": f"reject_{session.session_id}",
                    "action_id": "reject"
                }
            ]
        })
        
        return blocks
    
    def generate_discord_embed(self, session: PreviewSession) -> Dict[str, Any]:
        """Generate Discord embed format for preview."""
        
        # Calculate summary stats
        total_engagement = sum(item.estimated_reach * item.engagement_prediction for item in session.content_items)
        avg_engagement = (total_engagement / session.total_estimated_reach * 100) if session.total_estimated_reach > 0 else 0
        
        embed = {
            "title": f"📋 Content Preview: {session.campaign_name}",
            "description": f"Review your scheduled content across {session.total_platforms} platforms",
            "color": 0x00ff00,  # Green
            "timestamp": session.created_at.isoformat(),
            "fields": [
                {
                    "name": "📊 Campaign Stats",
                    "value": f"**Total Reach:** {session.total_estimated_reach:,}\n**Avg. Engagement:** {avg_engagement:.1f}%\n**Session ID:** `{session.session_id}`",
                    "inline": True
                }
            ],
            "footer": {
                "text": "AetherPost Content Preview System"
            }
        }
        
        # Add platform content (limited to first 3 for Discord limits)
        for i, item in enumerate(session.content_items[:3], 1):
            config = self.platform_configs.get(item.platform, {})
            icon = config.get("icon", "📱")
            display_name = config.get("display_name", item.platform.title())
            
            content_preview = item.text
            if len(content_preview) > 200:
                content_preview = content_preview[:200] + "..."
            
            char_status = ""
            if item.character_limit and item.character_count > item.character_limit:
                char_status = " ⚠️"
            
            field_value = f"**Reach:** {item.estimated_reach:,} | **Engagement:** {item.engagement_prediction:.1%}\n"
            field_value += f"**Characters:** {item.character_count}"
            if item.character_limit:
                field_value += f"/{item.character_limit}{char_status}"
            field_value += f"\n```{content_preview}```"
            
            embed["fields"].append({
                "name": f"{i}. {icon} {display_name}",
                "value": field_value[:1024],  # Discord field limit
                "inline": False
            })
        
        # Add more platforms indicator
        if len(session.content_items) > 3:
            embed["fields"].append({
                "name": "➕ Additional Platforms",
                "value": f"And {len(session.content_items) - 3} more platforms...",
                "inline": False
            })
        
        return embed
    
    def save_preview_to_file(self, session: PreviewSession, output_path: str, format_type: str = "markdown") -> str:
        """Save preview to file in specified format."""
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        if format_type == "markdown":
            content = self.generate_markdown_preview(session)
            file_path = output_path if output_path.endswith('.md') else f"{output_path}.md"
        elif format_type == "json":
            content = json.dumps(session.to_dict(), indent=2, ensure_ascii=False)
            file_path = output_path if output_path.endswith('.json') else f"{output_path}.json"
        else:
            raise ValueError(f"Unsupported format: {format_type}")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Preview saved to {file_path}")
        return file_path
    
    def generate_html_email_preview(self, session: PreviewSession) -> str:
        """Generate HTML email preview."""
        
        # Calculate stats
        total_engagement = sum(item.estimated_reach * item.engagement_prediction for item in session.content_items)
        avg_engagement = (total_engagement / session.total_estimated_reach * 100) if session.total_estimated_reach > 0 else 0
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Content Preview: {session.campaign_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .platform {{ border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; margin-bottom: 15px; }}
        .platform-header {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; }}
        .content-preview {{ background: #f8f9fa; padding: 15px; border-radius: 4px; font-family: monospace; white-space: pre-wrap; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin: 15px 0; }}
        .stat {{ background: #e9ecef; padding: 10px; border-radius: 4px; text-align: center; }}
        .hashtags {{ color: #0066cc; }}
        .warning {{ color: #dc3545; font-weight: bold; }}
        .success {{ color: #28a745; font-weight: bold; }}
        .buttons {{ text-align: center; margin-top: 30px; }}
        .button {{ display: inline-block; padding: 10px 20px; margin: 0 10px; text-decoration: none; border-radius: 4px; font-weight: bold; }}
        .approve {{ background: #28a745; color: white; }}
        .change {{ background: #ffc107; color: black; }}
        .reject {{ background: #dc3545; color: white; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📋 Content Preview: {session.campaign_name}</h1>
        <div class="stats">
            <div class="stat">
                <strong>Session ID</strong><br>
                {session.session_id}
            </div>
            <div class="stat">
                <strong>Total Platforms</strong><br>
                {session.total_platforms}
            </div>
            <div class="stat">
                <strong>Estimated Reach</strong><br>
                {session.total_estimated_reach:,}
            </div>
            <div class="stat">
                <strong>Avg. Engagement</strong><br>
                {avg_engagement:.1f}%
            </div>
        </div>
    </div>
"""
        
        # Platform content
        for i, item in enumerate(session.content_items, 1):
            config = self.platform_configs.get(item.platform, {})
            icon = config.get("icon", "📱")
            display_name = config.get("display_name", item.platform.title())
            
            # Character count status
            char_class = "success"
            char_text = f"{item.character_count}"
            if item.character_limit:
                char_text += f"/{item.character_limit}"
                if item.character_count > item.character_limit:
                    char_class = "warning"
                    char_text += " (OVER LIMIT)"
                elif item.character_count > item.character_limit * 0.9:
                    char_class = "warning"
                    char_text += " (Near limit)"
            
            html += f"""
    <div class="platform">
        <div class="platform-header">{i}. {icon} {display_name}</div>
        <div class="stats">
            <div class="stat">
                <strong>Type</strong><br>
                {item.content_type.title()}
            </div>
            <div class="stat">
                <strong>Characters</strong><br>
                <span class="{char_class}">{char_text}</span>
            </div>
            <div class="stat">
                <strong>Est. Reach</strong><br>
                {item.estimated_reach:,}
            </div>
            <div class="stat">
                <strong>Engagement</strong><br>
                {item.engagement_prediction:.1%}
            </div>
        </div>
"""
            
            # Title
            if item.title:
                html += f"""
        <h3>Title:</h3>
        <div style="font-style: italic; margin-bottom: 10px;">{item.title}</div>
"""
            
            # Content
            html += f"""
        <h3>Content:</h3>
        <div class="content-preview">{item.text}</div>
"""
            
            # Hashtags
            if item.hashtags:
                hashtag_html = " ".join(f'<span class="hashtags">#{tag}</span>' for tag in item.hashtags)
                html += f"""
        <h3>Hashtags:</h3>
        <div>{hashtag_html}</div>
"""
            
            # Scheduled time
            if item.scheduled_time:
                html += f"""
        <h3>Scheduled:</h3>
        <div>{item.scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}</div>
"""
            
            html += "</div>"
        
        # Action buttons
        approve_url = f"mailto:?subject=APPROVE: {session.campaign_name}&body=Session ID: {session.session_id}%0A%0AApproved for publishing."
        change_url = f"mailto:?subject=CHANGES REQUESTED: {session.campaign_name}&body=Session ID: {session.session_id}%0A%0ARequested changes:%0A%0A[Please specify changes needed]"
        reject_url = f"mailto:?subject=REJECTED: {session.campaign_name}&body=Session ID: {session.session_id}%0A%0ARejected. Reason:%0A%0A[Please specify reason]"
        
        html += f"""
    <div class="buttons">
        <a href="{approve_url}" class="button approve">✅ Approve All</a>
        <a href="{change_url}" class="button change">✏️ Request Changes</a>
        <a href="{reject_url}" class="button reject">❌ Reject</a>
    </div>
    
    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; color: #6c757d; text-align: center;">
        Generated by AetherPost Content Preview System<br>
        {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}
    </div>
</body>
</html>
"""
        
        return html