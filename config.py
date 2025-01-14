from pydantic_settings import BaseSettings
from pydantic import SecretStr, Field, Extra

class SearchEngineConfig(BaseSettings):
    """Search engine API configurations."""
    GOOGLE_API_KEY: SecretStr | None = None
    DUCKDUCKGO_API_KEY: SecretStr | None = None
    SERPER_API_KEY: SecretStr | None = None
    # Add the redis_url field
    redis_url: str = 'redis://localhost:6379'  # default value
    
    class Config:
        env_file = ".env"
        extra = Extra.allow
        alias_generator = str.upper

class QueueConfig(BaseSettings):
    """Message queue configurations."""
    REDIS_URL: str = Field("redis://localhost:6379", exclude=True)
    QUEUE_TIMEOUT: int = 300
    MAX_RETRIES: int = 3

    class Config:
        extra = Extra.allow

class Settings(BaseSettings):
    """Application settings."""
    MAX_CONCURRENT_REQUESTS: int = 5
    CACHE_TIMEOUT: int = 3600
    TELEMETRY_URL: str = "http://localhost:4317"
    search_engines: SearchEngineConfig = SearchEngineConfig()
    queue: QueueConfig = QueueConfig()
    
    class Config:
        env_file = ".env"
        extra = Extra.allow

settings = Settings()