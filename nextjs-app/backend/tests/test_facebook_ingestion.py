import os
import importlib
import sys
from datetime import datetime
from pathlib import Path
import uuid

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("FACEBOOK_GRAPH_ENABLED", "1")
os.environ.setdefault("FACEBOOK_GRAPH_LIMIT", "5")

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

app_module = importlib.import_module("app")
app = app_module.app
Leader = app_module.Leader
Post = app_module.Post
_sync_posts_for_leader = app_module._sync_posts_for_leader

def test_graph_ingestion_persists_avatar_and_media(monkeypatch):
    with app.app_context():
        leader = Leader(
            id=str(uuid.uuid4()),
            name="Graph Leader",
            handles={"facebook": "@graphleader"},
            tracking_topics=[],
        )
        app_module.db.session.add(leader)
        app_module.db.session.commit()

        fake_post = {
            "id": "123_456",
            "message": "Sample graph post",
            "created_time": datetime(2025, 10, 4, 10, 30, 0).isoformat(),
            "permalink_url": "https://facebook.com/posts/123",
            "full_picture": "https://images.example.com/post.jpg",
            "from": {
                "name": "Graph Leader",
                "picture": {
                    "data": {
                        "url": "https://images.example.com/avatar.jpg",
                    }
                }
            }
        }

        def fake_fetch_posts(handle: str, limit: int):
            assert handle == "@graphleader"
            assert limit > 0
            return [fake_post]

        monkeypatch.setattr(app_module.facebook_client, "fetch_posts", fake_fetch_posts)
        monkeypatch.setattr(app_module, "FACEBOOK_GRAPH_ENABLED", True)
        monkeypatch.setattr(app_module, "FACEBOOK_GRAPH_LIMIT", 5)

        posts, origin = _sync_posts_for_leader(leader)

        assert origin == "graph"
        assert len(posts) == 1
        stored = posts[0]
        assert stored["platform"] == "Facebook"
        assert stored["metrics"]["avatarUrl"] == "https://images.example.com/avatar.jpg"
        assert stored["metrics"]["mediaUrl"] == "https://images.example.com/post.jpg"
        assert stored["metrics"]["platformPostId"] == "123_456"
        assert stored["metrics"]["origin"] == "graph"

        refreshed = Post.query.filter_by(id=stored["id"]).one()
        assert refreshed.metrics.get("avatarUrl") == "https://images.example.com/avatar.jpg"
        assert refreshed.metrics.get("mediaUrl") == "https://images.example.com/post.jpg"
        assert refreshed.platform == "Facebook"


def test_sample_post_backfill_when_no_sources(monkeypatch):
    with app.app_context():
        leader = Leader(
            id=str(uuid.uuid4()),
            name="Sample Leader",
            handles={"facebook": "@vishnudeosai1"},
            tracking_topics=[],
        )
        app_module.db.session.add(leader)
        app_module.db.session.commit()

        monkeypatch.setattr(app_module, "FACEBOOK_GRAPH_ENABLED", False)

        def empty_fetch_articles(name: str, limit: int):
            return ([], "api")

        monkeypatch.setattr(app_module, "fetch_articles", empty_fetch_articles)

        posts, origin = _sync_posts_for_leader(leader)
        assert origin == "sample"
        assert len(posts) == 1
        stored = posts[0]
        assert stored["platform"] == "Facebook"
        assert stored["metrics"].get("language") == "hi"
        assert "आईए" in stored["content"]


def test_graph_ingestion_falls_back_to_news_on_error(monkeypatch):
    with app.app_context():
        leader = Leader(
            id=str(uuid.uuid4()),
            name="Fallback Leader",
            handles={"facebook": "@fallback"},
            tracking_topics=[],
        )
        app_module.db.session.add(leader)
        app_module.db.session.commit()

        def failing_fetch_posts(handle: str, limit: int):
            raise RuntimeError("graph boom")

        def fake_fetch_articles(name: str, limit: int):
            return ([{
                "url": "https://news.example.com/post",
                "title": "News rescue",
                "summary": "Fallback summary",
                "source": "NewsAPI",
                "language": "en",
                "published_at": datetime(2024, 1, 1, 6, 0, 0).isoformat(),
            }], "news")

        monkeypatch.setattr(app_module, "FACEBOOK_GRAPH_ENABLED", True)
        monkeypatch.setattr(app_module.facebook_client, "fetch_posts", failing_fetch_posts)
        monkeypatch.setattr(app_module, "fetch_articles", fake_fetch_articles)

        posts, origin = _sync_posts_for_leader(leader)

        assert origin == "news"
        assert len(posts) == 1
        stored = posts[0]
        assert stored["platform"] == "News"
        assert stored["metrics"].get("origin") == "news"
