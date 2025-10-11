import os
import sys
import importlib
import uuid
from datetime import datetime
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

app_module = importlib.import_module("app")
app = app_module.app
Leader = app_module.Leader
Post = app_module.Post
_sync_posts_for_leader = app_module._sync_posts_for_leader
fetch_articles_original = getattr(app_module, 'fetch_articles')

def _fake_fetch_articles(name: str, limit: int):  # noqa: D401
    # Deterministic single positive-ish article
    return ([{
        "url": "http://example.com/" + uuid.uuid4().hex,
        "title": f"Progress update for {name}",
        "summary": "Great improvement and success achieved",
        "source": "Example News",
        "published_at": datetime.utcnow().isoformat(),
        "language": "en",
    }], "test")


def test_ingest_posts_have_sentiment_score():
    # Monkeypatch fetch_articles
    setattr(app_module, 'fetch_articles', _fake_fetch_articles)
    try:
        with app.app_context():
            # Create a leader directly
            leader = Leader(id=str(uuid.uuid4()), name="Score Test Leader", handles={}, tracking_topics=[])
            app_module.db.session.add(leader)
            app_module.db.session.commit()

            # Run ingestion
            posts, origin = _sync_posts_for_leader(leader)
            assert origin == "test"
            assert posts, "Expected at least one post from fake ingestion"

            # Ensure each post's metrics has sentimentScore numeric
            for p in posts:
                metrics = p.get("metrics") or {}
                assert "sentimentScore" in metrics, f"sentimentScore missing in metrics: {metrics}"
                assert isinstance(metrics["sentimentScore"], (int, float)), "sentimentScore must be numeric"
                assert -1.0 <= metrics["sentimentScore"] <= 1.0, "sentimentScore out of expected range"
    finally:
        setattr(app_module, 'fetch_articles', fetch_articles_original)  # restore
