"""
Unit tests for checkpoint persistence module.
Tests checkpoint read/write operations and file-backed store.
"""
import os
import sys
import tempfile
import json
from pathlib import Path

import pytest

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from checkpoint import FileBackedCheckpointStore, get_checkpoint_store, set_checkpoint_store


class TestFileBackedCheckpointStore:
    """Tests for file-backed checkpoint storage."""
    
    def test_checkpoint_store_initialization(self):
        """Test that checkpoint store initializes with directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileBackedCheckpointStore(tmpdir)
            assert store.checkpoint_dir == Path(tmpdir)
            assert store.checkpoint_file.exists()
    
    def test_set_and_get_checkpoint(self):
        """Test basic set and get operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileBackedCheckpointStore(tmpdir)
            
            # Set checkpoint
            store.set_checkpoint("x:testuser", "cursor_12345")
            
            # Get checkpoint
            cursor = store.get_checkpoint("x:testuser")
            assert cursor == "cursor_12345"
    
    def test_get_nonexistent_checkpoint(self):
        """Test getting checkpoint that doesn't exist returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileBackedCheckpointStore(tmpdir)
            cursor = store.get_checkpoint("x:nonexistent")
            assert cursor is None
    
    def test_update_checkpoint(self):
        """Test updating existing checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileBackedCheckpointStore(tmpdir)
            
            # Set initial checkpoint
            store.set_checkpoint("x:user1", "cursor_1")
            assert store.get_checkpoint("x:user1") == "cursor_1"
            
            # Update checkpoint
            store.set_checkpoint("x:user1", "cursor_2")
            assert store.get_checkpoint("x:user1") == "cursor_2"
    
    def test_delete_checkpoint(self):
        """Test deleting checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileBackedCheckpointStore(tmpdir)
            
            # Set checkpoint
            store.set_checkpoint("x:user1", "cursor_1")
            assert store.get_checkpoint("x:user1") == "cursor_1"
            
            # Delete checkpoint
            store.delete_checkpoint("x:user1")
            assert store.get_checkpoint("x:user1") is None
    
    def test_multiple_checkpoints(self):
        """Test storing multiple checkpoints for different streams."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileBackedCheckpointStore(tmpdir)
            
            # Set multiple checkpoints
            store.set_checkpoint("x:user1", "cursor_1")
            store.set_checkpoint("x:user2", "cursor_2")
            store.set_checkpoint("fb:page1", "token_123")
            
            # Verify all checkpoints
            assert store.get_checkpoint("x:user1") == "cursor_1"
            assert store.get_checkpoint("x:user2") == "cursor_2"
            assert store.get_checkpoint("fb:page1") == "token_123"
    
    def test_checkpoint_persistence(self):
        """Test that checkpoints persist across store instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create first store and set checkpoint
            store1 = FileBackedCheckpointStore(tmpdir)
            store1.set_checkpoint("x:user1", "cursor_persistent")
            
            # Create second store with same directory
            store2 = FileBackedCheckpointStore(tmpdir)
            cursor = store2.get_checkpoint("x:user1")
            assert cursor == "cursor_persistent"
    
    def test_checkpoint_file_format(self):
        """Test that checkpoint file has correct JSON format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileBackedCheckpointStore(tmpdir)
            store.set_checkpoint("x:user1", "cursor_1")
            
            # Read file directly
            with open(store.checkpoint_file, "r") as f:
                data = json.load(f)
            
            assert "x:user1" in data
            assert data["x:user1"]["cursor"] == "cursor_1"
            assert "updated_at" in data["x:user1"]


class TestGlobalCheckpointStore:
    """Tests for global checkpoint store singleton."""
    
    def test_get_checkpoint_store_returns_instance(self):
        """Test that get_checkpoint_store returns a store instance."""
        store = get_checkpoint_store()
        assert store is not None
    
    def test_set_custom_checkpoint_store(self):
        """Test setting custom checkpoint store."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_store = FileBackedCheckpointStore(tmpdir)
            set_checkpoint_store(custom_store)
            
            retrieved_store = get_checkpoint_store()
            assert retrieved_store == custom_store
    
    def test_checkpoint_store_is_singleton(self):
        """Test that get_checkpoint_store returns same instance."""
        store1 = get_checkpoint_store()
        store2 = get_checkpoint_store()
        assert store1 is store2
