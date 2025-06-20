"""Instagram Graph API connector implementation."""

import asyncio
import aiohttp
import os
import json
import tempfile
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from PIL import Image, ImageDraw, ImageFont

from ...base import BaseConnector

logger = logging.getLogger(__name__)


class InstagramConnector(BaseConnector):
    """Instagram Business API connector for professional social media automation."""
    
    def __init__(self, credentials: Dict[str, str]):
        super().__init__(credentials)
        self.access_token = credentials.get('access_token')
        self.business_account_id = credentials.get('business_account_id')
        self.base_url = "https://graph.facebook.com/v18.0"
        
        if not self.access_token or not self.business_account_id:
            raise ValueError("Instagram requires access_token and business_account_id")
    
    @property
    def name(self) -> str:
        """Connector name."""
        return "instagram"
    
    @property
    def supported_media_types(self) -> List[str]:
        """Supported media types."""
        return ["image/jpeg", "image/png", "video/mp4", "video/mov"]
    
    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with Instagram Graph API."""
        try:
            logger.info("Authenticating with Instagram Graph API")
            
            # Test authentication by getting account info
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{self.business_account_id}"
                params = {
                    "fields": "account_type,username,followers_count",
                    "access_token": self.access_token
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        username = data.get('username', 'Unknown')
                        account_type = data.get('account_type', 'Unknown')
                        followers = data.get('followers_count', 0)
                        
                        if account_type in ['BUSINESS', 'CREATOR']:
                            logger.info(f"Successfully authenticated Instagram Business account: @{username} ({followers} followers)")
                            return True
                        else:
                            logger.error(f"Account type '{account_type}' is not supported. Business or Creator account required.")
                            return False
                    else:
                        error_text = await response.text()
                        logger.error(f"Instagram authentication failed: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Instagram authentication error: {e}")
            return False
    
    async def post(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Post content to Instagram using Graph API."""
        try:
            text_content = content.get('text', '')
            media_files = content.get('media', [])
            media_type = content.get('type', 'photo')
            
            # Generate hashtags and optimize caption
            hashtags = self._generate_instagram_hashtags(text_content)
            caption = self._create_optimized_caption(text_content, hashtags)
            
            # Handle different content types
            if media_files:
                if len(media_files) > 1:
                    # Carousel post
                    return await self._post_carousel(media_files, caption)
                elif media_files[0].lower().endswith(('.mp4', '.mov')):
                    # Video/Reel
                    return await self._post_video(media_files[0], caption)
                else:
                    # Single photo
                    return await self._post_photo(media_files[0], caption)
            else:
                # Text-only post with generated image
                return await self._post_text_as_image(text_content, caption)
                
        except Exception as e:
            logger.error(f"Instagram post failed: {e}")
            return {
                'status': 'failed',
                'platform': 'instagram',
                'error': str(e)
            }
    
    async def _post_photo(self, image_path: str, caption: str) -> Dict[str, Any]:
        """Post single photo to Instagram."""
        try:
            # Step 1: Create media container
            container_id = await self._create_media_container(
                media_type="IMAGE",
                media_url=image_path,
                caption=caption
            )
            
            if not container_id:
                raise Exception("Failed to create media container")
            
            # Step 2: Publish the container
            post_id = await self._publish_media(container_id)
            
            return {
                'status': 'published',
                'platform': 'instagram',
                'post_id': post_id,
                'url': f"https://instagram.com/p/{post_id}",
                'type': 'photo',
                'created_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to post photo: {e}")
            raise
    
    async def _post_video(self, video_path: str, caption: str) -> Dict[str, Any]:
        """Post video/reel to Instagram."""
        try:
            # Step 1: Create media container for video
            container_id = await self._create_media_container(
                media_type="VIDEO",
                media_url=video_path,
                caption=caption,
                is_reel=True
            )
            
            if not container_id:
                raise Exception("Failed to create video container")
            
            # Step 2: Wait for video processing (Instagram requirement)
            await self._wait_for_video_processing(container_id)
            
            # Step 3: Publish the container
            post_id = await self._publish_media(container_id)
            
            return {
                'status': 'published',
                'platform': 'instagram',
                'post_id': post_id,
                'url': f"https://instagram.com/reel/{post_id}",
                'type': 'video',
                'created_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to post video: {e}")
            raise
    
    async def _post_carousel(self, media_paths: List[str], caption: str) -> Dict[str, Any]:
        """Post carousel to Instagram."""
        try:
            # Step 1: Create media containers for each item
            container_ids = []
            
            for media_path in media_paths[:10]:  # Instagram limit: 10 items
                media_type = "VIDEO" if media_path.lower().endswith(('.mp4', '.mov')) else "IMAGE"
                
                container_id = await self._create_media_container(
                    media_type=media_type,
                    media_url=media_path,
                    is_carousel_item=True
                )
                
                if container_id:
                    container_ids.append(container_id)
            
            if not container_ids:
                raise Exception("Failed to create carousel containers")
            
            # Step 2: Create carousel container
            carousel_container_id = await self._create_carousel_container(container_ids, caption)
            
            if not carousel_container_id:
                raise Exception("Failed to create carousel container")
            
            # Step 3: Publish the carousel
            post_id = await self._publish_media(carousel_container_id)
            
            return {
                'status': 'published',
                'platform': 'instagram',
                'post_id': post_id,
                'url': f"https://instagram.com/p/{post_id}",
                'type': 'carousel',
                'item_count': len(container_ids),
                'created_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to post carousel: {e}")
            raise
    
    async def _post_text_as_image(self, text_content: str, caption: str) -> Dict[str, Any]:
        """Create and post text as image for text-only content."""
        try:
            # Generate simple text image
            image_path = await self._generate_text_image(text_content)
            
            # Post as photo
            return await self._post_photo(image_path, caption)
            
        except Exception as e:
            logger.error(f"Failed to post text as image: {e}")
            raise
    
    async def _create_media_container(self, media_type: str, media_url: str, 
                                    caption: str = None, is_reel: bool = False, 
                                    is_carousel_item: bool = False) -> Optional[str]:
        """Create media container using Instagram Graph API."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{self.business_account_id}/media"
                
                data = {
                    "media_type": media_type,
                    "access_token": self.access_token
                }
                
                # Handle different media types
                if media_type == "IMAGE":
                    data["image_url"] = media_url
                elif media_type == "VIDEO":
                    data["video_url"] = media_url
                    if is_reel:
                        data["media_type"] = "REELS"
                
                # Add caption only for non-carousel items
                if caption and not is_carousel_item:
                    data["caption"] = caption
                
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("id")
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to create media container: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error creating media container: {e}")
            return None
    
    async def _create_carousel_container(self, container_ids: List[str], caption: str) -> Optional[str]:
        """Create carousel container."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{self.business_account_id}/media"
                
                data = {
                    "media_type": "CAROUSEL",
                    "children": ",".join(container_ids),
                    "caption": caption,
                    "access_token": self.access_token
                }
                
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("id")
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to create carousel container: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error creating carousel container: {e}")
            return None
    
    async def _wait_for_video_processing(self, container_id: str, max_wait: int = 60) -> bool:
        """Wait for video processing to complete."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{container_id}"
                
                for attempt in range(max_wait):
                    params = {
                        "fields": "status_code",
                        "access_token": self.access_token
                    }
                    
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            result = await response.json()
                            status = result.get("status_code")
                            
                            if status == "FINISHED":
                                return True
                            elif status == "ERROR":
                                logger.error("Video processing failed")
                                return False
                            
                            # Wait 1 second before next check
                            await asyncio.sleep(1)
                        else:
                            logger.error(f"Failed to check video status: {response.status}")
                            return False
                
                logger.warning("Video processing timeout")
                return False
                
        except Exception as e:
            logger.error(f"Error waiting for video processing: {e}")
            return False
    
    async def _publish_media(self, container_id: str) -> Optional[str]:
        """Publish media container."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{self.business_account_id}/media_publish"
                
                data = {
                    "creation_id": container_id,
                    "access_token": self.access_token
                }
                
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("id")
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to publish media: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error publishing media: {e}")
            return None
    
    async def _generate_text_image(self, text: str) -> str:
        """Generate a simple text image for text-only posts."""
        try:
            # Create image
            width, height = 1080, 1080  # Instagram square format
            image = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(image)
            
            # Try to use a font, fall back to default if not available
            try:
                font = ImageFont.truetype("arial.ttf", 60)
            except OSError:
                font = ImageFont.load_default()
            
            # Add text with word wrapping
            lines = self._wrap_text(text, font, width - 100)
            y_offset = (height - len(lines) * 70) // 2
            
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                x = (width - text_width) // 2
                draw.text((x, y_offset), line, fill='black', font=font)
                y_offset += 70
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
            image.save(temp_file.name, 'JPEG', quality=90)
            temp_file.close()
            
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Failed to generate text image: {e}")
            raise
    
    def _wrap_text(self, text: str, font, max_width: int) -> List[str]:
        """Wrap text to fit within specified width."""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = font.getbbox(test_line)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)  # Single word too long
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _generate_instagram_hashtags(self, text: str) -> List[str]:
        """Generate Instagram hashtags based on content."""
        
        # Tech-related popular hashtags
        tech_hashtags = [
            '#programming', '#coding', '#developer', '#tech', '#software',
            '#webdev', '#javascript', '#python', '#react', '#nodejs',
            '#opensource', '#github', '#startup', '#innovation', '#ai',
            '#machinelearning', '#devlife', '#coder', '#codinglife'
        ]
        
        # Japanese hashtags
        jp_hashtags = [
            '#プログラミング', '#エンジニア', '#開発', '#テック', '#IT',
            '#スタートアップ', '#技術', '#コーディング', '#ウェブ開発'
        ]
        
        # General engagement hashtags
        engagement_hashtags = [
            '#instagood', '#photooftheday', '#follow', '#like4like',
            '#instadaily', '#picoftheday', '#amazing', '#awesome'
        ]
        
        # Content-based selection
        selected_hashtags = []
        text_lower = text.lower()
        
        # Tech keywords check
        tech_keywords = ['code', 'program', 'develop', 'tech', 'software', 'web', 'app']
        if any(keyword in text_lower for keyword in tech_keywords):
            selected_hashtags.extend(tech_hashtags[:10])
        
        # Add Japanese hashtags
        selected_hashtags.extend(jp_hashtags[:5])
        
        # Add engagement hashtags
        selected_hashtags.extend(engagement_hashtags[:5])
        
        # Instagram limit: 30 hashtags
        return selected_hashtags[:25]  # Keep it safe at 25
    
    def _create_optimized_caption(self, text: str, hashtags: List[str]) -> str:
        """Create optimized Instagram caption."""
        
        # Instagram caption best practices
        caption_parts = []
        
        # Main content
        caption_parts.append(text)
        
        # Add call to action
        if len(text) < 100:  # Short posts
            caption_parts.append("\\n\\n💭 What do you think? Share your thoughts!")
        
        # Add hashtags with spacing
        if hashtags:
            caption_parts.append("\\n\\n" + " ".join(hashtags))
        
        # Instagram optimization
        caption_parts.append("\\n\\n#AetherPost #AutomatedMarketing")
        
        return "".join(caption_parts)
    
    async def get_analytics(self) -> Dict[str, Any]:
        """Get Instagram account analytics."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{self.business_account_id}/insights"
                
                params = {
                    "metric": "follower_count,impressions,reach,profile_views",
                    "period": "day",
                    "access_token": self.access_token
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        insights = data.get('data', [])
                        
                        # Process insights
                        analytics = {
                            'platform': 'instagram',
                            'retrieved_at': datetime.utcnow().isoformat()
                        }
                        
                        for insight in insights:
                            metric_name = insight.get('name')
                            values = insight.get('values', [])
                            if values:
                                analytics[metric_name] = values[0].get('value', 0)
                        
                        return analytics
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get analytics: {response.status} - {error_text}")
                        return {'error': 'Failed to retrieve analytics'}
                        
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return {'error': str(e)}
    
    async def get_post_metrics(self, post_id: str) -> Dict[str, Any]:
        """Get metrics for a specific post."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{post_id}/insights"
                
                params = {
                    "metric": "impressions,reach,likes,comments,shares,saves",
                    "access_token": self.access_token
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        insights = data.get('data', [])
                        
                        # Process post metrics
                        metrics = {
                            'post_id': post_id,
                            'platform': 'instagram',
                            'retrieved_at': datetime.utcnow().isoformat()
                        }
                        
                        for insight in insights:
                            metric_name = insight.get('name')
                            values = insight.get('values', [])
                            if values:
                                metrics[metric_name] = values[0].get('value', 0)
                        
                        return metrics
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get post metrics: {response.status} - {error_text}")
                        return {'error': 'Failed to retrieve post metrics'}
                        
        except Exception as e:
            logger.error(f"Error getting post metrics: {e}")
            return {'error': str(e)}

    def validate_content(self, content: Dict[str, Any]) -> List[str]:
        """Validate content for Instagram."""
        issues = []
        
        text = content.get('text', '')
        media = content.get('media', [])
        
        # Caption length check (2200 character limit)
        if len(text) > 2000:  # Leave room for hashtags
            issues.append("Caption too long for Instagram (2000+ characters)")
        
        # Media count check
        if len(media) > 10:
            issues.append("Instagram supports maximum 10 media items per post")
        
        # Business account requirement
        if not self.business_account_id:
            issues.append("Instagram Business account required")
        
        return issues