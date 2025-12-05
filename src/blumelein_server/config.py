"""Configuration management using environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Server Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    environment: str = "development"

    # Google Cloud Configuration
    google_cloud_project: str = ""
    google_cloud_location: str = "us-central1"

    # Database Configuration
    database_type: str = "firestore"  # Options: firestore, memory (for testing)

    # Stripe Configuration
    stripe_api_key: str
    stripe_publishable_key: str
    stripe_webhook_secret: str = ""

    # CORS Configuration
    allowed_origins: str = "http://localhost:3000,http://localhost:4173,http://127.0.0.1:4173,http://localhost:5173,http://127.0.0.1:5173"

    # Admin Configuration
    admin_api_key: str

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        _allowed_origins = self.allowed_origins.split(",")
        print(f"Allowed origins: {_allowed_origins}")
        return [origin.strip() for origin in _allowed_origins]


# Global settings instance
settings = Settings()

