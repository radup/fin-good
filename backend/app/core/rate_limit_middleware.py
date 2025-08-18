"""
Rate limiting middleware for FastAPI.
Provides comprehensive protection against abuse, brute force attacks, and DDoS.
"""

import time
from typing import Callable, Dict, Optional, Set, Tuple
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
from datetime import datetime, timedelta
import ipaddress
import re

from app.core.rate_limiter import (
    RateLimiter, 
    RateLimitType, 
    RateLimitTier, 
    get_rate_limiter
)
from app.core.rate_limit_monitoring import record_rate_limit_metric
from app.core.error_monitoring import security_logger
from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware that protects all API endpoints.
    Implements multiple layers of protection:
    - General API rate limiting
    - Endpoint-specific limits
    - User-tier based limits
    - Brute force protection
    - DDoS protection
    """
    
    def __init__(self, app, enable_rate_limiting: bool = True):
        super().__init__(app)
        self.enable_rate_limiting = enable_rate_limiting
        self.rate_limiter: Optional[RateLimiter] = None
        
        # Endpoint patterns and their rate limit types
        self.endpoint_patterns = {
            r"/api/v1/auth/.*": RateLimitType.AUTH,
            r"/api/v1/upload/.*": RateLimitType.UPLOAD,
            r"/api/v1/analytics/.*": RateLimitType.ANALYTICS,
            r"/api/v1/monitoring/.*": RateLimitType.ADMIN,
            r"/health": None,  # No rate limiting for health checks
            r"/docs": None,    # No rate limiting for documentation
            r"/redoc": None    # No rate limiting for documentation
        }
        
        # Sensitive endpoints that require stricter protection
        self.sensitive_endpoints = {
            r"/api/v1/auth/login",
            r"/api/v1/auth/register", 
            r"/api/v1/auth/reset-password",
            r"/api/v1/auth/change-password"
        }
        
        # Trusted IP ranges (internal networks, CDNs, etc.)
        self.trusted_ips = self._parse_trusted_ips()
        
        # DDoS detection thresholds
        self.ddos_thresholds = {
            "requests_per_second": 50,
            "concurrent_connections": 100,
            "suspicious_patterns": 5
        }
    
    def _parse_trusted_ips(self) -> Set[ipaddress.IPv4Network]:
        """Parse trusted IP ranges from configuration."""
        trusted_ranges = [
            "127.0.0.0/8",    # Localhost
            "10.0.0.0/8",     # Private network
            "172.16.0.0/12",  # Private network
            "192.168.0.0/16", # Private network
        ]
        
        # Add any additional trusted IPs from settings
        if hasattr(settings, 'TRUSTED_IP_RANGES'):
            trusted_ranges.extend(settings.TRUSTED_IP_RANGES)
        
        return {ipaddress.IPv4Network(ip_range) for ip_range in trusted_ranges}
    
    def _is_trusted_ip(self, ip_address: str) -> bool:
        """Check if IP address is in trusted range."""
        try:
            ip = ipaddress.IPv4Address(ip_address)
            return any(ip in network for network in self.trusted_ips)
        except (ipaddress.AddressValueError, ValueError):
            return False
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address with proxy support."""
        # Check for forwarded headers (common with load balancers/proxies)
        forwarded_ips = request.headers.get("X-Forwarded-For")
        if forwarded_ips:
            # Take the first IP (original client)
            client_ip = forwarded_ips.split(",")[0].strip()
        else:
            # Check other common headers
            client_ip = (
                request.headers.get("X-Real-IP") or
                request.headers.get("X-Client-IP") or
                request.client.host if request.client else "unknown"
            )
        
        return client_ip
    
    def _get_user_identifier(self, request: Request) -> Tuple[str, RateLimitTier]:
        """
        Get user identifier and tier for rate limiting.
        Returns IP-based identifier if user not authenticated.
        """
        # Try to get user from JWT token or session
        user_id = getattr(request.state, 'user_id', None)
        user_tier = getattr(request.state, 'user_tier', RateLimitTier.FREE)
        
        if user_id:
            return f"user:{user_id}", user_tier
        else:
            # Use IP-based identifier for unauthenticated requests
            client_ip = self._get_client_ip(request)
            return f"ip:{client_ip}", RateLimitTier.FREE
    
    def _determine_rate_limit_type(self, path: str) -> Optional[RateLimitType]:
        """Determine the rate limit type based on endpoint path."""
        for pattern, limit_type in self.endpoint_patterns.items():
            if re.match(pattern, path):
                return limit_type
        
        # Default to general rate limiting for API endpoints
        if path.startswith("/api/"):
            return RateLimitType.GENERAL
        
        return None
    
    def _is_sensitive_endpoint(self, path: str) -> bool:
        """Check if endpoint requires extra security protection."""
        return any(re.match(pattern, path) for pattern in self.sensitive_endpoints)
    
    async def _check_ddos_protection(
        self, 
        request: Request, 
        client_ip: str
    ) -> Optional[JSONResponse]:
        """Check for DDoS patterns and suspicious activity."""
        if not self.rate_limiter:
            return None
        
        # Skip DDoS checks for trusted IPs
        if self._is_trusted_ip(client_ip):
            return None
        
        try:
            # Check IP-based DDoS limits
            ddos_result = await self.rate_limiter.check_rate_limit(
                f"ddos:{client_ip}",
                RateLimitType.DDOS,
                RateLimitTier.FREE
            )
            
            if not ddos_result.allowed:
                # Log DDoS attempt
                security_logger.critical(
                    "DDoS protection triggered",
                    extra={
                        "client_ip": client_ip,
                        "path": request.url.path,
                        "user_agent": request.headers.get("User-Agent"),
                        "current_usage": ddos_result.current_usage,
                        "limit": ddos_result.limit,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                # Create security block for severe DDoS attempts
                if ddos_result.current_usage > ddos_result.limit * 2:
                    await self.rate_limiter.create_security_block(
                        f"ip:{client_ip}",
                        RateLimitType.DDOS,
                        240,  # 4 hour block
                        "Severe DDoS attempt detected"
                    )
                
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Too many requests",
                        "message": "DDoS protection activated",
                        "retry_after": ddos_result.retry_after,
                        "type": "ddos_protection"
                    },
                    headers={
                        "Retry-After": str(ddos_result.retry_after or 60),
                        "X-RateLimit-Limit": str(ddos_result.limit),
                        "X-RateLimit-Remaining": str(ddos_result.remaining),
                        "X-RateLimit-Reset": str(int(ddos_result.reset_time.timestamp()))
                    }
                )
        
        except Exception as e:
            logger.error(f"Error in DDoS protection check: {e}")
        
        return None
    
    async def _check_brute_force_protection(
        self,
        request: Request,
        identifier: str,
        user_tier: RateLimitTier
    ) -> Optional[JSONResponse]:
        """Check for brute force attacks on sensitive endpoints."""
        if not self.rate_limiter or not self._is_sensitive_endpoint(request.url.path):
            return None
        
        try:
            # Check brute force limits
            bf_result = await self.rate_limiter.check_rate_limit(
                f"bf:{identifier}",
                RateLimitType.BRUTE_FORCE,
                user_tier
            )
            
            if not bf_result.allowed:
                # Log brute force attempt
                security_logger.warning(
                    "Brute force protection triggered",
                    extra={
                        "identifier": identifier,
                        "path": request.url.path,
                        "client_ip": self._get_client_ip(request),
                        "user_agent": request.headers.get("User-Agent"),
                        "current_usage": bf_result.current_usage,
                        "limit": bf_result.limit,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Too many authentication attempts",
                        "message": "Account temporarily locked for security",
                        "retry_after": bf_result.retry_after,
                        "type": "brute_force_protection"
                    },
                    headers={
                        "Retry-After": str(bf_result.retry_after or 900),  # 15 minutes default
                        "X-RateLimit-Limit": str(bf_result.limit),
                        "X-RateLimit-Remaining": str(bf_result.remaining),
                        "X-RateLimit-Reset": str(int(bf_result.reset_time.timestamp()))
                    }
                )
        
        except Exception as e:
            logger.error(f"Error in brute force protection check: {e}")
        
        return None
    
    async def _check_endpoint_rate_limit(
        self,
        request: Request,
        identifier: str,
        user_tier: RateLimitTier,
        limit_type: RateLimitType
    ) -> Optional[JSONResponse]:
        """Check endpoint-specific rate limits."""
        if not self.rate_limiter:
            return None
        
        try:
            result = await self.rate_limiter.check_rate_limit(
                identifier,
                limit_type,
                user_tier
            )
            
            if not result.allowed:
                # Log rate limit violation
                security_logger.info(
                    "Rate limit exceeded",
                    extra={
                        "identifier": identifier,
                        "limit_type": limit_type.value,
                        "user_tier": user_tier.value,
                        "path": request.url.path,
                        "current_usage": result.current_usage,
                        "limit": result.limit,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests for {limit_type.value} endpoints",
                        "retry_after": result.retry_after,
                        "type": "rate_limit"
                    },
                    headers={
                        "Retry-After": str(result.retry_after or 60),
                        "X-RateLimit-Limit": str(result.limit),
                        "X-RateLimit-Remaining": str(result.remaining),
                        "X-RateLimit-Reset": str(int(result.reset_time.timestamp())),
                        "X-RateLimit-Type": limit_type.value
                    }
                )
            
            # Add rate limit headers to successful responses and store metrics
            request.state.rate_limit_headers = {
                "X-RateLimit-Limit": str(result.limit),
                "X-RateLimit-Remaining": str(result.remaining),
                "X-RateLimit-Reset": str(int(result.reset_time.timestamp())),
                "X-RateLimit-Type": limit_type.value
            }
            
            # Store metrics for later recording
            request.state.current_usage = result.current_usage
            request.state.limit = result.limit
            request.state.remaining = result.remaining
        
        except Exception as e:
            logger.error(f"Error in rate limit check: {e}")
        
        return None
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Main middleware dispatch method."""
        # Skip rate limiting if disabled
        if not self.enable_rate_limiting:
            return await call_next(request)
        
        # Initialize rate limiter if needed
        if not self.rate_limiter:
            try:
                self.rate_limiter = await get_rate_limiter()
            except Exception as e:
                logger.error(f"Failed to initialize rate limiter: {e}")
                # Continue without rate limiting if Redis is unavailable
                return await call_next(request)
        
        start_time = time.time()
        path = request.url.path
        
        # Skip rate limiting for certain paths
        limit_type = self._determine_rate_limit_type(path)
        if limit_type is None:
            return await call_next(request)
        
        # Get client information
        client_ip = self._get_client_ip(request)
        identifier, user_tier = self._get_user_identifier(request)
        
        try:
            # 1. DDoS Protection (IP-based)
            ddos_response = await self._check_ddos_protection(request, client_ip)
            if ddos_response:
                return ddos_response
            
            # 2. Brute Force Protection (for sensitive endpoints)
            bf_response = await self._check_brute_force_protection(
                request, identifier, user_tier
            )
            if bf_response:
                return bf_response
            
            # 3. Endpoint-specific Rate Limiting
            rate_limit_response = await self._check_endpoint_rate_limit(
                request, identifier, user_tier, limit_type
            )
            if rate_limit_response:
                return rate_limit_response
            
            # Process the request
            response = await call_next(request)
            
            # Add rate limit headers to response
            if hasattr(request.state, 'rate_limit_headers'):
                for header, value in request.state.rate_limit_headers.items():
                    response.headers[header] = value
            
            # Record successful request metrics for monitoring
            try:
                await record_rate_limit_metric(
                    identifier=identifier,
                    limit_type=limit_type,
                    current_usage=getattr(request.state, 'current_usage', 0),
                    limit=getattr(request.state, 'limit', 0),
                    remaining=getattr(request.state, 'remaining', 0),
                    client_ip=client_ip,
                    user_agent=request.headers.get("User-Agent"),
                    endpoint=path,
                    user_tier=user_tier.value
                )
            except Exception as metric_error:
                logger.error(f"Error recording rate limit metric: {metric_error}")
            
            # Log successful request processing time
            processing_time = time.time() - start_time
            if processing_time > 5.0:  # Log slow requests
                logger.warning(
                    f"Slow request detected: {path} took {processing_time:.2f}s",
                    extra={
                        "path": path,
                        "processing_time": processing_time,
                        "client_ip": client_ip,
                        "identifier": identifier
                    }
                )
            
            return response
        
        except Exception as e:
            logger.error(
                f"Error in rate limiting middleware: {e}",
                extra={
                    "path": path,
                    "client_ip": client_ip,
                    "identifier": identifier,
                    "error": str(e)
                }
            )
            
            # Continue without rate limiting if there's an error
            return await call_next(request)


def create_rate_limit_middleware(enable_rate_limiting: bool = True):
    """Factory function to create rate limiting middleware."""
    def middleware_factory(app):
        return RateLimitMiddleware(app, enable_rate_limiting)
    return middleware_factory