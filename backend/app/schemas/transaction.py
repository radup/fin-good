from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Dict, Any, Union
from datetime import datetime
from decimal import Decimal

from app.core.financial_validators import FinancialAmount, TransactionType, CurrencyCode, TransactionValidator
from app.core.security_utils import input_sanitizer

class TransactionBase(BaseModel):
    """Base transaction model with enhanced validation for financial data"""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        json_encoders={Decimal: str}
    )
    
    date: datetime = Field(
        ...,
        description="Transaction date and time",
        examples=["2024-01-15T10:30:00Z"]
    )
    
    amount: Decimal = Field(
        ...,
        description="Transaction amount with financial precision",
        ge=Decimal('-999999999999.99'),
        le=Decimal('999999999999.99'),
        decimal_places=2,
        examples=[Decimal('123.45'), Decimal('-50.00')]
    )
    
    description: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Transaction description (sanitized for security)",
        examples=["Grocery Store Purchase", "ATM Withdrawal"]
    )
    
    vendor: Optional[str] = Field(
        None,
        max_length=200,
        description="Merchant or vendor name",
        examples=["Walmart", "Shell Gas Station"]
    )
    
    category: Optional[str] = Field(
        None,
        max_length=100,
        description="Transaction category",
        examples=["Food & Dining", "Transportation", "Income"]
    )
    
    subcategory: Optional[str] = Field(
        None,
        max_length=100,
        description="Transaction subcategory",
        examples=["Groceries", "Gas", "Salary"]
    )
    
    is_income: bool = Field(
        default=False,
        description="Whether this transaction represents income"
    )
    
    @field_validator('date')
    @classmethod
    def validate_transaction_date(cls, v):
        """Validate transaction date with business rules"""
        validator = TransactionValidator()
        return validator.validate_transaction_date(v)
    
    @field_validator('amount')
    @classmethod
    def validate_amount_precision(cls, v):
        """Validate amount with financial precision"""
        if isinstance(v, (int, float)):
            v = Decimal(str(v))
        elif isinstance(v, str):
            # Remove currency symbols and spaces
            import re
            cleaned = re.sub(r'[$€£¥,\s]', '', v)
            v = Decimal(cleaned)
        
        # Ensure proper precision (2 decimal places for most currencies)
        from decimal import ROUND_HALF_UP
        return v.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @field_validator('description')
    @classmethod
    def validate_and_sanitize_description(cls, v):
        """Sanitize description for security and PII protection"""
        if not v or not v.strip():
            raise ValueError("Description is required")
        
        # Sanitize using our security utilities
        return input_sanitizer.sanitize_financial_input(
            v.strip(),
            field_name="description",
            max_length=500,
            remove_pii=True
        )
    
    @field_validator('vendor')
    @classmethod
    def validate_and_sanitize_vendor(cls, v):
        """Sanitize vendor name"""
        if v is None:
            return v
        
        return input_sanitizer.sanitize_financial_input(
            v.strip(),
            field_name="vendor",
            max_length=200,
            remove_pii=True
        )
    
    @field_validator('category', 'subcategory')
    @classmethod
    def validate_and_sanitize_category(cls, v):
        """Sanitize category fields"""
        if v is None:
            return v
        
        return input_sanitizer.sanitize_financial_input(
            v.strip(),
            field_name="category",
            max_length=100,
            remove_pii=False  # Categories don't typically contain PII
        )

class TransactionCreate(TransactionBase):
    """Create transaction model with additional import metadata"""
    
    source: str = Field(
        default="csv",
        max_length=50,
        description="Source of transaction data",
        examples=["csv", "api", "manual", "bank_sync"]
    )
    
    source_id: Optional[str] = Field(
        None,
        max_length=255,
        description="External ID from source system"
    )
    
    import_batch: Optional[str] = Field(
        None,
        max_length=255,
        description="Batch identifier for bulk imports"
    )
    
    raw_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Original raw data from import source"
    )
    
    @field_validator('source')
    @classmethod
    def validate_source(cls, v):
        """Validate transaction source"""
        allowed_sources = ['csv', 'api', 'manual', 'bank_sync', 'qif', 'ofx']
        if v not in allowed_sources:
            raise ValueError(f"Source must be one of: {', '.join(allowed_sources)}")
        return v
    
    @field_validator('source_id', 'import_batch')
    @classmethod
    def validate_identifiers(cls, v):
        """Validate string identifiers"""
        if v is None:
            return v
        
        # Basic validation for identifiers
        import re
        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', v):
            raise ValueError("Identifier can only contain letters, numbers, hyphens, underscores, and dots")
        
        return v


