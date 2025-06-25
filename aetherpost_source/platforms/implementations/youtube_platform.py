"""YouTube platform implementation using YouTube Data API v3."""

import asyncio
import os
import logging
import aiohttp
import json
import mimetypes
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


class YouTubePlatform(BasePlatform):
    """YouTube platform connector using YouTube Data API v3."""
    
    def __init__(
        self,
        credentials: Dict[str, str],
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        # YouTube API configuration (set before parent init)
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.upload_url = "https://www.googleapis.com/upload/youtube/v3"
        
        super().__init__(credentials, config, **kwargs)
        self.api_key = credentials.get("api_key")
        self.client_id = credentials.get("client_id")
        self.client_secret = credentials.get("client_secret")
        self.access_token = credentials.get("access_token")
        self.refresh_token = credentials.get("refresh_token")
        self.channel_id = None  # Will be fetched during authentication
        
        # Session
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Only require access_token if credentials were provided  
        if not self.access_token and credentials:
            raise ValueError("YouTube requires access_token")
    
    # Required property implementations
    @property
    def platform_name(self) -> str:
        """Platform identifier."""
        return "youtube"
    
    @property
    def platform_display_name(self) -> str:
        """Human-readable platform name."""
        return "YouTube"
    
    @property
    def supported_content_types(self) -> List[ContentType]:
        """Supported content types for YouTube."""
        return [
            ContentType.VIDEO,
            ContentType.SHORT,  # YouTube Shorts
            ContentType.LIVE,   # Live streams
            ContentType.COMMUNITY  # Community posts
        ]
    
    @property
    def supported_media_types(self) -> List[str]:
        """Supported media MIME types."""
        return [
            "video/mp4",
            "video/x-flv",
            "video/3gpp",
            "video/quicktime",
            "video/x-msvideo",
            "video/x-ms-wmv",
            "video/webm",
            "image/jpeg",  # For thumbnails and community posts
            "image/png"
        ]
    
    @property
    def platform_capabilities(self) -> List[PlatformCapability]:
        """Platform capabilities."""
        return [
            PlatformCapability.POSTING,
            PlatformCapability.MEDIA_UPLOAD,
            PlatformCapability.PROFILE_MANAGEMENT,
            PlatformCapability.ANALYTICS,
            PlatformCapability.LIVE_STREAMING,
            PlatformCapability.PLAYLISTS
        ]
    
    @property
    def character_limit(self) -> int:
        """Character limit for YouTube video descriptions."""
        return 5000
    
    @property
    def title_limit(self) -> int:
        """Character limit for YouTube video titles."""
        return 100
    
    @property
    def tags_limit(self) -> int:
        """Character limit for all tags combined."""
        return 500
    
    # Required method implementations
    def _setup_authenticator(self):
        """Setup YouTube OAuth2 authenticator."""
        auth_config = {
            "authorization_endpoint": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_endpoint": "https://oauth2.googleapis.com/token",
            "scopes": [
                "https://www.googleapis.com/auth/youtube.upload",
                "https://www.googleapis.com/auth/youtube",
                "https://www.googleapis.com/auth/youtube.channel-memberships.creator"
            ]
        }
        self.authenticator = OAuth2Authenticator(
            credentials=self.credentials,
            platform=self.platform_name,
            base_url=self.base_url,
            auth_config=auth_config
        )
    
    async def authenticate(self) -> bool:
        """Test authentication with YouTube API."""
        try:
            # Get channel info to verify authentication
            async with self._get_session() as session:
                headers = self._get_authenticated_headers()
                params = {
                    "part": "snippet,statistics",
                    "mine": "true"
                }
                
                async with session.get(
                    f"{self.base_url}/channels",
                    headers=headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        items = data.get('items', [])
                        
                        if items:
                            channel = items[0]
                            self.channel_id = channel.get('id')
                            snippet = channel.get('snippet', {})
                            stats = channel.get('statistics', {})
                            
                            channel_name = snippet.get('title', 'Unknown')
                            subscriber_count = stats.get('subscriberCount', '0')
                            
                            logger.info(f"Successfully authenticated YouTube channel: {channel_name} ({subscriber_count} subscribers)")
                            self._authenticated = True
                            return True
                        else:
                            logger.error("No YouTube channel found for authenticated user")
                            return False
                    else:
                        error = await response.text()
                        logger.error(f"YouTube authentication failed: {error}")
                        return False
        
        except Exception as e:
            logger.error(f"YouTube authentication error: {e}")
            return False
    
    async def _post_content_impl(self, content: Content) -> PlatformResult:
        """Post content to YouTube."""
        try:
            # Handle different content types
            if content.content_type == ContentType.COMMUNITY:
                return await self._post_community(content)
            elif content.content_type == ContentType.SHORT:
                return await self._post_short(content)
            elif content.content_type == ContentType.LIVE:
                return await self._create_live_stream(content)
            else:
                return await self._upload_video(content)
        
        except Exception as e:
            logger.error(f"YouTube post error: {e}")
            return PlatformResult(
                success=False,
                platform=self.platform_name,
                action="post_content",
                error_message=str(e)
            )
    
    async def _upload_video(self, content: Content) -> PlatformResult:
        """Upload a video to YouTube."""
        try:
            if not content.media or not content.media[0].media_type.startswith('video/'):
                return PlatformResult(
                    success=False,
                    platform=self.platform_name,
                    action="upload_video",
                    error_message="YouTube requires a video file"
                )
            
            video_file = content.media[0]
            
            # Prepare video metadata
            video_data = {
                "snippet": {
                    "title": content.title or "Untitled Video",
                    "description": self._format_description(content),
                    "tags": self._extract_tags(content),
                    "categoryId": "22"  # People & Blogs default category
                },
                "status": {
                    "privacyStatus": content.platform_data.get('privacy', 'public'),
                    "selfDeclaredMadeForKids": False
                }
            }
            
            # Handle scheduled publishing
            if content.scheduled_time:
                video_data["status"]["publishAt"] = content.scheduled_time.isoformat()
                video_data["status"]["privacyStatus"] = "private"
            
            # Upload the video
            video_id = await self._upload_video_file(video_file, video_data)
            
            if not video_id:
                return PlatformResult(
                    success=False,
                    platform=self.platform_name,
                    action="upload_video",
                    error_message="Failed to upload video"
                )
            
            # Upload thumbnail if provided
            if len(content.media) > 1:
                for media in content.media[1:]:
                    if media.media_type.startswith('image/'):
                        await self._upload_thumbnail(video_id, media)
                        break
            
            return PlatformResult(
                success=True,
                platform=self.platform_name,
                action="upload_video",
                post_id=video_id,
                post_url=f"https://www.youtube.com/watch?v={video_id}",
                created_at=datetime.utcnow()
            )
        
        except Exception as e:
            logger.error(f"YouTube video upload error: {e}")
            return PlatformResult(
                success=False,
                platform=self.platform_name,
                action="upload_video",
                error_message=str(e)
            )
    
    async def _post_short(self, content: Content) -> PlatformResult:
        """Post a YouTube Short."""
        try:
            if not content.media or not content.media[0].media_type.startswith('video/'):
                return PlatformResult(
                    success=False,
                    platform=self.platform_name,
                    action="post_short",
                    error_message="YouTube Shorts requires a vertical video file"
                )
            
            video_file = content.media[0]
            
            # Validate video duration for Shorts (max 60 seconds)
            if video_file.duration and video_file.duration > 60:
                return PlatformResult(
                    success=False,
                    platform=self.platform_name,
                    action="post_short",
                    error_message="YouTube Shorts must be 60 seconds or less"
                )
            
            # Prepare Short metadata
            video_data = {
                "snippet": {
                    "title": content.title or "Untitled Short",
                    "description": self._format_description(content) + "\n\n#Shorts",
                    "tags": self._extract_tags(content) + ["shorts"],
                    "categoryId": "22"
                },
                "status": {
                    "privacyStatus": content.platform_data.get('privacy', 'public'),
                    "selfDeclaredMadeForKids": False
                }
            }
            
            # Upload the Short
            video_id = await self._upload_video_file(video_file, video_data)
            
            if video_id:
                return PlatformResult(
                    success=True,
                    platform=self.platform_name,
                    action="post_short",
                    post_id=video_id,
                    post_url=f"https://www.youtube.com/shorts/{video_id}",
                    created_at=datetime.utcnow()
                )
            else:
                return PlatformResult(
                    success=False,
                    platform=self.platform_name,
                    action="post_short",
                    error_message="Failed to upload Short"
                )
        
        except Exception as e:
            logger.error(f"YouTube Short upload error: {e}")
            return PlatformResult(
                success=False,
                platform=self.platform_name,
                action="post_short",
                error_message=str(e)
            )
    
    async def _post_community(self, content: Content) -> PlatformResult:
        """Post to YouTube Community tab."""
        try:
            # Community posts require channel membership features
            # This is a simplified implementation
            
            post_data = {
                "snippet": {
                    "textOriginal": content.text
                }
            }
            
            # Add image if provided
            if content.media and content.media[0].media_type.startswith('image/'):
                # Community posts with images require special handling
                # This would need implementation of image upload for community posts
                pass
            
            # Note: Full community post API is limited
            logger.warning("YouTube Community posts have limited API support")
            
            return PlatformResult(
                success=False,
                platform=self.platform_name,
                action="post_community",
                error_message="Community posts require additional API access"
            )
        
        except Exception as e:
            logger.error(f"YouTube community post error: {e}")
            return PlatformResult(
                success=False,
                platform=self.platform_name,
                action="post_community",
                error_message=str(e)
            )
    
    async def _create_live_stream(self, content: Content) -> PlatformResult:
        """Create a YouTube live stream."""
        try:
            # Create live broadcast
            broadcast_data = {
                "snippet": {
                    "title": content.title or "Live Stream",
                    "description": self._format_description(content),
                    "scheduledStartTime": content.scheduled_time.isoformat() if content.scheduled_time else datetime.utcnow().isoformat()
                },
                "status": {
                    "privacyStatus": content.platform_data.get('privacy', 'public'),
                    "selfDeclaredMadeForKids": False
                },
                "contentDetails": {
                    "enableAutoStart": True,
                    "enableAutoStop": True
                }
            }
            
            # This would need full implementation of live streaming API
            logger.warning("YouTube live streaming requires additional setup")
            
            return PlatformResult(
                success=False,
                platform=self.platform_name,
                action="create_live_stream",
                error_message="Live streaming requires additional configuration"
            )
        
        except Exception as e:
            logger.error(f"YouTube live stream error: {e}")
            return PlatformResult(
                success=False,
                platform=self.platform_name,
                action="create_live_stream",
                error_message=str(e)
            )
    
    async def _update_profile_impl(self, profile: Profile) -> PlatformResult:
        """Update YouTube channel profile."""
        try:
            updates_made = []
            
            # Update channel branding
            if profile.avatar_path and os.path.exists(profile.avatar_path):
                # Channel icon update requires branding API
                updates_made.append("channel_icon_queued")
            
            if profile.cover_path and os.path.exists(profile.cover_path):
                # Channel banner update
                updates_made.append("channel_banner_queued")
            
            # Update channel description
            if profile.bio:
                channel_update = {
                    "id": self.channel_id,
                    "brandingSettings": {
                        "channel": {
                            "description": profile.bio,
                            "keywords": " ".join(profile.tags) if hasattr(profile, 'tags') else ""
                        }
                    }
                }
                
                async with self._get_session() as session:
                    headers = self._get_authenticated_headers()
                    params = {"part": "brandingSettings"}
                    
                    async with session.put(
                        f"{self.base_url}/channels",
                        headers=headers,
                        params=params,
                        json=channel_update
                    ) as response:
                        if response.status == 200:
                            updates_made.append("channel_description")
            
            return PlatformResult(
                success=True,
                platform=self.platform_name,
                action="update_profile",
                profile_updated=len(updates_made) > 0,
                raw_data={
                    "updates_made": updates_made,
                    "channel_id": self.channel_id
                }
            )
        
        except Exception as e:
            logger.error(f"YouTube profile update error: {e}")
            return PlatformResult(
                success=False,
                platform=self.platform_name,
                action="update_profile",
                error_message=str(e)
            )
    
    async def _delete_post_impl(self, post_id: str) -> PlatformResult:
        """Delete a YouTube video."""
        try:
            async with self._get_session() as session:
                headers = self._get_authenticated_headers()
                params = {"id": post_id}
                
                async with session.delete(
                    f"{self.base_url}/videos",
                    headers=headers,
                    params=params
                ) as response:
                    if response.status == 204:
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
            logger.error(f"YouTube delete error: {e}")
            return PlatformResult(
                success=False,
                platform=self.platform_name,
                action="delete_post",
                post_id=post_id,
                error_message=str(e)
            )
    
    # Helper methods
    async def _upload_video_file(self, video_file: MediaFile, metadata: Dict[str, Any]) -> Optional[str]:
        """Upload video file to YouTube."""
        try:
            # Step 1: Create video resource
            async with self._get_session() as session:
                headers = self._get_authenticated_headers()
                params = {
                    "part": "snippet,status",
                    "uploadType": "resumable"
                }
                
                # Initiate resumable upload
                async with session.post(
                    f"{self.upload_url}/videos",
                    headers=headers,
                    params=params,
                    json=metadata
                ) as response:
                    if response.status != 200:
                        error = await response.text()
                        logger.error(f"Failed to initiate upload: {error}")
                        return None
                    
                    upload_url = response.headers.get('Location')
                    if not upload_url:
                        logger.error("No upload URL received")
                        return None
                
                # Step 2: Upload video file
                with open(video_file.file_path, 'rb') as f:
                    video_data = f.read()
                
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": video_file.media_type or "video/mp4",
                    "Content-Length": str(len(video_data))
                }
                
                async with session.put(
                    upload_url,
                    headers=headers,
                    data=video_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('id')
                    else:
                        error = await response.text()
                        logger.error(f"Failed to upload video: {error}")
                        return None
        
        except Exception as e:
            logger.error(f"Error uploading video file: {e}")
            return None
    
    async def _upload_thumbnail(self, video_id: str, thumbnail: MediaFile) -> bool:
        """Upload thumbnail for a video."""
        try:
            with open(thumbnail.file_path, 'rb') as f:
                thumbnail_data = f.read()
            
            async with self._get_session() as session:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": thumbnail.media_type or "image/jpeg"
                }
                
                params = {"videoId": video_id}
                
                async with session.post(
                    f"{self.upload_url}/thumbnails/set",
                    headers=headers,
                    params=params,
                    data=thumbnail_data
                ) as response:
                    return response.status == 200
        
        except Exception as e:
            logger.error(f"Error uploading thumbnail: {e}")
            return False
    
    def _format_description(self, content: Content) -> str:
        """Format video description with links and hashtags."""
        description = content.text
        
        # Add links if provided
        if hasattr(content, 'links') and content.links:
            description += "\n\n🔗 Links:\n"
            for link in content.links:
                description += f"• {link.get('title', 'Link')}: {link.get('url')}\n"
        
        # Add hashtags
        if content.hashtags:
            hashtags = [f'#{tag.lstrip("#")}' for tag in content.hashtags]
            description += "\n\n" + " ".join(hashtags)
        
        # Ensure within limit
        if len(description) > self.character_limit:
            description = description[:self.character_limit-3] + "..."
        
        return description
    
    def _extract_tags(self, content: Content) -> List[str]:
        """Extract tags from content."""
        tags = []
        
        # Add hashtags as tags
        if content.hashtags:
            tags.extend([tag.lstrip('#') for tag in content.hashtags])
        
        # Add any additional tags from platform data
        if content.platform_data and 'tags' in content.platform_data:
            tags.extend(content.platform_data['tags'])
        
        # Ensure total length doesn't exceed limit
        result_tags = []
        total_length = 0
        
        for tag in tags:
            tag_length = len(tag) + 1  # +1 for comma separator
            if total_length + tag_length <= self.tags_limit:
                result_tags.append(tag)
                total_length += tag_length
            else:
                break
        
        return result_tags
    
    def _get_authenticated_headers(self) -> Dict[str, str]:
        """Get headers with authentication."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8",
            "Accept-Charset": "utf-8"
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            # Set up connector with proper encoding
            connector = aiohttp.TCPConnector(
                enable_cleanup_closed=True
            )
            
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=300),  # 5 minutes for video uploads
                connector=connector,
                json_serialize=lambda obj: json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
            )
        return self._session
    
    async def cleanup(self):
        """Cleanup platform resources."""
        await super().cleanup()
        
        if self._session and not self._session.closed:
            await self._session.close()
    
    # Platform-specific validation
    async def _validate_content_platform_specific(self, content: Content) -> Dict[str, Any]:
        """YouTube-specific content validation."""
        errors = []
        warnings = []
        
        # Title validation
        if not content.title:
            errors.append("YouTube videos require a title")
        elif len(content.title) > self.title_limit:
            errors.append(f"Title exceeds {self.title_limit} character limit")
        
        # Description validation
        if len(content.text) > self.character_limit:
            errors.append(f"Description exceeds {self.character_limit} character limit")
        
        # Video file validation
        if content.content_type in [ContentType.VIDEO, ContentType.SHORT]:
            if not content.media or not content.media[0].media_type.startswith('video/'):
                errors.append("Video content requires a video file")
            else:
                video = content.media[0]
                
                # File size check (128GB limit)
                if video.file_size and video.file_size > 128 * 1024 * 1024 * 1024:
                    errors.append("Video file exceeds YouTube's 128GB limit")
                
                # Duration check for Shorts
                if content.content_type == ContentType.SHORT:
                    if video.duration and video.duration > 60:
                        errors.append("YouTube Shorts must be 60 seconds or less")
                    
                    # Aspect ratio check
                    if video.aspect_ratio and (video.aspect_ratio > 1.0):
                        warnings.append("YouTube Shorts should be vertical (9:16 aspect ratio)")
        
        # Tags validation
        if content.hashtags:
            tags_text = ",".join([tag.lstrip('#') for tag in content.hashtags])
            if len(tags_text) > self.tags_limit:
                warnings.append(f"Combined tags exceed {self.tags_limit} character limit")
        
        return {
            'errors': errors,
            'warnings': warnings
        }
    
    async def _get_analytics_impl(self, post_id: Optional[str], timeframe: Optional[str]) -> Dict[str, Any]:
        """Get analytics data for YouTube videos."""
        try:
            if post_id:
                # Get video statistics
                async with self._get_session() as session:
                    headers = self._get_authenticated_headers()
                    params = {
                        "part": "statistics",
                        "id": post_id
                    }
                    
                    async with session.get(
                        f"{self.base_url}/videos",
                        headers=headers,
                        params=params
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            items = data.get('items', [])
                            
                            if items:
                                stats = items[0].get('statistics', {})
                                return {
                                    'platform': self.platform_name,
                                    'post_id': post_id,
                                    'metrics': {
                                        'views': int(stats.get('viewCount', 0)),
                                        'likes': int(stats.get('likeCount', 0)),
                                        'dislikes': int(stats.get('dislikeCount', 0)),
                                        'comments': int(stats.get('commentCount', 0)),
                                        'favorites': int(stats.get('favoriteCount', 0))
                                    }
                                }
            else:
                # Get channel analytics
                # Note: Detailed analytics require YouTube Analytics API
                async with self._get_session() as session:
                    headers = self._get_authenticated_headers()
                    params = {
                        "part": "statistics",
                        "id": self.channel_id
                    }
                    
                    async with session.get(
                        f"{self.base_url}/channels",
                        headers=headers,
                        params=params
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            items = data.get('items', [])
                            
                            if items:
                                stats = items[0].get('statistics', {})
                                return {
                                    'platform': self.platform_name,
                                    'channel_metrics': {
                                        'subscribers': int(stats.get('subscriberCount', 0)),
                                        'total_views': int(stats.get('viewCount', 0)),
                                        'total_videos': int(stats.get('videoCount', 0))
                                    }
                                }
            
            return {'error': 'No analytics data available', 'platform': self.platform_name}
        
        except Exception as e:
            logger.error(f"YouTube analytics error: {e}")
            return {'error': str(e), 'platform': self.platform_name}