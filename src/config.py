"""Configuration management for SIAHL Telegram Bot."""

from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Telegram Configuration
    telegram_bot_token: str = Field(..., description="Telegram Bot API token")

    # Database Configuration
    database_url: str = Field(..., description="PostgreSQL connection URL")

    # SIAHL League Configuration
    siahl_base_url: str = Field(
        default="https://stats.sharksice.timetoscore.com",
        description="Base URL for SIAHL stats website"
    )
    default_league_id: int = Field(default=1, description="Default league ID")
    current_season: int = Field(default=72, description="Current season number")

    # Scraper Configuration
    scraper_user_agent: str = Field(
        default="SIAHL-Bot/1.0",
        description="User-Agent header for web requests"
    )
    scraper_delay_ms: int = Field(
        default=500,
        description="Delay between requests in milliseconds"
    )
    scraper_max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts"
    )

    # Notification Configuration
    notification_batch_size: int = Field(
        default=30,
        description="Number of notifications to send in one batch"
    )
    notification_delay_ms: int = Field(
        default=100,
        description="Delay between notifications in milliseconds"
    )

    # Cache Configuration
    cache_default_ttl: int = Field(
        default=3600,
        description="Default cache TTL in seconds (1 hour)"
    )
    cache_stats_ttl: int = Field(
        default=21600,
        description="Stats cache TTL in seconds (6 hours)"
    )

    # AI Configuration (Optional)
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key for AI features"
    )
    ai_features_enabled: bool = Field(
        default=False,
        description="Enable AI-powered features"
    )
    ai_rate_limit_per_group: int = Field(
        default=10,
        description="Max AI API calls per group per day"
    )
    ai_model: str = Field(
        default="claude-3-5-haiku-20241022",
        description="Claude model to use"
    )

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    sentry_dsn: Optional[str] = Field(
        default=None,
        description="Sentry DSN for error tracking"
    )

    # Environment
    environment: str = Field(
        default="development",
        description="Environment: development, staging, production"
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in allowed_levels:
            raise ValueError(f"Invalid log level. Must be one of {allowed_levels}")
        return v_upper

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment."""
        allowed_envs = {"development", "staging", "production"}
        v_lower = v.lower()
        if v_lower not in allowed_envs:
            raise ValueError(f"Invalid environment. Must be one of {allowed_envs}")
        return v_lower

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"

    @property
    def scraper_delay_seconds(self) -> float:
        """Get scraper delay in seconds."""
        return self.scraper_delay_ms / 1000.0

    @property
    def notification_delay_seconds(self) -> float:
        """Get notification delay in seconds."""
        return self.notification_delay_ms / 1000.0


# Global settings instance
settings = Settings()


# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
TESTS_ROOT = PROJECT_ROOT / "tests"
TEMP_DIR = PROJECT_ROOT / "tmp"

# Ensure temp directory exists
TEMP_DIR.mkdir(exist_ok=True)
