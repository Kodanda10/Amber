"""
REV-002: Reviewer Attribution Tests
Tests that reviewer identity and timestamp are captured on approve/reject actions.
"""
import os
import sys
import importlib
from pathlib import Path
import pytest
from datetime import datetime

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

# Ensure the backend directory is on sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

app_module = importlib.import_module("app")
app = app_module.app
Leader = app_module.Leader
Post = app_module.Post
ReviewItem = app_module.ReviewItem


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.app_context():
        app_module.init_db()
    with app.test_client() as client:
        yield client


def test_approve_captures_reviewer_identity(client, monkeypatch):
    """
    REV-002: Verify that approve action captures reviewer identity.
    """
    monkeypatch.setattr(app_module, "ADMIN_JWT_SECRET", "test-secret")
    monkeypatch.setattr(app_module, "ADMIN_JWT_TTL", 3600)
    
    # Generate a reviewer token
    token = app_module.generate_admin_token("reviewer_alice", role="reviewer")
    
    # Create a review item
    leaders_resp = client.get("/api/leaders")
    leader_id = leaders_resp.get_json()[0]["id"]
    
    post_payload = {
        "leaderId": leader_id,
        "platform": "News",
        "content": "Test content for approval",
        "requiresReview": True,
    }
    create_resp = client.post("/api/posts", json=post_payload)
    post_id = create_resp.get_json()["id"]
    
    review_resp = client.get("/api/review")
    review_id = next(item["id"] for item in review_resp.get_json() if item["postId"] == post_id)
    
    # Approve with authentication
    approve_resp = client.post(
        f"/api/review/{review_id}/approve",
        headers={'Authorization': f'Bearer {token}'}
    )
    
    assert approve_resp.status_code == 200
    data = approve_resp.get_json()
    assert data["state"] == "approved"
    assert "reviewedBy" in data
    assert data["reviewedBy"] == "reviewer_alice"
    assert "reviewedAt" in data
    # Verify reviewedAt is a valid ISO timestamp
    datetime.fromisoformat(data["reviewedAt"].replace("Z", "+00:00"))


def test_reject_captures_reviewer_identity(client, monkeypatch):
    """
    REV-002: Verify that reject action captures reviewer identity.
    """
    monkeypatch.setattr(app_module, "ADMIN_JWT_SECRET", "test-secret")
    monkeypatch.setattr(app_module, "ADMIN_JWT_TTL", 3600)
    
    # Generate an admin token
    token = app_module.generate_admin_token("admin_bob", role="admin")
    
    # Create a review item
    leaders_resp = client.get("/api/leaders")
    leader_id = leaders_resp.get_json()[0]["id"]
    
    post_payload = {
        "leaderId": leader_id,
        "platform": "News",
        "content": "Test content for rejection",
        "requiresReview": True,
    }
    create_resp = client.post("/api/posts", json=post_payload)
    post_id = create_resp.get_json()["id"]
    
    review_resp = client.get("/api/review")
    review_id = next(item["id"] for item in review_resp.get_json() if item["postId"] == post_id)
    
    # Reject with authentication
    reject_resp = client.post(
        f"/api/review/{review_id}/reject",
        headers={'Authorization': f'Bearer {token}'},
        json={"notes": "Content needs verification"}
    )
    
    assert reject_resp.status_code == 200
    data = reject_resp.get_json()
    assert data["state"] == "rejected"
    assert "reviewedBy" in data
    assert data["reviewedBy"] == "admin_bob"
    assert "reviewedAt" in data
    assert data["notes"] == "Content needs verification"
    datetime.fromisoformat(data["reviewedAt"].replace("Z", "+00:00"))


def test_reviewer_attribution_persists_in_database(client, monkeypatch):
    """
    REV-002: Verify that reviewer attribution is persisted to the database.
    """
    monkeypatch.setattr(app_module, "ADMIN_JWT_SECRET", "test-secret")
    monkeypatch.setattr(app_module, "ADMIN_JWT_TTL", 3600)
    
    token = app_module.generate_admin_token("reviewer_charlie", role="reviewer")
    
    # Create a review item
    leaders_resp = client.get("/api/leaders")
    leader_id = leaders_resp.get_json()[0]["id"]
    
    post_payload = {
        "leaderId": leader_id,
        "platform": "News",
        "content": "Test content",
        "requiresReview": True,
    }
    create_resp = client.post("/api/posts", json=post_payload)
    post_id = create_resp.get_json()["id"]
    
    review_resp = client.get("/api/review")
    review_id = next(item["id"] for item in review_resp.get_json() if item["postId"] == post_id)
    
    # Approve
    client.post(
        f"/api/review/{review_id}/approve",
        headers={'Authorization': f'Bearer {token}'}
    )
    
    # Fetch review queue again to verify persistence
    review_list_resp = client.get("/api/review")
    items = review_list_resp.get_json()
    
    approved_item = next((item for item in items if item["id"] == review_id), None)
    assert approved_item is not None
    assert approved_item["reviewedBy"] == "reviewer_charlie"
    assert "reviewedAt" in approved_item


def test_multiple_reviewers_tracked_separately(client, monkeypatch):
    """
    REV-002: Verify that different reviewers are tracked separately.
    """
    monkeypatch.setattr(app_module, "ADMIN_JWT_SECRET", "test-secret")
    monkeypatch.setattr(app_module, "ADMIN_JWT_TTL", 3600)
    
    # Create two review items
    leaders_resp = client.get("/api/leaders")
    leader_id = leaders_resp.get_json()[0]["id"]
    
    # First item
    post1 = client.post("/api/posts", json={
        "leaderId": leader_id,
        "platform": "News",
        "content": "First post",
        "requiresReview": True,
    }).get_json()
    
    # Second item
    post2 = client.post("/api/posts", json={
        "leaderId": leader_id,
        "platform": "News",
        "content": "Second post",
        "requiresReview": True,
    }).get_json()
    
    review_resp = client.get("/api/review")
    items = review_resp.get_json()
    review1_id = next(item["id"] for item in items if item["postId"] == post1["id"])
    review2_id = next(item["id"] for item in items if item["postId"] == post2["id"])
    
    # Reviewer 1 approves first item
    token1 = app_module.generate_admin_token("reviewer_one", role="reviewer")
    client.post(
        f"/api/review/{review1_id}/approve",
        headers={'Authorization': f'Bearer {token1}'}
    )
    
    # Reviewer 2 rejects second item
    token2 = app_module.generate_admin_token("reviewer_two", role="reviewer")
    client.post(
        f"/api/review/{review2_id}/reject",
        headers={'Authorization': f'Bearer {token2}'},
        json={"notes": "Needs work"}
    )
    
    # Verify both reviewers are tracked
    review_list = client.get("/api/review").get_json()
    
    item1 = next(item for item in review_list if item["id"] == review1_id)
    item2 = next(item for item in review_list if item["id"] == review2_id)
    
    assert item1["reviewedBy"] == "reviewer_one"
    assert item1["state"] == "approved"
    
    assert item2["reviewedBy"] == "reviewer_two"
    assert item2["state"] == "rejected"
