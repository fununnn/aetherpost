"""Usage tracking for OSS edition limits."""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

from .edition import get_limit, is_enterprise

logger = logging.getLogger(__name__)


class UsageTracker:
    """Track usage for OSS edition limits."""
    
    def __init__(self):
        self.usage_file = Path.home() / ".aetherpost" / "usage.json"
        self.usage_file.parent.mkdir(exist_ok=True)
        self.usage_data = self._load_usage_data()
    
    def _load_usage_data(self) -> Dict[str, Any]:
        """Load usage data from file."""
        try:
            if self.usage_file.exists():
                with open(self.usage_file, 'r') as f:
                    data = json.load(f)
                    # Clean old data (older than 30 days)
                    self._clean_old_data(data)
                    return data
        except Exception as e:
            logger.warning(f"Could not load usage data: {e}")
        
        return {
            "posts": [],
            "campaigns": [],
            "platforms": set(),
            "last_reset": datetime.now().isoformat()
        }
    
    def _save_usage_data(self):
        """Save usage data to file."""
        try:
            # Convert sets to lists for JSON serialization
            data_to_save = self.usage_data.copy()
            if 'platforms' in data_to_save and isinstance(data_to_save['platforms'], set):
                data_to_save['platforms'] = list(data_to_save['platforms'])
            
            with open(self.usage_file, 'w') as f:
                json.dump(data_to_save, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save usage data: {e}")
    
    def _clean_old_data(self, data: Dict[str, Any]):
        """Remove old data to keep file size manageable."""
        cutoff_date = datetime.now() - timedelta(days=30)
        cutoff_str = cutoff_date.isoformat()
        
        # Clean old posts
        if 'posts' in data:
            data['posts'] = [p for p in data['posts'] if p.get('timestamp', '') > cutoff_str]
        
        # Clean old campaigns
        if 'campaigns' in data:
            data['campaigns'] = [c for c in data['campaigns'] if c.get('created', '') > cutoff_str]
    
    def check_daily_post_limit(self) -> bool:
        """Check if daily post limit is reached."""
        if is_enterprise():
            return True  # No limits for enterprise
        
        max_posts = get_limit('max_posts_per_day')
        today = datetime.now().date()
        
        today_posts = [
            p for p in self.usage_data.get('posts', [])
            if datetime.fromisoformat(p['timestamp']).date() == today
        ]
        
        return len(today_posts) < max_posts
    
    def check_platform_limit(self, platforms: list) -> bool:
        """Check if platform limit is reached."""
        if is_enterprise():
            return True  # No limits for enterprise
        
        max_platforms = get_limit('max_platforms')
        used_platforms = set(self.usage_data.get('platforms', []))
        new_platforms = set(platforms) - used_platforms
        
        return len(used_platforms) + len(new_platforms) <= max_platforms
    
    def check_campaign_limit(self) -> bool:
        """Check if campaign limit is reached."""
        if is_enterprise():
            return True  # No limits for enterprise
        
        max_campaigns = get_limit('max_campaigns')
        active_campaigns = len(self.usage_data.get('campaigns', []))
        
        return active_campaigns < max_campaigns
    
    def record_post(self, platforms: list, message: str):
        """Record a post for usage tracking."""
        post_record = {
            'timestamp': datetime.now().isoformat(),
            'platforms': platforms,
            'message_length': len(message)
        }
        
        self.usage_data.setdefault('posts', []).append(post_record)
        
        # Update used platforms
        platform_set = set(self.usage_data.get('platforms', []))
        platform_set.update(platforms)
        self.usage_data['platforms'] = platform_set
        
        self._save_usage_data()
        logger.info(f"Recorded post to {len(platforms)} platforms")
    
    def record_campaign(self, campaign_name: str):
        """Record a campaign creation."""
        campaign_record = {
            'name': campaign_name,
            'created': datetime.now().isoformat()
        }
        
        self.usage_data.setdefault('campaigns', []).append(campaign_record)
        self._save_usage_data()
        logger.info(f"Recorded campaign: {campaign_name}")
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get current usage summary."""
        today = datetime.now().date()
        today_posts = [
            p for p in self.usage_data.get('posts', [])
            if datetime.fromisoformat(p['timestamp']).date() == today
        ]
        
        return {
            'posts_today': len(today_posts),
            'max_posts_per_day': get_limit('max_posts_per_day'),
            'platforms_used': len(set(self.usage_data.get('platforms', []))),
            'max_platforms': get_limit('max_platforms'),
            'active_campaigns': len(self.usage_data.get('campaigns', [])),
            'max_campaigns': get_limit('max_campaigns'),
            'is_enterprise': is_enterprise()
        }
    
    def get_limits_message(self) -> str:
        """Get user-friendly limits message."""
        summary = self.get_usage_summary()
        
        if summary['is_enterprise']:
            return "✨ Enterprise Edition - Unlimited usage"
        
        return (
            f"📊 Usage (OSS Edition):\n"
            f"  • Posts today: {summary['posts_today']}/{summary['max_posts_per_day']}\n"
            f"  • Platforms: {summary['platforms_used']}/{summary['max_platforms']}\n"
            f"  • Campaigns: {summary['active_campaigns']}/{summary['max_campaigns']}\n"
            f"  \n"
            f"🚀 Upgrade to Enterprise for unlimited usage"
        )


# Global usage tracker instance
usage_tracker = UsageTracker()


def check_daily_post_limit() -> bool:
    """Check daily post limit."""
    return usage_tracker.check_daily_post_limit()


def check_platform_limit(platforms: list) -> bool:
    """Check platform limit."""
    return usage_tracker.check_platform_limit(platforms)


def check_campaign_limit() -> bool:
    """Check campaign limit."""
    return usage_tracker.check_campaign_limit()


def record_post(platforms: list, message: str):
    """Record a post."""
    usage_tracker.record_post(platforms, message)


def record_campaign(campaign_name: str):
    """Record a campaign."""
    usage_tracker.record_campaign(campaign_name)


def get_usage_summary() -> Dict[str, Any]:
    """Get usage summary."""
    return usage_tracker.get_usage_summary()


def get_limits_message() -> str:
    """Get limits message."""
    return usage_tracker.get_limits_message()