"""Unified rate limiting system for platform APIs."""

import asyncio
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


@dataclass
class RateLimit:
    """Rate limit configuration for an endpoint or operation."""
    
    requests_per_minute: Optional[int] = None
    requests_per_hour: Optional[int] = None
    requests_per_day: Optional[int] = None
    burst_limit: Optional[int] = None
    window_size: int = 60  # seconds
    endpoint: Optional[str] = None
    operation: Optional[str] = None
    
    def __post_init__(self):
        # Calculate per-second rate from other limits
        if self.requests_per_minute and not hasattr(self, 'requests_per_second'):
            self.requests_per_second = self.requests_per_minute / 60.0
        elif self.requests_per_hour and not hasattr(self, 'requests_per_second'):
            self.requests_per_second = self.requests_per_hour / 3600.0
        elif self.requests_per_day and not hasattr(self, 'requests_per_second'):
            self.requests_per_second = self.requests_per_day / 86400.0
        else:
            self.requests_per_second = 1.0  # Default fallback


@dataclass 
class RateLimitConfig:
    """Complete rate limiting configuration for a platform."""
    
    platform: str
    global_limit: Optional[RateLimit] = None
    endpoint_limits: Dict[str, RateLimit] = field(default_factory=dict)
    operation_limits: Dict[str, RateLimit] = field(default_factory=dict)
    backoff_multiplier: float = 2.0
    max_backoff: int = 300  # 5 minutes max
    jitter_range: float = 0.1
    
    def get_limit_for_endpoint(self, endpoint: str) -> RateLimit:
        """Get the most specific rate limit for an endpoint."""
        
        # Check exact endpoint match
        if endpoint in self.endpoint_limits:
            return self.endpoint_limits[endpoint]
        
        # Check partial endpoint matches (for parameterized endpoints)
        for pattern, limit in self.endpoint_limits.items():
            if pattern in endpoint or endpoint.startswith(pattern):
                return limit
        
        # Fall back to global limit
        return self.global_limit or RateLimit()
    
    def get_limit_for_operation(self, operation: str) -> RateLimit:
        """Get rate limit for a specific operation."""
        return self.operation_limits.get(operation, self.global_limit or RateLimit())


