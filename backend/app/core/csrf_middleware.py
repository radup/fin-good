"""
CSRF protection middleware for FinGood financial application.
Automatically validates CSRF tokens for state-changing HTTP methods.
"""

import logging
from typing import Callable, List, Set

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.csrf import csrf_protection, CSRFTokenMissingError, CSRFTokenInvalidError
from app.core.cookie_auth import extract_token_from_request
from app.core.security import jwt_manager

# Configure CSRF middleware logging
csrf_middleware_logger = logging.getLogger("fingood.csrf_middleware")


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection middleware that validates tokens for state-changing operations.
    Implements automatic CSRF protection for financial application security.
    """
    
    def __init__(
        self, 
        app, 
        exempt_paths: List[str] = None,
        require_csrf_methods: Set[str] = None
    ):
        """
        Initialize CSRF protection middleware.
        
        Args:
            app: FastAPI application instance
            exempt_paths: List of paths to exempt from CSRF protection
            require_csrf_methods: HTTP methods that require CSRF protection
        """
        super().__init__(app)
        
        # Default exempt paths (authentication endpoints)
        self.exempt_paths = exempt_paths or [
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh-csrf",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/"
        ]
        
        # HTTP methods that require CSRF protection
        self.require_csrf_methods = require_csrf_methods or {
            "POST", "PUT", "PATCH", "DELETE"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and validate CSRF token if required.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or endpoint handler
            
        Returns:
            HTTP response
        """
        try:
            # Check if CSRF protection is required for this request
            if self._should_validate_csrf(request):
                await self._validate_csrf_token(request)
            
            # Process the request
            response = await call_next(request)
            return response
            
        except HTTPException:
            # Re-raise HTTP exceptions (like CSRF failures)
            raise
        except Exception as e:
            csrf_middleware_logger.error(f"CSRF middleware error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="CSRF protection error"
            )
    
    def _should_validate_csrf(self, request: Request) -> bool:
        """
        Determine if CSRF validation is required for this request.
        
        Args:
            request: HTTP request to evaluate
            
        Returns:
            True if CSRF validation is required
        """
        # Skip if method doesn't require CSRF protection
        if request.method not in self.require_csrf_methods:
            return False
        
        # Skip if path is exempt
        if any(request.url.path.startswith(exempt_path) for exempt_path in self.exempt_paths):
            return False
        
        # Skip if user is not authenticated (no auth cookie)
        auth_token = extract_token_from_request(request)
        if not auth_token:
            return False
        
        csrf_middleware_logger.debug(
            f"CSRF validation required for {request.method} {request.url.path}"
        )
        return True
    
    async def _validate_csrf_token(self, request: Request) -> None:
        """
        Validate CSRF token for the request.
        
        Args:
            request: HTTP request to validate
            
        Raises:
            HTTPException: If CSRF validation fails
        """
        try:
            # For CSRF validation, we use a simplified approach
            # that doesn't require user ID binding to avoid database calls in middleware
            
            # Extract CSRF tokens from request
            cookie_token, header_token = csrf_protection.extract_csrf_tokens(request)
            
            # Check if tokens are present
            if not cookie_token:
                raise CSRFTokenMissingError("CSRF cookie token missing")
            
            if not header_token:
                raise CSRFTokenMissingError("CSRF header token missing")
            
            # Validate cookie token (basic validation without user binding)
            csrf_protection.validate_csrf_token(cookie_token)
            
            # Verify tokens match (double-submit pattern)
            import hmac
            if not hmac.compare_digest(cookie_token, header_token):
                csrf_middleware_logger.warning(
                    f"CSRF token mismatch - Method: {request.method}, "
                    f"Path: {request.url.path}"
                )
                raise CSRFTokenInvalidError("CSRF tokens do not match")
            
            csrf_middleware_logger.info(
                f"CSRF validation passed - Method: {request.method}, "
                f"Path: {request.url.path}"
            )
            
        except CSRFTokenMissingError as e:
            csrf_middleware_logger.warning(
                f"CSRF token missing - Method: {request.method}, "
                f"Path: {request.url.path}, Error: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token required for this operation"
            )
        
        except CSRFTokenInvalidError as e:
            csrf_middleware_logger.warning(
                f"CSRF token invalid - Method: {request.method}, "
                f"Path: {request.url.path}, Error: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid CSRF token - please refresh the page and try again"
            )
        
        except Exception as e:
            csrf_middleware_logger.error(
                f"CSRF validation error - Method: {request.method}, "
                f"Path: {request.url.path}, Error: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF validation failed"
            )
    
# Removed _extract_user_id_from_request method as CSRF validation
# now uses a simplified approach without user ID binding


def create_csrf_middleware(
    exempt_paths: List[str] = None,
    require_csrf_methods: Set[str] = None
) -> type:
    """
    Factory function to create CSRF middleware with custom configuration.
    
    Args:
        exempt_paths: Additional paths to exempt from CSRF protection
        require_csrf_methods: HTTP methods requiring CSRF protection
        
    Returns:
        Configured CSRF middleware class
    """
    class ConfiguredCSRFMiddleware(CSRFProtectionMiddleware):
        def __init__(self, app):
            super().__init__(app, exempt_paths, require_csrf_methods)
    
    return ConfiguredCSRFMiddleware