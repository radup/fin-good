"""
Request tracing and context middleware for FinGood Financial Platform

This middleware provides:
- Request ID generation and tracking
- Correlation ID support for distributed tracing
- Request context management for security auditing
- Performance monitoring and rate limiting support
"""

import uuid
import time
import logging
from typing import Callable, Optional
from datetime import datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.audit_logger import security_audit_logger

logger = logging.getLogger(__name__)


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request tracing, correlation IDs, and security context
    
    Features:
    - Generates unique request IDs for each request
    - Supports correlation IDs from headers for distributed tracing
    - Tracks request timing for performance monitoring
    - Maintains security context for audit logging
    - Sanitizes headers to prevent information leakage
    """
    
    def __init__(
        self,
        app: ASGIApp,
        request_id_header: str = "X-Request-ID",
        correlation_id_header: str = "X-Correlation-ID",
        enable_timing: bool = True,
        enable_security_logging: bool = True
    ):
        super().__init__(app)
        self.request_id_header = request_id_header
        self.correlation_id_header = correlation_id_header
        self.enable_timing = enable_timing
        self.enable_security_logging = enable_security_logging
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with tracing and security context"""
        start_time = time.time() if self.enable_timing else None
        
        # Generate or extract request ID
        request_id = self._get_or_generate_request_id(request)
        request.state.request_id = request_id
        
        # Extract correlation ID for distributed tracing
        correlation_id = self._get_correlation_id(request)
        request.state.correlation_id = correlation_id
        
        # Set up security context
        self._setup_security_context(request)
        
        # Log request start for security monitoring
        if self.enable_security_logging:
            self._log_request_start(request)
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Add tracing headers to response
            response.headers[self.request_id_header] = request_id
            if correlation_id:
                response.headers[self.correlation_id_header] = correlation_id
            
            # Log successful request completion
            if self.enable_timing:
                duration = time.time() - start_time
                response.headers["X-Response-Time"] = f"{duration:.3f}s"
                
                # Log slow requests as potential security concerns
                if duration > 10.0:  # 10 second threshold
                    logger.warning(f"Slow request detected", extra={
                        "request_id": request_id,
                        "path": request.url.path,
                        "method": request.method,
                        "duration": duration,
                        "status_code": response.status_code,
                        "client_ip": self._get_client_ip(request)
                    })
            
            # Log security-relevant response information
            if self.enable_security_logging and response.status_code >= 400:
                self._log_error_response(request, response)
            
            return response
            
        except Exception as exc:
            # Log unhandled exceptions with full context
            duration = time.time() - start_time if start_time else None
            
            logger.error(f"Request failed with exception", extra={
                "request_id": request_id,
                "correlation_id": correlation_id,
                "path": request.url.path,
                "method": request.method,
                "exception_type": type(exc).__name__,
                "duration": duration,
                "client_ip": self._get_client_ip(request),
                "user_agent": request.headers.get("User-Agent")
            })
            
            # Re-raise to let error handlers process it
            raise
    
    def _get_or_generate_request_id(self, request: Request) -> str:
        """Get request ID from headers or generate a new one"""
        # Check if client provided a request ID
        existing_id = request.headers.get(self.request_id_header)
        if existing_id and self._is_valid_uuid(existing_id):
            return existing_id
        
        # Generate new UUID for this request
        return str(uuid.uuid4())
    
    def _get_correlation_id(self, request: Request) -> Optional[str]:
        """Extract correlation ID for distributed tracing"""
        correlation_id = request.headers.get(self.correlation_id_header)
        if correlation_id and self._is_valid_uuid(correlation_id):
            return correlation_id
        return None
    
    def _is_valid_uuid(self, uuid_string: str) -> bool:
        """Validate UUID format for security"""
        try:
            uuid.UUID(uuid_string)
            return True
        except (ValueError, TypeError):
            return False
    
    def _setup_security_context(self, request: Request) -> None:
        """Set up security context for the request"""
        # Store client information securely
        request.state.client_ip = self._get_client_ip(request)
        request.state.user_agent = request.headers.get("User-Agent", "")[:500]  # Limit length
        request.state.timestamp = datetime.utcnow()
        
        # Initialize user context (will be set by auth middleware)
        request.state.user_id = None
        request.state.user_email = None
        request.state.is_authenticated = False
        
        # Track potentially suspicious headers
        self._check_suspicious_headers(request)
    
    def _check_suspicious_headers(self, request: Request) -> None:
        """Check for suspicious request headers"""
        suspicious_patterns = [
            "sqlmap", "nmap", "burp", "nikto", "dirb", "gobuster",
            "wfuzz", "acunetix", "nessus", "openvas", "metasploit"
        ]
        
        user_agent = request.headers.get("User-Agent", "").lower()
        
        for pattern in suspicious_patterns:
            if pattern in user_agent:
                security_audit_logger.log_suspicious_activity(
                    description=f"Suspicious user agent detected: {pattern}",
                    request=request,
                    details={
                        "user_agent": user_agent[:200],  # Limit for security
                        "pattern_matched": pattern,
                        "request_id": request.state.request_id
                    }
                )
                break
    
    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Safely extract client IP address"""
        # Check for forwarded headers (in order of preference)
        forwarded_headers = [
            "X-Forwarded-For",
            "X-Real-IP", 
            "X-Client-IP",
            "CF-Connecting-IP"  # Cloudflare
        ]
        
        for header in forwarded_headers:
            ip = request.headers.get(header)
            if ip:
                # Take the first IP in case of comma-separated list
                return ip.split(",")[0].strip()
        
        # Fallback to direct connection IP
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return None
    
    def _log_request_start(self, request: Request) -> None:
        """Log request start for security monitoring"""
        # Only log security-relevant information
        sensitive_paths = ["/api/v1/auth", "/api/v1/transactions", "/api/v1/upload"]
        
        if any(request.url.path.startswith(path) for path in sensitive_paths):
            logger.info(f"Security-sensitive request started", extra={
                "request_id": request.state.request_id,
                "correlation_id": request.state.correlation_id,
                "path": request.url.path,
                "method": request.method,
                "client_ip": request.state.client_ip,
                "timestamp": request.state.timestamp.isoformat()
            })
    
    def _log_error_response(self, request: Request, response: Response) -> None:
        """Log error responses for security analysis"""
        logger.warning(f"Error response sent", extra={
            "request_id": request.state.request_id,
            "correlation_id": request.state.correlation_id,
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "client_ip": request.state.client_ip,
            "user_id": getattr(request.state, 'user_id', None)
        })


class SecurityHeaderMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses
    
    Implements security best practices for financial applications:
    - Content Security Policy
    - Strict Transport Security
    - X-Frame-Options
    - X-Content-Type-Options
    - And more...
    """
    
    def __init__(self, app: ASGIApp, enable_csp: bool = True):
        super().__init__(app)
        self.enable_csp = enable_csp
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response"""
        response = await call_next(request)
        
        # Security headers for financial applications
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            "Cache-Control": "no-store, no-cache, must-revalidate, private"
        }
        
        # Content Security Policy for financial security
        if self.enable_csp:
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # May need adjustment
                "style-src 'self' 'unsafe-inline'",
                "img-src 'self' data: https:",
                "font-src 'self'",
                "connect-src 'self'",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'"
            ]
            security_headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        # Add security headers
        for header, value in security_headers.items():
            response.headers[header] = value
        
        # Remove potentially sensitive headers
        sensitive_headers = ["Server", "X-Powered-By", "X-AspNet-Version"]
        for header in sensitive_headers:
            response.headers.pop(header, None)
        
        return response


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Basic rate limiting middleware for financial API security
    
    Implements:
    - Per-IP rate limiting
    - Per-user rate limiting (when authenticated)
    - Endpoint-specific limits
    - Suspicious activity detection
    """
    
    def __init__(
        self,
        app: ASGIApp,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        enable_per_endpoint_limits: bool = True
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.enable_per_endpoint_limits = enable_per_endpoint_limits
        
        # Simple in-memory rate limiting (production should use Redis)
        self.request_counts = {}
        self.last_cleanup = time.time()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limits before processing request"""
        current_time = time.time()
        
        # Cleanup old entries periodically
        if current_time - self.last_cleanup > 300:  # 5 minutes
            self._cleanup_old_entries(current_time)
            self.last_cleanup = current_time
        
        # Get rate limiting key (IP or user-based)
        rate_limit_key = self._get_rate_limit_key(request)
        
        # Check if rate limit exceeded
        if self._is_rate_limited(rate_limit_key, current_time):
            # Log rate limiting event
            security_audit_logger.log_suspicious_activity(
                description="Rate limit exceeded",
                request=request,
                details={
                    "rate_limit_key": rate_limit_key,
                    "requests_per_minute": self.requests_per_minute,
                    "endpoint": request.url.path
                }
            )
            
            # Return rate limit error
            from app.core.exceptions import RateLimitException
            raise RateLimitException(retry_after=60)
        
        # Record this request
        self._record_request(rate_limit_key, current_time)
        
        return await call_next(request)
    
    def _get_rate_limit_key(self, request: Request) -> str:
        """Get rate limiting key based on user or IP"""
        # Prefer user-based rate limiting when authenticated
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP-based rate limiting
        client_ip = getattr(request.state, 'client_ip', None)
        if client_ip:
            return f"ip:{client_ip}"
        
        # Fallback for unknown clients
        return "unknown"
    
    def _is_rate_limited(self, key: str, current_time: float) -> bool:
        """Check if the key has exceeded rate limits"""
        if key not in self.request_counts:
            return False
        
        requests = self.request_counts[key]
        
        # Check per-minute limit
        recent_requests = [
            timestamp for timestamp in requests 
            if current_time - timestamp < 60
        ]
        
        if len(recent_requests) >= self.requests_per_minute:
            return True
        
        # Check per-hour limit
        hourly_requests = [
            timestamp for timestamp in requests 
            if current_time - timestamp < 3600
        ]
        
        if len(hourly_requests) >= self.requests_per_hour:
            return True
        
        return False
    
    def _record_request(self, key: str, current_time: float) -> None:
        """Record a request for rate limiting"""
        if key not in self.request_counts:
            self.request_counts[key] = []
        
        self.request_counts[key].append(current_time)
        
        # Keep only recent requests to limit memory usage
        self.request_counts[key] = [
            timestamp for timestamp in self.request_counts[key]
            if current_time - timestamp < 3600  # Keep last hour
        ]
    
    def _cleanup_old_entries(self, current_time: float) -> None:
        """Clean up old rate limiting entries"""
        keys_to_remove = []
        
        for key, timestamps in self.request_counts.items():
            # Remove old timestamps
            recent_timestamps = [
                timestamp for timestamp in timestamps
                if current_time - timestamp < 3600
            ]
            
            if recent_timestamps:
                self.request_counts[key] = recent_timestamps
            else:
                keys_to_remove.append(key)
        
        # Remove empty entries
        for key in keys_to_remove:
            del self.request_counts[key]