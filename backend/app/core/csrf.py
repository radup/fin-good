"""
CSRF protection for FinGood financial application.
Implements secure CSRF token generation and validation with double-submit cookies.
"""

import hashlib
import hmac
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, Request, Response, status
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.core.config import settings

# Configure CSRF logging
csrf_logger = logging.getLogger("fingood.csrf")


class CSRFError(Exception):
    """Base exception for CSRF protection errors."""
    pass


class CSRFTokenMissingError(CSRFError):
    """CSRF token is missing from request."""
    pass


class CSRFTokenInvalidError(CSRFError):
    """CSRF token is invalid or expired."""
    pass


class CSRFProtection:
    """
    CSRF protection implementation using double-submit cookies pattern.
    Provides robust protection against CSRF attacks for financial applications.
    """
    
    def __init__(self, test_settings=None):
        # Use test settings if provided, otherwise use global settings
        config = test_settings if test_settings else settings
        
        if config is None:
            # Fallback for testing when settings are not initialized
            self.secret_key = "test-csrf-secret-key-for-testing-only"
            self.expire_minutes = 60
            self.cookie_name = "fingood_auth_csrf"
            self.header_name = "X-CSRF-Token"
        else:
            self.secret_key = config.CSRF_SECRET_KEY
            self.expire_minutes = config.CSRF_TOKEN_EXPIRE_MINUTES
            self.cookie_name = f"{config.COOKIE_NAME}_csrf"
            self.header_name = "X-CSRF-Token"
        
        self.serializer = URLSafeTimedSerializer(self.secret_key)
    
    def generate_csrf_token(self, user_id: Optional[int] = None) -> str:
        """
        Generate a secure CSRF token.
        
        Args:
            user_id: Optional user ID to bind token to specific user
            
        Returns:
            Secure CSRF token string
        """
        try:
            # Create token payload
            payload = {
                "timestamp": datetime.utcnow().isoformat(),
                "nonce": secrets.token_urlsafe(16),
                "user_id": user_id
            }
            
            # Sign the payload (expiration is handled during verification)
            token = self.serializer.dumps(payload)
            
            csrf_logger.info(f"CSRF token generated for user: {user_id}")
            return token
            
        except Exception as e:
            csrf_logger.error(f"Failed to generate CSRF token: {str(e)}")
            raise CSRFError(f"CSRF token generation failed: {str(e)}")
    
    def validate_csrf_token(
        self, 
        token: str, 
        user_id: Optional[int] = None,
        request: Optional[Request] = None
    ) -> bool:
        """
        Validate a CSRF token.
        
        Args:
            token: CSRF token to validate
            user_id: Optional user ID to verify token binding
            request: Optional request for audit logging
            
        Returns:
            True if token is valid, False otherwise
            
        Raises:
            CSRFTokenInvalidError: If token is invalid or expired
        """
        try:
            # Deserialize and validate token
            payload = self.serializer.loads(
                token, 
                max_age=self.expire_minutes * 60
            )
            
            # Verify user binding if provided
            if user_id is not None and payload.get("user_id") != user_id:
                csrf_logger.warning(
                    f"CSRF token user mismatch - Expected: {user_id}, "
                    f"Token user: {payload.get('user_id')}"
                )
                return False
            
            csrf_logger.info(f"CSRF token validated for user: {user_id}")
            return True
            
        except SignatureExpired:
            csrf_logger.warning(f"Expired CSRF token attempted for user: {user_id}")
            raise CSRFTokenInvalidError("CSRF token has expired")
            
        except BadSignature:
            csrf_logger.warning(f"Invalid CSRF token attempted for user: {user_id}")
            raise CSRFTokenInvalidError("Invalid CSRF token")
            
        except Exception as e:
            csrf_logger.error(f"CSRF token validation error: {str(e)}")
            raise CSRFTokenInvalidError(f"CSRF validation failed: {str(e)}")
    
    def set_csrf_cookie(self, response: Response, token: str) -> None:
        """
        Set CSRF token as secure cookie.
        
        Args:
            response: FastAPI response object
            token: CSRF token to set
        """
        try:
            response.set_cookie(
                key=self.cookie_name,
                value=token,
                max_age=self.expire_minutes * 60,
                httponly=False,  # Client needs to read this for headers
                secure=settings.COOKIE_SECURE,
                samesite=settings.COOKIE_SAMESITE,
                domain=settings.COOKIE_DOMAIN
            )
            
            csrf_logger.debug("CSRF cookie set successfully")
            
        except Exception as e:
            csrf_logger.error(f"Failed to set CSRF cookie: {str(e)}")
            raise CSRFError(f"Failed to set CSRF cookie: {str(e)}")
    
    def clear_csrf_cookie(self, response: Response) -> None:
        """
        Clear CSRF token cookie.
        
        Args:
            response: FastAPI response object
        """
        try:
            response.delete_cookie(
                key=self.cookie_name,
                secure=settings.COOKIE_SECURE,
                samesite=settings.COOKIE_SAMESITE,
                domain=settings.COOKIE_DOMAIN
            )
            
            csrf_logger.debug("CSRF cookie cleared successfully")
            
        except Exception as e:
            csrf_logger.error(f"Failed to clear CSRF cookie: {str(e)}")
    
    def extract_csrf_tokens(self, request: Request) -> tuple[Optional[str], Optional[str]]:
        """
        Extract CSRF tokens from request (cookie and header).
        
        Args:
            request: FastAPI request object
            
        Returns:
            Tuple of (cookie_token, header_token)
        """
        try:
            # Get token from cookie
            cookie_token = request.cookies.get(self.cookie_name)
            
            # Get token from header
            header_token = request.headers.get(self.header_name)
            
            return cookie_token, header_token
            
        except Exception as e:
            csrf_logger.error(f"Failed to extract CSRF tokens: {str(e)}")
            return None, None
    
    def verify_double_submit(
        self, 
        request: Request, 
        user_id: Optional[int] = None
    ) -> bool:
        """
        Verify CSRF protection using double-submit pattern.
        
        Args:
            request: FastAPI request object
            user_id: Optional user ID for token binding
            
        Returns:
            True if CSRF protection passes
            
        Raises:
            CSRFTokenMissingError: If tokens are missing
            CSRFTokenInvalidError: If tokens are invalid or don't match
        """
        try:
            cookie_token, header_token = self.extract_csrf_tokens(request)
            
            # Check if tokens are present
            if not cookie_token:
                raise CSRFTokenMissingError("CSRF cookie token missing")
            
            if not header_token:
                raise CSRFTokenMissingError("CSRF header token missing")
            
            # Validate cookie token
            if not self.validate_csrf_token(cookie_token, user_id, request):
                raise CSRFTokenInvalidError("Invalid CSRF cookie token")
            
            # Verify tokens match (double-submit pattern)
            if not hmac.compare_digest(cookie_token, header_token):
                csrf_logger.warning(
                    f"CSRF token mismatch - User: {user_id}, "
                    f"IP: {self._get_client_ip(request)}"
                )
                raise CSRFTokenInvalidError("CSRF tokens do not match")
            
            csrf_logger.info(f"CSRF protection verified for user: {user_id}")
            return True
            
        except (CSRFTokenMissingError, CSRFTokenInvalidError):
            raise
        except Exception as e:
            csrf_logger.error(f"CSRF verification error: {str(e)}")
            raise CSRFTokenInvalidError(f"CSRF verification failed: {str(e)}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request headers."""
        # Check for forwarded headers (common in load balancer setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"


# Global CSRF protection instance
csrf_protection = CSRFProtection()


# Convenience functions
def generate_csrf_token(user_id: Optional[int] = None) -> str:
    """Generate a CSRF token."""
    return csrf_protection.generate_csrf_token(user_id)


def verify_csrf_protection(request: Request, user_id: Optional[int] = None) -> bool:
    """Verify CSRF protection for a request."""
    return csrf_protection.verify_double_submit(request, user_id)


def set_csrf_cookie(response: Response, token: str) -> None:
    """Set CSRF token cookie."""
    csrf_protection.set_csrf_cookie(response, token)


def clear_csrf_cookie(response: Response) -> None:
    """Clear CSRF token cookie."""
    csrf_protection.clear_csrf_cookie(response)