"""Platform registry for automatic platform discovery and management."""

import logging
import importlib
import inspect
from typing import Dict, Type, List, Optional, Any
from pathlib import Path

from .base_platform import BasePlatform

logger = logging.getLogger(__name__)


class PlatformRegistry:
    """Registry for managing available platforms."""
    
    def __init__(self):
        self._platforms: Dict[str, Type[BasePlatform]] = {}
        self._platform_configs: Dict[str, Dict[str, Any]] = {}
        self._auto_discovered = False
    
    def register_platform(
        self, 
        platform_name: str, 
        platform_class: Type[BasePlatform],
        config: Optional[Dict[str, Any]] = None
    ):
        """Register a platform class."""
        
        if not issubclass(platform_class, BasePlatform):
            raise ValueError(f"Platform class must inherit from BasePlatform")
        
        self._platforms[platform_name] = platform_class
        if config:
            self._platform_configs[platform_name] = config
        
        logger.debug(f"Registered platform: {platform_name}")
    
    def unregister_platform(self, platform_name: str):
        """Unregister a platform."""
        
        if platform_name in self._platforms:
            del self._platforms[platform_name]
            
        if platform_name in self._platform_configs:
            del self._platform_configs[platform_name]
        
        logger.debug(f"Unregistered platform: {platform_name}")
    
    def get_platform_class(self, platform_name: str) -> Optional[Type[BasePlatform]]:
        """Get platform class by name."""
        
        # Auto-discover if not done yet
        if not self._auto_discovered:
            self.auto_discover_platforms()
        
        return self._platforms.get(platform_name)
    
    def get_available_platforms(self) -> List[str]:
        """Get list of available platform names."""
        
        # Auto-discover if not done yet
        if not self._auto_discovered:
            self.auto_discover_platforms()
        
        return list(self._platforms.keys())
    
    def get_platform_info(self, platform_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a platform."""
        
        platform_class = self.get_platform_class(platform_name)
        if not platform_class:
            return None
        
        # Get information through class inspection
        try:
            # Create a temporary instance to get properties
            # (This is safe because we're only reading properties)
            temp_instance = platform_class({})  # Empty credentials for info gathering
            
            info = {
                'name': platform_name,
                'class_name': platform_class.__name__,
                'module': platform_class.__module__,
                'display_name': temp_instance.platform_display_name,
                'supported_content_types': [ct.value for ct in temp_instance.supported_content_types],
                'supported_media_types': temp_instance.supported_media_types,
                'capabilities': [cap.value for cap in temp_instance.platform_capabilities],
                'character_limit': temp_instance.character_limit,
                'config': self._platform_configs.get(platform_name, {}),
                'docstring': platform_class.__doc__ or "No description available"
            }
            
            return info
            
        except Exception as e:
            logger.warning(f"Failed to get info for platform {platform_name}: {e}")
            return {
                'name': platform_name,
                'class_name': platform_class.__name__,
                'module': platform_class.__module__,
                'error': str(e)
            }
    
    def auto_discover_platforms(self):
        """Automatically discover and register platforms from implementations directory."""
        
        try:
            # Get the implementations directory
            implementations_dir = Path(__file__).parent.parent / "implementations"
            
            if not implementations_dir.exists():
                logger.warning("Implementations directory not found")
                return
            
            # Discover platform modules
            for platform_file in implementations_dir.glob("*_platform.py"):
                try:
                    self._discover_platform_from_file(platform_file)
                except Exception as e:
                    logger.warning(f"Failed to discover platform from {platform_file}: {e}")
            
            self._auto_discovered = True
            logger.info(f"Auto-discovered {len(self._platforms)} platforms")
            
        except Exception as e:
            logger.error(f"Platform auto-discovery failed: {e}")
    
    def _discover_platform_from_file(self, platform_file: Path):
        """Discover and register platform from a Python file."""
        
        # Extract platform name from filename (e.g., twitter_platform.py -> twitter)
        platform_name = platform_file.stem.replace('_platform', '')
        
        # Build module path 
        module_path = f"platforms.implementations.{platform_file.stem}"
        
        try:
            # Import the module using relative import
            module = importlib.import_module(module_path, package="aetherpost_source")
            
            # Find platform classes in the module
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, BasePlatform) and 
                    obj != BasePlatform and 
                    obj.__module__ == module_path):
                    
                    # Register the platform
                    self.register_platform(platform_name, obj)
                    logger.debug(f"Auto-registered platform: {platform_name} ({name})")
                    break
            else:
                logger.warning(f"No platform class found in {platform_file}")
                
        except ImportError as e:
            logger.warning(f"Failed to import platform module {module_path}: {e}")
        except Exception as e:
            logger.error(f"Error discovering platform from {platform_file}: {e}")
    
    def validate_platform(self, platform_name: str) -> Dict[str, Any]:
        """Validate a platform implementation."""
        
        platform_class = self.get_platform_class(platform_name)
        if not platform_class:
            return {
                'valid': False,
                'errors': [f"Platform '{platform_name}' not found"]
            }
        
        errors = []
        warnings = []
        
        try:
            # Check required abstract methods
            required_methods = [
                'platform_name',
                'platform_display_name', 
                'supported_content_types',
                'supported_media_types',
                'platform_capabilities',
                'character_limit',
                '_setup_authenticator',
                '_post_content_impl',
                '_update_profile_impl',
                '_delete_post_impl'
            ]
            
            for method in required_methods:
                if not hasattr(platform_class, method):
                    errors.append(f"Missing required method: {method}")
            
            # Check if platform can be instantiated
            try:
                temp_instance = platform_class({})
                
                # Validate properties
                if not isinstance(temp_instance.platform_name, str):
                    errors.append("platform_name must return a string")
                
                if not isinstance(temp_instance.platform_display_name, str):
                    errors.append("platform_display_name must return a string")
                
                if not isinstance(temp_instance.character_limit, int):
                    errors.append("character_limit must return an integer")
                
                if temp_instance.character_limit <= 0:
                    warnings.append("character_limit should be positive")
                
            except Exception as e:
                errors.append(f"Failed to instantiate platform: {e}")
            
        except Exception as e:
            errors.append(f"Validation error: {e}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'platform': platform_name
        }
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        
        if not self._auto_discovered:
            self.auto_discover_platforms()
        
        # Count platforms by capabilities
        capability_counts = {}
        content_type_counts = {}
        
        for platform_name in self._platforms:
            info = self.get_platform_info(platform_name)
            if info:
                for capability in info.get('capabilities', []):
                    capability_counts[capability] = capability_counts.get(capability, 0) + 1
                
                for content_type in info.get('supported_content_types', []):
                    content_type_counts[content_type] = content_type_counts.get(content_type, 0) + 1
        
        return {
            'total_platforms': len(self._platforms),
            'platform_names': list(self._platforms.keys()),
            'capability_distribution': capability_counts,
            'content_type_distribution': content_type_counts,
            'auto_discovered': self._auto_discovered
        }
    
    def search_platforms(self, **criteria) -> List[str]:
        """Search platforms by criteria."""
        
        if not self._auto_discovered:
            self.auto_discover_platforms()
        
        matching_platforms = []
        
        for platform_name in self._platforms:
            info = self.get_platform_info(platform_name)
            if not info:
                continue
            
            matches = True
            
            # Check capabilities
            if 'capabilities' in criteria:
                required_caps = criteria['capabilities']
                if isinstance(required_caps, str):
                    required_caps = [required_caps]
                
                platform_caps = info.get('capabilities', [])
                if not all(cap in platform_caps for cap in required_caps):
                    matches = False
            
            # Check content types
            if 'content_types' in criteria:
                required_types = criteria['content_types']
                if isinstance(required_types, str):
                    required_types = [required_types]
                
                platform_types = info.get('supported_content_types', [])
                if not all(ct in platform_types for ct in required_types):
                    matches = False
            
            # Check character limit
            if 'min_character_limit' in criteria:
                if info.get('character_limit', 0) < criteria['min_character_limit']:
                    matches = False
            
            if 'max_character_limit' in criteria:
                if info.get('character_limit', float('inf')) > criteria['max_character_limit']:
                    matches = False
            
            if matches:
                matching_platforms.append(platform_name)
        
        return matching_platforms
    
    def clear_registry(self):
        """Clear all registered platforms."""
        
        self._platforms.clear()
        self._platform_configs.clear()
        self._auto_discovered = False
        
        logger.info("Cleared platform registry")


# Global registry instance
platform_registry = PlatformRegistry()