class TransactionUpdate(BaseModel):
    """Update transaction model with validation"""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    category: Optional[str] = Field(
        None,
        max_length=100,
        description="Updated transaction category"
    )
    
    subcategory: Optional[str] = Field(
        None,
        max_length=100,
        description="Updated transaction subcategory"
    )
    
    create_rule: bool = Field(
        default=False,
        description="Whether to create categorization rule from this update"
    )
    
    @field_validator('category', 'subcategory')
    @classmethod
    def validate_and_sanitize_category_update(cls, v):
        """Sanitize category fields for updates"""
        if v is None:
            return v
        
        return input_sanitizer.sanitize_financial_input(
            v.strip(),
            field_name="category",
            max_length=100,
            remove_pii=False
        )

class TransactionResponse(TransactionBase):
    """Transaction response model with enhanced metadata"""
    
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        json_encoders={Decimal: str}
    )
    
    id: int = Field(..., description="Unique transaction ID")
    user_id: int = Field(..., description="Owner user ID")
    source: str = Field(..., description="Transaction data source")
    source_id: Optional[str] = Field(None, description="External source ID")
    import_batch: Optional[str] = Field(None, description="Import batch identifier")
    
    is_processed: bool = Field(..., description="Whether transaction has been processed")
    is_categorized: bool = Field(..., description="Whether transaction has been categorized")
    confidence_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Categorization confidence score (0-1)"
    )
    
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Original raw data")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    # Auto-categorization response fields
    auto_categorized_count: Optional[int] = Field(
        None,
        ge=0,
        description="Number of similar transactions auto-categorized"
    )
    new_rule_created: Optional[bool] = Field(
        None,
        description="Whether a new categorization rule was created"
    )


class TransactionSummary(BaseModel):
    """Transaction summary with financial aggregations"""
    
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    total_transactions: int = Field(
        ...,
        ge=0,
        description="Total number of transactions"
    )
    
    total_income: Decimal = Field(
        ...,
        description="Total income amount"
    )
    
    total_expenses: Decimal = Field(
        ...,
        description="Total expense amount"
    )
    
    categorized_count: int = Field(
        ...,
        ge=0,
        description="Number of categorized transactions"
    )
    
    uncategorized_count: int = Field(
        ...,
        ge=0,
        description="Number of uncategorized transactions"
    )
    
    categories: Dict[str, Decimal] = Field(
        ...,
        description="Category breakdown with amounts"
    )
    
    @field_validator('total_income', 'total_expenses')
    @classmethod
    def validate_summary_amounts(cls, v):
        """Validate summary amounts"""
        if isinstance(v, (int, float)):
            v = Decimal(str(v))
        
        from decimal import ROUND_HALF_UP
        return v.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @field_validator('categories')
    @classmethod
    def validate_category_amounts(cls, v):
        """Validate category amounts"""
        if not isinstance(v, dict):
            return v
        
        validated_categories = {}
        for category, amount in v.items():
            if isinstance(amount, (int, float)):
                amount = Decimal(str(amount))
            
            from decimal import ROUND_HALF_UP
            validated_categories[category] = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return validated_categories


class TransactionQueryParams(BaseModel):
    """Validated query parameters for transaction endpoints"""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    skip: int = Field(default=0, ge=0, le=10000, description="Number of records to skip")
    limit: int = Field(default=50, ge=1, le=1000, description="Number of records to return")
    
    category: Optional[str] = Field(None, max_length=100, description="Filter by category")
    subcategory: Optional[str] = Field(None, max_length=100, description="Filter by subcategory")
    vendor: Optional[str] = Field(None, max_length=200, description="Filter by vendor")
    description: Optional[str] = Field(None, max_length=500, description="Filter by description")
    
    start_date: Optional[datetime] = Field(None, description="Filter from this date")
    end_date: Optional[datetime] = Field(None, description="Filter until this date")
    
    is_income: Optional[bool] = Field(None, description="Filter by income/expense")
    is_categorized: Optional[bool] = Field(None, description="Filter by categorization status")
    
    min_amount: Optional[Decimal] = Field(None, description="Minimum amount filter")
    max_amount: Optional[Decimal] = Field(None, description="Maximum amount filter")
    
    sort_by: str = Field(
        default="date",
        description="Sort field",
        pattern="^(date|amount|description|vendor|category)$"
    )
    sort_order: str = Field(
        default="desc",
        description="Sort order",
        pattern="^(asc|desc)$"
    )
    
    @field_validator('category', 'subcategory', 'vendor', 'description')
    @classmethod
    def sanitize_filter_strings(cls, v):
        """Sanitize string filter parameters"""
        if v is None:
            return v
        
        return input_sanitizer.sanitize_financial_input(
            v.strip(),
            field_name="filter",
            max_length=500,
            remove_pii=False
        )
    
    @field_validator('min_amount', 'max_amount')
    @classmethod
    def validate_amount_filters(cls, v):
        """Validate amount filter parameters"""
        if v is None:
            return v
        
        if isinstance(v, (int, float)):
            v = Decimal(str(v))
        
        from decimal import ROUND_HALF_UP
        return v.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
