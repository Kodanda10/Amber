"""Test Twitter/X ingestion functionality (ING-015)."""
import os
import importlib
import sys
from datetime import datetime
from pathlib import Path
import uuid

import pytest


os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("TWITTER_ENABLED", "1")
os.environ.setdefault("TWITTER_LIMIT", "10")

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

app_module = importlib.import_module("app")
app = app_module.app
Leader = app_module.Leader
Post = app_module.Post
_sync_posts_for_leader = app_module._sync_posts_for_leader


@pytest.fixture(autouse=True)
def reset_db():
    with app.app_context():
        app_module.db.drop_all()
        app_module.db.create_all()
        if hasattr(app_module, "ensure_post_schema"):
            app_module.ensure_post_schema()
        yield
        app_module.db.session.remove()

def test_twitter_ingestion_persists_posts(monkeypatch):
    """Test that Twitter posts are persisted with correct platform and metrics (ING-015)."""
    # Ensure Twitter is enabled for this test
    monkeypatch.setattr(app_module, "TWITTER_ENABLED", True)
    
    with app.app_context():
        leader = Leader(
            id=str(uuid.uuid4()),
            name="Twitter Leader",
            handles={"twitter": "@testleader"},
            tracking_topics=["policy", "governance"],
        )
        app_module.db.session.add(leader)
        app_module.db.session.commit()

        fake_tweets = [
            {
                "id": "1234567890",
                "text": "This is a sample tweet from a political leader.",
                "created_at": "2024-10-10T10:00:00.000Z",
                "author_id": "987654321",
                "public_metrics": {
                    "like_count": 150,
                    "retweet_count": 30,
                    "reply_count": 10,
                    "quote_count": 5,
                },
                "author": {
                    "id": "987654321",
                    "name": "Twitter Leader",
                    "username": "testleader",
                    "profile_image_url": "https://pbs.twimg.com/profile_images/test.jpg",
                },
            },
            {
                "id": "1234567891",
                "text": "Another important announcement about public policy.",
                "created_at": "2024-10-11T12:00:00.000Z",
                "author_id": "987654321",
                "public_metrics": {
                    "like_count": 200,
                    "retweet_count": 45,
                    "reply_count": 15,
                    "quote_count": 8,
                },
                "author": {
                    "id": "987654321",
                    "name": "Twitter Leader",
                    "username": "testleader",
                    "profile_image_url": "https://pbs.twimg.com/profile_images/test.jpg",
                },
            },
        ]

        def fake_fetch_posts(handle: str, limit: int):
            return fake_tweets

        monkeypatch.setattr("twitter_client.fetch_posts", fake_fetch_posts)

        posts, origin = _sync_posts_for_leader(leader)
        app_module.db.session.commit()

        assert origin == "twitter"
        assert len(posts) >= 1
        
        post_dict = posts[0]
        assert post_dict["platform"] == "Twitter"
        assert post_dict["content"] in [
            "This is a sample tweet from a political leader.",
            "Another important announcement about public policy.",
        ]
        assert post_dict["metrics"]["origin"] == "twitter"
        assert "platformPostId" in post_dict["metrics"]
        assert post_dict["metrics"]["platformPostId"] in {"1234567890", "1234567891"}
        assert post_dict["metrics"]["likes"] > 0
        assert "link" in post_dict["metrics"]
        assert post_dict["metrics"]["link"].startswith("https://twitter.com/")


def test_twitter_ingestion_with_media(monkeypatch):
    """Test that Twitter posts with media are persisted correctly (ING-015)."""
    # Ensure Twitter is enabled for this test
    monkeypatch.setattr(app_module, "TWITTER_ENABLED", True)
    
    with app.app_context():
        leader = Leader(
            id=str(uuid.uuid4()),
            name="Media Test Leader",
            handles={"twitter": "@testleader"},
            tracking_topics=["media"],
        )
        app_module.db.session.add(leader)
        app_module.db.session.commit()

        fake_tweets = [
            {
                "id": "1234567891",
                "text": "Tweet with media attachment.",
                "created_at": "2024-10-11T12:00:00.000Z",
                "author_id": "987654321",
                "public_metrics": {
                    "like_count": 200,
                    "retweet_count": 45,
                    "reply_count": 15,
                },
                "media": [
                    {
                        "media_key": "media1",
                        "type": "photo",
                        "url": "https://pbs.twimg.com/media/test_image.jpg",
                    }
                ],
                "author": {
                    "id": "987654321",
                    "name": "Media Test Leader",
                    "username": "testleader",
                    "profile_image_url": "https://pbs.twimg.com/profile_images/test.jpg",
                },
            },
        ]

        def fake_fetch_posts(handle: str, limit: int):
            return fake_tweets

        monkeypatch.setattr("twitter_client.fetch_posts", fake_fetch_posts)

        posts, origin = _sync_posts_for_leader(leader)
        app_module.db.session.commit()

        assert origin == "twitter"
        assert len(posts) >= 1
        
        post_dict = posts[0]
        assert "mediaUrl" in post_dict["metrics"]
        assert "pbs.twimg.com" in post_dict["metrics"]["mediaUrl"]


def test_twitter_falls_back_to_news_on_error(monkeypatch):
    """Test that ingestion falls back to news when Twitter API fails (ING-015)."""
    # Ensure Twitter is enabled for this test
    monkeypatch.setattr(app_module, "TWITTER_ENABLED", True)
    
    with app.app_context():
        leader = Leader(
            id=str(uuid.uuid4()),
            name="Fallback Test Leader",
            handles={"twitter": "@testleader"},
            tracking_topics=["test"],
        )
        app_module.db.session.add(leader)
        app_module.db.session.commit()

        def fake_fetch_posts_error(handle: str, limit: int):
            raise Exception("API Error")

        def fake_fetch_articles(query: str, limit: int):
            return ([
                {
                    "url": "https://example.com/news1",
                    "title": "News Article",
                    "summary": "Summary",
                    "source": "News Source",
                    "published_at": "2024-10-10T10:00:00.000Z",
                    "language": "en",
                }
            ], "scraper")

        monkeypatch.setattr("twitter_client.fetch_posts", fake_fetch_posts_error)
        monkeypatch.setattr("news_sources.fetch_articles", fake_fetch_articles)

        posts, origin = _sync_posts_for_leader(leader)
        app_module.db.session.commit()

        # Should have news posts as fallback
        assert len(posts) >= 1
        # Origin should be news/scraper, not twitter
        assert origin in ["scraper", "news", "sample"]


def test_twitter_disabled_skips_ingestion(monkeypatch):
    """Test that Twitter ingestion is skipped when TWITTER_ENABLED=False (ING-015)."""
    with app.app_context():
        leader = Leader(
            id=str(uuid.uuid4()),
            name="Disabled Test Leader",
            handles={"twitter": "@testleader"},
            tracking_topics=["test"],
        )
        app_module.db.session.add(leader)
        app_module.db.session.commit()

        fetch_called = False

        def fake_fetch_posts(handle: str, limit: int):
            nonlocal fetch_called
            fetch_called = True
            return []

        def fake_fetch_articles(query: str, limit: int):
            return ([
                {
                    "url": "https://example.com/news1",
                    "title": "News Article",
                    "summary": "Summary",
                    "source": "News Source",
                    "published_at": "2024-10-10T10:00:00.000Z",
                    "language": "en",
                }
            ], "scraper")

        monkeypatch.setattr("twitter_client.fetch_posts", fake_fetch_posts)
        monkeypatch.setattr("news_sources.fetch_articles", fake_fetch_articles)
        monkeypatch.setattr(app_module, "TWITTER_ENABLED", False)

        posts, origin = _sync_posts_for_leader(leader)
        app_module.db.session.commit()

        # Twitter fetch should never be called
        assert not fetch_called


def test_platform_post_id_backfill_from_metrics(monkeypatch):
    monkeypatch.setattr(app_module, "TWITTER_ENABLED", True)

    with app.app_context():
        leader = Leader(
            id=str(uuid.uuid4()),
            name="Backfill Leader",
            handles={"twitter": "@backfill"},
            tracking_topics=["backfill"],
        )
        app_module.db.session.add(leader)
        app_module.db.session.commit()

        legacy_post = Post(
            id=str(uuid.uuid4()),
            leader_id=leader.id,
            platform="Twitter",
            content="Legacy tweet",
            timestamp=datetime.utcnow(),
            sentiment="Neutral",
            metrics={"externalId": "legacy-tweet", "origin": "twitter"},
        )
        app_module.db.session.add(legacy_post)
        app_module.db.session.commit()

        def fake_fetch_posts(handle: str, limit: int):
            return []

        monkeypatch.setattr("twitter_client.fetch_posts", fake_fetch_posts)

        posts, origin = _sync_posts_for_leader(leader)

        refreshed = Post.query.filter_by(id=legacy_post.id).one()
        assert refreshed.platform_post_id == "legacy-tweet"
        assert refreshed.metrics.get("platformPostId") == "legacy-tweet"
        assert Post.query.filter_by(leader_id=leader.id).filter(Post.platform_post_id == "legacy-tweet").count() == 1
