"""
Enhanced Endpoint-Specific Validators for FinGood Financial Platform

Comprehensive validation framework providing endpoint-specific validation rules,
type coercion, sanitization, and business logic validation for all API endpoints.
Focuses on financial data integrity, security, and regulatory compliance.
"""

import re
import logging
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Union, Type, Callable, get_origin, get_args
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ValidationError, ConfigDict
from fastapi import Query, Path, Body, HTTPException, status

from app.core.financial_validators import (
    FinancialAmount, TransactionType, CurrencyCode, 
    TransactionValidator, ComplianceValidator, FinancialValidatorService
)
from app.core.security_utils import input_sanitizer, sql_injection_prevention
from app.core.exceptions import ValidationException
from app.schemas.error import FieldError, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Validation severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EndpointValidationConfig(BaseModel):
    """Configuration for endpoint-specific validation"""
    
    model_config = ConfigDict(frozen=True)
    
    endpoint_name: str
    require_authentication: bool = True
    require_csrf_protection: bool = True
    max_request_size: int = 1024 * 1024  # 1MB default
    rate_limit_per_minute: int = 60
    enable_sql_injection_check: bool = True
    enable_xss_protection: bool = True
    enable_pii_detection: bool = True
    validation_severity: ValidationSeverity = ValidationSeverity.HIGH
    custom_validators: List[str] = Field(default_factory=list)


