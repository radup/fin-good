"""
Financial Transaction Security and Error Handling

This module provides specialized error handling and security features
for financial transactions, ensuring compliance with financial regulations
and preventing data leakage.
"""

import logging
import hashlib
import re
from typing import Any, Dict, Optional, List, Tuple
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta
from dataclasses import dataclass

from fastapi import Request

from app.core.exceptions import (
    FinancialComplianceException,
    InsufficientFundsException,
    TransactionLimitExceededException,
    BusinessLogicException,
    ValidationException,
    DataIntegrityException
)
from app.schemas.error import ErrorSeverity, FieldError
from app.core.audit_logger import security_audit_logger

logger = logging.getLogger(__name__)


@dataclass
class TransactionContext:
    """Context information for financial transactions"""
    user_id: Optional[str]
    account_id: Optional[str]
    transaction_type: str
    amount: Decimal
    currency: str
    timestamp: datetime
    request_id: Optional[str]
    correlation_id: Optional[str]
    client_ip: Optional[str]
    source_system: str = "web_api"


class FinancialDataSanitizer:
    """
    Sanitizes financial data in error messages and logs to prevent
    sensitive information leakage while maintaining audit trails.
    """
    
    # Patterns for sensitive financial data
    ACCOUNT_NUMBER_PATTERN = re.compile(r'\b\d{4,20}\b')
    CARD_NUMBER_PATTERN = re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b')
    SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    ROUTING_NUMBER_PATTERN = re.compile(r'\b\d{9}\b')
    
    @classmethod
    def sanitize_amount(cls, amount: Any) -> str:
        """Sanitize monetary amounts for logging"""
        if isinstance(amount, (int, float, Decimal)):
            # For security, only show rounded amounts in logs
            if amount > 10000:
                return "[LARGE_AMOUNT]"
            elif amount > 1000:
                return "[MEDIUM_AMOUNT]"
            else:
                return "[SMALL_AMOUNT]"
        return str(amount)
    
    @classmethod
    def sanitize_account_id(cls, account_id: str) -> str:
        """Sanitize account IDs for logging"""
        if not account_id:
            return ""
        
        # Show only first 2 and last 2 characters
        if len(account_id) > 6:
            return f"{account_id[:2]}***{account_id[-2:]}"
        else:
            return "***"
    
    @classmethod
    def sanitize_error_message(cls, message: str) -> str:
        """Sanitize error messages to remove sensitive data"""
        # Replace account numbers
        message = cls.ACCOUNT_NUMBER_PATTERN.sub('[ACCOUNT]', message)
        
        # Replace card numbers
        message = cls.CARD_NUMBER_PATTERN.sub('[CARD]', message)
        
        # Replace SSNs
        message = cls.SSN_PATTERN.sub('[SSN]', message)
        
        # Replace routing numbers
        message = cls.ROUTING_NUMBER_PATTERN.sub('[ROUTING]', message)
        
        return message
    
    @classmethod
    def create_audit_hash(cls, data: str) -> str:
        """Create a hash for audit purposes without exposing data"""
        return hashlib.sha256(data.encode()).hexdigest()[:16]


