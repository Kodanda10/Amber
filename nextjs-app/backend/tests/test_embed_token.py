"""
Unit tests for embed token service.
Tests token generation, validation, expiration, and origin checking.
"""
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from embed_token_service import EmbedTokenService


class TestEmbedTokenServiceInitialization:
    """Tests for service initialization."""
    
    def test_initialization_requires_signing_key(self):
        """Test that initialization requires signing key."""
        # Temporarily clear env var
        old_key = os.environ.get("EMBED_SIGNING_KEY")
        if "EMBED_SIGNING_KEY" in os.environ:
            del os.environ["EMBED_SIGNING_KEY"]
        
        try:
            with pytest.raises(ValueError, match="EMBED_SIGNING_KEY"):
                EmbedTokenService(signing_key=None)
        finally:
            if old_key:
                os.environ["EMBED_SIGNING_KEY"] = old_key
    
    def test_initialization_with_signing_key(self):
        """Test successful initialization with signing key."""
        service = EmbedTokenService(signing_key="test-secret-key-32-chars-long!")
        assert service.signing_key == "test-secret-key-32-chars-long!"
        assert service.default_ttl == 60
    
    def test_custom_ttl(self):
        """Test initialization with custom TTL."""
        service = EmbedTokenService(
            signing_key="test-secret-key",
            default_ttl=120
        )
        assert service.default_ttl == 120
    
    def test_allowed_origins(self):
        """Test initialization with allowed origins."""
        origins = ["https://example.com", "https://trusted.com"]
        service = EmbedTokenService(
            signing_key="test-secret-key",
            allowed_origins=origins
        )
        assert service.allowed_origins == origins


class TestTokenGeneration:
    """Tests for token generation."""
    
    def test_generate_token_basic(self):
        """Test basic token generation."""
        service = EmbedTokenService(signing_key="test-secret-key")
        result = service.generate_token(dashboard_id="dashboard-123")
        
        assert "token" in result
        assert "expiresAt" in result
        assert isinstance(result["token"], str)
        assert len(result["token"]) > 0
    
    def test_generate_token_with_user_id(self):
        """Test token generation with user ID."""
        service = EmbedTokenService(signing_key="test-secret-key")
        result = service.generate_token(
            dashboard_id="dashboard-123",
            user_id="user-456"
        )
        
        # Token should be generated successfully
        assert "token" in result
        
        # Validate token contains user ID
        payload = service.validate_token(result["token"])
        assert payload["userId"] == "user-456"
    
    def test_generate_token_with_allowed_origins(self):
        """Test token generation with custom allowed origins."""
        service = EmbedTokenService(signing_key="test-secret-key")
        origins = ["https://custom.com"]
        
        result = service.generate_token(
            dashboard_id="dashboard-123",
            allowed_origins=origins
        )
        
        payload = service.validate_token(result["token"])
        assert payload["allowedOrigins"] == origins
    
    def test_generate_token_uses_default_origins(self):
        """Test that token uses service default origins."""
        default_origins = ["https://default.com"]
        service = EmbedTokenService(
            signing_key="test-secret-key",
            allowed_origins=default_origins
        )
        
        result = service.generate_token(dashboard_id="dashboard-123")
        payload = service.validate_token(result["token"])
        
        assert payload["allowedOrigins"] == default_origins
    
    def test_generate_token_custom_ttl(self):
        """Test token generation with custom TTL."""
        service = EmbedTokenService(signing_key="test-secret-key")
        
        result = service.generate_token(
            dashboard_id="dashboard-123",
            ttl=300  # 5 minutes
        )
        
        payload = service.validate_token(result["token"])
        
        # Check TTL is approximately correct (within 5 seconds)
        ttl = payload["exp"] - payload["iat"]
        assert 295 <= ttl <= 305
    
    def test_token_expiration_format(self):
        """Test that expiresAt is in ISO 8601 format."""
        service = EmbedTokenService(signing_key="test-secret-key")
        result = service.generate_token(dashboard_id="dashboard-123")
        
        # Should be ISO format with Z suffix
        assert result["expiresAt"].endswith("Z")
        # Should be parseable as ISO timestamp
        from datetime import datetime
        datetime.fromisoformat(result["expiresAt"].replace("Z", "+00:00"))


