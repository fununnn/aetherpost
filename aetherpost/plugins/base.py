"""Base classes for AetherPost plugins."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class BaseConnector(ABC):
    """Base class for all platform connectors."""
    
    def __init__(self, credentials: Dict[str, str]):
        self.credentials = credentials
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with the platform."""
        pass
    
    @abstractmethod
    async def post(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Post content to the platform."""
        pass
    
    async def delete(self, post_id: str) -> bool:
        """Delete a post from the platform."""
        return False
    
    async def get_metrics(self, post_id: str) -> Dict[str, Any]:
        """Get metrics for a specific post."""
        return {}


class SNSConnectorBase(ABC):
    """Base class for social media platform connectors."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Connector name."""
        pass
    
    @property
    @abstractmethod
    def supported_media_types(self) -> List[str]:
        """List of supported media types."""
        pass
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with the platform."""
        pass
    
    @abstractmethod
    async def post(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Post content to the platform."""
        pass
    
    @abstractmethod
    async def delete(self, post_id: str) -> bool:
        """Delete a post from the platform."""
        pass
    
    @abstractmethod
    async def get_metrics(self, post_id: str) -> Dict[str, Any]:
        """Get metrics for a specific post."""
        pass
    
    def validate_content(self, content: Dict[str, Any]) -> List[str]:
        """Validate content for this platform. Return list of issues."""
        issues = []
        
        if not content.get('text'):
            issues.append("Text content is required")
        
        return issues


class AIProviderBase(ABC):
    """Base class for AI content generation providers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass
    
    @abstractmethod
    async def generate_text(self, prompt: str, config: Dict[str, Any]) -> str:
        """Generate text content based on prompt."""
        pass


class AnalyticsProviderBase(ABC):
    """Base class for analytics and metrics providers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass
    
    @abstractmethod
    async def collect_metrics(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect metrics for a post from external sources."""
        pass
    
    @abstractmethod
    async def analyze_performance(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze campaign performance and provide insights."""
        pass
    
    @abstractmethod
    async def generate_report(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate analytics report from collected metrics."""
        pass
    
    @abstractmethod
    async def get_trending_topics(self, platform: str, category: Optional[str] = None) -> List[str]:
        """Get trending topics for content optimization."""
        pass