class RateLimiter:
    """Unified rate limiter with multiple algorithms and adaptive behavior."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.platform = config.platform
        
        # Track request timestamps for sliding window
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque())
        
        # Track rate limit hits for adaptive behavior
        self.limit_hits: Dict[str, List[datetime]] = defaultdict(list)
        self.current_delays: Dict[str, float] = defaultdict(float)
        
        # Lock for thread-safe operations
        self._locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        
        # Statistics tracking
        self.stats = {
            'requests_made': defaultdict(int),
            'requests_delayed': defaultdict(int),
            'total_delay_time': defaultdict(float),
            'rate_limit_hits': defaultdict(int)
        }
    
    async def acquire(self, endpoint: str, operation: Optional[str] = None) -> Dict[str, Any]:
        """Acquire permission to make a request, applying rate limiting."""
        
        key = f"{endpoint}:{operation}" if operation else endpoint
        
        async with self._locks[key]:
            # Get applicable rate limit
            limit = self._get_applicable_limit(endpoint, operation)
            
            # Check if we need to wait
            wait_time = self._calculate_wait_time(key, limit)
            
            if wait_time > 0:
                logger.info(f"Rate limiting {self.platform} {key}: waiting {wait_time:.2f}s")
                self.stats['requests_delayed'][key] += 1
                self.stats['total_delay_time'][key] += wait_time
                
                await asyncio.sleep(wait_time)
            
            # Record this request
            self._record_request(key)
            self.stats['requests_made'][key] += 1
            
            return {
                'granted': True,
                'wait_time': wait_time,
                'remaining_quota': self._get_remaining_quota(key, limit),
                'reset_time': self._get_reset_time(key, limit)
            }
    
    def _get_applicable_limit(self, endpoint: str, operation: Optional[str]) -> RateLimit:
        """Get the most applicable rate limit for the request."""
        
        if operation:
            op_limit = self.config.get_limit_for_operation(operation)
            if op_limit != self.config.global_limit:
                return op_limit
        
        return self.config.get_limit_for_endpoint(endpoint)
    
    def _calculate_wait_time(self, key: str, limit: RateLimit) -> float:
        """Calculate how long to wait before making the request."""
        
        now = time.time()
        history = self.request_history[key]
        
        # Clean old entries outside the window
        window_start = now - limit.window_size
        while history and history[0] < window_start:
            history.popleft()
        
        # Check if we're within limits
        current_count = len(history)
        
        # Determine the applicable limit
        if limit.requests_per_minute and limit.window_size <= 60:
            max_requests = limit.requests_per_minute
            window = 60
        elif limit.requests_per_hour and limit.window_size <= 3600:
            max_requests = limit.requests_per_hour  
            window = 3600
        else:
            # Use per-second rate
            max_requests = int(limit.requests_per_second * limit.window_size)
            window = limit.window_size
        
        if current_count >= max_requests:
            # We've hit the limit, calculate wait time
            oldest_request = history[0]
            wait_time = (oldest_request + window) - now
            
            # Apply adaptive backoff if we've been hitting limits
            wait_time *= self._get_backoff_multiplier(key)
            
            return max(0, wait_time)
        
        # Check burst limit
        if limit.burst_limit and current_count >= limit.burst_limit:
            # Apply a small delay for burst protection
            return 1.0
        
        return 0.0
    
    def _get_backoff_multiplier(self, key: str) -> float:
        """Get adaptive backoff multiplier based on recent rate limit hits."""
        
        now = datetime.utcnow()
        recent_hits = [
            hit for hit in self.limit_hits[key] 
            if (now - hit).total_seconds() < 300  # Last 5 minutes
        ]
        
        if len(recent_hits) == 0:
            return 1.0
        elif len(recent_hits) <= 2:
            return 1.2
        elif len(recent_hits) <= 5:
            return 1.5
        else:
            return min(2.0, 1.0 + (len(recent_hits) * 0.1))
    
    def _record_request(self, key: str):
        """Record a request in the history."""
        now = time.time()
        self.request_history[key].append(now)
    
    def _get_remaining_quota(self, key: str, limit: RateLimit) -> int:
        """Get remaining requests in current window."""
        
        current_count = len(self.request_history[key])
        
        if limit.requests_per_minute:
            return max(0, limit.requests_per_minute - current_count)
        elif limit.requests_per_hour:
            return max(0, limit.requests_per_hour - current_count)
        else:
            max_requests = int(limit.requests_per_second * limit.window_size)
            return max(0, max_requests - current_count)
    
    def _get_reset_time(self, key: str, limit: RateLimit) -> Optional[datetime]:
        """Get when the rate limit window resets."""
        
        history = self.request_history[key]
        if not history:
            return None
        
        oldest_request = history[0]
        reset_time = datetime.fromtimestamp(oldest_request + limit.window_size)
        return reset_time
    
    async def handle_rate_limit_response(
        self, 
        endpoint: str, 
        response_headers: Dict[str, str],
        status_code: int = 429
    ):
        """Handle rate limit response from API."""
        
        if status_code == 429:
            # Record rate limit hit
            key = endpoint
            self.limit_hits[key].append(datetime.utcnow())
            self.stats['rate_limit_hits'][key] += 1
            
            # Extract retry-after if available
            retry_after = response_headers.get('Retry-After')
            if retry_after:
                try:
                    delay = int(retry_after)
                    logger.warning(f"Rate limited by {self.platform} for {endpoint}, waiting {delay}s")
                    await asyncio.sleep(delay)
                except ValueError:
                    # Retry-After might be a date
                    pass
        
        # Update rate limit info from headers if available
        self._update_limits_from_headers(endpoint, response_headers)
    
    def _update_limits_from_headers(self, endpoint: str, headers: Dict[str, str]):
        """Update rate limit configuration based on API response headers."""
        
        # Common rate limit headers
        remaining = headers.get('X-RateLimit-Remaining') or headers.get('X-Rate-Limit-Remaining')
        limit = headers.get('X-RateLimit-Limit') or headers.get('X-Rate-Limit-Limit')
        reset = headers.get('X-RateLimit-Reset') or headers.get('X-Rate-Limit-Reset')
        
        if remaining and limit:
            try:
                remaining_count = int(remaining)
                total_limit = int(limit)
                
                # Update our understanding of the rate limit
                if endpoint not in self.config.endpoint_limits:
                    # Create new rate limit based on observed values
                    self.config.endpoint_limits[endpoint] = RateLimit(
                        requests_per_minute=total_limit,
                        endpoint=endpoint
                    )
                
                logger.debug(f"Rate limit info for {endpoint}: {remaining_count}/{total_limit}")
                
            except ValueError:
                pass
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get rate limiting statistics."""
        
        total_requests = sum(self.stats['requests_made'].values())
        total_delays = sum(self.stats['requests_delayed'].values())
        total_delay_time = sum(self.stats['total_delay_time'].values())
        total_hits = sum(self.stats['rate_limit_hits'].values())
        
        return {
            'platform': self.platform,
            'total_requests': total_requests,
            'total_delays': total_delays,
            'total_delay_time': total_delay_time,
            'total_rate_limit_hits': total_hits,
            'delay_percentage': (total_delays / total_requests * 100) if total_requests > 0 else 0,
            'average_delay': (total_delay_time / total_delays) if total_delays > 0 else 0,
            'by_endpoint': {
                endpoint: {
                    'requests': self.stats['requests_made'][endpoint],
                    'delays': self.stats['requests_delayed'][endpoint],
                    'delay_time': self.stats['total_delay_time'][endpoint],
                    'rate_limit_hits': self.stats['rate_limit_hits'][endpoint]
                }
                for endpoint in set(
                    list(self.stats['requests_made'].keys()) + 
                    list(self.stats['requests_delayed'].keys())
                )
            }
        }
    
    def reset_statistics(self):
        """Reset all statistics."""
        
        self.stats = {
            'requests_made': defaultdict(int),
            'requests_delayed': defaultdict(int),
            'total_delay_time': defaultdict(float),
            'rate_limit_hits': defaultdict(int)
        }
        
        self.request_history.clear()
        self.limit_hits.clear()
        self.current_delays.clear()
        
        logger.info(f"Reset rate limiting statistics for {self.platform}")


