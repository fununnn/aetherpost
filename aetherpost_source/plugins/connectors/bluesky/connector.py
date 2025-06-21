"""Bluesky (AT Protocol) connector implementation."""

import asyncio
import aiohttp
import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from urllib.parse import urlparse

from ...base import SNSConnectorBase

logger = logging.getLogger(__name__)


class BlueskyConnector(SNSConnectorBase):
    """Bluesky social media platform connector."""
    
    def __init__(self, credentials: Dict[str, str]):
        self.identifier = credentials.get("identifier")  # username or email
        self.password = credentials.get("password")
        self.base_url = credentials.get("base_url", "https://bsky.social")
        self.session_token = None
        self.did = None
        
        if not self.identifier or not self.password:
            raise ValueError("Bluesky requires identifier and password")
    
    @property
    def name(self) -> str:
        return "bluesky"
    
    @property
    def supported_media_types(self) -> List[str]:
        return ["image/jpeg", "image/png", "image/gif", "image/webp"]
    
    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with Bluesky using AT Protocol."""
        try:
            logger.info("Authenticating with Bluesky AT Protocol")
            
            auth_data = {
                "identifier": self.identifier,
                "password": self.password
            }
            
            async with aiohttp.ClientSession() as session:
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
                            return True
                        else:
                            logger.warning("Authentication successful but couldn't retrieve profile")
                            return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Bluesky auth failed: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Bluesky authentication error: {e}")
            return False
    
    async def post(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Post content to Bluesky with enhanced features."""
        if not self.session_token:
            await self.authenticate({})
        
        if not self.session_token:
            raise Exception("Authentication required")
        
        try:
            # Prepare post data
            text = content.get("text", "")
            media_files = content.get("media", [])
            post_type = content.get("type", "single")
            
            # Handle different post types
            if post_type == "thread" and isinstance(content.get("thread"), list):
                return await self._post_thread(content.get("thread", []))
            
            # Optimize text for Bluesky
            optimized_text = self._optimize_text_for_bluesky(text, content.get("hashtags", []))
            
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
            
            # Handle embeds
            embed = await self._create_embed(optimized_text, media_files)
            if embed:
                record["embed"] = embed
            
            # Create post
            post_data = {
                "repo": self.did,
                "collection": "app.bsky.feed.post",
                "record": record
            }
            
            headers = {
                "Authorization": f"Bearer {self.session_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/xrpc/com.atproto.repo.createRecord",
                    json=post_data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        post_uri = data.get("uri")
                        post_id = post_uri.split("/")[-1] if post_uri else None
                        
                        return {
                            "post_id": post_id,
                            "uri": post_uri,
                            "url": f"https://bsky.app/profile/{self.identifier}/post/{post_id}",
                            "platform": "bluesky",
                            "status": "published",
                            "created_at": datetime.utcnow().isoformat()
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Post failed: {response.status} - {error_text}")
                        raise Exception(f"Post failed: {response.status} - {error_text}")
                        
        except Exception as e:
            logger.error(f"Bluesky post error: {e}")
            return {
                "error": str(e),
                "platform": "bluesky",
                "status": "failed"
            }
    
    async def delete(self, post_id: str) -> bool:
        """Delete a post from Bluesky."""
        if not self.session_token:
            await self.authenticate({})
        
        try:
            # Construct record URI
            record_uri = f"at://{self.did}/app.bsky.feed.post/{post_id}"
            
            delete_data = {
                "repo": self.did,
                "collection": "app.bsky.feed.post",
                "rkey": post_id
            }
            
            headers = {
                "Authorization": f"Bearer {self.session_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/xrpc/com.atproto.repo.deleteRecord",
                    json=delete_data,
                    headers=headers
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            print(f"Error deleting Bluesky post {post_id}: {e}")
            return False
    
    async def get_metrics(self, post_id: str) -> Dict[str, Any]:
        """Get metrics for a Bluesky post."""
        if not self.session_token:
            await self.authenticate({})
        
        try:
            # Get post details
            post_uri = f"at://{self.did}/app.bsky.feed.post/{post_id}"
            
            params = {
                "uri": post_uri
            }
            
            headers = {
                "Authorization": f"Bearer {self.session_token}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/xrpc/app.bsky.feed.getPostThread",
                    params=params,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        post_data = data.get("thread", {}).get("post", {})
                        
                        # Extract metrics
                        like_count = post_data.get("likeCount", 0)
                        repost_count = post_data.get("repostCount", 0)
                        reply_count = post_data.get("replyCount", 0)
                        
                        return {
                            "likes": like_count,
                            "reposts": repost_count,
                            "replies": reply_count,
                            "total_engagement": like_count + repost_count + reply_count,
                            "platform": "bluesky"
                        }
                    else:
                        return {"error": f"Failed to get metrics: {response.status}"}
                        
        except Exception as e:
            return {"error": str(e)}
    
    async def _upload_media(self, media_files: List[str]) -> List[Dict[str, Any]]:
        """Upload media files to Bluesky."""
        uploaded_images = []
        
        for media_file in media_files[:4]:  # Bluesky supports up to 4 images
            try:
                async with aiohttp.ClientSession() as session:
                    with open(media_file, 'rb') as f:
                        data = aiohttp.FormData()
                        data.add_field('file', f, filename=media_file)
                        
                        headers = {
                            "Authorization": f"Bearer {self.session_token}"
                        }
                        
                        async with session.post(
                            f"{self.base_url}/xrpc/com.atproto.repo.uploadBlob",
                            data=data,
                            headers=headers
                        ) as response:
                            if response.status == 200:
                                upload_data = await response.json()
                                blob = upload_data.get("blob")
                                
                                uploaded_images.append({
                                    "alt": "",  # Alt text for accessibility
                                    "image": blob
                                })
            except Exception as e:
                print(f"Failed to upload {media_file}: {e}")
                continue
        
        return uploaded_images
    
    async def _post_thread(self, thread_posts: List[str]) -> Dict[str, Any]:
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
                
                headers = {
                    "Authorization": f"Bearer {self.session_token}",
                    "Content-Type": "application/json"
                }
                
                async with aiohttp.ClientSession() as session:
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
            
            return {
                "status": "published" if thread_results else "failed",
                "platform": "bluesky",
                "type": "thread",
                "thread_count": len(thread_results),
                "posts": thread_results,
                "thread_url": thread_results[0]["url"] if thread_results else None
            }
            
        except Exception as e:
            logger.error(f"Thread posting failed: {e}")
            return {
                "error": str(e),
                "platform": "bluesky",
                "status": "failed"
            }
    
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
    
    async def _create_embed(self, text: str, media_files: List[str]) -> Optional[Dict[str, Any]]:
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
            headers = {
                "Authorization": f"Bearer {self.session_token}"
            }
            
            params = {
                "actor": self.did
            }
            
            async with aiohttp.ClientSession() as session:
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
    
    async def search_posts(self, query: str, limit: int = 25) -> Dict[str, Any]:
        """Search for posts on Bluesky."""
        try:
            headers = {
                "Authorization": f"Bearer {self.session_token}"
            }
            
            params = {
                "q": query,
                "limit": limit
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/xrpc/app.bsky.feed.searchPosts",
                    params=params,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "posts": data.get("posts", []),
                            "cursor": data.get("cursor"),
                            "total": len(data.get("posts", [])),
                            "platform": "bluesky"
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Search failed: {response.status} - {error_text}")
                        return {"error": f"Search failed: {response.status}"}
                        
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {"error": str(e)}
    
    def validate_content(self, content: Dict[str, Any]) -> List[str]:
        """Validate content for Bluesky."""
        issues = []
        
        text = content.get('text', '')
        media = content.get('media', [])
        post_type = content.get('type', 'single')
        
        # Character limit check
        if len(text) > 300:
            issues.append("Text exceeds Bluesky's 300 character limit")
        
        # Media count check
        if len(media) > 4:
            issues.append("Bluesky supports maximum 4 images per post")
        
        # Thread validation
        if post_type == "thread":
            thread_posts = content.get('thread', [])
            if not thread_posts:
                issues.append("Thread type requires 'thread' array")
            elif len(thread_posts) > 25:  # Reasonable thread limit
                issues.append("Thread too long (max 25 posts recommended)")
            
            for i, post_text in enumerate(thread_posts):
                if len(post_text) > 300:
                    issues.append(f"Thread post {i+1} exceeds 300 character limit")
        
        return issues