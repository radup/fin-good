"""
Comprehensive Query Parameter Validation for FinGood Financial Platform

Advanced query parameter validation system with type coercion, sanitization,
business rule validation, and security checks. Provides decorators and
utilities for validating all query parameters across API endpoints.
"""

import re
import logging
from functools import wraps
from typing import Any, Dict, List, Optional, Union, Callable, get_type_hints
from decimal import Decimal
from datetime import datetime
from fastapi import Query, HTTPException, status, Request
from pydantic import BaseModel, Field, ValidationError, ConfigDict

from app.core.endpoint_validators import parameter_validator, ParameterValidator
from app.core.security_utils import input_sanitizer, sql_injection_prevention
from app.core.exceptions import ValidationException
from app.schemas.error import FieldError, APIErrorResponse, ErrorDetail, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class QueryParameterConfig(BaseModel):
    """Configuration for query parameter validation"""
    
    model_config = ConfigDict(frozen=True)
    
    param_name: str
    required: bool = False
    default_value: Any = None
    param_type: type = str
    min_value: Optional[Union[int, float, Decimal]] = None
    max_value: Optional[Union[int, float, Decimal]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    allowed_values: Optional[List[str]] = None
    custom_validator: Optional[Callable] = None
    description: str = ""
    security_level: str = "medium"  # low, medium, high, critical


class ValidatedQueryParams(BaseModel):
    """Base class for validated query parameters with common pagination and filtering"""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'  # Reject unknown parameters
    )
    
    # Common pagination parameters
    skip: int = Field(
        default=0,
        ge=0,
        le=100000,
        description="Number of records to skip for pagination"
    )
    
    limit: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Maximum number of records to return"
    )
    
    # Common sorting parameters
    sort_by: str = Field(
        default="date",
        pattern=r"^(id|date|amount|description|vendor|category|created_at|updated_at)$",
        description="Field to sort results by"
    )
    
    sort_order: str = Field(
        default="desc",
        pattern=r"^(asc|desc)$",
        description="Sort order: asc or desc"
    )


class TransactionQueryParams(ValidatedQueryParams):
    """Validated query parameters for transaction endpoints"""
    
    # Date filters
    start_date: Optional[datetime] = Field(
        None,
        description="Filter transactions from this date (ISO format)"
    )
    
    end_date: Optional[datetime] = Field(
        None,
        description="Filter transactions until this date (ISO format)"
    )
    
    # Amount filters
    min_amount: Optional[Decimal] = Field(
        None,
        ge=Decimal('0.00'),
        le=Decimal('999999999999.99'),
        decimal_places=2,
        description="Minimum transaction amount"
    )
    
    max_amount: Optional[Decimal] = Field(
        None,
        ge=Decimal('0.00'),
        le=Decimal('999999999999.99'),
        decimal_places=2,
        description="Maximum transaction amount"
    )
    
    # Category filters
    category: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9\s\-_&]+$",
        description="Filter by transaction category"
    )
    
    subcategory: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9\s\-_&]+$",
        description="Filter by transaction subcategory"
    )
    
    # Vendor/merchant filter
    vendor: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        pattern=r"^[a-zA-Z0-9\s\-_&.,()]+$",
        description="Filter by vendor/merchant name"
    )
    
    # Description filter
    description: Optional[str] = Field(
        None,
        min_length=3,
        max_length=500,
        description="Filter by transaction description (partial match)"
    )
    
    # Boolean filters
    is_income: Optional[bool] = Field(
        None,
        description="Filter for income (true) or expense (false) transactions"
    )
    
    is_categorized: Optional[bool] = Field(
        None,
        description="Filter for categorized (true) or uncategorized (false) transactions"
    )
    
    # Additional filters
    import_batch: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        pattern=r"^[a-zA-Z0-9\-_]+$",
        description="Filter by import batch ID"
    )
    
    @classmethod
    def from_request(cls, request: Request) -> 'TransactionQueryParams':
        """Create validated query params from FastAPI request"""
        
        query_params = dict(request.query_params)
        
        # Apply parameter validation and sanitization
        validated_params = {}
        field_errors = []
        
        for param_name, value in query_params.items():
            try:
                # Use our parameter validator for comprehensive validation
                validated_value = parameter_validator.validate_parameter(
                    param_name, value, 'transactions'
                )
                validated_params[param_name] = validated_value
                
            except ValidationException as e:
                field_errors.extend(e.field_errors)
            except Exception as e:
                field_errors.append(FieldError(
                    field=param_name,
                    message=str(e),
                    code="PARAMETER_VALIDATION_ERROR",
                    value=str(value)[:100]
                ))
        
        if field_errors:
            raise ValidationException(
                message="Query parameter validation failed",
                field_errors=field_errors
            )
        
        try:
            return cls(**validated_params)
        except ValidationError as e:
            # Convert Pydantic validation errors to our format
            pydantic_errors = []
            for error in e.errors():
                field_name = '.'.join(str(loc) for loc in error['loc'])
                pydantic_errors.append(FieldError(
                    field=field_name,
                    message=error['msg'],
                    code="PYDANTIC_VALIDATION_ERROR",
                    value=error.get('input')
                ))
            
            raise ValidationException(
                message="Query parameter schema validation failed",
                field_errors=pydantic_errors
            )


