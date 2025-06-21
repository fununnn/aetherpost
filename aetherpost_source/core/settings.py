"""Configuration management for AetherPost."""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class Config:
    """Configuration management class."""
    
    def __init__(self):
        self.config = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from environment variables and .env files."""
        # Load from .env.aetherpost if it exists
        env_file = Path('.env.aetherpost')
        if env_file.exists():
            self._load_env_file(env_file)
        
        # Also check for .env file
        env_file_default = Path('.env')
        if env_file_default.exists():
            self._load_env_file(env_file_default)
        
        # Override with actual environment variables
        self._load_environment_vars()
    
    def _load_env_file(self, file_path: Path):
        """Load environment variables from a file."""
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key and value:
                            self.config[key] = value
            logger.info(f"Loaded configuration from {file_path}")
        except Exception as e:
            logger.warning(f"Could not load {file_path}: {e}")
    
    def _load_environment_vars(self):
        """Load configuration from environment variables."""
        # Define all possible configuration keys
        config_keys = [
            # Social Media APIs
            'TWITTER_API_KEY', 'TWITTER_API_SECRET', 'TWITTER_ACCESS_TOKEN',
            'TWITTER_ACCESS_TOKEN_SECRET', 'TWITTER_BEARER_TOKEN',
            'INSTAGRAM_APP_ID', 'INSTAGRAM_APP_SECRET', 'INSTAGRAM_ACCESS_TOKEN',
            'TIKTOK_CLIENT_KEY', 'TIKTOK_CLIENT_SECRET', 'TIKTOK_ACCESS_TOKEN',
            'YOUTUBE_API_KEY', 'YOUTUBE_CLIENT_ID', 'YOUTUBE_CLIENT_SECRET', 'YOUTUBE_CHANNEL_ID',
            'REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET', 'REDDIT_USERNAME', 'REDDIT_PASSWORD',
            
            # AI Services
            'OPENAI_API_KEY', 'ELEVENLABS_API_KEY', 'SYNTHESIA_API_KEY',
            'RUNWAY_API_KEY', 'DID_API_KEY', 'DALLE_API_KEY', 'MIDJOURNEY_API_KEY',
            
            # Cloud & Infrastructure
            'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION',
            'REDIS_URL',
            
            # Optional Services
            'ZAPIER_API_KEY', 'BUFFER_ACCESS_TOKEN', 'CANVA_API_KEY'
        ]
        
        # Add all environment variables that match our patterns
        for key, value in os.environ.items():
            if any(key.startswith(prefix) for prefix in ['TWITTER_', 'INSTAGRAM_', 'TIKTOK_', 'YOUTUBE_', 'REDDIT_', 'OPENAI_', 'ELEVENLABS_', 'SYNTHESIA_', 'RUNWAY_', 'DID_', 'DALLE_', 'MIDJOURNEY_', 'AWS_', 'REDIS_', 'ZAPIER_', 'BUFFER_', 'CANVA_', 'TEST_']):
                self.config[key] = value
        
        # Also check specific config keys
        for key in config_keys:
            value = os.getenv(key)
            if value:
                self.config[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)
    
    def get_platform_credentials(self, platform: str) -> Dict[str, str]:
        """Get credentials for a specific platform."""
        platform_configs = {
            'twitter': {
                'api_key': self.get('TWITTER_API_KEY'),
                'api_secret': self.get('TWITTER_API_SECRET'),
                'access_token': self.get('TWITTER_ACCESS_TOKEN'),
                'access_token_secret': self.get('TWITTER_ACCESS_TOKEN_SECRET'),
                'bearer_token': self.get('TWITTER_BEARER_TOKEN')
            },
            'instagram': {
                'app_id': self.get('INSTAGRAM_APP_ID'),
                'app_secret': self.get('INSTAGRAM_APP_SECRET'),
                'access_token': self.get('INSTAGRAM_ACCESS_TOKEN')
            },
            'tiktok': {
                'client_key': self.get('TIKTOK_CLIENT_KEY'),
                'client_secret': self.get('TIKTOK_CLIENT_SECRET'),
                'access_token': self.get('TIKTOK_ACCESS_TOKEN')
            },
            'youtube': {
                'api_key': self.get('YOUTUBE_API_KEY'),
                'client_id': self.get('YOUTUBE_CLIENT_ID'),
                'client_secret': self.get('YOUTUBE_CLIENT_SECRET'),
                'channel_id': self.get('YOUTUBE_CHANNEL_ID')
            },
            'reddit': {
                'client_id': self.get('REDDIT_CLIENT_ID'),
                'client_secret': self.get('REDDIT_CLIENT_SECRET'),
                'username': self.get('REDDIT_USERNAME'),
                'password': self.get('REDDIT_PASSWORD')
            }
        }
        
        return {k: v for k, v in platform_configs.get(platform, {}).items() if v is not None}
    
    def get_ai_credentials(self, service: str) -> Optional[str]:
        """Get AI service credentials."""
        ai_services = {
            'openai': 'OPENAI_API_KEY',
            'elevenlabs': 'ELEVENLABS_API_KEY',
            'synthesia': 'SYNTHESIA_API_KEY',
            'runway': 'RUNWAY_API_KEY',
            'did': 'DID_API_KEY',
            'dalle': 'DALLE_API_KEY',
            'midjourney': 'MIDJOURNEY_API_KEY'
        }
        
        key = ai_services.get(service)
        return self.get(key) if key else None
    
    def verify_required_config(self, required_keys: list) -> Dict[str, bool]:
        """Verify that required configuration keys are present."""
        verification = {}
        for key in required_keys:
            verification[key] = bool(self.get(key))
        return verification
    
    def is_platform_configured(self, platform: str) -> bool:
        """Check if a platform is properly configured."""
        creds = self.get_platform_credentials(platform)
        
        # Minimum required credentials per platform
        required_creds = {
            'twitter': ['api_key', 'api_secret'],
            'instagram': ['app_id', 'app_secret'],
            'tiktok': ['client_key', 'client_secret'],
            'youtube': ['api_key'],
            'reddit': ['client_id', 'client_secret']
        }
        
        if platform not in required_creds:
            return False
        
        for req_key in required_creds[platform]:
            if not creds.get(req_key):
                return False
        
        return True
    
    def get_configured_platforms(self) -> list:
        """Get list of properly configured platforms."""
        platforms = ['twitter', 'instagram', 'tiktok', 'youtube', 'reddit']
        return [p for p in platforms if self.is_platform_configured(p)]


# Global configuration instance
config = Config()