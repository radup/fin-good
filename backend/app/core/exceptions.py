"""
Custom Exception Classes and Error Handling for FinGood Financial Platform

This module provides custom exceptions that map to standardized error responses
with appropriate security considerations for financial applications.
"""

from fastapi import HTTPException, status
from typing import Optional, Dict, Any, List
from app.schemas.error import ErrorCategory, ErrorSeverity, FieldError
import uuid


class FinGoodException(Exception):
    """Base exception class for FinGood platform"""
    
    def __init__(
        self,
        message: str,
        code: str,
        category: ErrorCategory,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        user_message: Optional[str] = None,
        suggested_action: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        field_errors: Optional[List[FieldError]] = None,
        transaction_id: Optional[str] = None,
        account_id: Optional[str] = None,
        retry_after: Optional[int] = None,
        external_service: Optional[str] = None,
        external_error_id: Optional[str] = None
    ):
        self.message = message
        self.code = code
        self.category = category
        self.severity = severity
        self.user_message = user_message or message
        self.suggested_action = suggested_action
        self.context = context or {}
        self.field_errors = field_errors or []
        self.transaction_id = transaction_id
        self.account_id = account_id
        self.retry_after = retry_after
        self.external_service = external_service
        self.external_error_id = external_error_id
        self.correlation_id = str(uuid.uuid4())
        super().__init__(self.message)


class ValidationException(FinGoodException):
    """Exception for validation errors"""
    
    def __init__(
        self,
        message: str = "Validation failed",
        field_errors: Optional[List[FieldError]] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            user_message="Please correct the highlighted fields and try again",
            suggested_action="Review the field errors and provide valid data",
            field_errors=field_errors,
            **kwargs
        )


class AuthenticationException(FinGoodException):
    """Exception for authentication failures"""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        code: str = "AUTHENTICATION_FAILED",
        **kwargs
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.MEDIUM,
            user_message="Please check your credentials and try again",
            suggested_action="Verify your email and password are correct",
            **kwargs
        )


class AuthorizationException(FinGoodException):
    """Exception for authorization failures"""
    
    def __init__(
        self,
        message: str = "Access denied",
        code: str = "ACCESS_DENIED",
        **kwargs
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.HIGH,
            user_message="You don't have permission to perform this action",
            suggested_action="Contact your administrator for access",
            **kwargs
        )


class ResourceNotFoundException(FinGoodException):
    """Exception for resource not found errors"""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        message: Optional[str] = None,
        **kwargs
    ):
        message = message or f"{resource_type} not found"
        super().__init__(
            message=message,
            code="RESOURCE_NOT_FOUND",
            category=ErrorCategory.RESOURCE_NOT_FOUND,
            severity=ErrorSeverity.LOW,
            user_message=f"The requested {resource_type.lower()} could not be found",
            suggested_action="Please check the ID and try again",
            context={"resource_type": resource_type, "resource_id": resource_id},
            **kwargs
        )


class BusinessLogicException(FinGoodException):
    """Exception for business logic violations"""
    
    def __init__(
        self,
        message: str,
        code: str,
        user_message: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.BUSINESS_LOGIC,
            severity=ErrorSeverity.MEDIUM,
            user_message=user_message or message,
            **kwargs
        )


class RateLimitException(FinGoodException):
    """Exception for rate limiting"""
    
    def __init__(
        self,
        retry_after: int = 60,
        message: str = "Rate limit exceeded",
        **kwargs
    ):
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            category=ErrorCategory.RATE_LIMITING,
            severity=ErrorSeverity.MEDIUM,
            user_message="You've made too many requests. Please wait before trying again",
            suggested_action=f"Wait {retry_after} seconds before making another request",
            retry_after=retry_after,
            **kwargs
        )


class ExternalServiceException(FinGoodException):
    """Exception for external service failures"""
    
    def __init__(
        self,
        service_name: str,
        message: str = "External service error",
        external_error_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code="EXTERNAL_SERVICE_ERROR",
            category=ErrorCategory.EXTERNAL_SERVICE,
            severity=ErrorSeverity.HIGH,
            user_message="We're experiencing issues with an external service. Please try again later",
            suggested_action="If the problem persists, please contact support",
            external_service=service_name,
            external_error_id=external_error_id,
            **kwargs
        )


