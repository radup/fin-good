"""
Comprehensive error handling for cookie-based authentication failures.
Provides detailed error responses and security logging for FinGood.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.cookie_auth import clear_auth_cookie
from app.core.csrf import clear_csrf_cookie

# Configure cookie error logging
cookie_error_logger = logging.getLogger("fingood.cookie_errors")


class CookieErrorHandler:
    """
    Handles cookie-related authentication and security errors.
    Provides consistent error responses and cleanup for failed authentication.
    """
    
    @staticmethod
    def handle_authentication_error(
        error: Exception,
        request: Request,
        response: Optional[Response] = None,
        user_id: Optional[int] = None
    ) -> JSONResponse:
        """
        Handle authentication errors with proper cookie cleanup.
        
        Args:
            error: The authentication error that occurred
            request: FastAPI request object
            response: Optional response object for cookie cleanup
            user_id: Optional user ID for logging
            
        Returns:
            JSON error response
        """
        try:
            # Log the authentication error
            client_ip = CookieErrorHandler._get_client_ip(request)
            user_agent = request.headers.get("User-Agent", "unknown")
            
            cookie_error_logger.warning(
                f"Authentication error - User: {user_id}, IP: {client_ip}, "
                f"User-Agent: {user_agent}, Error: {str(error)}"
            )
            
            # Create error response
            error_response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Authentication failed - please log in again",
                    "error_type": "authentication_error",
                    "requires_login": True
                },
                headers={"WWW-Authenticate": "Cookie"}
            )
            
            # Clear authentication cookies on error
            if response:
                clear_auth_cookie(response, user_id)
                clear_csrf_cookie(response)
            else:
                # Clear cookies on the error response
                clear_auth_cookie(error_response, user_id)
                clear_csrf_cookie(error_response)
            
            return error_response
            
        except Exception as cleanup_error:
            cookie_error_logger.error(f"Error during auth error cleanup: {str(cleanup_error)}")
            
            # Return basic error response if cleanup fails
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Authentication failed",
                    "error_type": "authentication_error",
                    "requires_login": True
                }
            )
    
    @staticmethod
    def handle_csrf_error(
        error: Exception,
        request: Request,
        response: Optional[Response] = None
    ) -> JSONResponse:
        """
        Handle CSRF protection errors.
        
        Args:
            error: The CSRF error that occurred
            request: FastAPI request object
            response: Optional response object
            
        Returns:
            JSON error response
        """
        try:
            # Log the CSRF error
            client_ip = CookieErrorHandler._get_client_ip(request)
            user_agent = request.headers.get("User-Agent", "unknown")
            
            cookie_error_logger.warning(
                f"CSRF protection error - IP: {client_ip}, "
                f"User-Agent: {user_agent}, Error: {str(error)}"
            )
            
            # Determine specific error message
            if "missing" in str(error).lower():
                detail = "CSRF protection token missing - please refresh the page"
                error_type = "csrf_token_missing"
            elif "mismatch" in str(error).lower() or "invalid" in str(error).lower():
                detail = "Invalid CSRF token - please refresh the page and try again"
                error_type = "csrf_token_invalid"
            else:
                detail = "CSRF protection failed - please refresh the page"
                error_type = "csrf_protection_failed"
            
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "detail": detail,
                    "error_type": error_type,
                    "requires_refresh": True
                }
            )
            
        except Exception as cleanup_error:
            cookie_error_logger.error(f"Error during CSRF error handling: {str(cleanup_error)}")
            
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "detail": "CSRF protection failed",
                    "error_type": "csrf_protection_failed",
                    "requires_refresh": True
                }
            )
    
    @staticmethod
    def handle_cookie_security_error(
        error: Exception,
        request: Request
    ) -> JSONResponse:
        """
        Handle cookie security configuration errors.
        
        Args:
            error: The security error that occurred
            request: FastAPI request object
            
        Returns:
            JSON error response
        """
        try:
            # Log the security error
            client_ip = CookieErrorHandler._get_client_ip(request)
            
            cookie_error_logger.error(
                f"Cookie security error - IP: {client_ip}, Error: {str(error)}"
            )
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Security configuration error",
                    "error_type": "security_error",
                    "contact_support": True
                }
            )
            
        except Exception as cleanup_error:
            cookie_error_logger.error(f"Error during security error handling: {str(cleanup_error)}")
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Internal security error",
                    "error_type": "security_error"
                }
            )
    
    @staticmethod
    def handle_token_expired_error(
        request: Request,
        response: Optional[Response] = None,
        user_id: Optional[int] = None
    ) -> JSONResponse:
        """
        Handle expired JWT token errors.
        
        Args:
            request: FastAPI request object
            response: Optional response object for cookie cleanup
            user_id: Optional user ID for logging
            
        Returns:
            JSON error response
        """
        try:
            # Log the token expiry
            client_ip = CookieErrorHandler._get_client_ip(request)
            
            cookie_error_logger.info(
                f"Token expired - User: {user_id}, IP: {client_ip}"
            )
            
            # Create error response
            error_response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Session has expired - please log in again",
                    "error_type": "token_expired",
                    "requires_login": True
                },
                headers={"WWW-Authenticate": "Cookie"}
            )
            
            # Clear expired cookies
            if response:
                clear_auth_cookie(response, user_id)
                clear_csrf_cookie(response)
            else:
                clear_auth_cookie(error_response, user_id)
                clear_csrf_cookie(error_response)
            
            return error_response
            
        except Exception as cleanup_error:
            cookie_error_logger.error(f"Error during token expiry cleanup: {str(cleanup_error)}")
            
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Session expired",
                    "error_type": "token_expired",
                    "requires_login": True
                }
            )
    
    @staticmethod
    def handle_token_revoked_error(
        request: Request,
        response: Optional[Response] = None,
        user_id: Optional[int] = None
    ) -> JSONResponse:
        """
        Handle revoked JWT token errors.
        
        Args:
            request: FastAPI request object
            response: Optional response object for cookie cleanup
            user_id: Optional user ID for logging
            
        Returns:
            JSON error response
        """
        try:
            # Log the token revocation attempt
            client_ip = CookieErrorHandler._get_client_ip(request)
            
            cookie_error_logger.warning(
                f"Revoked token attempted - User: {user_id}, IP: {client_ip}"
            )
            
            # Create error response
            error_response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Session has been revoked - please log in again",
                    "error_type": "token_revoked",
                    "requires_login": True,
                    "security_notice": "Your session was terminated for security reasons"
                },
                headers={"WWW-Authenticate": "Cookie"}
            )
            
            # Clear revoked cookies
            if response:
                clear_auth_cookie(response, user_id)
                clear_csrf_cookie(response)
            else:
                clear_auth_cookie(error_response, user_id)
                clear_csrf_cookie(error_response)
            
            return error_response
            
        except Exception as cleanup_error:
            cookie_error_logger.error(f"Error during token revocation cleanup: {str(cleanup_error)}")
            
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Session revoked",
                    "error_type": "token_revoked",
                    "requires_login": True
                }
            )
    
    @staticmethod
    def create_error_context(
        error: Exception,
        request: Request,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create error context for logging and debugging.
        
        Args:
            error: The error that occurred
            request: FastAPI request object
            user_id: Optional user ID
            
        Returns:
            Dictionary with error context information
        """
        return {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "user_id": user_id,
            "request_method": request.method,
            "request_path": str(request.url.path),
            "client_ip": CookieErrorHandler._get_client_ip(request),
            "user_agent": request.headers.get("User-Agent", "unknown"),
            "timestamp": str(datetime.utcnow())
        }
    
    @staticmethod
    def _get_client_ip(request: Request) -> str:
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


# Global error handler instance
cookie_error_handler = CookieErrorHandler()


# Convenience functions for common error scenarios
def handle_auth_error(
    error: Exception,
    request: Request,
    response: Optional[Response] = None,
    user_id: Optional[int] = None
) -> JSONResponse:
    """Handle authentication error with cleanup."""
    return cookie_error_handler.handle_authentication_error(error, request, response, user_id)


def handle_csrf_error(
    error: Exception,
    request: Request,
    response: Optional[Response] = None
) -> JSONResponse:
    """Handle CSRF error."""
    return cookie_error_handler.handle_csrf_error(error, request, response)


def handle_expired_token(
    request: Request,
    response: Optional[Response] = None,
    user_id: Optional[int] = None
) -> JSONResponse:
    """Handle expired token error."""
    return cookie_error_handler.handle_token_expired_error(request, response, user_id)


def handle_revoked_token(
    request: Request,
    response: Optional[Response] = None,
    user_id: Optional[int] = None
) -> JSONResponse:
    """Handle revoked token error."""
    return cookie_error_handler.handle_token_revoked_error(request, response, user_id)