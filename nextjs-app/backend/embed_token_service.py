# backend/embed_token_service.py
"""
Secure dashboard embedding with short-lived signed tokens.
Supports JWT (HS256) signing and origin validation.
"""
from __future__ import annotations

import os
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import hmac
import hashlib
import logging


class EmbedTokenService:
    """
    Service for generating and validating secure embed tokens.
    
    Features:
    - Short-lived JWT tokens (default 60s TTL)
    - Origin validation
    - HMAC signing with configurable secret
    """
    
    def __init__(
        self,
        signing_key: Optional[str] = None,
        default_ttl: int = 60,
        allowed_origins: Optional[List[str]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize embed token service.
        
        Args:
            signing_key: Secret key for signing tokens
            default_ttl: Default token TTL in seconds (default: 60)
            allowed_origins: List of allowed origins for embedding
            logger: Optional logger instance
        """
        self.signing_key = signing_key or os.getenv("EMBED_SIGNING_KEY")
        if not self.signing_key:
            raise ValueError("EMBED_SIGNING_KEY must be provided")
        
        self.default_ttl = default_ttl
        self.allowed_origins = allowed_origins or self._parse_allowed_origins()
        self.logger = logger or logging.getLogger(__name__)
        
        # Metrics
        self.metrics = {
            "token_requested": 0,
            "token_failed": 0,
            "token_validated": 0,
            "token_expired": 0,
            "token_invalid": 0,
        }
    
    def _parse_allowed_origins(self) -> List[str]:
        """Parse allowed origins from environment variable."""
        origins_str = os.getenv("EMBED_ALLOWED_ORIGINS", "")
        if not origins_str:
            return []
        return [origin.strip() for origin in origins_str.split(",") if origin.strip()]
    
    def generate_token(
        self,
        dashboard_id: str,
        user_id: Optional[str] = None,
        allowed_origins: Optional[List[str]] = None,
        ttl: Optional[int] = None,
    ) -> Dict[str, str]:
        """
        Generate a signed embed token.
        
        Args:
            dashboard_id: Dashboard ID to embed
            user_id: Optional user ID for the requester
            allowed_origins: Optional list of allowed origins (overrides default)
            ttl: Optional TTL in seconds (overrides default)
        
        Returns:
            Dictionary with 'token' and 'expiresAt' fields
        """
        try:
            ttl = ttl or self.default_ttl
            now = int(time.time())
            exp = now + ttl
            
            # Build payload
            payload = {
                "dashboardId": dashboard_id,
                "iat": now,
                "exp": exp,
            }
            
            if user_id:
                payload["userId"] = user_id
            
            if allowed_origins:
                payload["allowedOrigins"] = allowed_origins
            elif self.allowed_origins:
                payload["allowedOrigins"] = self.allowed_origins
            
            # Create JWT-like token (simplified, using HMAC)
            # Format: base64(header).base64(payload).signature
            token = self._sign_payload(payload)
            
            self.metrics["token_requested"] += 1
            
            self.logger.info(
                "Generated embed token for dashboard=%s, user=%s, ttl=%d",
                dashboard_id,
                user_id or "anonymous",
                ttl
            )
            
            return {
                "token": token,
                "expiresAt": datetime.utcfromtimestamp(exp).isoformat() + "Z",
            }
            
        except Exception as e:
            self.metrics["token_failed"] += 1
            self.logger.error("Failed to generate embed token: %s", str(e))
            raise
    
    def validate_token(
        self,
        token: str,
        required_dashboard_id: Optional[str] = None,
        origin: Optional[str] = None,
    ) -> Dict:
        """
        Validate an embed token.
        
        Args:
            token: Token to validate
            required_dashboard_id: Optional dashboard ID to verify
            origin: Optional origin to verify against allowedOrigins
        
        Returns:
            Decoded payload dictionary
        
        Raises:
            ValueError: If token is invalid, expired, or doesn't match requirements
        """
        try:
            # Decode and verify signature
            payload = self._verify_token(token)
            
            # Check expiration
            exp = payload.get("exp")
            if not exp or int(time.time()) > exp:
                self.metrics["token_expired"] += 1
                raise ValueError("Token has expired")
            
            # Verify dashboard ID if required
            if required_dashboard_id:
                if payload.get("dashboardId") != required_dashboard_id:
                    self.metrics["token_invalid"] += 1
                    raise ValueError("Token dashboard ID mismatch")
            
            # Verify origin if provided
            if origin:
                allowed_origins = payload.get("allowedOrigins", [])
                if allowed_origins and origin not in allowed_origins:
                    self.metrics["token_invalid"] += 1
                    raise ValueError(f"Origin {origin} not allowed")
            
            self.metrics["token_validated"] += 1
            return payload
            
        except Exception as e:
            self.metrics["token_invalid"] += 1
            self.logger.warning("Token validation failed: %s", str(e))
            raise
    
    def _sign_payload(self, payload: Dict) -> str:
        """
        Sign a payload and create a token.
        
        Args:
            payload: Payload dictionary
        
        Returns:
            Signed token string
        """
        # Serialize payload
        payload_str = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        payload_bytes = payload_str.encode("utf-8")
        
        # Create signature
        signature = hmac.new(
            self.signing_key.encode("utf-8"),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        
        # Combine into token: payload.signature
        import base64
        payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode("utf-8").rstrip("=")
        return f"{payload_b64}.{signature}"
    
    def _verify_token(self, token: str) -> Dict:
        """
        Verify token signature and decode payload.
        
        Args:
            token: Token to verify
        
        Returns:
            Decoded payload dictionary
        
        Raises:
            ValueError: If token format is invalid or signature doesn't match
        """
        try:
            parts = token.split(".")
            if len(parts) != 2:
                raise ValueError("Invalid token format")
            
            payload_b64, signature = parts
            
            # Decode payload
            import base64
            # Add padding if needed
            padding = 4 - (len(payload_b64) % 4)
            if padding != 4:
                payload_b64 += "=" * padding
            
            payload_bytes = base64.urlsafe_b64decode(payload_b64)
            payload = json.loads(payload_bytes.decode("utf-8"))
            
            # Verify signature
            expected_signature = hmac.new(
                self.signing_key.encode("utf-8"),
                payload_bytes,
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                raise ValueError("Invalid signature")
            
            return payload
            
        except Exception as e:
            raise ValueError(f"Token verification failed: {str(e)}")
    
    def get_metrics(self) -> Dict:
        """Get token service metrics."""
        return self.metrics.copy()
