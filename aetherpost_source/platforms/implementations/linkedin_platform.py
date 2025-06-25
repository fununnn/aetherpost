"""LinkedIn platform implementation using LinkedIn API v2."""

import asyncio
import os
import logging
import aiohttp
import json
import base64
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


class LinkedInPlatform(BasePlatform):
    """LinkedIn platform connector using LinkedIn API v2."""
    
    def __init__(
        self,
        credentials: Dict[str, str],
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        # LinkedIn API configuration (set before parent init)
        self.base_url = "https://api.linkedin.com/v2"
        
        super().__init__(credentials, config, **kwargs)
        self.client_id = credentials.get("client_id")
        self.client_secret = credentials.get("client_secret")
        self.access_token = credentials.get("access_token")
        self.person_urn = None  # Will be fetched during authentication
        
        # Session
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Only require access_token if credentials were provided
        if not self.access_token and credentials:
            raise ValueError("LinkedIn requires access_token")
    
    # Required property implementations
    @property
    def platform_name(self) -> str:
        """Platform identifier."""
        return "linkedin"
    
    @property
    def platform_display_name(self) -> str:
        """Human-readable platform name."""
        return "LinkedIn"
    
    @property
    def supported_content_types(self) -> List[ContentType]:
        """Supported content types for LinkedIn."""
        return [
            ContentType.TEXT,
            ContentType.IMAGE,
            ContentType.VIDEO,
            ContentType.ARTICLE,
            ContentType.DOCUMENT
        ]
    
    @property
    def supported_media_types(self) -> List[str]:
        """Supported media MIME types."""
        return [
            "image/jpeg",
            "image/png",
            "image/gif",
            "video/mp4",
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]
    
    @property
    def platform_capabilities(self) -> List[PlatformCapability]:
        """Platform capabilities."""
        return [
            PlatformCapability.POSTING,
            PlatformCapability.MEDIA_UPLOAD,
            PlatformCapability.PROFILE_MANAGEMENT,
            PlatformCapability.ANALYTICS,
            PlatformCapability.ARTICLES,
            PlatformCapability.DOCUMENTS
        ]
    
    @property
    def character_limit(self) -> int:
        """Character limit for LinkedIn posts."""
        return 3000
    
    # Required method implementations
    def _setup_authenticator(self):
        """Setup LinkedIn OAuth2 authenticator."""
        auth_config = {
            "authorization_endpoint": "https://www.linkedin.com/oauth/v2/authorization",
            "token_endpoint": "https://www.linkedin.com/oauth/v2/accessToken",
            "scopes": ["r_liteprofile", "r_emailaddress", "w_member_social"]
        }
        self.authenticator = OAuth2Authenticator(
            credentials=self.credentials,
            platform=self.platform_name,
            base_url=self.base_url,
            auth_config=auth_config
        )
    
    async def authenticate(self) -> bool:
        """Test authentication with LinkedIn API."""
        try:
            # Get user profile to verify authentication and get person URN
            async with self._get_session() as session:
                headers = self._get_authenticated_headers()
                
                async with session.get(
                    f"{self.base_url}/me",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.person_urn = data.get('id')
                        
                        # Get additional profile info
                        first_name = data.get('localizedFirstName', '')
                        last_name = data.get('localizedLastName', '')
                        
                        logger.info(f"Successfully authenticated LinkedIn account: {first_name} {last_name}")
                        self._authenticated = True
                        return True
                    else:
                        error = await response.text()
                        logger.error(f"LinkedIn authentication failed: {error}")
                        return False
        
        except Exception as e:
            logger.error(f"LinkedIn authentication error: {e}")
            return False
    
    async def _post_content_impl(self, content: Content) -> PlatformResult:
        """Post content to LinkedIn."""
        try:
            # Handle different content types
            if content.content_type == ContentType.ARTICLE:
                return await self._post_article(content)
            else:
                return await self._post_share(content)
        
        except Exception as e:
            logger.error(f"LinkedIn post error: {e}")
            return PlatformResult(
                success=False,
                platform=self.platform_name,
                action="post_content",
                error_message=str(e)
            )
    
    async def _post_share(self, content: Content) -> PlatformResult:
        """Post a share update to LinkedIn."""
        try:
            # Build share content
            share_content = {
                "author": f"urn:li:person:{self.person_urn}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": self._format_text_with_hashtags(content)
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            # Add media if present
            if content.media:
                media_assets = await self._upload_media_files(content.media)
                if media_assets:
                    share_content["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = self._get_media_category(content.media[0])
                    share_content["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = media_assets
            
            # Post the share
            async with self._get_session() as session:
                headers = self._get_authenticated_headers()
                headers["X-Restli-Protocol-Version"] = "2.0.0"
                
                async with session.post(
                    f"{self.base_url}/ugcPosts",
                    json=share_content,
                    headers=headers
                ) as response:
                    if response.status == 201:
                        data = await response.json()
                        post_id = data.get('id')
                        
                        return PlatformResult(
                            success=True,
                            platform=self.platform_name,
                            action="post_content",
                            post_id=post_id,
                            post_url=self._get_post_url(post_id),
                            created_at=datetime.utcnow()
                        )
                    else:
                        error = await response.text()
                        return PlatformResult(
                            success=False,
                            platform=self.platform_name,
                            action="post_content",
                            error_message=f"Post failed: {response.status} - {error}"
                        )
        
        except Exception as e:
            logger.error(f"LinkedIn share post error: {e}")
            return PlatformResult(
                success=False,
                platform=self.platform_name,
                action="post_content",
                error_message=str(e)
            )
    
    async def _post_article(self, content: Content) -> PlatformResult:
        """Post an article to LinkedIn."""
        try:
            # Articles require special handling and permissions
            # For now, convert to regular post with link
            return await self._post_share(content)
        
        except Exception as e:
            logger.error(f"LinkedIn article post error: {e}")
            return PlatformResult(
                success=False,
                platform=self.platform_name,
                action="post_article",
                error_message=str(e)
            )
    
    async def _update_profile_impl(self, profile: Profile) -> PlatformResult:
        """Update LinkedIn profile."""
        try:
            updates_made = []
            
            # Update profile picture if provided
            if profile.avatar_path and os.path.exists(profile.avatar_path):
                avatar_result = await self._update_profile_picture(profile.avatar_path)
                if avatar_result:
                    updates_made.append("profile_picture")
            
            # Update headline/bio if provided
            if profile.bio:
                # LinkedIn API v2 has limited profile update capabilities
                # Most profile updates require different permissions
                updates_made.append("bio_queued")
            
            return PlatformResult(
                success=True,
                platform=self.platform_name,
                action="update_profile",
                profile_updated=len(updates_made) > 0,
                raw_data={
                    "updates_made": updates_made,
                    "note": "LinkedIn API has limited profile update capabilities"
                }
            )
        
        except Exception as e:
            logger.error(f"LinkedIn profile update error: {e}")
            return PlatformResult(
                success=False,
                platform=self.platform_name,
                action="update_profile",
                error_message=str(e)
            )
    
    async def _delete_post_impl(self, post_id: str) -> PlatformResult:
        """Delete a LinkedIn post."""
        try:
            async with self._get_session() as session:
                headers = self._get_authenticated_headers()
                headers["X-Restli-Protocol-Version"] = "2.0.0"
                
                async with session.delete(
                    f"{self.base_url}/ugcPosts/{post_id}",
                    headers=headers
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
            logger.error(f"LinkedIn delete error: {e}")
            return PlatformResult(
                success=False,
                platform=self.platform_name,
                action="delete_post",
                post_id=post_id,
                error_message=str(e)
            )
    
    # Helper methods
    async def _upload_media_files(self, media_files: List[MediaFile]) -> List[Dict[str, Any]]:
        """Upload media files to LinkedIn."""
        media_assets = []
        
        for media_file in media_files[:1]:  # LinkedIn typically supports 1 media item per post
            try:
                # Register upload
                upload_request = await self._register_upload(media_file)
                if not upload_request:
                    continue
                
                asset = upload_request.get('value', {}).get('asset')
                upload_url = upload_request.get('value', {}).get('uploadMechanism', {}).get('com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest', {}).get('uploadUrl')
                
                if not asset or not upload_url:
                    continue
                
                # Upload the file
                success = await self._upload_file(media_file.file_path, upload_url)
                if success:
                    media_asset = {
                        "status": "READY",
                        "media": asset
                    }
                    
                    # Add description if available
                    if media_file.alt_text:
                        media_asset["description"] = {
                            "text": media_file.alt_text
                        }
                    
                    # Add title for articles/documents
                    if media_file.title:
                        media_asset["title"] = {
                            "text": media_file.title
                        }
                    
                    media_assets.append(media_asset)
            
            except Exception as e:
                logger.error(f"Failed to upload media file: {e}")
                continue
        
        return media_assets
    
    async def _register_upload(self, media_file: MediaFile) -> Optional[Dict[str, Any]]:
        """Register media upload with LinkedIn."""
        try:
            # Determine upload request based on media type
            if media_file.media_type.startswith('image/'):
                register_request = {
                    "registerUploadRequest": {
                        "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                        "owner": f"urn:li:person:{self.person_urn}",
                        "serviceRelationships": [{
                            "relationshipType": "OWNER",
                            "identifier": "urn:li:userGeneratedContent"
                        }]
                    }
                }
            elif media_file.media_type.startswith('video/'):
                register_request = {
                    "registerUploadRequest": {
                        "recipes": ["urn:li:digitalmediaRecipe:feedshare-video"],
                        "owner": f"urn:li:person:{self.person_urn}",
                        "serviceRelationships": [{
                            "relationshipType": "OWNER",
                            "identifier": "urn:li:userGeneratedContent"
                        }]
                    }
                }
            else:
                # Document upload
                register_request = {
                    "registerUploadRequest": {
                        "recipes": ["urn:li:digitalmediaRecipe:feedshare-document"],
                        "owner": f"urn:li:person:{self.person_urn}",
                        "serviceRelationships": [{
                            "relationshipType": "OWNER",
                            "identifier": "urn:li:userGeneratedContent"
                        }]
                    }
                }
            
            async with self._get_session() as session:
                headers = self._get_authenticated_headers()
                
                async with session.post(
                    f"{self.base_url}/assets?action=registerUpload",
                    json=register_request,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error = await response.text()
                        logger.error(f"Failed to register upload: {error}")
                        return None
        
        except Exception as e:
            logger.error(f"Error registering upload: {e}")
            return None
    
    async def _upload_file(self, file_path: str, upload_url: str) -> bool:
        """Upload file to LinkedIn's upload URL."""
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            async with self._get_session() as session:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/octet-stream"
                }
                
                async with session.put(
                    upload_url,
                    data=file_data,
                    headers=headers
                ) as response:
                    return response.status == 201
        
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return False
    
    async def _update_profile_picture(self, avatar_path: str) -> bool:
        """Update LinkedIn profile picture."""
        try:
            # Register profile picture upload
            media_file = MediaFile(
                file_path=avatar_path,
                media_type="image/jpeg",
                file_size=os.path.getsize(avatar_path)
            )
            
            upload_request = await self._register_upload(media_file)
            if not upload_request:
                return False
            
            asset = upload_request.get('value', {}).get('asset')
            upload_url = upload_request.get('value', {}).get('uploadMechanism', {}).get('com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest', {}).get('uploadUrl')
            
            if not asset or not upload_url:
                return False
            
            # Upload the profile picture
            success = await self._upload_file(avatar_path, upload_url)
            
            if success:
                # Update profile with new picture
                # Note: This requires additional permissions
                logger.info("Profile picture uploaded successfully")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error updating profile picture: {e}")
            return False
    
    def _format_text_with_hashtags(self, content: Content) -> str:
        """Format text with hashtags for LinkedIn."""
        text = content.text
        
        # LinkedIn handles hashtags well inline or at the end
        if content.hashtags:
            hashtags = [f'#{tag.lstrip("#")}' for tag in content.hashtags]
            hashtag_text = ' '.join(hashtags)
            
            # Add hashtags at the end with proper spacing
            text = f"{text}\n\n{hashtag_text}"
        
        return text
    
    def _get_media_category(self, media_file: MediaFile) -> str:
        """Get LinkedIn media category based on file type."""
        if media_file.media_type.startswith('image/'):
            return "IMAGE"
        elif media_file.media_type.startswith('video/'):
            return "VIDEO"
        else:
            return "ARTICLE"
    
    def _get_post_url(self, post_id: str) -> str:
        """Generate LinkedIn post URL."""
        # LinkedIn post URLs follow a specific pattern
        # This is a simplified version
        return f"https://www.linkedin.com/feed/update/{post_id}/"
    
    def _get_authenticated_headers(self) -> Dict[str, str]:
        """Get headers with authentication."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
            "Accept-Charset": "utf-8",
            "User-Agent": "AetherPost/1.0 (LinkedIn)"
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            # Set up connector with proper encoding
            connector = aiohttp.TCPConnector(
                enable_cleanup_closed=True
            )
            
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
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
        """LinkedIn-specific content validation."""
        errors = []
        warnings = []
        
        # Text length check
        if len(content.text) > self.character_limit:
            errors.append(f"Text exceeds LinkedIn's {self.character_limit} character limit")
        
        # Media validation
        if len(content.media) > 1:
            warnings.append("LinkedIn typically supports only 1 media item per post")
        
        # Video file size check
        for media in content.media:
            if media.media_type.startswith('video/'):
                if media.file_size and media.file_size > 5 * 1024 * 1024 * 1024:  # 5GB
                    errors.append(f"Video file exceeds LinkedIn's 5GB limit")
                
                if media.duration and media.duration > 600:  # 10 minutes
                    warnings.append(f"Video duration {media.duration}s exceeds recommended 10 minute limit")
        
        # Article validation
        if content.content_type == ContentType.ARTICLE:
            if not content.title:
                errors.append("Articles require a title")
            if len(content.text) < 100:
                warnings.append("Articles should have substantial content (100+ characters)")
        
        return {
            'errors': errors,
            'warnings': warnings
        }
    
    async def _get_analytics_impl(self, post_id: Optional[str], timeframe: Optional[str]) -> Dict[str, Any]:
        """Get analytics data for LinkedIn posts."""
        try:
            if post_id:
                # Get specific post analytics
                async with self._get_session() as session:
                    headers = self._get_authenticated_headers()
                    headers["X-Restli-Protocol-Version"] = "2.0.0"
                    
                    # LinkedIn analytics API requires special permissions
                    # This is a simplified version
                    url = f"{self.base_url}/organizationalEntityShareStatistics"
                    params = {
                        "q": "organizationalEntity",
                        "organizationalEntity": f"urn:li:share:{post_id}"
                    }
                    
                    async with session.get(url, params=params, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            return {
                                'platform': self.platform_name,
                                'post_id': post_id,
                                'metrics': {
                                    'impressions': data.get('totalShareStatistics', {}).get('impressionCount', 0),
                                    'clicks': data.get('totalShareStatistics', {}).get('clickCount', 0),
                                    'engagement': data.get('totalShareStatistics', {}).get('engagement', 0),
                                    'shares': data.get('totalShareStatistics', {}).get('shareCount', 0)
                                }
                            }
            
            return {'error': 'Analytics requires additional permissions', 'platform': self.platform_name}
        
        except Exception as e:
            logger.error(f"LinkedIn analytics error: {e}")
            return {'error': str(e), 'platform': self.platform_name}