# Predefined rate limit configurations for common platforms
class PlatformRateLimits:
    """Predefined rate limit configurations for popular platforms."""
    
    @staticmethod
    def twitter() -> RateLimitConfig:
        """Twitter API v2 rate limits."""
        return RateLimitConfig(
            platform="twitter",
            global_limit=RateLimit(requests_per_minute=300),
            endpoint_limits={
                "POST /2/tweets": RateLimit(requests_per_minute=30),
                "DELETE /2/tweets": RateLimit(requests_per_minute=30),
                "GET /2/users/me": RateLimit(requests_per_minute=75),
                "PUT /1.1/account/update_profile": RateLimit(requests_per_hour=15)
            },
            operation_limits={
                "post_tweet": RateLimit(requests_per_minute=30),
                "update_profile": RateLimit(requests_per_hour=15),
                "upload_media": RateLimit(requests_per_minute=30)
            }
        )
    
    @staticmethod
    def bluesky() -> RateLimitConfig:
        """Bluesky AT Protocol rate limits."""
        return RateLimitConfig(
            platform="bluesky",
            global_limit=RateLimit(requests_per_minute=100),
            endpoint_limits={
                "POST /xrpc/com.atproto.repo.createRecord": RateLimit(requests_per_minute=30),
                "POST /xrpc/com.atproto.repo.deleteRecord": RateLimit(requests_per_minute=30),
                "POST /xrpc/com.atproto.repo.putRecord": RateLimit(requests_per_minute=30)
            }
        )
    
    @staticmethod
    def instagram() -> RateLimitConfig:
        """Instagram Basic Display API rate limits."""
        return RateLimitConfig(
            platform="instagram",
            global_limit=RateLimit(requests_per_hour=200),
            endpoint_limits={
                "POST /media": RateLimit(requests_per_hour=25),
                "POST /media_publish": RateLimit(requests_per_hour=25)
            }
        )
    
    @staticmethod
    def linkedin() -> RateLimitConfig:
        """LinkedIn API rate limits."""
        return RateLimitConfig(
            platform="linkedin",
            global_limit=RateLimit(requests_per_day=1000),
            endpoint_limits={
                "POST /v2/ugcPosts": RateLimit(requests_per_day=100),
                "POST /v2/assets": RateLimit(requests_per_day=100)
            }
        )
    
    @staticmethod
    def youtube() -> RateLimitConfig:
        """YouTube Data API v3 rate limits."""
        return RateLimitConfig(
            platform="youtube",
            global_limit=RateLimit(requests_per_day=10000),  # Quota units
            endpoint_limits={
                "POST /upload": RateLimit(requests_per_day=6),  # Video uploads
                "PUT /videos": RateLimit(requests_per_day=50)   # Video updates
            }
        )