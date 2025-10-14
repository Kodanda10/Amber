# backend/http_retry_client.py
"""
HTTP client with exponential backoff, jitter, and retry-after support.
Production-ready retry logic for handling transient errors and rate limits.
"""
from __future__ import annotations

import random
import time
from typing import Dict, Optional, Callable
import requests
import logging


class HTTPRetryClient:
    """
    HTTP client wrapper with production-grade retry logic.
    
    Features:
    - Exponential backoff with full jitter
    - Retry-After header support for 429 responses
    - Configurable retry count and base delay
    - Request/response hooks for logging and metrics
    """
    
    def __init__(
        self,
        base_delay_ms: int = 500,
        max_delay_ms: int = 60000,
        backoff_factor: float = 2.0,
        max_retries: int = 6,
        session: Optional[requests.Session] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize HTTP retry client.
        
        Args:
            base_delay_ms: Base delay in milliseconds (default: 500ms)
            max_delay_ms: Maximum delay in milliseconds (default: 60s)
            backoff_factor: Exponential backoff factor (default: 2.0)
            max_retries: Maximum number of retry attempts (default: 6)
            session: Optional requests.Session to use
            logger: Optional logger for structured logging
        """
        self.base_delay_ms = base_delay_ms
        self.max_delay_ms = max_delay_ms
        self.backoff_factor = backoff_factor
        self.max_retries = max_retries
        self.session = session or requests.Session()
        self.logger = logger or logging.getLogger(__name__)
    
    def request(
        self,
        method: str,
        url: str,
        retry_on_status: Optional[set] = None,
        on_retry: Optional[Callable] = None,
        **kwargs
    ) -> requests.Response:
        """
        Make HTTP request with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            retry_on_status: Set of status codes to retry on (default: {429, 500, 502, 503, 504})
            on_retry: Optional callback called on each retry attempt
            **kwargs: Additional arguments passed to requests
        
        Returns:
            requests.Response object
        
        Raises:
            requests.RequestException: If max retries exceeded or non-retryable error
        """
        if retry_on_status is None:
            retry_on_status = {429, 500, 502, 503, 504}
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(method, url, **kwargs)
                
                # If status is retryable, handle backoff
                if response.status_code in retry_on_status:
                    if attempt >= self.max_retries:
                        # Max retries reached
                        self.logger.warning(
                            "Max retries reached for %s %s, status=%d",
                            method,
                            url,
                            response.status_code
                        )
                        return response
                    
                    # Calculate delay with exponential backoff and jitter
                    delay_ms = self._calculate_delay(
                        attempt,
                        response.status_code,
                        response.headers
                    )
                    
                    self.logger.info(
                        "Retrying %s %s (attempt %d/%d) after %dms, status=%d",
                        method,
                        url,
                        attempt + 1,
                        self.max_retries,
                        delay_ms,
                        response.status_code
                    )
                    
                    if on_retry:
                        on_retry(attempt, delay_ms, response)
                    
                    time.sleep(delay_ms / 1000.0)
                    continue
                
                # Success or non-retryable error
                return response
                
            except requests.RequestException as e:
                last_exception = e
                
                if attempt >= self.max_retries:
                    self.logger.error(
                        "Max retries reached for %s %s: %s",
                        method,
                        url,
                        str(e)
                    )
                    raise
                
                delay_ms = self._calculate_delay(attempt, None, {})
                
                self.logger.info(
                    "Retrying %s %s (attempt %d/%d) after %dms due to exception: %s",
                    method,
                    url,
                    attempt + 1,
                    self.max_retries,
                    delay_ms,
                    str(e)
                )
                
                if on_retry:
                    on_retry(attempt, delay_ms, None)
                
                time.sleep(delay_ms / 1000.0)
        
        # Should not reach here, but raise last exception if we do
        if last_exception:
            raise last_exception
        
        raise requests.RequestException("Max retries exceeded")
    
    def _calculate_delay(
        self,
        attempt: int,
        status_code: Optional[int],
        headers: Dict[str, str]
    ) -> int:
        """
        Calculate delay for next retry with exponential backoff and jitter.
        
        Args:
            attempt: Current attempt number (0-indexed)
            status_code: HTTP status code (if available)
            headers: Response headers
        
        Returns:
            Delay in milliseconds
        """
        # Check for Retry-After header (used by rate limiting)
        if status_code == 429:
            retry_after = headers.get("Retry-After") or headers.get("retry-after")
            if retry_after:
                try:
                    # Retry-After can be in seconds or HTTP-date format
                    # We'll assume seconds for simplicity
                    retry_after_seconds = int(retry_after)
                    return min(retry_after_seconds * 1000, self.max_delay_ms)
                except (ValueError, TypeError):
                    pass
        
        # Calculate exponential backoff with full jitter
        # Formula: random(0, min(max_delay, base_delay * (backoff_factor ^ attempt)))
        exponential_delay = self.base_delay_ms * (self.backoff_factor ** attempt)
        max_delay = min(exponential_delay, self.max_delay_ms)
        
        # Full jitter: random delay between 0 and max_delay
        return int(random.uniform(0, max_delay))
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """Convenience method for GET requests."""
        return self.request("GET", url, **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        """Convenience method for POST requests."""
        return self.request("POST", url, **kwargs)
    
    def put(self, url: str, **kwargs) -> requests.Response:
        """Convenience method for PUT requests."""
        return self.request("PUT", url, **kwargs)
    
    def delete(self, url: str, **kwargs) -> requests.Response:
        """Convenience method for DELETE requests."""
        return self.request("DELETE", url, **kwargs)
