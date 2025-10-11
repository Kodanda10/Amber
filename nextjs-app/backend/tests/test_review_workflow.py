import os
import sys
import importlib
from pathlib import Path

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


def test_review_workflow():
    client = app.test_client()
    # Ensure at least one leader exists (seed_data may have created some already)
    leaders_resp = client.get("/api/leaders")
    assert leaders_resp.status_code == 200
    leaders = leaders_resp.get_json()
    leader_id = leaders[0]["id"]

    # Create a post requiring review
    post_payload = {
        "leaderId": leader_id,
        "platform": "News",
        "content": "Test content needing review",
        "requiresReview": True,
        "reviewNotes": "Check facts",
    }
    create_resp = client.post("/api/posts", json=post_payload)
    assert create_resp.status_code == 201
    post_id = create_resp.get_json()["id"]

    # Get review queue
    review_resp = client.get("/api/review")
    assert review_resp.status_code == 200
    items = review_resp.get_json()
    assert any(item["postId"] == post_id for item in items)
    review_id = next(item["id"] for item in items if item["postId"] == post_id)

    # Generate admin token for authentication
    token = app_module.generate_admin_token("test_admin", role="admin")
    auth_headers = {'Authorization': f'Bearer {token}'}

    # Approve
    approve_resp = client.post(f"/api/review/{review_id}/approve", headers=auth_headers)
    assert approve_resp.status_code == 200
    assert approve_resp.get_json()["state"] == "approved"

    # Reject (should update state again)
    reject_resp = client.post(f"/api/review/{review_id}/reject", json={"notes": "Incorrect"}, headers=auth_headers)
    assert reject_resp.status_code == 200
    assert reject_resp.get_json()["state"] == "rejected"
