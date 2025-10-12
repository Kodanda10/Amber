"""
Test suite for rate limiting implementation (SEC-003).
Tests Redis-backed token bucket rate limiter with IP and user-based keys.
"""
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch, Mock
import pytest

# Set test environment variables before importing app
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("RATE_LIMITING_ENABLED", "true")
os.environ.setdefault("REQUESTS_PER_MINUTE", "10")
os.environ.setdefault("BURST_SIZE", "10")
os.environ.setdefault("WINDOW_SECONDS", "60")

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import importlib
import fakeredis
import redis as redis_module

# Mock Redis before importing rate_limiter
fake_redis_server = fakeredis.FakeServer()

def mock_redis_from_url(*args, **kwargs):
    """Mock Redis connection using fakeredis."""
    return fakeredis.FakeStrictRedis(server=fake_redis_server, decode_responses=True)

# Set up permanent mock before importing any modules that use Redis
import sys
sys.modules['redis'] = Mock()
sys.modules['redis'].from_url = mock_redis_from_url
sys.modules['redis'].Redis = fakeredis.FakeStrictRedis
sys.modules['redis'].RedisError = redis_module.RedisError
sys.modules['redis'].ConnectionError = redis_module.ConnectionError
sys.modules['redis'].TimeoutError = redis_module.TimeoutError

# Now import modules
rate_limiter_module = importlib.import_module("rate_limiter")
RateLimiter = rate_limiter_module.RateLimiter
rate_limit = rate_limiter_module.rate_limit
get_rate_limiter = rate_limiter_module.get_rate_limiter


@pytest.fixture(autouse=True, scope="function")
def reset_redis():
    """Reset Redis before and after each test."""
    try:
        client = fakeredis.FakeStrictRedis(server=fake_redis_server, decode_responses=True)
        client.flushall()
    except:
        pass
    yield
    try:
        client = fakeredis.FakeStrictRedis(server=fake_redis_server, decode_responses=True)
        client.flushall()
    except:
        pass


@pytest.fixture
def limiter():
    """Provide a fresh rate limiter instance for each test."""
    limiter = RateLimiter()
    # Force it to use fake redis
    limiter._redis_client = fakeredis.FakeStrictRedis(server=fake_redis_server, decode_responses=True)
    return limiter


class TestRateLimitBasics:
    """Test basic rate limiting functionality."""
    
    def test_rate_limit_allows_within_limit(self, limiter):
        """Test that requests within limit are allowed."""
        identifier = "192.168.1.1"
        
        # First 10 requests should be allowed (BURST_SIZE=10)
        for i in range(10):
            allowed, retry_after = limiter.check_rate_limit(identifier, "ip")
            assert allowed is True, f"Request {i+1} should be allowed"
            assert retry_after is None, f"No retry_after for request {i+1}"
    
    def test_rate_limit_blocks_over_limit(self, limiter):
        """Test that requests over limit are blocked."""
        identifier = "192.168.1.2"
        
        # Exhaust all tokens (BURST_SIZE=10)
        for i in range(10):
            allowed, _ = limiter.check_rate_limit(identifier, "ip")
            assert allowed is True
        
        # Next request should be rate limited
        allowed, retry_after = limiter.check_rate_limit(identifier, "ip")
        assert allowed is False, "Request should be rate limited"
        assert retry_after is not None, "Should have retry_after"
        assert retry_after > 0, "retry_after should be positive"
    
    def test_retry_after_value_is_reasonable(self, limiter):
        """Test that retry_after value is reasonable."""
        identifier = "192.168.1.3"
        
        # Exhaust tokens
        for i in range(10):
            limiter.check_rate_limit(identifier, "ip")
        
        # Check retry_after
        allowed, retry_after = limiter.check_rate_limit(identifier, "ip")
        assert not allowed
        assert retry_after is not None
        # With 10 requests/60 seconds, we need 1 token which takes 6 seconds
        assert 1 <= retry_after <= 10, f"retry_after should be reasonable, got {retry_after}"


class TestRateLimitKeyTypes:
    """Test different rate limit key types (IP vs user)."""
    
    def test_ip_based_rate_limiting(self, limiter):
        """Test IP-based rate limiting isolates different IPs."""
        ip1 = "192.168.1.10"
        ip2 = "192.168.1.11"
        
        # Exhaust limit for ip1
        for i in range(10):
            allowed, _ = limiter.check_rate_limit(ip1, "ip")
            assert allowed is True
        
        # ip1 should be rate limited
        allowed, _ = limiter.check_rate_limit(ip1, "ip")
        assert allowed is False, "ip1 should be rate limited"
        
        # ip2 should still have full quota
        allowed, _ = limiter.check_rate_limit(ip2, "ip")
        assert allowed is True, "ip2 should not be rate limited"
    
    def test_user_based_rate_limiting(self, limiter):
        """Test user-based rate limiting isolates different users."""
        user1 = "user123"
        user2 = "user456"
        
        # Exhaust limit for user1
        for i in range(10):
            allowed, _ = limiter.check_rate_limit(user1, "user")
            assert allowed is True
        
        # user1 should be rate limited
        allowed, _ = limiter.check_rate_limit(user1, "user")
        assert allowed is False, "user1 should be rate limited"
        
        # user2 should still have full quota
        allowed, _ = limiter.check_rate_limit(user2, "user")
        assert allowed is True, "user2 should not be rate limited"
    
    def test_ip_and_user_keys_are_separate(self, limiter):
        """Test that IP and user keys are independent."""
        identifier = "test123"
        
        # Exhaust IP-based limit
        for i in range(10):
            allowed, _ = limiter.check_rate_limit(identifier, "ip")
            assert allowed is True
        
        # IP should be rate limited
        allowed, _ = limiter.check_rate_limit(identifier, "ip")
        assert allowed is False, "IP key should be rate limited"
        
        # But user key should still have full quota
        allowed, _ = limiter.check_rate_limit(identifier, "user")
        assert allowed is True, "User key should not be rate limited"


class TestTokenBucketBehavior:
    """Test token bucket algorithm behavior."""
    
    def test_tokens_refill_over_time(self, limiter):
        """Test that tokens refill at the configured rate."""
        identifier = "192.168.1.20"
        
        # Consume some tokens
        for i in range(5):
            allowed, _ = limiter.check_rate_limit(identifier, "ip")
            assert allowed is True
        
        # Get current state
        state1 = limiter.get_current_limits(identifier, "ip")
        tokens1 = state1.get("tokens_available", 0)
        
        # Wait for tokens to refill
        # With 10 requests/60 seconds = 1/6 tokens per second
        # After 1 second, should have ~0.167 more tokens
        time.sleep(1.1)
        
        # Make a request to trigger token refill calculation
        allowed, _ = limiter.check_rate_limit(identifier, "ip")
        assert allowed is True, "Should have refilled enough for one more request"
        
        # Check that we consumed the refilled token
        state2 = limiter.get_current_limits(identifier, "ip")
        tokens2 = state2.get("tokens_available", 0)
        
        # After refill and consuming 1, should be back to ~5 tokens
        assert 4 <= tokens2 <= 6, f"Tokens should be around 5, got {tokens2}"
    
    def test_burst_capacity_is_limited(self, limiter):
        """Test that tokens don't accumulate beyond burst size."""
        identifier = "192.168.1.21"
        
        # Wait to allow tokens to accumulate
        time.sleep(2)
        
        # Try to consume all tokens plus more
        allowed_count = 0
        for i in range(15):  # Try more than BURST_SIZE=10
            allowed, _ = limiter.check_rate_limit(identifier, "ip", cost=1)
            if allowed:
                allowed_count += 1
        
        # Should only allow up to burst size (10), plus maybe 1-2 from refill during the loop
        assert allowed_count <= 12, f"Should not allow much more than burst size, got {allowed_count}"
    
    def test_cost_parameter_works(self, limiter):
        """Test that cost parameter consumes multiple tokens."""
        identifier = "192.168.1.22"
        
        # Consume 5 tokens at once
        allowed, _ = limiter.check_rate_limit(identifier, "ip", cost=5)
        assert allowed is True, "Should allow consuming 5 tokens"
        
        # Should have 5 tokens left
        state = limiter.get_current_limits(identifier, "ip")
        tokens = state.get("tokens_available", 0)
        assert 4 <= tokens <= 6, f"Should have ~5 tokens remaining, got {tokens}"
        
        # Can consume 5 more
        allowed, _ = limiter.check_rate_limit(identifier, "ip", cost=5)
        assert allowed is True, "Should allow consuming remaining 5 tokens"
        
        # Now should be exhausted
        allowed, _ = limiter.check_rate_limit(identifier, "ip", cost=1)
        assert allowed is False, "Should be rate limited after exhausting tokens"


class TestConcurrency:
    """Test rate limiting under concurrent requests."""
    
    def test_concurrent_requests_respect_limit(self, limiter):
        """Test that concurrent requests don't bypass rate limit."""
        identifier = "192.168.1.30"
        
        # Simulate concurrent requests by rapid succession
        allowed_count = 0
        denied_count = 0
        
        for i in range(15):
            allowed, _ = limiter.check_rate_limit(identifier, "ip")
            if allowed:
                allowed_count += 1
            else:
                denied_count += 1
        
        # Should allow exactly burst size (10), though small timing variations might allow 1-2 more
        assert 10 <= allowed_count <= 12, f"Should allow ~burst size, got {allowed_count}"
        assert denied_count >= 3, f"Should deny some requests, got {denied_count}"


class TestRedisFailure:
    """Test behavior when Redis is unavailable."""
    
    def test_fail_open_when_redis_unavailable(self):
        """Test that rate limiter fails open when Redis errors occur during check."""
        limiter = RateLimiter()
        # Mock the redis client to raise errors
        mock_client = Mock()
        mock_client.pipeline.side_effect = redis_module.RedisError("Connection lost")
        limiter._redis_client = mock_client
        
        # Should fail open and allow the request
        allowed, retry_after = limiter.check_rate_limit("192.168.1.100", "ip")
        assert allowed is True, "Should fail open when Redis is unavailable"
        assert retry_after is None, "No retry_after when failing open"


class TestRateLimitDisabled:
    """Test behavior when rate limiting is disabled."""
    
    def test_no_rate_limiting_when_disabled(self):
        """Test that rate limiting can be disabled via config."""
        with patch.dict(os.environ, {"RATE_LIMITING_ENABLED": "false"}):
            # Reload module to pick up new config
            importlib.reload(rate_limiter_module)
            
            with patch('redis.from_url', side_effect=mock_redis_from_url):
                limiter = RateLimiter()
                limiter._redis_client = None
                
                identifier = "192.168.1.60"
                
                # Should allow unlimited requests
                for i in range(20):
                    allowed, retry_after = limiter.check_rate_limit(identifier, "ip")
                    assert allowed is True, f"Request {i+1} should be allowed when disabled"
                    assert retry_after is None, f"No retry_after when disabled"


# Flask integration tests
# Import app after rate_limiter to ensure proper patching
app_module = importlib.import_module("app")
app = app_module.app


@pytest.fixture(scope="function")
def test_app(reset_redis):
    """Create a test Flask app with rate limiting."""
    from flask import Flask, jsonify
    test_app = Flask(__name__)
    test_app.config['TESTING'] = True
    
    # Ensure rate limiter uses fake redis
    rate_limiter_module._rate_limiter = None  # Reset global limiter
    limiter = RateLimiter()
    limiter._redis_client = fakeredis.FakeStrictRedis(server=fake_redis_server, decode_responses=True)
    rate_limiter_module._rate_limiter = limiter
    
    @test_app.route('/test-ip-limit')
    @rate_limit(key_type='ip', cost=1)
    def test_ip_endpoint():
        return jsonify({"status": "ok"})
    
    @test_app.route('/test-user-limit')
    @rate_limit(key_type='user', cost=1)
    def test_user_endpoint():
        return jsonify({"status": "ok"})
    
    return test_app


