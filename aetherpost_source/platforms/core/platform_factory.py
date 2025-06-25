"""Platform factory for creating platform instances."""

import logging
from typing import Dict, Any, Optional, List, Type

from .base_platform import BasePlatform
from .platform_registry import platform_registry
from .error_handling.exceptions import ConfigurationError, PlatformError
from .rate_limiting.rate_limiter import RateLimitConfig, PlatformRateLimits
from .error_handling.retry_strategy import RetryStrategy, RetryStrategies

logger = logging.getLogger(__name__)


class PlatformFactory:
    """Factory for creating and configuring platform instances."""
    
    def __init__(self):
        self._default_configs: Dict[str, Dict[str, Any]] = {}
        self._default_rate_limits: Dict[str, RateLimitConfig] = {}
        self._default_retry_strategies: Dict[str, RetryStrategy] = {}
        
        # Initialize default configurations
        self._setup_default_configurations()
    
    def create_platform(
        self,
        platform_name: str,
        credentials: Dict[str, str],
        config: Optional[Dict[str, Any]] = None,
        rate_limit_config: Optional[RateLimitConfig] = None,
        retry_strategy: Optional[RetryStrategy] = None
    ) -> BasePlatform:
        """Create a platform instance with the given configuration."""
        
        try:
            # Get platform class from registry
            platform_class = platform_registry.get_platform_class(platform_name)
            if not platform_class:
                raise ConfigurationError(
                    f"Platform '{platform_name}' not found. Available platforms: {platform_registry.get_available_platforms()}",
                    platform=platform_name,
                    config_key="platform_name"
                )
            
            # Merge configurations
            final_config = self._merge_config(platform_name, config)
            
            # Get rate limiting configuration
            final_rate_limit_config = rate_limit_config or self._get_default_rate_limit_config(platform_name)
            
            # Get retry strategy
            final_retry_strategy = retry_strategy or self._get_default_retry_strategy(platform_name)
            
            # Validate credentials
            self._validate_credentials(platform_name, platform_class, credentials)
            
            # Create platform instance
            platform_instance = platform_class(
                credentials=credentials,
                config=final_config,
                rate_limit_config=final_rate_limit_config,
                retry_strategy=final_retry_strategy
            )
            
            logger.info(f"Created {platform_name} platform instance")
            return platform_instance
            
        except Exception as e:
            logger.error(f"Failed to create platform '{platform_name}': {e}")
            if isinstance(e, (ConfigurationError, PlatformError)):
                raise
            else:
                raise ConfigurationError(
                    f"Failed to create platform '{platform_name}': {str(e)}",
                    platform=platform_name,
                    original_error=e
                )
    
    def create_multiple_platforms(
        self,
        platform_configs: Dict[str, Dict[str, Any]]
    ) -> Dict[str, BasePlatform]:
        """Create multiple platform instances from a configuration dictionary."""
        
        platforms = {}
        errors = {}
        
        for platform_name, platform_config in platform_configs.items():
            try:
                credentials = platform_config.get('credentials', {})
                config = platform_config.get('config', {})
                
                # Create rate limit config if provided
                rate_limit_config = None
                if 'rate_limits' in platform_config:
                    rate_limit_config = self._create_rate_limit_config(
                        platform_name, 
                        platform_config['rate_limits']
                    )
                
                # Create retry strategy if provided  
                retry_strategy = None
                if 'retry_strategy' in platform_config:
                    retry_strategy = self._create_retry_strategy(
                        platform_config['retry_strategy']
                    )
                
                platform = self.create_platform(
                    platform_name,
                    credentials,
                    config,
                    rate_limit_config,
                    retry_strategy
                )
                
                platforms[platform_name] = platform
                
            except Exception as e:
                logger.error(f"Failed to create platform '{platform_name}': {e}")
                errors[platform_name] = str(e)
        
        if errors:
            logger.warning(f"Failed to create {len(errors)} platforms: {list(errors.keys())}")
        
        logger.info(f"Successfully created {len(platforms)} platforms: {list(platforms.keys())}")
        return platforms
    
    def validate_platform_config(
        self, 
        platform_name: str, 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate platform configuration."""
        
        errors = []
        warnings = []
        
        # Check if platform exists
        platform_class = platform_registry.get_platform_class(platform_name)
        if not platform_class:
            errors.append(f"Platform '{platform_name}' not found")
            return {
                'valid': False,
                'errors': errors,
                'warnings': warnings
            }
        
        # Validate credentials
        credentials = config.get('credentials', {})
        cred_validation = self._validate_credentials(platform_name, platform_class, credentials, raise_on_error=False)
        errors.extend(cred_validation.get('errors', []))
        warnings.extend(cred_validation.get('warnings', []))
        
        # Validate configuration options
        platform_config = config.get('config', {})
        config_validation = self._validate_platform_specific_config(platform_name, platform_config)
        errors.extend(config_validation.get('errors', []))
        warnings.extend(config_validation.get('warnings', []))
        
        # Validate rate limiting config
        if 'rate_limits' in config:
            rate_limit_validation = self._validate_rate_limit_config(config['rate_limits'])
            errors.extend(rate_limit_validation.get('errors', []))
            warnings.extend(rate_limit_validation.get('warnings', []))
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'platform': platform_name
        }
    
    def get_platform_requirements(self, platform_name: str) -> Dict[str, Any]:
        """Get requirements for configuring a platform."""
        
        platform_class = platform_registry.get_platform_class(platform_name)
        if not platform_class:
            return {'error': f"Platform '{platform_name}' not found"}
        
        try:
            # Get platform info
            platform_info = platform_registry.get_platform_info(platform_name)
            
            # Get required credentials
            temp_instance = platform_class({})
            required_credentials = []
            
            if hasattr(temp_instance, 'authenticator') and temp_instance.authenticator:
                required_credentials = temp_instance.authenticator.required_credentials
            
            # Get configuration schema
            config_schema = self._get_config_schema(platform_name)
            
            return {
                'platform_name': platform_name,
                'display_name': platform_info.get('display_name', platform_name),
                'required_credentials': required_credentials,
                'optional_credentials': self._get_optional_credentials(platform_name),
                'config_schema': config_schema,
                'supported_features': {
                    'content_types': platform_info.get('supported_content_types', []),
                    'media_types': platform_info.get('supported_media_types', []),
                    'capabilities': platform_info.get('capabilities', [])
                },
                'limits': {
                    'character_limit': platform_info.get('character_limit', 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get requirements for {platform_name}: {e}")
            return {'error': str(e)}
    
    def _setup_default_configurations(self):
        """Setup default configurations for known platforms."""
        
        # Twitter defaults
        self._default_configs['twitter'] = {
            'api_version': 'v2',
            'upload_chunked': True,
            'wait_on_rate_limit': True
        }
        
        # Bluesky defaults
        self._default_configs['bluesky'] = {
            'base_url': 'https://bsky.social',
            'max_retries': 3,
            'timeout': 30
        }
        
        # Instagram defaults
        self._default_configs['instagram'] = {
            'api_version': 'v18.0',
            'upload_timeout': 120,
            'max_retries': 3
        }
        
        # LinkedIn defaults
        self._default_configs['linkedin'] = {
            'api_version': 'v2',
            'upload_timeout': 60,
            'max_retries': 3
        }
        
        # YouTube defaults
        self._default_configs['youtube'] = {
            'api_version': 'v3',
            'upload_timeout': 300,  # 5 minutes for video uploads
            'chunk_size': 8 * 1024 * 1024,  # 8MB chunks
            'max_retries': 5
        }
        
        # Setup default rate limits
        self._default_rate_limits['twitter'] = PlatformRateLimits.twitter()
        self._default_rate_limits['bluesky'] = PlatformRateLimits.bluesky()
        self._default_rate_limits['instagram'] = PlatformRateLimits.instagram()
        self._default_rate_limits['linkedin'] = PlatformRateLimits.linkedin()
        self._default_rate_limits['youtube'] = PlatformRateLimits.youtube()
        
        # Setup default retry strategies
        self._default_retry_strategies['twitter'] = RetryStrategies.social_media()
        self._default_retry_strategies['bluesky'] = RetryStrategies.rate_limit_aware()
        self._default_retry_strategies['instagram'] = RetryStrategies.conservative()
        self._default_retry_strategies['linkedin'] = RetryStrategies.conservative()
        self._default_retry_strategies['youtube'] = RetryStrategies.aggressive()
    
    def _merge_config(self, platform_name: str, user_config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge user configuration with defaults."""
        
        final_config = self._default_configs.get(platform_name, {}).copy()
        
        if user_config:
            final_config.update(user_config)
        
        return final_config
    
    def _get_default_rate_limit_config(self, platform_name: str) -> Optional[RateLimitConfig]:
        """Get default rate limit configuration for platform."""
        return self._default_rate_limits.get(platform_name)
    
    def _get_default_retry_strategy(self, platform_name: str) -> RetryStrategy:
        """Get default retry strategy for platform."""
        return self._default_retry_strategies.get(platform_name, RetryStrategies.social_media())
    
    def _validate_credentials(
        self, 
        platform_name: str, 
        platform_class: Type[BasePlatform], 
        credentials: Dict[str, str],
        raise_on_error: bool = True
    ) -> Dict[str, Any]:
        """Validate platform credentials."""
        
        errors = []
        warnings = []
        
        try:
            # Create temporary instance to check required credentials
            temp_instance = platform_class({})
            
            if hasattr(temp_instance, 'authenticator') and temp_instance.authenticator:
                required_creds = temp_instance.authenticator.required_credentials
                
                missing_creds = []
                for cred in required_creds:
                    if not credentials.get(cred):
                        missing_creds.append(cred)
                
                if missing_creds:
                    error_msg = f"Missing required credentials for {platform_name}: {', '.join(missing_creds)}"
                    errors.append(error_msg)
                    
                    if raise_on_error:
                        raise ConfigurationError(
                            error_msg,
                            platform=platform_name,
                            config_key="credentials"
                        )
            
        except Exception as e:
            if raise_on_error and not isinstance(e, ConfigurationError):
                raise ConfigurationError(
                    f"Credential validation failed for {platform_name}: {str(e)}",
                    platform=platform_name,
                    original_error=e
                )
            elif not isinstance(e, ConfigurationError):
                errors.append(str(e))
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_platform_specific_config(self, platform_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate platform-specific configuration options."""
        
        errors = []
        warnings = []
        
        # Platform-specific validation rules
        if platform_name == 'twitter':
            if 'api_version' in config and config['api_version'] not in ['v1.1', 'v2']:
                errors.append("Twitter API version must be 'v1.1' or 'v2'")
        
        elif platform_name == 'bluesky':
            if 'base_url' in config and not config['base_url'].startswith('https://'):
                warnings.append("Bluesky base_url should use HTTPS")
        
        elif platform_name == 'instagram':
            if 'upload_timeout' in config and config['upload_timeout'] < 30:
                warnings.append("Instagram upload timeout should be at least 30 seconds")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_rate_limit_config(self, rate_limit_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate rate limiting configuration."""
        
        errors = []
        warnings = []
        
        # Check required fields and values
        if 'requests_per_minute' in rate_limit_config:
            rpm = rate_limit_config['requests_per_minute']
            if not isinstance(rpm, int) or rpm <= 0:
                errors.append("requests_per_minute must be a positive integer")
        
        if 'requests_per_hour' in rate_limit_config:
            rph = rate_limit_config['requests_per_hour']
            if not isinstance(rph, int) or rph <= 0:
                errors.append("requests_per_hour must be a positive integer")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _create_rate_limit_config(self, platform_name: str, config: Dict[str, Any]) -> RateLimitConfig:
        """Create rate limit configuration from dictionary."""
        
        from .rate_limiting.rate_limiter import RateLimit
        
        # Create global limit
        global_limit = None
        if 'global' in config:
            global_config = config['global']
            global_limit = RateLimit(
                requests_per_minute=global_config.get('requests_per_minute'),
                requests_per_hour=global_config.get('requests_per_hour'),
                requests_per_day=global_config.get('requests_per_day'),
                burst_limit=global_config.get('burst_limit')
            )
        
        # Create endpoint limits
        endpoint_limits = {}
        if 'endpoints' in config:
            for endpoint, endpoint_config in config['endpoints'].items():
                endpoint_limits[endpoint] = RateLimit(
                    requests_per_minute=endpoint_config.get('requests_per_minute'),
                    requests_per_hour=endpoint_config.get('requests_per_hour'),
                    requests_per_day=endpoint_config.get('requests_per_day'),
                    burst_limit=endpoint_config.get('burst_limit'),
                    endpoint=endpoint
                )
        
        return RateLimitConfig(
            platform=platform_name,
            global_limit=global_limit,
            endpoint_limits=endpoint_limits,
            backoff_multiplier=config.get('backoff_multiplier', 2.0),
            max_backoff=config.get('max_backoff', 300)
        )
    
    def _create_retry_strategy(self, config: Dict[str, Any]) -> RetryStrategy:
        """Create retry strategy from configuration."""
        
        from .error_handling.retry_strategy import BackoffType
        
        return RetryStrategy(
            max_retries=config.get('max_retries', 3),
            base_delay=config.get('base_delay', 1.0),
            max_delay=config.get('max_delay', 300.0),
            backoff_type=BackoffType(config.get('backoff_type', 'exponential')),
            backoff_multiplier=config.get('backoff_multiplier', 2.0),
            jitter_range=config.get('jitter_range', 0.1),
            operation_configs=config.get('operation_configs', {})
        )
    
    def _get_config_schema(self, platform_name: str) -> Dict[str, Any]:
        """Get configuration schema for platform."""
        
        # Return basic schema - this could be expanded with more detailed schemas
        return {
            'type': 'object',
            'properties': {
                'timeout': {'type': 'integer', 'minimum': 1},
                'max_retries': {'type': 'integer', 'minimum': 0},
                'user_agent': {'type': 'string'}
            },
            'additionalProperties': True
        }
    
    def _get_optional_credentials(self, platform_name: str) -> List[str]:
        """Get optional credentials for platform."""
        
        optional_creds = {
            'twitter': ['bearer_token'],
            'bluesky': ['base_url'],
            'instagram': ['app_secret'],
            'youtube': ['refresh_token'],
            'linkedin': ['redirect_uri']
        }
        
        return optional_creds.get(platform_name, [])


# Global factory instance
platform_factory = PlatformFactory()