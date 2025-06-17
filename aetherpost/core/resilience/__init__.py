"""Resilience and error handling utilities."""

import asyncio
import functools
import random
import time
from typing import Callable, Any, Optional, Type, Tuple
from dataclasses import dataclass
import logging

from ..logging import get_logger

logger = get_logger("resilience")


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    exceptions: Tuple[Type[Exception], ...] = (Exception,)


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """Circuit breaker pattern implementation."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    def call(self, func: Callable, *args, **kwargs):
        """Call function with circuit breaker protection."""
        
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
                logger.info("Circuit breaker transitioning to half-open")
            else:
                raise CircuitBreakerError("Circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker."""
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self):
        """Handle successful function call."""
        if self.state == "half-open":
            self.state = "closed"
            logger.info("Circuit breaker reset to closed")
        
        self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed function call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


def retry(config: RetryConfig = None):
    """Decorator for adding retry behavior to functions."""
    
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                
                except config.exceptions as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts - 1:
                        logger.error(
                            f"Function {func.__name__} failed after {config.max_attempts} attempts",
                            extra={"function": func.__name__, "attempts": config.max_attempts}
                        )
                        raise e
                    
                    delay = _calculate_delay(config, attempt)
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{config.max_attempts}), "
                        f"retrying in {delay:.2f}s: {e}",
                        extra={"function": func.__name__, "attempt": attempt + 1, "delay": delay}
                    )
                    time.sleep(delay)
            
            raise last_exception
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                
                except config.exceptions as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts - 1:
                        logger.error(
                            f"Async function {func.__name__} failed after {config.max_attempts} attempts",
                            extra={"function": func.__name__, "attempts": config.max_attempts}
                        )
                        raise e
                    
                    delay = _calculate_delay(config, attempt)
                    logger.warning(
                        f"Async function {func.__name__} failed (attempt {attempt + 1}/{config.max_attempts}), "
                        f"retrying in {delay:.2f}s: {e}",
                        extra={"function": func.__name__, "attempt": attempt + 1, "delay": delay}
                    )
                    await asyncio.sleep(delay)
            
            raise last_exception
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def _calculate_delay(config: RetryConfig, attempt: int) -> float:
    """Calculate delay for retry attempt."""
    
    # Exponential backoff
    delay = config.base_delay * (config.exponential_base ** attempt)
    
    # Apply maximum delay
    delay = min(delay, config.max_delay)
    
    # Add jitter if enabled
    if config.jitter:
        delay *= (0.5 + random.random() * 0.5)
    
    return delay


class TimeoutError(Exception):
    """Exception raised when operation times out."""
    pass


def timeout(seconds: float):
    """Decorator for adding timeout to functions."""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                logger.warning(
                    f"Function {func.__name__} timed out after {seconds}s",
                    extra={"function": func.__name__, "timeout": seconds}
                )
                raise TimeoutError(f"Function {func.__name__} timed out after {seconds}s")
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Function {func.__name__} timed out after {seconds}s")
            
            # Set the signal handler
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(seconds))
            
            try:
                result = func(*args, **kwargs)
                signal.alarm(0)  # Disable the alarm
                return result
            except TimeoutError:
                logger.warning(
                    f"Function {func.__name__} timed out after {seconds}s",
                    extra={"function": func.__name__, "timeout": seconds}
                )
                raise
            finally:
                signal.signal(signal.SIGALRM, old_handler)
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class HealthChecker:
    """Health checking functionality."""
    
    def __init__(self):
        self.checks = {}
    
    def register_check(self, name: str, check_func: Callable[[], bool]):
        """Register a health check function."""
        self.checks[name] = check_func
    
    async def run_checks(self) -> dict:
        """Run all registered health checks."""
        results = {}
        overall_healthy = True
        
        for name, check_func in self.checks.items():
            try:
                if asyncio.iscoroutinefunction(check_func):
                    healthy = await check_func()
                else:
                    healthy = check_func()
                
                results[name] = {
                    "healthy": healthy,
                    "timestamp": time.time()
                }
                
                if not healthy:
                    overall_healthy = False
            
            except Exception as e:
                logger.error(f"Health check {name} failed: {e}")
                results[name] = {
                    "healthy": False,
                    "error": str(e),
                    "timestamp": time.time()
                }
                overall_healthy = False
        
        results["overall"] = {
            "healthy": overall_healthy,
            "timestamp": time.time()
        }
        
        return results


# Global health checker instance
health_checker = HealthChecker()


def register_health_check(name: str):
    """Decorator to register a function as a health check."""
    
    def decorator(func: Callable[[], bool]) -> Callable[[], bool]:
        health_checker.register_check(name, func)
        return func
    
    return decorator


class RateLimiter:
    """Rate limiting functionality."""
    
    def __init__(self, requests_per_second: float):
        self.requests_per_second = requests_per_second
        self.tokens = requests_per_second
        self.last_update = time.time()
    
    def acquire(self) -> bool:
        """Try to acquire a token for rate limiting."""
        now = time.time()
        elapsed = now - self.last_update
        
        # Add tokens based on elapsed time
        self.tokens = min(
            self.requests_per_second,
            self.tokens + elapsed * self.requests_per_second
        )
        self.last_update = now
        
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        
        return False
    
    async def wait_for_token(self):
        """Wait until a token is available."""
        while not self.acquire():
            await asyncio.sleep(0.1)


def rate_limit(requests_per_second: float):
    """Decorator for rate limiting function calls."""
    
    limiter = RateLimiter(requests_per_second)
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            await limiter.wait_for_token()
            return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we'll do a simple blocking wait
            while not limiter.acquire():
                time.sleep(0.1)
            return func(*args, **kwargs)
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator