"""
Tests for X/Twitter Ingestion Service Integration (ING-012)
Tests the ingest_x_posts function and integration with X API client.
"""
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("X_INGEST_ENABLED", "true")

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import importlib
app_module = importlib.import_module("app")
app = app_module.app
Leader = app_module.Leader
Post = app_module.Post

with app.app_context():
    app_module.init_db()


@pytest.fixture(autouse=True)
def reset_db():
    """Reset database for each test."""
    with app.app_context():
        app_module.db.drop_all()
        app_module.db.create_all()
        if hasattr(app_module, "ensure_post_schema"):
            app_module.ensure_post_schema()
        yield
        app_module.db.session.remove()


def test_ingest_x_posts_creates_records():
    """Test that ingest_x_posts creates Post records from X API data."""
    # Create a leader with X handle
    with app.app_context():
        leader = Leader(
            id="test-leader-1",
            name="Test Leader",
            handles={"x": "testleader"},
            tracking_topics=["test"]
        )
        app_module.db.session.add(leader)
        app_module.db.session.commit()
        
        # Mock X API client to return sample posts
        mock_x_data = {
            "posts": [
                {
                    "id": "x_tweet_123",
                    "text": "Test tweet from X",
                    "created_at": "2025-10-11T12:00:00Z",
                    "author": "testleader",
                    "media_urls": [],
                    "avatar": "https://example.com/avatar.jpg"
                }
            ],
            "next_token": None,
            "user_avatar": "https://example.com/avatar.jpg"
        }
        
        # Mock the create_client function to return a mock client
        mock_client = Mock()
        mock_client.fetch_user_timeline.return_value = mock_x_data
        
        with patch('app.x_client.create_client', return_value=mock_client):
            # Call ingestion function
            posts = app_module.ingest_x_posts(leader.id)
        
        # Verify post was created
        assert len(posts) == 1
        assert posts[0]["content"] == "Test tweet from X"
        assert posts[0]["platform"] == "X"
        
        # Verify database record
        db_post = Post.query.filter_by(leader_id=leader.id).first()
        assert db_post is not None
        assert db_post.content == "Test tweet from X"
        assert db_post.platform == "X"


def test_deduplication_by_external_id():
    """Test that posts are deduplicated by external_id (X tweet ID)."""
    with app.app_context():
        leader = Leader(
            id="test-leader-2",
            name="Test Leader",
            handles={"x": "testleader"},
            tracking_topics=["test"]
        )
        app_module.db.session.add(leader)
        app_module.db.session.commit()
        
        # Create existing post with same X ID
        existing_post = Post(
            id="existing-post-1",
            leader_id=leader.id,
            platform="X",
            content="Old tweet content",
            timestamp=app_module.datetime.utcnow(),
            sentiment="Neutral",
            metrics={"externalId": "x_tweet_123", "origin": "x"}
        )
        app_module.db.session.add(existing_post)
        app_module.db.session.commit()
        
        # Mock X API to return post with same ID but different content
        mock_x_data = {
            "posts": [
                {
                    "id": "x_tweet_123",  # Same ID as existing post
                    "text": "Updated tweet content",
                    "created_at": "2025-10-11T12:00:00Z",
                    "author": "testleader",
                    "media_urls": [],
                    "avatar": "https://example.com/avatar.jpg"
                }
            ],
            "next_token": None,
            "user_avatar": "https://example.com/avatar.jpg"
        }
        
        mock_client = Mock()
        mock_client.fetch_user_timeline.return_value = mock_x_data
        
        with patch('app.x_client.create_client', return_value=mock_client):
            posts = app_module.ingest_x_posts(leader.id)
        
        # Should not create duplicate - should return existing post
        all_posts = Post.query.filter_by(leader_id=leader.id).all()
        assert len(all_posts) == 1
        # Content should be unchanged (no update on existing)
        assert all_posts[0].content == "Old tweet content"


def test_origin_field_set_to_x():
    """Test that posts from X have origin='x' in metrics."""
    with app.app_context():
        leader = Leader(
            id="test-leader-3",
            name="Test Leader",
            handles={"x": "testleader"},
            tracking_topics=["test"]
        )
        app_module.db.session.add(leader)
        app_module.db.session.commit()
        
        mock_x_data = {
            "posts": [
                {
                    "id": "x_tweet_456",
                    "text": "Another test tweet",
                    "created_at": "2025-10-11T12:00:00Z",
                    "author": "testleader",
                    "media_urls": [],
                    "avatar": "https://example.com/avatar.jpg"
                }
            ],
            "next_token": None,
            "user_avatar": "https://example.com/avatar.jpg"
        }
        
        mock_client = Mock()
        mock_client.fetch_user_timeline.return_value = mock_x_data
        
        with patch('app.x_client.create_client', return_value=mock_client):
            posts = app_module.ingest_x_posts(leader.id)
        
        # Check metrics have origin='x'
        assert posts[0]["metrics"]["origin"] == "x"
        
        # Check database
        db_post = Post.query.filter_by(leader_id=leader.id).first()
        assert db_post.metrics["origin"] == "x"


def test_media_urls_persisted():
    """Test that media URLs from X posts are persisted in metrics."""
    with app.app_context():
        leader = Leader(
            id="test-leader-4",
            name="Test Leader",
            handles={"x": "testleader"},
            tracking_topics=["test"]
        )
        app_module.db.session.add(leader)
        app_module.db.session.commit()
        
        mock_x_data = {
            "posts": [
                {
                    "id": "x_tweet_789",
                    "text": "Tweet with photo",
                    "created_at": "2025-10-11T12:00:00Z",
                    "author": "testleader",
                    "media_urls": [
                        "https://pbs.twimg.com/media/photo1.jpg",
                        "https://pbs.twimg.com/media/photo2.jpg"
                    ],
                    "avatar": "https://example.com/avatar.jpg"
                }
            ],
            "next_token": None,
            "user_avatar": "https://example.com/avatar.jpg"
        }
        
        mock_client = Mock()
        mock_client.fetch_user_timeline.return_value = mock_x_data
        
        with patch('app.x_client.create_client', return_value=mock_client):
            posts = app_module.ingest_x_posts(leader.id)
        
        # Check media URLs are in metrics
        assert "mediaUrl" in posts[0]["metrics"]
        assert posts[0]["metrics"]["mediaUrl"] == "https://pbs.twimg.com/media/photo1.jpg"
        
        # Check avatarUrl is persisted
        assert "avatarUrl" in posts[0]["metrics"]
        assert posts[0]["metrics"]["avatarUrl"] == "https://example.com/avatar.jpg"


def test_ingest_x_posts_skips_if_no_x_handle():
    """Test that ingestion skips leaders without X handles."""
    with app.app_context():
        leader = Leader(
            id="test-leader-5",
            name="Test Leader",
            handles={"facebook": "@testleader"},  # No X handle
            tracking_topics=["test"]
        )
        app_module.db.session.add(leader)
        app_module.db.session.commit()
        
        # Should return empty list without calling X API
        mock_client = Mock()
        with patch('app.x_client.create_client', return_value=mock_client):
            posts = app_module.ingest_x_posts(leader.id)
            
            # Should not have called X API
            mock_client.fetch_user_timeline.assert_not_called()
            assert len(posts) == 0


def test_ingest_x_posts_handles_api_errors():
    """Test that ingestion handles X API errors gracefully."""
    with app.app_context():
        leader = Leader(
            id="test-leader-6",
            name="Test Leader",
            handles={"x": "testleader"},
            tracking_topics=["test"]
        )
        app_module.db.session.add(leader)
        app_module.db.session.commit()
        
        # Mock X API to raise an error
        mock_client = Mock()
        mock_client.fetch_user_timeline.side_effect = Exception("API Error")
        
        with patch('app.x_client.create_client', return_value=mock_client):
            posts = app_module.ingest_x_posts(leader.id)
            
            # Should return empty list, not crash
            assert len(posts) == 0
            assert Post.query.filter_by(leader_id=leader.id).count() == 0
