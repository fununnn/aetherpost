"""Rate limiting and API quota management system."""

import asyncio
import time
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
import logging
from datetime import datetime, timedelta

from ..exceptions import RateLimitError, AetherPostError, ErrorCode
from ..logging.logger import logger


class RateLimitStrategy(Enum):
    """Rate limiting strategies."""
    CONSERVATIVE = "conservative"  # Stay well below limits
    AGGRESSIVE = "aggressive"      # Use full limits
    ADAPTIVE = "adaptive"          # Adjust based on usage


@dataclass
class RateLimit:
    """Rate limit configuration for a platform/endpoint."""
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_limit: int = 5  # Max requests in quick succession
    retry_after: int = 60  # Default retry delay in seconds


@dataclass
class UsageStats:
    """Usage statistics for rate limiting."""
    requests_made: int = 0
    last_request_time: float = 0
    daily_requests: int = 0
    daily_reset_time: float = 0
    errors_count: int = 0
    last_error_time: float = 0
    request_times: List[float] = field(default_factory=list)
    
    def reset_daily(self):
        """Reset daily counters."""
        self.daily_requests = 0
        self.daily_reset_time = time.time()
    
    def add_request(self):
        """Record a successful request."""
        current_time = time.time()
        self.requests_made += 1
        self.daily_requests += 1
        self.last_request_time = current_time
        
        # Keep only requests from last hour for rate calculation
        hour_ago = current_time - 3600
        self.request_times = [t for t in self.request_times if t > hour_ago]
        self.request_times.append(current_time)
    
    def add_error(self):
        """Record an error."""
        self.errors_count += 1
        self.last_error_time = time.time()


