from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # OpenAI settings
    OPENAI_API_KEY: str
    
    # OpenAlex settings
    OPENALEX_EMAIL: Optional[str] = None  # Optional email for polite API usage
    
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Search settings
    DEFAULT_MAX_RESULTS: int = 10
    CACHE_TTL: int = 3600  # 1 hour in seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 