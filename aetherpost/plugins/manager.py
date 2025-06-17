"""Plugin management system."""

import importlib
import inspect
from pathlib import Path
from typing import Dict, Type, Any, List

from .base import SNSConnectorBase, AIProviderBase, AnalyticsProviderBase


class PluginManager:
    """Manage plugins for connectors, AI providers, and analytics."""
    
    def __init__(self):
        self.connectors: Dict[str, Type[SNSConnectorBase]] = {}
        self.ai_providers: Dict[str, Type[AIProviderBase]] = {}
        self.analytics_providers: Dict[str, Type[AnalyticsProviderBase]] = {}
        
        # Auto-discover built-in plugins
        self.discover_plugins()
    
    def register_connector(self, name: str, connector_class: Type[SNSConnectorBase]):
        """Register an SNS connector."""
        if not issubclass(connector_class, SNSConnectorBase):
            raise ValueError(f"Connector must inherit from SNSConnectorBase")
        
        self.connectors[name] = connector_class
    
    def register_ai_provider(self, name: str, provider_class: Type[AIProviderBase]):
        """Register an AI provider."""
        if not issubclass(provider_class, AIProviderBase):
            raise ValueError(f"AI provider must inherit from AIProviderBase")
        
        self.ai_providers[name] = provider_class
    
    def register_analytics_provider(self, name: str, provider_class: Type[AnalyticsProviderBase]):
        """Register an analytics provider."""
        if not issubclass(provider_class, AnalyticsProviderBase):
            raise ValueError(f"Analytics provider must inherit from AnalyticsProviderBase")
        
        self.analytics_providers[name] = provider_class
    
    def load_connector(self, name: str, credentials: Dict[str, Any]) -> SNSConnectorBase:
        """Load and instantiate an SNS connector."""
        if name not in self.connectors:
            raise ValueError(f"Unknown connector: {name}")
        
        connector_class = self.connectors[name]
        return connector_class(credentials)
    
    def load_ai_provider(self, name: str, config: Dict[str, Any]) -> AIProviderBase:
        """Load and instantiate an AI provider."""
        if name not in self.ai_providers:
            raise ValueError(f"Unknown AI provider: {name}")
        
        provider_class = self.ai_providers[name]
        return provider_class(config)
    
    def load_analytics_provider(self, name: str, config: Dict[str, Any]) -> AnalyticsProviderBase:
        """Load and instantiate an analytics provider."""
        if name not in self.analytics_providers:
            raise ValueError(f"Unknown analytics provider: {name}")
        
        provider_class = self.analytics_providers[name]
        return provider_class(config)
    
    def discover_plugins(self):
        """Auto-discover plugins in the plugins directory."""
        plugin_dir = Path(__file__).parent
        
        # Discover connectors
        self._discover_in_directory(
            plugin_dir / "connectors", 
            SNSConnectorBase, 
            self.register_connector
        )
        
        # Discover AI providers
        self._discover_in_directory(
            plugin_dir / "ai_providers", 
            AIProviderBase, 
            self.register_ai_provider
        )
        
        # Discover analytics providers
        self._discover_in_directory(
            plugin_dir / "analytics", 
            AnalyticsProviderBase, 
            self.register_analytics_provider
        )
    
    def _discover_in_directory(self, directory: Path, base_class: Type, register_func):
        """Discover plugins in a specific directory."""
        if not directory.exists():
            return
        
        for item in directory.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                # Try to load connector/provider from directory
                try:
                    module_path = f"autopromo.plugins.{directory.name}.{item.name}.{directory.name[:-1]}"
                    module = importlib.import_module(module_path)
                    
                    # Find classes that inherit from the base class
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, base_class) and 
                            obj != base_class and 
                            not obj.__name__.endswith('Base')):
                            register_func(item.name, obj)
                            break
                
                except ImportError:
                    # Try alternative naming conventions
                    continue
    
    def list_connectors(self) -> List[str]:
        """List available SNS connectors."""
        return list(self.connectors.keys())
    
    def list_ai_providers(self) -> List[str]:
        """List available AI providers."""
        return list(self.ai_providers.keys())
    
    def list_analytics_providers(self) -> List[str]:
        """List available analytics providers."""
        return list(self.analytics_providers.keys())
    
    def get_connector_info(self, name: str) -> Dict[str, Any]:
        """Get information about a connector."""
        if name not in self.connectors:
            raise ValueError(f"Unknown connector: {name}")
        
        connector_class = self.connectors[name]
        # Create temporary instance to get info
        temp_instance = connector_class({})
        
        return {
            "name": name,
            "class": connector_class.__name__,
            "supported_media_types": temp_instance.supported_media_types,
            "module": connector_class.__module__
        }
    
    def diagnose(self) -> Dict[str, Any]:
        """Run diagnostics on all plugins."""
        diagnosis = {
            "connectors": {},
            "ai_providers": {},
            "analytics_providers": {}
        }
        
        # Test connectors
        for name in self.connectors:
            try:
                info = self.get_connector_info(name)
                diagnosis["connectors"][name] = {
                    "status": "ok",
                    "info": info
                }
            except Exception as e:
                diagnosis["connectors"][name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Test AI providers
        for name in self.ai_providers:
            try:
                provider_class = self.ai_providers[name]
                diagnosis["ai_providers"][name] = {
                    "status": "ok",
                    "class": provider_class.__name__,
                    "module": provider_class.__module__
                }
            except Exception as e:
                diagnosis["ai_providers"][name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return diagnosis


# Global plugin manager instance
plugin_manager = PluginManager()

# Register available plugins
try:
    # Register Twitter connector
    from .connectors.twitter.connector import TwitterConnector
    plugin_manager.register_connector("twitter", TwitterConnector)
except ImportError:
    pass

try:
    # Register Bluesky connector
    from .connectors.bluesky.connector import BlueskyConnector
    plugin_manager.register_connector("bluesky", BlueskyConnector)
except ImportError:
    pass

try:
    # Register Mastodon connector
    from .connectors.mastodon.connector import MastodonConnector
    plugin_manager.register_connector("mastodon", MastodonConnector)
except ImportError:
    pass

# Note: AI Assistant provider removed for OSS release

try:
    # Register OpenAI AI provider
    from .ai_providers.openai.provider import OpenAIProvider
    plugin_manager.register_ai_provider("openai", OpenAIProvider)
except ImportError:
    pass

try:
    # Register Basic Analytics provider
    from .analytics.basic.provider import BasicAnalyticsProvider
    plugin_manager.register_analytics_provider("basic", BasicAnalyticsProvider)
except ImportError:
    pass