"""State management for tracking campaign progress and results."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class PostRecord(BaseModel):
    """Record of a social media post."""
    id: str
    platform: str
    post_id: str
    url: str
    created_at: datetime
    content: Dict[str, Any]
    metrics: Dict[str, int] = {}
    status: str = "published"  # published, failed, deleted
    variant_id: Optional[str] = None


class MediaRecord(BaseModel):
    """Record of generated media."""
    id: str
    type: str  # image, video
    path: str
    provider: str
    created_at: datetime


class AnalyticsRecord(BaseModel):
    """Analytics summary."""
    total_reach: int = 0
    total_engagement: int = 0
    best_performing_variant: Optional[str] = None
    platform_performance: Dict[str, Dict[str, Any]] = {}


class CampaignState(BaseModel):
    """Complete campaign state."""
    version: str = "1.0"
    campaign_id: str
    created_at: datetime
    updated_at: datetime
    posts: List[PostRecord] = []
    media: List[MediaRecord] = []
    analytics: AnalyticsRecord = AnalyticsRecord()


class StateManager:
    """Manage campaign state persistence."""
    
    def __init__(self, state_file: str = "promo.state.json"):
        self.state_file = Path(state_file)
        self.state: Optional[CampaignState] = None
    
    def initialize_campaign(self, campaign_name: str) -> CampaignState:
        """Initialize a new campaign state."""
        campaign_id = f"campaign-{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow()
        
        self.state = CampaignState(
            campaign_id=campaign_id,
            created_at=now,
            updated_at=now
        )
        
        self.save_state()
        return self.state
    
    def load_state(self) -> Optional[CampaignState]:
        """Load campaign state from file."""
        if not self.state_file.exists():
            return None
        
        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)
            self.state = CampaignState(**data)
            return self.state
        except Exception as e:
            raise ValueError(f"Failed to load state: {e}")
    
    def save_state(self):
        """Save current state to file."""
        if not self.state:
            return
        
        self.state.updated_at = datetime.utcnow()
        
        with open(self.state_file, 'w') as f:
            json.dump(
                self.state.dict(),
                f,
                indent=2,
                default=str  # Handle datetime serialization
            )
    
    def add_post(self, 
                 platform: str,
                 post_id: str,
                 url: str,
                 content: Dict[str, Any],
                 variant_id: Optional[str] = None) -> PostRecord:
        """Add a new post record."""
        if not self.state:
            raise ValueError("No active campaign state")
        
        record = PostRecord(
            id=f"post-{uuid.uuid4().hex[:8]}",
            platform=platform,
            post_id=post_id,
            url=url,
            created_at=datetime.utcnow(),
            content=content,
            variant_id=variant_id
        )
        
        self.state.posts.append(record)
        self.save_state()
        return record
    
    def update_post_metrics(self, post_id: str, metrics: Dict[str, int]):
        """Update metrics for a specific post."""
        if not self.state:
            return
        
        for post in self.state.posts:
            if post.post_id == post_id:
                post.metrics.update(metrics)
                break
        
        self.save_state()
    
    def add_media(self, 
                  media_type: str,
                  path: str,
                  provider: str) -> MediaRecord:
        """Add a media record."""
        if not self.state:
            raise ValueError("No active campaign state")
        
        record = MediaRecord(
            id=f"media-{uuid.uuid4().hex[:8]}",
            type=media_type,
            path=path,
            provider=provider,
            created_at=datetime.utcnow()
        )
        
        self.state.media.append(record)
        self.save_state()
        return record
    
    def get_posts_by_platform(self, platform: str) -> List[PostRecord]:
        """Get all posts for a specific platform."""
        if not self.state:
            return []
        
        return [post for post in self.state.posts if post.platform == platform]
    
    def get_successful_posts(self) -> List[PostRecord]:
        """Get all successfully published posts."""
        if not self.state:
            return []
        
        return [post for post in self.state.posts if post.status == "published"]
    
    def calculate_analytics(self) -> AnalyticsRecord:
        """Calculate analytics from current posts."""
        if not self.state:
            return AnalyticsRecord()
        
        total_reach = 0
        total_engagement = 0
        platform_performance = {}
        
        for post in self.get_successful_posts():
            # Calculate reach and engagement
            metrics = post.metrics
            reach = metrics.get('impressions', 0) or metrics.get('views', 0)
            engagement = (
                metrics.get('likes', 0) + 
                metrics.get('retweets', 0) + 
                metrics.get('replies', 0) +
                metrics.get('clicks', 0)
            )
            
            total_reach += reach
            total_engagement += engagement
            
            # Platform performance
            if post.platform not in platform_performance:
                platform_performance[post.platform] = {
                    'posts': 0,
                    'total_reach': 0,
                    'total_engagement': 0
                }
            
            platform_performance[post.platform]['posts'] += 1
            platform_performance[post.platform]['total_reach'] += reach
            platform_performance[post.platform]['total_engagement'] += engagement
        
        analytics = AnalyticsRecord(
            total_reach=total_reach,
            total_engagement=total_engagement,
            platform_performance=platform_performance
        )
        
        self.state.analytics = analytics
        self.save_state()
        
        return analytics
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get a summary of the current state."""
        if not self.state:
            return {"status": "no_active_campaign"}
        
        return {
            "campaign_id": self.state.campaign_id,
            "created_at": self.state.created_at,
            "total_posts": len(self.state.posts),
            "successful_posts": len(self.get_successful_posts()),
            "platforms": list(set(post.platform for post in self.state.posts)),
            "total_media": len(self.state.media),
            "analytics": self.state.analytics.dict()
        }
    
    def remove_post(self, post_id: str) -> bool:
        """Remove a post from the state."""
        if not self.state:
            return False
        
        # Find and remove the post
        for i, post in enumerate(self.state.posts):
            if post.post_id == post_id:
                del self.state.posts[i]
                self.save_state()
                return True
        
        return False
    
    def clear_state(self) -> None:
        """Clear all campaign state."""
        if self.state_file.exists():
            self.state_file.unlink()
        self.state = None