class ParameterValidator:
    """Enhanced parameter validation with type coercion and business rules"""
    
    def __init__(self):
        self.financial_validator = FinancialValidatorService()
        self.compliance_validator = ComplianceValidator()
        
        # Parameter-specific validation rules
        self.validation_rules = {
            # Pagination parameters
            'skip': {
                'type': int,
                'min_value': 0,
                'max_value': 100000,
                'default': 0,
                'description': 'Number of records to skip for pagination'
            },
            'limit': {
                'type': int,
                'min_value': 1,
                'max_value': 1000,
                'default': 50,
                'description': 'Maximum number of records to return'
            },
            'page': {
                'type': int,
                'min_value': 1,
                'max_value': 10000,
                'default': 1,
                'description': 'Page number for pagination'
            },
            
            # Financial parameters
            'amount': {
                'type': Decimal,
                'min_value': Decimal('-999999999999.99'),
                'max_value': Decimal('999999999999.99'),
                'precision': 2,
                'description': 'Financial amount with currency precision'
            },
            'min_amount': {
                'type': Decimal,
                'min_value': Decimal('0.00'),
                'max_value': Decimal('999999999999.99'),
                'precision': 2,
                'description': 'Minimum amount filter'
            },
            'max_amount': {
                'type': Decimal,
                'min_value': Decimal('0.00'),
                'max_value': Decimal('999999999999.99'),
                'precision': 2,
                'description': 'Maximum amount filter'
            },
            
            # Date parameters
            'start_date': {
                'type': datetime,
                'min_value': datetime(2000, 1, 1),
                'max_value': None,  # Will be set to future limit
                'description': 'Start date for filtering (ISO format)'
            },
            'end_date': {
                'type': datetime,
                'min_value': datetime(2000, 1, 1),
                'max_value': None,  # Will be set to future limit
                'description': 'End date for filtering (ISO format)'
            },
            'date': {
                'type': datetime,
                'min_value': datetime(2000, 1, 1),
                'max_value': None,
                'description': 'Transaction date (ISO format)'
            },
            
            # String parameters with length limits
            'category': {
                'type': str,
                'min_length': 1,
                'max_length': 100,
                'pattern': r'^[a-zA-Z0-9\s\-_&]+$',
                'description': 'Transaction category name'
            },
            'subcategory': {
                'type': str,
                'min_length': 1,
                'max_length': 100,
                'pattern': r'^[a-zA-Z0-9\s\-_&]+$',
                'description': 'Transaction subcategory name'
            },
            'vendor': {
                'type': str,
                'min_length': 1,
                'max_length': 200,
                'pattern': r'^[a-zA-Z0-9\s\-_&.,()]+$',
                'description': 'Vendor or merchant name'
            },
            'description': {
                'type': str,
                'min_length': 3,
                'max_length': 500,
                'description': 'Transaction description'
            },
            
            # Boolean parameters
            'is_income': {
                'type': bool,
                'description': 'Filter for income transactions'
            },
            'is_categorized': {
                'type': bool,
                'description': 'Filter for categorized transactions'
            },
            'create_rule': {
                'type': bool,
                'description': 'Whether to create categorization rule'
            },
            
            # Enumeration parameters
            'sort_by': {
                'type': str,
                'allowed_values': ['date', 'amount', 'description', 'vendor', 'category', 'id'],
                'default': 'date',
                'description': 'Field to sort by'
            },
            'sort_order': {
                'type': str,
                'allowed_values': ['asc', 'desc'],
                'default': 'desc',
                'description': 'Sort order'
            },
            'transaction_type': {
                'type': str,
                'allowed_values': [t.value for t in TransactionType],
                'description': 'Type of financial transaction'
            },
            'currency': {
                'type': str,
                'allowed_values': [c.value for c in CurrencyCode],
                'default': 'USD',
                'description': 'Currency code (ISO 4217)'
            },
            
            # Identifier parameters
            'transaction_id': {
                'type': int,
                'min_value': 1,
                'max_value': 9223372036854775807,  # Max int64
                'description': 'Unique transaction identifier'
            },
            'user_id': {
                'type': int,
                'min_value': 1,
                'max_value': 9223372036854775807,
                'description': 'User identifier'
            },
            'batch_id': {
                'type': str,
                'min_length': 1,
                'max_length': 255,
                'pattern': r'^[a-zA-Z0-9\-_]+$',
                'description': 'Import batch identifier'
            },
        }
        
        # Set dynamic date limits
        future_limit = datetime.now() + timedelta(days=365)
        for param in ['start_date', 'end_date', 'date']:
            if param in self.validation_rules:
                self.validation_rules[param]['max_value'] = future_limit
    
    def validate_parameter(
        self, 
        param_name: str, 
        value: Any, 
        endpoint_name: str = None,
        custom_rules: Dict[str, Any] = None
    ) -> Any:
        """
        Validate and convert a single parameter
        
        Args:
            param_name: Name of the parameter
            value: Raw parameter value
            endpoint_name: Name of the endpoint for context
            custom_rules: Override default validation rules
        
        Returns:
            Validated and converted parameter value
        """
        
        if value is None:
            return None
        
        # Get validation rules
        rules = custom_rules or self.validation_rules.get(param_name, {})
        if not rules:
            # For unknown parameters, apply basic sanitization
            return self._sanitize_unknown_parameter(param_name, value)
        
        try:
            # Type conversion and validation
            param_type = rules.get('type', str)
            converted_value = self._convert_parameter_type(param_name, value, param_type)
            
            # Apply type-specific validation
            if param_type == int:
                converted_value = self._validate_integer_parameter(param_name, converted_value, rules)
            elif param_type == Decimal:
                converted_value = self._validate_decimal_parameter(param_name, converted_value, rules)
            elif param_type == str:
                converted_value = self._validate_string_parameter(param_name, converted_value, rules)
            elif param_type == datetime:
                converted_value = self._validate_datetime_parameter(param_name, converted_value, rules)
            elif param_type == bool:
                converted_value = self._validate_boolean_parameter(param_name, converted_value, rules)
            
            # Apply business logic validation
            self._apply_business_rules(param_name, converted_value, endpoint_name)
            
            return converted_value
            
        except (ValueError, ValidationException) as e:
            raise ValidationException(
                message=f"Invalid parameter '{param_name}'",
                field_errors=[FieldError(
                    field=param_name,
                    message=str(e),
                    code="INVALID_PARAMETER",
                    value=str(value)[:100] if value else None
                )]
            )
        except Exception as e:
            logger.error(f"Unexpected error validating parameter {param_name}: {str(e)}")
            raise ValidationException(
                message=f"Parameter validation failed for '{param_name}'",
                field_errors=[FieldError(
                    field=param_name,
                    message="Internal validation error",
                    code="VALIDATION_ERROR",
                    value=None
                )]
            )
    
    def _convert_parameter_type(self, param_name: str, value: Any, target_type: Type) -> Any:
        """Convert parameter to target type with proper error handling"""
        
        if isinstance(value, target_type):
            return value
        
        try:
            if target_type == int:
                if isinstance(value, str):
                    # Remove any whitespace and validate format
                    cleaned = value.strip()
                    if not re.match(r'^-?\d+$', cleaned):
                        raise ValueError(f"'{value}' is not a valid integer")
                    return int(cleaned)
                return int(value)
            
            elif target_type == Decimal:
                if isinstance(value, str):
                    # Clean and validate decimal string
                    cleaned = re.sub(r'[$,\s]', '', value.strip())
                    if not re.match(r'^-?\d*\.?\d*$', cleaned):
                        raise ValueError(f"'{value}' is not a valid decimal number")
                    return Decimal(cleaned)
                return Decimal(str(value))
            
            elif target_type == datetime:
                if isinstance(value, str):
                    # Parse ISO format datetime
                    try:
                        # Handle various ISO formats
                        if 'T' in value:
                            return datetime.fromisoformat(value.replace('Z', '+00:00'))
                        else:
                            return datetime.fromisoformat(value)
                    except ValueError:
                        # Try parsing as date only
                        try:
                            parsed_date = datetime.strptime(value, '%Y-%m-%d')
                            return parsed_date
                        except ValueError:
                            raise ValueError(f"'{value}' is not a valid ISO datetime format")
                return value
            
            elif target_type == bool:
                if isinstance(value, str):
                    lower_value = value.lower().strip()
                    if lower_value in ['true', '1', 'yes', 'on']:
                        return True
                    elif lower_value in ['false', '0', 'no', 'off']:
                        return False
                    else:
                        raise ValueError(f"'{value}' is not a valid boolean value")
                return bool(value)
            
            elif target_type == str:
                return str(value)
            
            else:
                raise ValueError(f"Unsupported parameter type: {target_type}")
                
        except (ValueError, InvalidOperation) as e:
            raise ValueError(f"Cannot convert '{value}' to {target_type.__name__}: {str(e)}")
    
    def _validate_integer_parameter(self, param_name: str, value: int, rules: Dict[str, Any]) -> int:
        """Validate integer parameter with range checks"""
        
        min_value = rules.get('min_value')
        max_value = rules.get('max_value')
        
        if min_value is not None and value < min_value:
            raise ValueError(f"Value {value} is below minimum {min_value}")
        
        if max_value is not None and value > max_value:
            raise ValueError(f"Value {value} exceeds maximum {max_value}")
        
        return value
    
    def _validate_decimal_parameter(self, param_name: str, value: Decimal, rules: Dict[str, Any]) -> Decimal:
        """Validate decimal parameter with precision and range checks"""
        
        # Range validation
        min_value = rules.get('min_value')
        max_value = rules.get('max_value')
        
        if min_value is not None and value < min_value:
            raise ValueError(f"Amount {value} is below minimum {min_value}")
        
        if max_value is not None and value > max_value:
            raise ValueError(f"Amount {value} exceeds maximum {max_value}")
        
        # Precision validation
        precision = rules.get('precision', 2)
        if value.as_tuple().exponent < -precision:
            raise ValueError(f"Amount cannot have more than {precision} decimal places")
        
        # Round to proper precision
        quantize_exp = Decimal('0.' + '0' * (precision - 1) + '1')
        return value.quantize(quantize_exp, rounding=ROUND_HALF_UP)
    
    def _validate_string_parameter(self, param_name: str, value: str, rules: Dict[str, Any]) -> str:
        """Validate string parameter with length, pattern, and security checks"""
        
        # Security sanitization first
        sanitized_value = input_sanitizer.sanitize_financial_input(
            value,
            field_name=param_name,
            max_length=rules.get('max_length', 1000),
            remove_pii=param_name not in ['category', 'subcategory']  # Don't remove PII from categories
        )
        
        # Length validation
        min_length = rules.get('min_length', 0)
        max_length = rules.get('max_length', 1000)
        
        if len(sanitized_value) < min_length:
            raise ValueError(f"Must be at least {min_length} characters long")
        
        if len(sanitized_value) > max_length:
            raise ValueError(f"Cannot exceed {max_length} characters")
        
        # Pattern validation
        pattern = rules.get('pattern')
        if pattern and not re.match(pattern, sanitized_value):
            raise ValueError(f"Does not match required format")
        
        # Allowed values validation
        allowed_values = rules.get('allowed_values')
        if allowed_values and sanitized_value not in allowed_values:
            raise ValueError(f"Must be one of: {', '.join(allowed_values)}")
        
        return sanitized_value
    
    def _validate_datetime_parameter(self, param_name: str, value: datetime, rules: Dict[str, Any]) -> datetime:
        """Validate datetime parameter with range checks"""
        
        min_value = rules.get('min_value')
        max_value = rules.get('max_value')
        
        if min_value and value < min_value:
            raise ValueError(f"Date {value.isoformat()} is before minimum {min_value.isoformat()}")
        
        if max_value and value > max_value:
            raise ValueError(f"Date {value.isoformat()} is after maximum {max_value.isoformat()}")
        
        return value
    
    def _validate_boolean_parameter(self, param_name: str, value: bool, rules: Dict[str, Any]) -> bool:
        """Validate boolean parameter (no additional rules currently)"""
        return value
    
    def _sanitize_unknown_parameter(self, param_name: str, value: Any) -> str:
        """Apply basic sanitization to unknown parameters"""
        
        if not isinstance(value, str):
            value = str(value)
        
        # Apply basic security sanitization
        return input_sanitizer.sanitize_financial_input(
            value,
            field_name=param_name,
            max_length=500,
            remove_pii=True
        )
    
    def _apply_business_rules(self, param_name: str, value: Any, endpoint_name: str = None):
        """Apply business logic validation rules"""
        
        # Financial amount business rules
        if param_name in ['amount', 'min_amount', 'max_amount'] and isinstance(value, Decimal):
            # Check for suspicious round amounts (potential money laundering)
            if value > Decimal('10000') and value % Decimal('1000') == 0:
                logger.warning(
                    f"Suspicious round amount detected: {value}",
                    extra={"param_name": param_name, "endpoint": endpoint_name, "amount": str(value)}
                )
            
            # Check compliance thresholds
            if self.compliance_validator.check_ctr_requirement(value, TransactionType.PAYMENT):
                logger.info(
                    f"Amount triggers CTR requirement: {value}",
                    extra={"param_name": param_name, "endpoint": endpoint_name, "compliance_flag": "CTR"}
                )
        
        # Date business rules
        if param_name in ['start_date', 'end_date', 'date'] and isinstance(value, datetime):
            # Check for dates too far in the future
            if value > datetime.now() + timedelta(days=30):
                raise ValueError("Date cannot be more than 30 days in the future")
            
            # Check for dates too far in the past for certain operations
            if endpoint_name in ['transactions', 'analytics'] and value < datetime.now() - timedelta(days=7*365):
                logger.warning(
                    f"Very old date requested: {value.isoformat()}",
                    extra={"param_name": param_name, "endpoint": endpoint_name}
                )
        
        # Category validation
        if param_name in ['category', 'subcategory'] and isinstance(value, str):
            # Validate against known financial categories (basic check)
            suspicious_categories = ['cash', 'untraceable', 'anonymous', 'crypto']
            if any(suspicious in value.lower() for suspicious in suspicious_categories):
                logger.warning(
                    f"Potentially suspicious category: {value}",
                    extra={"param_name": param_name, "endpoint": endpoint_name}
                )


class RequestBodyValidator:
    """Enhanced request body validation with comprehensive financial data checks"""
    
    def __init__(self):
        self.financial_validator = FinancialValidatorService()
        self.parameter_validator = ParameterValidator()
    
    def validate_transaction_create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate transaction creation request body"""
        
        validated_data = {}
        field_errors = []
        
        # Required fields validation
        required_fields = ['date', 'amount', 'description']
        for field in required_fields:
            if field not in data or data[field] is None:
                field_errors.append(FieldError(
                    field=field,
                    message=f"Field '{field}' is required",
                    code="REQUIRED_FIELD_MISSING",
                    value=None
                ))
        
        if field_errors:
            raise ValidationException(
                message="Required fields missing",
                field_errors=field_errors
            )
        
        # Validate each field
        for field_name, value in data.items():
            try:
                if field_name in ['date']:
                    validated_data[field_name] = self.parameter_validator.validate_parameter(
                        field_name, value, 'transaction_create'
                    )
                elif field_name in ['amount']:
                    validated_data[field_name] = self.parameter_validator.validate_parameter(
                        field_name, value, 'transaction_create'
                    )
                elif field_name in ['description', 'vendor', 'category', 'subcategory']:
                    validated_data[field_name] = self.parameter_validator.validate_parameter(
                        field_name, value, 'transaction_create'
                    )
                elif field_name in ['is_income', 'create_rule']:
                    validated_data[field_name] = self.parameter_validator.validate_parameter(
                        field_name, value, 'transaction_create'
                    )
                else:
                    # Handle additional fields with basic validation
                    if isinstance(value, str):
                        validated_data[field_name] = input_sanitizer.sanitize_financial_input(
                            value, field_name=field_name, max_length=500
                        )
                    else:
                        validated_data[field_name] = value
                        
            except ValidationException as e:
                field_errors.extend(e.field_errors)
            except Exception as e:
                field_errors.append(FieldError(
                    field=field_name,
                    message=str(e),
                    code="FIELD_VALIDATION_ERROR",
                    value=str(value)[:100] if value else None
                ))
        
        if field_errors:
            raise ValidationException(
                message="Request body validation failed",
                field_errors=field_errors
            )
        
        # Additional business logic validation
        self._validate_transaction_business_rules(validated_data)
        
        return validated_data
    
    def validate_transaction_update(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate transaction update request body"""
        
        validated_data = {}
        field_errors = []
        
        # Validate each field (all optional for updates)
        for field_name, value in data.items():
            try:
                if field_name in ['category', 'subcategory']:
                    validated_data[field_name] = self.parameter_validator.validate_parameter(
                        field_name, value, 'transaction_update'
                    )
                elif field_name in ['create_rule']:
                    validated_data[field_name] = self.parameter_validator.validate_parameter(
                        field_name, value, 'transaction_update'
                    )
                else:
                    # Handle unexpected fields
                    if isinstance(value, str):
                        validated_data[field_name] = input_sanitizer.sanitize_financial_input(
                            value, field_name=field_name, max_length=200
                        )
                    else:
                        validated_data[field_name] = value
                        
            except ValidationException as e:
                field_errors.extend(e.field_errors)
            except Exception as e:
                field_errors.append(FieldError(
                    field=field_name,
                    message=str(e),
                    code="FIELD_VALIDATION_ERROR",
                    value=str(value)[:100] if value else None
                ))
        
        if field_errors:
            raise ValidationException(
                message="Update request validation failed",
                field_errors=field_errors
            )
        
        return validated_data
    
    def validate_user_registration(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate user registration request body"""
        
        validated_data = {}
        field_errors = []
        
        # Required fields
        required_fields = ['email', 'password', 'full_name']
        for field in required_fields:
            if field not in data or not data[field]:
                field_errors.append(FieldError(
                    field=field,
                    message=f"Field '{field}' is required",
                    code="REQUIRED_FIELD_MISSING",
                    value=None
                ))
        
        if field_errors:
            raise ValidationException(
                message="Required fields missing for registration",
                field_errors=field_errors
            )
        
        # Validate email
        if 'email' in data:
            email = data['email'].strip().lower()
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                field_errors.append(FieldError(
                    field='email',
                    message="Invalid email format",
                    code="INVALID_EMAIL_FORMAT",
                    value=email
                ))
            else:
                validated_data['email'] = email
        
        # Validate password
        if 'password' in data:
            password = data['password']
            if len(password) < 8:
                field_errors.append(FieldError(
                    field='password',
                    message="Password must be at least 8 characters long",
                    code="PASSWORD_TOO_SHORT",
                    value=len(password)
                ))
            elif not re.search(r'[A-Z]', password):
                field_errors.append(FieldError(
                    field='password',
                    message="Password must contain at least one uppercase letter",
                    code="PASSWORD_MISSING_UPPERCASE",
                    value=None
                ))
            elif not re.search(r'[a-z]', password):
                field_errors.append(FieldError(
                    field='password',
                    message="Password must contain at least one lowercase letter",
                    code="PASSWORD_MISSING_LOWERCASE",
                    value=None
                ))
            elif not re.search(r'\d', password):
                field_errors.append(FieldError(
                    field='password',
                    message="Password must contain at least one digit",
                    code="PASSWORD_MISSING_DIGIT",
                    value=None
                ))
            else:
                validated_data['password'] = password
        
        # Validate full name
        if 'full_name' in data:
            full_name = input_sanitizer.sanitize_financial_input(
                data['full_name'], 
                field_name='full_name', 
                max_length=100, 
                remove_pii=False
            )
            if len(full_name.strip()) < 2:
                field_errors.append(FieldError(
                    field='full_name',
                    message="Full name must be at least 2 characters long",
                    code="NAME_TOO_SHORT",
                    value=len(full_name)
                ))
            else:
                validated_data['full_name'] = full_name
        
        # Validate optional fields
        for field_name in ['company_name', 'business_type']:
            if field_name in data and data[field_name]:
                try:
                    validated_data[field_name] = input_sanitizer.sanitize_financial_input(
                        data[field_name],
                        field_name=field_name,
                        max_length=200,
                        remove_pii=False
                    )
                except ValidationException as e:
                    field_errors.extend(e.field_errors)
        
        if field_errors:
            raise ValidationException(
                message="Registration data validation failed",
                field_errors=field_errors
            )
        
        return validated_data
    
    def _validate_transaction_business_rules(self, data: Dict[str, Any]):
        """Apply business rules validation to transaction data"""
        
        # Use the financial validator service for comprehensive validation
        try:
            result = self.financial_validator.validate_complete_transaction(
                amount=data['amount'],
                transaction_type=TransactionType.PAYMENT,  # Default type
                description=data['description'],
                transaction_date=data.get('date'),
                currency=CurrencyCode.USD
            )
            
            if not result['valid']:
                raise ValidationException(
                    message="Transaction validation failed",
                    field_errors=[FieldError(
                        field="transaction",
                        message="; ".join(result['errors']),
                        code="BUSINESS_RULE_VIOLATION",
                        value=None
                    )]
                )
            
            # Log compliance flags
            if result.get('compliance_flags'):
                logger.info(
                    f"Transaction compliance flags: {result['compliance_flags']}",
                    extra={"compliance_flags": result['compliance_flags']}
                )
                
        except Exception as e:
            logger.error(f"Business rules validation error: {str(e)}")
            raise ValidationException(
                message="Business rules validation failed",
                field_errors=[FieldError(
                    field="transaction",
                    message="Failed to validate business rules",
                    code="BUSINESS_RULE_ERROR",
                    value=str(e)
                )]
            )


# Global instances for easy import
parameter_validator = ParameterValidator()
request_body_validator = RequestBodyValidator()