"""Base models and data structures for AetherPost."""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
import json


class ContentType(Enum):
    """Universal content types across all AetherPost features."""
    ANNOUNCEMENT = "announcement"
    EDUCATIONAL = "educational"
    PROMOTIONAL = "promotional"
    ENGAGEMENT = "engagement"
    COMMUNITY = "community"
    BEHIND_SCENES = "behind_scenes"
    MILESTONE = "milestone"
    SEASONAL = "seasonal"
    TECHNICAL = "technical"
    NEWS = "news"


class Platform(Enum):
    """Supported social media platforms."""
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    REDDIT = "reddit"
    GITHUB = "github"
    DISCORD = "discord"
    SLACK = "slack"
    HACKERNEWS = "hackernews"
    BLUESKY = "bluesky"
    MASTODON = "mastodon"


class Priority(Enum):
    """Priority levels for content and tasks."""
    HIGH = 1
    MEDIUM = 2
    LOW = 3


@dataclass
class PlatformConfig:
    """Platform-specific configuration and constraints."""
    platform: Platform
    display_name: str
    character_limit: Optional[int]
    supports_media: bool
    supports_hashtags: bool
    supports_links: bool
    supports_threads: bool
    optimal_posting_times: List[str]
    api_supported: bool
    manual_only_fields: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "platform": self.platform.value,
            "display_name": self.display_name,
            "character_limit": self.character_limit,
            "supports_media": self.supports_media,
            "supports_hashtags": self.supports_hashtags,
            "supports_links": self.supports_links,
            "supports_threads": self.supports_threads,
            "optimal_posting_times": self.optimal_posting_times,
            "api_supported": self.api_supported,
            "manual_only_fields": self.manual_only_fields
        }


@dataclass
class ContentItem:
    """Universal content item structure."""
    id: str
    platform: Platform
    content_type: ContentType
    text: str
    hashtags: List[str] = field(default_factory=list)
    media_urls: List[str] = field(default_factory=list)
    links: List[str] = field(default_factory=list)
    scheduled_time: Optional[datetime] = None
    priority: Priority = Priority.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def character_count(self) -> int:
        """Calculate character count."""
        return len(self.text)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "platform": self.platform.value,
            "content_type": self.content_type.value,
            "text": self.text,
            "hashtags": self.hashtags,
            "media_urls": self.media_urls,
            "links": self.links,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "priority": self.priority.value,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "character_count": self.character_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentItem':
        """Create from dictionary."""
        return cls(
            id=data["id"],
            platform=Platform(data["platform"]),
            content_type=ContentType(data["content_type"]),
            text=data["text"],
            hashtags=data.get("hashtags", []),
            media_urls=data.get("media_urls", []),
            links=data.get("links", []),
            scheduled_time=datetime.fromisoformat(data["scheduled_time"]) if data.get("scheduled_time") else None,
            priority=Priority(data.get("priority", 2)),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now()
        )


@dataclass
class TemplateContext:
    """Universal template context for content generation."""
    app_name: str
    description: str
    website_url: Optional[str] = None
    github_url: Optional[str] = None
    contact_email: Optional[str] = None
    author: str = "AetherPost Team"
    company: Optional[str] = None
    location: Optional[str] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template rendering."""
        base_dict = {
            "app_name": self.app_name,
            "description": self.description,
            "website_url": self.website_url,
            "github_url": self.github_url,
            "contact_email": self.contact_email,
            "author": self.author,
            "company": self.company,
            "location": self.location
        }
        base_dict.update(self.custom_fields)
        return base_dict
    
    def update(self, **kwargs) -> 'TemplateContext':
        """Create updated context with new values."""
        new_context = TemplateContext(**{
            field.name: getattr(self, field.name) 
            for field in self.__dataclass_fields__.values()
        })
        
        for key, value in kwargs.items():
            if hasattr(new_context, key):
                setattr(new_context, key, value)
            else:
                new_context.custom_fields[key] = value
        
        return new_context


@dataclass
class GenerationRequest:
    """Request for content generation."""
    template_context: TemplateContext
    platforms: List[Platform]
    content_type: ContentType
    style: str = "friendly"
    count: int = 1
    additional_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of content validation."""
    is_valid: bool
    score: float  # 0-100
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    @property
    def has_errors(self) -> bool:
        """Check if there are validation errors."""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are warnings."""
        return len(self.warnings) > 0


class BaseGenerator(ABC):
    """Abstract base class for all content generators."""
    
    def __init__(self, platform_configs: Optional[Dict[Platform, PlatformConfig]] = None):
        self.platform_configs = platform_configs or {}
    
    @abstractmethod
    def generate(self, request: GenerationRequest) -> List[ContentItem]:
        """Generate content based on request."""
        pass
    
    @abstractmethod
    def validate(self, content: ContentItem) -> ValidationResult:
        """Validate generated content."""
        pass
    
    def get_platform_config(self, platform: Platform) -> Optional[PlatformConfig]:
        """Get configuration for platform."""
        return self.platform_configs.get(platform)


class BaseManager(ABC):
    """Abstract base class for all managers."""
    
    def __init__(self):
        self.config = self._load_config()
    
    @abstractmethod
    def _load_config(self) -> Dict[str, Any]:
        """Load manager-specific configuration."""
        pass
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration."""
        self.config = config
        self._persist_config(config)
    
    @abstractmethod
    def _persist_config(self, config: Dict[str, Any]) -> None:
        """Persist configuration to storage."""
        pass


