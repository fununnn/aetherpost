"""Scheduling data models."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class FrequencyType(str, Enum):
    """Posting frequency types."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class ScheduleStatus(str, Enum):
    """Schedule status."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ScheduleConfig:
    """Schedule configuration."""
    
    frequency: FrequencyType
    start_time: datetime
    end_time: Optional[datetime] = None
    timezone: str = "UTC"
    max_posts_per_day: int = 10
    posting_hours: List[int] = None  # Hours of day to post (0-23)
    days_of_week: List[int] = None   # Days of week (0=Monday, 6=Sunday)
    custom_interval_minutes: Optional[int] = None
    enabled: bool = True
    
    def __post_init__(self):
        """Set defaults after initialization."""
        if self.posting_hours is None:
            self.posting_hours = [9, 12, 15, 18]  # 9AM, 12PM, 3PM, 6PM
        if self.days_of_week is None:
            self.days_of_week = [0, 1, 2, 3, 4]  # Monday to Friday


@dataclass  
class ScheduledPost:
    """Scheduled post data."""
    
    id: str
    campaign_file: str
    scheduled_time: datetime
    platforms: List[str]
    content: Optional[Dict[str, Any]] = None
    status: ScheduleStatus = ScheduleStatus.PENDING
    created_at: datetime = None
    attempts: int = 0
    max_attempts: int = 3
    last_error: Optional[str] = None
    posted_at: Optional[datetime] = None
    post_ids: Dict[str, str] = None  # platform -> post_id mapping
    
    def __post_init__(self):
        """Set defaults after initialization."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.post_ids is None:
            self.post_ids = {}
    
    def can_retry(self) -> bool:
        """Check if post can be retried."""
        return (
            self.status == ScheduleStatus.FAILED and 
            self.attempts < self.max_attempts
        )
    
    def mark_attempt(self, error: Optional[str] = None):
        """Mark an attempt."""
        self.attempts += 1
        if error:
            self.last_error = error
            self.status = ScheduleStatus.FAILED
    
    def mark_completed(self, post_ids: Dict[str, str]):
        """Mark as completed."""
        self.status = ScheduleStatus.COMPLETED
        self.posted_at = datetime.utcnow()
        self.post_ids.update(post_ids)