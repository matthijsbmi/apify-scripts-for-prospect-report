"""
Configuration settings for the Apify Prospect Analyzer API.

This module provides configuration management using Pydantic settings.
"""

import os
from typing import List, Optional
from pydantic import Field

try:
    # Try the new import first (pydantic v2+)
    from pydantic_settings import BaseSettings
except ImportError:
    # Fall back to the old import (pydantic v1)
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings configuration."""
    
    # API Configuration
    api_name: str = "Apify Prospect Analyzer API"
    api_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8005, env="PORT")
    
    # CORS Configuration
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    
    # Security
    allowed_hosts: List[str] = Field(default=["*"], env="ALLOWED_HOSTS")
    
    # Apify Configuration
    apify_api_token: Optional[str] = Field(default=None, env="APIFY_API_TOKEN")
    apify_base_url: str = Field(default="https://api.apify.com/v2", env="APIFY_BASE_URL")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Cache Configuration
    enable_cache: bool = Field(default=True, env="ENABLE_CACHE")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")  # 1 hour
    
    # Budget and Cost Management
    default_max_budget: float = Field(default=10.0, env="DEFAULT_MAX_BUDGET")
    cost_warning_threshold: float = Field(default=0.8, env="COST_WARNING_THRESHOLD")
    default_compute_unit_cost: float = Field(default=0.02, env="DEFAULT_COMPUTE_UNIT_COST")
    
    # Data Collection
    default_timeout: int = Field(default=300, env="DEFAULT_TIMEOUT")  # 5 minutes
    max_batch_size: int = Field(default=100, env="MAX_BATCH_SIZE")
    
    # Environment and Testing
    environment: str = Field(default="development", env="ENVIRONMENT")
    testing: bool = Field(default=False, env="TESTING")
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings() 