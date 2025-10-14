# backend/rate_limiter.py
"""
Simple in-memory rate limiter for API endpoints.
Suitable for development; consider Redis-backed limiter for production.
"""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict, Optional
from threading import Lock


class RateLimiter:
    """
    Token bucket rate limiter with per-key tracking.
    """
    
    def __init__(
        self,
        max_requests: int = 60,
        window_seconds: int = 60,
    ):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum number of requests per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = Lock()
    
    def is_allowed(self, key: str) -> bool:
        """
        Check if request is allowed for the given key.
        
        Args:
            key: Rate limit key (e.g., IP address, API key, user ID)
        
        Returns:
            True if request is allowed, False if rate limited
        """
        with self.lock:
            now = time.time()
            cutoff = now - self.window_seconds
            
            # Remove old requests outside the window
            if key in self.requests:
                self.requests[key] = [
                    timestamp for timestamp in self.requests[key]
                    if timestamp > cutoff
                ]
            
            # Check if under limit
            if len(self.requests[key]) >= self.max_requests:
                return False
            
            # Add current request
            self.requests[key].append(now)
            return True
    
    def get_remaining(self, key: str) -> int:
        """
        Get remaining requests for key in current window.
        
        Args:
            key: Rate limit key
        
        Returns:
            Number of remaining requests
        """
        with self.lock:
            now = time.time()
            cutoff = now - self.window_seconds
            
            # Count recent requests
            if key in self.requests:
                recent = sum(1 for ts in self.requests[key] if ts > cutoff)
                return max(0, self.max_requests - recent)
            
            return self.max_requests
    
    def reset(self, key: str) -> None:
        """
        Reset rate limit for key.
        
        Args:
            key: Rate limit key
        """
        with self.lock:
            if key in self.requests:
                del self.requests[key]
    
    def cleanup_old_entries(self, max_age_seconds: int = 3600) -> None:
        """
        Remove old entries to prevent memory bloat.
        
        Args:
            max_age_seconds: Remove entries older than this
        """
        with self.lock:
            now = time.time()
            cutoff = now - max_age_seconds
            
            keys_to_remove = []
            for key, timestamps in self.requests.items():
                if not timestamps or max(timestamps) < cutoff:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.requests[key]
