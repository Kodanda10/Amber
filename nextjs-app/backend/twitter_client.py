"""Lightweight Twitter/X API v2 client."""
from __future__ import annotations

import os
from typing import Dict, List

import requests

TWITTER_API_BASE = os.getenv("TWITTER_API_BASE", "https://api.twitter.com/2")
TWITTER_TIMEOUT = int(os.getenv("TWITTER_TIMEOUT", "15"))


class TwitterAPIError(Exception):
    """Raised when the Twitter API returns an unexpected response."""


def _bearer_token() -> str:
    token = os.getenv("TWITTER_BEARER_TOKEN")
    if not token:
        raise TwitterAPIError("TWITTER_BEARER_TOKEN is not configured")
    return token


def fetch_posts(handle: str, limit: int = 10) -> List[Dict]:
    """Fetch recent tweets for a given Twitter handle.

    Parameters
    ----------
    handle: str
        Twitter handle (e.g. "@narendramodi").
    limit: int
        Maximum number of tweets to retrieve.
    """
    if not handle:
        return []
    
    token = _bearer_token()
    username = handle.lstrip("@")
    
    # First, get the user ID from the username
    user_url = f"{TWITTER_API_BASE}/users/by/username/{username}"
    headers = {"Authorization": f"Bearer {token}"}
    
    user_response = requests.get(user_url, headers=headers, timeout=TWITTER_TIMEOUT)
    user_response.raise_for_status()
    user_data = user_response.json()
    
    if "data" not in user_data:
        return []
    
    user_id = user_data["data"]["id"]
    
    # Now fetch the user's tweets
    tweets_url = f"{TWITTER_API_BASE}/users/{user_id}/tweets"
    params = {
        "max_results": min(limit, 100),  # Twitter API max is 100
        "tweet.fields": "created_at,text,public_metrics,entities",
        "expansions": "attachments.media_keys,author_id",
        "media.fields": "url,preview_image_url,type",
        "user.fields": "name,username,profile_image_url",
    }
    
    tweets_response = requests.get(tweets_url, headers=headers, params=params, timeout=TWITTER_TIMEOUT)
    tweets_response.raise_for_status()
    tweets_data = tweets_response.json()
    
    posts = tweets_data.get("data", [])
    includes = tweets_data.get("includes", {})
    
    # Enrich posts with media and user info
    media_map = {}
    if "media" in includes:
        for media in includes["media"]:
            media_map[media["media_key"]] = media
    
    users_map = {}
    if "users" in includes:
        for user in includes["users"]:
            users_map[user["id"]] = user
    
    enriched_posts = []
    for post in posts:
        enriched = {**post}
        
        # Add media URLs if present
        if "attachments" in post and "media_keys" in post["attachments"]:
            media_keys = post["attachments"]["media_keys"]
            media_items = [media_map.get(key) for key in media_keys if key in media_map]
            if media_items:
                enriched["media"] = media_items
        
        # Add user info
        author_id = post.get("author_id")
        if author_id and author_id in users_map:
            enriched["author"] = users_map[author_id]
        
        enriched_posts.append(enriched)
    
    return enriched_posts
