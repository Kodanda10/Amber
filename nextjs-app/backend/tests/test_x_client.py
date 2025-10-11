"""
Tests for X API Client (ING-010)
Following TDD methodology for Twitter/X API integration.
"""
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Setup path for imports
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from x_client import (
    XAPIClient,
    XAPIError,
    XAPIAuthError,
    XAPIRateLimitError,
    create_client
)


class TestXAPIClientInitialization:
    """Test client initialization and configuration."""
    
    def test_client_requires_bearer_token(self):
        """Test that client raises error without bearer token."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(XAPIAuthError, match="No bearer token provided"):
                XAPIClient()
    
    def test_client_accepts_bearer_token_param(self):
        """Test client initialization with explicit token."""
        client = XAPIClient(bearer_token="test_token_123")
        assert client.bearer_token == "test_token_123"
    
    def test_client_reads_from_env_var(self):
        """Test client reads TWITTER_BEARER_TOKEN from environment."""
        with patch.dict(os.environ, {"TWITTER_BEARER_TOKEN": "env_token_456"}):
            client = XAPIClient()
            assert client.bearer_token == "env_token_456"
    
    def test_client_sets_authorization_header(self):
        """Test client sets proper authorization header."""
        client = XAPIClient(bearer_token="test_token")
        assert "Authorization" in client.session.headers
        assert client.session.headers["Authorization"] == "Bearer test_token"


class TestFetchUserTimeline:
    """Test fetching user timeline functionality."""
    
    @patch('x_client.requests.Session.request')
    def test_fetch_timeline_success(self, mock_request):
        """Test successful timeline fetch."""
        # Mock user lookup response
        user_response = Mock()
        user_response.status_code = 200
        user_response.json.return_value = {
            "data": {
                "id": "123456",
                "username": "testuser",
                "profile_image_url": "https://example.com/avatar.jpg"
            }
        }
        
        # Mock timeline response
        timeline_response = Mock()
        timeline_response.status_code = 200
        timeline_response.json.return_value = {
            "data": [
                {
                    "id": "tweet_1",
                    "text": "Test tweet content",
                    "created_at": "2025-10-11T12:00:00Z",
                    "author_id": "123456"
                }
            ],
            "meta": {
                "result_count": 1
            }
        }
        
        mock_request.side_effect = [user_response, timeline_response]
        
        client = XAPIClient(bearer_token="test_token")
        result = client.fetch_user_timeline("testuser", max_results=10)
        
        assert "posts" in result
        assert len(result["posts"]) == 1
        assert result["posts"][0]["id"] == "tweet_1"
        assert result["posts"][0]["text"] == "Test tweet content"
        assert result["posts"][0]["author"] == "testuser"
        assert result["posts"][0]["avatar"] == "https://example.com/avatar.jpg"
        assert result["user_avatar"] == "https://example.com/avatar.jpg"
    
    @patch('x_client.requests.Session.request')
    def test_fetch_timeline_with_media(self, mock_request):
        """Test timeline fetch includes media URLs."""
        user_response = Mock()
        user_response.status_code = 200
        user_response.json.return_value = {
            "data": {
                "id": "123456",
                "username": "testuser",
                "profile_image_url": "https://example.com/avatar.jpg"
            }
        }
        
        timeline_response = Mock()
        timeline_response.status_code = 200
        timeline_response.json.return_value = {
            "data": [
                {
                    "id": "tweet_1",
                    "text": "Tweet with photo",
                    "created_at": "2025-10-11T12:00:00Z",
                    "author_id": "123456",
                    "attachments": {
                        "media_keys": ["media_key_1", "media_key_2"]
                    }
                }
            ],
            "includes": {
                "media": [
                    {
                        "media_key": "media_key_1",
                        "url": "https://example.com/photo1.jpg"
                    },
                    {
                        "media_key": "media_key_2",
                        "preview_image_url": "https://example.com/photo2.jpg"
                    }
                ]
            },
            "meta": {
                "result_count": 1
            }
        }
        
        mock_request.side_effect = [user_response, timeline_response]
        
        client = XAPIClient(bearer_token="test_token")
        result = client.fetch_user_timeline("testuser")
        
        assert len(result["posts"]) == 1
        assert len(result["posts"][0]["media_urls"]) == 2
        assert "https://example.com/photo1.jpg" in result["posts"][0]["media_urls"]
        assert "https://example.com/photo2.jpg" in result["posts"][0]["media_urls"]


class TestPaginationHandling:
    """Test pagination cursor handling."""
    
    @patch('x_client.requests.Session.request')
    def test_pagination_cursor_handling(self, mock_request):
        """Test that pagination tokens are properly handled."""
        user_response = Mock()
        user_response.status_code = 200
        user_response.json.return_value = {
            "data": {"id": "123456", "username": "testuser"}
        }
        
        timeline_response = Mock()
        timeline_response.status_code = 200
        timeline_response.json.return_value = {
            "data": [
                {"id": "tweet_1", "text": "Tweet", "created_at": "2025-10-11T12:00:00Z"}
            ],
            "meta": {
                "result_count": 1,
                "next_token": "next_page_token_123"
            }
        }
        
        mock_request.side_effect = [user_response, timeline_response]
        
        client = XAPIClient(bearer_token="test_token")
        result = client.fetch_user_timeline("testuser")
        
        assert result["next_token"] == "next_page_token_123"
    
    @patch('x_client.requests.Session.request')
    def test_pagination_token_sent_in_request(self, mock_request):
        """Test that pagination token is sent in subsequent requests."""
        user_response = Mock()
        user_response.status_code = 200
        user_response.json.return_value = {
            "data": {"id": "123456", "username": "testuser"}
        }
        
        timeline_response = Mock()
        timeline_response.status_code = 200
        timeline_response.json.return_value = {
            "data": [],
            "meta": {"result_count": 0}
        }
        
        mock_request.side_effect = [user_response, timeline_response]
        
        client = XAPIClient(bearer_token="test_token")
        client.fetch_user_timeline("testuser", pagination_token="existing_token")
        
        # Check that pagination token was sent in the timeline request
        timeline_call = mock_request.call_args_list[1]
        assert "pagination_token" in timeline_call[1]["params"]
        assert timeline_call[1]["params"]["pagination_token"] == "existing_token"


class TestRateLimitHandling:
    """Test rate limit detection and backoff."""
    
    @patch('time.sleep')
    @patch('x_client.requests.Session.request')
    def test_rate_limit_backoff(self, mock_request, mock_sleep):
        """Test exponential backoff on rate limit errors."""
        # First call: rate limit error
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"x-rate-limit-reset": "1699999999"}
        
        # Second call: success
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "data": {"id": "123456", "username": "testuser"}
        }
        
        mock_request.side_effect = [rate_limit_response, success_response]
        
        client = XAPIClient(bearer_token="test_token")
        result = client._get_user_by_username("testuser")
        
        # Should have slept once with exponential backoff (2^0 = 1 second)
        mock_sleep.assert_called_once_with(1)
        assert result["id"] == "123456"
    
    @patch('time.sleep')
    @patch('x_client.requests.Session.request')
    def test_rate_limit_max_retries(self, mock_request, mock_sleep):
        """Test that rate limit errors raise exception after max retries."""
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"x-rate-limit-reset": "1699999999"}
        
        mock_request.return_value = rate_limit_response
        
        client = XAPIClient(bearer_token="test_token")
        
        with pytest.raises(XAPIRateLimitError, match="Rate limit exceeded"):
            client._get_user_by_username("testuser")
        
        # Should have retried 3 times (0, 1, 2)
        assert mock_sleep.call_count == 3


class TestAuthenticationErrors:
    """Test authentication error handling."""
    
    @patch('x_client.requests.Session.request')
    def test_invalid_token_raises_auth_error(self, mock_request):
        """Test that invalid token raises XAPIAuthError."""
        auth_error_response = Mock()
        auth_error_response.status_code = 401
        auth_error_response.text = "Unauthorized: Invalid token"
        
        mock_request.return_value = auth_error_response
        
        client = XAPIClient(bearer_token="invalid_token")
        
        with pytest.raises(XAPIAuthError, match="Authentication failed"):
            client._get_user_by_username("testuser")
    
    @patch('x_client.requests.Session.request')
    def test_forbidden_raises_auth_error(self, mock_request):
        """Test that 403 errors raise XAPIAuthError."""
        forbidden_response = Mock()
        forbidden_response.status_code = 403
        forbidden_response.text = "Forbidden"
        
        mock_request.return_value = forbidden_response
        
        client = XAPIClient(bearer_token="test_token")
        
        with pytest.raises(XAPIAuthError, match="Authentication failed"):
            client._get_user_by_username("testuser")


class TestFactoryFunction:
    """Test create_client factory function."""
    
    def test_create_client_with_token(self):
        """Test factory function creates client with token."""
        client = create_client(bearer_token="factory_token")
        assert isinstance(client, XAPIClient)
        assert client.bearer_token == "factory_token"
    
    def test_create_client_from_env(self):
        """Test factory function reads from environment."""
        with patch.dict(os.environ, {"TWITTER_BEARER_TOKEN": "env_factory_token"}):
            client = create_client()
            assert isinstance(client, XAPIClient)
            assert client.bearer_token == "env_factory_token"
