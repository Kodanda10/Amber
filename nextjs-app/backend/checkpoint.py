# backend/checkpoint.py
"""
Checkpoint persistence for resumable ingestion.
Stores last processed cursor/tweet-id for each stream to enable resume-from-checkpoint functionality.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime


class CheckpointStore:
    """
    Abstract interface for checkpoint persistence.
    Allows pluggable backends (file, DB, Redis, etc.)
    """
    
    def get_checkpoint(self, stream_key: str) -> Optional[str]:
        """
        Retrieve the last checkpoint for a given stream.
        
        Args:
            stream_key: Unique identifier for the ingestion stream (e.g., "x:username")
        
        Returns:
            Last checkpoint value (cursor/tweet-id) or None if not found
        """
        raise NotImplementedError
    
    def set_checkpoint(self, stream_key: str, cursor: str) -> None:
        """
        Store a checkpoint for a given stream.
        
        Args:
            stream_key: Unique identifier for the ingestion stream
            cursor: Checkpoint value to store (cursor/tweet-id)
        """
        raise NotImplementedError
    
    def delete_checkpoint(self, stream_key: str) -> None:
        """
        Delete a checkpoint for a given stream.
        
        Args:
            stream_key: Unique identifier for the ingestion stream
        """
        raise NotImplementedError


class FileBackedCheckpointStore(CheckpointStore):
    """
    File-backed checkpoint storage.
    Simple implementation for development; consider DB-backed store for production.
    """
    
    def __init__(self, checkpoint_dir: Optional[str] = None):
        """
        Initialize file-backed checkpoint store.
        
        Args:
            checkpoint_dir: Directory to store checkpoint files. Defaults to ./checkpoints
        """
        self.checkpoint_dir = Path(checkpoint_dir or os.getenv("CHECKPOINT_DIR", "./checkpoints"))
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_file = self.checkpoint_dir / "ingestion_checkpoints.json"
        
        # Initialize checkpoint file if it doesn't exist
        if not self.checkpoint_file.exists():
            self._save_checkpoints({})
    
    def _load_checkpoints(self) -> Dict[str, Dict]:
        """Load all checkpoints from file."""
        try:
            with open(self.checkpoint_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _save_checkpoints(self, checkpoints: Dict[str, Dict]) -> None:
        """Save all checkpoints to file."""
        with open(self.checkpoint_file, "w") as f:
            json.dump(checkpoints, f, indent=2)
    
    def get_checkpoint(self, stream_key: str) -> Optional[str]:
        """Retrieve checkpoint for stream."""
        checkpoints = self._load_checkpoints()
        checkpoint_data = checkpoints.get(stream_key)
        if checkpoint_data:
            return checkpoint_data.get("cursor")
        return None
    
    def set_checkpoint(self, stream_key: str, cursor: str) -> None:
        """Store checkpoint for stream."""
        checkpoints = self._load_checkpoints()
        checkpoints[stream_key] = {
            "cursor": cursor,
            "updated_at": datetime.utcnow().isoformat(),
        }
        self._save_checkpoints(checkpoints)
    
    def delete_checkpoint(self, stream_key: str) -> None:
        """Delete checkpoint for stream."""
        checkpoints = self._load_checkpoints()
        if stream_key in checkpoints:
            del checkpoints[stream_key]
            self._save_checkpoints(checkpoints)


# Global checkpoint store instance
_checkpoint_store: Optional[CheckpointStore] = None


def get_checkpoint_store() -> CheckpointStore:
    """
    Get the global checkpoint store instance.
    Lazy initialization with file-backed store by default.
    
    TODO: Replace with DB-backed store for production (e.g., checkpoints table)
    """
    global _checkpoint_store
    if _checkpoint_store is None:
        _checkpoint_store = FileBackedCheckpointStore()
    return _checkpoint_store


def set_checkpoint_store(store: CheckpointStore) -> None:
    """
    Set custom checkpoint store (useful for testing or production DB-backed store).
    
    Args:
        store: CheckpointStore implementation to use
    """
    global _checkpoint_store
    _checkpoint_store = store
