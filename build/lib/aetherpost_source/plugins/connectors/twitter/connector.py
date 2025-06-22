"""Twitter API v2 connector implementation."""

import asyncio
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

try:
    import tweepy
except ImportError:
    tweepy = None

from ...base import SNSConnectorBase


class TwitterConnector(SNSConnectorBase):
    """Twitter API v2 connector."""
    
    def __init__(self, credentials: Dict[str, str]):
        if tweepy is None:
            raise ImportError("tweepy is required for Twitter connector. Install with: pip install tweepy")
        
        self.credentials = credentials
        self.client = None
        self.api = None
        self._setup_client()
    
    @property
    def name(self) -> str:
        return "twitter"
    
    @property
    def supported_media_types(self) -> List[str]:
        return ["image/jpeg", "image/png", "image/gif", "video/mp4"]
    
    def _setup_client(self):
        """Setup Twitter API client."""
        try:
            # Twitter API v2 client
            self.client = tweepy.Client(
                bearer_token=self.credentials.get("bearer_token"),
                consumer_key=self.credentials.get("api_key"),
                consumer_secret=self.credentials.get("api_secret"),
                access_token=self.credentials.get("access_token"),
                access_token_secret=self.credentials.get("access_token_secret"),
                wait_on_rate_limit=True
            )
            
            # Twitter API v1.1 for media upload
            auth = tweepy.OAuth1UserHandler(
                self.credentials.get("api_key"),
                self.credentials.get("api_secret"),
                self.credentials.get("access_token"),
                self.credentials.get("access_token_secret")
            )
            self.api = tweepy.API(auth, wait_on_rate_limit=True)
        
        except Exception as e:
            raise ValueError(f"Failed to setup Twitter client: {e}")
    
    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Test authentication with Twitter API."""
        try:
            # Update credentials and recreate client
            self.credentials = credentials
            self._setup_client()
            
            # Test authentication by getting user info
            me = self.client.get_me()
            return me.data is not None
        
        except Exception as e:
            print(f"Twitter authentication failed: {e}")
            return False
    
    async def post(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Post content to Twitter."""
        try:
            text = content.get("text", "")
            media_paths = content.get("media", [])
            hashtags = content.get("hashtags", [])
            
            # Add hashtags to text if provided
            if hashtags:
                # Ensure hashtags start with #
                formatted_hashtags = []
                for tag in hashtags:
                    if isinstance(tag, str):
                        if not tag.startswith('#'):
                            tag = f'#{tag}'
                        formatted_hashtags.append(tag)
                
                if formatted_hashtags:
                    # Add hashtags at the end if they don't exceed character limit
                    hashtag_text = ' ' + ' '.join(formatted_hashtags)
                    if len(text + hashtag_text) <= 280:  # Twitter character limit
                        text += hashtag_text
                    else:
                        # If adding hashtags would exceed limit, truncate text and add hashtags
                        available_space = 280 - len(hashtag_text)
                        if available_space > 20:  # Keep some reasonable text
                            text = text[:available_space-3] + "..." + hashtag_text
            
            # Validate content
            issues = self.validate_content({"text": text, "media": media_paths})
            if issues:
                return {
                    "error": f"Content validation failed: {', '.join(issues)}",
                    "status": "failed"
                }
            
            # Upload media if provided
            media_ids = []
            if media_paths:
                for media_path in media_paths:
                    try:
                        # Check if media_path is a valid file path
                        if isinstance(media_path, str) and os.path.exists(media_path):
                            # Use API v1.1 for media upload
                            media = self.api.media_upload(media_path)
                            media_ids.append(media.media_id)
                        else:
                            print(f"Media path does not exist or is not a file: {media_path}")
                    except Exception as e:
                        print(f"Failed to upload media {media_path}: {e}")
                        continue
            
            # Create tweet
            tweet_params = {"text": text}
            if media_ids:
                tweet_params["media_ids"] = media_ids
            
            tweet = self.client.create_tweet(**tweet_params)
            
            if tweet.data:
                post_id = str(tweet.data["id"])
                return {
                    "id": post_id,
                    "url": f"https://twitter.com/user/status/{post_id}",
                    "platform": "twitter",
                    "created_at": datetime.utcnow().isoformat(),
                    "status": "published"
                }
            else:
                return {
                    "error": "Tweet creation failed",
                    "status": "failed"
                }
        
        except Exception as e:
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def delete(self, post_id: str) -> bool:
        """Delete a tweet."""
        try:
            self.client.delete_tweet(post_id)
            return True
        except Exception as e:
            print(f"Failed to delete tweet {post_id}: {e}")
            return False
    
    async def get_metrics(self, post_id: str) -> Dict[str, Any]:
        """Get metrics for a tweet."""
        try:
            tweet = self.client.get_tweet(
                post_id,
                tweet_fields=["public_metrics", "created_at"]
            )
            
            if tweet.data and tweet.data.public_metrics:
                metrics = tweet.data.public_metrics
                return {
                    "likes": metrics.get("like_count", 0),
                    "retweets": metrics.get("retweet_count", 0),
                    "replies": metrics.get("reply_count", 0),
                    "quotes": metrics.get("quote_count", 0),
                    "impressions": metrics.get("impression_count", 0),
                    "retrieved_at": datetime.utcnow().isoformat()
                }
            else:
                return {"error": "Tweet not found or metrics unavailable"}
        
        except Exception as e:
            return {"error": str(e)}
    
    def validate_content(self, content: Dict[str, Any]) -> List[str]:
        """Validate content for Twitter."""
        issues = super().validate_content(content)
        
        text = content.get("text", "")
        
        # Check character limit
        if len(text) > 280:
            issues.append(f"Text exceeds Twitter's 280 character limit ({len(text)} characters)")
        
        # Check media count
        media = content.get("media", [])
        if len(media) > 4:
            issues.append("Twitter supports maximum 4 media items per tweet")
        
        return issues