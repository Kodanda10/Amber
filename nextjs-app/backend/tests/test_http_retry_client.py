"""
Unit tests for HTTP retry client with exponential backoff and jitter.
Tests retry logic, backoff calculation, and Retry-After header support.
"""
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch
import time

import pytest
import requests

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from http_retry_client import HTTPRetryClient


class TestHTTPRetryClientInitialization:
    """Tests for client initialization."""
    
    def test_default_initialization(self):
        """Test client initializes with default values."""
        client = HTTPRetryClient()
        assert client.base_delay_ms == 500
        assert client.max_delay_ms == 60000
        assert client.backoff_factor == 2.0
        assert client.max_retries == 6
    
    def test_custom_initialization(self):
        """Test client initializes with custom values."""
        client = HTTPRetryClient(
            base_delay_ms=1000,
            max_delay_ms=30000,
            backoff_factor=3.0,
            max_retries=3
        )
        assert client.base_delay_ms == 1000
        assert client.max_delay_ms == 30000
        assert client.backoff_factor == 3.0
        assert client.max_retries == 3


class TestBackoffCalculation:
    """Tests for exponential backoff calculation."""
    
    def test_backoff_increases_exponentially(self):
        """Test that backoff delay increases exponentially."""
        client = HTTPRetryClient(base_delay_ms=100, max_delay_ms=10000)
        
        # Delay should be between 0 and base_delay for attempt 0 with jitter
        delay1 = client._calculate_delay(0, None, {})
        assert 0 <= delay1 <= 100
        
        # Delay for higher attempts should be larger (on average)
        delay5 = client._calculate_delay(5, None, {})
        # For attempt 5: 100 * (2^5) = 3200, capped at 10000
        assert 0 <= delay5 <= 3200
    
    def test_backoff_respects_max_delay(self):
        """Test that backoff doesn't exceed max_delay."""
        client = HTTPRetryClient(base_delay_ms=1000, max_delay_ms=5000)
        
        # High attempt number should still be capped
        delay = client._calculate_delay(10, None, {})
        assert delay <= 5000
    
    def test_retry_after_header_honored(self):
        """Test that Retry-After header is honored for 429 responses."""
        client = HTTPRetryClient()
        
        # Retry-After: 30 seconds
        headers = {"Retry-After": "30"}
        delay = client._calculate_delay(0, 429, headers)
        
        assert delay == 30000  # 30 seconds in milliseconds
    
    def test_retry_after_capped_at_max_delay(self):
        """Test that Retry-After is capped at max_delay."""
        client = HTTPRetryClient(max_delay_ms=10000)
        
        # Retry-After: 100 seconds (exceeds max)
        headers = {"Retry-After": "100"}
        delay = client._calculate_delay(0, 429, headers)
        
        assert delay == 10000  # Capped at max_delay


