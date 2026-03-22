from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

# Find root .env file - go up from app/core/config.py to project root
# app/core/config.py -> app/core -> app -> Phase_3_5_Fee_Explainer -> backend -> app_reviews_analyzer
ROOT_DIR = Path(__file__).parent.parent.parent.parent.parent
ENV_FILE = ROOT_DIR / ".env"


class Settings(BaseSettings):
    # LLM API Keys
    GROQ_API_KEY_FEE_EXPLAINER: str = ""
    
    # Groq Model for Fee Explainer
    GROQ_MODEL_FEE_EXPLAINER: str = "llama-3.3-70b-versatile"
    
    # Google Doc Configuration
    GOOGLE_DOC_ID: str = ""
    
    # App Settings
    DEBUG: bool = True
    
    # Data directories
    DATA_DIR: Path = Path(__file__).parent.parent.parent / "data"
    
    class Config:
        env_file = str(ENV_FILE)
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