class TestTokenValidation:
    """Tests for token validation."""
    
    def test_validate_valid_token(self):
        """Test validating a valid token."""
        service = EmbedTokenService(signing_key="test-secret-key")
        result = service.generate_token(dashboard_id="dashboard-123")
        
        payload = service.validate_token(result["token"])
        
        assert payload["dashboardId"] == "dashboard-123"
        assert "iat" in payload
        assert "exp" in payload
    
    def test_validate_expired_token(self):
        """Test that expired tokens are rejected."""
        service = EmbedTokenService(signing_key="test-secret-key")
        
        # Generate token with very short TTL
        result = service.generate_token(dashboard_id="dashboard-123", ttl=1)
        
        # Wait for token to expire
        time.sleep(2)
        
        with pytest.raises(ValueError, match="expired"):
            service.validate_token(result["token"])
    
    def test_validate_token_with_wrong_signature(self):
        """Test that tokens with wrong signature are rejected."""
        service1 = EmbedTokenService(signing_key="secret-1")
        service2 = EmbedTokenService(signing_key="secret-2")
        
        result = service1.generate_token(dashboard_id="dashboard-123")
        
        # Try to validate with different service (different key)
        with pytest.raises(ValueError, match="signature"):
            service2.validate_token(result["token"])
    
    def test_validate_malformed_token(self):
        """Test that malformed tokens are rejected."""
        service = EmbedTokenService(signing_key="test-secret-key")
        
        with pytest.raises(ValueError):
            service.validate_token("not-a-valid-token")
    
    def test_validate_token_dashboard_id_match(self):
        """Test validating token with required dashboard ID."""
        service = EmbedTokenService(signing_key="test-secret-key")
        result = service.generate_token(dashboard_id="dashboard-123")
        
        # Validation with matching dashboard ID should succeed
        payload = service.validate_token(
            result["token"],
            required_dashboard_id="dashboard-123"
        )
        assert payload["dashboardId"] == "dashboard-123"
    
    def test_validate_token_dashboard_id_mismatch(self):
        """Test that validation fails with wrong dashboard ID."""
        service = EmbedTokenService(signing_key="test-secret-key")
        result = service.generate_token(dashboard_id="dashboard-123")
        
        with pytest.raises(ValueError, match="mismatch"):
            service.validate_token(
                result["token"],
                required_dashboard_id="dashboard-456"
            )
    
    def test_validate_token_origin_allowed(self):
        """Test origin validation with allowed origin."""
        service = EmbedTokenService(signing_key="test-secret-key")
        origins = ["https://allowed.com", "https://trusted.com"]
        
        result = service.generate_token(
            dashboard_id="dashboard-123",
            allowed_origins=origins
        )
        
        # Validation with allowed origin should succeed
        payload = service.validate_token(
            result["token"],
            origin="https://allowed.com"
        )
        assert payload["dashboardId"] == "dashboard-123"
    
    def test_validate_token_origin_not_allowed(self):
        """Test that validation fails with disallowed origin."""
        service = EmbedTokenService(signing_key="test-secret-key")
        origins = ["https://allowed.com"]
        
        result = service.generate_token(
            dashboard_id="dashboard-123",
            allowed_origins=origins
        )
        
        with pytest.raises(ValueError, match="not allowed"):
            service.validate_token(
                result["token"],
                origin="https://evil.com"
            )


class TestTokenMetrics:
    """Tests for token service metrics."""
    
    def test_metrics_track_token_requests(self):
        """Test that metrics track token requests."""
        service = EmbedTokenService(signing_key="test-secret-key")
        
        initial_metrics = service.get_metrics()
        initial_requested = initial_metrics["token_requested"]
        
        service.generate_token(dashboard_id="dashboard-123")
        
        updated_metrics = service.get_metrics()
        assert updated_metrics["token_requested"] == initial_requested + 1
    
    def test_metrics_track_token_validation(self):
        """Test that metrics track successful validations."""
        service = EmbedTokenService(signing_key="test-secret-key")
        result = service.generate_token(dashboard_id="dashboard-123")
        
        initial_metrics = service.get_metrics()
        initial_validated = initial_metrics["token_validated"]
        
        service.validate_token(result["token"])
        
        updated_metrics = service.get_metrics()
        assert updated_metrics["token_validated"] == initial_validated + 1
    
    def test_metrics_track_expired_tokens(self):
        """Test that metrics track expired tokens."""
        service = EmbedTokenService(signing_key="test-secret-key")
        result = service.generate_token(dashboard_id="dashboard-123", ttl=1)
        
        time.sleep(2)
        
        initial_metrics = service.get_metrics()
        initial_expired = initial_metrics["token_expired"]
        
        try:
            service.validate_token(result["token"])
        except ValueError:
            pass
        
        updated_metrics = service.get_metrics()
        assert updated_metrics["token_expired"] == initial_expired + 1
    
    def test_metrics_track_invalid_tokens(self):
        """Test that metrics track invalid tokens."""
        service = EmbedTokenService(signing_key="test-secret-key")
        
        initial_metrics = service.get_metrics()
        initial_invalid = initial_metrics["token_invalid"]
        
        try:
            service.validate_token("invalid-token")
        except ValueError:
            pass
        
        updated_metrics = service.get_metrics()
        assert updated_metrics["token_invalid"] == initial_invalid + 1