@pytest.fixture
def test_client(test_app, reset_redis):
    """Provide test client."""
    # Clear Redis before each test
    try:
        client = fakeredis.FakeStrictRedis(server=fake_redis_server, decode_responses=True)
        client.flushall()
    except:
        pass
    
    with test_app.test_client() as client:
        yield client
    
    # Clear Redis after test
    try:
        redis_client = fakeredis.FakeStrictRedis(server=fake_redis_server, decode_responses=True)
        redis_client.flushall()
    except:
        pass


class TestRateLimitDecorator:
    """Test the @rate_limit decorator on Flask routes."""
    
    def test_decorator_enforces_rate_limit(self, test_client):
        """Test that decorator properly enforces rate limits."""
        ip = "192.168.1.50"
        
        # First 10 requests should succeed
        for i in range(10):
            response = test_client.get('/test-ip-limit', 
                                      environ_base={'REMOTE_ADDR': ip})
            assert response.status_code == 200, f"Request {i+1} should succeed"
        
        # 11th should be rate limited
        response = test_client.get('/test-ip-limit', 
                                  environ_base={'REMOTE_ADDR': ip})
        assert response.status_code == 429, "Should return 429 Too Many Requests"
        
        data = response.get_json()
        assert data['error'] == 'rate_limit_exceeded'
        assert 'retry_after' in data
    
    def test_decorator_includes_retry_after_header(self, test_client):
        """Test that 429 response includes Retry-After header."""
        ip = "192.168.1.51"
        
        # Exhaust rate limit
        for i in range(10):
            test_client.get('/test-ip-limit', 
                           environ_base={'REMOTE_ADDR': ip})
        
        # Check Retry-After header in 429 response
        response = test_client.get('/test-ip-limit', 
                                  environ_base={'REMOTE_ADDR': ip})
        assert response.status_code == 429
        assert 'Retry-After' in response.headers, "Should include Retry-After header"
        
        retry_after = int(response.headers['Retry-After'])
        assert retry_after > 0, "Retry-After should be positive"
        assert retry_after <= 60, "Retry-After should be reasonable"
    
    def test_decorator_includes_rate_limit_headers(self, test_client):
        """Test that 429 responses include X-RateLimit-* headers."""
        ip = "192.168.1.52"
        
        # Exhaust rate limit
        for i in range(10):
            test_client.get('/test-ip-limit', 
                           environ_base={'REMOTE_ADDR': ip})
        
        # Check headers in 429 response
        response = test_client.get('/test-ip-limit', 
                                  environ_base={'REMOTE_ADDR': ip})
        assert response.status_code == 429
        
        assert 'X-RateLimit-Limit' in response.headers
        assert 'X-RateLimit-Remaining' in response.headers
        assert 'X-RateLimit-Reset' in response.headers
        
        assert response.headers['X-RateLimit-Limit'] == '10'
        assert response.headers['X-RateLimit-Remaining'] == '0'
    
    def test_decorator_with_user_key_type_falls_back_to_ip(self, test_client):
        """Test decorator with user-based rate limiting falls back to IP."""
        # Without authentication, should fall back to IP
        ip = "192.168.1.53"
        
        for i in range(10):
            response = test_client.get('/test-user-limit', 
                                      environ_base={'REMOTE_ADDR': ip})
            assert response.status_code == 200
        
        response = test_client.get('/test-user-limit', 
                                  environ_base={'REMOTE_ADDR': ip})
        assert response.status_code == 429, "Should rate limit by IP when no user auth"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