class SystemException(FinGoodException):
    """Exception for system-level errors"""
    
    def __init__(
        self,
        message: str = "An unexpected error occurred",
        code: str = "SYSTEM_ERROR",
        **kwargs
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.SYSTEM_ERROR,
            severity=ErrorSeverity.CRITICAL,
            user_message="We're experiencing technical difficulties. Please try again later",
            suggested_action="If the problem persists, please contact support",
            **kwargs
        )


class FinancialComplianceException(FinGoodException):
    """Exception for financial compliance violations"""
    
    def __init__(
        self,
        message: str,
        code: str,
        compliance_context: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.FINANCIAL_COMPLIANCE,
            severity=ErrorSeverity.HIGH,
            context=compliance_context,
            **kwargs
        )


class DataIntegrityException(FinGoodException):
    """Exception for data integrity violations"""
    
    def __init__(
        self,
        message: str = "Data integrity violation",
        code: str = "DATA_INTEGRITY_ERROR",
        **kwargs
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.DATA_INTEGRITY,
            severity=ErrorSeverity.HIGH,
            user_message="There was a problem processing your request",
            suggested_action="Please try again or contact support if the issue persists",
            **kwargs
        )


# Specific financial platform exceptions

class InsufficientFundsException(FinancialComplianceException):
    """Exception for insufficient funds"""
    
    def __init__(
        self,
        available_balance: float,
        requested_amount: float,
        account_id: str,
        **kwargs
    ):
        super().__init__(
            message="Insufficient funds for transaction",
            code="INSUFFICIENT_FUNDS",
            user_message="You don't have enough funds for this transaction",
            suggested_action="Please check your balance or reduce the transaction amount",
            compliance_context={
                "available_balance": available_balance,
                "requested_amount": requested_amount
            },
            account_id=account_id,
            **kwargs
        )


class TransactionLimitExceededException(FinancialComplianceException):
    """Exception for transaction limit violations"""
    
    def __init__(
        self,
        limit_type: str,
        limit_amount: float,
        current_usage: float,
        attempted_amount: float,
        **kwargs
    ):
        super().__init__(
            message=f"{limit_type} limit exceeded",
            code="TRANSACTION_LIMIT_EXCEEDED",
            user_message=f"This transaction exceeds your {limit_type.lower()} limit",
            suggested_action="Contact support to increase your limits or try a smaller amount",
            compliance_context={
                "limit_type": limit_type,
                "limit_amount": limit_amount,
                "current_usage": current_usage,
                "attempted_amount": attempted_amount
            },
            **kwargs
        )


class InvalidAccountException(ValidationException):
    """Exception for invalid account operations"""
    
    def __init__(
        self,
        account_id: str,
        reason: str,
        **kwargs
    ):
        super().__init__(
            message=f"Invalid account operation: {reason}",
            field_errors=[FieldError(
                field="account_id",
                message=reason,
                code="INVALID_ACCOUNT",
                value=account_id
            )],
            **kwargs
        )


class DuplicateTransactionException(BusinessLogicException):
    """Exception for duplicate transaction attempts"""
    
    def __init__(
        self,
        original_transaction_id: str,
        **kwargs
    ):
        super().__init__(
            message="Duplicate transaction detected",
            code="DUPLICATE_TRANSACTION",
            user_message="This transaction appears to be a duplicate",
            suggested_action="Please check your transaction history",
            context={"original_transaction_id": original_transaction_id},
            **kwargs
        )


class FinancialAnalyticsError(FinGoodException):
    """Exception for financial analytics processing errors"""
    
    def __init__(
        self,
        message: str,
        code: str = "ANALYTICS_ERROR",
        analytics_context: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.BUSINESS_LOGIC,
            severity=ErrorSeverity.MEDIUM,
            user_message="Unable to generate financial analytics",
            suggested_action="Please try again or contact support if the issue persists",
            context=analytics_context,
            **kwargs
        )