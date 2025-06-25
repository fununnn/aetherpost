"""Retry strategies for platform operations."""

import asyncio
import random
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum


class BackoffType(Enum):
    """Types of backoff strategies."""
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIXED = "fixed"
    JITTERED = "jittered"


class RetryStrategy:
    """Configurable retry strategy for platform operations."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 300.0,
        backoff_type: BackoffType = BackoffType.EXPONENTIAL,
        backoff_multiplier: float = 2.0,
        jitter_range: float = 0.1,
        operation_configs: Optional[Dict[str, Dict[str, Any]]] = None
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_type = backoff_type
        self.backoff_multiplier = backoff_multiplier
        self.jitter_range = jitter_range
        self.operation_configs = operation_configs or {}
        
        # Track retry attempts per operation
        self.retry_counts: Dict[str, int] = {}
        self.last_attempts: Dict[str, datetime] = {}
    
    def should_retry(self, operation: str, current_attempt: int) -> bool:
        """Determine if an operation should be retried."""
        
        # Check operation-specific config
        op_config = self.operation_configs.get(operation, {})
        max_retries = op_config.get('max_retries', self.max_retries)
        
        if current_attempt >= max_retries:
            return False
        
        # Check rate limiting for this operation
        operation_key = f"{operation}:{datetime.utcnow().strftime('%Y-%m-%d-%H')}"
        hourly_retries = self.retry_counts.get(operation_key, 0)
        
        # Limit to 100 retries per operation per hour
        if hourly_retries >= 100:
            return False
        
        return True
    
    def get_delay(self, operation: str, attempt: int) -> float:
        """Calculate delay before next retry attempt."""
        
        # Check operation-specific config
        op_config = self.operation_configs.get(operation, {})
        base_delay = op_config.get('base_delay', self.base_delay)
        max_delay = op_config.get('max_delay', self.max_delay)
        backoff_type = BackoffType(op_config.get('backoff_type', self.backoff_type.value))
        
        # Calculate base delay based on backoff type
        if backoff_type == BackoffType.FIXED:
            delay = base_delay
        elif backoff_type == BackoffType.LINEAR:
            delay = base_delay * attempt
        elif backoff_type == BackoffType.EXPONENTIAL:
            delay = base_delay * (self.backoff_multiplier ** (attempt - 1))
        elif backoff_type == BackoffType.JITTERED:
            exponential_delay = base_delay * (self.backoff_multiplier ** (attempt - 1))
            jitter = random.uniform(-self.jitter_range, self.jitter_range) * exponential_delay
            delay = exponential_delay + jitter
        else:
            delay = base_delay
        
        # Apply maximum delay limit
        delay = min(delay, max_delay)
        
        # Track this retry attempt
        operation_key = f"{operation}:{datetime.utcnow().strftime('%Y-%m-%d-%H')}"
        self.retry_counts[operation_key] = self.retry_counts.get(operation_key, 0) + 1
        self.last_attempts[operation] = datetime.utcnow()
        
        return delay
    
    async def execute_with_retry(
        self,
        operation_name: str,
        operation_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute an operation with automatic retry logic."""
        
        attempt = 1
        last_error = None
        
        while attempt <= self.max_retries + 1:  # +1 for initial attempt
            try:
                # Execute the operation
                if asyncio.iscoroutinefunction(operation_func):
                    return await operation_func(*args, **kwargs)
                else:
                    return operation_func(*args, **kwargs)
                    
            except Exception as error:
                last_error = error
                
                # Check if we should retry
                if not self.should_retry(operation_name, attempt):
                    break
                
                # Calculate delay and wait
                delay = self.get_delay(operation_name, attempt)
                
                # Log retry attempt
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Retry {attempt}/{self.max_retries} for {operation_name} "
                    f"after {delay:.2f}s delay. Error: {error}"
                )
                
                await asyncio.sleep(delay)
                attempt += 1
        
        # All retries exhausted, raise the last error
        raise last_error
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get retry statistics for monitoring."""
        
        current_hour = datetime.utcnow().strftime('%Y-%m-%d-%H')
        current_hour_retries = {
            op: count for op, count in self.retry_counts.items()
            if op.endswith(current_hour)
        }
        
        return {
            'max_retries': self.max_retries,
            'base_delay': self.base_delay,
            'backoff_type': self.backoff_type.value,
            'current_hour_retries': sum(current_hour_retries.values()),
            'operations_with_retries': len(current_hour_retries),
            'last_retry_time': max(self.last_attempts.values()) if self.last_attempts else None,
            'total_operations_retried': len(self.last_attempts)
        }
    
    def reset_statistics(self):
        """Reset retry statistics."""
        self.retry_counts.clear()
        self.last_attempts.clear()


# Predefined retry strategies for common use cases
class RetryStrategies:
    """Collection of predefined retry strategies."""
    
    @staticmethod
    def aggressive() -> RetryStrategy:
        """Aggressive retry strategy for critical operations."""
        return RetryStrategy(
            max_retries=5,
            base_delay=0.5,
            max_delay=60.0,
            backoff_type=BackoffType.EXPONENTIAL,
            backoff_multiplier=1.5
        )
    
    @staticmethod
    def conservative() -> RetryStrategy:
        """Conservative retry strategy for non-critical operations."""
        return RetryStrategy(
            max_retries=2,
            base_delay=2.0,
            max_delay=30.0,
            backoff_type=BackoffType.LINEAR,
            backoff_multiplier=1.0
        )
    
    @staticmethod
    def rate_limit_aware() -> RetryStrategy:
        """Retry strategy optimized for rate-limited APIs."""
        return RetryStrategy(
            max_retries=3,
            base_delay=30.0,
            max_delay=900.0,  # 15 minutes max
            backoff_type=BackoffType.JITTERED,
            backoff_multiplier=2.0,
            jitter_range=0.2
        )
    
    @staticmethod
    def social_media() -> RetryStrategy:
        """Retry strategy tailored for social media platforms."""
        return RetryStrategy(
            max_retries=4,
            base_delay=1.0,
            max_delay=300.0,
            backoff_type=BackoffType.EXPONENTIAL,
            backoff_multiplier=2.0,
            operation_configs={
                'authenticate': {'max_retries': 2, 'base_delay': 5.0},
                'post_content': {'max_retries': 3, 'base_delay': 2.0},
                'upload_media': {'max_retries': 5, 'base_delay': 3.0},
                'get_analytics': {'max_retries': 2, 'base_delay': 1.0}
            }
        )