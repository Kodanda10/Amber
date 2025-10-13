# backend/x_ingestion_service.py
"""
Production-ready X/Twitter ingestion service with:
- Retry/backoff logic
- Checkpoint-based resume
- Idempotent writes
- Dry-run mode
- Schema validation
- Metrics tracking
"""
from __future__ import annotations

import os
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from checkpoint import get_checkpoint_store
from http_retry_client import HTTPRetryClient
import x_client


class XIngestionService:
    """
    Production ingestion service for X/Twitter content.
    """
    
    def __init__(
        self,
        bearer_token: Optional[str] = None,
        dry_run: bool = False,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize X ingestion service.
        
        Args:
            bearer_token: Twitter API bearer token
            dry_run: If True, fetch and validate but don't persist
            logger: Optional logger instance
        """
        self.bearer_token = bearer_token or os.getenv("TWITTER_BEARER_TOKEN") or os.getenv("X_API_BEARER")
        self.dry_run = dry_run or os.getenv("INGESTION_DRY_RUN", "false").lower() in {"1", "true", "yes"}
        self.logger = logger or logging.getLogger(__name__)
        self.checkpoint_store = get_checkpoint_store()
        
        # Metrics
        self.metrics = {
            "processed": 0,
            "failed": 0,
            "rate_limited": 0,
            "skipped_duplicates": 0,
        }
    
    def ingest_for_user(
        self,
        username: str,
        max_results: int = 10,
        use_checkpoint: bool = True,
    ) -> Tuple[List[Dict], Dict]:
        """
        Ingest posts for a specific X/Twitter user.
        
        Args:
            username: Twitter username (without @)
            max_results: Maximum number of posts to fetch
            use_checkpoint: Whether to use checkpoint for resume
        
        Returns:
            Tuple of (posts list, metadata dict with next_token and metrics)
        """
        stream_key = f"x:{username}"
        
        # Get checkpoint if resume is enabled
        pagination_token = None
        if use_checkpoint:
            pagination_token = self.checkpoint_store.get_checkpoint(stream_key)
            if pagination_token:
                self.logger.info(
                    "Resuming ingestion for %s from checkpoint: %s",
                    username,
                    pagination_token[:20] + "..." if len(pagination_token) > 20 else pagination_token
                )
        
        try:
            # Create X client and fetch timeline
            client = x_client.create_client(self.bearer_token)
            result = client.fetch_user_timeline(
                username=username,
                max_results=max_results,
                pagination_token=pagination_token
            )
            
            posts = result.get("posts", [])
            next_token = result.get("next_token")
            
            # Validate posts
            validated_posts = []
            for post in posts:
                if self._validate_post_schema(post):
                    validated_posts.append(post)
                    self.metrics["processed"] += 1
                else:
                    self.logger.warning("Invalid post schema for post_id=%s", post.get("id"))
                    self.metrics["failed"] += 1
            
            # Save checkpoint if we have a next token
            if use_checkpoint and next_token:
                if not self.dry_run:
                    self.checkpoint_store.set_checkpoint(stream_key, next_token)
                self.logger.info("Saved checkpoint for %s: %s", username, next_token[:20] + "...")
            
            metadata = {
                "next_token": next_token,
                "user_avatar": result.get("user_avatar"),
                "metrics": self.metrics.copy(),
                "dry_run": self.dry_run,
            }
            
            if self.dry_run:
                self.logger.info(
                    "DRY RUN: Would have ingested %d posts for %s",
                    len(validated_posts),
                    username
                )
            
            return validated_posts, metadata
            
        except x_client.XAPIRateLimitError as e:
            self.metrics["rate_limited"] += 1
            self.logger.warning(
                "Rate limited while fetching posts for %s: %s",
                username,
                str(e)
            )
            raise
        except x_client.XAPIError as e:
            self.metrics["failed"] += 1
            self.logger.error(
                "Error fetching posts for %s: %s",
                username,
                str(e)
            )
            raise
    
    def _validate_post_schema(self, post: Dict) -> bool:
        """
        Validate that post has required fields.
        
        Args:
            post: Post dictionary from X API
        
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["id", "text", "created_at", "author"]
        
        for field in required_fields:
            if field not in post:
                return False
        
        # Validate types
        if not isinstance(post["id"], str):
            return False
        if not isinstance(post["text"], str):
            return False
        if not isinstance(post["author"], str):
            return False
        
        return True
    
    def reset_checkpoint(self, username: str) -> None:
        """
        Reset checkpoint for a user (start from beginning).
        
        Args:
            username: Twitter username
        """
        stream_key = f"x:{username}"
        self.checkpoint_store.delete_checkpoint(stream_key)
        self.logger.info("Reset checkpoint for %s", username)
    
    def get_metrics(self) -> Dict:
        """Get current ingestion metrics."""
        return self.metrics.copy()
