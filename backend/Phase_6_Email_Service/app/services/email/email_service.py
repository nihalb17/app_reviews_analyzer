"""Email Service for sending reports via Resend API"""
import logging
import base64
from pathlib import Path
from typing import Optional, List

import requests

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email reports with PDF attachments via Resend API"""
    
    RESEND_API_URL = "https://api.resend.com/emails"
    
    def __init__(self):
        self.api_key = settings.RESEND_API_KEY
        self.from_email = settings.RESEND_FROM_EMAIL
        
        if not self.api_key:
            logger.warning("RESEND_API_KEY not configured. Email sending will fail.")
    
    def send_report(
        self,
        role: str,
        recipient: str,
        html_file: str,
        pdf_file: str,
        subject: Optional[str] = None
    ) -> bool:
        """
        Send report email with HTML body and PDF attachment via Resend API
        
        Args:
            role: Target role (Product, Support, UI/UX, Leadership)
            recipient: Email address to send to
            html_file: Path to HTML file for email body
            pdf_file: Path to PDF file to attach
            subject: Optional custom subject line
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            if not self.api_key:
                logger.error("RESEND_API_KEY not configured")
                return False
            
            # Read HTML content
            html_path = Path(html_file)
            if not html_path.exists():
                logger.error(f"HTML file not found: {html_file}")
                return False
            
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Prepare attachments
            attachments: List[dict] = []
            
            # Attach PDF
            pdf_path = Path(pdf_file)
            if pdf_path.exists():
                with open(pdf_path, 'rb') as f:
                    pdf_content = f.read()
                    pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
                
                # Sanitize role name for filename
                safe_role = role.lower().replace('/', '_')
                attachments.append({
                    "filename": f"groww_insights_{safe_role}.pdf",
                    "content": pdf_base64
                })
            else:
                logger.warning(f"PDF file not found: {pdf_file}")
            
            # Prepare email payload
            email_subject = subject or f"Groww Playstore Reviews Insights - {role} Team"
            
            payload = {
                "from": self.from_email,
                "to": [recipient],
                "subject": email_subject,
                "html": html_content,
            }
            
            if attachments:
                payload["attachments"] = attachments
            
            # Send via Resend API
            logger.info(f"Sending email via Resend API to {recipient}")
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                self.RESEND_API_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✓ Email sent successfully to {recipient}, ID: {result.get('id')}")
                return True
            else:
                logger.error(f"✗ Resend API error: {response.status_code} - {response.text}")
                return False
            
        except Exception as e:
            logger.error(f"✗ Failed to send email: {str(e)}")
            return False
