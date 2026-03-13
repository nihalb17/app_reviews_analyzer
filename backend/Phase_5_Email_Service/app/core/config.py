"""Configuration for Phase 5 Email Service"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Resend Configuration
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "onboarding@resend.dev"
    
    # Role-based email mappings
    PRODUCT_TEAM_EMAIL: str = ""
    SUPPORT_TEAM_EMAIL: str = ""
    UI_UX_TEAM_EMAIL: str = ""
    LEADERSHIP_TEAM_EMAIL: str = ""
    
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
        return role_emails.get(role, "")


settings = Settings()
