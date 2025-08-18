"""
Request/Response Logging Middleware for FinGood Financial Application

This middleware provides comprehensive request and response logging with
request ID tracking, correlation IDs, performance metrics, and security
event logging. Designed for financial application compliance and monitoring.
"""

import json
import time
import uuid
import asyncio
from typing import Callable, Dict, Any, Optional, Set, List
from datetime import datetime, timezone
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.types import ASGIApp
import logging

from app.core.logging_config import (
    get_logger, 
    LogCategory, 
    set_request_context, 
    clear_request_context,
    SensitiveDataFilter
)
from app.core.performance_monitor import measure_api_request, MetricType
from app.core.transaction_audit import TransactionType, TransactionOutcome


class RequestResponseLoggingMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive request/response logging middleware for financial applications.
    Provides audit trails, performance monitoring, and security event logging.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        log_requests: bool = True,
        log_responses: bool = True,
        log_request_body: bool = False,
        log_response_body: bool = False,
        mask_sensitive_data: bool = True,
        max_body_size: int = 1024 * 1024,  # 1MB
        excluded_paths: Optional[Set[str]] = None,
        excluded_user_agents: Optional[Set[str]] = None,
        log_level: str = "INFO"
    ):
        """
        Initialize request/response logging middleware
        
        Args:
            app: ASGI application
            log_requests: Whether to log requests
            log_responses: Whether to log responses
            log_request_body: Whether to log request body (security risk)
            log_response_body: Whether to log response body (security risk)
            mask_sensitive_data: Whether to mask sensitive data
            max_body_size: Maximum body size to log
            excluded_paths: Paths to exclude from logging
            excluded_user_agents: User agents to exclude from logging
            log_level: Logging level
        """
        super().__init__(app)
        self.log_requests = log_requests
        self.log_responses = log_responses
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.mask_sensitive_data = mask_sensitive_data
        self.max_body_size = max_body_size
        self.excluded_paths = excluded_paths or {
            "/health", "/metrics", "/favicon.ico", "/robots.txt"
        }
        self.excluded_user_agents = excluded_user_agents or {
            "HealthCheck", "Monitoring", "Pingdom", "StatusCake"
        }
        
        # Initialize loggers
        self.api_logger = get_logger('fingood.api', LogCategory.API)
        self.security_logger = get_logger('fingood.security', LogCategory.SECURITY)
        self.performance_logger = get_logger('fingood.performance', LogCategory.PERFORMANCE)
        
        # Request tracking
        self.active_requests: Dict[str, Dict[str, Any]] = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and response with comprehensive logging
        """
        # Generate request ID and set context
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Check if request should be logged
        if self._should_exclude_request(request):
            return await call_next(request)
        
        # Extract request information
        start_time = time.time()
        request_info = await self._extract_request_info(request)
        
        # Set request context for logging correlation
        set_request_context(
            request_id=request_id,
            user_id=getattr(request.state, 'user_id', None),
            session_id=getattr(request.state, 'session_id', None)
        )
        
        # Track active request
        self.active_requests[request_id] = {
            'start_time': start_time,
            'request_info': request_info,
            'path': request.url.path,
            'method': request.method
        }
        
        try:
            # Log incoming request
            if self.log_requests:
                await self._log_request(request_info)
            
            # Process the request
            response = await call_next(request)
            
            # Calculate processing time
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            # Extract response information
            response_info = await self._extract_response_info(response, duration_ms)
            
            # Log outgoing response
            if self.log_responses:
                await self._log_response(request_info, response_info)
            
            # Log performance metrics
            await self._log_performance(request_info, response_info)
            
            # Log security events if needed
            await self._log_security_events(request_info, response_info)
            
            return response
            
        except Exception as e:
            # Log error
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            await self._log_error(request_info, str(e), duration_ms)
            raise
            
        finally:
            # Clean up
            self.active_requests.pop(request_id, None)
            clear_request_context()
    
    def _should_exclude_request(self, request: Request) -> bool:
        """Check if request should be excluded from logging"""
        
        # Check excluded paths
        if request.url.path in self.excluded_paths:
            return True
        
        # Check excluded user agents
        user_agent = request.headers.get("user-agent", "")
        if any(excluded in user_agent for excluded in self.excluded_user_agents):
            return True
        
        # Check for health check patterns
        if any(health_path in request.url.path.lower() 
               for health_path in ["/health", "/ping", "/status"]):
            return True
        
        return False
    
    async def _extract_request_info(self, request: Request) -> Dict[str, Any]:
        """Extract comprehensive request information"""
        
        # Basic request info
        request_info = {
            'request_id': request.state.request_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'method': request.method,
            'url': str(request.url),
            'path': request.url.path,
            'query_params': dict(request.query_params),
            'headers': dict(request.headers),
            'client_ip': self._get_client_ip(request),
            'user_agent': request.headers.get('user-agent'),
            'content_type': request.headers.get('content-type'),
            'content_length': request.headers.get('content-length'),
            'host': request.headers.get('host'),
            'scheme': request.url.scheme,
            'referer': request.headers.get('referer'),
        }
        
        # Add user context if available
        if hasattr(request.state, 'user_id'):
            request_info['user_id'] = request.state.user_id
        if hasattr(request.state, 'session_id'):
            request_info['session_id'] = request.state.session_id
        
        # Add request body if enabled and appropriate
        if (self.log_request_body and 
            request.method in ['POST', 'PUT', 'PATCH'] and
            self._is_safe_to_log_body(request)):
            
            try:
                body = await self._read_request_body(request)
                if body and len(body) <= self.max_body_size:
                    request_info['body'] = body[:self.max_body_size]
            except Exception as e:
                request_info['body_error'] = str(e)
        
        # Mask sensitive data if enabled
        if self.mask_sensitive_data:
            request_info = SensitiveDataFilter.filter_sensitive_data(request_info)
        
        return request_info
    
    async def _extract_response_info(self, response: Response, duration_ms: float) -> Dict[str, Any]:
        """Extract response information"""
        
        response_info = {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'duration_ms': duration_ms,
            'content_type': response.headers.get('content-type'),
            'content_length': response.headers.get('content-length'),
        }
        
        # Add response body if enabled and appropriate
        if (self.log_response_body and 
            self._is_safe_to_log_response_body(response)):
            
            try:
                # For streaming responses, we can't easily capture the body
                if not isinstance(response, StreamingResponse):
                    # This is complex and potentially memory-intensive
                    # In production, consider logging only specific responses
                    pass
            except Exception as e:
                response_info['body_error'] = str(e)
        
        return response_info
    
    async def _log_request(self, request_info: Dict[str, Any]):
        """Log incoming request"""
        
        log_data = {
            'event_type': 'api_request_received',
            'request_id': request_info['request_id'],
            'method': request_info['method'],
            'path': request_info['path'],
            'client_ip': request_info['client_ip'],
            'user_agent': request_info.get('user_agent'),
            'user_id': request_info.get('user_id'),
            'session_id': request_info.get('session_id'),
            'content_type': request_info.get('content_type'),
            'query_params_count': len(request_info.get('query_params', {})),
            'headers_count': len(request_info.get('headers', {})),
        }
        
        self.api_logger.info(
            f"API Request: {request_info['method']} {request_info['path']}",
            extra=log_data
        )
    
    async def _log_response(self, request_info: Dict[str, Any], response_info: Dict[str, Any]):
        """Log outgoing response"""
        
        log_data = {
            'event_type': 'api_response_sent',
            'request_id': request_info['request_id'],
            'method': request_info['method'],
            'path': request_info['path'],
            'status_code': response_info['status_code'],
            'duration_ms': response_info['duration_ms'],
            'client_ip': request_info['client_ip'],
            'user_id': request_info.get('user_id'),
            'response_size': response_info.get('content_length'),
            'success': 200 <= response_info['status_code'] < 400,
        }
        
        # Determine log level based on status code
        if response_info['status_code'] >= 500:
            log_level = logging.ERROR
        elif response_info['status_code'] >= 400:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO
        
        self.api_logger.log(
            log_level,
            f"API Response: {response_info['status_code']} {request_info['method']} {request_info['path']} ({response_info['duration_ms']:.2f}ms)",
            extra=log_data
        )
    
    async def _log_performance(self, request_info: Dict[str, Any], response_info: Dict[str, Any]):
        """Log performance metrics"""
        
        # Use the performance monitor to record API performance
        await measure_api_request(
            endpoint=request_info['path'],
            method=request_info['method'],
            duration_ms=response_info['duration_ms'],
            status_code=response_info['status_code'],
            response_size=self._parse_content_length(response_info.get('content_length')),
            request_id=request_info['request_id'],
            user_id=request_info.get('user_id'),
            client_ip=request_info['client_ip']
        )
    
    async def _log_security_events(self, request_info: Dict[str, Any], response_info: Dict[str, Any]):
        """Log security-relevant events"""
        
        security_events = []
        
        # Authentication failures
        if response_info['status_code'] == 401:
            security_events.append({
                'event_type': 'authentication_failure',
                'risk_level': 'medium',
                'details': {
                    'endpoint': request_info['path'],
                    'method': request_info['method'],
                    'client_ip': request_info['client_ip'],
                    'user_agent': request_info.get('user_agent')
                }
            })
        
        # Authorization failures
        elif response_info['status_code'] == 403:
            security_events.append({
                'event_type': 'authorization_failure',
                'risk_level': 'medium',
                'details': {
                    'endpoint': request_info['path'],
                    'method': request_info['method'],
                    'user_id': request_info.get('user_id'),
                    'client_ip': request_info['client_ip']
                }
            })
        
        # Suspicious request patterns
        if self._is_suspicious_request(request_info):
            security_events.append({
                'event_type': 'suspicious_request_pattern',
                'risk_level': 'high',
                'details': {
                    'endpoint': request_info['path'],
                    'method': request_info['method'],
                    'client_ip': request_info['client_ip'],
                    'user_agent': request_info.get('user_agent'),
                    'suspicious_indicators': self._get_suspicious_indicators(request_info)
                }
            })
        
        # Log security events
        for event in security_events:
            self.security_logger.warning(
                f"Security event: {event['event_type']}",
                extra={
                    'request_id': request_info['request_id'],
                    'security_event': True,
                    **event
                }
            )
    
    async def _log_error(self, request_info: Dict[str, Any], error: str, duration_ms: float):
        """Log request processing error"""
        
        log_data = {
            'event_type': 'api_request_error',
            'request_id': request_info['request_id'],
            'method': request_info['method'],
            'path': request_info['path'],
            'error': error,
            'duration_ms': duration_ms,
            'client_ip': request_info['client_ip'],
            'user_id': request_info.get('user_id'),
        }
        
        self.api_logger.error(
            f"API Error: {request_info['method']} {request_info['path']} - {error}",
            extra=log_data
        )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        
        # Check forwarded headers (reverse proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"
    
    def _is_safe_to_log_body(self, request: Request) -> bool:
        """Check if it's safe to log request body"""
        
        content_type = request.headers.get('content-type', '').lower()
        
        # Never log binary content
        if any(binary_type in content_type for binary_type in [
            'image/', 'video/', 'audio/', 'application/octet-stream',
            'application/pdf', 'application/zip'
        ]):
            return False
        
        # Be cautious with file uploads
        if 'multipart/form-data' in content_type:
            return False
        
        # Generally safe for JSON and form data (with masking)
        return content_type.startswith(('application/json', 'application/x-www-form-urlencoded'))
    
    def _is_safe_to_log_response_body(self, response: Response) -> bool:
        """Check if it's safe to log response body"""
        
        content_type = response.headers.get('content-type', '').lower()
        
        # Only log JSON responses
        return content_type.startswith('application/json')
    
    async def _read_request_body(self, request: Request) -> Optional[str]:
        """Read and return request body"""
        try:
            body = await request.body()
            if body:
                return body.decode('utf-8', errors='replace')
        except Exception:
            pass
        return None
    
    def _parse_content_length(self, content_length: Optional[str]) -> Optional[int]:
        """Parse content length header"""
        if content_length:
            try:
                return int(content_length)
            except ValueError:
                pass
        return None
    
    def _is_suspicious_request(self, request_info: Dict[str, Any]) -> bool:
        """Check if request has suspicious patterns"""
        
        # Check for common attack patterns in URL
        path = request_info['path'].lower()
        suspicious_patterns = [
            '../', '..\\', 'union select', 'script>', '<iframe',
            'javascript:', 'vbscript:', 'onload=', 'onerror=',
            'eval(', 'alert(', 'document.cookie', 'base64'
        ]
        
        if any(pattern in path for pattern in suspicious_patterns):
            return True
        
        # Check query parameters
        query_params = request_info.get('query_params', {})
        for value in query_params.values():
            if isinstance(value, str) and any(pattern in value.lower() for pattern in suspicious_patterns):
                return True
        
        # Check user agent for known bad patterns
        user_agent = request_info.get('user_agent', '').lower()
        suspicious_agents = ['sqlmap', 'nikto', 'burp', 'nmap', 'masscan']
        if any(agent in user_agent for agent in suspicious_agents):
            return True
        
        return False
    
    def _get_suspicious_indicators(self, request_info: Dict[str, Any]) -> List[str]:
        """Get list of suspicious indicators in request"""
        indicators = []
        
        path = request_info['path'].lower()
        if '../' in path or '..\\'  in path:
            indicators.append('path_traversal_attempt')
        
        if any(sql_keyword in path for sql_keyword in ['union', 'select', 'insert', 'delete']):
            indicators.append('sql_injection_attempt')
        
        if any(xss_pattern in path for xss_pattern in ['script>', '<iframe', 'javascript:']):
            indicators.append('xss_attempt')
        
        user_agent = request_info.get('user_agent', '').lower()
        if any(tool in user_agent for tool in ['sqlmap', 'nikto', 'burp']):
            indicators.append('security_tool_detected')
        
        return indicators
    
    def get_active_requests(self) -> Dict[str, Dict[str, Any]]:
        """Get currently active requests"""
        current_time = time.time()
        active = {}
        
        for request_id, info in self.active_requests.items():
            duration = current_time - info['start_time']
            active[request_id] = {
                **info,
                'duration_seconds': duration
            }
        
        return active
    
    def get_request_stats(self) -> Dict[str, Any]:
        """Get request processing statistics"""
        return {
            'active_requests': len(self.active_requests),
            'middleware_config': {
                'log_requests': self.log_requests,
                'log_responses': self.log_responses,
                'log_request_body': self.log_request_body,
                'log_response_body': self.log_response_body,
                'mask_sensitive_data': self.mask_sensitive_data,
                'max_body_size': self.max_body_size,
                'excluded_paths_count': len(self.excluded_paths)
            }
        }


# Convenience function to create the middleware
def create_request_logging_middleware(
    log_level: str = "INFO",
    log_bodies: bool = False,
    **kwargs
) -> RequestResponseLoggingMiddleware:
    """
    Create request logging middleware with sensible defaults for financial applications
    
    Args:
        log_level: Logging level
        log_bodies: Whether to log request/response bodies (security risk)
        **kwargs: Additional middleware configuration
        
    Returns:
        Configured middleware instance
    """
    return RequestResponseLoggingMiddleware(
        log_requests=True,
        log_responses=True,
        log_request_body=log_bodies,
        log_response_body=log_bodies,
        mask_sensitive_data=True,
        log_level=log_level,
        **kwargs
    )