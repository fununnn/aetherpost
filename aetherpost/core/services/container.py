"""Dependency injection container for AetherPost services."""

import logging
from typing import Type, TypeVar, Dict, Any, Optional, Callable, get_type_hints
from dataclasses import dataclass
from abc import ABC, abstractmethod
import inspect

from aetherpost.core.common.base_models import OperationResult


logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class ServiceDefinition:
    """Definition of a service in the container."""
    interface: Type
    implementation: Type
    singleton: bool = True
    factory: Optional[Callable] = None
    dependencies: Optional[Dict[str, Type]] = None


class ServiceLifecycle:
    """Manages service lifecycle and instance caching."""
    
    def __init__(self):
        self._instances: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
    
    def get_instance(self, service_type: Type[T], factory: Callable[[], T], 
                    singleton: bool = True) -> T:
        """Get service instance with proper lifecycle management."""
        if singleton and service_type in self._instances:
            return self._instances[service_type]
        
        instance = factory()
        
        if singleton:
            self._instances[service_type] = instance
        
        return instance
    
    def clear_cache(self) -> None:
        """Clear all cached instances."""
        self._instances.clear()


class Container:
    """Dependency injection container for managing services."""
    
    def __init__(self):
        self.services: Dict[Type, ServiceDefinition] = {}
        self.lifecycle = ServiceLifecycle()
        
    def register_service(self, interface: Type[T], implementation: Type[T], 
                        singleton: bool = True) -> None:
        """Register a service implementation for an interface."""
        dependencies = self._extract_dependencies(implementation)
        
        self.services[interface] = ServiceDefinition(
            interface=interface,
            implementation=implementation,
            singleton=singleton,
            dependencies=dependencies
        )
        
        logger.debug(f"Registered service: {interface.__name__} -> {implementation.__name__}")
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T],
                        singleton: bool = True) -> None:
        """Register a factory function for a service."""
        self.services[interface] = ServiceDefinition(
            interface=interface,
            implementation=None,
            singleton=singleton,
            factory=factory
        )
        
        logger.debug(f"Registered factory for: {interface.__name__}")
    
    def register_instance(self, interface: Type[T], instance: T) -> None:
        """Register a pre-created instance."""
        self.services[interface] = ServiceDefinition(
            interface=interface,
            implementation=type(instance),
            singleton=True
        )
        self.lifecycle._instances[interface] = instance
        
        logger.debug(f"Registered instance: {interface.__name__}")
    
    def get_service(self, interface: Type[T]) -> T:
        """Get service instance with dependency injection."""
        if interface not in self.services:
            raise ValueError(f"Service not registered: {interface.__name__}")
        
        service_def = self.services[interface]
        
        def factory():
            if service_def.factory:
                return service_def.factory()
            
            if service_def.implementation:
                # Resolve dependencies
                dependencies = {}
                if service_def.dependencies:
                    for param_name, dep_type in service_def.dependencies.items():
                        dependencies[param_name] = self.get_service(dep_type)
                
                return service_def.implementation(**dependencies)
            
            raise ValueError(f"No implementation or factory for: {interface.__name__}")
        
        return self.lifecycle.get_instance(
            interface, 
            factory, 
            service_def.singleton
        )
    
    def _extract_dependencies(self, implementation: Type) -> Dict[str, Type]:
        """Extract constructor dependencies from type hints."""
        try:
            constructor = implementation.__init__
            signature = inspect.signature(constructor)
            type_hints = get_type_hints(constructor)
            
            dependencies = {}
            for param_name, param in signature.parameters.items():
                if param_name == 'self':
                    continue
                
                if param_name in type_hints:
                    dependencies[param_name] = type_hints[param_name]
            
            return dependencies
            
        except Exception as e:
            logger.warning(f"Failed to extract dependencies for {implementation.__name__}: {e}")
            return {}
    
    def validate_registrations(self) -> OperationResult:
        """Validate all service registrations."""
        errors = []
        
        for interface, service_def in self.services.items():
            try:
                # Check if implementation exists
                if service_def.implementation and not inspect.isclass(service_def.implementation):
                    errors.append(f"Invalid implementation for {interface.__name__}")
                
                # Check if dependencies can be resolved
                if service_def.dependencies:
                    for dep_name, dep_type in service_def.dependencies.items():
                        if dep_type not in self.services:
                            errors.append(f"Unresolved dependency {dep_type.__name__} for {interface.__name__}")
                
            except Exception as e:
                errors.append(f"Validation error for {interface.__name__}: {e}")
        
        if errors:
            return OperationResult.error_result(
                "Service registration validation failed",
                errors=errors
            )
        
        return OperationResult.success_result("All service registrations valid")
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about registered services."""
        info = {
            "total_services": len(self.services),
            "cached_instances": len(self.lifecycle._instances),
            "services": {}
        }
        
        for interface, service_def in self.services.items():
            info["services"][interface.__name__] = {
                "implementation": service_def.implementation.__name__ if service_def.implementation else "Factory",
                "singleton": service_def.singleton,
                "has_dependencies": bool(service_def.dependencies),
                "is_cached": interface in self.lifecycle._instances
            }
        
        return info
    
    def clear_cache(self) -> None:
        """Clear all cached service instances."""
        self.lifecycle.clear_cache()
        logger.info("Service cache cleared")


# Service interfaces for type safety
class PlatformServiceProtocol(ABC):
    """Protocol for platform services."""
    
    @abstractmethod
    async def get_authenticated_connector(self, platform: str):
        """Get authenticated connector for platform."""
        pass
    
    @abstractmethod
    def validate_platform_config(self, platform: str) -> OperationResult:
        """Validate platform configuration."""
        pass


class ContentServiceProtocol(ABC):
    """Protocol for content services."""
    
    @abstractmethod
    async def generate_content(self, request: Dict[str, Any]) -> OperationResult:
        """Generate content based on request."""
        pass
    
    @abstractmethod
    async def validate_content(self, content: str, platform: str) -> OperationResult:
        """Validate content for platform requirements."""
        pass


class ConfigServiceProtocol(ABC):
    """Protocol for configuration services."""
    
    @abstractmethod
    def get_config(self) -> Any:
        """Get current configuration."""
        pass
    
    @abstractmethod
    def validate_config(self) -> OperationResult:
        """Validate current configuration."""
        pass


# Global container instance
container = Container()


# Decorator for automatic service injection
def inject(**injections):
    """Decorator for automatic dependency injection."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Inject specified services
            for param_name, service_type in injections.items():
                if param_name not in kwargs:
                    kwargs[param_name] = container.get_service(service_type)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Service registration helpers
def service(interface: Type[T], singleton: bool = True):
    """Decorator to register a class as a service implementation."""
    def decorator(implementation: Type[T]):
        container.register_service(interface, implementation, singleton)
        return implementation
    return decorator


def factory_service(interface: Type[T], singleton: bool = True):
    """Decorator to register a factory function."""
    def decorator(factory_func: Callable[[], T]):
        container.register_factory(interface, factory_func, singleton)
        return factory_func
    return decorator