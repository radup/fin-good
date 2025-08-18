"""
Global Error Handlers and Middleware for FinGood Financial Platform

This module provides centralized error handling with security-conscious
error responses that don't leak sensitive information while providing
useful debugging information for developers.
"""

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
import logging
import traceback
import sys
from datetime import datetime
from typing import Union, Dict, Any, Optional

from app.core.exceptions import FinGoodException, ValidationException
from app.schemas.error import (
    APIErrorResponse, 
    ErrorDetail, 
    ErrorCategory, 
    ErrorSeverity,
    FieldError,
    ValidationErrorResponse,
    AuthenticationErrorResponse,
    RateLimitErrorResponse
)
from app.core.config import settings
from app.core.audit_logger import security_audit_logger
from app.core.error_monitoring import error_monitor

# Configure logging
logger = logging.getLogger(__name__)


def create_error_response(
    request: Request,
    error_detail: ErrorDetail,
    status_code: int = 500,
    include_debug_info: bool = False
) -> JSONResponse:
    """Create a standardized error response"""
    
    # Sanitize developer message in production
    if not include_debug_info and not settings.DEBUG:
        error_detail.developer_message = None
        error_detail.context = {}
    
    response_data = APIErrorResponse(
        error=error_detail,
        request_id=getattr(request.state, 'request_id', None),
        path=str(request.url.path),
        method=request.method,
        documentation_url=f"https://docs.fingood.com/api/errors#{error_detail.code}",
        support_url="https://support.fingood.com"
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response_data.model_dump(exclude_none=True),
        headers={
            "X-Error-Code": error_detail.code,
            "X-Correlation-ID": error_detail.correlation_id,
            "X-API-Version": "v1"
        }
    )


def sanitize_value_for_logging(value: Any) -> Any:
    """Sanitize sensitive data from error logging"""
    if isinstance(value, str):
        # Mask potential sensitive data
        sensitive_patterns = ['password', 'token', 'key', 'secret', 'ssn', 'account']
        for pattern in sensitive_patterns:
            if pattern in value.lower():
                return "[REDACTED]"
    elif isinstance(value, datetime):
        # Convert datetime objects to ISO format strings
        return value.isoformat()
    return value


