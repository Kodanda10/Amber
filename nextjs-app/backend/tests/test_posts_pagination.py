import os
import importlib
import sys
from pathlib import Path
from datetime import datetime, timedelta
import uuid

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

app_module = importlib.import_module("app")
app = app_module.app
Leader = app_module.Leader
Post = app_module.Post
with app.app_context():
    app_module.init_db()

def _seed_posts(db):
    with app.app_context():
        if Leader.query.count() == 0:
            leader = Leader(id=str(uuid.uuid4()), name="Test Leader", handles={}, tracking_topics=["policy"]) 
            db.session.add(leader)
            db.session.commit()
        leader = Leader.query.first()
        # create 30 posts
        base_time = datetime.utcnow()
        for i in range(30):
            p = Post(
                id=str(uuid.uuid4()),
                leader_id=leader.id,
                platform="News",
                content=f"Post {i}",
                timestamp=base_time - timedelta(minutes=i),
                sentiment="Neutral",
                metrics={"likes":0,"comments":0,"shares":0},
                verification_status="Needs Review"
            )
            app_module.db.session.add(p)
        app_module.db.session.commit()


def test_paginated_posts():
    _seed_posts(app_module.db)
    client = app.test_client()
    resp = client.get("/api/posts/paginated?limit=10")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["hasMore"] is True
    assert len(data["items"]) == 10
    cursor = data["nextCursor"]
    assert cursor
    # next page
    resp2 = client.get(f"/api/posts/paginated?limit=10&before={cursor}")
    data2 = resp2.get_json()
    assert len(data2["items"]) <= 10
