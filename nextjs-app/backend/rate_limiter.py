# backend/rate_limiter.py
"""
Redis-backed token bucket rate limiter for production-ready rate limiting.
Supports IP-based and user-identity-based rate limiting with horizontal scalability.
"""
from __future__ import annotations

import os
import time
import logging
from typing import Optional, Tuple
from functools import wraps

from flask import request, jsonify, g
import redis

logger = logging.getLogger(__name__)

# Configuration from environment variables
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REQUESTS_PER_MINUTE = int(os.getenv("REQUESTS_PER_MINUTE", "60"))
BURST_SIZE = int(os.getenv("BURST_SIZE", str(REQUESTS_PER_MINUTE)))
WINDOW_SECONDS = int(os.getenv("WINDOW_SECONDS", "60"))

# Enable/disable rate limiting (can be disabled in testing)
RATE_LIMITING_ENABLED = os.getenv("RATE_LIMITING_ENABLED", "true").lower() in {"1", "true", "yes", "on"}


class RateLimiter:
    """
    Token bucket rate limiter backed by Redis for distributed rate limiting.
    
    Uses the token bucket algorithm:
    - Tokens are added at a constant rate (REQUESTS_PER_MINUTE / WINDOW_SECONDS)
    - Each request consumes one token
    - If no tokens available, request is rate limited
    - Supports bursts up to BURST_SIZE tokens
    """
    
    def __init__(self, redis_url: str = REDIS_URL):
        """
        Initialize rate limiter with Redis connection.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self._redis_client: Optional[redis.Redis] = None
        self.tokens_per_second = REQUESTS_PER_MINUTE / WINDOW_SECONDS
        self.burst_size = BURST_SIZE
        self.window_seconds = WINDOW_SECONDS
    
    @property
    def redis_client(self) -> redis.Redis:
        """Lazy initialization of Redis client with connection pooling."""
        if self._redis_client is None:
            try:
                self._redis_client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2,
                    retry_on_timeout=True,
                    max_connections=50,
                )
                # Test connection
                self._redis_client.ping()
                logger.info("Redis connection established for rate limiting")
            except (redis.ConnectionError, redis.TimeoutError) as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise
        return self._redis_client
    
    def _get_rate_limit_key(self, identifier: str, key_type: str = "ip") -> str:
        """
        Generate Redis key for rate limiting.
        
        Args:
            identifier: IP address or user ID
            key_type: Type of key ('ip' or 'user')
        
        Returns:
            Redis key string
        """
        return f"rate_limit:{key_type}:{identifier}"
    
    def check_rate_limit(
        self, 
        identifier: str, 
        key_type: str = "ip",
        cost: int = 1
    ) -> Tuple[bool, Optional[int]]:
        """
        Check if request should be rate limited using token bucket algorithm.
        
        Args:
            identifier: IP address or user ID
            key_type: Type of key ('ip' or 'user')
            cost: Number of tokens to consume (default 1)
        
        Returns:
            Tuple of (allowed, retry_after_seconds)
            - allowed: True if request is allowed, False if rate limited
            - retry_after_seconds: Seconds to wait before retrying (None if allowed)
        """
        if not RATE_LIMITING_ENABLED:
            return True, None
        
        key = self._get_rate_limit_key(identifier, key_type)
        now = time.time()
        
        try:
            # Use pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            
            # Get current state
            pipe.hget(key, 'tokens')
            pipe.hget(key, 'last_update')
            result = pipe.execute()
            
            tokens = float(result[0]) if result[0] else self.burst_size
            last_update = float(result[1]) if result[1] else now
            
            # Calculate tokens to add based on time elapsed
            time_elapsed = now - last_update
            tokens_to_add = time_elapsed * self.tokens_per_second
            tokens = min(self.burst_size, tokens + tokens_to_add)
            
            # Check if we have enough tokens
            if tokens >= cost:
                # Consume tokens
                tokens = tokens - cost
                pipe = self.redis_client.pipeline()
                pipe.hset(key, 'tokens', tokens)
                pipe.hset(key, 'last_update', now)
                pipe.expire(key, self.window_seconds * 2)
                pipe.execute()
                return True, None
            else:
                # Rate limited - calculate retry_after
                tokens_needed = cost - tokens
                retry_after = int(tokens_needed / self.tokens_per_second) + 1
                
                logger.warning(
                    f"Rate limit exceeded for {key_type}={identifier}, "
                    f"retry_after={retry_after}s"
                )
                return False, retry_after
            
        except redis.RedisError as e:
            logger.error(f"Redis error in rate limiting: {e}")
            # Fail open - allow request if Redis is down
            return True, None
    
    def get_current_limits(self, identifier: str, key_type: str = "ip") -> dict:
        """
        Get current rate limit status for debugging/monitoring.
        
        Args:
            identifier: IP address or user ID
            key_type: Type of key ('ip' or 'user')
        
        Returns:
            Dictionary with current rate limit status
        """
        key = self._get_rate_limit_key(identifier, key_type)
        
        try:
            state = self.redis_client.hmget(key, 'tokens', 'last_update')
            tokens = float(state[0]) if state[0] else self.burst_size
            last_update = float(state[1]) if state[1] else time.time()
            
            return {
                "tokens_available": tokens,
                "last_update": last_update,
                "tokens_per_second": self.tokens_per_second,
                "burst_size": self.burst_size,
            }
        except redis.RedisError as e:
            logger.error(f"Redis error getting rate limit status: {e}")
            return {}


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def rate_limit(key_type: str = "ip", cost: int = 1):
    """
    Decorator to apply rate limiting to Flask routes.
    
    Args:
        key_type: Type of rate limiting ('ip' or 'user')
        cost: Number of tokens to consume (default 1)
    
    Returns:
        Decorated function that enforces rate limiting
    
    Example:
        @app.route('/api/resource')
        @rate_limit(key_type='ip', cost=1)
        def my_endpoint():
            return jsonify({"status": "ok"})
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not RATE_LIMITING_ENABLED:
                return func(*args, **kwargs)
            
            # Determine identifier based on key_type
            if key_type == "user":
                # Check if user is authenticated
                auth_payload = getattr(g, 'auth_payload', None)
                if auth_payload:
                    identifier = auth_payload.get('sub', '')
                    if not identifier:
                        # Fall back to IP if no user ID
                        identifier = request.remote_addr or "unknown"
                        actual_key_type = "ip"
                    else:
                        actual_key_type = "user"
                else:
                    # Not authenticated, use IP
                    identifier = request.remote_addr or "unknown"
                    actual_key_type = "ip"
            else:
                # IP-based rate limiting
                identifier = request.remote_addr or "unknown"
                actual_key_type = "ip"
            
            # Check rate limit
            limiter = get_rate_limiter()
            allowed, retry_after = limiter.check_rate_limit(
                identifier, 
                actual_key_type, 
                cost
            )
            
            if not allowed:
                response = jsonify({
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": retry_after,
                })
                response.status_code = 429
                if retry_after:
                    response.headers['Retry-After'] = str(retry_after)
                response.headers['X-RateLimit-Limit'] = str(REQUESTS_PER_MINUTE)
                response.headers['X-RateLimit-Remaining'] = '0'
                response.headers['X-RateLimit-Reset'] = str(int(time.time()) + retry_after)
                
                # Log rate limit event for monitoring
                logger.warning(
                    f"Rate limit exceeded: {actual_key_type}={identifier}, "
                    f"endpoint={request.endpoint}, retry_after={retry_after}s",
                    extra={
                        "rate_limit_exceeded": True,
                        "identifier": identifier,
                        "key_type": actual_key_type,
                        "endpoint": request.endpoint,
                        "retry_after": retry_after,
                    }
                )
                
                return response
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator
