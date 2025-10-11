"""
SEC-002: Role-Based Access Control Tests
Tests that reviewer vs admin permissions are enforced on review endpoints.
"""
import os
import sys
import importlib
from pathlib import Path
import pytest

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


def test_reviewer_can_approve_review(client, monkeypatch):
    """
    SEC-002: Reviewers should be able to approve review items.
    """
    monkeypatch.setattr(app_module, "ADMIN_JWT_SECRET", "test-secret")
    monkeypatch.setattr(app_module, "ADMIN_JWT_TTL", 3600)
    
    # Generate a reviewer token
    token = app_module.generate_admin_token("reviewer1", role="reviewer")
    
    # Create a review item
    leaders_resp = client.get("/api/leaders")
    leader_id = leaders_resp.get_json()[0]["id"]
    
    post_payload = {
        "leaderId": leader_id,
        "platform": "News",
        "content": "Test content for review",
        "requiresReview": True,
    }
    create_resp = client.post("/api/posts", json=post_payload)
    post_id = create_resp.get_json()["id"]
    
    review_resp = client.get("/api/review")
    review_id = next(item["id"] for item in review_resp.get_json() if item["postId"] == post_id)
    
    # Reviewer should be able to approve
    approve_resp = client.post(
        f"/api/review/{review_id}/approve",
        headers={'Authorization': f'Bearer {token}'}
    )
    assert approve_resp.status_code == 200
    assert approve_resp.get_json()["state"] == "approved"


def test_reviewer_can_reject_review(client, monkeypatch):
    """
    SEC-002: Reviewers should be able to reject review items.
    """
    monkeypatch.setattr(app_module, "ADMIN_JWT_SECRET", "test-secret")
    monkeypatch.setattr(app_module, "ADMIN_JWT_TTL", 3600)
    
    # Generate a reviewer token
    token = app_module.generate_admin_token("reviewer1", role="reviewer")
    
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
    
    # Reviewer should be able to reject
    reject_resp = client.post(
        f"/api/review/{review_id}/reject",
        headers={'Authorization': f'Bearer {token}'},
        json={"notes": "Not accurate"}
    )
    assert reject_resp.status_code == 200
    assert reject_resp.get_json()["state"] == "rejected"


def test_admin_can_approve_review(client, monkeypatch):
    """
    SEC-002: Admins should be able to approve review items.
    """
    monkeypatch.setattr(app_module, "ADMIN_JWT_SECRET", "test-secret")
    monkeypatch.setattr(app_module, "ADMIN_JWT_TTL", 3600)
    
    # Generate an admin token
    token = app_module.generate_admin_token("admin1", role="admin")
    
    # Create a review item
    leaders_resp = client.get("/api/leaders")
    leader_id = leaders_resp.get_json()[0]["id"]
    
    post_payload = {
        "leaderId": leader_id,
        "platform": "News",
        "content": "Test content for admin approval",
        "requiresReview": True,
    }
    create_resp = client.post("/api/posts", json=post_payload)
    post_id = create_resp.get_json()["id"]
    
    review_resp = client.get("/api/review")
    review_id = next(item["id"] for item in review_resp.get_json() if item["postId"] == post_id)
    
    # Admin should be able to approve
    approve_resp = client.post(
        f"/api/review/{review_id}/approve",
        headers={'Authorization': f'Bearer {token}'}
    )
    assert approve_resp.status_code == 200
    assert approve_resp.get_json()["state"] == "approved"


def test_unauthorized_cannot_approve_review(client):
    """
    SEC-002: Unauthorized users should not be able to approve review items.
    """
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
    
    # No token should result in 401
    approve_resp = client.post(f"/api/review/{review_id}/approve")
    assert approve_resp.status_code == 401


def test_unauthorized_cannot_reject_review(client):
    """
    SEC-002: Unauthorized users should not be able to reject review items.
    """
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
    
    # No token should result in 401
    reject_resp = client.post(f"/api/review/{review_id}/reject", json={"notes": "Test"})
    assert reject_resp.status_code == 401


def test_invalid_token_cannot_approve_review(client):
    """
    SEC-002: Invalid tokens should not be able to approve review items.
    """
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
    
    # Invalid token should result in 401
    approve_resp = client.post(
        f"/api/review/{review_id}/approve",
        headers={'Authorization': 'Bearer invalid-token'}
    )
    assert approve_resp.status_code == 401
