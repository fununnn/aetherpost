"""Platform service for unified platform operations."""

import logging
from typing import Dict, List, Any, Optional, Protocol
from dataclasses import dataclass
from datetime import datetime

from aetherpost.core.common.base_models import Platform, OperationResult
from aetherpost.core.common.config_manager import config_manager, PlatformCredentials
from aetherpost.core.common.error_handler import handle_errors
from aetherpost.core.services.container import service, PlatformServiceProtocol
from aetherpost.plugins.manager import plugin_manager


logger = logging.getLogger(__name__)


@dataclass
class ConnectorInfo:
    """Information about a platform connector."""
    platform: Platform
    connector_type: str
    is_authenticated: bool
    capabilities: List[str]
    rate_limits: Dict[str, Any]
    last_used: Optional[datetime] = None


class ConnectorProtocol(Protocol):
    """Protocol for platform connectors."""
    
    async def authenticate(self, credentials: PlatformCredentials) -> bool:
        """Authenticate with platform."""
        ...
    
    async def post(self, content: str, **kwargs) -> Dict[str, Any]:
        """Post content to platform."""
        ...
    
    async def validate_content(self, content: str) -> OperationResult:
        """Validate content for platform."""
        ...
    
    def get_capabilities(self) -> List[str]:
        """Get connector capabilities."""
        ...


@service(PlatformServiceProtocol)
class PlatformService:
    """Unified service for all platform operations."""
    
    def __init__(self):
        self.authenticated_connectors: Dict[Platform, ConnectorProtocol] = {}
        self.connector_cache: Dict[Platform, ConnectorInfo] = {}
        
    @handle_errors
    async def get_authenticated_connector(self, platform: Platform) -> ConnectorProtocol:
        """Get authenticated connector for platform."""
        # Check cache first
        if platform in self.authenticated_connectors:
            connector = self.authenticated_connectors[platform]
            if await self._verify_authentication(connector):
                return connector
        
        # Get credentials
        credentials = config_manager.config.get_platform_credentials(platform)
        if not credentials or not credentials.is_valid():
            raise ValueError(f"Invalid credentials for platform: {platform.value}")
        
        # Load connector
        connector = await self._load_connector(platform)
        
        # Authenticate
        auth_success = await connector.authenticate(credentials)
        if not auth_success:
            raise ValueError(f"Authentication failed for platform: {platform.value}")
        
        # Cache connector
        self.authenticated_connectors[platform] = connector
        self.connector_cache[platform] = ConnectorInfo(
            platform=platform,
            connector_type=type(connector).__name__,
            is_authenticated=True,
            capabilities=connector.get_capabilities(),
            rate_limits=getattr(connector, 'rate_limits', {}),
            last_used=datetime.now()
        )
        
        logger.info(f"Successfully authenticated connector for {platform.value}")
        return connector
    
    async def _load_connector(self, platform: Platform) -> ConnectorProtocol:
        """Load connector from plugin manager."""
        try:
            connector = plugin_manager.load_connector(platform.value)
            if not connector:
                raise ValueError(f"No connector available for platform: {platform.value}")
            return connector
        except Exception as e:
            logger.error(f"Failed to load connector for {platform.value}: {e}")
            raise
    
    async def _verify_authentication(self, connector: ConnectorProtocol) -> bool:
        """Verify if connector is still authenticated."""
        try:
            # This would depend on connector implementation
            # For now, assume it's valid
            return True
        except Exception:
            return False
    
    @handle_errors
    def validate_platform_config(self, platform: Platform) -> OperationResult:
        """Validate platform configuration."""
        try:
            credentials = config_manager.config.get_platform_credentials(platform)
            
            if not credentials:
                return OperationResult.error_result(
                    f"No credentials configured for {platform.value}"
                )
            
            if not credentials.is_valid():
                return OperationResult.error_result(
                    f"Invalid credentials for {platform.value}",
                    errors=["Check API keys and tokens"]
                )
            
            return OperationResult.success_result(
                f"Platform {platform.value} configuration is valid"
            )
            
        except Exception as e:
            return OperationResult.error_result(
                f"Configuration validation failed for {platform.value}: {e}"
            )
    
    @handle_errors
    async def post_content(self, platform: Platform, content: str, 
                          **options) -> OperationResult:
        """Post content to platform with unified interface."""
        try:
            connector = await self.get_authenticated_connector(platform)
            
            # Validate content first
            validation = await connector.validate_content(content)
            if not validation.success:
                return validation
            
            # Post content
            result = await connector.post(content, **options)
            
            # Update last used time
            if platform in self.connector_cache:
                self.connector_cache[platform].last_used = datetime.now()
            
            return OperationResult.success_result(
                f"Content posted to {platform.value}",
                data=result
            )
            
        except Exception as e:
            logger.error(f"Failed to post to {platform.value}: {e}")
            return OperationResult.error_result(
                f"Failed to post to {platform.value}: {e}"
            )
    
    @handle_errors
    async def validate_content_for_platform(self, platform: Platform, 
                                           content: str) -> OperationResult:
        """Validate content for specific platform requirements."""
        try:
            connector = await self.get_authenticated_connector(platform)
            return await connector.validate_content(content)
        except Exception as e:
            return OperationResult.error_result(
                f"Content validation failed for {platform.value}: {e}"
            )
    
    def get_configured_platforms(self) -> List[Platform]:
        """Get list of properly configured platforms."""
        configured = []
        
        for platform in Platform:
            validation = self.validate_platform_config(platform)
            if validation.success:
                configured.append(platform)
        
        return configured
    
    def get_platform_capabilities(self, platform: Platform) -> List[str]:
        """Get capabilities for a platform."""
        if platform in self.connector_cache:
            return self.connector_cache[platform].capabilities
        
        # Try to load connector to get capabilities
        try:
            # This would need to be implemented based on connector interface
            return []
        except Exception:
            return []
    
    def get_connector_status(self) -> Dict[str, Any]:
        """Get status of all connectors."""
        status = {
            "total_platforms": len(Platform),
            "configured_platforms": len(self.get_configured_platforms()),
            "authenticated_connectors": len(self.authenticated_connectors),
            "connectors": {}
        }
        
        for platform, info in self.connector_cache.items():
            status["connectors"][platform.value] = {
                "connector_type": info.connector_type,
                "is_authenticated": info.is_authenticated,
                "capabilities_count": len(info.capabilities),
                "last_used": info.last_used.isoformat() if info.last_used else None
            }
        
        return status
    
    async def refresh_authentication(self, platform: Platform) -> OperationResult:
        """Refresh authentication for a platform."""
        try:
            # Remove from cache to force re-authentication
            if platform in self.authenticated_connectors:
                del self.authenticated_connectors[platform]
            if platform in self.connector_cache:
                del self.connector_cache[platform]
            
            # Re-authenticate
            await self.get_authenticated_connector(platform)
            
            return OperationResult.success_result(
                f"Authentication refreshed for {platform.value}"
            )
            
        except Exception as e:
            return OperationResult.error_result(
                f"Failed to refresh authentication for {platform.value}: {e}"
            )
    
    def clear_cache(self) -> None:
        """Clear all cached connectors."""
        self.authenticated_connectors.clear()
        self.connector_cache.clear()
        logger.info("Platform service cache cleared")