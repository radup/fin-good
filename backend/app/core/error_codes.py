"""
Comprehensive Error Code Catalog for FinGood Financial Platform

This module defines all standardized error codes used throughout the platform
with descriptions, HTTP status codes, and user-friendly messages.
"""

from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum
from app.schemas.error import ErrorCategory, ErrorSeverity


@dataclass
class ErrorCodeDefinition:
    """Definition of an error code with all relevant information"""
    code: str
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    http_status: int
    user_message: str
    suggested_action: str
    description: str
    resolution_steps: Optional[str] = None
    related_codes: Optional[list] = None


class FinGoodErrorCodes:
    """Centralized catalog of all FinGood error codes"""
    
    # Authentication Errors (AUTH_xxx)
    AUTHENTICATION_FAILED = ErrorCodeDefinition(
        code="AUTH_001",
        message="Authentication failed",
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.MEDIUM,
        http_status=401,
        user_message="Invalid email or password",
        suggested_action="Please check your credentials and try again",
        description="User provided invalid login credentials",
        resolution_steps="1. Verify email address is correct\n2. Check password spelling\n3. Use password reset if needed"
    )
    
    INVALID_TOKEN = ErrorCodeDefinition(
        code="AUTH_002",
        message="Invalid or expired authentication token",
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.MEDIUM,
        http_status=401,
        user_message="Your session has expired. Please log in again",
        suggested_action="Please log in to continue",
        description="JWT token is invalid, expired, or malformed",
        resolution_steps="1. Log out and log back in\n2. Clear browser cache if issues persist"
    )
    
    TOKEN_EXPIRED = ErrorCodeDefinition(
        code="AUTH_003",
        message="Authentication token has expired",
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.LOW,
        http_status=401,
        user_message="Your session has expired",
        suggested_action="Please log in again to continue",
        description="JWT token has passed its expiration time",
        resolution_steps="1. Log in again to get a new token\n2. Enable 'Remember Me' for longer sessions"
    )
    
    ACCOUNT_LOCKED = ErrorCodeDefinition(
        code="AUTH_004",
        message="Account is temporarily locked",
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.HIGH,
        http_status=423,
        user_message="Your account has been temporarily locked for security",
        suggested_action="Please contact support or wait for the lockout period to expire",
        description="Account locked due to too many failed login attempts",
        resolution_steps="1. Wait for lockout period to expire\n2. Contact support for immediate assistance\n3. Use account recovery options"
    )
    
    # Authorization Errors (AUTHZ_xxx)
    ACCESS_DENIED = ErrorCodeDefinition(
        code="AUTHZ_001",
        message="Access denied",
        category=ErrorCategory.AUTHORIZATION,
        severity=ErrorSeverity.HIGH,
        http_status=403,
        user_message="You don't have permission to perform this action",
        suggested_action="Contact your administrator for access",
        description="User lacks required permissions for the requested operation",
        resolution_steps="1. Contact system administrator\n2. Request appropriate role assignment\n3. Verify account status"
    )
    
    INSUFFICIENT_PERMISSIONS = ErrorCodeDefinition(
        code="AUTHZ_002",
        message="Insufficient permissions for this operation",
        category=ErrorCategory.AUTHORIZATION,
        severity=ErrorSeverity.MEDIUM,
        http_status=403,
        user_message="You need additional permissions to perform this action",
        suggested_action="Contact your administrator to request access",
        description="User's role lacks specific permission for this operation",
        resolution_steps="1. Contact administrator\n2. Request specific permission\n3. Verify business justification for access"
    )
    
    # Validation Errors (VAL_xxx)
    VALIDATION_ERROR = ErrorCodeDefinition(
        code="VAL_001",
        message="Request validation failed",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.MEDIUM,
        http_status=422,
        user_message="Please correct the highlighted fields and try again",
        suggested_action="Review the field errors and provide valid data",
        description="One or more request fields failed validation",
        resolution_steps="1. Check required fields\n2. Verify data formats\n3. Ensure values are within allowed ranges"
    )
    
    INVALID_EMAIL_FORMAT = ErrorCodeDefinition(
        code="VAL_002",
        message="Invalid email format",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.LOW,
        http_status=422,
        user_message="Please enter a valid email address",
        suggested_action="Use the format: user@example.com",
        description="Email address doesn't match required format",
        resolution_steps="1. Check for typos\n2. Ensure @ symbol is present\n3. Verify domain extension"
    )
    
    INVALID_AMOUNT = ErrorCodeDefinition(
        code="VAL_003",
        message="Invalid amount value",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.MEDIUM,
        http_status=422,
        user_message="Please enter a valid amount",
        suggested_action="Amount must be greater than 0 and properly formatted",
        description="Financial amount is negative, zero, or improperly formatted",
        resolution_steps="1. Use positive numbers only\n2. Use proper decimal format\n3. Check for currency requirements"
    )
    
    # Business Logic Errors (BIZ_xxx)
    DUPLICATE_TRANSACTION = ErrorCodeDefinition(
        code="BIZ_001",
        message="Duplicate transaction detected",
        category=ErrorCategory.BUSINESS_LOGIC,
        severity=ErrorSeverity.MEDIUM,
        http_status=409,
        user_message="This transaction appears to be a duplicate",
        suggested_action="Please check your transaction history",
        description="Transaction with identical details already exists",
        resolution_steps="1. Check recent transactions\n2. Verify transaction details\n3. Contact support if this is not a duplicate"
    )
    
    INVALID_TRANSACTION_STATE = ErrorCodeDefinition(
        code="BIZ_002",
        message="Invalid transaction state for this operation",
        category=ErrorCategory.BUSINESS_LOGIC,
        severity=ErrorSeverity.MEDIUM,
        http_status=400,
        user_message="This operation cannot be performed on the current transaction",
        suggested_action="Check the transaction status and try again",
        description="Transaction is in a state that doesn't allow the requested operation",
        resolution_steps="1. Check transaction status\n2. Verify operation is allowed\n3. Contact support for state clarification"
    )
    
    # Resource Not Found Errors (RNF_xxx)
    USER_NOT_FOUND = ErrorCodeDefinition(
        code="RNF_001",
        message="User not found",
        category=ErrorCategory.RESOURCE_NOT_FOUND,
        severity=ErrorSeverity.LOW,
        http_status=404,
        user_message="The requested user could not be found",
        suggested_action="Please check the user ID and try again",
        description="User with specified ID does not exist",
        resolution_steps="1. Verify user ID\n2. Check if user was deleted\n3. Search by different criteria"
    )
    
    TRANSACTION_NOT_FOUND = ErrorCodeDefinition(
        code="RNF_002",
        message="Transaction not found",
        category=ErrorCategory.RESOURCE_NOT_FOUND,
        severity=ErrorSeverity.LOW,
        http_status=404,
        user_message="The requested transaction could not be found",
        suggested_action="Please check the transaction ID and try again",
        description="Transaction with specified ID does not exist",
        resolution_steps="1. Verify transaction ID\n2. Check date ranges\n3. Search in different accounts"
    )
    
    ACCOUNT_NOT_FOUND = ErrorCodeDefinition(
        code="RNF_003",
        message="Account not found",
        category=ErrorCategory.RESOURCE_NOT_FOUND,
        severity=ErrorSeverity.MEDIUM,
        http_status=404,
        user_message="The requested account could not be found",
        suggested_action="Please check the account ID and try again",
        description="Account with specified ID does not exist",
        resolution_steps="1. Verify account number\n2. Check account status\n3. Contact support for account verification"
    )
    
    # Rate Limiting Errors (RATE_xxx)
    RATE_LIMIT_EXCEEDED = ErrorCodeDefinition(
        code="RATE_001",
        message="Rate limit exceeded",
        category=ErrorCategory.RATE_LIMITING,
        severity=ErrorSeverity.MEDIUM,
        http_status=429,
        user_message="You've made too many requests. Please wait before trying again",
        suggested_action="Wait 60 seconds before making another request",
        description="API rate limit has been exceeded",
        resolution_steps="1. Wait for rate limit reset\n2. Implement request throttling\n3. Contact support for higher limits if needed"
    )
    
    # Financial Compliance Errors (FIN_xxx)
    INSUFFICIENT_FUNDS = ErrorCodeDefinition(
        code="FIN_001",
        message="Insufficient funds for transaction",
        category=ErrorCategory.FINANCIAL_COMPLIANCE,
        severity=ErrorSeverity.HIGH,
        http_status=400,
        user_message="You don't have enough funds for this transaction",
        suggested_action="Please check your balance or reduce the transaction amount",
        description="Account balance is insufficient for the requested transaction",
        resolution_steps="1. Check account balance\n2. Transfer funds if needed\n3. Reduce transaction amount"
    )
    
    TRANSACTION_LIMIT_EXCEEDED = ErrorCodeDefinition(
        code="FIN_002",
        message="Transaction limit exceeded",
        category=ErrorCategory.FINANCIAL_COMPLIANCE,
        severity=ErrorSeverity.HIGH,
        http_status=400,
        user_message="This transaction exceeds your limit",
        suggested_action="Contact support to increase your limits or try a smaller amount",
        description="Transaction amount exceeds account or regulatory limits",
        resolution_steps="1. Check transaction limits\n2. Contact support for limit increase\n3. Split transaction into smaller amounts"
    )
    
    DAILY_LIMIT_EXCEEDED = ErrorCodeDefinition(
        code="FIN_003",
        message="Daily transaction limit exceeded",
        category=ErrorCategory.FINANCIAL_COMPLIANCE,
        severity=ErrorSeverity.HIGH,
        http_status=400,
        user_message="You've reached your daily transaction limit",
        suggested_action="Try again tomorrow or contact support for higher limits",
        description="Daily transaction limit has been reached",
        resolution_steps="1. Wait until next day\n2. Contact support for limit increase\n3. Prioritize essential transactions"
    )
    
    ACCOUNT_FROZEN = ErrorCodeDefinition(
        code="FIN_004",
        message="Account is frozen",
        category=ErrorCategory.FINANCIAL_COMPLIANCE,
        severity=ErrorSeverity.CRITICAL,
        http_status=423,
        user_message="Your account has been temporarily frozen",
        suggested_action="Please contact support immediately",
        description="Account has been frozen due to suspicious activity or compliance issues",
        resolution_steps="1. Contact support immediately\n2. Provide requested documentation\n3. Follow compliance procedures"
    )
    
    # External Service Errors (EXT_xxx)
    EXTERNAL_SERVICE_UNAVAILABLE = ErrorCodeDefinition(
        code="EXT_001",
        message="External service temporarily unavailable",
        category=ErrorCategory.EXTERNAL_SERVICE,
        severity=ErrorSeverity.HIGH,
        http_status=502,
        user_message="We're experiencing issues with an external service. Please try again later",
        suggested_action="If the problem persists, please contact support",
        description="Required external service is not responding",
        resolution_steps="1. Wait and retry\n2. Check service status page\n3. Contact support if issue persists"
    )
    
    BANK_API_ERROR = ErrorCodeDefinition(
        code="EXT_002",
        message="Bank API error",
        category=ErrorCategory.EXTERNAL_SERVICE,
        severity=ErrorSeverity.HIGH,
        http_status=502,
        user_message="We're having trouble connecting to your bank. Please try again later",
        suggested_action="If the problem continues, please contact support",
        description="Bank API returned an error or is unavailable",
        resolution_steps="1. Retry the operation\n2. Check bank service status\n3. Contact support with details"
    )
    
    # System Errors (SYS_xxx)
    INTERNAL_SERVER_ERROR = ErrorCodeDefinition(
        code="SYS_001",
        message="Internal server error",
        category=ErrorCategory.SYSTEM_ERROR,
        severity=ErrorSeverity.CRITICAL,
        http_status=500,
        user_message="We're experiencing technical difficulties. Please try again later",
        suggested_action="If the problem persists, please contact support",
        description="Unexpected server error occurred",
        resolution_steps="1. Try again in a few minutes\n2. Clear browser cache\n3. Contact support with error details"
    )
    
    DATABASE_CONNECTION_ERROR = ErrorCodeDefinition(
        code="SYS_002",
        message="Database connection error",
        category=ErrorCategory.SYSTEM_ERROR,
        severity=ErrorSeverity.CRITICAL,
        http_status=503,
        user_message="We're experiencing database issues. Please try again later",
        suggested_action="Please try again in a few minutes",
        description="Unable to connect to the database",
        resolution_steps="1. Wait for service restoration\n2. Check system status page\n3. Contact support if extended outage"
    )
    
    # Data Integrity Errors (DATA_xxx)
    DATA_INTEGRITY_ERROR = ErrorCodeDefinition(
        code="DATA_001",
        message="Data integrity constraint violation",
        category=ErrorCategory.DATA_INTEGRITY,
        severity=ErrorSeverity.HIGH,
        http_status=409,
        user_message="There was a conflict with existing data",
        suggested_action="Please check your data and try again",
        description="Operation would violate data integrity constraints",
        resolution_steps="1. Check for duplicate data\n2. Verify referential integrity\n3. Contact support for data issues"
    )
    
    CONCURRENT_MODIFICATION = ErrorCodeDefinition(
        code="DATA_002",
        message="Concurrent modification detected",
        category=ErrorCategory.DATA_INTEGRITY,
        severity=ErrorSeverity.MEDIUM,
        http_status=409,
        user_message="The data was modified by another user. Please refresh and try again",
        suggested_action="Refresh the page and retry your operation",
        description="Data was modified by another process during the operation",
        resolution_steps="1. Refresh the data\n2. Merge changes if needed\n3. Retry the operation"
    )

    @classmethod
    def get_all_codes(cls) -> Dict[str, ErrorCodeDefinition]:
        """Get all error code definitions as a dictionary"""
        return {
            attr_name: attr_value
            for attr_name, attr_value in cls.__dict__.items()
            if isinstance(attr_value, ErrorCodeDefinition)
        }
    
    @classmethod
    def get_code(cls, code: str) -> Optional[ErrorCodeDefinition]:
        """Get a specific error code definition"""
        all_codes = cls.get_all_codes()
        for definition in all_codes.values():
            if definition.code == code:
                return definition
        return None
    
    @classmethod
    def get_codes_by_category(cls, category: ErrorCategory) -> Dict[str, ErrorCodeDefinition]:
        """Get all error codes for a specific category"""
        all_codes = cls.get_all_codes()
        return {
            name: definition
            for name, definition in all_codes.items()
            if definition.category == category
        }
    
    @classmethod
    def get_codes_by_severity(cls, severity: ErrorSeverity) -> Dict[str, ErrorCodeDefinition]:
        """Get all error codes for a specific severity level"""
        all_codes = cls.get_all_codes()
        return {
            name: definition
            for name, definition in all_codes.items()
            if definition.severity == severity
        }