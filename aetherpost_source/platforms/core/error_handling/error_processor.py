"""Centralized error processing and handling."""

import asyncio
import logging
from typing import Dict, Any, Optional, Type, Callable, Awaitable
from datetime import datetime, timedelta

from .exceptions import PlatformError, RateLimitError, NetworkError, AuthenticationError
from .retry_strategy import RetryStrategy

logger = logging.getLogger(__name__)


class ErrorProcessor:
    """Centralized error processing and recovery system."""
    
    def __init__(self):
        self.error_handlers: Dict[Type[Exception], Callable] = {}
        self.retry_strategies: Dict[str, RetryStrategy] = {}
        self.error_counts: Dict[str, int] = {}
        self.last_errors: Dict[str, datetime] = {}
    
    def register_handler(
        self, 
        error_type: Type[Exception], 
        handler: Callable[[Exception], Any]
    ):
        """Register a custom error handler for specific error types."""
        self.error_handlers[error_type] = handler
    
    def register_retry_strategy(self, platform: str, strategy: RetryStrategy):
        """Register retry strategy for a specific platform."""
        self.retry_strategies[platform] = strategy
    
    async def process_error(
        self,
        error: Exception,
        platform: str,
        operation: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process an error and determine appropriate response."""
        
        # Track error occurrence
        error_key = f"{platform}:{operation}:{type(error).__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        self.last_errors[error_key] = datetime.utcnow()
        
        # Log error details
        logger.error(
            f"Platform error in {platform}.{operation}: {error}",
            extra={
                'platform': platform,
                'operation': operation,
                'error_type': type(error).__name__,
                'error_count': self.error_counts[error_key],
                'context': context
            }
        )
        
        # Process based on error type
        if isinstance(error, RateLimitError):
            return await self._handle_rate_limit_error(error, platform, operation)
        elif isinstance(error, AuthenticationError):
            return await self._handle_auth_error(error, platform, operation)
        elif isinstance(error, NetworkError):
            return await self._handle_network_error(error, platform, operation)
        else:
            return await self._handle_generic_error(error, platform, operation)
    
    async def _handle_rate_limit_error(
        self, 
        error: RateLimitError, 
        platform: str, 
        operation: str
    ) -> Dict[str, Any]:
        """Handle rate limit errors with appropriate delays."""
        
        retry_after = error.retry_after or 60  # Default 60 seconds
        
        logger.warning(
            f"Rate limit hit for {platform}.{operation}, waiting {retry_after}s"
        )
        
        return {
            'action': 'retry',
            'delay': retry_after,
            'max_retries': 3,
            'backoff_multiplier': 1.0,  # No additional backoff for rate limits
            'reason': 'rate_limit'
        }
    
    async def _handle_auth_error(
        self, 
        error: AuthenticationError, 
        platform: str, 
        operation: str
    ) -> Dict[str, Any]:
        """Handle authentication errors."""
        
        error_key = f"{platform}:auth"
        recent_auth_errors = self.error_counts.get(error_key, 0)
        
        if recent_auth_errors >= 3:
            logger.error(f"Multiple auth failures for {platform}, requires manual intervention")
            return {
                'action': 'fail',
                'reason': 'authentication_failure',
                'requires_manual_intervention': True
            }
        
        return {
            'action': 'retry',
            'delay': 5,
            'max_retries': 2,
            'backoff_multiplier': 2.0,
            'reason': 'authentication_retry'
        }
    
    async def _handle_network_error(
        self, 
        error: NetworkError, 
        platform: str, 
        operation: str
    ) -> Dict[str, Any]:
        """Handle network-related errors."""
        
        # Exponential backoff for network errors
        error_key = f"{platform}:{operation}:network"
        error_count = self.error_counts.get(error_key, 0)
        
        if error_count >= 5:
            logger.error(f"Too many network errors for {platform}.{operation}")
            return {
                'action': 'fail',
                'reason': 'network_failure_threshold_exceeded'
            }
        
        delay = min(2 ** error_count, 300)  # Exponential backoff, max 5 minutes
        
        return {
            'action': 'retry',
            'delay': delay,
            'max_retries': 5,
            'backoff_multiplier': 2.0,
            'reason': 'network_error'
        }
    
    async def _handle_generic_error(
        self, 
        error: Exception, 
        platform: str, 
        operation: str
    ) -> Dict[str, Any]:
        """Handle generic errors with custom handlers if available."""
        
        error_type = type(error)
        
        # Check for custom handler
        if error_type in self.error_handlers:
            try:
                return await self.error_handlers[error_type](error)
            except Exception as handler_error:
                logger.error(f"Error handler failed: {handler_error}")
        
        # Default generic handling
        return {
            'action': 'fail',
            'reason': 'unhandled_error',
            'error_type': error_type.__name__,
            'error_message': str(error)
        }
    
    async def should_retry(
        self,
        platform: str,
        operation: str,
        current_attempt: int
    ) -> bool:
        """Determine if an operation should be retried based on error history."""
        
        strategy = self.retry_strategies.get(platform)
        if not strategy:
            return current_attempt < 3  # Default: retry up to 3 times
        
        return strategy.should_retry(operation, current_attempt)
    
    def get_error_statistics(self, platform: Optional[str] = None) -> Dict[str, Any]:
        """Get error statistics for monitoring and debugging."""
        
        if platform:
            # Filter by platform
            platform_errors = {
                k: v for k, v in self.error_counts.items() 
                if k.startswith(f"{platform}:")
            }
            return {
                'platform': platform,
                'total_errors': sum(platform_errors.values()),
                'error_breakdown': platform_errors,
                'last_error': max(
                    (self.last_errors.get(k) for k in platform_errors.keys()),
                    default=None
                )
            }
        else:
            # All platforms
            return {
                'total_errors': sum(self.error_counts.values()),
                'error_breakdown': dict(self.error_counts),
                'platforms_affected': len(set(
                    k.split(':')[0] for k in self.error_counts.keys()
                )),
                'last_error': max(self.last_errors.values()) if self.last_errors else None
            }
    
    def reset_error_counts(self, platform: Optional[str] = None):
        """Reset error counts for monitoring reset."""
        
        if platform:
            keys_to_remove = [k for k in self.error_counts.keys() if k.startswith(f"{platform}:")]
            for key in keys_to_remove:
                del self.error_counts[key]
                if key in self.last_errors:
                    del self.last_errors[key]
        else:
            self.error_counts.clear()
            self.last_errors.clear()
        
        logger.info(f"Reset error counts for {platform or 'all platforms'}")


# Global error processor instance
error_processor = ErrorProcessor()