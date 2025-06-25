"""Unified base platform class for all social media platforms."""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from enum import Enum

from .authentication.base_authenticator import BaseAuthenticator, AuthSession
from .error_handling.exceptions import *
from .error_handling.error_processor import error_processor
from .error_handling.retry_strategy import RetryStrategy, RetryStrategies
from .rate_limiting.rate_limiter import RateLimiter, RateLimitConfig

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Supported content types across platforms."""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    THREAD = "thread"
    STORY = "story"
    LIVE = "live"
    CAROUSEL = "carousel"
    ARTICLE = "article"
    DOCUMENT = "document"
    SHORT = "short"
    COMMUNITY = "community"


class PlatformCapability(Enum):
    """Platform capabilities."""
    POSTING = "posting"
    MEDIA_UPLOAD = "media_upload"
    PROFILE_MANAGEMENT = "profile_management"
    ANALYTICS = "analytics"
    DIRECT_MESSAGING = "direct_messaging"
    LIVE_STREAMING = "live_streaming"
    STORIES = "stories"
    THREADS = "threads"
    SCHEDULING = "scheduling"
    HASHTAGS = "hashtags"
    PLAYLISTS = "playlists"
    ARTICLES = "articles"
    DOCUMENTS = "documents"


@dataclass
class MediaFile:
    """Media file information."""
    file_path: str
    media_type: str
    file_size: Optional[int] = None
    duration: Optional[float] = None
    dimensions: Optional[tuple] = None
    alt_text: Optional[str] = None
    title: Optional[str] = None
    aspect_ratio: Optional[float] = None
    
    def __post_init__(self):
        if not self.file_size:
            try:
                import os
                self.file_size = os.path.getsize(self.file_path)
            except:
                pass
        
        # Calculate aspect ratio from dimensions if available
        if self.dimensions and len(self.dimensions) >= 2 and not self.aspect_ratio:
            width, height = self.dimensions[0], self.dimensions[1]
            if height > 0:
                self.aspect_ratio = width / height


@dataclass
class Content:
    """Unified content structure for all platforms."""
    text: str = ""
    media: List[MediaFile] = field(default_factory=list)
    content_type: ContentType = ContentType.TEXT
    hashtags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    
    # Platform-specific data
    platform_data: Dict[str, Any] = field(default_factory=dict)
    
    # Thread/Story specific
    thread_posts: List[str] = field(default_factory=list)
    story_duration: Optional[int] = None
    
    # Scheduling
    scheduled_time: Optional[datetime] = None
    
    # Metadata
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    location: Optional[str] = None
    
    # Links for videos/articles
    links: List[Dict[str, str]] = field(default_factory=list)
    
    def get_total_length(self) -> int:
        """Get total character count including hashtags and mentions."""
        total = len(self.text)
        for hashtag in self.hashtags:
            total += len(f"#{hashtag} ")
        for mention in self.mentions:
            total += len(f"@{mention} ")
        return total


@dataclass
class Profile:
    """Unified profile structure for all platforms."""
    display_name: Optional[str] = None
    bio: Optional[str] = None
    website_url: Optional[str] = None
    location: Optional[str] = None
    avatar_path: Optional[str] = None
    cover_path: Optional[str] = None
    
    # Platform-specific profile data
    platform_data: Dict[str, Any] = field(default_factory=dict)
    
    # Additional URLs
    additional_urls: List[str] = field(default_factory=list)
    
    # Business info
    business_email: Optional[str] = None
    phone_number: Optional[str] = None
    category: Optional[str] = None
    
    # Tags/keywords for profile optimization
    tags: List[str] = field(default_factory=list)


@dataclass
class PlatformResult:
    """Unified result structure for platform operations."""
    success: bool
    platform: str
    action: str
    
    # Content posting results
    post_id: Optional[str] = None
    post_url: Optional[str] = None
    
    # Profile update results
    profile_updated: bool = False
    
    # Media upload results
    media_ids: List[str] = field(default_factory=list)
    
    # Analytics results
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Raw platform response
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    # Error information
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    retry_after: Optional[int] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'success': self.success,
            'platform': self.platform,
            'action': self.action,
            'post_id': self.post_id,
            'post_url': self.post_url,
            'profile_updated': self.profile_updated,
            'media_ids': self.media_ids,
            'metrics': self.metrics,
            'error_message': self.error_message,
            'error_code': self.error_code,
            'retry_after': self.retry_after,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class BasePlatform(ABC):
    """Unified base class for all social media platform implementations."""
    
    def __init__(
        self,
        credentials: Dict[str, str],
        config: Optional[Dict[str, Any]] = None,
        rate_limit_config: Optional[RateLimitConfig] = None,
        retry_strategy: Optional[RetryStrategy] = None
    ):
        self.credentials = credentials
        self.config = config or {}
        
        # Initialize core systems
        self.authenticator: Optional[BaseAuthenticator] = None
        self.rate_limiter: Optional[RateLimiter] = None
        self.retry_strategy = retry_strategy or RetryStrategies.social_media()
        
        # Platform state
        self._authenticated = False
        self._current_session: Optional[AuthSession] = None
        
        # Statistics tracking
        self.stats = {
            'posts_created': 0,
            'posts_failed': 0,
            'profiles_updated': 0,
            'media_uploaded': 0,
            'errors_encountered': 0,
            'total_operations': 0
        }
        
        # Setup platform-specific components
        self._setup_authenticator()
        self._setup_rate_limiter(rate_limit_config)
    
    # Abstract properties that must be implemented
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Platform identifier (e.g., 'twitter', 'bluesky')."""
        pass
    
    @property
    @abstractmethod
    def platform_display_name(self) -> str:
        """Human-readable platform name (e.g., 'Twitter', 'Bluesky')."""
        pass
    
    @property
    @abstractmethod
    def supported_content_types(self) -> List[ContentType]:
        """List of supported content types."""
        pass
    
    @property
    @abstractmethod
    def supported_media_types(self) -> List[str]:
        """List of supported media MIME types."""
        pass
    
    @property
    @abstractmethod
    def platform_capabilities(self) -> List[PlatformCapability]:
        """List of platform capabilities."""
        pass
    
    @property
    @abstractmethod
    def character_limit(self) -> int:
        """Character limit for text posts."""
        pass
    
    # Abstract methods that must be implemented
    @abstractmethod
    def _setup_authenticator(self):
        """Setup platform-specific authenticator."""
        pass
    
    @abstractmethod
    async def _post_content_impl(self, content: Content) -> PlatformResult:
        """Platform-specific content posting implementation."""
        pass
    
    @abstractmethod
    async def _update_profile_impl(self, profile: Profile) -> PlatformResult:
        """Platform-specific profile update implementation."""
        pass
    
    @abstractmethod
    async def _delete_post_impl(self, post_id: str) -> PlatformResult:
        """Platform-specific post deletion implementation."""
        pass
    
    # Core public interface
    async def authenticate(self) -> bool:
        """Authenticate with the platform."""
        try:
            if not self.authenticator:
                raise ConfigurationError(
                    "No authenticator configured",
                    platform=self.platform_name
                )
            
            auth_result = await self.authenticator.authenticate()
            
            if auth_result.success:
                self._authenticated = True
                self._current_session = auth_result.session
                logger.info(f"Successfully authenticated with {self.platform_display_name}")
                return True
            else:
                self._authenticated = False
                error_msg = auth_result.error_message or "Authentication failed"
                logger.error(f"Authentication failed for {self.platform_display_name}: {error_msg}")
                return False
                
        except Exception as e:
            self._authenticated = False
            await self._handle_error(e, "authenticate")
            return False
    
    async def post_content(self, content: Content) -> PlatformResult:
        """Post content to the platform with unified error handling and retry logic."""
        
        operation = f"post_{content.content_type.value}"
        self.stats['total_operations'] += 1
        
        try:
            # Ensure authentication
            if not await self._ensure_authenticated():
                raise AuthenticationError(
                    "Authentication required for posting",
                    platform=self.platform_name
                )
            
            # Validate content
            validation_result = await self.validate_content(content)
            if not validation_result['is_valid']:
                raise ContentValidationError(
                    "Content validation failed",
                    platform=self.platform_name,
                    validation_errors=validation_result['errors'],
                    content_type=content.content_type.value
                )
            
            # Apply rate limiting
            if self.rate_limiter:
                await self.rate_limiter.acquire("post_content", operation)
            
            # Execute with retry logic
            result = await self.retry_strategy.execute_with_retry(
                operation,
                self._post_content_impl,
                content
            )
            
            if result.success:
                self.stats['posts_created'] += 1
                logger.info(f"Successfully posted to {self.platform_display_name}: {result.post_id}")
            else:
                self.stats['posts_failed'] += 1
                logger.error(f"Failed to post to {self.platform_display_name}: {result.error_message}")
            
            return result
            
        except Exception as e:
            self.stats['posts_failed'] += 1
            self.stats['errors_encountered'] += 1
            return await self._handle_error(e, operation, content_type=content.content_type.value)
    
    async def update_profile(self, profile: Profile) -> PlatformResult:
        """Update platform profile with unified error handling."""
        
        operation = "update_profile"
        self.stats['total_operations'] += 1
        
        try:
            # Ensure authentication
            if not await self._ensure_authenticated():
                raise AuthenticationError(
                    "Authentication required for profile update",
                    platform=self.platform_name
                )
            
            # Apply rate limiting
            if self.rate_limiter:
                await self.rate_limiter.acquire("profile", operation)
            
            # Execute with retry logic
            result = await self.retry_strategy.execute_with_retry(
                operation,
                self._update_profile_impl,
                profile
            )
            
            if result.success:
                self.stats['profiles_updated'] += 1
                logger.info(f"Successfully updated profile on {self.platform_display_name}")
            else:
                logger.error(f"Failed to update profile on {self.platform_display_name}: {result.error_message}")
            
            return result
            
        except Exception as e:
            self.stats['errors_encountered'] += 1
            return await self._handle_error(e, operation)
    
    async def delete_post(self, post_id: str) -> PlatformResult:
        """Delete a post from the platform."""
        
        operation = "delete_post"
        self.stats['total_operations'] += 1
        
        try:
            # Ensure authentication
            if not await self._ensure_authenticated():
                raise AuthenticationError(
                    "Authentication required for post deletion",
                    platform=self.platform_name
                )
            
            # Apply rate limiting
            if self.rate_limiter:
                await self.rate_limiter.acquire("delete_post", operation)
            
            # Execute with retry logic
            result = await self.retry_strategy.execute_with_retry(
                operation,
                self._delete_post_impl,
                post_id
            )
            
            if result.success:
                logger.info(f"Successfully deleted post {post_id} from {self.platform_display_name}")
            else:
                logger.error(f"Failed to delete post {post_id} from {self.platform_display_name}: {result.error_message}")
            
            return result
            
        except Exception as e:
            self.stats['errors_encountered'] += 1
            return await self._handle_error(e, operation, post_id=post_id)
    
    async def validate_content(self, content: Content) -> Dict[str, Any]:
        """Validate content for this platform."""
        
        errors = []
        warnings = []
        
        # Check content type support
        if content.content_type not in self.supported_content_types:
            errors.append(f"Content type {content.content_type.value} not supported")
        
        # Check character limit
        if content.get_total_length() > self.character_limit:
            errors.append(f"Content exceeds character limit: {content.get_total_length()} > {self.character_limit}")
        
        # Check media support
        for media in content.media:
            if media.media_type not in self.supported_media_types:
                errors.append(f"Media type {media.media_type} not supported")
        
        # Platform-specific validation
        platform_validation = await self._validate_content_platform_specific(content)
        errors.extend(platform_validation.get('errors', []))
        warnings.extend(platform_validation.get('warnings', []))
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'platform': self.platform_name
        }
    
    async def _validate_content_platform_specific(self, content: Content) -> Dict[str, Any]:
        """Platform-specific content validation (override in subclasses)."""
        return {'errors': [], 'warnings': []}
    
    async def get_analytics(self, post_id: Optional[str] = None, timeframe: Optional[str] = None) -> Dict[str, Any]:
        """Get analytics data (if supported by platform)."""
        
        if PlatformCapability.ANALYTICS not in self.platform_capabilities:
            return {
                'error': 'Analytics not supported by this platform',
                'platform': self.platform_name
            }
        
        try:
            return await self._get_analytics_impl(post_id, timeframe)
        except Exception as e:
            await self._handle_error(e, "get_analytics")
            return {
                'error': str(e),
                'platform': self.platform_name
            }
    
    async def _get_analytics_impl(self, post_id: Optional[str], timeframe: Optional[str]) -> Dict[str, Any]:
        """Platform-specific analytics implementation (override in subclasses)."""
        return {'message': 'Analytics not implemented for this platform'}
    
    # Helper methods
    async def _ensure_authenticated(self) -> bool:
        """Ensure the platform is authenticated."""
        
        if not self._authenticated or not self._current_session:
            return await self.authenticate()
        
        # Check if session is still valid
        if self.authenticator:
            is_valid = await self.authenticator.is_session_valid(self._current_session)
            if not is_valid:
                return await self.authenticate()
        
        return True
    
    def _setup_rate_limiter(self, rate_limit_config: Optional[RateLimitConfig]):
        """Setup rate limiter for this platform."""
        
        if rate_limit_config:
            self.rate_limiter = RateLimiter(rate_limit_config)
        else:
            # Try to get default rate limits for this platform
            from .rate_limiting.rate_limiter import PlatformRateLimits
            
            if hasattr(PlatformRateLimits, self.platform_name):
                default_config = getattr(PlatformRateLimits, self.platform_name)()
                self.rate_limiter = RateLimiter(default_config)
    
    async def _handle_error(
        self, 
        error: Exception, 
        operation: str, 
        **context
    ) -> PlatformResult:
        """Centralized error handling."""
        
        # Process error through unified error processor
        error_response = await error_processor.process_error(
            error, 
            self.platform_name, 
            operation, 
            context
        )
        
        # Create error result
        result = PlatformResult(
            success=False,
            platform=self.platform_name,
            action=operation,
            error_message=str(error),
            error_code=error_response.get('reason', 'unknown_error')
        )
        
        # Handle rate limiting
        if isinstance(error, RateLimitError) and self.rate_limiter:
            result.retry_after = error.retry_after
            await self.rate_limiter.handle_rate_limit_response(
                operation, 
                {}, 
                429
            )
        
        return result
    
    def get_platform_info(self) -> Dict[str, Any]:
        """Get comprehensive platform information."""
        
        return {
            'name': self.platform_name,
            'display_name': self.platform_display_name,
            'supported_content_types': [ct.value for ct in self.supported_content_types],
            'supported_media_types': self.supported_media_types,
            'capabilities': [cap.value for cap in self.platform_capabilities],
            'character_limit': self.character_limit,
            'authenticated': self._authenticated,
            'statistics': dict(self.stats),
            'rate_limiter_stats': self.rate_limiter.get_statistics() if self.rate_limiter else None,
            'retry_strategy_stats': self.retry_strategy.get_statistics() if self.retry_strategy else None
        }
    
    def get_session_info(self) -> Optional[Dict[str, Any]]:
        """Get current authentication session information."""
        
        if self.authenticator:
            return self.authenticator.get_session_info()
        return None
    
    async def cleanup(self):
        """Cleanup platform resources."""
        
        try:
            if self.authenticator and self._current_session:
                await self.authenticator.revoke_session()
            
            self._authenticated = False
            self._current_session = None
            
            logger.info(f"Cleaned up {self.platform_display_name} platform")
            
        except Exception as e:
            logger.warning(f"Error during {self.platform_display_name} cleanup: {e}")