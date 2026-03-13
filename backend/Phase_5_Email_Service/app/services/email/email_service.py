"""Email Service for sending reports via SMTP"""
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email reports with PDF attachments"""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_pass = settings.SMTP_PASSWORD
        self.default_sender = settings.DEFAULT_SENDER or self.smtp_user
    
    def send_report(
        self,
        role: str,
        recipient: str,
        html_file: str,
        pdf_file: str,
        subject: Optional[str] = None
    ) -> bool:
        """
        Send report email with HTML body and PDF attachment
        
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
            # Read HTML content
            html_path = Path(html_file)
            if not html_path.exists():
                logger.error(f"HTML file not found: {html_file}")
                return False
            
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.default_sender
            msg['To'] = recipient
            
            if subject:
                msg['Subject'] = subject
            else:
                msg['Subject'] = f"Groww Playstore Reviews Insights - {role} Team"
            
            # Attach HTML body
            msg.attach(MIMEText(html_content, 'html'))
            
            # Attach PDF
            pdf_path = Path(pdf_file)
            if pdf_path.exists():
                with open(pdf_path, 'rb') as f:
                    pdf_attachment = MIMEBase('application', 'pdf')
                    pdf_attachment.set_payload(f.read())
                    encoders.encode_base64(pdf_attachment)
                    
                    # Sanitize role name for filename
                    safe_role = role.lower().replace('/', '_')
                    pdf_attachment.add_header(
                        'Content-Disposition',
                        f'attachment; filename="groww_insights_{safe_role}.pdf"'
                    )
                    msg.attach(pdf_attachment)
            else:
                logger.warning(f"PDF file not found: {pdf_file}")
            
            # Send email
            logger.info(f"Connecting to SMTP server {self.smtp_host}:{self.smtp_port}")
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                
                logger.info(f"Sending email to {recipient}")
                server.send_message(msg)
                logger.info(f"✓ Email sent successfully to {recipient}")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to send email: {str(e)}")
            return False
