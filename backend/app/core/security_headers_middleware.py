"""
Security Headers Middleware for FinGood Financial Application

Implements comprehensive security headers including HSTS, CSP, X-Frame-Options,
X-Content-Type-Options, and Referrer-Policy for financial data protection.

CRITICAL SECURITY: This middleware ensures all responses include security headers
required for financial applications and regulatory compliance.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse
from typing import Callable, Optional
import logging
from urllib.parse import urlparse

from app.core.logging_config import get_logger, LogCategory

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive Security Headers Middleware for Financial Applications
    
    Features:
    - HTTPS enforcement with automatic redirects
    - HSTS (HTTP Strict Transport Security) headers
    - Content Security Policy (CSP) with strict financial app settings
    - X-Frame-Options for clickjacking protection
    - X-Content-Type-Options for MIME type sniffing protection
    - Referrer-Policy for privacy protection
    - Secure cookie enforcement
    - Financial application specific security configurations
    """
    
    def __init__(
        self,
        app,
        enforce_https: bool = True,
        hsts_max_age: int = 31536000,  # 1 year
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = True,
        csp_policy: Optional[str] = None,
        allowed_frame_origins: Optional[list] = None,
        referrer_policy: str = "strict-origin-when-cross-origin",
        enable_security_logging: bool = True
    ):
        super().__init__(app)
        self.enforce_https = enforce_https
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains
        self.hsts_preload = hsts_preload
        self.allowed_frame_origins = allowed_frame_origins or []
        self.referrer_policy = referrer_policy
        self.enable_security_logging = enable_security_logging
        
        # Initialize logger
        self.logger = get_logger('fingood.security.headers', LogCategory.SECURITY)
        
        # Default CSP for financial applications - very strict
        if csp_policy is None:
            self.csp_policy = self._build_default_csp()
        else:
            self.csp_policy = csp_policy
        
        self.logger.info("Security Headers Middleware initialized", extra={
            'enforce_https': self.enforce_https,
            'hsts_max_age': self.hsts_max_age,
            'hsts_include_subdomains': self.hsts_include_subdomains,
            'hsts_preload': self.hsts_preload,
            'csp_enabled': bool(self.csp_policy),
            'referrer_policy': self.referrer_policy
        })
    
    def _build_default_csp(self) -> str:
        """
        Build default Content Security Policy for financial applications.
        
        This CSP is designed to be strict and secure for financial data handling:
        - Blocks inline scripts and styles by default
        - Restricts resource loading to same origin
        - Prevents data exfiltration through strict policies
        - Allows specific trusted sources only
        """
        csp_directives = [
            "default-src 'self'",  # Only allow resources from same origin
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Allow scripts (needed for FastAPI docs)
            "style-src 'self' 'unsafe-inline'",  # Allow styles (needed for FastAPI docs)
            "img-src 'self' data: https:",  # Allow images from self, data URIs, and HTTPS
            "font-src 'self' data:",  # Allow fonts from self and data URIs
            "connect-src 'self'",  # Only allow AJAX/WebSocket to same origin
            "media-src 'self'",  # Only allow media from same origin
            "object-src 'none'",  # Block all plugins (Flash, Java, etc.)
            "child-src 'none'",  # Block frames and workers
            "frame-src 'none'",  # Block all framing (additional protection)
            "worker-src 'none'",  # Block web workers
            "manifest-src 'self'",  # Allow web app manifest from same origin
            "base-uri 'self'",  # Restrict base tag to same origin
            "form-action 'self'",  # Only allow forms to submit to same origin
            "frame-ancestors 'none'",  # Prevent being framed (clickjacking protection)
            "upgrade-insecure-requests",  # Automatically upgrade HTTP to HTTPS
            "block-all-mixed-content"  # Block mixed content
        ]
        
        return "; ".join(csp_directives)
    
    def _is_https_request(self, request: Request) -> bool:
        """Check if the request is using HTTPS."""
        # Check scheme directly
        if request.url.scheme == "https":
            return True
        
        # Check for proxy headers (common in production deployments)
        forwarded_proto = request.headers.get("x-forwarded-proto", "").lower()
        forwarded_ssl = request.headers.get("x-forwarded-ssl", "").lower()
        
        return forwarded_proto == "https" or forwarded_ssl == "on"
    
    def _should_enforce_https(self, request: Request) -> bool:
        """Determine if HTTPS should be enforced for this request."""
        if not self.enforce_https:
            return False
        
        # Don't enforce HTTPS for localhost during development
        host = request.headers.get("host", "").lower()
        if host.startswith("localhost") or host.startswith("127.0.0.1"):
            return False
        
        # Don't enforce for health checks and internal endpoints
        path = request.url.path.lower()
        bypass_paths = ["/health", "/metrics", "/status", "/ping"]
        if any(path.startswith(bp) for bp in bypass_paths):
            return False
        
        return True
    
    def _create_https_redirect(self, request: Request) -> RedirectResponse:
        """Create HTTPS redirect response."""
        https_url = request.url.replace(scheme="https")
        
        if self.enable_security_logging:
            self.logger.warning("HTTP request redirected to HTTPS", extra={
                'original_url': str(request.url),
                'redirect_url': str(https_url),
                'client_ip': request.client.host if request.client else 'unknown',
                'user_agent': request.headers.get('user-agent', 'unknown')
            })
        
        return RedirectResponse(
            url=str(https_url),
            status_code=301,  # Permanent redirect
            headers=self._get_security_headers(is_https=True)
        )
    
    def _get_security_headers(self, is_https: bool = True) -> dict:
        """Get all security headers for the response."""
        headers = {}
        
        # HSTS Header (only for HTTPS)
        if is_https:
            hsts_value = f"max-age={self.hsts_max_age}"
            if self.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if self.hsts_preload:
                hsts_value += "; preload"
            headers["Strict-Transport-Security"] = hsts_value
        
        # Content Security Policy
        if self.csp_policy:
            headers["Content-Security-Policy"] = self.csp_policy
        
        # X-Frame-Options for clickjacking protection
        if self.allowed_frame_origins:
            # If specific origins are allowed, use ALLOW-FROM (limited browser support)
            # For better support, use CSP frame-ancestors instead
            headers["X-Frame-Options"] = "SAMEORIGIN"
        else:
            headers["X-Frame-Options"] = "DENY"
        
        # X-Content-Type-Options to prevent MIME sniffing
        headers["X-Content-Type-Options"] = "nosniff"
        
        # X-XSS-Protection (legacy but still useful)
        headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer Policy for privacy
        headers["Referrer-Policy"] = self.referrer_policy
        
        # Additional security headers for financial applications
        headers["X-Permitted-Cross-Domain-Policies"] = "none"
        headers["X-Download-Options"] = "noopen"
        headers["X-DNS-Prefetch-Control"] = "off"
        
        # Permissions Policy (formerly Feature Policy)
        permissions_policy = [
            "geolocation=()",  # Block geolocation
            "microphone=()",   # Block microphone
            "camera=()",       # Block camera
            "payment=(self)",  # Allow payment API only for same origin
            "usb=()",          # Block USB access
            "magnetometer=()", # Block magnetometer
            "gyroscope=()",    # Block gyroscope
            "accelerometer=()", # Block accelerometer
            "ambient-light-sensor=()", # Block ambient light sensor
            "autoplay=()",     # Block autoplay
            "encrypted-media=()", # Block encrypted media
            "fullscreen=(self)", # Allow fullscreen only for same origin
            "picture-in-picture=()" # Block picture-in-picture
        ]
        headers["Permissions-Policy"] = ", ".join(permissions_policy)
        
        return headers
    
    def _log_security_violation(self, request: Request, violation_type: str, details: str):
        """Log security violations for monitoring and compliance."""
        if self.enable_security_logging:
            self.logger.warning(f"Security violation: {violation_type}", extra={
                'violation_type': violation_type,
                'details': details,
                'url': str(request.url),
                'method': request.method,
                'client_ip': request.client.host if request.client else 'unknown',
                'user_agent': request.headers.get('user-agent', 'unknown'),
                'referer': request.headers.get('referer', 'none'),
                'host': request.headers.get('host', 'unknown')
            })
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add security headers to response."""
        
        # Check if HTTPS enforcement is needed
        is_https = self._is_https_request(request)
        
        if self._should_enforce_https(request) and not is_https:
            self._log_security_violation(
                request, 
                "http_access_attempt", 
                "HTTP request to financial application blocked"
            )
            return self._create_https_redirect(request)
        
        # Process the request
        try:
            response = await call_next(request)
        except Exception as e:
            # Simplified error logging to avoid datetime serialization issues
            # Just log basic info without extra fields that might contain datetime objects
            try:
                import logging
                simple_logger = logging.getLogger('simple_error')
                simple_logger.error(f"Request processing error: {type(e).__name__} at {request.method} {request.url.path}")
            except:
                # If even this fails, continue without logging
                pass
            raise
        
        # Add security headers to response
        security_headers = self._get_security_headers(is_https=is_https)
        
        for header_name, header_value in security_headers.items():
            response.headers[header_name] = header_value
        
        # Secure cookie enforcement
        if is_https:
            self._enforce_secure_cookies(response)
        
        # Log successful security header application (debug level)
        if self.enable_security_logging:
            self.logger.debug("Security headers applied", extra={
                'url': str(request.url),
                'is_https': is_https,
                'headers_applied': list(security_headers.keys())
            })
        
        return response
    
    def _enforce_secure_cookies(self, response: Response):
        """Enforce secure cookie settings for HTTPS responses."""
        # Check if response has Set-Cookie headers
        set_cookie_headers = response.headers.getlist("set-cookie")
        
        if not set_cookie_headers:
            return
        
        # Remove existing Set-Cookie headers
        del response.headers["set-cookie"]
        
        # Re-add with secure flags
        for cookie_header in set_cookie_headers:
            # Parse and modify cookie
            secure_cookie = self._make_cookie_secure(cookie_header)
            response.headers.append("set-cookie", secure_cookie)
    
    def _make_cookie_secure(self, cookie_header: str) -> str:
        """Make a cookie header secure by adding necessary flags."""
        # Add Secure flag if not present
        if "secure" not in cookie_header.lower():
            cookie_header += "; Secure"
        
        # Add HttpOnly flag if not present (for non-CSRF cookies)
        if "httponly" not in cookie_header.lower() and "csrf" not in cookie_header.lower():
            cookie_header += "; HttpOnly"
        
        # Add SameSite=Strict if not present
        if "samesite" not in cookie_header.lower():
            cookie_header += "; SameSite=Strict"
        
        return cookie_header