@dataclass
class OperationResult:
    """Standard result structure for operations."""
    success: bool
    message: str
    data: Optional[Any] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def success_result(cls, message: str, data: Any = None, **metadata) -> 'OperationResult':
        """Create successful result."""
        return cls(
            success=True,
            message=message,
            data=data,
            metadata=metadata
        )
    
    @classmethod
    def error_result(cls, message: str, errors: List[str] = None, **metadata) -> 'OperationResult':
        """Create error result."""
        return cls(
            success=False,
            message=message,
            errors=errors or [message],
            metadata=metadata
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata": self.metadata
        }


# Platform configurations (centralized)
PLATFORM_CONFIGS = {
    Platform.TWITTER: PlatformConfig(
        platform=Platform.TWITTER,
        display_name="Twitter/X",
        character_limit=280,
        supports_media=True,
        supports_hashtags=True,
        supports_links=True,
        supports_threads=True,
        optimal_posting_times=["09:00", "13:00", "18:00"],
        api_supported=True,
        manual_only_fields=["bio", "profile_image"]
    ),
    
    Platform.INSTAGRAM: PlatformConfig(
        platform=Platform.INSTAGRAM,
        display_name="Instagram",
        character_limit=2200,
        supports_media=True,
        supports_hashtags=True,
        supports_links=False,  # Only link in bio
        supports_threads=False,
        optimal_posting_times=["11:00", "14:00", "17:00", "20:00"],
        api_supported=True,
        manual_only_fields=["bio", "profile_image", "story"]
    ),
    
    Platform.LINKEDIN: PlatformConfig(
        platform=Platform.LINKEDIN,
        display_name="LinkedIn",
        character_limit=3000,
        supports_media=True,
        supports_hashtags=True,
        supports_links=True,
        supports_threads=False,
        optimal_posting_times=["08:00", "12:00", "17:00"],
        api_supported=True,
        manual_only_fields=["bio", "profile_image"]
    ),
    
    Platform.REDDIT: PlatformConfig(
        platform=Platform.REDDIT,
        display_name="Reddit",
        character_limit=40000,
        supports_media=True,
        supports_hashtags=False,
        supports_links=True,
        supports_threads=True,
        optimal_posting_times=["10:00", "14:00", "19:00"],
        api_supported=True,
        manual_only_fields=["bio", "profile_image"]
    ),
    
    Platform.GITHUB: PlatformConfig(
        platform=Platform.GITHUB,
        display_name="GitHub",
        character_limit=160,
        supports_media=True,
        supports_hashtags=False,
        supports_links=True,
        supports_threads=False,
        optimal_posting_times=["09:00", "14:00", "16:00"],
        api_supported=True,
        manual_only_fields=["bio", "profile_image", "readme"]
    ),
    
    Platform.HACKERNEWS: PlatformConfig(
        platform=Platform.HACKERNEWS,
        display_name="Hacker News",
        character_limit=80,  # Title limit
        supports_media=False,
        supports_hashtags=False,
        supports_links=True,
        supports_threads=True,
        optimal_posting_times=["08:00", "14:00"],
        api_supported=False,
        manual_only_fields=["title", "url", "text"]
    ),
    
    Platform.YOUTUBE: PlatformConfig(
        platform=Platform.YOUTUBE,
        display_name="YouTube",
        character_limit=5000,
        supports_media=True,
        supports_hashtags=True,
        supports_links=True,
        supports_threads=False,
        optimal_posting_times=["14:00", "18:00", "20:00"],
        api_supported=True,
        manual_only_fields=["bio", "channel_art"]
    ),
    
    Platform.TIKTOK: PlatformConfig(
        platform=Platform.TIKTOK,
        display_name="TikTok",
        character_limit=300,
        supports_media=True,
        supports_hashtags=True,
        supports_links=True,
        supports_threads=False,
        optimal_posting_times=["06:00", "09:00", "19:00", "21:00"],
        api_supported=False,
        manual_only_fields=["bio", "profile_image", "video"]
    ),
    
    Platform.DISCORD: PlatformConfig(
        platform=Platform.DISCORD,
        display_name="Discord",
        character_limit=2000,
        supports_media=True,
        supports_hashtags=False,
        supports_links=True,
        supports_threads=True,
        optimal_posting_times=["12:00", "18:00", "21:00"],
        api_supported=True,
        manual_only_fields=["bio", "profile_image"]
    )
}