class AnalyticsQueryParams(ValidatedQueryParams):
    """Validated query parameters for analytics endpoints"""
    
    # Time period for analytics
    start_date: datetime = Field(
        ...,
        description="Start date for analytics period (required)"
    )
    
    end_date: datetime = Field(
        ...,
        description="End date for analytics period (required)"
    )
    
    # Grouping options
    group_by: str = Field(
        default="month",
        pattern=r"^(day|week|month|quarter|year|category|vendor)$",
        description="How to group analytics data"
    )
    
    # Category filters
    categories: Optional[List[str]] = Field(
        None,
        max_items=50,
        description="List of categories to include in analytics"
    )
    
    # Include/exclude options
    include_income: bool = Field(
        default=True,
        description="Include income transactions in analytics"
    )
    
    include_expenses: bool = Field(
        default=True,
        description="Include expense transactions in analytics"
    )
    
    # Currency filter
    currency: str = Field(
        default="USD",
        pattern=r"^[A-Z]{3}$",
        description="Currency code for analytics (ISO 4217)"
    )


class UserQueryParams(ValidatedQueryParams):
    """Validated query parameters for user management endpoints"""
    
    # Search filters
    email: Optional[str] = Field(
        None,
        min_length=3,
        max_length=254,
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        description="Filter by user email"
    )
    
    full_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="Filter by user full name (partial match)"
    )
    
    # Status filters
    is_active: Optional[bool] = Field(
        None,
        description="Filter by user active status"
    )
    
    # Registration date filters
    registered_after: Optional[datetime] = Field(
        None,
        description="Filter users registered after this date"
    )
    
    registered_before: Optional[datetime] = Field(
        None,
        description="Filter users registered before this date"
    )


def validate_query_parameters(param_class: type):
    """
    Decorator to validate query parameters using specified parameter class
    
    Args:
        param_class: Pydantic model class for parameter validation
    
    Returns:
        Decorator function that validates and injects validated parameters
    """
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # Look in kwargs
                request = kwargs.get('request')
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found in function arguments"
                )
            
            try:
                # Validate query parameters
                if hasattr(param_class, 'from_request'):
                    validated_params = param_class.from_request(request)
                else:
                    # Fallback to direct instantiation
                    query_params = dict(request.query_params)
                    validated_params = param_class(**query_params)
                
                # Add validated parameters to kwargs
                kwargs['validated_params'] = validated_params
                
                # Call the original function
                return await func(*args, **kwargs)
                
            except ValidationException as e:
                # Convert to HTTPException with proper error response
                error_response = APIErrorResponse(
                    error=ErrorDetail(
                        code="QUERY_PARAMETER_VALIDATION_FAILED",
                        message=e.message,
                        category=ErrorCategory.VALIDATION_ERROR,
                        severity=ErrorSeverity.MEDIUM,
                        correlation_id=e.correlation_id,
                        user_message="Invalid query parameters provided",
                        suggested_action="Please check your query parameters and try again",
                        field_errors=e.field_errors
                    ),
                    request_id=getattr(request.state, 'request_id', None),
                    path=str(request.url.path),
                    method=request.method
                )
                
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=error_response.dict()
                )
            
            except ValidationError as e:
                # Handle Pydantic validation errors
                field_errors = []
                for error in e.errors():
                    field_name = '.'.join(str(loc) for loc in error['loc'])
                    field_errors.append(FieldError(
                        field=field_name,
                        message=error['msg'],
                        code="SCHEMA_VALIDATION_ERROR",
                        value=error.get('input')
                    ))
                
                error_response = APIErrorResponse(
                    error=ErrorDetail(
                        code="QUERY_PARAMETER_SCHEMA_ERROR",
                        message="Query parameter schema validation failed",
                        category=ErrorCategory.VALIDATION_ERROR,
                        severity=ErrorSeverity.MEDIUM,
                        user_message="Invalid query parameters format",
                        suggested_action="Please check the API documentation for correct parameter format",
                        field_errors=field_errors
                    ),
                    request_id=getattr(request.state, 'request_id', None),
                    path=str(request.url.path),
                    method=request.method
                )
                
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=error_response.dict()
                )
            
            except Exception as e:
                logger.error(f"Unexpected error in query parameter validation: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal error during parameter validation"
                )
        
        return wrapper
    return decorator


def validate_path_parameters(*param_configs: QueryParameterConfig):
    """
    Decorator to validate path parameters
    
    Args:
        param_configs: Configuration objects for path parameter validation
    
    Returns:
        Decorator function that validates path parameters
    """
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            field_errors = []
            
            # Validate each configured path parameter
            for config in param_configs:
                param_value = kwargs.get(config.param_name)
                
                if param_value is None and config.required:
                    field_errors.append(FieldError(
                        field=config.param_name,
                        message=f"Required path parameter '{config.param_name}' is missing",
                        code="REQUIRED_PATH_PARAMETER_MISSING",
                        value=None
                    ))
                    continue
                
                if param_value is not None:
                    try:
                        # Use parameter validator for validation
                        validated_value = parameter_validator.validate_parameter(
                            config.param_name, 
                            param_value, 
                            'path_parameter'
                        )
                        kwargs[config.param_name] = validated_value
                        
                    except ValidationException as e:
                        field_errors.extend(e.field_errors)
                    except Exception as e:
                        field_errors.append(FieldError(
                            field=config.param_name,
                            message=str(e),
                            code="PATH_PARAMETER_VALIDATION_ERROR",
                            value=str(param_value)
                        ))
            
            if field_errors:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "error": {
                            "code": "PATH_PARAMETER_VALIDATION_FAILED",
                            "message": "Path parameter validation failed",
                            "field_errors": [error.dict() for error in field_errors]
                        }
                    }
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


class QueryParameterHelper:
    """Helper class for common query parameter operations"""
    
    @staticmethod
    def sanitize_like_parameter(value: str, max_length: int = 100) -> str:
        """
        Sanitize a parameter that will be used in SQL LIKE operations
        
        Args:
            value: Parameter value to sanitize
            max_length: Maximum allowed length
        
        Returns:
            Sanitized value safe for LIKE operations
        """
        
        if not value:
            return ""
        
        # Basic sanitization
        sanitized = input_sanitizer.sanitize_financial_input(
            value,
            field_name="like_parameter",
            max_length=max_length,
            remove_pii=True
        )
        
        # Escape SQL LIKE wildcards to prevent injection
        sanitized = sanitized.replace('%', '\\%').replace('_', '\\_')
        
        return f"%{sanitized}%"
    
    @staticmethod
    def validate_date_range(start_date: Optional[datetime], end_date: Optional[datetime]) -> None:
        """
        Validate date range parameters
        
        Args:
            start_date: Start date of range
            end_date: End date of range
        
        Raises:
            ValidationException: If date range is invalid
        """
        
        if start_date and end_date:
            if start_date > end_date:
                raise ValidationException(
                    message="Invalid date range",
                    field_errors=[FieldError(
                        field="date_range",
                        message="Start date cannot be after end date",
                        code="INVALID_DATE_RANGE",
                        value=f"{start_date.isoformat()} > {end_date.isoformat()}"
                    )]
                )
            
            # Check for overly large date ranges
            max_range = datetime.now() - datetime(2000, 1, 1)
            if end_date - start_date > max_range:
                raise ValidationException(
                    message="Date range too large",
                    field_errors=[FieldError(
                        field="date_range",
                        message="Date range cannot exceed maximum allowed period",
                        code="DATE_RANGE_TOO_LARGE",
                        value=str(end_date - start_date)
                    )]
                )
    
    @staticmethod
    def validate_amount_range(min_amount: Optional[Decimal], max_amount: Optional[Decimal]) -> None:
        """
        Validate amount range parameters
        
        Args:
            min_amount: Minimum amount
            max_amount: Maximum amount
        
        Raises:
            ValidationException: If amount range is invalid
        """
        
        if min_amount and max_amount:
            if min_amount > max_amount:
                raise ValidationException(
                    message="Invalid amount range",
                    field_errors=[FieldError(
                        field="amount_range",
                        message="Minimum amount cannot be greater than maximum amount",
                        code="INVALID_AMOUNT_RANGE",
                        value=f"{min_amount} > {max_amount}"
                    )]
                )
            
            if min_amount < 0 or max_amount < 0:
                raise ValidationException(
                    message="Invalid amount range",
                    field_errors=[FieldError(
                        field="amount_range",
                        message="Amount range values cannot be negative",
                        code="NEGATIVE_AMOUNT_RANGE",
                        value=f"min: {min_amount}, max: {max_amount}"
                    )]
                )


# Global helper instance
query_helper = QueryParameterHelper()