class PlatformRateLimiter:
    """Rate limiter for a specific platform."""
    
    # Default rate limits for different platforms
    DEFAULT_LIMITS = {
        "twitter": RateLimit(
            requests_per_minute=300,
            requests_per_hour=15000,
            requests_per_day=500000,
            burst_limit=10
        ),
        "instagram": RateLimit(
            requests_per_minute=200,
            requests_per_hour=5000,
            requests_per_day=50000,
            burst_limit=5
        ),
        "youtube": RateLimit(
            requests_per_minute=100,
            requests_per_hour=10000,
            requests_per_day=1000000,
            burst_limit=3
        ),
        "linkedin": RateLimit(
            requests_per_minute=100,
            requests_per_hour=2000,
            requests_per_day=20000,
            burst_limit=5
        ),
        "tiktok": RateLimit(
            requests_per_minute=50,
            requests_per_hour=1000,
            requests_per_day=10000,
            burst_limit=3
        ),
        "reddit": RateLimit(
            requests_per_minute=60,
            requests_per_hour=3600,
            requests_per_day=100000,
            burst_limit=10
        )
    }
    
    def __init__(self, platform: str, strategy: RateLimitStrategy = RateLimitStrategy.CONSERVATIVE):
        self.platform = platform
        self.strategy = strategy
        self.rate_limit = self._get_rate_limit()
        self.usage_stats = UsageStats()
        self._lock = asyncio.Lock()
        
        # Adjust limits based on strategy
        self._apply_strategy()
        
        logger.info(f"Initialized rate limiter for {platform}", platform=platform, extra={
            "strategy": strategy.value,
            "limits": {
                "per_minute": self.rate_limit.requests_per_minute,
                "per_hour": self.rate_limit.requests_per_hour,
                "per_day": self.rate_limit.requests_per_day
            }
        })
    
    def _get_rate_limit(self) -> RateLimit:
        """Get rate limit configuration for platform."""
        return self.DEFAULT_LIMITS.get(self.platform, RateLimit(
            requests_per_minute=60,
            requests_per_hour=1000,
            requests_per_day=10000
        ))
    
    def _apply_strategy(self):
        """Apply rate limiting strategy."""
        if self.strategy == RateLimitStrategy.CONSERVATIVE:
            # Use 70% of limits
            self.rate_limit.requests_per_minute = int(self.rate_limit.requests_per_minute * 0.7)
            self.rate_limit.requests_per_hour = int(self.rate_limit.requests_per_hour * 0.7)
            self.rate_limit.requests_per_day = int(self.rate_limit.requests_per_day * 0.7)
        elif self.strategy == RateLimitStrategy.AGGRESSIVE:
            # Use 95% of limits
            self.rate_limit.requests_per_minute = int(self.rate_limit.requests_per_minute * 0.95)
            self.rate_limit.requests_per_hour = int(self.rate_limit.requests_per_hour * 0.95)
            self.rate_limit.requests_per_day = int(self.rate_limit.requests_per_day * 0.95)
        # ADAPTIVE uses dynamic adjustment based on actual usage
    
    async def acquire(self, endpoint: str = "default") -> bool:
        """Acquire permission to make a request."""
        async with self._lock:
            current_time = time.time()
            
            # Reset daily stats if needed
            if current_time - self.usage_stats.daily_reset_time > 86400:  # 24 hours
                self.usage_stats.reset_daily()
            
            # Check if we can make a request
            if not self._can_make_request(current_time):
                delay = self._calculate_delay(current_time)
                
                logger.warning(
                    f"Rate limit reached for {self.platform}",
                    platform=self.platform,
                    extra={
                        "endpoint": endpoint,
                        "delay_seconds": delay,
                        "daily_requests": self.usage_stats.daily_requests,
                        "recent_requests": len(self.usage_stats.request_times)
                    }
                )
                
                raise RateLimitError(
                    platform=self.platform,
                    retry_after=delay,
                    details={
                        "endpoint": endpoint,
                        "daily_requests": self.usage_stats.daily_requests,
                        "requests_per_day_limit": self.rate_limit.requests_per_day
                    }
                )
            
            # Record the request
            self.usage_stats.add_request()
            
            logger.debug(f"Rate limit permission granted for {self.platform}", platform=self.platform, extra={
                "endpoint": endpoint,
                "daily_requests": self.usage_stats.daily_requests,
                "recent_requests": len(self.usage_stats.request_times)
            })
            
            return True
    
    def _can_make_request(self, current_time: float) -> bool:
        """Check if we can make a request now."""
        
        # Check daily limit
        if self.usage_stats.daily_requests >= self.rate_limit.requests_per_day:
            return False
        
        # Check recent requests for burst and minute limits
        minute_ago = current_time - 60
        recent_requests = [t for t in self.usage_stats.request_times if t > minute_ago]
        
        # Check minute limit
        if len(recent_requests) >= self.rate_limit.requests_per_minute:
            return False
        
        # Check burst limit (requests in last 10 seconds)
        burst_window = current_time - 10
        burst_requests = [t for t in recent_requests if t > burst_window]
        if len(burst_requests) >= self.rate_limit.burst_limit:
            return False
        
        # Check if we're in error backoff
        if self.usage_stats.errors_count > 0:
            error_backoff = self._calculate_error_backoff()
            if current_time - self.usage_stats.last_error_time < error_backoff:
                return False
        
        return True
    
    def _calculate_delay(self, current_time: float) -> int:
        """Calculate how long to wait before next request."""
        
        # Find the longest delay needed
        delays = []
        
        # Daily limit delay
        if self.usage_stats.daily_requests >= self.rate_limit.requests_per_day:
            daily_reset = self.usage_stats.daily_reset_time + 86400
            delays.append(int(daily_reset - current_time))
        
        # Minute limit delay
        minute_ago = current_time - 60
        recent_requests = [t for t in self.usage_stats.request_times if t > minute_ago]
        if len(recent_requests) >= self.rate_limit.requests_per_minute:
            oldest_in_minute = min(recent_requests)
            delays.append(int(60 - (current_time - oldest_in_minute)))
        
        # Burst limit delay
        burst_window = current_time - 10
        burst_requests = [t for t in recent_requests if t > burst_window]
        if len(burst_requests) >= self.rate_limit.burst_limit:
            oldest_in_burst = min(burst_requests)
            delays.append(int(10 - (current_time - oldest_in_burst)))
        
        # Error backoff delay
        if self.usage_stats.errors_count > 0:
            error_backoff = self._calculate_error_backoff()
            time_since_error = current_time - self.usage_stats.last_error_time
            if time_since_error < error_backoff:
                delays.append(int(error_backoff - time_since_error))
        
        return max(delays) if delays else 60
    
    def _calculate_error_backoff(self) -> int:
        """Calculate exponential backoff for errors."""
        return min(60 * (2 ** min(self.usage_stats.errors_count, 5)), 300)  # Max 5 minutes
    
    def record_success(self):
        """Record a successful API call."""
        # Reset error count on success
        if self.usage_stats.errors_count > 0:
            logger.info(f"API errors cleared for {self.platform}", platform=self.platform)
            self.usage_stats.errors_count = 0
    
    def record_error(self, error_type: str = "unknown"):
        """Record an API error."""
        self.usage_stats.add_error()
        
        logger.warning(f"API error recorded for {self.platform}", platform=self.platform, extra={
            "error_type": error_type,
            "total_errors": self.usage_stats.errors_count,
            "backoff_seconds": self._calculate_error_backoff()
        })
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        current_time = time.time()
        recent_requests = [t for t in self.usage_stats.request_times if t > current_time - 3600]
        
        return {
            "platform": self.platform,
            "strategy": self.strategy.value,
            "daily_requests": self.usage_stats.daily_requests,
            "daily_limit": self.rate_limit.requests_per_day,
            "recent_requests_hour": len(recent_requests),
            "hourly_limit": self.rate_limit.requests_per_hour,
            "total_errors": self.usage_stats.errors_count,
            "last_request": datetime.fromtimestamp(self.usage_stats.last_request_time).isoformat() if self.usage_stats.last_request_time > 0 else None,
            "can_make_request": self._can_make_request(current_time)
        }


