"""Caching and performance optimization utilities."""

import asyncio
import functools
import hashlib
import json
import pickle
import time
from typing import Any, Callable, Optional, Dict, Union
from dataclasses import dataclass
from pathlib import Path
import redis
import aioredis

from ..logging import get_logger

logger = get_logger("cache")


@dataclass
class CacheConfig:
    """Cache configuration."""
    ttl: int = 3600  # Time to live in seconds
    max_size: int = 1000  # Maximum cache size for in-memory cache
    prefix: str = "aetherpost"
    use_redis: bool = True
    redis_url: str = "redis://localhost:6379/0"


class CacheManager:
    """Centralized cache management."""
    
    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self.memory_cache = {}
        self.cache_stats = {"hits": 0, "misses": 0, "sets": 0}
        
        # Redis clients
        self.redis_client = None
        self.async_redis_client = None
        
        if self.config.use_redis:
            self._setup_redis()
    
    def _setup_redis(self):
        """Setup Redis clients."""
        try:
            self.redis_client = redis.from_url(self.config.redis_url)
            self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed, falling back to memory cache: {e}")
            self.config.use_redis = False
    
    async def _setup_async_redis(self):
        """Setup async Redis client."""
        if not self.async_redis_client and self.config.use_redis:
            try:
                self.async_redis_client = await aioredis.from_url(self.config.redis_url)
                await self.async_redis_client.ping()
                logger.info("Async Redis connection established")
            except Exception as e:
                logger.warning(f"Async Redis connection failed: {e}")
    
    def _make_key(self, key: str) -> str:
        """Create cache key with prefix."""
        return f"{self.config.prefix}:{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (sync)."""
        cache_key = self._make_key(key)
        
        try:
            if self.config.use_redis and self.redis_client:
                value = self.redis_client.get(cache_key)
                if value:
                    self.cache_stats["hits"] += 1
                    return pickle.loads(value)
            else:
                # Memory cache fallback
                if cache_key in self.memory_cache:
                    entry = self.memory_cache[cache_key]
                    if entry["expires"] > time.time():
                        self.cache_stats["hits"] += 1
                        return entry["value"]
                    else:
                        del self.memory_cache[cache_key]
            
            self.cache_stats["misses"] += 1
            return None
        
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.cache_stats["misses"] += 1
            return None
    
    async def aget(self, key: str) -> Optional[Any]:
        """Get value from cache (async)."""
        cache_key = self._make_key(key)
        
        try:
            if self.config.use_redis:
                await self._setup_async_redis()
                if self.async_redis_client:
                    value = await self.async_redis_client.get(cache_key)
                    if value:
                        self.cache_stats["hits"] += 1
                        return pickle.loads(value)
            
            # Memory cache fallback
            if cache_key in self.memory_cache:
                entry = self.memory_cache[cache_key]
                if entry["expires"] > time.time():
                    self.cache_stats["hits"] += 1
                    return entry["value"]
                else:
                    del self.memory_cache[cache_key]
            
            self.cache_stats["misses"] += 1
            return None
        
        except Exception as e:
            logger.error(f"Async cache get error: {e}")
            self.cache_stats["misses"] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache (sync)."""
        cache_key = self._make_key(key)
        ttl = ttl or self.config.ttl
        
        try:
            if self.config.use_redis and self.redis_client:
                serialized = pickle.dumps(value)
                self.redis_client.setex(cache_key, ttl, serialized)
            else:
                # Memory cache fallback
                self._cleanup_memory_cache()
                self.memory_cache[cache_key] = {
                    "value": value,
                    "expires": time.time() + ttl
                }
            
            self.cache_stats["sets"] += 1
            return True
        
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def aset(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache (async)."""
        cache_key = self._make_key(key)
        ttl = ttl or self.config.ttl
        
        try:
            if self.config.use_redis:
                await self._setup_async_redis()
                if self.async_redis_client:
                    serialized = pickle.dumps(value)
                    await self.async_redis_client.setex(cache_key, ttl, serialized)
                    self.cache_stats["sets"] += 1
                    return True
            
            # Memory cache fallback
            self._cleanup_memory_cache()
            self.memory_cache[cache_key] = {
                "value": value,
                "expires": time.time() + ttl
            }
            
            self.cache_stats["sets"] += 1
            return True
        
        except Exception as e:
            logger.error(f"Async cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        cache_key = self._make_key(key)
        
        try:
            if self.config.use_redis and self.redis_client:
                self.redis_client.delete(cache_key)
            
            if cache_key in self.memory_cache:
                del self.memory_cache[cache_key]
            
            return True
        
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def _cleanup_memory_cache(self):
        """Clean up expired entries from memory cache."""
        if len(self.memory_cache) > self.config.max_size:
            # Remove oldest entries
            sorted_items = sorted(
                self.memory_cache.items(),
                key=lambda x: x[1]["expires"]
            )
            
            # Keep only the newest max_size/2 entries
            to_keep = dict(sorted_items[-(self.config.max_size // 2):])
            self.memory_cache = to_keep
    
    def clear(self):
        """Clear all cache entries."""
        try:
            if self.config.use_redis and self.redis_client:
                pattern = f"{self.config.prefix}:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            
            self.memory_cache.clear()
            logger.info("Cache cleared")
        
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
    
    def get_stats(self) -> Dict[str, Union[int, float]]:
        """Get cache statistics."""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (
            self.cache_stats["hits"] / total_requests 
            if total_requests > 0 else 0
        )
        
        return {
            **self.cache_stats,
            "hit_rate": hit_rate,
            "memory_entries": len(self.memory_cache)
        }


# Global cache manager instance
cache_manager = CacheManager()


def _generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """Generate cache key from function name and arguments."""
    # Create a hash of the function arguments
    key_parts = [func_name]
    
    # Add positional arguments
    for arg in args:
        if hasattr(arg, '__dict__'):
            # For objects, use their dict representation
            key_parts.append(str(sorted(arg.__dict__.items())))
        else:
            key_parts.append(str(arg))
    
    # Add keyword arguments
    for k, v in sorted(kwargs.items()):
        if hasattr(v, '__dict__'):
            key_parts.append(f"{k}={sorted(v.__dict__.items())}")
        else:
            key_parts.append(f"{k}={v}")
    
    # Create hash
    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def cache(ttl: int = 3600, key_prefix: Optional[str] = None):
    """Decorator for caching function results."""
    
    def decorator(func: Callable) -> Callable:
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            prefix = key_prefix or func.__name__
            cache_key = f"{prefix}:{_generate_cache_key(func.__name__, args, kwargs)}"
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {func.__name__}, executing function")
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            prefix = key_prefix or func.__name__
            cache_key = f"{prefix}:{_generate_cache_key(func.__name__, args, kwargs)}"
            
            # Try to get from cache
            cached_result = await cache_manager.aget(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {func.__name__}, executing function")
            result = await func(*args, **kwargs)
            await cache_manager.aset(cache_key, result, ttl)
            
            return result
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class PerformanceMonitor:
    """Performance monitoring utilities."""
    
    def __init__(self):
        self.metrics = {}
    
    def record_timing(self, operation: str, duration: float):
        """Record timing metrics."""
        if operation not in self.metrics:
            self.metrics[operation] = {
                "count": 0,
                "total_time": 0.0,
                "min_time": float("inf"),
                "max_time": 0.0
            }
        
        metrics = self.metrics[operation]
        metrics["count"] += 1
        metrics["total_time"] += duration
        metrics["min_time"] = min(metrics["min_time"], duration)
        metrics["max_time"] = max(metrics["max_time"], duration)
    
    def get_stats(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics."""
        stats = {}
        
        for operation, metrics in self.metrics.items():
            avg_time = (
                metrics["total_time"] / metrics["count"] 
                if metrics["count"] > 0 else 0
            )
            
            stats[operation] = {
                "count": metrics["count"],
                "avg_time": avg_time,
                "min_time": metrics["min_time"] if metrics["min_time"] != float("inf") else 0,
                "max_time": metrics["max_time"],
                "total_time": metrics["total_time"]
            }
        
        return stats


# Global performance monitor
performance_monitor = PerformanceMonitor()


def measure_performance(operation_name: Optional[str] = None):
    """Decorator for measuring function performance."""
    
    def decorator(func: Callable) -> Callable:
        op_name = operation_name or func.__name__
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                performance_monitor.record_timing(op_name, duration)
                logger.debug(f"Function {op_name} took {duration:.3f}s")
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                performance_monitor.record_timing(op_name, duration)
                logger.debug(f"Async function {op_name} took {duration:.3f}s")
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class ConnectionPool:
    """Connection pooling for external services."""
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.pools = {}
    
    def get_pool(self, service_name: str):
        """Get connection pool for a service."""
        if service_name not in self.pools:
            # Initialize pool for service
            # Implementation depends on specific service type
            pass
        return self.pools.get(service_name)


# Global connection pool
connection_pool = ConnectionPool()


def batch_process(batch_size: int = 10, delay: float = 0.1):
    """Decorator for batching function calls."""
    
    def decorator(func: Callable) -> Callable:
        batch_queue = []
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            batch_queue.append((args, kwargs))
            
            if len(batch_queue) >= batch_size:
                # Process batch
                batch = batch_queue[:batch_size]
                batch_queue[:batch_size] = []
                
                results = []
                for batch_args, batch_kwargs in batch:
                    result = await func(*batch_args, **batch_kwargs)
                    results.append(result)
                
                return results[0]  # Return result for current call
            else:
                # Wait for more items or timeout
                await asyncio.sleep(delay)
                return await func(*args, **kwargs)
        
        return async_wrapper
    
    return decorator