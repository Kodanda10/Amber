"""Lightweight Facebook Graph API client."""
from __future__ import annotations

import os
from typing import Dict, List

import requests

GRAPH_API_BASE = os.getenv("FACEBOOK_GRAPH_API_BASE", "https://graph.facebook.com/v19.0")
GRAPH_TIMEOUT = int(os.getenv("FACEBOOK_GRAPH_TIMEOUT", "15"))

class FacebookGraphError(Exception):
    """Raised when the Graph API returns an unexpected response."""


def _access_token() -> str:
    token = os.getenv("FACEBOOK_GRAPH_TOKEN")
    if not token:
        raise FacebookGraphError("FACEBOOK_GRAPH_TOKEN is not configured")
    return token


def fetch_posts(handle: str, limit: int = 10) -> List[Dict]:
    """Fetch recent posts for a given Facebook page/profile handle.

    Parameters
    ----------
    handle: str
        Facebook handle (e.g. "@vishnudeosai1").
    limit: int
        Maximum number of posts to retrieve.
    """
    if not handle:
        return []
    token = _access_token()
    username = handle.lstrip("@")
    fields = (
        "id,message,created_time,full_picture,permalink_url,"\
        "attachments{data{media_type,media,url}},"\
        "from{name,picture{data{url}}}"
    )
    params = {
        "access_token": token,
        "fields": f"posts.limit({limit}){{{fields}}}",
    }
    response = requests.get(f"{GRAPH_API_BASE}/{username}", params=params, timeout=GRAPH_TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    return payload.get("posts", {}).get("data", [])
