"""Mastodon connector implementation."""

import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin

from ...base import SNSConnectorBase


class MastodonConnector(SNSConnectorBase):
    """Mastodon federated social media platform connector."""
    
    def __init__(self, credentials: Dict[str, str]):
        self.instance_url = credentials.get("instance_url")
        self.access_token = credentials.get("access_token")
        
        if not self.instance_url or not self.access_token:
            raise ValueError("Mastodon requires instance_url and access_token")
        
        # Ensure instance URL has proper format
        if not self.instance_url.startswith(("http://", "https://")):
            self.instance_url = f"https://{self.instance_url}"
    
    @property
    def name(self) -> str:
        return "mastodon"
    
    @property
    def supported_media_types(self) -> List[str]:
        return [
            "image/jpeg", "image/png", "image/gif", "image/webp",
            "video/mp4", "video/webm", "video/quicktime",
            "audio/mpeg", "audio/ogg", "audio/wav"
        ]
    
    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Verify authentication with Mastodon instance."""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    urljoin(self.instance_url, "/api/v1/accounts/verify_credentials"),
                    headers=headers
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            print(f"Mastodon authentication error: {e}")
            return False
    
    async def post(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Post content to Mastodon."""
        try:
            # Prepare status text
            text = content.get("text", "")
            media_files = content.get("media", [])
            
            # Add hashtags if provided
            hashtags = content.get("hashtags", [])
            if hashtags:
                hashtag_text = " " + " ".join(f"#{tag.lstrip('#')}" for tag in hashtags)
                text += hashtag_text
            
            # Upload media first if present
            media_ids = []
            if media_files:
                media_ids = await self._upload_media(media_files)
            
            # Prepare post data
            post_data = {
                "status": text,
                "visibility": "public",  # public, unlisted, private, direct
            }
            
            if media_ids:
                post_data["media_ids"] = media_ids
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    urljoin(self.instance_url, "/api/v1/statuses"),
                    json=post_data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        post_id = data.get("id")
                        post_url = data.get("url")
                        
                        return {
                            "post_id": post_id,
                            "url": post_url,
                            "platform": "mastodon",
                            "status": "success"
                        }
                    else:
                        error_text = await response.text()
                        raise Exception(f"Post failed: {response.status} - {error_text}")
                        
        except Exception as e:
            return {
                "error": str(e),
                "platform": "mastodon",
                "status": "error"
            }
    
    async def delete(self, post_id: str) -> bool:
        """Delete a post from Mastodon."""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.delete(
                    urljoin(self.instance_url, f"/api/v1/statuses/{post_id}"),
                    headers=headers
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            print(f"Error deleting Mastodon post {post_id}: {e}")
            return False
    
    async def get_metrics(self, post_id: str) -> Dict[str, Any]:
        """Get metrics for a Mastodon post."""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    urljoin(self.instance_url, f"/api/v1/statuses/{post_id}"),
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract metrics
                        favourites_count = data.get("favourites_count", 0)
                        reblogs_count = data.get("reblogs_count", 0)
                        replies_count = data.get("replies_count", 0)
                        
                        return {
                            "likes": favourites_count,
                            "boosts": reblogs_count,
                            "replies": replies_count,
                            "total_engagement": favourites_count + reblogs_count + replies_count,
                            "platform": "mastodon"
                        }
                    else:
                        return {"error": f"Failed to get metrics: {response.status}"}
                        
        except Exception as e:
            return {"error": str(e)}
    
    async def _upload_media(self, media_files: List[str]) -> List[str]:
        """Upload media files to Mastodon."""
        media_ids = []
        
        for media_file in media_files[:4]:  # Mastodon supports up to 4 attachments
            try:
                headers = {
                    "Authorization": f"Bearer {self.access_token}"
                }
                
                async with aiohttp.ClientSession() as session:
                    with open(media_file, 'rb') as f:
                        data = aiohttp.FormData()
                        data.add_field('file', f, filename=media_file)
                        
                        async with session.post(
                            urljoin(self.instance_url, "/api/v2/media"),
                            data=data,
                            headers=headers
                        ) as response:
                            if response.status == 200 or response.status == 202:
                                upload_data = await response.json()
                                media_id = upload_data.get("id")
                                
                                # Wait for processing if needed
                                if upload_data.get("url") is None:
                                    media_id = await self._wait_for_media_processing(media_id)
                                
                                if media_id:
                                    media_ids.append(media_id)
                                    
            except Exception as e:
                print(f"Failed to upload {media_file}: {e}")
                continue
        
        return media_ids
    
    async def _wait_for_media_processing(self, media_id: str, max_attempts: int = 10) -> Optional[str]:
        """Wait for media processing to complete."""
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        for attempt in range(max_attempts):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        urljoin(self.instance_url, f"/api/v1/media/{media_id}"),
                        headers=headers
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get("url"):  # Processing complete
                                return media_id
                            else:
                                await asyncio.sleep(1)  # Wait and retry
                                
            except Exception as e:
                print(f"Error checking media processing: {e}")
                break
        
        return None
    
    def validate_content(self, content: Dict[str, Any]) -> List[str]:
        """Validate content for Mastodon."""
        issues = super().validate_content(content)
        
        text = content.get('text', '')
        if len(text) > 500:
            issues.append("Text exceeds Mastodon's 500 character limit")
        
        media = content.get('media', [])
        if len(media) > 4:
            issues.append("Mastodon supports maximum 4 media attachments per post")
        
        return issues