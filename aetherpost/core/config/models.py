"""Configuration data models using Pydantic."""

from datetime import datetime
import re
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator


class PlatformConfig(BaseModel):
    """Configuration for a social media platform."""
    name: str
    enabled: bool = True
    credentials: Dict[str, str] = Field(default_factory=dict)


class ContentConfig(BaseModel):
    """Content generation configuration."""
    style: str = "casual"
    action: str = "Learn more"
    max_length: int = 280
    hashtags: List[str] = Field(default_factory=list)
    ai_prompt: Optional[str] = None
    language: str = "en"  # ISO 639-1 language code (en, ja, es, fr, de, etc.)
    
    @validator('language')
    def validate_language(cls, v):
        """Validate language code."""
        # Common language codes
        valid_languages = {
            'en', 'ja', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ko', 'zh', 
            'ar', 'hi', 'th', 'vi', 'tr', 'nl', 'sv', 'da', 'no', 'fi'
        }
        if v not in valid_languages:
            raise ValueError(f"Unsupported language code: {v}. Supported: {', '.join(sorted(valid_languages))}")
        return v


class ScheduleConfig(BaseModel):
    """Posting schedule configuration."""
    type: str = "immediate"  # immediate, delayed, recurring
    datetime: Optional[datetime] = None
    timezone: str = "UTC"
    frequency: Optional[str] = None  # daily, weekly, monthly
    exclude_weekends: bool = False


class ExperimentConfig(BaseModel):
    """A/B testing configuration."""
    enabled: bool = False
    variants: List[Dict[str, str]] = Field(default_factory=list)
    metric: str = "engagement_rate"
    duration: str = "7_days"


class StoryConfig(BaseModel):
    """Story mode configuration."""
    title: str
    episodes: List[Dict[str, str]] = Field(default_factory=list)


class CampaignConfig(BaseModel):
    """Main campaign configuration."""
    name: str
    concept: str
    url: Optional[str] = None
    platforms: List[str]
    content: ContentConfig = Field(default_factory=ContentConfig)
    schedule: Union[str, ScheduleConfig] = Field(default_factory=ScheduleConfig)
    image: Optional[str] = None
    experiments: Optional[ExperimentConfig] = None
    story: Optional[StoryConfig] = None
    analytics: bool = True

    @validator('platforms')
    def validate_platforms(cls, v):
        """Validate platform names."""
        valid_platforms = {'twitter', 'bluesky', 'mastodon', 'reddit', 'youtube', 'linkedin', 'discord', 'dev_to'}
        for platform in v:
            if platform not in valid_platforms:
                raise ValueError(f"Unknown platform: {platform}")
        return v

    @validator('name')
    def validate_name(cls, v):
        """Validate campaign name."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Campaign name cannot be empty")
        return v.strip()
    
    @validator('schedule', pre=True)
    def parse_schedule(cls, v):
        """Parse schedule string into ScheduleConfig object."""
        if isinstance(v, str):
            # Parse natural language schedule formats
            schedule_config = ScheduleConfig()
            
            if v.lower() == "now" or v.lower() == "immediate":
                schedule_config.type = "immediate"
            elif re.match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}', v):
                # ISO format: "2025-06-14 10:00"
                schedule_config.type = "delayed"
                schedule_config.datetime = datetime.strptime(v, "%Y-%m-%d %H:%M")
            elif "tomorrow" in v.lower():
                schedule_config.type = "delayed"
                # Simple parsing for "tomorrow 10am" format
                # In real implementation, would use more sophisticated parsing
            elif "every" in v.lower():
                schedule_config.type = "recurring"
                if "monday" in v.lower():
                    schedule_config.frequency = "weekly"
                elif "day" in v.lower():
                    schedule_config.frequency = "daily"
            else:
                # Default to immediate for unrecognized formats
                schedule_config.type = "immediate"
            
            return schedule_config
        elif isinstance(v, dict):
            return ScheduleConfig(**v)
        else:
            return v


class CredentialsConfig(BaseModel):
    """Credentials configuration."""
    twitter: Optional[Dict[str, str]] = None
    ai_service: Optional[Dict[str, str]] = None
    openai: Optional[Dict[str, str]] = None
    bluesky: Optional[Dict[str, str]] = None
    mastodon: Optional[Dict[str, str]] = None