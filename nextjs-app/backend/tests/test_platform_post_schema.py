import os
import uuid
from datetime import datetime

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import app as app_module  # noqa: E402

app = app_module.app
Leader = app_module.Leader
Post = app_module.Post
ensure_post_schema = app_module.ensure_post_schema
ingest_x_posts = app_module.ingest_x_posts


@pytest.fixture(autouse=True)
def reset_db():
    """Ensure a fresh in-memory database for each test."""
    with app.app_context():
        app_module.db.drop_all()
        app_module.db.create_all()
        ensure_post_schema()
        yield
        app_module.db.session.remove()


def test_ensure_post_schema_backfills_platform_post_id():
    with app.app_context():
        leader = Leader(
            id=str(uuid.uuid4()),
            name="Migrated Leader",
            handles={"facebook": "@migrated"},
            tracking_topics=["migration"],
        )
        app_module.db.session.add(leader)
        app_module.db.session.flush()

        post = Post(
            id=str(uuid.uuid4()),
            leader_id=leader.id,
            platform="Facebook",
            content="Legacy content",
            timestamp=datetime.utcnow(),
            sentiment="Neutral",
            metrics={
                "platformPostId": "legacy123",
                "link": "https://example.com/legacy",
            },
            verification_status="Needs Review",
        )
        post.platform_post_id = None
        app_module.db.session.add(post)
        app_module.db.session.commit()

        ensure_post_schema()

        refreshed = Post.query.get(post.id)
        assert refreshed.platform_post_id == "legacy123"
        assert refreshed.metrics["platformPostId"] == "legacy123"
        assert refreshed.metrics["externalId"] == "legacy123"


def test_ingest_x_posts_backfills_existing_external_id(monkeypatch):
    with app.app_context():
        leader = Leader(
            id=str(uuid.uuid4()),
            name="X Leader",
            handles={"x": "@dedup"},
            tracking_topics=["dedup"],
        )
        app_module.db.session.add(leader)
        app_module.db.session.flush()

        post = Post(
            id=str(uuid.uuid4()),
            leader_id=leader.id,
            platform="Twitter",
            content="Existing tweet",
            timestamp=datetime.utcnow(),
            sentiment="Neutral",
            metrics={
                "externalId": "tweet123",
                "origin": "x",
                "mediaUrl": None,
            },
            verification_status="Needs Review",
        )
        post.platform_post_id = None
        app_module.db.session.add(post)
        app_module.db.session.commit()
        leader_id = leader.id
        post_id = post.id

    class FakeClient:
        def fetch_user_timeline(self, *args, **kwargs):
            return []

    monkeypatch.setattr(app_module.x_client, "create_client", lambda: FakeClient())

    with app.app_context():
        posts = ingest_x_posts(leader_id)
        assert posts == []

        refreshed = Post.query.get(post_id)
        assert refreshed.platform_post_id == "tweet123"
        assert refreshed.metrics["platformPostId"] == "tweet123"
        assert refreshed.metrics["externalId"] == "tweet123"
