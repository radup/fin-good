from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

from app.core.security_utils import input_sanitizer


class ExportFormat(str, Enum):
    """Supported export formats."""
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"


class ExportStatus(str, Enum):
    """Export job statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExportFilterParams(BaseModel):
    """Enhanced filter parameters for exports with security validation."""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    # Date range filters
    from_date: Optional[date] = Field(
        None,
        description="Start date for export (inclusive)"
    )
    to_date: Optional[date] = Field(
        None,
        description="End date for export (inclusive)"
    )
    
    # Category filters
    categories: Optional[List[str]] = Field(
        None,
        max_items=50,
        description="List of categories to include"
    )
    subcategories: Optional[List[str]] = Field(
        None,
        max_items=100,
        description="List of subcategories to include"
    )
    
    # Amount filters
    min_amount: Optional[Decimal] = Field(
        None,
        ge=Decimal('-999999999.99'),
        le=Decimal('999999999.99'),
        description="Minimum transaction amount"
    )
    max_amount: Optional[Decimal] = Field(
        None,
        ge=Decimal('-999999999.99'),
        le=Decimal('999999999.99'),
        description="Maximum transaction amount"
    )
    
    # Transaction type filters
    is_income: Optional[bool] = Field(
        None,
        description="Filter by income/expense type"
    )
    is_categorized: Optional[bool] = Field(
        None,
        description="Filter by categorization status"
    )
    
    # Text filters (with security sanitization)
    vendor_contains: Optional[str] = Field(
        None,
        max_length=200,
        description="Filter by vendor name (partial match)"
    )
    description_contains: Optional[str] = Field(
        None,
        max_length=500,
        description="Filter by description (partial match)"
    )
    
    # Import batch filter
    import_batch: Optional[str] = Field(
        None,
        max_length=255,
        description="Filter by import batch ID"
    )
    
    @field_validator('from_date')
    @classmethod
    def validate_from_date(cls, v):
        """Validate from_date parameter."""
        if v is None:
            return v
        
        # Check for reasonable date range (no more than 10 years)
        max_past_date = date.today() - timedelta(days=3650)  # 10 years
        max_future_date = date.today() + timedelta(days=365)  # 1 year future
        
        if v < max_past_date:
            raise ValueError("Date cannot be more than 10 years in the past")
        if v > max_future_date:
            raise ValueError("Date cannot be more than 1 year in the future")
        
        return v
    
    @field_validator('to_date')
    @classmethod
    def validate_to_date(cls, v):
        """Validate to_date parameter."""
        if v is None:
            return v
        
        # Check for reasonable date range (no more than 10 years)
        max_past_date = date.today() - timedelta(days=3650)  # 10 years
        max_future_date = date.today() + timedelta(days=365)  # 1 year future
        
        if v < max_past_date:
            raise ValueError("Date cannot be more than 10 years in the past")
        if v > max_future_date:
            raise ValueError("Date cannot be more than 1 year in the future")
        
        return v
    
    @model_validator(mode='after')
    def validate_date_range_consistency(self):
        """Validate that from_date is not after to_date."""
        if self.from_date and self.to_date and self.from_date > self.to_date:
            raise ValueError("from_date cannot be after to_date")
        return self
    
    @field_validator('categories', 'subcategories')
    @classmethod
    def validate_category_lists(cls, v):
        """Validate and sanitize category lists."""
        if v is None:
            return v
        
        sanitized = []
        for category in v:
            if not category or not category.strip():
                continue
            
            sanitized_category = input_sanitizer.sanitize_financial_input(
                category.strip(),
                field_name="category",
                max_length=100,
                remove_pii=False
            )
            if sanitized_category:
                sanitized.append(sanitized_category)
        
        return sanitized if sanitized else None
    
    @field_validator('vendor_contains', 'description_contains')
    @classmethod
    def validate_text_filters(cls, v):
        """Validate and sanitize text filter parameters."""
        if v is None:
            return v
        
        return input_sanitizer.sanitize_financial_input(
            v.strip(),
            field_name="search_filter",
            max_length=500,
            remove_pii=True
        )
    
    @field_validator('min_amount', 'max_amount')
    @classmethod
    def validate_amount_range(cls, v):
        """Validate amount range parameters."""
        if v is None:
            return v
        
        if isinstance(v, (int, float)):
            v = Decimal(str(v))
        
        from decimal import ROUND_HALF_UP
        return v.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


class ExportColumnsConfig(BaseModel):
    """Configuration for which columns to include in export."""
    
    # Core transaction fields
    include_id: bool = Field(default=True, description="Include transaction ID")
    include_date: bool = Field(default=True, description="Include transaction date")
    include_amount: bool = Field(default=True, description="Include transaction amount")
    include_description: bool = Field(default=True, description="Include description")
    include_vendor: bool = Field(default=True, description="Include vendor")
    
    # Categorization fields
    include_category: bool = Field(default=True, description="Include category")
    include_subcategory: bool = Field(default=True, description="Include subcategory")
    include_is_income: bool = Field(default=True, description="Include income flag")
    
    # Processing fields
    include_source: bool = Field(default=False, description="Include data source")
    include_import_batch: bool = Field(default=False, description="Include import batch")
    include_is_categorized: bool = Field(default=False, description="Include categorization status")
    include_confidence_score: bool = Field(default=False, description="Include AI confidence score")
    
    # Timestamps
    include_created_at: bool = Field(default=False, description="Include creation timestamp")
    include_updated_at: bool = Field(default=False, description="Include update timestamp")
    
    # Additional data
    include_raw_data: bool = Field(default=False, description="Include raw import data")
    include_meta_data: bool = Field(default=False, description="Include metadata")


class ExportOptionsConfig(BaseModel):
    """Advanced export configuration options."""
    
    # File options
    compress_output: bool = Field(default=False, description="Compress output file (for large exports)")
    include_summary_sheet: bool = Field(default=True, description="Include summary sheet (Excel only)")
    include_category_breakdown: bool = Field(default=True, description="Include category breakdown (Excel only)")
    
    # CSV options
    csv_delimiter: Literal[",", ";", "\t"] = Field(default=",", description="CSV field delimiter")
    csv_quote_char: Literal['"', "'"] = Field(default='"', description="CSV quote character")
    csv_include_bom: bool = Field(default=False, description="Include BOM for UTF-8 CSV")
    
    # Data formatting
    date_format: Literal["YYYY-MM-DD", "MM/DD/YYYY", "DD/MM/YYYY", "DD-MM-YYYY"] = Field(
        default="YYYY-MM-DD",
        description="Date format for export"
    )
    currency_symbol: Optional[str] = Field(
        None,
        max_length=5,
        description="Currency symbol to include in amounts"
    )
    decimal_places: Literal[2, 3, 4] = Field(default=2, description="Number of decimal places for amounts")
    
    # Security options
    anonymize_vendor_names: bool = Field(default=False, description="Replace vendor names with generic labels")
    mask_amounts: bool = Field(default=False, description="Partially mask transaction amounts")


class ExportRequest(BaseModel):
    """Request model for custom export with comprehensive filtering."""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    export_format: ExportFormat = Field(..., description="Export format")
    filters: Optional[ExportFilterParams] = Field(None, description="Export filters")
    columns: Optional[ExportColumnsConfig] = Field(None, description="Column configuration")
    options: Optional[ExportOptionsConfig] = Field(None, description="Export options")
    
    # Export metadata
    export_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Custom name for the export"
    )
    
    @field_validator('export_name')
    @classmethod
    def validate_export_name(cls, v):
        """Validate and sanitize export name."""
        if v is None:
            return v
        
        return input_sanitizer.sanitize_financial_input(
            v.strip(),
            field_name="export_name",
            max_length=100,
            remove_pii=True
        )


class ExportJobResponse(BaseModel):
    """Response for export job creation."""
    
    job_id: str = Field(..., description="Unique export job identifier")
    status: ExportStatus = Field(..., description="Current job status")
    estimated_records: int = Field(..., description="Estimated number of records to export")
    estimated_completion_time: Optional[datetime] = Field(
        None,
        description="Estimated completion time"
    )
    download_url: Optional[str] = Field(None, description="Download URL when completed")
    created_at: datetime = Field(..., description="Job creation timestamp")
    message: Optional[str] = Field(None, description="Status message")


class ExportProgress(BaseModel):
    """Export progress information."""
    
    job_id: str = Field(..., description="Export job identifier")
    status: ExportStatus = Field(..., description="Current status")
    progress_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Completion percentage"
    )
    records_processed: int = Field(..., description="Number of records processed")
    total_records: int = Field(..., description="Total number of records to process")
    current_operation: str = Field(..., description="Current operation description")
    started_at: datetime = Field(..., description="Job start timestamp")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class ExportSummary(BaseModel):
    """Summary information for completed export."""
    
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    total_records: int = Field(..., description="Total records exported")
    file_size_bytes: int = Field(..., description="Export file size in bytes")
    export_format: ExportFormat = Field(..., description="Export format used")
    date_range: Dict[str, Optional[date]] = Field(..., description="Date range of exported data")
    
    # Financial summary
    total_income: Decimal = Field(..., description="Total income in export")
    total_expenses: Decimal = Field(..., description="Total expenses in export")
    net_amount: Decimal = Field(..., description="Net amount (income - expenses)")
    
    # Category breakdown
    categories_included: int = Field(..., description="Number of categories in export")
    category_breakdown: Dict[str, Decimal] = Field(..., description="Amount by category")
    
    # Processing info
    processing_time_seconds: float = Field(..., description="Time taken to process export")
    compression_ratio: Optional[float] = Field(None, description="Compression ratio if compressed")
    
    @field_validator('total_income', 'total_expenses', 'net_amount')
    @classmethod
    def validate_amounts(cls, v):
        """Validate financial amounts."""
        if isinstance(v, (int, float)):
            v = Decimal(str(v))
        
        from decimal import ROUND_HALF_UP
        return v.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @field_validator('category_breakdown')
    @classmethod
    def validate_category_breakdown(cls, v):
        """Validate category breakdown amounts."""
        if not isinstance(v, dict):
            return v
        
        validated = {}
        for category, amount in v.items():
            if isinstance(amount, (int, float)):
                amount = Decimal(str(amount))
            
            from decimal import ROUND_HALF_UP
            validated[category] = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return validated


class ExportHistoryEntry(BaseModel):
    """Historical export entry for user's export history."""
    
    job_id: str = Field(..., description="Export job identifier")
    export_name: Optional[str] = Field(None, description="Custom export name")
    export_format: ExportFormat = Field(..., description="Export format")
    status: ExportStatus = Field(..., description="Final status")
    
    # Metadata
    created_at: datetime = Field(..., description="Export creation time")
    completed_at: Optional[datetime] = Field(None, description="Export completion time")
    expires_at: Optional[datetime] = Field(None, description="Download expiration time")
    
    # Summary info
    total_records: int = Field(..., description="Total records exported")
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes")
    download_count: int = Field(default=0, description="Number of times downloaded")
    
    # URLs
    download_url: Optional[str] = Field(None, description="Download URL if available")
    
    # Error info
    error_message: Optional[str] = Field(None, description="Error message if failed")