class GlobalRateLimitManager:
    """Global rate limit manager for all platforms."""
    
    def __init__(self, strategy: RateLimitStrategy = RateLimitStrategy.CONSERVATIVE):
        self.strategy = strategy
        self.limiters: Dict[str, PlatformRateLimiter] = {}
        self.stats_file = Path("logs/rate_limit_stats.json")
        
        # Load saved stats
        self._load_stats()
        
        # Schedule periodic stats saving
        self._schedule_stats_save()
    
    def get_limiter(self, platform: str) -> PlatformRateLimiter:
        """Get or create rate limiter for platform."""
        if platform not in self.limiters:
            self.limiters[platform] = PlatformRateLimiter(platform, self.strategy)
        return self.limiters[platform]
    
    async def acquire(self, platform: str, endpoint: str = "default") -> bool:
        """Acquire permission to make request to platform."""
        limiter = self.get_limiter(platform)
        return await limiter.acquire(endpoint)
    
    def record_success(self, platform: str):
        """Record successful API call."""
        if platform in self.limiters:
            self.limiters[platform].record_success()
    
    def record_error(self, platform: str, error_type: str = "unknown"):
        """Record API error."""
        limiter = self.get_limiter(platform)
        limiter.record_error(error_type)
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all platforms."""
        return {
            platform: limiter.get_stats()
            for platform, limiter in self.limiters.items()
        }
    
    def _load_stats(self):
        """Load saved rate limit statistics."""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f:
                    saved_stats = json.load(f)
                
                for platform, stats in saved_stats.items():
                    limiter = self.get_limiter(platform)
                    # Restore usage stats
                    limiter.usage_stats.daily_requests = stats.get("daily_requests", 0)
                    limiter.usage_stats.errors_count = stats.get("errors_count", 0)
                    
                    # Only restore if from same day
                    daily_reset_time = stats.get("daily_reset_time", 0)
                    if time.time() - daily_reset_time < 86400:
                        limiter.usage_stats.daily_reset_time = daily_reset_time
                    else:
                        limiter.usage_stats.reset_daily()
                
                logger.info("Rate limit stats loaded from file")
                
            except Exception as e:
                logger.warning(f"Failed to load rate limit stats: {e}")
    
    def _save_stats(self):
        """Save current rate limit statistics."""
        try:
            self.stats_file.parent.mkdir(exist_ok=True)
            
            stats_to_save = {}
            for platform, limiter in self.limiters.items():
                stats_to_save[platform] = {
                    "daily_requests": limiter.usage_stats.daily_requests,
                    "daily_reset_time": limiter.usage_stats.daily_reset_time,
                    "errors_count": limiter.usage_stats.errors_count,
                    "last_error_time": limiter.usage_stats.last_error_time
                }
            
            with open(self.stats_file, 'w') as f:
                json.dump(stats_to_save, f, indent=2)
            
            logger.debug("Rate limit stats saved")
            
        except Exception as e:
            logger.warning(f"Failed to save rate limit stats: {e}")
    
    def _schedule_stats_save(self):
        """Schedule periodic stats saving."""
        import threading
        
        def save_periodically():
            while True:
                time.sleep(300)  # Save every 5 minutes
                self._save_stats()
        
        thread = threading.Thread(target=save_periodically, daemon=True)
        thread.start()


# Global rate limit manager
rate_limit_manager = GlobalRateLimitManager()


# Decorator for automatic rate limiting
def rate_limited(platform: str, endpoint: str = "default"):
    """Decorator to add automatic rate limiting to API calls."""
    
    def decorator(func: Callable):
        async def async_wrapper(*args, **kwargs):
            try:
                # Acquire rate limit permission
                await rate_limit_manager.acquire(platform, endpoint)
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Record success
                rate_limit_manager.record_success(platform)
                
                return result
                
            except RateLimitError:
                # Re-raise rate limit errors
                raise
            except Exception as e:
                # Record other errors
                error_type = type(e).__name__
                rate_limit_manager.record_error(platform, error_type)
                raise
        
        def sync_wrapper(*args, **kwargs):
            return asyncio.run(async_wrapper(*args, **kwargs))
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator