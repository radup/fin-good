"""
Financial Data Validators for FinGood Platform

Specialized validators for financial data with compliance, precision,
and security features for banking and transaction processing.
"""

import re
import logging
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime, date, timedelta
from typing import Any, Optional, Union, List, Dict
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.schemas.error import FieldError
from app.core.exceptions import ValidationException

logger = logging.getLogger(__name__)


class CurrencyCode(str, Enum):
    """Supported currency codes (ISO 4217)"""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CAD = "CAD"
    AUD = "AUD"
    JPY = "JPY"


class TransactionType(str, Enum):
    """Financial transaction types"""
    DEBIT = "debit"
    CREDIT = "credit"
    TRANSFER = "transfer"
    PAYMENT = "payment"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    REFUND = "refund"
    FEE = "fee"
    INTEREST = "interest"
    DIVIDEND = "dividend"


class AccountType(str, Enum):
    """Financial account types"""
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT_CARD = "credit_card"
    INVESTMENT = "investment"
    LOAN = "loan"
    MORTGAGE = "mortgage"


class FinancialAmount(BaseModel):
    """Validated financial amount with currency and precision controls"""
    
    amount: Decimal = Field(..., description="Monetary amount with precise decimal handling")
    currency: CurrencyCode = Field(default=CurrencyCode.USD, description="Currency code (ISO 4217)")
    
    model_config = ConfigDict(
        json_encoders={Decimal: str},
        validate_assignment=True
    )
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        """Validate monetary amount with financial precision"""
        
        if v is None:
            raise ValueError("Amount cannot be null")
        
        # Convert to Decimal for precise financial calculations
        if not isinstance(v, Decimal):
            try:
                if isinstance(v, str):
                    # Remove currency symbols, commas, and spaces
                    cleaned = re.sub(r'[$€£¥,\s]', '', v)
                    v = Decimal(cleaned)
                else:
                    v = Decimal(str(v))
            except (InvalidOperation, ValueError):
                raise ValueError("Amount must be a valid decimal number")
        
        # Financial amount limits (configurable per use case)
        max_amount = Decimal('999999999999.99')  # 1 trillion limit
        min_amount = Decimal('-999999999999.99')
        
        if v > max_amount:
            raise ValueError(f"Amount exceeds maximum limit of {max_amount}")
        if v < min_amount:
            raise ValueError(f"Amount below minimum limit of {min_amount}")
        
        # Validate precision (most currencies use 2 decimal places)
        precision = cls._get_currency_precision(CurrencyCode.USD)  # Default to USD
        if v.as_tuple().exponent < -precision:
            raise ValueError(f"Amount cannot have more than {precision} decimal places")
        
        # Round to proper precision
        quantize_exp = Decimal('0.01') if precision == 2 else Decimal('0.001')
        v = v.quantize(quantize_exp, rounding=ROUND_HALF_UP)
        
        return v
    
    @staticmethod
    def _get_currency_precision(currency: CurrencyCode) -> int:
        """Get decimal precision for currency"""
        precision_map = {
            CurrencyCode.USD: 2,
            CurrencyCode.EUR: 2,
            CurrencyCode.GBP: 2,
            CurrencyCode.CAD: 2,
            CurrencyCode.AUD: 2,
            CurrencyCode.JPY: 0,  # Yen has no decimal places
        }
        return precision_map.get(currency, 2)
    
    def to_cents(self) -> int:
        """Convert amount to cents/smallest unit for storage"""
        precision = self._get_currency_precision(self.currency)
        multiplier = 10 ** precision
        return int(self.amount * multiplier)
    
    @classmethod
    def from_cents(cls, cents: int, currency: CurrencyCode = CurrencyCode.USD) -> 'FinancialAmount':
        """Create amount from cents/smallest unit"""
        precision = cls._get_currency_precision(currency)
        divisor = 10 ** precision
        amount = Decimal(cents) / divisor
        return cls(amount=amount, currency=currency)


class BankAccountValidator:
    """Validator for bank account information"""
    
    def __init__(self):
        # US routing number patterns
        self.routing_patterns = {
            'federal_reserve': r'^0[0-9]',
            'thrift': r'^1[0-9]',
            'electronic': r'^2[0-9]',
            'traveler_check': r'^3[0-9]',
        }
    
    def validate_us_routing_number(self, routing_number: str) -> str:
        """Validate US ABA routing number with checksum verification"""
        
        if not routing_number:
            raise ValueError("Routing number is required")
        
        # Clean input
        cleaned = re.sub(r'[\s\-]', '', routing_number)
        
        # Must be exactly 9 digits
        if not re.match(r'^\d{9}$', cleaned):
            raise ValueError("Routing number must be exactly 9 digits")
        
        # Validate ABA checksum
        if not self._validate_aba_checksum(cleaned):
            raise ValueError("Invalid routing number: checksum verification failed")
        
        # Validate routing number range
        first_two = cleaned[:2]
        if not ('01' <= first_two <= '99'):
            raise ValueError("Invalid routing number: outside valid range")
        
        return cleaned
    
    def _validate_aba_checksum(self, routing_number: str) -> bool:
        """Validate ABA routing number using the standard checksum algorithm"""
        
        if len(routing_number) != 9:
            return False
        
        # ABA checksum formula: 3*d1 + 7*d2 + 1*d3 + 3*d4 + 7*d5 + 1*d6 + 3*d7 + 7*d8 + 1*d9
        weights = [3, 7, 1, 3, 7, 1, 3, 7, 1]
        checksum = sum(int(digit) * weight for digit, weight in zip(routing_number, weights))
        
        return checksum % 10 == 0
    
    def validate_account_number(self, account_number: str, account_type: Optional[AccountType] = None) -> str:
        """Validate bank account number"""
        
        if not account_number:
            raise ValueError("Account number is required")
        
        # Clean input
        cleaned = re.sub(r'[\s\-]', '', account_number)
        
        # Basic format validation
        if not re.match(r'^[0-9A-Za-z]+$', cleaned):
            raise ValueError("Account number can only contain letters and numbers")
        
        # Length validation (varies by bank, but reasonable limits)
        if len(cleaned) < 4:
            raise ValueError("Account number too short (minimum 4 characters)")
        if len(cleaned) > 20:
            raise ValueError("Account number too long (maximum 20 characters)")
        
        # Type-specific validation
        if account_type == AccountType.CREDIT_CARD:
            return self._validate_credit_card_number(cleaned)
        
        return cleaned
    
    def _validate_credit_card_number(self, card_number: str) -> str:
        """Validate credit card number using Luhn algorithm"""
        
        # Must be all digits for credit cards
        if not card_number.isdigit():
            raise ValueError("Credit card number must contain only digits")
        
        # Length validation
        if len(card_number) < 13 or len(card_number) > 19:
            raise ValueError("Credit card number must be 13-19 digits")
        
        # Luhn algorithm validation
        if not self._luhn_checksum(card_number):
            raise ValueError("Invalid credit card number: checksum verification failed")
        
        # For security, return masked version
        return self._mask_card_number(card_number)
    
    def _luhn_checksum(self, card_number: str) -> bool:
        """Validate credit card number using Luhn algorithm"""
        
        def luhn_digit(digit, odd):
            return (digit * 2 - 9) if odd and digit > 4 else (digit * 2) if odd else digit
        
        return sum(luhn_digit(int(digit), i % 2) 
                  for i, digit in enumerate(reversed(card_number))) % 10 == 0
    
    def _mask_card_number(self, card_number: str) -> str:
        """Mask credit card number for security (show only last 4 digits)"""
        return '*' * (len(card_number) - 4) + card_number[-4:]


class TransactionValidator:
    """Validator for financial transactions"""
    
    def __init__(self):
        self.amount_validator = FinancialAmount
        self.bank_validator = BankAccountValidator()
        
        # Transaction limits (configurable)
        self.daily_limits = {
            TransactionType.WITHDRAWAL: Decimal('5000.00'),
            TransactionType.TRANSFER: Decimal('10000.00'),
            TransactionType.PAYMENT: Decimal('25000.00'),
        }
        
        self.suspicious_patterns = [
            # Round amounts that might indicate money laundering
            r'^\d+00\.00$',  # Exact hundreds/thousands
            # Frequent small amounts just under reporting thresholds
            r'^(99[0-9][0-9]|9[0-9][0-9][0-9])\.00$',  # Just under $10,000
        ]
    
    def validate_transaction_amount(
        self, 
        amount: Union[str, float, Decimal], 
        transaction_type: TransactionType,
        currency: CurrencyCode = CurrencyCode.USD
    ) -> FinancialAmount:
        """Validate transaction amount with type-specific rules"""
        
        # Create validated amount
        validated_amount = FinancialAmount(amount=amount, currency=currency)
        
        # Check transaction-specific limits
        if transaction_type in self.daily_limits:
            limit = self.daily_limits[transaction_type]
            if validated_amount.amount > limit:
                raise ValueError(
                    f"{transaction_type.value} amount ${validated_amount.amount} "
                    f"exceeds daily limit of ${limit}"
                )
        
        # Check for suspicious patterns
        amount_str = str(validated_amount.amount)
        for pattern in self.suspicious_patterns:
            if re.match(pattern, amount_str):
                logger.warning(
                    f"Suspicious transaction pattern detected: {amount_str}",
                    extra={"transaction_type": transaction_type.value, "amount": amount_str}
                )
        
        # Zero amount validation
        if validated_amount.amount == 0 and transaction_type not in [
            TransactionType.FEE, TransactionType.INTEREST
        ]:
            raise ValueError("Transaction amount cannot be zero")
        
        # Negative amount validation
        if validated_amount.amount < 0 and transaction_type not in [
            TransactionType.REFUND, TransactionType.FEE
        ]:
            raise ValueError(f"Negative amounts not allowed for {transaction_type.value}")
        
        return validated_amount
    
    def validate_transaction_date(self, transaction_date: Union[str, datetime, date]) -> datetime:
        """Validate transaction date with business rules"""
        
        if isinstance(transaction_date, str):
            try:
                # Try parsing ISO format first
                if 'T' in transaction_date:
                    parsed_date = datetime.fromisoformat(transaction_date.replace('Z', '+00:00'))
                else:
                    # Parse date only
                    parsed_date = datetime.strptime(transaction_date, '%Y-%m-%d')
            except ValueError:
                raise ValueError("Transaction date must be in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)")
        elif isinstance(transaction_date, date):
            parsed_date = datetime.combine(transaction_date, datetime.min.time())
        elif isinstance(transaction_date, datetime):
            parsed_date = transaction_date
        else:
            raise ValueError("Transaction date must be a string, date, or datetime")
        
        # Business rules validation
        now = datetime.now()
        
        # Cannot be too far in the future
        if parsed_date > now + timedelta(days=1):
            raise ValueError("Transaction date cannot be more than 1 day in the future")
        
        # Cannot be too far in the past (adjust based on business needs)
        max_age = timedelta(days=7 * 365)  # 7 years
        if parsed_date < now - max_age:
            raise ValueError(f"Transaction date cannot be more than {max_age.days} days old")
        
        return parsed_date
    
    def validate_transaction_description(self, description: str) -> str:
        """Validate and sanitize transaction description"""
        
        if not description or not description.strip():
            raise ValueError("Transaction description is required")
        
        # Length validation
        description = description.strip()
        if len(description) < 3:
            raise ValueError("Transaction description must be at least 3 characters")
        if len(description) > 500:
            raise ValueError("Transaction description cannot exceed 500 characters")
        
        # Security: Remove potential sensitive information patterns
        # This is basic - in production, use more sophisticated PII detection
        
        # Remove credit card numbers
        description = re.sub(r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b', '[CARD]', description)
        
        # Remove SSNs
        description = re.sub(r'\b\d{3}[\s\-]?\d{2}[\s\-]?\d{4}\b', '[SSN]', description)
        
        # Remove phone numbers
        description = re.sub(r'\b\d{3}[\s\-]?\d{3}[\s\-]?\d{4}\b', '[PHONE]', description)
        
        # Remove email addresses
        description = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', description)
        
        # Remove account numbers (8+ consecutive digits)
        description = re.sub(r'\b\d{8,}\b', '[ACCOUNT]', description)
        
        return description


class ComplianceValidator:
    """Validator for financial compliance and regulatory requirements"""
    
    def __init__(self):
        # BSA/AML thresholds (Bank Secrecy Act / Anti-Money Laundering)
        self.cash_reporting_threshold = Decimal('10000.00')  # CTR threshold
        self.suspicious_activity_threshold = Decimal('5000.00')  # SAR monitoring
        
        # OFAC and sanctions screening patterns
        # In production, integrate with real OFAC API
        self.restricted_keywords = [
            'taliban', 'al-qaeda', 'isis', 'north korea', 'iran sanctions'
        ]
    
    def check_ctr_requirement(self, amount: Decimal, transaction_type: TransactionType) -> bool:
        """Check if transaction requires Currency Transaction Report (CTR)"""
        
        cash_transaction_types = [
            TransactionType.DEPOSIT,
            TransactionType.WITHDRAWAL,
            TransactionType.PAYMENT
        ]
        
        return (transaction_type in cash_transaction_types and 
                amount >= self.cash_reporting_threshold)
    
    def check_sar_monitoring(self, amount: Decimal, description: str = "") -> bool:
        """Check if transaction requires Suspicious Activity Report monitoring"""
        
        # Amount-based monitoring
        if amount >= self.suspicious_activity_threshold:
            return True
        
        # Pattern-based monitoring
        description_lower = description.lower()
        for keyword in self.restricted_keywords:
            if keyword in description_lower:
                return True
        
        return False
    
    def validate_customer_information(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate customer information for KYC compliance"""
        
        required_fields = ['first_name', 'last_name', 'date_of_birth', 'address', 'ssn']
        missing_fields = [field for field in required_fields if not customer_data.get(field)]
        
        if missing_fields:
            raise ValidationException(
                message="Missing required customer information for compliance",
                field_errors=[
                    FieldError(
                        field=field,
                        message="This field is required for KYC compliance",
                        code="COMPLIANCE_REQUIRED",
                        value=None
                    ) for field in missing_fields
                ]
            )
        
        # Additional validation can be added here
        return customer_data


class FinancialValidatorService:
    """Centralized service for all financial validation operations"""
    
    def __init__(self):
        self.transaction_validator = TransactionValidator()
        self.bank_validator = BankAccountValidator()
        self.compliance_validator = ComplianceValidator()
    
    def validate_complete_transaction(
        self,
        amount: Union[str, float, Decimal],
        transaction_type: TransactionType,
        description: str,
        transaction_date: Optional[Union[str, datetime, date]] = None,
        currency: CurrencyCode = CurrencyCode.USD,
        **kwargs
    ) -> Dict[str, Any]:
        """Perform complete validation of a financial transaction"""
        
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'compliance_flags': []
        }
        
        try:
            # Validate amount
            validated_amount = self.transaction_validator.validate_transaction_amount(
                amount, transaction_type, currency
            )
            
            # Validate description
            validated_description = self.transaction_validator.validate_transaction_description(description)
            
            # Validate date
            validated_date = transaction_date or datetime.now()
            if transaction_date:
                validated_date = self.transaction_validator.validate_transaction_date(transaction_date)
            
            # Compliance checks
            if self.compliance_validator.check_ctr_requirement(validated_amount.amount, transaction_type):
                validation_result['compliance_flags'].append('CTR_REQUIRED')
            
            if self.compliance_validator.check_sar_monitoring(validated_amount.amount, validated_description):
                validation_result['compliance_flags'].append('SAR_MONITORING')
            
            validation_result.update({
                'validated_data': {
                    'amount': validated_amount.amount,
                    'currency': validated_amount.currency,
                    'description': validated_description,
                    'date': validated_date,
                    'type': transaction_type
                }
            })
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(str(e))
        
        return validation_result


class SortParameterValidator:
    """Secure validator for sort parameters to prevent SQL injection"""
    
    def __init__(self):
        # Whitelist of allowed sort fields for Transaction model
        self.allowed_transaction_fields = {
            'date': 'date',
            'amount': 'amount', 
            'description': 'description',
            'vendor': 'vendor',
            'category': 'category',
            'subcategory': 'subcategory',
            'is_income': 'is_income',
            'is_categorized': 'is_categorized',
            'confidence_score': 'confidence_score',
            'created_at': 'created_at',
            'updated_at': 'updated_at'
        }
        
        # Allowed sort orders
        self.allowed_sort_orders = {'asc', 'desc'}
        
        # Default values for security
        self.default_sort_field = 'date'
        self.default_sort_order = 'desc'
    
    def validate_sort_parameters(
        self, 
        sort_by: str, 
        sort_order: str = 'desc',
        model_type: str = 'transaction'
    ) -> tuple[str, str]:
        """
        Validate and sanitize sort parameters for financial queries
        
        Args:
            sort_by: Field name to sort by
            sort_order: Sort direction ('asc' or 'desc')
            model_type: Type of model being sorted (currently supports 'transaction')
        
        Returns:
            Tuple of (validated_field, validated_order)
        
        Raises:
            ValidationException: If parameters contain dangerous content
        """
        
        # Get allowed fields for the model type
        if model_type == 'transaction':
            allowed_fields = self.allowed_transaction_fields
        else:
            raise ValidationException(
                message=f"Unsupported model type for sorting: {model_type}",
                field_errors=[FieldError(
                    field="model_type",
                    message="Only 'transaction' model sorting is currently supported",
                    code="UNSUPPORTED_MODEL_TYPE",
                    value=model_type
                )]
            )
        
        # Validate sort_by parameter
        if not sort_by:
            logger.warning("Empty sort_by parameter, using default")
            validated_field = self.default_sort_field
        else:
            # Basic input sanitization
            sort_by_clean = str(sort_by).strip().lower()
            
            # Length validation
            if len(sort_by_clean) > 50:
                raise ValidationException(
                    message="Sort field name too long",
                    field_errors=[FieldError(
                        field="sort_by",
                        message="Sort field name cannot exceed 50 characters",
                        code="SORT_FIELD_TOO_LONG",
                        value=len(sort_by_clean)
                    )]
                )
            
            # Whitelist validation
            if sort_by_clean not in allowed_fields:
                logger.warning(
                    f"Invalid sort field attempted: {sort_by_clean}",
                    extra={"attempted_field": sort_by_clean, "allowed_fields": list(allowed_fields.keys())}
                )
                raise ValidationException(
                    message="Invalid sort field",
                    field_errors=[FieldError(
                        field="sort_by",
                        message=f"Sort field must be one of: {', '.join(allowed_fields.keys())}",
                        code="INVALID_SORT_FIELD",
                        value=sort_by_clean
                    )]
                )
            
            validated_field = allowed_fields[sort_by_clean]
        
        # Validate sort_order parameter
        if not sort_order:
            logger.warning("Empty sort_order parameter, using default")
            validated_order = self.default_sort_order
        else:
            # Basic input sanitization
            sort_order_clean = str(sort_order).strip().lower()
            
            # Length validation
            if len(sort_order_clean) > 10:
                raise ValidationException(
                    message="Sort order value too long",
                    field_errors=[FieldError(
                        field="sort_order",
                        message="Sort order cannot exceed 10 characters",
                        code="SORT_ORDER_TOO_LONG",
                        value=len(sort_order_clean)
                    )]
                )
            
            # Whitelist validation
            if sort_order_clean not in self.allowed_sort_orders:
                logger.warning(
                    f"Invalid sort order attempted: {sort_order_clean}",
                    extra={"attempted_order": sort_order_clean, "allowed_orders": list(self.allowed_sort_orders)}
                )
                raise ValidationException(
                    message="Invalid sort order",
                    field_errors=[FieldError(
                        field="sort_order",
                        message=f"Sort order must be one of: {', '.join(self.allowed_sort_orders)}",
                        code="INVALID_SORT_ORDER",
                        value=sort_order_clean
                    )]
                )
            
            validated_order = sort_order_clean
        
        logger.info(
            f"Sort parameters validated successfully",
            extra={"validated_field": validated_field, "validated_order": validated_order}
        )
        
        return validated_field, validated_order
    
    def get_allowed_fields(self, model_type: str = 'transaction') -> list[str]:
        """Get list of allowed sort fields for a model type"""
        if model_type == 'transaction':
            return list(self.allowed_transaction_fields.keys())
        else:
            return []


def validate_and_secure_sort_parameters(
    sort_by: str,
    sort_order: str = 'desc',
    model_type: str = 'transaction',
    user_id: Optional[int] = None,
    request_context: Optional[Dict[str, Any]] = None
) -> tuple[str, str]:
    """
    Comprehensive security validation for sort parameters with logging and injection prevention
    
    This function provides:
    - Whitelist validation of sort fields
    - SQL injection detection and prevention
    - Security audit logging
    - Input sanitization
    - Error handling with security alerts
    
    Args:
        sort_by: Field name to sort by
        sort_order: Sort direction ('asc' or 'desc')
        model_type: Type of model being sorted
        user_id: User ID for audit logging
        request_context: Additional request context for logging
    
    Returns:
        Tuple of (validated_field, validated_order)
    
    Raises:
        ValidationException: If parameters are invalid or contain dangerous content
    """
    
    # Import here to avoid circular imports
    from app.core.security_utils import sql_injection_prevention
    from app.core.audit_logger import security_audit_logger, SecurityEventType, RiskLevel, SecurityEvent
    from datetime import datetime
    
    # Initialize validator
    validator = SortParameterValidator()
    
    try:
        # Additional SQL injection checks using existing security infrastructure
        if sort_by and sql_injection_prevention.is_sql_injection_attempt(sort_by, strict_mode=True):
            # Log security violation
            security_audit_logger.log_security_violation(
                violation_type="SQL_INJECTION_SORT_PARAMETER",
                description=f"SQL injection attempt detected in sort_by parameter: {sort_by[:100]}",
                user_id=user_id,
                details={
                    "parameter": "sort_by",
                    "attempted_value": sort_by[:100],  # Log first 100 chars only
                    "model_type": model_type,
                    "request_context": request_context
                }
            )
            
            raise ValidationException(
                message="Security violation: Dangerous sort parameter detected",
                field_errors=[FieldError(
                    field="sort_by",
                    message="Sort parameter contains potentially dangerous patterns",
                    code="SQL_INJECTION_ATTEMPT",
                    value="[REDACTED]"
                )]
            )
        
        if sort_order and sql_injection_prevention.is_sql_injection_attempt(sort_order, strict_mode=True):
            # Log security violation
            security_audit_logger.log_security_violation(
                violation_type="SQL_INJECTION_SORT_ORDER",
                description=f"SQL injection attempt detected in sort_order parameter: {sort_order[:100]}",
                user_id=user_id,
                details={
                    "parameter": "sort_order",
                    "attempted_value": sort_order[:100],
                    "model_type": model_type,
                    "request_context": request_context
                }
            )
            
            raise ValidationException(
                message="Security violation: Dangerous sort order detected",
                field_errors=[FieldError(
                    field="sort_order",
                    message="Sort order contains potentially dangerous patterns",
                    code="SQL_INJECTION_ATTEMPT",
                    value="[REDACTED]"
                )]
            )
        
        # Perform standard validation
        validated_field, validated_order = validator.validate_sort_parameters(
            sort_by, sort_order, model_type
        )
        
        # Log successful validation for audit trail
        logger.info(
            f"Sort parameters validated and secured successfully",
            extra={
                "user_id": user_id,
                "validated_field": validated_field,
                "validated_order": validated_order,
                "model_type": model_type,
                "original_sort_by": sort_by,
                "original_sort_order": sort_order
            }
        )
        
        return validated_field, validated_order
        
    except ValidationException:
        # Re-raise validation exceptions (already logged above)
        raise
    except Exception as e:
        # Log unexpected errors as security events
        security_audit_logger.log_security_violation(
            violation_type="SORT_PARAMETER_VALIDATION_ERROR",
            description=f"Unexpected error during sort parameter validation: {str(e)}",
            user_id=user_id,
            details={
                "error": str(e),
                "sort_by": sort_by[:100] if sort_by else None,
                "sort_order": sort_order[:100] if sort_order else None,
                "model_type": model_type,
                "request_context": request_context
            }
        )
        
        # Use secure defaults in case of error
        logger.error(f"Sort parameter validation error, using defaults: {str(e)}")
        return validator.default_sort_field, validator.default_sort_order