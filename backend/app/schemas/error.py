"""
Standardized API Error Response Schemas for FinGood Financial Platform

This module provides consistent error response formats that prioritize:
- Security (no sensitive data leakage)
- User experience (clear, actionable messages)
- Developer experience (debugging information)
- Compliance (audit trail support)
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum
import uuid


class ErrorCategory(str, Enum):
    """Error categories for classification and handling"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    RESOURCE_NOT_FOUND = "resource_not_found"
    RATE_LIMITING = "rate_limiting"
    EXTERNAL_SERVICE = "external_service"
    SYSTEM_ERROR = "system_error"
    FINANCIAL_COMPLIANCE = "financial_compliance"
    DATA_INTEGRITY = "data_integrity"


class ErrorSeverity(str, Enum):
    """Error severity levels for monitoring and alerting"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FieldError(BaseModel):
    """Individual field validation error"""
    field: str = Field(..., description="The field name that caused the error")
    message: str = Field(..., description="Human-readable error message for the field")
    code: str = Field(..., description="Machine-readable error code for the field")
    value: Optional[Union[str, int, float, bool]] = Field(
        None, 
        description="The invalid value that was provided (sanitized for security)"
    )


class ErrorDetail(BaseModel):
    """Detailed error information for debugging"""
    code: str = Field(..., description="Unique error code for this specific error type")
    message: str = Field(..., description="Human-readable error message")
    category: ErrorCategory = Field(..., description="Error category for classification")
    severity: ErrorSeverity = Field(ErrorSeverity.MEDIUM, description="Error severity level")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the error occurred")
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID for tracking this error")
    
    # User-facing information
    user_message: Optional[str] = Field(
        None, 
        description="Simplified message safe to display to end users"
    )
    suggested_action: Optional[str] = Field(
        None, 
        description="Recommended action for the user to resolve the issue"
    )
    
    # Developer information (only included in development/debugging)
    developer_message: Optional[str] = Field(
        None, 
        description="Technical details for developers (not shown in production)"
    )
    
    # Field-specific errors for validation failures
    field_errors: Optional[List[FieldError]] = Field(
        None, 
        description="Specific field validation errors"
    )
    
    # Additional context
    context: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional context data (sanitized for security)"
    )
    
    # Financial platform specific fields
    transaction_id: Optional[str] = Field(
        None, 
        description="Related transaction ID if applicable"
    )
    account_id: Optional[str] = Field(
        None, 
        description="Related account ID if applicable (obfuscated)"
    )
    
    # Rate limiting information
    retry_after: Optional[int] = Field(
        None, 
        description="Seconds to wait before retrying (for rate limiting errors)"
    )
    
    # External service information
    external_service: Optional[str] = Field(
        None, 
        description="Name of external service that caused the error"
    )
    external_error_id: Optional[str] = Field(
        None, 
        description="External service error reference ID"
    )


class APIErrorResponse(BaseModel):
    """Standardized API error response format"""
    success: bool = Field(False, description="Always false for error responses")
    error: ErrorDetail = Field(..., description="Detailed error information")
    
    # API versioning
    api_version: str = Field("v1", description="API version that generated this error")
    
    # Request information
    request_id: Optional[str] = Field(
        None, 
        description="Unique request identifier for debugging"
    )
    path: Optional[str] = Field(
        None, 
        description="API endpoint path where error occurred"
    )
    method: Optional[str] = Field(
        None, 
        description="HTTP method used"
    )
    
    # Documentation links
    documentation_url: Optional[str] = Field(
        None, 
        description="Link to relevant documentation"
    )
    support_url: Optional[str] = Field(
        None, 
        description="Link to support resources"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "The request contains invalid data",
                        "category": "validation",
                        "severity": "medium",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "correlation_id": "123e4567-e89b-12d3-a456-426614174000",
                        "user_message": "Please check your input and try again",
                        "suggested_action": "Verify all required fields are filled correctly",
                        "field_errors": [
                            {
                                "field": "amount",
                                "message": "Amount must be greater than 0",
                                "code": "INVALID_AMOUNT",
                                "value": -100
                            }
                        ]
                    },
                    "api_version": "v1",
                    "request_id": "req_123456789",
                    "path": "/api/v1/transactions",
                    "method": "POST",
                    "documentation_url": "https://docs.fingood.com/api/errors#VALIDATION_ERROR"
                }
            ]
        }


class ValidationErrorResponse(APIErrorResponse):
    """Specific error response for validation failures"""
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "success": False,
                    "error": {
                        "code": "FIELD_VALIDATION_ERROR",
                        "message": "One or more fields failed validation",
                        "category": "validation",
                        "severity": "medium",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "correlation_id": "123e4567-e89b-12d3-a456-426614174000",
                        "user_message": "Please correct the highlighted fields",
                        "suggested_action": "Review the field errors and provide valid data",
                        "field_errors": [
                            {
                                "field": "email",
                                "message": "Invalid email format",
                                "code": "INVALID_EMAIL_FORMAT",
                                "value": "invalid-email"
                            },
                            {
                                "field": "amount",
                                "message": "Amount must be between 0.01 and 1,000,000",
                                "code": "AMOUNT_OUT_OF_RANGE",
                                "value": 0
                            }
                        ]
                    },
                    "api_version": "v1",
                    "documentation_url": "https://docs.fingood.com/api/validation-errors"
                }
            ]
        }


class AuthenticationErrorResponse(APIErrorResponse):
    """Specific error response for authentication failures"""
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": "Authentication failed",
                        "category": "authentication",
                        "severity": "medium",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "correlation_id": "123e4567-e89b-12d3-a456-426614174000",
                        "user_message": "Invalid email or password",
                        "suggested_action": "Please check your credentials and try again"
                    },
                    "api_version": "v1",
                    "documentation_url": "https://docs.fingood.com/api/authentication"
                }
            ]
        }


class RateLimitErrorResponse(APIErrorResponse):
    """Specific error response for rate limiting"""
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests",
                        "category": "rate_limiting",
                        "severity": "medium",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "correlation_id": "123e4567-e89b-12d3-a456-426614174000",
                        "user_message": "You've made too many requests. Please wait before trying again",
                        "suggested_action": "Wait 60 seconds before making another request",
                        "retry_after": 60
                    },
                    "api_version": "v1",
                    "documentation_url": "https://docs.fingood.com/api/rate-limits"
                }
            ]
        }


class FinancialComplianceErrorResponse(APIErrorResponse):
    """Specific error response for financial compliance violations"""
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "success": False,
                    "error": {
                        "code": "TRANSACTION_LIMIT_EXCEEDED",
                        "message": "Transaction exceeds daily limit",
                        "category": "financial_compliance",
                        "severity": "high",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "correlation_id": "123e4567-e89b-12d3-a456-426614174000",
                        "user_message": "This transaction exceeds your daily limit",
                        "suggested_action": "Contact support to increase your limits or try a smaller amount",
                        "context": {
                            "daily_limit": 10000,
                            "current_usage": 9500,
                            "attempted_amount": 1000
                        }
                    },
                    "api_version": "v1",
                    "support_url": "https://support.fingood.com/limits"
                }
            ]
        }