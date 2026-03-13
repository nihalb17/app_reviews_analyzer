from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

# Find root .env file - go up from app/core/config.py to project root
# app/core/config.py -> app/core -> app -> Phase_3_Insight_Generation -> backend -> app_reviews_analyzer
ROOT_DIR = Path(__file__).parent.parent.parent.parent.parent
ENV_FILE = ROOT_DIR / ".env"


class Settings(BaseSettings):
    # LLM API Keys
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    
    # Groq Model
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    
    # Gemini Model
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    # App Settings
    DEBUG: bool = True
    
    class Config:
        env_file = str(ENV_FILE)
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