class TransactionSecurityValidator:
    """
    Validates financial transactions for security and compliance issues
    """
    
    def __init__(self):
        self.sanitizer = FinancialDataSanitizer()
    
    def validate_transaction_amount(
        self, 
        amount: Any, 
        currency: str = "USD",
        context: Optional[TransactionContext] = None
    ) -> Decimal:
        """
        Validate transaction amount with security checks
        
        Args:
            amount: The transaction amount to validate
            currency: Currency code
            context: Transaction context for auditing
            
        Returns:
            Validated Decimal amount
            
        Raises:
            ValidationException: If amount is invalid
            FinancialComplianceException: If amount violates limits
        """
        try:
            # Convert to Decimal for precise financial calculations
            if isinstance(amount, str):
                # Remove currency symbols and whitespace
                clean_amount = re.sub(r'[^\d.-]', '', amount)
                decimal_amount = Decimal(clean_amount)
            else:
                decimal_amount = Decimal(str(amount))
            
            # Validate amount is positive
            if decimal_amount <= 0:
                raise ValidationException(
                    message="Transaction amount must be positive",
                    field_errors=[FieldError(
                        field="amount",
                        message="Amount must be greater than 0",
                        code="INVALID_AMOUNT",
                        value=self.sanitizer.sanitize_amount(amount)
                    )]
                )
            
            # Check for unreasonably large amounts (potential fraud)
            max_single_transaction = Decimal('1000000')  # $1M limit
            if decimal_amount > max_single_transaction:
                # Log suspicious large transaction attempt
                if context:
                    security_audit_logger.log_suspicious_activity(
                        description="Extremely large transaction attempt",
                        user_id=context.user_id,
                        details={
                            "amount_category": self.sanitizer.sanitize_amount(decimal_amount),
                            "transaction_type": context.transaction_type,
                            "request_id": context.request_id
                        }
                    )
                
                raise FinancialComplianceException(
                    message="Transaction amount exceeds maximum allowed",
                    code="AMOUNT_TOO_LARGE",
                    user_message="This transaction amount is too large",
                    suggested_action="Please contact support for large transactions",
                    compliance_context={
                        "max_amount": str(max_single_transaction),
                        "attempted_amount": "[REDACTED]",
                        "amount_hash": self.sanitizer.create_audit_hash(str(decimal_amount))
                    }
                )
            
            # Check for suspicious precision (potential manipulation)
            if decimal_amount.as_tuple().exponent < -2:  # More than 2 decimal places
                logger.warning("Transaction with unusual precision detected", extra={
                    "amount_hash": self.sanitizer.create_audit_hash(str(decimal_amount)),
                    "user_id": context.user_id if context else None,
                    "precision": abs(decimal_amount.as_tuple().exponent)
                })
            
            return decimal_amount
            
        except (InvalidOperation, ValueError) as e:
            raise ValidationException(
                message="Invalid amount format",
                field_errors=[FieldError(
                    field="amount",
                    message="Amount must be a valid number",
                    code="INVALID_AMOUNT_FORMAT",
                    value=str(amount)[:20]  # Limit length for security
                )]
            )
    
    def validate_account_access(
        self,
        user_id: str,
        account_id: str,
        operation: str,
        context: Optional[TransactionContext] = None
    ) -> None:
        """
        Validate user has permission to access account
        
        Args:
            user_id: User attempting the operation
            account_id: Account being accessed
            operation: Type of operation (read, write, transfer)
            context: Transaction context
            
        Raises:
            AuthorizationException: If access is denied
        """
        # This would typically check against a user-account mapping
        # For now, we'll implement basic validation
        
        sanitized_account = self.sanitizer.sanitize_account_id(account_id)
        
        # Log account access attempt
        security_audit_logger.log_access_denied(
            resource=f"account:{sanitized_account}",
            user_id=user_id,
            reason=f"attempted_{operation}_operation"
        )
        
        # Placeholder for actual authorization logic
        # In production, this would check user permissions in database
        logger.info(f"Account access validation", extra={
            "user_id": user_id,
            "account_id": sanitized_account,
            "operation": operation,
            "request_id": context.request_id if context else None
        })
    
    def check_daily_limits(
        self,
        user_id: str,
        amount: Decimal,
        transaction_type: str,
        context: Optional[TransactionContext] = None
    ) -> None:
        """
        Check if transaction violates daily limits
        
        Args:
            user_id: User making the transaction
            amount: Transaction amount
            transaction_type: Type of transaction
            context: Transaction context
            
        Raises:
            TransactionLimitExceededException: If limits are exceeded
        """
        # Mock daily limits (would come from database in production)
        daily_limits = {
            "transfer": Decimal('10000'),
            "withdrawal": Decimal('5000'),
            "payment": Decimal('15000')
        }
        
        limit = daily_limits.get(transaction_type, Decimal('1000'))
        
        # Mock current usage (would query database in production)
        current_usage = Decimal('2500')  # Placeholder
        
        if current_usage + amount > limit:
            # Log limit violation attempt
            if context:
                security_audit_logger.log_suspicious_activity(
                    description="Daily limit violation attempt",
                    user_id=user_id,
                    details={
                        "transaction_type": transaction_type,
                        "limit_amount": str(limit),
                        "current_usage": str(current_usage),
                        "attempted_addition": self.sanitizer.sanitize_amount(amount),
                        "request_id": context.request_id
                    }
                )
            
            raise TransactionLimitExceededException(
                limit_type="daily",
                limit_amount=float(limit),
                current_usage=float(current_usage),
                attempted_amount=float(amount),
                user_message=f"This transaction would exceed your daily {transaction_type} limit",
                suggested_action="Try a smaller amount or wait until tomorrow"
            )
    
    def detect_suspicious_patterns(
        self,
        context: TransactionContext,
        request: Optional[Request] = None
    ) -> List[str]:
        """
        Detect suspicious transaction patterns
        
        Returns:
            List of suspicious pattern indicators
        """
        suspicious_indicators = []
        
        # Check for round amounts (possible money laundering)
        if context.amount % 100 == 0 and context.amount >= 1000:
            suspicious_indicators.append("round_large_amount")
        
        # Check for just-under-reporting thresholds
        reporting_thresholds = [Decimal('10000'), Decimal('3000')]
        for threshold in reporting_thresholds:
            if threshold - context.amount <= Decimal('100') and context.amount < threshold:
                suspicious_indicators.append("threshold_avoidance")
        
        # Check for unusual transaction times
        if context.timestamp.hour < 6 or context.timestamp.hour > 22:
            suspicious_indicators.append("unusual_time")
        
        # Check for high frequency (would need session/recent transaction data)
        # This is a placeholder - real implementation would query recent transactions
        
        if suspicious_indicators:
            security_audit_logger.log_suspicious_activity(
                description="Suspicious transaction pattern detected",
                user_id=context.user_id,
                request=request,
                details={
                    "indicators": suspicious_indicators,
                    "transaction_type": context.transaction_type,
                    "amount_category": self.sanitizer.sanitize_amount(context.amount),
                    "request_id": context.request_id
                }
            )
        
        return suspicious_indicators


