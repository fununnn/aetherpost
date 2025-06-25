"""Instagram platform implementation using Instagram Graph API."""

import asyncio
import os
import logging
import aiohttp
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from ..core.base_platform import BasePlatform, PlatformResult, Content, Profile, ContentType, PlatformCapability, MediaFile
from ..core.authentication.oauth2_authenticator import OAuth2Authenticator
from ..core.error_handling.exceptions import (
    AuthenticationError,
    PostingError,
    RateLimitError,
    ContentValidationError,
    MediaUploadError,
    ProfileUpdateError,
    NetworkError
)

logger = logging.getLogger(__name__)


class InstagramPlatform(BasePlatform):
    """Instagram platform connector using Instagram Graph API."""
    
    def __init__(
        self,
        credentials: Dict[str, str],
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        # Instagram Graph API configuration (set before parent init)
        self.base_url = "https://graph.facebook.com/v18.0"
        
        super().__init__(credentials, config, **kwargs)
        self.app_id = credentials.get("app_id")
        self.app_secret = credentials.get("app_secret")
        self.access_token = credentials.get("access_token")
        self.instagram_account_id = credentials.get("instagram_account_id")
        
        # Session
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Only require access_token if credentials were provided
        if not self.access_token and credentials:
            raise ValueError("Instagram requires access_token")
    
    # Required property implementations
    @property
    def platform_name(self) -> str:
        """Platform identifier."""
        return "instagram"
    
    @property
    def platform_display_name(self) -> str:
        """Human-readable platform name."""
        return "Instagram"
    
    @property
    def supported_content_types(self) -> List[ContentType]:
        """Supported content types for Instagram."""
        return [
            ContentType.IMAGE,
            ContentType.VIDEO,
            ContentType.CAROUSEL,
            ContentType.STORY
        ]
    
    @property
    def supported_media_types(self) -> List[str]:
        """Supported media MIME types."""
        return [
            "image/jpeg",
            "image/png",
            "video/mp4",
            "video/mov"
        ]
    
    @property
    def platform_capabilities(self) -> List[PlatformCapability]:
        """Platform capabilities."""
        return [
            PlatformCapability.POSTING,
            PlatformCapability.MEDIA_UPLOAD,
            PlatformCapability.PROFILE_MANAGEMENT,
            PlatformCapability.ANALYTICS,
            PlatformCapability.STORIES,
            PlatformCapability.HASHTAGS
        ]
    
    @property
    def character_limit(self) -> int:
        """Character limit for Instagram captions."""
        return 2200
    
    @property
    def hashtag_limit(self) -> int:
        """Maximum number of hashtags."""
        return 30
    
    # Required method implementations
    def _setup_authenticator(self):
        """Setup Instagram OAuth2 authenticator."""
        auth_config = {
            "authorization_endpoint": "https://api.instagram.com/oauth/authorize",
            "token_endpoint": "https://api.instagram.com/oauth/access_token",
            "scopes": ["user_profile", "user_media"]
        }
        self.authenticator = OAuth2Authenticator(
            credentials=self.credentials,
            platform=self.platform_name,
            base_url=self.base_url,
            auth_config=auth_config
        )
    
    async def authenticate(self) -> bool:
        """Test authentication with Instagram API."""
        try:
            if not self.instagram_account_id:
                # Get Instagram Business Account ID
                await self._get_instagram_account_id()
            
            # Test API access
            async with self._get_session() as session:
                url = f"{self.base_url}/{self.instagram_account_id}"
                params = {
                    "fields": "id,username,followers_count,media_count",
                    "access_token": self.access_token
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        username = data.get('username', 'Unknown')
                        followers = data.get('followers_count', 0)
                        logger.info(f"Successfully authenticated Instagram account: @{username} ({followers} followers)")
                        self._authenticated = True
                        return True
                    else:
                        error = await response.text()
                        logger.error(f"Instagram authentication failed: {error}")
                        return False
        
        except Exception as e:
            logger.error(f"Instagram authentication error: {e}")
            return False
    
    async def _post_content_impl(self, content: Content) -> PlatformResult:
        """Post content to Instagram."""
        try:
            # Instagram requires media for all posts
            if not content.media:
                return PlatformResult(
                    success=False,
                    platform=self.platform_name,
                    action="post_content",
                    error_message="Instagram requires at least one image or video"
                )
            
            # Handle different content types
            if content.content_type == ContentType.STORY:
                return await self._post_story(content)
            elif content.content_type == ContentType.CAROUSEL and len(content.media) > 1:
                return await self._post_carousel(content)
            else:
                return await self._post_single_media(content)
        
        except Exception as e:
            logger.error(f"Instagram post error: {e}")
            return PlatformResult(
                success=False,
                platform=self.platform_name,
                action="post_content",
                error_message=str(e)
            )
    
    async def _post_single_media(self, content: Content) -> PlatformResult:
        """Post single image or video to Instagram."""
        try:
            media_file = content.media[0]
            
            # Format caption with hashtags
            formatted_caption = self._format_caption_with_hashtags(content.text, content.hashtags)
            
            # Upload media and create container
            if media_file.media_type.startswith('image/'):
                container_id = await self._create_image_container(formatted_caption, media_file)
            else:
                container_id = await self._create_video_container(formatted_caption, media_file)
            
            if not container_id:
                return PlatformResult(
                    success=False,
                    platform=self.platform_name,
                    action="post_content",
                    error_message="Failed to create media container"
                )
            
            # Publish the container
            post_id = await self._publish_container(container_id)
            
            if post_id:
                return PlatformResult(
                    success=True,
                    platform=self.platform_name,
                    action="post_content",
                    post_id=post_id,
                    post_url=f"https://www.instagram.com/p/{post_id}/",
                    created_at=datetime.utcnow()
                )
            else:
                return PlatformResult(
                    success=False,
                    platform=self.platform_name,
                    action="post_content",
                    error_message="Failed to publish post"
                )
        
        except Exception as e:
            logger.error(f"Instagram single media post error: {e}")
            return PlatformResult(
                success=False,
                platform=self.platform_name,
                action="post_content",
                error_message=str(e)
            )
    
    async def _post_carousel(self, content: Content) -> PlatformResult:
        """Post carousel (multiple images/videos) to Instagram."""
        try:
            # Create containers for each media item
            container_ids = []
            for media_file in content.media[:10]:  # Instagram allows max 10 items
                if media_file.media_type.startswith('image/'):
                    container_id = await self._create_carousel_image_container(media_file)
                else:
                    container_id = await self._create_carousel_video_container(media_file)
                
                if container_id:
                    container_ids.append(container_id)
            
            if not container_ids:
                return PlatformResult(
                    success=False,
                    platform=self.platform_name,
                    action="post_carousel",
                    error_message="Failed to create carousel containers"
                )
            
            # Format caption with hashtags and create carousel container
            formatted_caption = self._format_caption_with_hashtags(content.text, content.hashtags)
            carousel_id = await self._create_carousel_container(formatted_caption, container_ids)
            
            if not carousel_id:
                return PlatformResult(
                    success=False,
                    platform=self.platform_name,
                    action="post_carousel",
                    error_message="Failed to create carousel"
                )
            
            # Publish carousel
            post_id = await self._publish_container(carousel_id)
            
            if post_id:
                return PlatformResult(
                    success=True,
                    platform=self.platform_name,
                    action="post_carousel",
                    post_id=post_id,
                    post_url=f"https://www.instagram.com/p/{post_id}/",
                    raw_data={"carousel_items": len(container_ids)},
                    created_at=datetime.utcnow()
                )
            else:
                return PlatformResult(
                    success=False,
                    platform=self.platform_name,
                    action="post_carousel",
                    error_message="Failed to publish carousel"
                )
        
        except Exception as e:
            logger.error(f"Instagram carousel post error: {e}")
            return PlatformResult(
                success=False,
                platform=self.platform_name,
                action="post_carousel",
                error_message=str(e)
            )
    
    async def _post_story(self, content: Content) -> PlatformResult:
        """Post story to Instagram."""
        try:
            media_file = content.media[0]
            
            # Upload media URL for story
            media_url = await self._upload_media_for_url(media_file)
            
            if not media_url:
                return PlatformResult(
                    success=False,
                    platform=self.platform_name,
                    action="post_story",
                    error_message="Failed to upload media for story"
                )
            
            # Create story
            async with self._get_session() as session:
                url = f"{self.base_url}/{self.instagram_account_id}/media"
                data = {
                    "media_type": "STORIES",
                    "image_url" if media_file.media_type.startswith('image/') else "video_url": media_url,
                    "access_token": self.access_token
                }
                
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        container_id = result.get('id')
                        
                        # Publish story
                        story_id = await self._publish_container(container_id)
                        
                        if story_id:
                            return PlatformResult(
                                success=True,
                                platform=self.platform_name,
                                action="post_story",
                                post_id=story_id,
                                raw_data={"story_expires_in": "24_hours"},
                                created_at=datetime.utcnow()
                            )
            
            return PlatformResult(
                success=False,
                platform=self.platform_name,
                action="post_story",
                error_message="Failed to create story"
            )
        
        except Exception as e:
            logger.error(f"Instagram story post error: {e}")
            return PlatformResult(
                success=False,
                platform=self.platform_name,
                action="post_story",
                error_message=str(e)
            )
    
    async def _update_profile_impl(self, profile: Profile) -> PlatformResult:
        """Update Instagram profile (limited by API)."""
        try:
            # Instagram Graph API has limited profile update capabilities
            # Mainly can update profile picture
            
            updates_made = []
            
            if profile.avatar_path and os.path.exists(profile.avatar_path):
                # Note: Profile picture update requires additional permissions
                # and is not available in all API versions
                updates_made.append("profile_picture_queued")
            
            # Bio, name, etc. cannot be updated via API
            # Return informational result
            
            return PlatformResult(
                success=True,
                platform=self.platform_name,
                action="update_profile",
                profile_updated=True,
                raw_data={
                    "updates_made": updates_made,
                    "note": "Instagram API has limited profile update capabilities. Bio and name must be updated manually."
                }
            )
        
        except Exception as e:
            logger.error(f"Instagram profile update error: {e}")
            return PlatformResult(
                success=False,
                platform=self.platform_name,
                action="update_profile",
                error_message=str(e)
            )
    
    async def _delete_post_impl(self, post_id: str) -> PlatformResult:
        """Delete an Instagram post."""
        try:
            async with self._get_session() as session:
                url = f"{self.base_url}/{post_id}"
                params = {"access_token": self.access_token}
                
                async with session.delete(url, params=params) as response:
                    if response.status == 200:
                        return PlatformResult(
                            success=True,
                            platform=self.platform_name,
                            action="delete_post",
                            post_id=post_id
                        )
                    else:
                        error = await response.text()
                        return PlatformResult(
                            success=False,
                            platform=self.platform_name,
                            action="delete_post",
                            post_id=post_id,
                            error_message=f"Delete failed: {error}"
                        )
        
        except Exception as e:
            logger.error(f"Instagram delete error: {e}")
            return PlatformResult(
                success=False,
                platform=self.platform_name,
                action="delete_post",
                post_id=post_id,
                error_message=str(e)
            )
    
    # Helper methods
    async def _get_instagram_account_id(self):
        """Get Instagram Business Account ID from Facebook Page."""
        try:
            # This requires Facebook Page ID
            # In practice, this would be configured during OAuth flow
            pass
        except Exception as e:
            logger.error(f"Failed to get Instagram account ID: {e}")
    
    async def _create_image_container(self, caption: str, media_file: MediaFile) -> Optional[str]:
        """Create image container for publishing."""
        try:
            # Upload image and get URL
            image_url = await self._upload_media_for_url(media_file)
            
            if not image_url:
                return None
            
            # Caption will be formatted later
            formatted_caption = caption
            
            async with self._get_session() as session:
                url = f"{self.base_url}/{self.instagram_account_id}/media"
                data = {
                    "image_url": image_url,
                    "caption": formatted_caption,
                    "access_token": self.access_token
                }
                
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('id')
                    else:
                        error = await response.text()
                        logger.error(f"Failed to create image container: {error}")
                        return None
        
        except Exception as e:
            logger.error(f"Error creating image container: {e}")
            return None
    
    async def _create_video_container(self, caption: str, media_file: MediaFile) -> Optional[str]:
        """Create video container for publishing."""
        try:
            # Upload video and get URL
            video_url = await self._upload_media_for_url(media_file)
            
            if not video_url:
                return None
            
            # Caption will be formatted later
            formatted_caption = caption
            
            async with self._get_session() as session:
                url = f"{self.base_url}/{self.instagram_account_id}/media"
                data = {
                    "video_url": video_url,
                    "caption": formatted_caption,
                    "media_type": "VIDEO",
                    "access_token": self.access_token
                }
                
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('id')
                    else:
                        error = await response.text()
                        logger.error(f"Failed to create video container: {error}")
                        return None
        
        except Exception as e:
            logger.error(f"Error creating video container: {e}")
            return None
    
    async def _create_carousel_image_container(self, media_file: MediaFile) -> Optional[str]:
        """Create image container for carousel."""
        try:
            image_url = await self._upload_media_for_url(media_file)
            if not image_url:
                return None
            
            async with self._get_session() as session:
                url = f"{self.base_url}/{self.instagram_account_id}/media"
                data = {
                    "image_url": image_url,
                    "is_carousel_item": True,
                    "access_token": self.access_token
                }
                
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('id')
                    else:
                        error = await response.text()
                        logger.error(f"Failed to create carousel image container: {error}")
                        return None
        
        except Exception as e:
            logger.error(f"Error creating carousel image container: {e}")
            return None
    
    async def _create_carousel_video_container(self, media_file: MediaFile) -> Optional[str]:
        """Create video container for carousel."""
        try:
            video_url = await self._upload_media_for_url(media_file)
            if not video_url:
                return None
            
            async with self._get_session() as session:
                url = f"{self.base_url}/{self.instagram_account_id}/media"
                data = {
                    "video_url": video_url,
                    "media_type": "VIDEO",
                    "is_carousel_item": True,
                    "access_token": self.access_token
                }
                
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('id')
                    else:
                        error = await response.text()
                        logger.error(f"Failed to create carousel video container: {error}")
                        return None
        
        except Exception as e:
            logger.error(f"Error creating carousel video container: {e}")
            return None
    
    async def _create_carousel_container(self, caption: str, container_ids: List[str]) -> Optional[str]:
        """Create carousel container from multiple media containers."""
        try:
            formatted_caption = caption
            
            async with self._get_session() as session:
                url = f"{self.base_url}/{self.instagram_account_id}/media"
                data = {
                    "media_type": "CAROUSEL",
                    "children": ",".join(container_ids),
                    "caption": formatted_caption,
                    "access_token": self.access_token
                }
                
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('id')
                    else:
                        error = await response.text()
                        logger.error(f"Failed to create carousel container: {error}")
                        return None
        
        except Exception as e:
            logger.error(f"Error creating carousel container: {e}")
            return None
    
    async def _publish_container(self, container_id: str) -> Optional[str]:
        """Publish a media container."""
        try:
            async with self._get_session() as session:
                url = f"{self.base_url}/{self.instagram_account_id}/media_publish"
                data = {
                    "creation_id": container_id,
                    "access_token": self.access_token
                }
                
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('id')
                    else:
                        error = await response.text()
                        logger.error(f"Failed to publish container: {error}")
                        return None
        
        except Exception as e:
            logger.error(f"Error publishing container: {e}")
            return None
    
    async def _upload_media_for_url(self, media_file: MediaFile) -> Optional[str]:
        """Upload media and return publicly accessible URL."""
        # In production, this would upload to a CDN or cloud storage
        # and return a public URL that Instagram can access
        # For now, return None as placeholder
        logger.warning("Media upload to CDN not implemented")
        return None
    
    def _format_caption_with_hashtags(self, caption: str, hashtags: List[str] = None) -> str:
        """Format caption with hashtags."""
        # Instagram best practice: hashtags at the end
        if hashtags:
            limited_hashtags = hashtags[:self.hashtag_limit]
            hashtag_text = ' '.join([f'#{tag.lstrip("#")}' for tag in limited_hashtags])
            return f"{caption}\n\n{hashtag_text}"
        return caption
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self._session
    
    async def cleanup(self):
        """Cleanup platform resources."""
        await super().cleanup()
        
        if self._session and not self._session.closed:
            await self._session.close()
    
    # Platform-specific validation
    async def _validate_content_platform_specific(self, content: Content) -> Dict[str, Any]:
        """Instagram-specific content validation."""
        errors = []
        warnings = []
        
        # Media requirement check
        if not content.media:
            errors.append("Instagram requires at least one image or video")
        
        # Caption length check
        if len(content.text) > self.character_limit:
            errors.append(f"Caption exceeds Instagram's {self.character_limit} character limit")
        
        # Hashtag count check
        hashtag_count = len(content.hashtags) if content.hashtags else 0
        if hashtag_count > self.hashtag_limit:
            errors.append(f"Too many hashtags: {hashtag_count} (max {self.hashtag_limit})")
        
        # Media count check for carousel
        if content.content_type == ContentType.CAROUSEL:
            if len(content.media) < 2:
                errors.append("Carousel requires at least 2 media items")
            elif len(content.media) > 10:
                errors.append("Carousel supports maximum 10 media items")
        
        # Video duration check
        for media in content.media:
            if media.media_type.startswith('video/'):
                if media.duration and media.duration > 60:  # 60 seconds for feed posts
                    warnings.append(f"Video duration {media.duration}s exceeds recommended 60s for feed posts")
                
                if content.content_type == ContentType.STORY and media.duration and media.duration > 15:
                    errors.append(f"Story video duration {media.duration}s exceeds 15s limit")
        
        return {
            'errors': errors,
            'warnings': warnings
        }
    
    async def _get_analytics_impl(self, post_id: Optional[str], timeframe: Optional[str]) -> Dict[str, Any]:
        """Get analytics data for Instagram posts."""
        try:
            if post_id:
                # Get specific post insights
                async with self._get_session() as session:
                    url = f"{self.base_url}/{post_id}/insights"
                    params = {
                        "metric": "engagement,impressions,reach,saved",
                        "access_token": self.access_token
                    }
                    
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            metrics = {}
                            
                            for item in data.get('data', []):
                                metric_name = item.get('name')
                                values = item.get('values', [])
                                if values:
                                    metrics[metric_name] = values[0].get('value', 0)
                            
                            return {
                                'platform': self.platform_name,
                                'post_id': post_id,
                                'metrics': metrics
                            }
            else:
                # Get account insights
                async with self._get_session() as session:
                    url = f"{self.base_url}/{self.instagram_account_id}/insights"
                    params = {
                        "metric": "follower_count,impressions,reach,profile_views",
                        "period": timeframe or "day",
                        "access_token": self.access_token
                    }
                    
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            metrics = {}
                            
                            for item in data.get('data', []):
                                metric_name = item.get('name')
                                values = item.get('values', [])
                                if values:
                                    metrics[metric_name] = values[0].get('value', 0)
                            
                            return {
                                'platform': self.platform_name,
                                'account_metrics': metrics
                            }
            
            return {'error': 'No analytics data available', 'platform': self.platform_name}
        
        except Exception as e:
            logger.error(f"Instagram analytics error: {e}")
            return {'error': str(e), 'platform': self.platform_name}