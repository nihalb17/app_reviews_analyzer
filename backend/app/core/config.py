from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/groww_reviews"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # App Settings
    APP_NAME: str = "Groww Reviews Analyser"
    DEBUG: bool = True
    
    # Play Store Settings
    APP_PACKAGE: str = "com.nextbillion.groww"
    MAX_REVIEWS: int = 2000
    
    # Filtering Settings
    MIN_WORDS: int = 5
    LANG_CONFIDENCE: float = 0.9
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