class FinancialErrorHandler:
    """
    Specialized error handler for financial operations with enhanced security
    """
    
    def __init__(self):
        self.sanitizer = FinancialDataSanitizer()
        self.validator = TransactionSecurityValidator()
    
    def handle_insufficient_funds(
        self,
        available_balance: Decimal,
        requested_amount: Decimal,
        account_id: str,
        context: Optional[TransactionContext] = None
    ) -> InsufficientFundsException:
        """
        Handle insufficient funds errors with proper sanitization
        """
        # Create sanitized error for logging
        sanitized_context = {
            "available_balance": self.sanitizer.sanitize_amount(available_balance),
            "requested_amount": self.sanitizer.sanitize_amount(requested_amount),
            "account_id": self.sanitizer.sanitize_account_id(account_id),
            "balance_hash": self.sanitizer.create_audit_hash(str(available_balance)),
            "amount_hash": self.sanitizer.create_audit_hash(str(requested_amount))
        }
        
        # Log the insufficient funds attempt
        if context:
            security_audit_logger.log_suspicious_activity(
                description="Insufficient funds transaction attempt",
                user_id=context.user_id,
                details={
                    **sanitized_context,
                    "transaction_type": context.transaction_type,
                    "request_id": context.request_id
                }
            )
        
        return InsufficientFundsException(
            available_balance=0.0,  # Don't expose actual balance
            requested_amount=0.0,   # Don't expose actual amount
            account_id=self.sanitizer.sanitize_account_id(account_id),
            user_message="Insufficient funds for this transaction",
            suggested_action="Please check your balance or add funds to your account"
        )
    
    def handle_duplicate_transaction(
        self,
        original_transaction_id: str,
        context: Optional[TransactionContext] = None
    ) -> BusinessLogicException:
        """
        Handle duplicate transaction detection
        """
        # Log duplicate transaction attempt
        if context:
            security_audit_logger.log_suspicious_activity(
                description="Duplicate transaction attempt",
                user_id=context.user_id,
                details={
                    "original_transaction_id": original_transaction_id,
                    "transaction_type": context.transaction_type,
                    "amount_category": self.sanitizer.sanitize_amount(context.amount),
                    "request_id": context.request_id
                }
            )
        
        return BusinessLogicException(
            message="Duplicate transaction detected",
            code="DUPLICATE_TRANSACTION",
            user_message="This transaction appears to be a duplicate",
            suggested_action="Please check your recent transactions"
        )
    
    def handle_data_integrity_violation(
        self,
        violation_type: str,
        affected_data: str,
        context: Optional[TransactionContext] = None
    ) -> DataIntegrityException:
        """
        Handle data integrity violations in financial data
        """
        # Sanitize the affected data description
        sanitized_data = self.sanitizer.sanitize_error_message(affected_data)
        
        # Log the integrity violation
        if context:
            security_audit_logger.log_security_violation(
                violation_type="data_integrity",
                description=f"Financial data integrity violation: {violation_type}",
                user_id=context.user_id,
                details={
                    "violation_type": violation_type,
                    "affected_data": sanitized_data,
                    "request_id": context.request_id,
                    "data_hash": self.sanitizer.create_audit_hash(affected_data)
                }
            )
        
        return DataIntegrityException(
            message=f"Data integrity violation: {violation_type}",
            code="FINANCIAL_DATA_INTEGRITY_ERROR",
            user_message="There was a problem processing your financial data",
            suggested_action="Please try again or contact support"
        )


# Global instances for use throughout the application
financial_sanitizer = FinancialDataSanitizer()
transaction_validator = TransactionSecurityValidator()
financial_error_handler = FinancialErrorHandler()