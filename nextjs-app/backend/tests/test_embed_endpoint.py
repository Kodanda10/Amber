"""
Integration tests for /api/embed/token endpoint.
Tests authentication, rate limiting, token generation, and validation.
"""
import os
import sys
import importlib
from pathlib import Path

import pytest

# Set test environment
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("EMBED_ENABLED", "true")
os.environ.setdefault("EMBED_SIGNING_KEY", "test-embed-secret-key-32-chars-long-for-testing!")
os.environ.setdefault("ADMIN_API_KEY", "test-admin-api-key")
os.environ.setdefault("EMBED_RATE_LIMIT_REQUESTS", "5")
os.environ.setdefault("EMBED_RATE_LIMIT_WINDOW", "60")

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

app_module = importlib.import_module("app")
app = app_module.app

with app.app_context():
    app_module.init_db()


@pytest.fixture
def client():
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def admin_token():
    """Generate admin token for authenticated requests."""
    with app.app_context():
        return app_module.generate_admin_token("test-admin")


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter before each test."""
    if app_module._embed_rate_limiter:
        app_module._embed_rate_limiter.requests.clear()
    yield


class TestEmbedTokenEndpointAuthentication:
    """Tests for endpoint authentication."""
    
    def test_endpoint_requires_authentication(self, client):
        """Test that endpoint requires authentication."""
        response = client.post("/api/embed/token", json={"dashboardId": "test-123"})
        # Should be either 401 (unauthorized) or 503 (service not enabled)
        assert response.status_code in [401, 503]
        data = response.get_json()
        assert "error" in data
    
    def test_endpoint_accepts_api_key(self, client):
        """Test that endpoint accepts valid API key."""
        response = client.post(
            "/api/embed/token",
            json={"dashboardId": "test-123"},
            headers={"Authorization": "Bearer test-admin-api-key"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "token" in data
        assert "expiresAt" in data
    
    def test_endpoint_accepts_admin_token(self, client, admin_token):
        """Test that endpoint accepts valid admin JWT token."""
        response = client.post(
            "/api/embed/token",
            json={"dashboardId": "test-123"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "token" in data
    
    def test_endpoint_rejects_invalid_api_key(self, client):
        """Test that endpoint rejects invalid API key."""
        response = client.post(
            "/api/embed/token",
            json={"dashboardId": "test-123"},
            headers={"Authorization": "Bearer wrong-key"}
        )
        assert response.status_code == 401


class TestEmbedTokenEndpointValidation:
    """Tests for request validation."""
    
    def test_endpoint_requires_dashboard_id(self, client):
        """Test that endpoint requires dashboardId."""
        response = client.post(
            "/api/embed/token",
            json={},
            headers={"Authorization": "Bearer test-admin-api-key"}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "dashboardId" in data["details"]
    
    def test_endpoint_accepts_custom_allowed_origins(self, client):
        """Test that endpoint accepts custom allowed origins."""
        response = client.post(
            "/api/embed/token",
            json={
                "dashboardId": "test-123",
                "allowedOrigins": ["https://custom.com"]
            },
            headers={"Authorization": "Bearer test-admin-api-key"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "token" in data


class TestEmbedTokenGeneration:
    """Tests for token generation."""
    
    def test_token_is_valid_format(self, client):
        """Test that generated token has valid format."""
        response = client.post(
            "/api/embed/token",
            json={"dashboardId": "test-123"},
            headers={"Authorization": "Bearer test-admin-api-key"}
        )
        assert response.status_code == 200
        data = response.get_json()
        
        # Token should be non-empty string
        assert isinstance(data["token"], str)
        assert len(data["token"]) > 0
        
        # Should have two parts separated by dot (payload.signature)
        assert "." in data["token"]
    
    def test_token_has_expiration(self, client):
        """Test that token has expiration timestamp."""
        response = client.post(
            "/api/embed/token",
            json={"dashboardId": "test-123"},
            headers={"Authorization": "Bearer test-admin-api-key"}
        )
        assert response.status_code == 200
        data = response.get_json()
        
        # Should have expiresAt in ISO format
        assert "expiresAt" in data
        assert data["expiresAt"].endswith("Z")
    
    def test_token_is_short_lived(self, client):
        """Test that token has short TTL (default 60s)."""
        import time
        from datetime import datetime, timezone
        
        before = datetime.now(timezone.utc)
        
        response = client.post(
            "/api/embed/token",
            json={"dashboardId": "test-123"},
            headers={"Authorization": "Bearer test-admin-api-key"}
        )
        
        after = datetime.now(timezone.utc)
        
        data = response.get_json()
        expires_at = datetime.fromisoformat(data["expiresAt"].replace("Z", "+00:00"))
        
        # TTL should be approximately 60 seconds
        ttl = (expires_at - before).total_seconds()
        assert 55 <= ttl <= 65  # Allow 5 second tolerance
    
    def test_different_tokens_for_different_dashboards(self, client):
        """Test that different dashboards get different tokens."""
        response1 = client.post(
            "/api/embed/token",
            json={"dashboardId": "dashboard-1"},
            headers={"Authorization": "Bearer test-admin-api-key"}
        )
        
        response2 = client.post(
            "/api/embed/token",
            json={"dashboardId": "dashboard-2"},
            headers={"Authorization": "Bearer test-admin-api-key"}
        )
        
        data1 = response1.get_json()
        data2 = response2.get_json()
        
        # Tokens should be different
        assert data1["token"] != data2["token"]


class TestEmbedTokenRateLimiting:
    """Tests for rate limiting."""
    
    def test_rate_limiting_enforced(self, client):
        """Test that rate limiting is enforced."""
        # Make requests up to the limit (5 requests per 60s)
        for i in range(5):
            response = client.post(
                "/api/embed/token",
                json={"dashboardId": f"test-{i}"},
                headers={"Authorization": "Bearer test-admin-api-key"}
            )
            assert response.status_code == 200
        
        # Next request should be rate limited
        response = client.post(
            "/api/embed/token",
            json={"dashboardId": "test-extra"},
            headers={"Authorization": "Bearer test-admin-api-key"}
        )
        assert response.status_code == 429
        data = response.get_json()
        assert data["error"] == "rate_limit_exceeded"


class TestEmbedTokenMetrics:
    """Tests for metrics tracking."""
    
    def test_metrics_track_successful_requests(self, client):
        """Test that metrics track successful token requests."""
        # Get initial metrics
        metrics_response = client.get("/api/metrics")
        initial_metrics = metrics_response.get_json()
        initial_requested = initial_metrics["ingest"].get("embed_token_requested", 0)
        
        # Request token
        client.post(
            "/api/embed/token",
            json={"dashboardId": "test-123"},
            headers={"Authorization": "Bearer test-admin-api-key"}
        )
        
        # Check updated metrics
        metrics_response = client.get("/api/metrics")
        updated_metrics = metrics_response.get_json()
        updated_requested = updated_metrics["ingest"].get("embed_token_requested", 0)
        
        assert updated_requested > initial_requested
    
    def test_metrics_track_failed_requests(self, client):
        """Test that metrics track failed token requests."""
        # Get initial metrics
        metrics_response = client.get("/api/metrics")
        initial_metrics = metrics_response.get_json()
        initial_failed = initial_metrics["ingest"].get("embed_token_failed", 0)
        
        # Request token without authentication (should fail)
        client.post("/api/embed/token", json={"dashboardId": "test-123"})
        
        # Check updated metrics
        metrics_response = client.get("/api/metrics")
        updated_metrics = metrics_response.get_json()
        updated_failed = updated_metrics["ingest"].get("embed_token_failed", 0)
        
        assert updated_failed > initial_failed
