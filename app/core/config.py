from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables
        env_parse_none_str="",  # Treat empty strings as None
    )
    
    api_title: str = "Flex Living Reviews API"
    api_version: str = "1.0.0"
    api_prefix: str = "/api"
    
    cors_origins: Optional[str] = Field(
        default=None,
        description="CORS origins as comma-separated string (e.g., 'http://localhost:3000,http://localhost:5173')"
    )
    
    _parsed_cors_origins: Optional[list[str]] = None
    
    @model_validator(mode="after")
    def parse_cors_origins(self):
        """Parse CORS origins from comma-separated string to list"""
        default_origins = [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ]
        
        if self.cors_origins is None or not self.cors_origins.strip():
            self._parsed_cors_origins = default_origins
            return self
        
        # Parse comma-separated string
        origins = [
            origin.strip() 
            for origin in self.cors_origins.split(",") 
            if origin.strip()
        ]
        
        self._parsed_cors_origins = origins if origins else default_origins
        return self
    
    def get_cors_origins(self) -> list[str]:
        """Get parsed CORS origins list"""
        if self._parsed_cors_origins is None:
            # Fallback if validator didn't run
            return [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173",
            ]
        return self._parsed_cors_origins
    
    # Hostaway Configuration - loaded from .env file
    hostaway_account_id: str = Field(
        default="1234",
        description="Hostaway account ID"
    )
    hostaway_api_key: str = Field(
        default="1234",
        description="Hostaway API key"
    )
    
    # Data Configuration
    mock_data_path: str = "data/mock_reviews.json"
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    log_file: Optional[str] = Field(
        default=None,
        description="Path to log file (optional). If not set, logs only to console."
    )
    
    # Rate Limiting Configuration
    rate_limit_per_minute: int = Field(
        default=60,
        description="Maximum requests per minute per IP address"
    )
    rate_limit_per_hour: int = Field(
        default=1000,
        description="Maximum requests per hour per IP address"
    )
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable or disable rate limiting"
    )
    
    # Database Configuration
    database_url: str = Field(
        default="postgresql+psycopg://flexreview:flexreview123@localhost:5432/flexreview_db",
        description="Database connection URL"
    )
    postgres_host: Optional[str] = Field(
        default=None,
        description="PostgreSQL host (overrides DATABASE_URL if set)"
    )
    postgres_port: Optional[int] = Field(
        default=None,
        description="PostgreSQL port"
    )
    postgres_user: Optional[str] = Field(
        default=None,
        description="PostgreSQL user"
    )
    postgres_password: Optional[str] = Field(
        default=None,
        description="PostgreSQL password"
    )
    postgres_db: Optional[str] = Field(
        default=None,
        description="PostgreSQL database name"
    )
    database_echo: bool = Field(
        default=False,
        description="Echo SQL queries (for debugging)"
    )
    
    @model_validator(mode="after")
    def build_database_url(self):
        """Build database URL from components if not provided"""
        # If DATABASE_URL is explicitly set, use it
        if self.database_url and not any([
            self.postgres_host, self.postgres_user, 
            self.postgres_password, self.postgres_db
        ]):
            return self
        
        # Build from components
        if all([self.postgres_host, self.postgres_user, self.postgres_password, self.postgres_db]):
            port = self.postgres_port or 5432
            self.database_url = (
                f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{port}/{self.postgres_db}"
            )
        
        return self
    

settings = Settings()

