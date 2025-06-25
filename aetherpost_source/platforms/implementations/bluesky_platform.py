"""Bluesky (AT Protocol) platform implementation."""

import asyncio
import aiohttp
import json
import os
import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from urllib.parse import urlparse

from ..core.base_platform import BasePlatform, PlatformResult, Content, Profile, ContentType, PlatformCapability, MediaFile
from ..core.authentication.basic_auth_authenticator import BasicAuthAuthenticator
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


class BlueskyPlatform(BasePlatform):
    """Bluesky social media platform connector using AT Protocol."""
    
    def __init__(
        self,
        credentials: Dict[str, str],
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        # Bluesky AT Protocol configuration (set before parent init)
        self.base_url = credentials.get("base_url", "https://bsky.social")
        self.identifier = credentials.get("identifier", "")  # username or email
        self.password = credentials.get("password", "")
        
        super().__init__(credentials, config, **kwargs)
        
        # Session state
        self.session_token = None
        self.did = None
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Only raise error if we're not in test/info mode
        if not self.identifier or not self.password:
            if credentials:  # Only raise if credentials were actually provided
                raise ValueError("Bluesky requires identifier and password")
    
    # Required property implementations
    @property
    def platform_name(self) -> str:
        """Platform identifier."""
        return "bluesky"
    
    @property
    def platform_display_name(self) -> str:
        """Human-readable platform name."""
        return "Bluesky"
    
    @property
    def supported_content_types(self) -> List[ContentType]:
        """Supported content types for Bluesky."""
        return [
            ContentType.TEXT,
            ContentType.IMAGE,
            ContentType.THREAD
        ]
    
    @property
    def supported_media_types(self) -> List[str]:
        """Supported media MIME types."""
        return [
            "image/jpeg",
            "image/png", 
            "image/gif",
            "image/webp"
        ]
    
    @property
    def platform_capabilities(self) -> List[PlatformCapability]:
        """Platform capabilities."""
        return [
            PlatformCapability.POSTING,
            PlatformCapability.MEDIA_UPLOAD,
            PlatformCapability.PROFILE_MANAGEMENT,
            PlatformCapability.THREADS
        ]
    
    @property
    def character_limit(self) -> int:
        """Character limit for Bluesky posts."""
        return 300
    
    # Required method implementations
    def _setup_authenticator(self):
        """Setup Bluesky authenticator (using basic auth for AT Protocol)."""
        self.authenticator = BasicAuthAuthenticator(
            credentials={
                'username': self.identifier,
                'password': self.password
            },
            platform=self.platform_name,
            base_url=self.base_url
        )
    
    async def authenticate(self) -> bool:
        """Authenticate with Bluesky using AT Protocol."""
        try:
            logger.info("Authenticating with Bluesky AT Protocol")
            
            auth_data = {
                "identifier": self.identifier,
                "password": self.password
            }
            
            session = await self._get_session()
            async with session.post(
                f"{self.base_url}/xrpc/com.atproto.server.createSession",
                json=auth_data
            ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.session_token = data.get("accessJwt")
                        self.did = data.get("did")
                        
                        # Get profile info for verification
                        profile = await self._get_profile()
                        if profile:
                            handle = profile.get('handle', 'Unknown')
                            followers = profile.get('followersCount', 0)
                            logger.info(f"Successfully authenticated Bluesky account: @{handle} ({followers} followers)")
                            self._authenticated = True
                            return True
                        else:
                            logger.warning("Authentication successful but couldn't retrieve profile")
                            self._authenticated = True
                            return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Bluesky auth failed: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Bluesky authentication error: {e}")
            return False
    
    async def _post_content_impl(self, content: Content) -> PlatformResult:
        """Post content to Bluesky with enhanced features."""
        try:
            # Handle different post types
            if content.content_type == ContentType.THREAD and content.thread_posts:
                return await self._post_thread(content.thread_posts)
            
            # Optimize text for Bluesky
            optimized_text = self._optimize_text_for_bluesky(content.text, content.hashtags)
            
            # Extract and handle links
            facets = self._extract_facets(optimized_text)
            
            # Build post record
            record = {
                "text": optimized_text,
                "createdAt": datetime.utcnow().isoformat() + "Z",
                "$type": "app.bsky.feed.post"
            }
            
            # Add facets for links and mentions
            if facets:
                record["facets"] = facets
            
            # Handle embeds (media)
            embed = await self._create_embed(optimized_text, content.media)
            if embed:
                record["embed"] = embed
            
            # Create post
            post_data = {
                "repo": self.did,
                "collection": "app.bsky.feed.post",
                "record": record
            }
            
            headers = self._get_authenticated_headers()
            
            session = await self._get_session()
            async with session.post(
                f"{self.base_url}/xrpc/com.atproto.repo.createRecord",
                json=post_data,
                headers=headers
            ) as response:
                    if response.status == 200:
                        data = await response.json()
                        post_uri = data.get("uri")
                        post_id = post_uri.split("/")[-1] if post_uri else None
                        
                        return PlatformResult(
                            success=True,
                            platform=self.platform_name,
                            action="post_content",
                            post_id=post_id,
                            post_url=f"https://bsky.app/profile/{self.identifier}/post/{post_id}",
                            raw_data=data,
                            created_at=datetime.utcnow()
                        )
                    else:
                        error_text = await response.text()
                        logger.error(f"Post failed: {response.status} - {error_text}")
                        return PlatformResult(
                            success=False,
                            platform=self.platform_name,
                            action="post_content",
                            error_message=f"Post failed: {response.status} - {error_text}"
                        )
                        
        except Exception as e:
            logger.error(f"Bluesky post error: {e}")
            return PlatformResult(
                success=False,
                platform=self.platform_name,
                action="post_content",
                error_message=str(e)
            )
    
    async def _update_profile_impl(self, profile: Profile) -> PlatformResult:
        """Update Bluesky profile."""
        try:
            # Get current profile record (not the profile API response)
            current_record = await self._get_profile_record()
            if not current_record:
                return PlatformResult(
                    success=False,
                    platform=self.platform_name,
                    action="update_profile",
                    error_message="Could not retrieve current profile record"
                )
            
            # Use the 'value' part of the record as base
            profile_record = current_record.get("value", {}).copy()
            
            # Ensure proper type
            profile_record["$type"] = "app.bsky.actor.profile"
            
            if profile.display_name:
                profile_record["displayName"] = profile.display_name
            
            if profile.bio:
                profile_record["description"] = profile.bio
            
            # Handle avatar upload
            if profile.avatar_path and os.path.exists(profile.avatar_path):
                avatar_blob = await self._upload_avatar(profile.avatar_path)
                if avatar_blob:
                    profile_record["avatar"] = avatar_blob
            
            # Handle banner upload  
            if profile.cover_path and os.path.exists(profile.cover_path):
                banner_blob = await self._upload_banner(profile.cover_path)
                if banner_blob:
                    profile_record["banner"] = banner_blob
            
            # Update profile record
            update_data = {
                "repo": self.did,
                "collection": "app.bsky.actor.profile",
                "rkey": "self",
                "record": profile_record
            }
            
            headers = self._get_authenticated_headers()
            
            session = await self._get_session()
            async with session.post(
                f"{self.base_url}/xrpc/com.atproto.repo.putRecord",
                json=update_data,
                headers=headers
            ) as response:
                    if response.status == 200:
                        return PlatformResult(
                            success=True,
                            platform=self.platform_name,
                            action="update_profile",
                            profile_updated=True,
                            raw_data=await response.json()
                        )
                    else:
                        error_text = await response.text()
                        return PlatformResult(
                            success=False,
                            platform=self.platform_name,
                            action="update_profile",
                            error_message=f"Profile update failed: {response.status} - {error_text}"
                        )
            
        except Exception as e:
            logger.error(f"Bluesky profile update error: {e}")
            return PlatformResult(
                success=False,
                platform=self.platform_name,
                action="update_profile",
                error_message=str(e)
            )
    
    async def _delete_post_impl(self, post_id: str) -> PlatformResult:
        """Delete a post from Bluesky."""
        try:
            delete_data = {
                "repo": self.did,
                "collection": "app.bsky.feed.post",
                "rkey": post_id
            }
            
            headers = self._get_authenticated_headers()
            
            session = await self._get_session()
            async with session.post(
                f"{self.base_url}/xrpc/com.atproto.repo.deleteRecord",
                json=delete_data,
                headers=headers
            ) as response:
                    return PlatformResult(
                        success=response.status == 200,
                        platform=self.platform_name,
                        action="delete_post",
                        post_id=post_id
                    )
                    
        except Exception as e:
            logger.error(f"Error deleting Bluesky post {post_id}: {e}")
            return PlatformResult(
                success=False,
                platform=self.platform_name,
                action="delete_post",
                post_id=post_id,
                error_message=str(e)
            )
    
    # Helper methods
    async def _post_thread(self, thread_posts: List[str]) -> PlatformResult:
        """Post a thread to Bluesky."""
        try:
            thread_results = []
            reply_to = None
            
            for i, post_text in enumerate(thread_posts):
                optimized_text = self._optimize_text_for_bluesky(post_text, [])
                facets = self._extract_facets(optimized_text)
                
                record = {
                    "text": optimized_text,
                    "createdAt": datetime.utcnow().isoformat() + "Z",
                    "$type": "app.bsky.feed.post"
                }
                
                if facets:
                    record["facets"] = facets
                
                # Add reply reference for subsequent posts
                if reply_to:
                    record["reply"] = {
                        "root": thread_results[0]["uri"],
                        "parent": reply_to
                    }
                
                post_data = {
                    "repo": self.did,
                    "collection": "app.bsky.feed.post",
                    "record": record
                }
                
                headers = self._get_authenticated_headers()
                
                session = await self._get_session()
                async with session.post(
                    f"{self.base_url}/xrpc/com.atproto.repo.createRecord",
                    json=post_data,
                    headers=headers
                ) as response:
                        if response.status == 200:
                            data = await response.json()
                            post_uri = data.get("uri")
                            post_id = post_uri.split("/")[-1] if post_uri else None
                            
                            result = {
                                "post_id": post_id,
                                "uri": post_uri,
                                "url": f"https://bsky.app/profile/{self.identifier}/post/{post_id}",
                                "thread_position": i + 1
                            }
                            
                            thread_results.append(result)
                            reply_to = post_uri
                            
                            # Small delay between thread posts
                            await asyncio.sleep(1)
                        else:
                            error_text = await response.text()
                            logger.error(f"Thread post {i+1} failed: {response.status} - {error_text}")
                            break
            
            return PlatformResult(
                success=len(thread_results) > 0,
                platform=self.platform_name,
                action="post_thread",
                raw_data={
                    "thread_count": len(thread_results),
                    "posts": thread_results,
                    "thread_url": thread_results[0]["url"] if thread_results else None
                }
            )
            
        except Exception as e:
            logger.error(f"Thread posting failed: {e}")
            return PlatformResult(
                success=False,
                platform=self.platform_name,
                action="post_thread",
                error_message=str(e)
            )
    
    def _optimize_text_for_bluesky(self, text: str, hashtags: List[str]) -> str:
        """Optimize text for Bluesky posting."""
        
        # Add hashtags if provided
        if hashtags:
            formatted_hashtags = [f"#{tag.lstrip('#')}" for tag in hashtags]
            hashtag_text = " " + " ".join(formatted_hashtags)
            
            # Check character limit (300 chars)
            if len(text + hashtag_text) <= 300:
                text += hashtag_text
            else:
                # Truncate text to fit hashtags
                available_space = 300 - len(hashtag_text) - 3  # -3 for "..."
                if available_space > 50:  # Keep meaningful text
                    text = text[:available_space] + "..." + hashtag_text
        
        return text
    
    def _extract_facets(self, text: str) -> List[Dict[str, Any]]:
        """Extract facets (links, mentions, hashtags) from text."""
        facets = []
        
        # Extract URLs
        url_pattern = r'https?://[^\s]+'
        for match in re.finditer(url_pattern, text):
            facets.append({
                "index": {
                    "byteStart": match.start(),
                    "byteEnd": match.end()
                },
                "features": [{
                    "$type": "app.bsky.richtext.facet#link",
                    "uri": match.group()
                }]
            })
        
        # Extract mentions (@username)
        mention_pattern = r'@([a-zA-Z0-9._-]+)'
        for match in re.finditer(mention_pattern, text):
            facets.append({
                "index": {
                    "byteStart": match.start(),
                    "byteEnd": match.end()
                },
                "features": [{
                    "$type": "app.bsky.richtext.facet#mention",
                    "did": f"did:plc:{match.group(1)}"  # Simplified - would need DID resolution
                }]
            })
        
        # Extract hashtags
        hashtag_pattern = r'#([a-zA-Z0-9_]+)'
        for match in re.finditer(hashtag_pattern, text):
            facets.append({
                "index": {
                    "byteStart": match.start(),
                    "byteEnd": match.end()
                },
                "features": [{
                    "$type": "app.bsky.richtext.facet#tag",
                    "tag": match.group(1)
                }]
            })
        
        return facets
    
    async def _create_embed(self, text: str, media_files: List[MediaFile]) -> Optional[Dict[str, Any]]:
        """Create embed for post (images or external link)."""
        
        # Handle media files
        if media_files:
            embed_images = await self._upload_media(media_files)
            if embed_images:
                return {
                    "$type": "app.bsky.embed.images",
                    "images": embed_images
                }
        
        # Handle external links
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, text)
        if urls:
            # Use first URL for link card
            url = urls[0]
            link_card = await self._create_link_card(url)
            if link_card:
                return {
                    "$type": "app.bsky.embed.external",
                    "external": link_card
                }
        
        return None
    
    async def _upload_media(self, media_files: List[MediaFile]) -> List[Dict[str, Any]]:
        """Upload media files to Bluesky."""
        uploaded_images = []
        
        for media_file in media_files[:4]:  # Bluesky supports up to 4 images
            try:
                blob = await self._upload_blob(media_file.file_path)
                if blob:
                    uploaded_images.append({
                        "alt": media_file.alt_text or "",
                        "image": blob
                    })
            except Exception as e:
                logger.error(f"Failed to upload {media_file.file_path}: {e}")
                continue
        
        return uploaded_images
    
    async def _upload_blob(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Upload a blob to Bluesky."""
        try:
            # Read file content
            with open(file_path, 'rb') as f:
                media_data = f.read()
            
            # Determine content type
            if file_path.lower().endswith('.png'):
                content_type = 'image/png'
            elif file_path.lower().endswith('.jpg') or file_path.lower().endswith('.jpeg'):
                content_type = 'image/jpeg'
            elif file_path.lower().endswith('.gif'):
                content_type = 'image/gif'
            else:
                content_type = 'application/octet-stream'
            
            # Set up headers for blob upload (different from JSON API)
            upload_headers = {
                'Authorization': f'Bearer {self.session_token}',
                'Content-Type': content_type,
                'Content-Length': str(len(media_data))
            }
            
            session = await self._get_session()
            async with session.post(
                f"{self.base_url}/xrpc/com.atproto.repo.uploadBlob",
                data=media_data,
                headers=upload_headers
            ) as response:
                if response.status == 200:
                    upload_data = await response.json()
                    blob = upload_data.get("blob")
                    logger.info(f"Blob uploaded successfully: {blob}")
                    return blob
                else:
                    error_text = await response.text()
                    logger.error(f"Blob upload failed: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to upload blob: {e}")
            return None
    
    async def _upload_avatar(self, avatar_path: str) -> Optional[Dict[str, Any]]:
        """Upload avatar image."""
        return await self._upload_blob(avatar_path)
    
    async def _upload_banner(self, banner_path: str) -> Optional[Dict[str, Any]]:
        """Upload banner image."""
        return await self._upload_blob(banner_path)
    
    async def _create_link_card(self, url: str) -> Optional[Dict[str, Any]]:
        """Create link card for external URL."""
        try:
            # Basic link card - in production would fetch page metadata
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            return {
                "uri": url,
                "title": f"Link to {domain}",
                "description": f"External link: {url}",
                "thumb": None  # Would upload a thumbnail blob
            }
            
        except Exception as e:
            logger.error(f"Failed to create link card: {e}")
            return None
    
    async def _get_profile(self) -> Optional[Dict[str, Any]]:
        """Get profile information."""
        try:
            headers = self._get_authenticated_headers()
            
            params = {
                "actor": self.did
            }
            
            session = await self._get_session()
            async with session.get(
                f"{self.base_url}/xrpc/app.bsky.actor.getProfile",
                params=params,
                headers=headers
            ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Failed to get profile: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting profile: {e}")
            return None
    
    async def _get_profile_record(self) -> Optional[Dict[str, Any]]:
        """Get profile record for updating."""
        try:
            headers = self._get_authenticated_headers()
            
            params = {
                "repo": self.did,
                "collection": "app.bsky.actor.profile",
                "rkey": "self"
            }
            
            session = await self._get_session()
            async with session.get(
                f"{self.base_url}/xrpc/com.atproto.repo.getRecord",
                params=params,
                headers=headers
            ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Failed to get profile record: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting profile record: {e}")
            return None
    
    def _get_authenticated_headers(self) -> Dict[str, str]:
        """Get headers with authentication."""
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": f"AetherPost/1.0 (bluesky)",
            "Accept": "application/json",
            "Accept-Charset": "utf-8"
        }
        
        if self.session_token:
            headers["Authorization"] = f"Bearer {self.session_token}"
        
        return headers
    
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
        """Bluesky-specific content validation."""
        errors = []
        warnings = []
        
        # Character limit check
        if len(content.text) > 300:
            errors.append("Text exceeds Bluesky's 300 character limit")
        
        # Media count check
        if len(content.media) > 4:
            errors.append("Bluesky supports maximum 4 images per post")
        
        # Thread validation
        if content.content_type == ContentType.THREAD:
            if not content.thread_posts:
                errors.append("Thread type requires thread_posts array")
            elif len(content.thread_posts) > 25:  # Reasonable thread limit
                errors.append("Thread too long (max 25 posts recommended)")
            
            for i, post_text in enumerate(content.thread_posts):
                if len(post_text) > 300:
                    errors.append(f"Thread post {i+1} exceeds 300 character limit")
        
        return {
            'errors': errors,
            'warnings': warnings
        }