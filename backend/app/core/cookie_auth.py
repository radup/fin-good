"""
Secure cookie-based authentication for FinGood financial application.
Implements HttpOnly cookies with comprehensive security measures.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import HTTPException, Request, Response, status, Depends
from fastapi.security.base import SecurityBase
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import jwt_manager, TokenExpiredError, TokenRevokedError, TokenInvalidError
from app.core.database import get_db
from app.models.user import User

# Configure cookie auth logging
cookie_auth_logger = logging.getLogger("fingood.cookie_auth")


class CookieAuthError(Exception):
    """Base exception for cookie authentication errors."""
    pass


class CookieSecurityError(CookieAuthError):
    """Cookie security validation failed."""
    pass


class CookieAuth(SecurityBase):
    """
    Cookie-based authentication security scheme.
    Replaces OAuth2PasswordBearer for secure cookie authentication.
    """
    
    def __init__(self):
        self.model_name = "CookieAuth"
        self.scheme_name = "CookieAuth"
    
    async def __call__(self, request: Request) -> Optional[str]:
        """
        Extract JWT token from secure cookie.
        
        Args:
            request: FastAPI request object
            
        Returns:
            JWT token string if present
            
        Raises:
            HTTPException: If token is missing or invalid
        """
        try:
            token = self._extract_token_from_cookie(request)
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required - no valid session found",
                    headers={"WWW-Authenticate": "Cookie"},
                )
            return token
            
        except Exception as e:
            cookie_auth_logger.error(f"Cookie authentication error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed - invalid session",
                headers={"WWW-Authenticate": "Cookie"},
            )
    
    def _extract_token_from_cookie(self, request: Request) -> Optional[str]:
        """Extract JWT token from cookie."""
        return request.cookies.get(settings.COOKIE_NAME)


class CookieManager:
    """
    Secure cookie management for JWT tokens.
    Implements comprehensive security measures for financial applications.
    """
    
    def __init__(self, test_settings=None):
        # Use test settings if provided, otherwise use global settings
        config = test_settings if test_settings else settings
        
        if config is None:
            # Fallback for testing when settings are not initialized
            self.cookie_name = "fingood_auth"
            self.secure = False  # Allow HTTP for testing
            self.httponly = True
            self.samesite = "lax"
            self.domain = None
            self.max_age = 30 * 60  # 30 minutes
        else:
            self.cookie_name = config.COOKIE_NAME
            self.secure = config.COOKIE_SECURE
            self.httponly = config.COOKIE_HTTPONLY
            self.samesite = config.COOKIE_SAMESITE
            self.domain = config.COOKIE_DOMAIN
            self.max_age = config.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    def set_auth_cookie(
        self, 
        response: Response, 
        token: str,
        user_id: Optional[int] = None
    ) -> None:
        """
        Set secure authentication cookie with JWT token.
        
        Args:
            response: FastAPI response object
            token: JWT token to store in cookie
            user_id: Optional user ID for logging
        """
        try:
            # Validate cookie security settings
            self._validate_cookie_security()
            
            # Set the secure cookie
            response.set_cookie(
                key=self.cookie_name,
                value=token,
                max_age=self.max_age,
                httponly=self.httponly,
                secure=self.secure,
                samesite=self.samesite,
                domain=self.domain,
                path="/"
            )
            
            cookie_auth_logger.info(
                f"Authentication cookie set - User: {user_id}, "
                f"Expires: {datetime.utcnow() + timedelta(seconds=self.max_age)}"
            )
            
        except Exception as e:
            cookie_auth_logger.error(f"Failed to set auth cookie: {str(e)}")
            raise CookieAuthError(f"Failed to set authentication cookie: {str(e)}")
    
    def clear_auth_cookie(
        self, 
        response: Response,
        user_id: Optional[int] = None
    ) -> None:
        """
        Clear authentication cookie securely.
        
        Args:
            response: FastAPI response object
            user_id: Optional user ID for logging
        """
        try:
            # Delete the cookie
            response.delete_cookie(
                key=self.cookie_name,
                secure=self.secure,
                samesite=self.samesite,
                domain=self.domain,
                path="/"
            )
            
            cookie_auth_logger.info(f"Authentication cookie cleared - User: {user_id}")
            
        except Exception as e:
            cookie_auth_logger.error(f"Failed to clear auth cookie: {str(e)}")
            # Don't raise exception for cookie clearing failures
    
    def extract_token_from_request(self, request: Request) -> Optional[str]:
        """
        Extract JWT token from request cookies.
        
        Args:
            request: FastAPI request object
            
        Returns:
            JWT token if present, None otherwise
        """
        try:
            token = request.cookies.get(self.cookie_name)
            
            if token:
                cookie_auth_logger.debug("Authentication token extracted from cookie")
            else:
                cookie_auth_logger.debug("No authentication token found in cookies")
            
            return token
            
        except Exception as e:
            cookie_auth_logger.error(f"Failed to extract token from cookies: {str(e)}")
            return None
    
    def validate_cookie_security(self) -> bool:
        """
        Validate that cookie security settings meet financial app requirements.
        
        Returns:
            True if settings are secure
            
        Raises:
            CookieSecurityError: If security settings are insufficient
        """
        try:
            self._validate_cookie_security()
            return True
            
        except CookieSecurityError:
            raise
        except Exception as e:
            cookie_auth_logger.error(f"Cookie security validation error: {str(e)}")
            raise CookieSecurityError(f"Cookie security validation failed: {str(e)}")
    
    def _validate_cookie_security(self) -> None:
        """Internal method to validate cookie security settings."""
        errors = []
        
        # Validate HttpOnly setting
        if not self.httponly:
            errors.append("Cookie must be HttpOnly for XSS protection")
        
        # Validate SameSite setting
        if self.samesite.lower() not in ["strict", "lax"]:
            errors.append("Cookie SameSite must be 'strict' or 'lax' for CSRF protection")
        
        # Validate Secure setting for production
        # Skip DEBUG check if settings is None (testing mode)
        if settings is not None and settings.DEBUG is False and not self.secure:
            errors.append("Cookie must be Secure in production environment")
        
        # Validate expiration time
        if self.max_age > 86400:  # 24 hours
            errors.append("Cookie expiration should not exceed 24 hours for financial applications")
        
        if errors:
            error_msg = "; ".join(errors)
            cookie_auth_logger.error(f"Cookie security validation failed: {error_msg}")
            raise CookieSecurityError(f"Insecure cookie configuration: {error_msg}")


# Global instances
cookie_auth = CookieAuth()
cookie_manager = CookieManager()


async def get_current_user_from_cookie(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from cookie-based JWT token.
    
    Args:
        request: FastAPI request object
        db: Database session
        
    Returns:
        Authenticated user object
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials - please log in again",
        headers={"WWW-Authenticate": "Cookie"},
    )
    
    try:
        # Extract token from cookie
        token = cookie_manager.extract_token_from_request(request)
        if not token:
            cookie_auth_logger.warning("No authentication token found in request")
            raise credentials_exception
        
        # Verify token using JWT manager
        payload = jwt_manager.verify_token(token, db, request)
        email: str = payload.get("sub")
        
        if email is None:
            cookie_auth_logger.warning("No email found in token payload")
            raise credentials_exception
        
        # Get user from database
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            cookie_auth_logger.warning(f"User not found for email: {email}")
            raise credentials_exception
        
        # Check if user is active
        if not user.is_active:
            cookie_auth_logger.warning(f"Inactive user attempted access: {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive - please contact support"
            )
        
        cookie_auth_logger.info(f"User authenticated successfully: {email}")
        return user
        
    except TokenExpiredError:
        cookie_auth_logger.warning("Expired token attempted authentication")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired - please log in again",
            headers={"WWW-Authenticate": "Cookie"},
        )
    
    except TokenRevokedError:
        cookie_auth_logger.warning("Revoked token attempted authentication")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been revoked - please log in again",
            headers={"WWW-Authenticate": "Cookie"},
        )
    
    except TokenInvalidError:
        cookie_auth_logger.warning("Invalid token attempted authentication")
        raise credentials_exception
    
    except HTTPException:
        raise
    
    except Exception as e:
        cookie_auth_logger.error(f"Unexpected authentication error: {str(e)}")
        raise credentials_exception


# Convenience functions
def set_auth_cookie(response: Response, token: str, user_id: Optional[int] = None) -> None:
    """Set authentication cookie."""
    cookie_manager.set_auth_cookie(response, token, user_id)


def clear_auth_cookie(response: Response, user_id: Optional[int] = None) -> None:
    """Clear authentication cookie."""
    cookie_manager.clear_auth_cookie(response, user_id)


def extract_token_from_request(request: Request) -> Optional[str]:
    """Extract JWT token from request."""
    return cookie_manager.extract_token_from_request(request)