def sanitize_context_for_monitoring(context: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize context dictionary for error monitoring to handle datetime serialization"""
    sanitized = {}
    for key, value in context.items():
        if isinstance(value, datetime):
            sanitized[key] = value.isoformat()
        elif isinstance(value, dict):
            sanitized[key] = sanitize_context_for_monitoring(value)
        elif isinstance(value, list):
            sanitized[key] = [
                item.isoformat() if isinstance(item, datetime) else item 
                for item in value
            ]
        else:
            sanitized[key] = sanitize_value_for_logging(value)
    return sanitized


def _get_client_ip(request: Request) -> Optional[str]:
    """Extract client IP from request safely"""
    # Check for forwarded headers first
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client IP
    if hasattr(request, "client") and request.client:
        return request.client.host
    
    return None


async def custom_exception_handler(request: Request, exc: FinGoodException) -> JSONResponse:
    """Handle custom FinGood exceptions"""
    
    # Log the error with appropriate level based on severity and audit trail
    log_message = f"FinGood Exception: {exc.code} - {exc.message}"
    
    # Enhanced logging with request context
    log_extra = {
        "correlation_id": exc.correlation_id,
        "category": exc.category.value,
        "severity": exc.severity.value,
        "path": request.url.path,
        "method": request.method,
        "user_id": getattr(request.state, 'user_id', None),
        "request_id": getattr(request.state, 'request_id', None),
        "client_ip": _get_client_ip(request),
        "user_agent": request.headers.get("User-Agent"),
        "error_code": exc.code
    }
    
    if exc.severity == ErrorSeverity.CRITICAL:
        logger.critical(log_message, extra=log_extra)
        # Log critical security events to audit logger - TEMPORARILY DISABLED
        # try:
        #     if exc.category in [ErrorCategory.FINANCIAL_COMPLIANCE, ErrorCategory.SYSTEM_ERROR]:
        #         security_audit_logger.log_security_violation(
        #             violation_type=exc.category.value,
        #             description=exc.message,
        #             user_id=getattr(request.state, 'user_id', None),
        #             request=request,
        #             details={"error_code": exc.code, "correlation_id": exc.correlation_id}
        #         )
        # except Exception as audit_error:
        #     logger.error(f"Security audit logging failed: {audit_error}")
    elif exc.severity == ErrorSeverity.HIGH:
        logger.error(log_message, extra=log_extra)
        # Log high-severity authentication/authorization failures - TEMPORARILY DISABLED
        # try:
        #     if exc.category == ErrorCategory.AUTHENTICATION:
        #         security_audit_logger.log_authentication_failure(
        #             attempted_email=getattr(request.state, 'attempted_email', "unknown"),
        #             request=request,
        #             reason=exc.code
        #         )
        #     elif exc.category == ErrorCategory.AUTHORIZATION:
        #         security_audit_logger.log_access_denied(
        #             resource=request.url.path,
        #             user_id=getattr(request.state, 'user_id', None),
        #             request=request,
        #             reason=exc.code
        #         )
        # except Exception as audit_error:
        #     logger.error(f"Security audit logging failed: {audit_error}")
    else:
        logger.warning(log_message, extra=log_extra)
    
    # Record error for monitoring and alerting - TEMPORARILY DISABLED
    # try:
    #     context = sanitize_context_for_monitoring({
    #         "user_id": getattr(request.state, 'user_id', None),
    #         "client_ip": _get_client_ip(request),
    #         "path": request.url.path,
    #         "method": request.method,
    #         "user_agent": request.headers.get("User-Agent"),
    #         "request_id": getattr(request.state, 'request_id', None),
    #         "correlation_id": exc.correlation_id
    #     })
    #     error_monitor.record_error(
    #         error_code=exc.code,
    #         category=exc.category,
    #         severity=exc.severity,
    #         context=context
    #     )
    # except Exception as monitoring_error:
    #     # If error monitoring fails, log it but don't let it break the response
    #     logger.error(f"Error monitoring failed: {monitoring_error}")
    pass
    
    # Create error detail
    error_detail = ErrorDetail(
        code=exc.code,
        message=exc.message,
        category=exc.category,
        severity=exc.severity,
        correlation_id=exc.correlation_id,
        user_message=exc.user_message,
        suggested_action=exc.suggested_action,
        developer_message=exc.message if settings.DEBUG else None,
        field_errors=exc.field_errors,
        context=exc.context,
        transaction_id=exc.transaction_id,
        account_id=exc.account_id,
        retry_after=exc.retry_after,
        external_service=exc.external_service,
        external_error_id=exc.external_error_id
    )
    
    # Map category to HTTP status code
    status_map = {
        ErrorCategory.AUTHENTICATION: status.HTTP_401_UNAUTHORIZED,
        ErrorCategory.AUTHORIZATION: status.HTTP_403_FORBIDDEN,
        ErrorCategory.VALIDATION: status.HTTP_422_UNPROCESSABLE_ENTITY,
        ErrorCategory.RESOURCE_NOT_FOUND: status.HTTP_404_NOT_FOUND,
        ErrorCategory.BUSINESS_LOGIC: status.HTTP_400_BAD_REQUEST,
        ErrorCategory.RATE_LIMITING: status.HTTP_429_TOO_MANY_REQUESTS,
        ErrorCategory.EXTERNAL_SERVICE: status.HTTP_502_BAD_GATEWAY,
        ErrorCategory.SYSTEM_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ErrorCategory.FINANCIAL_COMPLIANCE: status.HTTP_400_BAD_REQUEST,
        ErrorCategory.DATA_INTEGRITY: status.HTTP_409_CONFLICT
    }
    
    http_status = status_map.get(exc.category, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return create_error_response(
        request=request,
        error_detail=error_detail,
        status_code=http_status,
        include_debug_info=settings.DEBUG
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPExceptions"""
    
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}", extra={
        "path": request.url.path,
        "method": request.method,
        "status_code": exc.status_code
    })
    
    # Map HTTP status to error category
    category_map = {
        401: ErrorCategory.AUTHENTICATION,
        403: ErrorCategory.AUTHORIZATION,
        404: ErrorCategory.RESOURCE_NOT_FOUND,
        429: ErrorCategory.RATE_LIMITING,
    }
    
    category = category_map.get(exc.status_code, ErrorCategory.SYSTEM_ERROR)
    
    # Create user-friendly messages
    user_messages = {
        401: "Authentication required. Please log in to continue",
        403: "You don't have permission to access this resource",
        404: "The requested resource was not found",
        429: "Too many requests. Please slow down and try again later",
    }
    
    suggested_actions = {
        401: "Please log in with valid credentials",
        403: "Contact your administrator for access",
        404: "Please check the URL and try again",
        429: "Wait a moment before making another request",
    }
    
    error_detail = ErrorDetail(
        code=f"HTTP_{exc.status_code}",
        message=str(exc.detail),
        category=category,
        severity=ErrorSeverity.MEDIUM,
        user_message=user_messages.get(exc.status_code, str(exc.detail)),
        suggested_action=suggested_actions.get(exc.status_code, "Please try again"),
        developer_message=str(exc.detail) if settings.DEBUG else None
    )
    
    return create_error_response(
        request=request,
        error_detail=error_detail,
        status_code=exc.status_code,
        include_debug_info=settings.DEBUG
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors"""
    
    logger.warning(f"Validation Error: {len(exc.errors())} errors", extra={
        "path": request.url.path,
        "method": request.method,
        "error_count": len(exc.errors())
    })
    
    # Convert Pydantic errors to our format
    field_errors = []
    for error in exc.errors():
        field_path = ".".join(str(loc) for loc in error["loc"])
        field_errors.append(FieldError(
            field=field_path,
            message=error["msg"],
            code=error["type"].upper().replace(".", "_"),
            value=sanitize_value_for_logging(error.get("input"))
        ))
    
    error_detail = ErrorDetail(
        code="VALIDATION_ERROR",
        message="Request validation failed",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.MEDIUM,
        user_message="Please correct the highlighted fields and try again",
        suggested_action="Review the field errors and provide valid data",
        developer_message=f"Validation failed for {len(field_errors)} fields" if settings.DEBUG else None,
        field_errors=field_errors
    )
    
    return create_error_response(
        request=request,
        error_detail=error_detail,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        include_debug_info=settings.DEBUG
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle SQLAlchemy database errors"""
    
    logger.error(f"Database Error: {type(exc).__name__}", extra={
        "path": request.url.path,
        "method": request.method,
        "exception_type": type(exc).__name__
    })
    
    # Handle specific database errors
    if isinstance(exc, IntegrityError):
        error_detail = ErrorDetail(
            code="DATA_INTEGRITY_ERROR",
            message="Data integrity constraint violation",
            category=ErrorCategory.DATA_INTEGRITY,
            severity=ErrorSeverity.HIGH,
            user_message="There was a conflict with existing data",
            suggested_action="Please check your data and try again",
            developer_message=str(exc) if settings.DEBUG else None
        )
        http_status = status.HTTP_409_CONFLICT
    else:
        error_detail = ErrorDetail(
            code="DATABASE_ERROR",
            message="Database operation failed",
            category=ErrorCategory.SYSTEM_ERROR,
            severity=ErrorSeverity.CRITICAL,
            user_message="We're experiencing technical difficulties. Please try again later",
            suggested_action="If the problem persists, please contact support",
            developer_message=str(exc) if settings.DEBUG else None
        )
        http_status = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    return create_error_response(
        request=request,
        error_detail=error_detail,
        status_code=http_status,
        include_debug_info=settings.DEBUG
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other unhandled exceptions"""
    
    # Enhanced logging with request context for security monitoring
    log_extra = {
        "path": request.url.path,
        "method": request.method,
        "exception_type": type(exc).__name__,
        "user_id": getattr(request.state, 'user_id', None),
        "request_id": getattr(request.state, 'request_id', None),
        "client_ip": _get_client_ip(request),
        "user_agent": request.headers.get("User-Agent"),
        "traceback": traceback.format_exc() if settings.DEBUG else None
    }
    
    # Log the full exception for debugging
    logger.critical(f"Unhandled Exception: {type(exc).__name__} - {str(exc)}", extra=log_extra)
    
    # Log critical system errors to security audit trail
    # Security audit logging temporarily disabled
    # try:
    #     security_audit_logger.log_security_violation(
    #         violation_type="system_error",
    #         description=f"Unhandled exception: {type(exc).__name__}",
    #         user_id=getattr(request.state, 'user_id', None),
    #         request=request,
    #         details={
    #         #     "exception_type": type(exc).__name__,
    #         #     "error_message": str(exc)[:200],  # Limit message length for security
    #         #     "request_id": getattr(request.state, 'request_id', None)
    #         # }
    #     # )
    # except Exception as audit_error:
    #     # If security audit logging fails, log it but don't let it break the response
    #     logger.error(f"Security audit logging failed: {audit_error}")
    pass
    
    # Record unhandled exception for monitoring
    # Error monitoring temporarily disabled
    # try:
    #     context = sanitize_context_for_monitoring({
    #         "user_id": getattr(request.state, 'user_id', None),
    #         "client_ip": _get_client_ip(request),
    #         "path": request.url.path,
    #         "method": request.method,
    #         "exception_type": type(exc).__name__,
    #         "error_message": str(exc)[:200],
    #         "request_id": getattr(request.state, 'request_id', None)
    #     })
    #     error_monitor.record_error(
    #         error_code="INTERNAL_SERVER_ERROR",
    #         category=ErrorCategory.SYSTEM_ERROR,
    #         severity=ErrorSeverity.CRITICAL,
    #         context=context
    #     )
    # except Exception as monitoring_error:
    #     # If error monitoring fails, log it but don't let it break the response
    #     logger.error(f"Error monitoring failed: {monitoring_error}")
    pass
    
    error_detail = ErrorDetail(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        category=ErrorCategory.SYSTEM_ERROR,
        severity=ErrorSeverity.CRITICAL,
        user_message="We're experiencing technical difficulties. Please try again later",
        suggested_action="If the problem persists, please contact support",
        developer_message=f"{type(exc).__name__}: {str(exc)}" if settings.DEBUG else None
    )
    
    return create_error_response(
        request=request,
        error_detail=error_detail,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        include_debug_info=settings.DEBUG
    )


async def validation_middleware_exception_handler(request: Request, exc: ValidationException) -> JSONResponse:
    """Handle validation exceptions from our custom validation middleware"""
    
    logger.warning(f"Validation Middleware Error: {exc.message}", extra={
        "path": request.url.path,
        "method": request.method,
        "correlation_id": exc.correlation_id,
        "field_errors": len(exc.field_errors) if exc.field_errors else 0
    })
    
    # Log security violations if detected
    security_indicators = ['SQL_INJECTION_ATTEMPT', 'XSS_VIOLATION', 'SECURITY_VIOLATION']
    has_security_violation = any(
        error.code in security_indicators 
        for error in (exc.field_errors or [])
    )
    
    if has_security_violation:
        security_audit_logger.log_security_violation(
            violation_type="input_validation_security",
            description=f"Security violation detected in input validation: {exc.message}",
            user_id=getattr(request.state, 'user_id', None),
            request=request,
            details={
                "correlation_id": exc.correlation_id,
                "security_violations": [
                    error.code for error in (exc.field_errors or [])
                    if error.code in security_indicators
                ]
            }
        )
    
    error_detail = ErrorDetail(
        code=exc.code,
        message=exc.message,
        category=exc.category,
        severity=exc.severity,
        correlation_id=exc.correlation_id,
        user_message=exc.user_message,
        suggested_action=exc.suggested_action,
        developer_message=exc.message if settings.DEBUG else None,
        field_errors=exc.field_errors,
        context=exc.context
    )
    
    return create_error_response(
        request=request,
        error_detail=error_detail,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        include_debug_info=settings.DEBUG
    )


def setup_error_handlers(app: FastAPI) -> None:
    """Setup all error handlers for the FastAPI application"""
    
    # Custom exception handlers (order matters - more specific first)
    app.add_exception_handler(ValidationException, validation_middleware_exception_handler)
    app.add_exception_handler(FinGoodException, custom_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Error handlers configured successfully")