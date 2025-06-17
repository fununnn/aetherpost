"""Connector factory for creating platform connectors with proper configuration."""

import logging
from typing import Dict, Any, Optional, Type
from .settings import config

logger = logging.getLogger(__name__)


class ConnectorFactory:
    """Factory for creating platform connectors with proper configuration."""
    
    def __init__(self):
        self._connectors = {}
        self._register_connectors()
    
    def _register_connectors(self):
        """Register all available connectors."""
        try:
            from ..plugins.connectors.twitter.connector import TwitterConnector
            self._connectors['twitter'] = TwitterConnector
        except ImportError as e:
            logger.warning(f"Twitter connector not available: {e}")
        
        try:
            from ..plugins.connectors.instagram.connector import InstagramConnector
            self._connectors['instagram'] = InstagramConnector
        except ImportError as e:
            logger.warning(f"Instagram connector not available: {e}")
        
        try:
            from ..plugins.connectors.tiktok.connector import TikTokConnector
            self._connectors['tiktok'] = TikTokConnector
        except ImportError as e:
            logger.warning(f"TikTok connector not available: {e}")
        
        try:
            from ..plugins.connectors.youtube.connector import YouTubeConnector
            self._connectors['youtube'] = YouTubeConnector
        except ImportError as e:
            logger.warning(f"YouTube connector not available: {e}")
        
        try:
            from ..plugins.connectors.reddit.connector import RedditConnector
            self._connectors['reddit'] = RedditConnector
        except ImportError as e:
            logger.warning(f"Reddit connector not available: {e}")
    
    def create_connector(self, platform: str) -> Optional[Any]:
        """Create a connector for the specified platform."""
        if platform not in self._connectors:
            logger.error(f"Connector not available for platform: {platform}")
            return None
        
        # Get credentials from config
        credentials = config.get_platform_credentials(platform)
        
        if not credentials:
            logger.error(f"No credentials configured for platform: {platform}")
            return None
        
        # Check if platform is properly configured
        if not config.is_platform_configured(platform):
            logger.error(f"Platform {platform} is not properly configured")
            return None
        
        try:
            connector_class = self._connectors[platform]
            connector = connector_class(credentials)
            logger.info(f"Created connector for {platform}")
            return connector
        except Exception as e:
            logger.error(f"Failed to create connector for {platform}: {e}")
            return None
    
    def get_available_platforms(self) -> list:
        """Get list of available platforms."""
        return list(self._connectors.keys())
    
    def get_configured_platforms(self) -> list:
        """Get list of properly configured platforms."""
        return config.get_configured_platforms()
    
    def create_all_connectors(self) -> Dict[str, Any]:
        """Create all available and configured connectors."""
        connectors = {}
        configured_platforms = self.get_configured_platforms()
        
        for platform in configured_platforms:
            connector = self.create_connector(platform)
            if connector:
                connectors[platform] = connector
        
        return connectors


# Global connector factory instance
connector_factory = ConnectorFactory()