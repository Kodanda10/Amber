# backend/x_client.py
"""
Twitter/X API v2 Client for fetching user timeline posts.
Supports bearer token authentication, pagination, and rate limit handling.
"""
from __future__ import annotations

import os
import time
from typing import Dict, List, Optional
from datetime import datetime

import requests


class XAPIError(Exception):
    """Base exception for X API errors."""
    pass


class XAPIAuthError(XAPIError):
    """Authentication error with X API."""
    pass


class XAPIRateLimitError(XAPIError):
    """Rate limit exceeded error."""
    def __init__(self, message: str, reset_at: Optional[int] = None):
        super().__init__(message)
        self.reset_at = reset_at


class XAPIClient:
    """
    Client for Twitter/X API v2.
    
    Handles:
    - Bearer token authentication
    - User timeline fetching
    - Pagination cursors
    - Rate limit backoff
    """
    
    BASE_URL = "https://api.twitter.com/2"
    
    def __init__(self, bearer_token: Optional[str] = None):
        """
        Initialize X API client.
        
        Args:
            bearer_token: Twitter API bearer token. If not provided, reads from TWITTER_BEARER_TOKEN env var.
        
        Raises:
            XAPIAuthError: If no bearer token is provided.
        """
        self.bearer_token = bearer_token or os.getenv("TWITTER_BEARER_TOKEN")
        if not self.bearer_token:
            raise XAPIAuthError("No bearer token provided. Set TWITTER_BEARER_TOKEN env var.")
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.bearer_token}",
            "User-Agent": "Amber-X-Client/1.0"
        })
    
    def fetch_user_timeline(
        self,
        username: str,
        max_results: int = 10,
        pagination_token: Optional[str] = None
    ) -> Dict:
        """
        Fetch recent posts from a user's timeline.
        
        Args:
            username: Twitter username (without @)
            max_results: Number of posts to fetch (5-100)
            pagination_token: Token for fetching next page
        
        Returns:
            Dictionary with structure:
            {
                "posts": [
                    {
                        "id": "post_id",
                        "text": "content",
                        "created_at": "ISO8601 timestamp",
                        "author": "username",
                        "media_urls": ["url1", "url2"],
                        "avatar": "profile_image_url"
                    }
                ],
                "next_token": "token_for_next_page" or None,
                "user_avatar": "profile_image_url"
            }
        
        Raises:
            XAPIAuthError: If authentication fails
            XAPIRateLimitError: If rate limit is exceeded
            XAPIError: For other API errors
        """
        # First, get user ID and avatar
        user_info = self._get_user_by_username(username)
        user_id = user_info["id"]
        user_avatar = user_info.get("profile_image_url")
        
        # Fetch timeline
        url = f"{self.BASE_URL}/users/{user_id}/tweets"
        params = {
            "max_results": min(max(max_results, 5), 100),
            "tweet.fields": "created_at,text,author_id",
            "expansions": "attachments.media_keys",
            "media.fields": "url,preview_image_url"
        }
        
        if pagination_token:
            params["pagination_token"] = pagination_token
        
        response = self._make_request("GET", url, params=params)
        
        # Parse response
        posts = []
        data = response.get("data", [])
        includes = response.get("includes", {})
        media_map = {}
        
        # Build media lookup map
        for media in includes.get("media", []):
            media_key = media.get("media_key")
            media_url = media.get("url") or media.get("preview_image_url")
            if media_key and media_url:
                media_map[media_key] = media_url
        
        for tweet in data:
            media_urls = []
            if "attachments" in tweet and "media_keys" in tweet["attachments"]:
                for key in tweet["attachments"]["media_keys"]:
                    if key in media_map:
                        media_urls.append(media_map[key])
            
            posts.append({
                "id": tweet["id"],
                "text": tweet.get("text", ""),
                "created_at": tweet.get("created_at"),
                "author": username,
                "media_urls": media_urls,
                "avatar": user_avatar
            })
        
        return {
            "posts": posts,
            "next_token": response.get("meta", {}).get("next_token"),
            "user_avatar": user_avatar
        }
    
    def _get_user_by_username(self, username: str) -> Dict:
        """
        Get user information by username.
        
        Args:
            username: Twitter username (without @)
        
        Returns:
            Dict with id and profile_image_url
        """
        url = f"{self.BASE_URL}/users/by/username/{username}"
        params = {
            "user.fields": "profile_image_url"
        }
        
        response = self._make_request("GET", url, params=params)
        return response.get("data", {})
    
    def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Dict:
        """
        Make HTTP request with error handling and rate limit backoff.
        
        Args:
            method: HTTP method
            url: Full URL
            params: Query parameters
            retry_count: Current retry attempt
        
        Returns:
            Parsed JSON response
        
        Raises:
            XAPIAuthError: For 401/403 errors
            XAPIRateLimitError: For 429 errors
            XAPIError: For other errors
        """
        try:
            response = self.session.request(method, url, params=params, timeout=30)
            
            # Handle rate limiting with exponential backoff
            if response.status_code == 429:
                reset_time = response.headers.get("x-rate-limit-reset")
                if retry_count < 3:
                    # Exponential backoff: 2^retry_count seconds
                    sleep_time = 2 ** retry_count
                    time.sleep(sleep_time)
                    return self._make_request(method, url, params, retry_count + 1)
                else:
                    raise XAPIRateLimitError(
                        "Rate limit exceeded",
                        reset_at=int(reset_time) if reset_time else None
                    )
            
            # Handle authentication errors
            if response.status_code in (401, 403):
                raise XAPIAuthError(f"Authentication failed: {response.text}")
            
            # Handle other errors
            if response.status_code >= 400:
                raise XAPIError(f"API error {response.status_code}: {response.text}")
            
            return response.json()
            
        except requests.RequestException as e:
            raise XAPIError(f"Request failed: {str(e)}")


def create_client(bearer_token: Optional[str] = None) -> XAPIClient:
    """
    Factory function to create X API client.
    
    Args:
        bearer_token: Optional bearer token. If not provided, uses env var.
    
    Returns:
        Configured XAPIClient instance
    """
    return XAPIClient(bearer_token)
