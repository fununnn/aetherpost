"""Core posting scheduler implementation."""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

from .models import ScheduleConfig, ScheduledPost, FrequencyType, ScheduleStatus
from ..config.parser import ConfigLoader
from ..content.generator import ContentGenerator
from ..state.manager import StateManager
from ..exceptions import AetherPostError, ErrorCode
from ...platforms.core.platform_factory import platform_factory

logger = logging.getLogger(__name__)


class PostingScheduler:
    """Manages automated posting schedules."""
    
    def __init__(self, aetherpost_dir: str = ".aetherpost"):
        """Initialize scheduler."""
        self.aetherpost_dir = Path(aetherpost_dir)
        self.schedule_file = self.aetherpost_dir / "schedule.json"
        self.config_loader = ConfigLoader()
        self.state_manager = StateManager()
        
        # Ensure directory exists
        self.aetherpost_dir.mkdir(exist_ok=True)
    
    def create_schedule(
        self, 
        campaign_file: str = "campaign.yaml",
        platforms: Optional[List[str]] = None
    ) -> ScheduleConfig:
        """Create a posting schedule from campaign configuration."""
        
        # Load campaign config
        config = self.config_loader.load_campaign_config(campaign_file)
        
        # Extract scheduling parameters
        frequency = config.get("content", {}).get("frequency", "daily")
        posting_time = config.get("content", {}).get("posting_time", "09:00")
        timezone = config.get("content", {}).get("timezone", "UTC")
        max_posts = config.get("limits", {}).get("max_posts_per_day", 10)
        
        # Parse frequency
        try:
            freq_type = FrequencyType(frequency)
        except ValueError:
            freq_type = FrequencyType.DAILY
        
        # Parse posting time
        try:
            hour, minute = map(int, posting_time.split(":"))
            start_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
        except:
            start_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Determine platforms
        if not platforms:
            platforms = config.get("platforms", ["twitter", "bluesky"])
        
        # Create schedule config
        schedule_config = ScheduleConfig(
            frequency=freq_type,
            start_time=start_time,
            timezone=timezone,
            max_posts_per_day=max_posts,
            enabled=True
        )
        
        logger.info(f"Created schedule: {freq_type.value} posts starting at {start_time}")
        return schedule_config
    
    def generate_scheduled_posts(
        self,
        schedule_config: ScheduleConfig,
        campaign_file: str = "campaign.yaml",
        platforms: Optional[List[str]] = None,
        duration_days: int = 30
    ) -> List[ScheduledPost]:
        """Generate scheduled posts for a given duration."""
        
        if not platforms:
            config = self.config_loader.load_campaign_config(campaign_file)
            platforms = config.get("platforms", ["twitter", "bluesky"])
        
        scheduled_posts = []
        current_time = schedule_config.start_time
        end_time = current_time + timedelta(days=duration_days)
        
        while current_time < end_time:
            # Calculate next posting times based on frequency
            if schedule_config.frequency == FrequencyType.HOURLY:
                next_times = self._generate_hourly_times(current_time, schedule_config)
            elif schedule_config.frequency == FrequencyType.DAILY:
                next_times = self._generate_daily_times(current_time, schedule_config)
            elif schedule_config.frequency == FrequencyType.WEEKLY:
                next_times = self._generate_weekly_times(current_time, schedule_config)
            else:
                next_times = [current_time]
            
            for post_time in next_times:
                if post_time > end_time:
                    break
                
                # Create scheduled post
                scheduled_post = ScheduledPost(
                    id=str(uuid.uuid4()),
                    campaign_file=campaign_file,
                    scheduled_time=post_time,
                    platforms=platforms.copy()
                )
                scheduled_posts.append(scheduled_post)
            
            # Move to next period
            if schedule_config.frequency == FrequencyType.DAILY:
                current_time += timedelta(days=1)
            elif schedule_config.frequency == FrequencyType.WEEKLY:
                current_time += timedelta(weeks=1)
            elif schedule_config.frequency == FrequencyType.HOURLY:
                current_time += timedelta(hours=24)  # Generate for next day
            else:
                break
        
        logger.info(f"Generated {len(scheduled_posts)} scheduled posts for {duration_days} days")
        return scheduled_posts
    
    def _generate_hourly_times(self, base_time: datetime, config: ScheduleConfig) -> List[datetime]:
        """Generate hourly posting times."""
        times = []
        for hour in config.posting_hours:
            post_time = base_time.replace(hour=hour, minute=0, second=0, microsecond=0)
            if post_time >= base_time:
                times.append(post_time)
        return times[:config.max_posts_per_day]
    
    def _generate_daily_times(self, base_time: datetime, config: ScheduleConfig) -> List[datetime]:
        """Generate daily posting times."""
        if base_time.weekday() not in config.days_of_week:
            return []
        
        post_time = base_time.replace(
            hour=config.posting_hours[0] if config.posting_hours else 9,
            minute=0, 
            second=0, 
            microsecond=0
        )
        return [post_time]
    
    def _generate_weekly_times(self, base_time: datetime, config: ScheduleConfig) -> List[datetime]:
        """Generate weekly posting times."""
        times = []
        for day_of_week in config.days_of_week:
            # Calculate days until target day of week
            days_ahead = day_of_week - base_time.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            
            target_date = base_time + timedelta(days=days_ahead)
            post_time = target_date.replace(
                hour=config.posting_hours[0] if config.posting_hours else 9,
                minute=0,
                second=0,
                microsecond=0
            )
            times.append(post_time)
        
        return times
    
    def save_schedule(self, scheduled_posts: List[ScheduledPost]):
        """Save scheduled posts to disk."""
        schedule_data = {
            "version": "1.0",
            "created_at": datetime.utcnow().isoformat(),
            "posts": []
        }
        
        for post in scheduled_posts:
            post_data = {
                "id": post.id,
                "campaign_file": post.campaign_file,
                "scheduled_time": post.scheduled_time.isoformat(),
                "platforms": post.platforms,
                "status": post.status.value,
                "created_at": post.created_at.isoformat(),
                "attempts": post.attempts,
                "max_attempts": post.max_attempts,
                "last_error": post.last_error,
                "posted_at": post.posted_at.isoformat() if post.posted_at else None,
                "post_ids": post.post_ids
            }
            schedule_data["posts"].append(post_data)
        
        with open(self.schedule_file, 'w', encoding='utf-8') as f:
            json.dump(schedule_data, f, indent=2)
        
        logger.info(f"Saved {len(scheduled_posts)} scheduled posts to {self.schedule_file}")
    
    def load_schedule(self) -> List[ScheduledPost]:
        """Load scheduled posts from disk."""
        if not self.schedule_file.exists():
            return []
        
        try:
            with open(self.schedule_file, 'r', encoding='utf-8') as f:
                schedule_data = json.load(f)
            
            scheduled_posts = []
            for post_data in schedule_data.get("posts", []):
                post = ScheduledPost(
                    id=post_data["id"],
                    campaign_file=post_data["campaign_file"],
                    scheduled_time=datetime.fromisoformat(post_data["scheduled_time"]),
                    platforms=post_data["platforms"],
                    status=ScheduleStatus(post_data["status"]),
                    created_at=datetime.fromisoformat(post_data["created_at"]),
                    attempts=post_data.get("attempts", 0),
                    max_attempts=post_data.get("max_attempts", 3),
                    last_error=post_data.get("last_error"),
                    posted_at=datetime.fromisoformat(post_data["posted_at"]) if post_data.get("posted_at") else None,
                    post_ids=post_data.get("post_ids", {})
                )
                scheduled_posts.append(post)
            
            logger.info(f"Loaded {len(scheduled_posts)} scheduled posts from {self.schedule_file}")
            return scheduled_posts
            
        except Exception as e:
            logger.error(f"Error loading schedule: {e}")
            return []
    
    def get_pending_posts(self, until_time: Optional[datetime] = None) -> List[ScheduledPost]:
        """Get posts that are ready to be posted."""
        scheduled_posts = self.load_schedule()
        
        if until_time is None:
            until_time = datetime.utcnow()
        
        pending_posts = []
        for post in scheduled_posts:
            if (post.status == ScheduleStatus.PENDING and 
                post.scheduled_time <= until_time):
                pending_posts.append(post)
            elif (post.status == ScheduleStatus.FAILED and 
                  post.can_retry() and 
                  post.scheduled_time <= until_time):
                pending_posts.append(post)
        
        return pending_posts
    
    async def execute_scheduled_post(self, scheduled_post: ScheduledPost) -> bool:
        """Execute a scheduled post."""
        logger.info(f"Executing scheduled post {scheduled_post.id}")
        
        try:
            # Mark as running
            scheduled_post.status = ScheduleStatus.RUNNING
            self._update_post_in_schedule(scheduled_post)
            
            # Load configuration and credentials
            config = self.config_loader.load_campaign_config(scheduled_post.campaign_file)
            credentials = self.config_loader.load_credentials()
            
            # Generate content
            content_generator = ContentGenerator(config)
            content_items = await content_generator.generate_content(
                platforms=scheduled_post.platforms
            )
            
            # Post to each platform
            posted_ids = {}
            for platform_name in scheduled_post.platforms:
                try:
                    # Get platform content
                    platform_content = next(
                        (item for item in content_items if item.platform == platform_name), 
                        None
                    )
                    
                    if not platform_content:
                        logger.warning(f"No content generated for {platform_name}")
                        continue
                    
                    # Get platform credentials
                    if isinstance(credentials, dict):
                        platform_credentials = credentials.get(platform_name, {})
                    else:
                        platform_credentials = getattr(credentials, platform_name, {})
                    
                    if hasattr(platform_credentials, '__dict__'):
                        platform_credentials = platform_credentials.__dict__
                    
                    if not platform_credentials:
                        logger.warning(f"No credentials for {platform_name}")
                        continue
                    
                    # Create platform instance
                    platform_instance = platform_factory.create_platform(
                        platform_name=platform_name,
                        credentials=platform_credentials
                    )
                    
                    # Authenticate and post
                    if await platform_instance.authenticate():
                        post_result = await platform_instance.post_content(platform_content.content)
                        
                        if post_result.success and post_result.post_id:
                            posted_ids[platform_name] = post_result.post_id
                            logger.info(f"Posted to {platform_name}: {post_result.post_id}")
                            
                            # Save to state
                            from ..state.models import CampaignPost
                            campaign_post = CampaignPost(
                                post_id=post_result.post_id,
                                platform=platform_name,
                                content=platform_content.content.dict(),
                                created_at=datetime.utcnow()
                            )
                            self.state_manager.add_post(campaign_post)
                        else:
                            logger.error(f"Failed to post to {platform_name}: {post_result.error_message}")
                    
                    # Cleanup
                    await platform_instance.cleanup()
                    
                except Exception as e:
                    logger.error(f"Error posting to {platform_name}: {e}")
            
            # Mark as completed or failed
            if posted_ids:
                scheduled_post.mark_completed(posted_ids)
                logger.info(f"Scheduled post {scheduled_post.id} completed successfully")
            else:
                scheduled_post.mark_attempt("No successful posts")
                logger.error(f"Scheduled post {scheduled_post.id} failed - no successful posts")
            
            # Update schedule
            self._update_post_in_schedule(scheduled_post)
            return bool(posted_ids)
            
        except Exception as e:
            logger.error(f"Error executing scheduled post {scheduled_post.id}: {e}")
            scheduled_post.mark_attempt(str(e))
            self._update_post_in_schedule(scheduled_post)
            return False
    
    def _update_post_in_schedule(self, updated_post: ScheduledPost):
        """Update a specific post in the saved schedule."""
        scheduled_posts = self.load_schedule()
        
        for i, post in enumerate(scheduled_posts):
            if post.id == updated_post.id:
                scheduled_posts[i] = updated_post
                break
        
        self.save_schedule(scheduled_posts)
    
    def cleanup_old_posts(self, days_old: int = 30):
        """Remove old completed/failed posts from schedule."""
        scheduled_posts = self.load_schedule()
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        active_posts = []
        for post in scheduled_posts:
            if (post.status in [ScheduleStatus.PENDING, ScheduleStatus.RUNNING] or 
                post.scheduled_time > cutoff_date):
                active_posts.append(post)
        
        if len(active_posts) < len(scheduled_posts):
            removed_count = len(scheduled_posts) - len(active_posts)
            self.save_schedule(active_posts)
            logger.info(f"Cleaned up {removed_count} old scheduled posts")
    
    def pause_schedule(self):
        """Pause all pending posts."""
        scheduled_posts = self.load_schedule()
        
        for post in scheduled_posts:
            if post.status == ScheduleStatus.PENDING:
                post.status = ScheduleStatus.PAUSED
        
        self.save_schedule(scheduled_posts)
        logger.info("Paused all pending scheduled posts")
    
    def resume_schedule(self):
        """Resume all paused posts."""
        scheduled_posts = self.load_schedule()
        
        for post in scheduled_posts:
            if post.status == ScheduleStatus.PAUSED:
                post.status = ScheduleStatus.PENDING
        
        self.save_schedule(scheduled_posts)
        logger.info("Resumed all paused scheduled posts")
    
    def get_schedule_stats(self) -> Dict[str, Any]:
        """Get statistics about the current schedule."""
        scheduled_posts = self.load_schedule()
        
        stats = {
            "total_posts": len(scheduled_posts),
            "pending": len([p for p in scheduled_posts if p.status == ScheduleStatus.PENDING]),
            "completed": len([p for p in scheduled_posts if p.status == ScheduleStatus.COMPLETED]),
            "failed": len([p for p in scheduled_posts if p.status == ScheduleStatus.FAILED]),
            "paused": len([p for p in scheduled_posts if p.status == ScheduleStatus.PAUSED]),
            "next_post": None,
            "last_post": None
        }
        
        # Find next and last posts
        pending_posts = [p for p in scheduled_posts if p.status == ScheduleStatus.PENDING]
        completed_posts = [p for p in scheduled_posts if p.status == ScheduleStatus.COMPLETED]
        
        if pending_posts:
            next_post = min(pending_posts, key=lambda p: p.scheduled_time)
            stats["next_post"] = {
                "time": next_post.scheduled_time.isoformat(),
                "platforms": next_post.platforms
            }
        
        if completed_posts:
            last_post = max(completed_posts, key=lambda p: p.posted_at or datetime.min)
            stats["last_post"] = {
                "time": last_post.posted_at.isoformat() if last_post.posted_at else None,
                "platforms": list(last_post.post_ids.keys())
            }
        
        return stats