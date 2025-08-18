from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import re

class CategoryBase(BaseModel):
    name: str
    parent_category: Optional[str] = None
    color: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    user_id: int
    is_default: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class RuleBase(BaseModel):
    pattern: str = Field(..., min_length=1, max_length=255, description="Pattern to match against")
    pattern_type: str = Field(..., description="Type of pattern matching")
    category: str = Field(..., min_length=1, max_length=100, description="Target category")
    subcategory: Optional[str] = Field(None, max_length=100, description="Target subcategory")
    priority: int = Field(1, ge=1, le=100, description="Rule priority (1-100)")
    
    @validator('pattern_type')
    def validate_pattern_type(cls, v):
        allowed_types = ['regex', 'keyword', 'vendor', 'exact', 'contains']
        if v not in allowed_types:
            raise ValueError(f'pattern_type must be one of {allowed_types}')
        return v
    
    @validator('pattern')
    def validate_pattern(cls, v, values):
        if 'pattern_type' in values and values['pattern_type'] == 'regex':
            try:
                re.compile(v)
            except re.error:
                raise ValueError('Invalid regex pattern')
        return v

class RuleCreate(RuleBase):
    is_active: bool = True

class RuleUpdate(BaseModel):
    pattern: Optional[str] = Field(None, min_length=1, max_length=255)
    pattern_type: Optional[str] = None
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    priority: Optional[int] = Field(None, ge=1, le=100)
    is_active: Optional[bool] = None
    
    @validator('pattern_type')
    def validate_pattern_type(cls, v):
        if v is not None:
            allowed_types = ['regex', 'keyword', 'vendor', 'exact', 'contains']
            if v not in allowed_types:
                raise ValueError(f'pattern_type must be one of {allowed_types}')
        return v
    
    @validator('pattern')
    def validate_pattern(cls, v, values):
        if v is not None and 'pattern_type' in values and values['pattern_type'] == 'regex':
            try:
                re.compile(v)
            except re.error:
                raise ValueError('Invalid regex pattern')
        return v

class RuleResponse(RuleBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Pagination schema
class RuleListResponse(BaseModel):
    rules: List[RuleResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool

# Rule testing schemas
class RuleTestRequest(BaseModel):
    pattern: str = Field(..., min_length=1, max_length=255)
    pattern_type: str = Field(..., description="Type of pattern matching")
    test_description: Optional[str] = Field(None, description="Test against specific description")
    test_vendor: Optional[str] = Field(None, description="Test against specific vendor")
    limit: int = Field(10, ge=1, le=100, description="Max number of matching transactions to return")
    
    @validator('pattern_type')
    def validate_pattern_type(cls, v):
        allowed_types = ['regex', 'keyword', 'vendor', 'exact', 'contains']
        if v not in allowed_types:
            raise ValueError(f'pattern_type must be one of {allowed_types}')
        return v

class TransactionMatch(BaseModel):
    id: int
    description: str
    vendor: Optional[str]
    amount: float
    date: datetime
    current_category: Optional[str]
    current_subcategory: Optional[str]
    confidence: float

class RuleTestResponse(BaseModel):
    pattern: str
    pattern_type: str
    matches_found: int
    total_transactions: int
    match_rate: float
    sample_matches: List[TransactionMatch]
    potential_conflicts: List[Dict[str, Any]]

# Bulk operations schemas
class BulkRuleCreate(BaseModel):
    rules: List[RuleCreate] = Field(..., min_items=1, max_items=100)

class BulkRuleUpdate(BaseModel):
    rule_updates: List[Dict[str, Any]] = Field(..., min_items=1, max_items=100)

class BulkOperationResponse(BaseModel):
    successful: int
    failed: int
    errors: List[Dict[str, str]]
    created_rules: List[RuleResponse] = []
    updated_rules: List[RuleResponse] = []

# Rule performance analytics schemas
class RulePerformance(BaseModel):
    rule_id: int
    rule_pattern: str
    rule_category: str
    matches_count: int
    accuracy_rate: float
    last_match_date: Optional[datetime]
    effectiveness_score: float

class PerformanceAnalytics(BaseModel):
    total_rules: int
    active_rules: int
    inactive_rules: int
    total_matches: int
    average_accuracy: float
    top_performing_rules: List[RulePerformance]
    underperforming_rules: List[RulePerformance]
    category_distribution: Dict[str, int]

# Rule validation schemas
class RuleValidationResult(BaseModel):
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    conflicts: List[Dict[str, Any]] = []
    estimated_matches: int = 0

class RuleConflictInfo(BaseModel):
    conflicting_rule_id: int
    conflicting_pattern: str
    conflict_type: str  # 'duplicate', 'overlap', 'priority_conflict'
    severity: str  # 'low', 'medium', 'high'
    description: str

# Import/Export schemas
class RuleExportResponse(BaseModel):
    rules: List[Dict[str, Any]]
    export_date: datetime
    total_rules: int
    metadata: Dict[str, Any]

class RuleImportRequest(BaseModel):
    rules: List[Dict[str, Any]]
    overwrite_existing: bool = False
    validate_only: bool = False

class RuleImportResponse(BaseModel):
    imported_count: int
    skipped_count: int
    error_count: int
    validation_results: List[RuleValidationResult]
    imported_rules: List[RuleResponse] = []

# Rule templates
class RuleTemplate(BaseModel):
    name: str
    description: str
    category: str
    rules: List[RuleCreate]
    tags: List[str] = []

class RuleTemplateResponse(BaseModel):
    templates: List[RuleTemplate]
    categories: List[str]
