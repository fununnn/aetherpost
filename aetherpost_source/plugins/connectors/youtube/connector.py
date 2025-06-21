"""YouTube connector implementation."""

import asyncio
import os
import json
import tempfile
from typing import Dict, Any, Optional
import logging

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

from ...base import BaseConnector

logger = logging.getLogger(__name__)


class YouTubeConnector(BaseConnector):
    """YouTube connector for video promotion."""
    
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
    
    def __init__(self, credentials: Dict[str, str]):
        super().__init__(credentials)
        
        if not GOOGLE_API_AVAILABLE:
            raise ImportError("Google API client library is required for YouTube connector. Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        
        self.client_id = credentials.get('client_id')
        self.client_secret = credentials.get('client_secret')
        self.token_file = credentials.get('token_file', 'youtube_token.json')
        self.credentials_file = credentials.get('credentials_file', 'youtube_credentials.json')
        self.youtube = None
        self.creds = None
    
    @property
    def name(self) -> str:
        """Connector name."""
        return "youtube"
    
    @property
    def supported_media_types(self) -> list:
        """Supported media types."""
        return ["video/mp4", "video/mpeg", "video/avi", "video/mov"]
    
    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with YouTube API using OAuth2."""
        try:
            logger.info("Authenticating with YouTube API")
            
            # Load existing credentials
            if os.path.exists(self.token_file):
                self.creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
            
            # If there are no valid credentials available, let the user log in
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    # Check if credentials file exists
                    if not os.path.exists(self.credentials_file):
                        logger.error(f"YouTube credentials file not found: {self.credentials_file}")
                        logger.info("Please download OAuth2 credentials from Google Cloud Console")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES)
                    self.creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                with open(self.token_file, 'w') as token:
                    token.write(self.creds.to_json())
            
            # Build the YouTube API service
            self.youtube = build('youtube', 'v3', credentials=self.creds)
            
            # Test the connection
            request = self.youtube.channels().list(part="snippet", mine=True)
            response = request.execute()
            
            if response.get('items'):
                channel_name = response['items'][0]['snippet']['title']
                logger.info(f"Successfully authenticated as YouTube channel: {channel_name}")
                return True
            else:
                logger.error("No YouTube channel found for authenticated user")
                return False
                
        except Exception as e:
            logger.error(f"YouTube authentication failed: {e}")
            return False
    
    async def post(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Post to YouTube - requires video file."""
        try:
            if not self.youtube:
                raise Exception("YouTube client not authenticated")
            
            text_content = content.get('text', '')
            video_file = content.get('video_file')
            video_url = content.get('video_url')
            
            # Handle video source
            if video_file:
                video_path = video_file
            elif video_url:
                # Download video from URL
                video_path = await self._download_video(video_url)
            else:
                # Generate simple video from text
                video_path = await self._generate_simple_video(text_content)
            
            # Upload to YouTube
            result = await self._upload_video(video_path, text_content)
            
            # Clean up temporary file
            if video_path != video_file and os.path.exists(video_path):
                os.remove(video_path)
            
            return {
                'status': 'published',
                'platform': 'youtube',
                'post_id': result.get('video_id'),
                'url': f"https://youtube.com/watch?v={result.get('video_id')}",
                'type': 'video'
            }
            
        except Exception as e:
            logger.error(f"YouTube post failed: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def _generate_simple_video(self, text: str) -> str:
        """Generate a simple video from text using basic tools."""
        try:
            # For now, create a placeholder video file
            # In production, this could integrate with video generation services
            temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            temp_file.close()
            
            # Create a minimal video file (placeholder)
            # This would normally use ffmpeg or similar to create actual video
            logger.info(f"Generated placeholder video for text: {text[:50]}...")
            
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Failed to generate video: {e}")
            raise
    
    async def _download_video(self, video_url: str) -> str:
        """Download video from URL."""
        try:
            import urllib.request
            
            temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            temp_file.close()
            
            urllib.request.urlretrieve(video_url, temp_file.name)
            logger.info(f"Downloaded video from {video_url}")
            
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Failed to download video: {e}")
            raise
    
    async def _upload_video(self, video_path: str, description: str) -> Dict[str, Any]:
        """Upload video to YouTube."""
        try:
            if not self.youtube:
                raise Exception("YouTube client not authenticated")
            
            title = description[:60] + "..." if len(description) > 60 else description
            
            # Prepare video metadata
            body = {
                'snippet': {
                    'title': title,
                    'description': description + "\n\n#AetherPost #AutomatedPosting",
                    'tags': ['automation', 'social media', 'tech'],
                    'categoryId': '28',  # Science & Technology
                    'defaultLanguage': 'en'
                },
                'status': {
                    'privacyStatus': 'public',
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # Create media upload object
            media = MediaFileUpload(
                video_path, 
                chunksize=-1, 
                resumable=True,
                mimetype='video/mp4'
            )
            
            # Execute the upload
            insert_request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            response = None
            while response is None:
                status, response = insert_request.next_chunk()
                if status:
                    logger.info(f"Upload progress: {int(status.progress() * 100)}%")
            
            if 'id' in response:
                video_id = response['id']
                logger.info(f"Successfully uploaded video: {video_id}")
                return {
                    'video_id': video_id,
                    'upload_status': 'success',
                    'url': f"https://youtube.com/watch?v={video_id}"
                }
            else:
                raise Exception(f"Upload failed: {response}")
                
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            return {
                'upload_status': 'failed',
                'error': f"YouTube API error: {e}"
            }
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return {
                'upload_status': 'failed',
                'error': str(e)
            }
    
    async def get_video_analytics(self, video_id: str) -> Dict[str, Any]:
        """Get analytics for a specific video."""
        try:
            if not self.youtube:
                raise Exception("YouTube client not authenticated")
            
            # Get video statistics
            request = self.youtube.videos().list(
                part="statistics,snippet",
                id=video_id
            )
            response = request.execute()
            
            if not response.get('items'):
                return {
                    'video_id': video_id,
                    'error': 'Video not found',
                    'status': 'failed'
                }
            
            video = response['items'][0]
            stats = video.get('statistics', {})
            snippet = video.get('snippet', {})
            
            return {
                'video_id': video_id,
                'title': snippet.get('title'),
                'published_at': snippet.get('publishedAt'),
                'views': int(stats.get('viewCount', 0)),
                'likes': int(stats.get('likeCount', 0)),
                'comments': int(stats.get('commentCount', 0)),
                'duration': snippet.get('duration'),
                'url': f"https://youtube.com/watch?v={video_id}",
                'status': 'success'
            }
            
        except HttpError as e:
            logger.error(f"Failed to get analytics for video {video_id}: {e}")
            return {
                'video_id': video_id,
                'error': str(e),
                'status': 'failed'
            }
        except Exception as e:
            logger.error(f"Unexpected error getting analytics: {e}")
            return {
                'video_id': video_id,
                'error': str(e),
                'status': 'failed'
            }
    
    async def get_channel_analytics(self) -> Dict[str, Any]:
        """Get channel analytics."""
        try:
            if not self.youtube:
                raise Exception("YouTube client not authenticated")
            
            # Get channel info
            request = self.youtube.channels().list(
                part="statistics,snippet",
                mine=True
            )
            response = request.execute()
            
            if not response.get('items'):
                return {
                    'error': 'Channel not found',
                    'status': 'failed'
                }
            
            channel = response['items'][0]
            stats = channel.get('statistics', {})
            snippet = channel.get('snippet', {})
            
            return {
                'channel_name': snippet.get('title'),
                'subscribers': int(stats.get('subscriberCount', 0)),
                'total_views': int(stats.get('viewCount', 0)),
                'video_count': int(stats.get('videoCount', 0)),
                'created_at': snippet.get('publishedAt'),
                'status': 'success'
            }
            
        except HttpError as e:
            logger.error(f"Failed to get channel analytics: {e}")
            return {
                'error': str(e),
                'status': 'failed'
            }
        except Exception as e:
            logger.error(f"Unexpected error getting channel analytics: {e}")
            return {
                'error': str(e),
                'status': 'failed'
            }