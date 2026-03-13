"""Configuration for Phase 5 Email Service"""
from pydantic_settings import BaseSettings
from typing import Dict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # SMTP Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    
    # Role-based email mappings
    PRODUCT_TEAM_EMAIL: str = ""
    SUPPORT_TEAM_EMAIL: str = ""
    UI_UX_TEAM_EMAIL: str = ""
    LEADERSHIP_TEAM_EMAIL: str = ""
    
    # Default sender
    DEFAULT_SENDER: str = ""
    
    class Config:
        env_file = "../../.env"
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    def get_role_email(self, role: str) -> str:
        """Get email address for a specific role"""
        role_emails = {
            'Product': self.PRODUCT_TEAM_EMAIL,
            'Support': self.SUPPORT_TEAM_EMAIL,
            'UI/UX': self.UI_UX_TEAM_EMAIL,
            'Leadership': self.LEADERSHIP_TEAM_EMAIL
        }
        return role_emails.get(role, self.DEFAULT_SENDER)


settings = Settings()
