from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

# Find root .env file - go up from app/core/config.py to project root
# app/core/config.py -> app/core -> app -> Phase_4_MCP_Integration -> backend -> app_reviews_analyzer
ROOT_DIR = Path(__file__).parent.parent.parent.parent.parent
ENV_FILE = ROOT_DIR / ".env"


class Settings(BaseSettings):
    # Google Doc Configuration
    GOOGLE_DOC_ID: str = ""
    
    # Google OAuth Credentials (for MCP)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    
    # Data directories
    DATA_DIR: Path = Path(__file__).parent.parent.parent / "data"
    
    # Phase 3 data paths (for reading reviews JSON)
    PHASE3_DATA_DIR: Path = ROOT_DIR / "backend" / "Phase_3_Insight_Generation" / "data"
    
    # Phase 3.5 data paths (for reading fee explainer JSON)
    PHASE35_DATA_DIR: Path = ROOT_DIR / "backend" / "Phase_3_5_Fee_Explainer" / "data"
    
    # App Settings
    DEBUG: bool = True
    
    class Config:
        env_file = str(ENV_FILE)
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
