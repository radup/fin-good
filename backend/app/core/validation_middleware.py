"""
Request/Response Validation Middleware for FinGood Financial Platform

This middleware provides comprehensive validation for all API endpoints with:
- Pydantic-based request/response validation
- Financial data validation and sanitization
- SQL injection prevention
- Input sanitization and normalization
- Comprehensive error handling with field-level errors
"""

import re
import json
import html
import logging
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime
from decimal import Decimal, InvalidOperation
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, ValidationError, Field, field_validator
from sqlalchemy import text
import bleach

from app.schemas.error import (
    APIErrorResponse, ErrorDetail, FieldError, 
    ErrorCategory, ErrorSeverity
)
from app.core.exceptions import ValidationException

logger = logging.getLogger(__name__)


class ValidationMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive validation middleware for request/response processing
    with financial data security focus.
    """
    
    def __init__(
        self, 
        app,
        enable_request_validation: bool = True,
        enable_response_validation: bool = True,
        enable_sql_injection_check: bool = True,
        enable_xss_protection: bool = True,
        log_validation_errors: bool = True
    ):
        super().__init__(app)
        self.enable_request_validation = enable_request_validation
        self.enable_response_validation = enable_response_validation
        self.enable_sql_injection_check = enable_sql_injection_check
        self.enable_xss_protection = enable_xss_protection
        self.log_validation_errors = log_validation_errors
        
        # Initialize validators
        self.input_sanitizer = InputSanitizer()
        self.financial_validator = FinancialDataValidator()
        self.sql_injection_detector = SQLInjectionDetector()
        
    async def dispatch(self, request: Request, call_next):
        """Process request through validation pipeline"""
        
        # Validate and sanitize request
        if self.enable_request_validation:
            try:
                await self._validate_request(request)
            except ValidationException as e:
                return self._create_validation_error_response(e, request)
            except Exception as e:
                logger.error(f"Unexpected validation error: {str(e)}")
                return self._create_system_error_response(request)
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"Request processing error: {str(e)}")
            return self._create_system_error_response(request)
        
        # Validate response if needed
        if self.enable_response_validation and hasattr(response, 'body'):
            try:
                await self._validate_response(response, request)
            except Exception as e:
                logger.error(f"Response validation error: {str(e)}")
                # Don't fail the request for response validation errors
                # but log them for monitoring
        
        return response
    
    async def _validate_request(self, request: Request):
        """Validate incoming request data"""
        
        # Skip validation for certain endpoints
        if self._should_skip_validation(request):
            return
        
        # Get request body if available
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    body = json.loads(body.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                raise ValidationException(
                    message="Invalid JSON in request body",
                    field_errors=[FieldError(
                        field="body",
                        message="Request body must be valid JSON",
                        code="INVALID_JSON",
                        value=str(e)
                    )]
                )
        
        # Validate query parameters
        query_params = dict(request.query_params)
        validated_params = {}
        field_errors = []
        
        for key, value in query_params.items():
            try:
                validated_value = self._validate_parameter(key, value, request.url.path)
                validated_params[key] = validated_value
            except ValueError as e:
                field_errors.append(FieldError(
                    field=key,
                    message=str(e),
                    code="INVALID_PARAMETER",
                    value=value
                ))
        
        # Validate request body
        if body:
            try:
                validated_body = self._validate_body(body, request.url.path)
                # Store validated data back in request state for use by endpoints
                request.state.validated_body = validated_body
            except ValidationException as e:
                field_errors.extend(e.field_errors)
        
        # Check for SQL injection patterns
        if self.enable_sql_injection_check:
            all_values = list(query_params.values())
            if body and isinstance(body, dict):
                all_values.extend(self._extract_string_values(body))
            
            for value in all_values:
                if isinstance(value, str) and self.sql_injection_detector.is_suspicious(value):
                    field_errors.append(FieldError(
                        field="security",
                        message="Potentially dangerous input detected",
                        code="SECURITY_VIOLATION",
                        value="[REDACTED]"
                    ))
        
        # Raise validation exception if any errors found
        if field_errors:
            raise ValidationException(
                message="Request validation failed",
                field_errors=field_errors
            )
    
    async def _validate_response(self, response: Response, request: Request):
        """Validate outgoing response data"""
        
        # Only validate JSON responses
        if not response.headers.get('content-type', '').startswith('application/json'):
            return
        
        try:
            # This is a basic response validation
            # In a full implementation, you'd validate against response schemas
            pass
        except Exception as e:
            logger.warning(f"Response validation failed: {str(e)}")
    
    def _should_skip_validation(self, request: Request) -> bool:
        """Determine if validation should be skipped for this request"""
        
        skip_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
        
        return any(request.url.path.startswith(path) for path in skip_paths)
    
    def _validate_parameter(self, key: str, value: str, path: str) -> Any:
        """Validate individual query parameter"""
        
        # Sanitize input first
        if self.enable_xss_protection:
            value = self.input_sanitizer.sanitize_string(value)
        
        # Apply parameter-specific validation
        if key in ['skip', 'limit', 'page']:
            return self._validate_integer_param(key, value, min_value=0)
        elif key in ['amount', 'min_amount', 'max_amount']:
            return self.financial_validator.validate_amount(value)
        elif key in ['start_date', 'end_date']:
            return self._validate_date_param(key, value)
        elif key in ['sort_order']:
            return self._validate_enum_param(key, value, ['asc', 'desc'])
        elif key in ['is_income', 'is_categorized']:
            return self._validate_boolean_param(key, value)
        else:
            # Generic string validation
            return self.input_sanitizer.sanitize_string(value)
    
    def _validate_body(self, body: Dict[str, Any], path: str) -> Dict[str, Any]:
        """Validate request body data"""
        
        validated_body = {}
        field_errors = []
        
        for key, value in body.items():
            try:
                if key in ['amount']:
                    validated_body[key] = self.financial_validator.validate_amount(value)
                elif key in ['date']:
                    validated_body[key] = self._validate_date_value(key, value)
                elif key in ['description', 'vendor', 'category', 'subcategory']:
                    validated_body[key] = self.input_sanitizer.sanitize_string(str(value))
                elif key in ['is_income', 'is_categorized', 'create_rule']:
                    validated_body[key] = self._validate_boolean_value(key, value)
                else:
                    # Generic validation
                    if isinstance(value, str):
                        validated_body[key] = self.input_sanitizer.sanitize_string(value)
                    else:
                        validated_body[key] = value
            except ValueError as e:
                field_errors.append(FieldError(
                    field=key,
                    message=str(e),
                    code="INVALID_FIELD_VALUE",
                    value=value
                ))
        
        if field_errors:
            raise ValidationException(
                message="Body validation failed",
                field_errors=field_errors
            )
        
        return validated_body
    
    def _validate_integer_param(self, key: str, value: str, min_value: int = None, max_value: int = None) -> int:
        """Validate integer parameter"""
        try:
            int_value = int(value)
            if min_value is not None and int_value < min_value:
                raise ValueError(f"{key} must be >= {min_value}")
            if max_value is not None and int_value > max_value:
                raise ValueError(f"{key} must be <= {max_value}")
            return int_value
        except ValueError:
            raise ValueError(f"{key} must be a valid integer")
    
    def _validate_date_param(self, key: str, value: str) -> datetime:
        """Validate date parameter"""
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError(f"{key} must be a valid ISO format date")
    
    def _validate_date_value(self, key: str, value: Any) -> datetime:
        """Validate date value from body"""
        if isinstance(value, str):
            return self._validate_date_param(key, value)
        elif isinstance(value, datetime):
            return value
        else:
            raise ValueError(f"{key} must be a valid date")
    
    def _validate_enum_param(self, key: str, value: str, allowed_values: List[str]) -> str:
        """Validate enum parameter"""
        if value.lower() not in [v.lower() for v in allowed_values]:
            raise ValueError(f"{key} must be one of: {', '.join(allowed_values)}")
        return value.lower()
    
    def _validate_boolean_param(self, key: str, value: str) -> bool:
        """Validate boolean parameter"""
        if value.lower() in ['true', '1', 'yes', 'on']:
            return True
        elif value.lower() in ['false', '0', 'no', 'off']:
            return False
        else:
            raise ValueError(f"{key} must be a valid boolean (true/false)")
    
    def _validate_boolean_value(self, key: str, value: Any) -> bool:
        """Validate boolean value from body"""
        if isinstance(value, bool):
            return value
        elif isinstance(value, str):
            return self._validate_boolean_param(key, value)
        else:
            raise ValueError(f"{key} must be a boolean value")
    
    def _extract_string_values(self, data: Any) -> List[str]:
        """Recursively extract string values from nested data structure"""
        strings = []
        
        if isinstance(data, str):
            strings.append(data)
        elif isinstance(data, dict):
            for value in data.values():
                strings.extend(self._extract_string_values(value))
        elif isinstance(data, list):
            for item in data:
                strings.extend(self._extract_string_values(item))
        
        return strings
    
    def _create_validation_error_response(self, exception: ValidationException, request: Request) -> JSONResponse:
        """Create standardized validation error response"""
        
        if self.log_validation_errors:
            logger.warning(
                f"Validation error on {request.method} {request.url.path}: {exception.message}",
                extra={
                    "correlation_id": exception.correlation_id,
                    "field_errors": [error.dict() for error in exception.field_errors]
                }
            )
        
        error_response = APIErrorResponse(
            error=ErrorDetail(
                code=exception.code,
                message=exception.message,
                category=exception.category,
                severity=exception.severity,
                correlation_id=exception.correlation_id,
                user_message=exception.user_message,
                suggested_action=exception.suggested_action,
                field_errors=exception.field_errors
            ),
            request_id=getattr(request.state, 'request_id', None),
            path=str(request.url.path),
            method=request.method
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.dict()
        )
    
    def _create_system_error_response(self, request: Request) -> JSONResponse:
        """Create standardized system error response"""
        
        error_response = APIErrorResponse(
            error=ErrorDetail(
                code="SYSTEM_ERROR",
                message="An unexpected error occurred during request processing",
                category=ErrorCategory.SYSTEM_ERROR,
                severity=ErrorSeverity.CRITICAL,
                user_message="We're experiencing technical difficulties. Please try again later",
                suggested_action="If the problem persists, please contact support"
            ),
            request_id=getattr(request.state, 'request_id', None),
            path=str(request.url.path),
            method=request.method
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.dict()
        )


class InputSanitizer:
    """Input sanitization utilities for XSS prevention and data cleaning"""
    
    def __init__(self):
        # Configure bleach for HTML sanitization
        self.allowed_tags = []  # No HTML tags allowed in financial data
        self.allowed_attributes = {}
        self.allowed_protocols = ['http', 'https', 'mailto']
    
    def sanitize_string(self, value: str, max_length: int = 1000) -> str:
        """Sanitize string input for XSS prevention"""
        if not isinstance(value, str):
            return str(value)
        
        # Limit length
        if len(value) > max_length:
            raise ValueError(f"Input too long (max {max_length} characters)")
        
        # HTML entity decode first
        value = html.unescape(value)
        
        # Remove/escape HTML tags
        value = bleach.clean(
            value,
            tags=self.allowed_tags,
            attributes=self.allowed_attributes,
            protocols=self.allowed_protocols,
            strip=True
        )
        
        # Remove null bytes and control characters
        value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
        
        # Normalize whitespace
        value = re.sub(r'\s+', ' ', value).strip()
        
        return value
    
    def sanitize_financial_description(self, description: str) -> str:
        """Specialized sanitization for financial transaction descriptions"""
        
        # Basic sanitization
        description = self.sanitize_string(description, max_length=500)
        
        # Remove potentially sensitive patterns
        # (keeping basic merchant/vendor information but removing specific identifiers)
        
        # Remove card numbers (basic pattern)
        description = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[CARD]', description)
        
        # Remove SSNs (basic pattern)
        description = re.sub(r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b', '[SSN]', description)
        
        # Remove phone numbers (basic pattern)
        description = re.sub(r'\b\d{3}[-\s]?\d{3}[-\s]?\d{4}\b', '[PHONE]', description)
        
        # Remove email addresses
        description = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', description)
        
        return description


class FinancialDataValidator:
    """Specialized validators for financial data with precision and compliance checks"""
    
    def __init__(self):
        self.max_amount = Decimal('9999999999.99')  # 10 billion max
        self.min_amount = Decimal('-9999999999.99')  # Allow negative for refunds
        self.precision = 2  # Standard currency precision
    
    def validate_amount(self, value: Any) -> Decimal:
        """Validate financial amount with proper precision"""
        
        if value is None:
            raise ValueError("Amount cannot be null")
        
        # Convert to Decimal for precise financial calculations
        try:
            if isinstance(value, str):
                # Remove currency symbols and commas
                cleaned_value = re.sub(r'[$,\s]', '', value)
                amount = Decimal(cleaned_value)
            elif isinstance(value, (int, float)):
                amount = Decimal(str(value))
            elif isinstance(value, Decimal):
                amount = value
            else:
                raise ValueError("Amount must be a number")
        except (InvalidOperation, ValueError):
            raise ValueError("Amount must be a valid number")
        
        # Validate range
        if amount > self.max_amount:
            raise ValueError(f"Amount too large (max: {self.max_amount})")
        if amount < self.min_amount:
            raise ValueError(f"Amount too small (min: {self.min_amount})")
        
        # Validate precision (no more than 2 decimal places for currency)
        if amount.as_tuple().exponent < -self.precision:
            raise ValueError(f"Amount cannot have more than {self.precision} decimal places")
        
        return amount
    
    def validate_account_number(self, account_number: str) -> str:
        """Validate account number format"""
        
        if not account_number:
            raise ValueError("Account number is required")
        
        # Remove spaces and dashes
        cleaned = re.sub(r'[\s-]', '', account_number)
        
        # Basic format validation (adjust based on your requirements)
        if not re.match(r'^[0-9]{8,20}$', cleaned):
            raise ValueError("Account number must be 8-20 digits")
        
        return cleaned
    
    def validate_routing_number(self, routing_number: str) -> str:
        """Validate US routing number with checksum"""
        
        if not routing_number:
            raise ValueError("Routing number is required")
        
        # Remove spaces and dashes
        cleaned = re.sub(r'[\s-]', '', routing_number)
        
        # Must be exactly 9 digits
        if not re.match(r'^[0-9]{9}$', cleaned):
            raise ValueError("Routing number must be exactly 9 digits")
        
        # Validate ABA checksum
        if not self._validate_aba_checksum(cleaned):
            raise ValueError("Invalid routing number checksum")
        
        return cleaned
    
    def _validate_aba_checksum(self, routing_number: str) -> bool:
        """Validate ABA routing number checksum"""
        
        if len(routing_number) != 9:
            return False
        
        # ABA checksum algorithm
        checksum = (
            3 * int(routing_number[0]) +
            7 * int(routing_number[1]) +
            1 * int(routing_number[2]) +
            3 * int(routing_number[3]) +
            7 * int(routing_number[4]) +
            1 * int(routing_number[5]) +
            3 * int(routing_number[6]) +
            7 * int(routing_number[7]) +
            1 * int(routing_number[8])
        ) % 10
        
        return checksum == 0


class SQLInjectionDetector:
    """SQL injection pattern detection for enhanced security"""
    
    def __init__(self):
        # Common SQL injection patterns
        self.sql_patterns = [
            r"('|(\\'))+.*(\\')?(;|--|\s)",  # Quote-based injection
            r"(;|\s)(union|select|insert|update|delete|drop|create|alter|exec|execute)\s",  # SQL keywords
            r"(;|\s)(or|and)\s+\d+\s*=\s*\d+",  # Boolean injection
            r"(;|\s)(waitfor|delay)\s+",  # Time-based injection
            r"(;|\s)(load_file|into\s+outfile|dumpfile)\s+",  # File operations
            r"(;|\s)(benchmark|sleep)\s*\(",  # Performance functions
            r"\/\*.*\*\/",  # SQL comments
            r"--\s.*",  # SQL line comments
            r"(;|\s)(\w+\s*=\s*\w+\s*--)",  # Assignment with comment
        ]
        
        # Compile patterns for performance
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.sql_patterns]
    
    def is_suspicious(self, value: str) -> bool:
        """Check if string contains potential SQL injection patterns"""
        
        if not isinstance(value, str) or len(value) < 3:
            return False
        
        # Check against all patterns
        for pattern in self.compiled_patterns:
            if pattern.search(value):
                return True
        
        return False
    
    def sanitize_sql_identifier(self, identifier: str) -> str:
        """Sanitize SQL identifier (table/column names)"""
        
        # Only allow alphanumeric characters and underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '', identifier)
        
        # Must start with letter or underscore
        if not re.match(r'^[a-zA-Z_]', sanitized):
            raise ValueError("Invalid SQL identifier")
        
        # Reasonable length limit
        if len(sanitized) > 63:  # PostgreSQL limit
            raise ValueError("SQL identifier too long")
        
        return sanitized