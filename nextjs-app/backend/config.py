# backend/config.py
"""
Configuration loader and validator.
Validates required environment variables on startup and provides fail-fast behavior.
"""
from __future__ import annotations

import os
import sys
import logging
from typing import Dict, List, Optional


logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Configuration validation error."""
    pass


class Config:
    """
    Application configuration with validation.
    """
    
    # Database
    DATABASE_URL: str
    
    # Admin authentication
    ADMIN_JWT_SECRET: str
    ADMIN_JWT_TTL: int
    ADMIN_BOOTSTRAP_SECRET: str
    ADMIN_API_KEY: Optional[str]
    
    # Twitter/X ingestion
    TWITTER_ENABLED: bool
    TWITTER_BEARER_TOKEN: Optional[str]
    X_API_BEARER: Optional[str]
    TWITTER_LIMIT: int
    X_INGEST_ENABLED: bool
    X_INGEST_LIMIT: int
    INGESTION_DRY_RUN: bool
    
    # Checkpoint storage
    CHECKPOINT_DIR: str
    
    # Embedding
    EMBED_ENABLED: bool
    EMBED_SIGNING_KEY: Optional[str]
    EMBED_ALLOWED_ORIGINS: List[str]
    EMBED_TOKEN_TTL: int
    EMBED_RATE_LIMIT_REQUESTS: int
    EMBED_RATE_LIMIT_WINDOW: int
    
    # Facebook
    FACEBOOK_GRAPH_ENABLED: bool
    FACEBOOK_GRAPH_TOKEN: Optional[str]
    FACEBOOK_GRAPH_LIMIT: int
    
    # App settings
    POST_LIMIT: int
    
    @classmethod
    def load(cls) -> "Config":
        """
        Load and validate configuration from environment.
        
        Returns:
            Config instance
        
        Raises:
            ConfigError: If required variables are missing or invalid
        """
        config = cls()
        errors: List[str] = []
        
        # Database (required)
        config.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///amber.db")
        
        # Admin authentication (required)
        config.ADMIN_JWT_SECRET = os.getenv("ADMIN_JWT_SECRET")
        if not config.ADMIN_JWT_SECRET:
            errors.append("ADMIN_JWT_SECRET is required")
        
        config.ADMIN_JWT_TTL = int(os.getenv("ADMIN_JWT_TTL", "3600"))
        config.ADMIN_BOOTSTRAP_SECRET = os.getenv("ADMIN_BOOTSTRAP_SECRET", config.ADMIN_JWT_SECRET)
        config.ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
        
        # Twitter/X ingestion
        config.TWITTER_ENABLED = os.getenv("TWITTER_ENABLED", "0").lower() in {"1", "true", "yes", "on"}
        config.X_INGEST_ENABLED = os.getenv("X_INGEST_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
        config.TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
        config.X_API_BEARER = os.getenv("X_API_BEARER")
        config.TWITTER_LIMIT = int(os.getenv("TWITTER_LIMIT", "10"))
        config.X_INGEST_LIMIT = int(os.getenv("X_INGEST_LIMIT", "10"))
        config.INGESTION_DRY_RUN = os.getenv("INGESTION_DRY_RUN", "false").lower() in {"1", "true", "yes"}
        
        # Validate Twitter token if ingestion is enabled
        if (config.TWITTER_ENABLED or config.X_INGEST_ENABLED):
            if not config.TWITTER_BEARER_TOKEN and not config.X_API_BEARER:
                errors.append(
                    "TWITTER_BEARER_TOKEN or X_API_BEARER is required when Twitter/X ingestion is enabled"
                )
        
        # Checkpoint storage
        config.CHECKPOINT_DIR = os.getenv("CHECKPOINT_DIR", "./checkpoints")
        
        # Embedding
        config.EMBED_ENABLED = os.getenv("EMBED_ENABLED", "false").lower() in {"1", "true", "yes"}
        config.EMBED_SIGNING_KEY = os.getenv("EMBED_SIGNING_KEY")
        config.EMBED_TOKEN_TTL = int(os.getenv("EMBED_TOKEN_TTL", "60"))
        config.EMBED_RATE_LIMIT_REQUESTS = int(os.getenv("EMBED_RATE_LIMIT_REQUESTS", "10"))
        config.EMBED_RATE_LIMIT_WINDOW = int(os.getenv("EMBED_RATE_LIMIT_WINDOW", "60"))
        
        # Parse allowed origins
        origins_str = os.getenv("EMBED_ALLOWED_ORIGINS", "")
        config.EMBED_ALLOWED_ORIGINS = [
            origin.strip() for origin in origins_str.split(",") if origin.strip()
        ]
        
        # Validate embedding config if enabled
        if config.EMBED_ENABLED:
            if not config.EMBED_SIGNING_KEY:
                errors.append("EMBED_SIGNING_KEY is required when embedding is enabled")
            elif len(config.EMBED_SIGNING_KEY) < 32:
                errors.append("EMBED_SIGNING_KEY must be at least 32 characters long")
            
            if not config.ADMIN_API_KEY:
                logger.warning(
                    "ADMIN_API_KEY not set. Token endpoint will require session-based auth."
                )
        
        # Facebook
        config.FACEBOOK_GRAPH_ENABLED = os.getenv("FACEBOOK_GRAPH_ENABLED", "0").lower() in {"1", "true", "yes", "on"}
        config.FACEBOOK_GRAPH_TOKEN = os.getenv("FACEBOOK_GRAPH_TOKEN")
        config.FACEBOOK_GRAPH_LIMIT = int(os.getenv("FACEBOOK_GRAPH_LIMIT", "5"))
        
        if config.FACEBOOK_GRAPH_ENABLED and not config.FACEBOOK_GRAPH_TOKEN:
            errors.append("FACEBOOK_GRAPH_TOKEN is required when Facebook Graph is enabled")
        
        # App settings
        config.POST_LIMIT = int(os.getenv("POST_LIMIT", "6"))
        
        # Fail fast if there are errors
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            logger.error(error_msg)
            raise ConfigError(error_msg)
        
        # Log configuration (without secrets)
        logger.info("Configuration loaded successfully")
        logger.info("  Database: %s", config.DATABASE_URL.split("@")[-1] if "@" in config.DATABASE_URL else config.DATABASE_URL)
        logger.info("  Twitter/X ingestion: %s", config.TWITTER_ENABLED or config.X_INGEST_ENABLED)
        logger.info("  Embedding: %s", config.EMBED_ENABLED)
        logger.info("  Facebook Graph: %s", config.FACEBOOK_GRAPH_ENABLED)
        logger.info("  Dry run mode: %s", config.INGESTION_DRY_RUN)
        
        return config
    
    @staticmethod
    def get_secrets_manager_config() -> Dict:
        """
        Get configuration for secrets manager integration.
        Placeholder for SSM/Secrets Manager integration.
        
        Returns:
            Dictionary with secrets manager configuration
        """
        return {
            "enabled": os.getenv("SECRETS_MANAGER_ENABLED", "false").lower() in {"1", "true"},
            "provider": os.getenv("SECRETS_MANAGER_PROVIDER", "aws-ssm"),  # aws-ssm, aws-secrets, gcp-secret-manager
            "region": os.getenv("AWS_REGION", "us-east-1"),
            "prefix": os.getenv("SECRETS_PREFIX", "/amber/prod/"),
        }


def load_config() -> Config:
    """
    Load and validate configuration.
    Convenience function for application startup.
    
    Returns:
        Config instance
    
    Raises:
        ConfigError: If configuration is invalid
    """
    return Config.load()