class TestRetryLogic:
    """Tests for request retry behavior."""
    
    def test_successful_request_no_retry(self):
        """Test that successful requests don't retry."""
        mock_response = Mock()
        mock_response.status_code = 200
        
        mock_session = Mock()
        mock_session.request.return_value = mock_response
        
        client = HTTPRetryClient(session=mock_session)
        response = client.request("GET", "http://example.com")
        
        assert response.status_code == 200
        assert mock_session.request.call_count == 1
    
    def test_retry_on_429_rate_limit(self):
        """Test that 429 responses trigger retry."""
        # First two requests fail with 429, third succeeds
        mock_responses = [
            Mock(status_code=429, headers={}),
            Mock(status_code=429, headers={}),
            Mock(status_code=200, headers={}),
        ]
        
        mock_session = Mock()
        mock_session.request.side_effect = mock_responses
        
        # Use very short delays for testing
        client = HTTPRetryClient(
            session=mock_session,
            base_delay_ms=1,
            max_retries=3
        )
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            response = client.request("GET", "http://example.com")
        
        assert response.status_code == 200
        assert mock_session.request.call_count == 3
    
    def test_retry_on_500_server_error(self):
        """Test that 500 responses trigger retry."""
        mock_responses = [
            Mock(status_code=500, headers={}),
            Mock(status_code=200, headers={}),
        ]
        
        mock_session = Mock()
        mock_session.request.side_effect = mock_responses
        
        client = HTTPRetryClient(session=mock_session, base_delay_ms=1)
        
        with patch('time.sleep'):
            response = client.request("GET", "http://example.com")
        
        assert response.status_code == 200
        assert mock_session.request.call_count == 2
    
    def test_retry_on_503_service_unavailable(self):
        """Test that 503 responses trigger retry."""
        mock_responses = [
            Mock(status_code=503, headers={}),
            Mock(status_code=200, headers={}),
        ]
        
        mock_session = Mock()
        mock_session.request.side_effect = mock_responses
        
        client = HTTPRetryClient(session=mock_session, base_delay_ms=1)
        
        with patch('time.sleep'):
            response = client.request("GET", "http://example.com")
        
        assert mock_session.request.call_count == 2
    
    def test_max_retries_exceeded(self):
        """Test that max retries limit is enforced."""
        # All requests fail with 429
        mock_response = Mock(status_code=429, headers={})
        
        mock_session = Mock()
        mock_session.request.return_value = mock_response
        
        client = HTTPRetryClient(session=mock_session, base_delay_ms=1, max_retries=2)
        
        with patch('time.sleep'):
            response = client.request("GET", "http://example.com")
        
        # Should try: initial + 2 retries = 3 total
        assert mock_session.request.call_count == 3
        assert response.status_code == 429
    
    def test_non_retryable_error_no_retry(self):
        """Test that 400 Bad Request doesn't retry."""
        mock_response = Mock(status_code=400, headers={})
        
        mock_session = Mock()
        mock_session.request.return_value = mock_response
        
        client = HTTPRetryClient(session=mock_session)
        response = client.request("GET", "http://example.com")
        
        assert response.status_code == 400
        assert mock_session.request.call_count == 1
    
    def test_request_exception_triggers_retry(self):
        """Test that request exceptions trigger retry."""
        # First request fails with exception, second succeeds
        mock_session = Mock()
        mock_session.request.side_effect = [
            requests.RequestException("Connection error"),
            Mock(status_code=200, headers={}),
        ]
        
        client = HTTPRetryClient(session=mock_session, base_delay_ms=1)
        
        with patch('time.sleep'):
            response = client.request("GET", "http://example.com")
        
        assert response.status_code == 200
        assert mock_session.request.call_count == 2
    
    def test_on_retry_callback(self):
        """Test that on_retry callback is called."""
        mock_responses = [
            Mock(status_code=429, headers={}),
            Mock(status_code=200, headers={}),
        ]
        
        mock_session = Mock()
        mock_session.request.side_effect = mock_responses
        
        callback_calls = []
        def on_retry(attempt, delay_ms, response):
            callback_calls.append((attempt, delay_ms, response))
        
        client = HTTPRetryClient(session=mock_session, base_delay_ms=1)
        
        with patch('time.sleep'):
            client.request("GET", "http://example.com", on_retry=on_retry)
        
        assert len(callback_calls) == 1
        assert callback_calls[0][0] == 0  # First retry attempt


class TestConvenienceMethods:
    """Tests for convenience methods (get, post, etc.)."""
    
    def test_get_method(self):
        """Test GET convenience method."""
        mock_response = Mock(status_code=200)
        mock_session = Mock()
        mock_session.request.return_value = mock_response
        
        client = HTTPRetryClient(session=mock_session)
        response = client.get("http://example.com")
        
        assert response.status_code == 200
        mock_session.request.assert_called_once_with("GET", "http://example.com")
    
    def test_post_method(self):
        """Test POST convenience method."""
        mock_response = Mock(status_code=201)
        mock_session = Mock()
        mock_session.request.return_value = mock_response
        
        client = HTTPRetryClient(session=mock_session)
        response = client.post("http://example.com", json={"key": "value"})
        
        assert response.status_code == 201
        mock_session.request.assert_called_once_with("POST", "http://example.com", json={"key": "value"})
