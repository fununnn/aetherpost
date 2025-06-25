"""Twitter API platform implementation."""

import asyncio
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

try:
    import tweepy
except ImportError:
    tweepy = None

from ..core.base_platform import BasePlatform, PlatformResult, Content, Profile, ContentType, PlatformCapability, MediaFile
from ..core.authentication.api_key_authenticator import TwitterApiKeyAuthenticator
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


class TwitterPlatform(BasePlatform):
    """Twitter API platform connector."""
    
    def __init__(
        self,
        credentials: Dict[str, str],
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        if tweepy is None:
            raise ImportError("tweepy is required for Twitter connector. Install with: pip install tweepy")
        
        super().__init__(credentials, config, **kwargs)
        
        # Twitter API credentials
        self.api_key = credentials.get("api_key")
        self.api_secret = credentials.get("api_secret")
        self.access_token = credentials.get("access_token")
        self.access_token_secret = credentials.get("access_token_secret")
        self.bearer_token = credentials.get("bearer_token")
        
        # Twitter clients
        self.client = None  # API v2 client
        self.api = None     # API v1.1 for media upload
        
        self._setup_clients()
    
    # Required property implementations
    @property
    def platform_name(self) -> str:
        """Platform identifier."""
        return "twitter"
    
    @property
    def platform_display_name(self) -> str:
        """Human-readable platform name."""
        return "Twitter"
    
    @property
    def supported_content_types(self) -> List[ContentType]:
        """Supported content types for Twitter."""
        return [
            ContentType.TEXT,
            ContentType.IMAGE,
            ContentType.VIDEO,
            ContentType.THREAD
        ]
    
    @property
    def supported_media_types(self) -> List[str]:
        """Supported media MIME types."""
        return [
            "image/jpeg",
            "image/png",
            "image/gif",
            "video/mp4"
        ]
    
    @property
    def platform_capabilities(self) -> List[PlatformCapability]:
        """Platform capabilities."""
        return [
            PlatformCapability.POSTING,
            PlatformCapability.MEDIA_UPLOAD,
            PlatformCapability.PROFILE_MANAGEMENT,
            PlatformCapability.ANALYTICS,
            PlatformCapability.THREADS
        ]
    
    @property
    def character_limit(self) -> int:
        """Character limit for Twitter posts."""
        return 280
    
    # Required method implementations
    def _setup_authenticator(self):
        """Setup Twitter authenticator."""
        self.authenticator = TwitterApiKeyAuthenticator(
            credentials=self.credentials,
            platform=self.platform_name,
            base_url="https://api.twitter.com"
        )
    
    def _setup_clients(self):
        """Setup Twitter API clients."""
        try:
            # Only setup clients if we have credentials
            if self.api_key and self.api_secret:
                # Twitter API v2 client
                self.client = tweepy.Client(
                    bearer_token=self.bearer_token,
                    consumer_key=self.api_key,
                    consumer_secret=self.api_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_token_secret,
                    wait_on_rate_limit=True
                )
                
                # Twitter API v1.1 for media upload
                auth = tweepy.OAuth1UserHandler(
                    self.api_key,
                    self.api_secret,
                    self.access_token,
                    self.access_token_secret
                )
                self.api = tweepy.API(auth, wait_on_rate_limit=True)
        
        except Exception as e:
            # Only raise error if credentials were provided
            if self.api_key or self.api_secret:
                raise ValueError(f"Failed to setup Twitter client: {e}")
    
    async def authenticate(self) -> bool:
        """Test authentication with Twitter API."""
        try:
            # Test authentication by getting user info
            me = self.client.get_me()
            if me.data:
                logger.info(f"Successfully authenticated Twitter account: @{me.data.username}")
                self._authenticated = True
                return True
            else:
                return False
        
        except Exception as e:
            logger.error(f"Twitter authentication failed: {e}")
            return False
    
    async def _post_content_impl(self, content: Content) -> PlatformResult:
        """Post content to Twitter."""
        try:
            # Handle thread posting
            if content.content_type == ContentType.THREAD and content.thread_posts:
                return await self._post_thread(content.thread_posts, content.media)
            
            # Prepare tweet text
            tweet_text = content.text
            
            # Add hashtags to text if provided
            if content.hashtags:
                formatted_hashtags = []
                for tag in content.hashtags:
                    if isinstance(tag, str):
                        if not tag.startswith('#'):
                            tag = f'#{tag}'
                        formatted_hashtags.append(tag)
                
                if formatted_hashtags:
                    hashtag_text = ' ' + ' '.join(formatted_hashtags)
                    if len(tweet_text + hashtag_text) <= 280:
                        tweet_text += hashtag_text
                    else:
                        # Truncate text to fit hashtags
                        available_space = 280 - len(hashtag_text)
                        if available_space > 20:
                            tweet_text = tweet_text[:available_space-3] + "..." + hashtag_text
            
            # Upload media if provided
            media_ids = []
            if content.media:
                media_ids = await self._upload_media(content.media)
            
            # Create tweet
            tweet_params = {"text": tweet_text}
            if media_ids:
                tweet_params["media_ids"] = media_ids
            
            # Use run_in_executor for synchronous tweepy call
            tweet = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.client.create_tweet(**tweet_params)
            )
            
            if tweet.data:
                post_id = str(tweet.data["id"])
                return PlatformResult(
                    success=True,
                    platform=self.platform_name,
                    action="post_content",
                    post_id=post_id,
                    post_url=f"https://twitter.com/user/status/{post_id}",
                    created_at=datetime.utcnow()
                )
            else:
                return PlatformResult(
                    success=False,
                    platform=self.platform_name,
                    action="post_content",
                    error_message="Tweet creation failed"
                )
        
        except Exception as e:
            logger.error(f"Twitter post error: {e}")
            return PlatformResult(
                success=False,
                platform=self.platform_name,
                action="post_content",
                error_message=str(e)
            )
    
    async def _update_profile_impl(self, profile: Profile) -> PlatformResult:
        """Update Twitter profile."""
        try:
            # Prepare profile updates
            updates = {}
            
            if profile.display_name:
                updates['name'] = profile.display_name
            
            if profile.bio:
                updates['description'] = profile.bio
            
            if profile.website_url:
                updates['url'] = profile.website_url
            
            if profile.location:
                updates['location'] = profile.location
            
            # Update profile using API v1.1 (which has update_profile method)
            if updates:
                await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self.api.update_profile(**updates)
                )
            
            # Update profile image if provided
            if profile.avatar_path and os.path.exists(profile.avatar_path):
                await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self.api.update_profile_image(profile.avatar_path)
                )
            
            # Update banner if provided
            if profile.cover_path and os.path.exists(profile.cover_path):
                await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self.api.update_profile_banner(profile.cover_path)
                )
            
            return PlatformResult(
                success=True,
                platform=self.platform_name,
                action="update_profile",
                profile_updated=True
            )
        
        except Exception as e:
            logger.error(f"Twitter profile update error: {e}")
            return PlatformResult(
                success=False,
                platform=self.platform_name,
                action="update_profile",
                error_message=str(e)
            )
    
    async def _delete_post_impl(self, post_id: str) -> PlatformResult:
        """Delete a tweet."""
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.client.delete_tweet(post_id)
            )
            
            return PlatformResult(
                success=result.data.get('deleted', False) if result.data else False,
                platform=self.platform_name,
                action="delete_post",
                post_id=post_id
            )
        
        except Exception as e:
            logger.error(f"Twitter delete error: {e}")
            return PlatformResult(
                success=False,
                platform=self.platform_name,
                action="delete_post",
                post_id=post_id,
                error_message=str(e)
            )
    
    # Helper methods
    async def _upload_media(self, media_files: List[MediaFile]) -> List[str]:
        """Upload media files and return media IDs."""
        media_ids = []
        
        for media_file in media_files:
            try:
                if isinstance(media_file.file_path, str) and os.path.exists(media_file.file_path):
                    # Use run_in_executor for synchronous API call
                    media = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: self.api.media_upload(media_file.file_path)
                    )
                    media_ids.append(media.media_id)
                else:
                    logger.warning(f"Media path does not exist: {media_file.file_path}")
            except Exception as e:
                logger.error(f"Failed to upload media {media_file.file_path}: {e}")
                continue
        
        return media_ids
    
    async def _post_thread(self, thread_posts: List[str], media_files: Optional[List[MediaFile]] = None) -> PlatformResult:
        """Post a thread to Twitter."""
        try:
            thread_results = []
            previous_tweet_id = None
            
            # Upload media for first tweet if provided
            media_ids = []
            if media_files:
                media_ids = await self._upload_media(media_files)
            
            for i, post_text in enumerate(thread_posts):
                # Prepare tweet parameters
                tweet_params = {"text": post_text}
                
                # Add media to first tweet only
                if i == 0 and media_ids:
                    tweet_params["media_ids"] = media_ids
                
                # Add reply reference for subsequent tweets
                if previous_tweet_id:
                    tweet_params["in_reply_to_tweet_id"] = previous_tweet_id
                
                # Create tweet
                tweet = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self.client.create_tweet(**tweet_params)
                )
                
                if tweet.data:
                    tweet_id = str(tweet.data["id"])
                    thread_results.append({
                        "post_id": tweet_id,
                        "url": f"https://twitter.com/user/status/{tweet_id}",
                        "thread_position": i + 1
                    })
                    previous_tweet_id = tweet_id
                    
                    # Small delay between tweets
                    await asyncio.sleep(1)
                else:
                    logger.error(f"Thread tweet {i+1} failed")
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
            logger.error(f"Twitter thread posting failed: {e}")
            return PlatformResult(
                success=False,
                platform=self.platform_name,
                action="post_thread",
                error_message=str(e)
            )
    
    async def _get_analytics_impl(self, post_id: Optional[str], timeframe: Optional[str]) -> Dict[str, Any]:
        """Get analytics data for tweets."""
        try:
            if post_id:
                # Get specific tweet metrics
                tweet = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self.client.get_tweet(
                        post_id, 
                        tweet_fields=['public_metrics', 'created_at']
                    )
                )
                
                if tweet.data and tweet.data.public_metrics:
                    metrics = tweet.data.public_metrics
                    return {
                        'platform': self.platform_name,
                        'post_id': post_id,
                        'metrics': {
                            'retweets': metrics.get('retweet_count', 0),
                            'likes': metrics.get('like_count', 0),
                            'replies': metrics.get('reply_count', 0),
                            'quotes': metrics.get('quote_count', 0),
                            'impressions': metrics.get('impression_count', 0)
                        },
                        'created_at': tweet.data.created_at.isoformat() if tweet.data.created_at else None
                    }
            else:
                # Get user metrics
                me = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self.client.get_me(user_fields=['public_metrics'])
                )
                
                if me.data and me.data.public_metrics:
                    metrics = me.data.public_metrics
                    return {
                        'platform': self.platform_name,
                        'user_metrics': {
                            'followers': metrics.get('followers_count', 0),
                            'following': metrics.get('following_count', 0),
                            'tweets': metrics.get('tweet_count', 0),
                            'listed': metrics.get('listed_count', 0)
                        }
                    }
            
            return {'error': 'No analytics data available', 'platform': self.platform_name}
        
        except Exception as e:
            logger.error(f"Twitter analytics error: {e}")
            return {'error': str(e), 'platform': self.platform_name}
    
    # Platform-specific validation
    async def _validate_content_platform_specific(self, content: Content) -> Dict[str, Any]:
        """Twitter-specific content validation."""
        errors = []
        warnings = []
        
        # Character limit check (more precise for Twitter)
        total_length = len(content.text)
        if content.hashtags:
            hashtag_length = sum(len(f"#{tag.lstrip('#')} ") for tag in content.hashtags)
            total_length += hashtag_length
        
        if total_length > 280:
            errors.append(f"Tweet exceeds Twitter's 280 character limit: {total_length} characters")
        
        # Media count check
        if len(content.media) > 4:
            errors.append("Twitter supports maximum 4 media files per tweet")
        
        # Thread validation
        if content.content_type == ContentType.THREAD:
            if not content.thread_posts:
                errors.append("Thread type requires thread_posts array")
            elif len(content.thread_posts) > 25:
                warnings.append("Very long thread (over 25 tweets) may have reduced visibility")
            
            for i, post_text in enumerate(content.thread_posts):
                if len(post_text) > 280:
                    errors.append(f"Thread tweet {i+1} exceeds 280 character limit")
        
        # Video file size check
        for media in content.media:
            if media.media_type.startswith('video/'):
                if media.file_size and media.file_size > 512 * 1024 * 1024:  # 512MB
                    errors.append(f"Video file {media.file_path} exceeds Twitter's 512MB limit")
                    
                if media.duration and media.duration > 140:  # 140 seconds
                    errors.append(f"Video duration {media.duration}s exceeds Twitter's 140s limit")
        
        return {
            'errors': errors,
            'warnings': warnings
        }
    
    def get_twitter_credentials(self) -> Dict[str, str]:
        """Get Twitter-specific credentials for external use."""
        return {
            'api_key': self.api_key,
            'api_secret': self.api_secret,
            'access_token': self.access_token,
            'access_token_secret': self.access_token_secret,
            'bearer_token': self.bearer_token
        }