"""YouTube-specific configuration models."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class YouTubeConfig(BaseModel):
    """YouTube platform configuration."""
    
    # OAuth2 credentials
    client_id: str = Field(..., description="Google OAuth2 client ID")
    client_secret: str = Field(..., description="Google OAuth2 client secret")
    credentials_file: str = Field(
        default="youtube_credentials.json",
        description="Path to OAuth2 credentials JSON file"
    )
    token_file: str = Field(
        default="youtube_token.json",
        description="Path to store OAuth2 tokens"
    )
    
    # Channel settings
    default_privacy: str = Field(
        default="public",
        description="Default video privacy setting"
    )
    default_category: str = Field(
        default="28",  # Science & Technology
        description="Default video category ID"
    )
    default_language: str = Field(
        default="en",
        description="Default video language"
    )
    
    # Content settings
    auto_generate_tags: bool = Field(
        default=True,
        description="Automatically generate relevant tags"
    )
    default_tags: List[str] = Field(
        default=["AetherPost", "automation", "social media"],
        description="Default tags to add to all videos"
    )
    
    # Upload settings
    chunk_size: int = Field(
        default=1024*1024,  # 1MB
        description="Upload chunk size in bytes"
    )
    max_retries: int = Field(default=3, description="Maximum upload retries")
    
    @validator('default_privacy')
    def validate_privacy(cls, v):
        """Validate privacy setting."""
        valid_privacy = {'public', 'private', 'unlisted'}
        if v not in valid_privacy:
            raise ValueError(f"Privacy must be one of: {valid_privacy}")
        return v
    
    class Config:
        """Pydantic config."""
        json_encoders = {
            # Custom encoders if needed
        }


class YouTubeVideoConfig(BaseModel):
    """Configuration for a YouTube video upload."""
    
    title: str = Field(..., max_length=100, description="Video title")
    description: str = Field(..., max_length=5000, description="Video description")
    tags: List[str] = Field(default_factory=list, description="Video tags")
    
    # Video settings
    category_id: str = Field(default="28", description="YouTube category ID")
    privacy_status: str = Field(default="public", description="Privacy setting")
    language: str = Field(default="en", description="Video language")
    
    # Advanced settings
    made_for_kids: bool = Field(default=False, description="Content made for kids")
    embeddable: bool = Field(default=True, description="Allow embedding")
    public_stats_viewable: bool = Field(default=True, description="Show view counts")
    
    # Thumbnail and metadata
    thumbnail_file: Optional[str] = Field(None, description="Custom thumbnail file path")
    
    # Shorts specific
    is_short: bool = Field(default=False, description="Mark as YouTube Short")
    
    @validator('title')
    def validate_title(cls, v):
        """Validate video title."""
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags list."""
        if len(v) > 500:  # YouTube limit
            raise ValueError("Too many tags (max 500)")
        return v
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "title": "New Developer Tool Demo",
                "description": "Demonstrating a new tool for developers...",
                "tags": ["development", "tools", "programming", "demo"],
                "category_id": "28",
                "privacy_status": "public",
                "language": "en",
                "made_for_kids": False,
                "embeddable": True,
                "public_stats_viewable": True,
                "is_short": False
            }
        }


class YouTubeAnalyticsConfig(BaseModel):
    """Configuration for YouTube analytics."""
    
    # Metrics to track
    track_views: bool = Field(default=True, description="Track view counts")
    track_engagement: bool = Field(default=True, description="Track likes/comments")
    track_watch_time: bool = Field(default=True, description="Track watch time")
    track_subscribers: bool = Field(default=True, description="Track subscriber changes")
    
    # Reporting
    report_frequency: str = Field(
        default="daily",
        description="How often to generate reports"
    )
    metrics_retention_days: int = Field(
        default=90,
        description="How long to keep detailed metrics"
    )
    
    @validator('report_frequency')
    def validate_frequency(cls, v):
        """Validate report frequency."""
        valid_frequencies = {'hourly', 'daily', 'weekly', 'monthly'}
        if v not in valid_frequencies:
            raise ValueError(f"Frequency must be one of: {valid_frequencies}")
        return v
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "track_views": True,
                "track_engagement": True,
                "track_watch_time": True,
                "track_subscribers": True,
                "report_frequency": "daily",
                "metrics_retention_days": 90
            }
        }


class YouTubeContentStrategy(BaseModel):
    """Content strategy configuration for YouTube."""
    
    # Content types
    preferred_video_length: int = Field(
        default=60,  # seconds
        description="Preferred video length in seconds"
    )
    content_themes: List[str] = Field(
        default=["technology", "tutorials", "announcements"],
        description="Main content themes"
    )
    
    # Optimization
    optimize_for_shorts: bool = Field(
        default=True,
        description="Optimize content for YouTube Shorts"
    )
    include_captions: bool = Field(
        default=True,
        description="Include auto-generated captions"
    )
    
    # Scheduling
    optimal_posting_times: List[str] = Field(
        default=["14:00", "18:00", "20:00"],
        description="Optimal posting times (UTC)"
    )
    avoid_weekends: bool = Field(
        default=False,
        description="Avoid posting on weekends"
    )
    
    class Config:
        """Pydantic config."""
        schema_extra = {
            "example": {
                "preferred_video_length": 60,
                "content_themes": ["technology", "tutorials", "product demos"],
                "optimize_for_shorts": True,
                "include_captions": True,
                "optimal_posting_times": ["14:00", "18:00", "20:00"],
                "avoid_weekends": False
            }
        }