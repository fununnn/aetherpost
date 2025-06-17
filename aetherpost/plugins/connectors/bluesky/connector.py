"""Bluesky (AT Protocol) connector implementation."""

import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime

from ...base import SNSConnectorBase


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
                        return True
                    else:
                        print(f"Bluesky auth failed: {response.status}")
                        return False
                        
        except Exception as e:
            print(f"Bluesky authentication error: {e}")
            return False
    
    async def post(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Post content to Bluesky."""
        if not self.session_token:
            await self.authenticate({})
        
        if not self.session_token:
            raise Exception("Authentication required")
        
        try:
            # Prepare post data
            text = content.get("text", "")
            media_files = content.get("media", [])
            
            # Add hashtags if provided
            hashtags = content.get("hashtags", [])
            if hashtags:
                hashtag_text = " " + " ".join(f"#{tag.lstrip('#')}" for tag in hashtags)
                text += hashtag_text
            
            # Bluesky post structure
            post_data = {
                "repo": self.did,
                "collection": "app.bsky.feed.post",
                "record": {
                    "text": text,
                    "createdAt": datetime.utcnow().isoformat() + "Z",
                    "$type": "app.bsky.feed.post"
                }
            }
            
            # Handle media uploads if present
            if media_files:
                embed_images = await self._upload_media(media_files)
                if embed_images:
                    post_data["record"]["embed"] = {
                        "$type": "app.bsky.embed.images",
                        "images": embed_images
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
                            "url": f"{self.base_url}/profile/{self.identifier}/post/{post_id}",
                            "platform": "bluesky",
                            "status": "success"
                        }
                    else:
                        error_text = await response.text()
                        raise Exception(f"Post failed: {response.status} - {error_text}")
                        
        except Exception as e:
            return {
                "error": str(e),
                "platform": "bluesky",
                "status": "error"
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
    
    def validate_content(self, content: Dict[str, Any]) -> List[str]:
        """Validate content for Bluesky."""
        issues = super().validate_content(content)
        
        text = content.get('text', '')
        if len(text) > 300:
            issues.append("Text exceeds Bluesky's 300 character limit")
        
        media = content.get('media', [])
        if len(media) > 4:
            issues.append("Bluesky supports maximum 4 images per post")
        
        return issues