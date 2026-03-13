from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

# Find root .env file - go up from app/core/config.py to project root
# app/core/config.py -> app/core -> app -> Phase_2_Theme_Extraction_Classification -> backend -> app_reviews_analyzer
ROOT_DIR = Path(__file__).parent.parent.parent.parent.parent
ENV_FILE = ROOT_DIR / ".env"


class Settings(BaseSettings):
    # LLM API Keys
    GROQ_API_KEY: str = ""
    GROQ_API_KEY_FALLBACK: str = ""  # Fallback key if primary hits rate limit
    GEMINI_API_KEY: str = ""
    
    # Groq Model
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    
    # Gemini Model
    GEMINI_MODEL: str = "gemini-2.0-flash"
    
    # App Settings
    DEBUG: bool = True
    
    class Config:
        env_file = str(ENV_FILE)
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
