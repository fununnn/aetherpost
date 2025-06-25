"""AetherPost unified platform system."""

from .core.base_platform import BasePlatform, PlatformResult, PlatformError
from .core.platform_registry import PlatformRegistry
from .core.platform_factory import PlatformFactory

__all__ = [
    'BasePlatform',
    'PlatformResult', 
    'PlatformError',
    'PlatformRegistry',
    'PlatformFactory'
]