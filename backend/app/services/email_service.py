"""
Email service for sending password reset tokens and other notifications.
Provides secure, templated email functionality for financial applications.
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from typing import Optional, Dict, Any
import logging
from datetime import datetime
import os
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailConfig:
    """Email configuration with security best practices."""
    
    def __init__(self):
        # Email server configuration (environment variables)
        self.smtp_host = os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        
        # Email sender configuration
        self.from_email = os.getenv("FROM_EMAIL", "noreply@fingood.com")
        self.from_name = os.getenv("FROM_NAME", "FinGood Security")
        
        # Template configuration
        self.template_dir = Path(__file__).parent.parent / "templates" / "emails"
        
        # Security settings
        self.enable_email_security_headers = True
        self.max_recipients_per_email = 1  # Security: limit recipients
        self.email_timeout_seconds = 30
        
    def is_configured(self) -> bool:
        """Check if email service is properly configured."""
        return bool(
            self.smtp_host and 
            self.smtp_user and 
            self.smtp_password and
            self.from_email
        )


class EmailService:
    """
    Secure email service for password reset and notifications.
    Implements security best practices for financial applications.
    """
    
    def __init__(self):
        self.config = EmailConfig()
        self._template_env = None
        
        # Initialize Jinja2 template environment
        if self.config.template_dir.exists():
            self._template_env = Environment(
                loader=FileSystemLoader(str(self.config.template_dir)),
                autoescape=True  # Security: auto-escape HTML
            )
    
    def _get_smtp_connection(self) -> smtplib.SMTP:
        """Create secure SMTP connection with TLS."""
        try:
            # Create SMTP connection
            server = smtplib.SMTP(
                self.config.smtp_host, 
                self.config.smtp_port,
                timeout=self.config.email_timeout_seconds
            )
            
            # Enable debug logging in development
            if settings.DEBUG:
                server.set_debuglevel(1)
            
            # Start TLS encryption
            if self.config.smtp_use_tls:
                context = ssl.create_default_context()
                server.starttls(context=context)
            
            # Authenticate
            if self.config.smtp_user and self.config.smtp_password:
                server.login(self.config.smtp_user, self.config.smtp_password)
            
            return server
            
        except Exception as e:
            logger.error(f"Failed to create SMTP connection: {e}")
            raise EmailServiceException(f"Email service unavailable: {str(e)}")
    
    def _create_message(
        self, 
        to_email: str, 
        subject: str, 
        html_body: str,
        text_body: Optional[str] = None
    ) -> MIMEMultipart:
        """Create secure email message with proper headers."""
        
        # Create message
        msg = MIMEMultipart("alternative")
        
        # Set headers
        msg["Subject"] = subject
        msg["From"] = formataddr((self.config.from_name, self.config.from_email))
        msg["To"] = to_email
        msg["Date"] = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
        
        # Add security headers
        if self.config.enable_email_security_headers:
            msg["X-Mailer"] = "FinGood Security System"
            msg["X-Priority"] = "3"  # Normal priority
            msg["X-MSMail-Priority"] = "Normal"
            msg["Importance"] = "Normal"
        
        # Add text version (fallback)
        if text_body:
            text_part = MIMEText(text_body, "plain", "utf-8")
            msg.attach(text_part)
        
        # Add HTML version
        html_part = MIMEText(html_body, "html", "utf-8")
        msg.attach(html_part)
        
        return msg
    
    def _render_template(self, template_name: str, **kwargs) -> tuple[str, str]:
        """Render email template with context data."""
        if not self._template_env:
            # Fallback to simple template if Jinja2 not available
            return self._render_simple_template(template_name, **kwargs)
        
        try:
            # Load HTML template
            html_template = self._template_env.get_template(f"{template_name}.html")
            html_content = html_template.render(**kwargs)
            
            # Load text template (optional)
            text_content = None
            try:
                text_template = self._template_env.get_template(f"{template_name}.txt")
                text_content = text_template.render(**kwargs)
            except:
                # Generate simple text version from HTML
                text_content = self._html_to_text(html_content)
            
            return html_content, text_content
            
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            return self._render_simple_template(template_name, **kwargs)
    
    def _render_simple_template(self, template_name: str, **kwargs) -> tuple[str, str]:
        """Simple fallback template rendering."""
        if template_name == "password_reset":
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c3e50;">Password Reset Request</h2>
                    <p>Hello {kwargs.get('user_name', 'User')},</p>
                    <p>We received a request to reset your password for your FinGood account.</p>
                    <p>Click the link below to reset your password. This link will expire in 1 hour:</p>
                    <p style="margin: 20px 0;">
                        <a href="{kwargs.get('reset_link')}" 
                           style="background-color: #3498db; color: white; padding: 12px 24px; 
                                  text-decoration: none; border-radius: 4px; display: inline-block;">
                            Reset Password
                        </a>
                    </p>
                    <p>If you didn't request this password reset, please ignore this email.</p>
                    <p>For security reasons, this link will expire on {kwargs.get('expires_at')}.</p>
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                    <p style="color: #666; font-size: 12px;">
                        This is an automated message from FinGood Security. Please do not reply to this email.
                    </p>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
Password Reset Request

Hello {kwargs.get('user_name', 'User')},

We received a request to reset your password for your FinGood account.

Reset your password by visiting this link:
{kwargs.get('reset_link')}

This link will expire in 1 hour ({kwargs.get('expires_at')}).

If you didn't request this password reset, please ignore this email.

---
This is an automated message from FinGood Security. Please do not reply to this email.
            """
            
            return html_content, text_content
        
        # Default template
        return "<p>Email content</p>", "Email content"
    
    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML to plain text (basic implementation)."""
        import re
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html_content)
        
        # Decode HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        
        # Clean up whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()
        
        return text
    
    async def send_password_reset_email(
        self,
        user_email: str,
        user_name: str,
        reset_token: str,
        expires_at: datetime
    ) -> bool:
        """
        Send password reset email with secure token.
        
        Args:
            user_email: Recipient email address
            user_name: User's full name
            reset_token: Secure reset token
            expires_at: Token expiration time
            
        Returns:
            bool: True if email sent successfully
        """
        if not self.config.is_configured():
            logger.error("Email service not configured - cannot send password reset email")
            return False
        
        try:
            # Create reset link (this should match your frontend reset page)
            reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
            
            # Prepare template context
            template_context = {
                "user_name": user_name,
                "user_email": user_email,
                "reset_link": reset_link,
                "reset_token": reset_token,
                "expires_at": expires_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "company_name": "FinGood",
                "support_email": "support@fingood.com"
            }
            
            # Render email template
            html_content, text_content = self._render_template(
                "password_reset", 
                **template_context
            )
            
            # Create and send email
            subject = "Password Reset Request - FinGood"
            await self._send_email(
                to_email=user_email,
                subject=subject,
                html_body=html_content,
                text_body=text_content
            )
            
            logger.info(
                f"Password reset email sent successfully to {user_email}",
                extra={
                    "user_email": user_email,
                    "expires_at": expires_at.isoformat(),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to send password reset email to {user_email}: {e}",
                extra={
                    "user_email": user_email,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            return False
    
    async def _send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> None:
        """Send email with proper error handling and security."""
        
        # Validate email address (basic validation)
        if not self._is_valid_email(to_email):
            raise EmailServiceException(f"Invalid email address: {to_email}")
        
        # Create message
        message = self._create_message(to_email, subject, html_body, text_body)
        
        # Send email
        with self._get_smtp_connection() as server:
            server.send_message(message)
    
    def _is_valid_email(self, email: str) -> bool:
        """Basic email validation."""
        import re
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None


class EmailServiceException(Exception):
    """Exception raised by email service."""
    pass


# Global email service instance
_email_service_instance = None


def get_email_service() -> EmailService:
    """Get global email service instance."""
    global _email_service_instance
    
    if _email_service_instance is None:
        _email_service_instance = EmailService()
    
    return _email_service_instance