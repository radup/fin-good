"""
Error Message Sanitization for Financial Security

This module provides comprehensive error message sanitization to prevent
information disclosure while maintaining security audit trails and developer debugging.
Implements CRIT-008 requirements for financial system error handling.
"""

import re
import logging
import traceback
from typing import Dict, Any, Optional, List, Tuple, Union
from pathlib import Path
from datetime import datetime
import json

from app.core.config import settings
from app.schemas.error import ErrorDetail, ErrorCategory, ErrorSeverity, FieldError


logger = logging.getLogger(__name__)


class ErrorSanitizer:
    """
    Comprehensive error message sanitization for financial applications.
    
    Ensures sensitive information like system paths, database details, internal
    structures, and configuration data are removed from user-facing error messages
    while maintaining complete developer logs for debugging.
    """
    
    # Sensitive patterns to sanitize
    SENSITIVE_PATTERNS = {
        # File system paths (Unix and Windows)
        'file_paths': [
            r'/[a-zA-Z0-9_\-\.\/]+',  # Unix paths
            r'[A-Za-z]:\\[a-zA-Z0-9_\-\.\\]+',  # Windows paths
            r'\/var\/[a-zA-Z0-9_\-\.\/]+',  # /var paths
            r'\/home\/[a-zA-Z0-9_\-\.\/]+',  # /home paths
            r'\/tmp\/[a-zA-Z0-9_\-\.\/]+',  # /tmp paths
            r'\/Users\/[a-zA-Z0-9_\-\.\/]+',  # macOS user paths
        ],
        
        # Database connection strings and details
        'database': [
            r'postgresql://[^\s]+',
            r'mysql://[^\s]+',
            r'sqlite:///[^\s]+',
            r'Host:\s*[a-zA-Z0-9\.\-]+',
            r'Port:\s*\d+',
            r'Database:\s*[a-zA-Z0-9_\-]+',
            r'User:\s*[a-zA-Z0-9_\-]+',
            r'Schema:\s*[a-zA-Z0-9_\-]+',
            r'Table "[a-zA-Z0-9_\-]+"',
            r'Column "[a-zA-Z0-9_\-]+"',
            r'DETAIL:\s*[^\n]+',
            r'HINT:\s*[^\n]+',
            r'LINE \d+:\s*[^\n]+',
            r'CONTEXT:\s*[^\n]+',
            r'Query:\s*[^\n]+',
            r'SQL state:\s*[^\n]+',
        ],
        
        # Server and network information
        'network': [
            r'\b(?:\d{1,3}\.){3}\d{1,3}\b',  # IP addresses
            r'localhost:\d+',
            r'127\.0\.0\.1:\d+',
            r'0\.0\.0\.0:\d+',
            r'Server:\s*[a-zA-Z0-9\.\-]+',
            r'Host:\s*[a-zA-Z0-9\.\-]+',
            r'Port:\s*\d+',
        ],
        
        # Authentication and security details
        'auth': [
            r'Token:\s*[a-zA-Z0-9\.\-_]+',
            r'Bearer\s+[a-zA-Z0-9\.\-_]+',
            r'api[_\-]?key["\']?\s*[:=]\s*["\']?[a-zA-Z0-9\.\-_]+',
            r'secret["\']?\s*[:=]\s*["\']?[a-zA-Z0-9\.\-_]+',
            r'password["\']?\s*[:=]\s*["\']?[^\s"\']+',
            r'JWT\s+[a-zA-Z0-9\.\-_]+',
            r'Session ID:\s*[a-zA-Z0-9\.\-_]+',
        ],
        
        # Internal service and module information
        'internal': [
            r'app\.[a-zA-Z0-9_\.]+',  # Python module paths
            r'File\s+"[^"]+\.py"',
            r'line\s+\d+',
            r'in\s+[a-zA-Z0-9_]+',
            r'function\s+[a-zA-Z0-9_]+',
            r'class\s+[a-zA-Z0-9_]+',
            r'Exception in thread',
            r'Traceback \(most recent call last\)',
        ],
        
        # Configuration and environment variables
        'config': [
            r'[A-Z_]+_URL=\S+',
            r'[A-Z_]+_KEY=\S+',
            r'[A-Z_]+_SECRET=\S+',
            r'DEBUG=\S+',
            r'ENVIRONMENT=\S+',
            r'VERSION=\S+',
        ],
        
        # Financial and PII data patterns
        'financial': [
            r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b',  # Credit card patterns
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN patterns
            r'\$\d+\.\d{2}',  # Specific dollar amounts in errors
            r'account[_\s]*(?:id|number)["\']?\s*[:=]\s*["\']?[a-zA-Z0-9\-_]+',
            r'customer[_\s]*id["\']?\s*[:=]\s*["\']?[a-zA-Z0-9\-_]+',
        ]
    }
    
    # Safe replacements for sensitive data
    SAFE_REPLACEMENTS = {
        'file_paths': '[SYSTEM_PATH]',
        'database': '[DATABASE_INFO]',
        'network': '[SERVER_INFO]',
        'auth': '[AUTH_TOKEN]',
        'internal': '[INTERNAL_REFERENCE]',
        'config': '[CONFIG_VALUE]',
        'financial': '[PROTECTED_DATA]',
    }
    
    # User-friendly error messages for common scenarios
    USER_FRIENDLY_MESSAGES = {
        'database_error': "We're experiencing a temporary database issue. Please try again in a moment.",
        'file_error': "There was an issue processing your file. Please check the format and try again.",
        'network_error': "We're experiencing connectivity issues. Please try again later.",
        'auth_error': "Authentication failed. Please check your credentials and try again.",
        'validation_error': "The provided data is invalid. Please review and correct the highlighted fields.",
        'permission_error': "You don't have permission to perform this action.",
        'rate_limit_error': "Too many requests. Please wait before trying again.",
        'system_error': "We're experiencing technical difficulties. Please try again later.",
        'external_service_error': "We're experiencing issues with an external service. Please try again later.",
        'compliance_error': "This action violates our compliance policies.",
    }
    
    def __init__(self):
        """Initialize the error sanitizer with compiled regex patterns."""
        self._compiled_patterns = {}
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Compile all regex patterns for efficient matching."""
        for category, patterns in self.SENSITIVE_PATTERNS.items():
            self._compiled_patterns[category] = [
                re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                for pattern in patterns
            ]
    
    def sanitize_error_message(
        self, 
        message: str, 
        include_safe_details: bool = False,
        preserve_field_names: bool = True
    ) -> str:
        """
        Sanitize an error message by removing sensitive information.
        
        Args:
            message: The original error message
            include_safe_details: Whether to include some safe technical details
            preserve_field_names: Whether to preserve field names in validation errors
            
        Returns:
            Sanitized error message safe for user display
        """
        if not message:
            return message
        
        sanitized = str(message)
        
        # Apply sanitization patterns
        for category, patterns in self._compiled_patterns.items():
            replacement = self.SAFE_REPLACEMENTS[category]
            
            for pattern in patterns:
                # For certain categories, preserve some context if requested
                if include_safe_details and category in ['database', 'internal']:
                    # Keep error type but remove specifics
                    if 'constraint' in sanitized.lower():
                        sanitized = pattern.sub('[CONSTRAINT_VIOLATION]', sanitized)
                    elif 'foreign key' in sanitized.lower():
                        sanitized = pattern.sub('[REFERENCE_ERROR]', sanitized)
                    else:
                        sanitized = pattern.sub(replacement, sanitized)
                else:
                    sanitized = pattern.sub(replacement, sanitized)
        
        # Clean up multiple consecutive sanitization markers
        sanitized = re.sub(r'\[([A-Z_]+)\](\s*\[([A-Z_]+)\])+', r'[\1]', sanitized)
        
        # Remove empty parentheses and brackets after sanitization
        sanitized = re.sub(r'\(\s*\[?[A-Z_]*\]?\s*\)', '', sanitized)
        sanitized = re.sub(r'\[\s*\]', '', sanitized)
        
        # Clean up extra whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        return sanitized
    
    def get_user_friendly_message(
        self, 
        error_category: ErrorCategory,
        original_message: str = None
    ) -> str:
        """
        Get a user-friendly error message based on error category.
        
        Args:
            error_category: The category of error
            original_message: Original error message for context
            
        Returns:
            User-friendly error message
        """
        category_mapping = {
            ErrorCategory.AUTHENTICATION: 'auth_error',
            ErrorCategory.AUTHORIZATION: 'permission_error',
            ErrorCategory.VALIDATION: 'validation_error',
            ErrorCategory.RATE_LIMITING: 'rate_limit_error',
            ErrorCategory.EXTERNAL_SERVICE: 'external_service_error',
            ErrorCategory.SYSTEM_ERROR: 'system_error',
            ErrorCategory.FINANCIAL_COMPLIANCE: 'compliance_error',
            ErrorCategory.DATA_INTEGRITY: 'database_error',
        }
        
        message_key = category_mapping.get(error_category, 'system_error')
        base_message = self.USER_FRIENDLY_MESSAGES[message_key]
        
        # Add context from original message if it's safe
        if original_message and len(original_message) < 100:
            # Check if original message contains only safe information
            if not any(
                any(pattern.search(original_message) for pattern in patterns)
                for patterns in self._compiled_patterns.values()
            ):
                return f"{base_message} ({original_message})"
        
        return base_message
    
    def sanitize_exception_for_logging(
        self, 
        exception: Exception,
        include_traceback: bool = None
    ) -> Dict[str, Any]:
        """
        Sanitize exception information for secure logging.
        
        Args:
            exception: The exception to sanitize
            include_traceback: Whether to include traceback (defaults to DEBUG setting)
            
        Returns:
            Dictionary with sanitized exception information
        """
        if include_traceback is None:
            include_traceback = settings.DEBUG
        
        result = {
            'type': type(exception).__name__,
            'message': self.sanitize_error_message(str(exception)),
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        # Add traceback if in debug mode and requested
        if include_traceback:
            tb = traceback.format_exc()
            result['traceback'] = self.sanitize_error_message(tb, include_safe_details=True)
        
        # Add exception attributes safely
        safe_attrs = {}
        for attr_name in ['code', 'errno', 'filename', 'lineno']:
            if hasattr(exception, attr_name):
                attr_value = getattr(exception, attr_name)
                if attr_name == 'filename' and attr_value:
                    # Sanitize file paths
                    safe_attrs[attr_name] = self.sanitize_error_message(str(attr_value))
                elif isinstance(attr_value, (str, int, float, bool)):
                    safe_attrs[attr_name] = attr_value
        
        if safe_attrs:
            result['attributes'] = safe_attrs
        
        return result
    
    def create_sanitized_error_detail(
        self,
        exception: Exception,
        error_code: str,
        error_category: ErrorCategory,
        error_severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        user_message: Optional[str] = None,
        suggested_action: Optional[str] = None,
        field_errors: Optional[List[FieldError]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorDetail:
        """
        Create a sanitized ErrorDetail from an exception.
        
        Args:
            exception: The original exception
            error_code: Standardized error code
            error_category: Error category
            error_severity: Error severity level
            user_message: Custom user message (will be sanitized)
            suggested_action: Suggested action for user
            field_errors: Field-specific errors
            context: Additional context (will be sanitized)
            
        Returns:
            Sanitized ErrorDetail instance
        """
        # Sanitize the original exception message
        sanitized_message = self.sanitize_error_message(str(exception))
        
        # Use provided user message or generate one
        if user_message:
            final_user_message = self.sanitize_error_message(user_message)
        else:
            final_user_message = self.get_user_friendly_message(error_category, sanitized_message)
        
        # Sanitize developer message (only include if in debug mode)
        developer_message = None
        if settings.DEBUG:
            developer_message = sanitized_message
        
        # Sanitize context if provided
        sanitized_context = {}
        if context:
            for key, value in context.items():
                if isinstance(value, str):
                    sanitized_context[key] = self.sanitize_error_message(value)
                elif isinstance(value, (int, float, bool, list, dict)):
                    # For complex types, convert to string and sanitize
                    sanitized_context[key] = self.sanitize_error_message(str(value))
                else:
                    sanitized_context[key] = str(type(value).__name__)
        
        # Sanitize field errors
        sanitized_field_errors = []
        if field_errors:
            for field_error in field_errors:
                sanitized_field_errors.append(FieldError(
                    field=field_error.field,  # Field names are generally safe
                    message=self.sanitize_error_message(field_error.message),
                    code=field_error.code,
                    value=self.sanitize_error_message(str(field_error.value)) if field_error.value else None
                ))
        
        return ErrorDetail(
            code=error_code,
            message=sanitized_message,
            category=error_category,
            severity=error_severity,
            user_message=final_user_message,
            suggested_action=suggested_action,
            developer_message=developer_message,
            field_errors=sanitized_field_errors or None,
            context=sanitized_context if sanitized_context else None
        )
    
    def log_original_error(
        self,
        exception: Exception,
        correlation_id: str,
        request_context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log the original, unsanitized error for developer debugging.
        
        Args:
            exception: The original exception
            correlation_id: Correlation ID for tracking
            request_context: Additional request context
        """
        log_data = {
            'correlation_id': correlation_id,
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        # Add traceback in debug mode
        if settings.DEBUG:
            log_data['traceback'] = traceback.format_exc()
        
        # Add request context if provided
        if request_context:
            # Sanitize request context for logging
            safe_context = {}
            for key, value in request_context.items():
                if key.lower() in ['password', 'token', 'secret', 'key']:
                    safe_context[key] = '[REDACTED]'
                else:
                    safe_context[key] = value
            log_data['request_context'] = safe_context
        
        # Log at appropriate level based on exception type
        if isinstance(exception, (PermissionError, FileNotFoundError)):
            logger.warning(f"Application error [{correlation_id}]", extra=log_data)
        elif isinstance(exception, (ConnectionError, TimeoutError)):
            logger.error(f"Infrastructure error [{correlation_id}]", extra=log_data)
        else:
            logger.critical(f"Unexpected error [{correlation_id}]", extra=log_data)


# Global sanitizer instance
error_sanitizer = ErrorSanitizer()


def sanitize_error_for_user(
    exception: Exception,
    error_category: ErrorCategory = ErrorCategory.SYSTEM_ERROR,
    include_technical_details: bool = False
) -> Tuple[str, str]:
    """
    Convenience function to sanitize an error for user display.
    
    Args:
        exception: The exception to sanitize
        error_category: Category of error for appropriate messaging
        include_technical_details: Whether to include some technical details
        
    Returns:
        Tuple of (user_message, sanitized_technical_message)
    """
    user_message = error_sanitizer.get_user_friendly_message(error_category, str(exception))
    technical_message = error_sanitizer.sanitize_error_message(
        str(exception), 
        include_safe_details=include_technical_details
    )
    
    return user_message, technical_message


def create_secure_error_response(
    exception: Exception,
    error_code: str,
    error_category: ErrorCategory,
    correlation_id: Optional[str] = None,
    **kwargs
) -> ErrorDetail:
    """
    Convenience function to create a secure error response.
    
    Args:
        exception: The original exception
        error_code: Standardized error code
        error_category: Error category
        correlation_id: Optional correlation ID for logging
        **kwargs: Additional arguments for ErrorDetail
        
    Returns:
        Sanitized ErrorDetail instance
    """
    if correlation_id:
        error_sanitizer.log_original_error(exception, correlation_id)
    
    return error_sanitizer.create_sanitized_error_detail(
        exception=exception,
        error_code=error_code,
        error_category=error_category,
        **kwargs
    )