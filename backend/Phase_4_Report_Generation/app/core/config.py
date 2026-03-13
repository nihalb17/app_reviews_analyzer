"""
Phase 4 Configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Groww Brand Colors
    GROWW_PRIMARY_COLOR: str = "#00D09C"
    GROWW_SECONDARY_COLOR: str = "#5367FF"
    GROWW_BACKGROUND: str = "#FFFFFF"
    GROWW_TEXT_PRIMARY: str = "#1A1A1A"
    GROWW_TEXT_SECONDARY: str = "#6C6C6C"
    
    # Report Settings
    REPORT_TITLE: str = "Reviews Insights Report"
    COMPANY_NAME: str = "Groww"
    
    # Paths
    TEMPLATES_DIR: str = "app/templates"
    OUTPUT_DIR: str = "data"
    
    class Config:
        env_file = "../../.env"
        env_file_encoding = "utf-8"
        extra = "allow"  # Allow extra fields from .env


settings = Settings()
