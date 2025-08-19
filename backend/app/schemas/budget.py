"""
Budget Analysis Schemas for FinGood Financial Platform

This module provides comprehensive Pydantic schemas for budget management,
analysis, and forecasting. Includes request/response models and validation
for all budget-related operations.
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class BudgetType(str, Enum):
    """Types of budgets supported by the system."""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    PROJECT = "project"
    GOAL_BASED = "goal_based"


class BudgetStatus(str, Enum):
    """Budget status lifecycle."""
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    ARCHIVED = "archived"


class VarianceType(str, Enum):
    """Types of budget variance analysis."""
    FAVORABLE = "favorable"
    UNFAVORABLE = "unfavorable"
    ON_TARGET = "on_target"


class ForecastMethod(str, Enum):
    """Forecasting methods for budget predictions."""
    PROPHET = "prophet"
    LINEAR = "linear"
    MANUAL = "manual"
    HISTORICAL_AVERAGE = "historical_average"


# Base Schemas
class BudgetItemBase(BaseModel):
    """Base schema for budget items."""
    category: str = Field(..., min_length=1, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    is_income: bool = False
    budgeted_amount: float = Field(..., gt=0)
    use_historical_data: bool = True
    forecast_method: ForecastMethod = ForecastMethod.PROPHET
    notes: Optional[str] = None
    priority: int = Field(default=1, ge=1, le=3)


class BudgetItemCreate(BudgetItemBase):
    """Schema for creating budget items."""
    monthly_breakdown: Optional[Dict[str, float]] = None


class BudgetItemUpdate(BaseModel):
    """Schema for updating budget items."""
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    is_income: Optional[bool] = None
    budgeted_amount: Optional[float] = Field(None, gt=0)
    use_historical_data: Optional[bool] = None
    forecast_method: Optional[ForecastMethod] = None
    notes: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=3)
    monthly_breakdown: Optional[Dict[str, float]] = None


class BudgetItemResponse(BudgetItemBase):
    """Schema for budget item responses."""
    id: int
    budget_id: int
    monthly_breakdown: Optional[Dict[str, float]] = None
    forecast_confidence: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BudgetBase(BaseModel):
    """Base schema for budgets."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    budget_type: BudgetType = BudgetType.MONTHLY
    start_date: datetime
    end_date: datetime
    warning_threshold: float = Field(default=0.85, ge=0.1, le=1.0)
    critical_threshold: float = Field(default=1.0, ge=0.1, le=2.0)
    auto_rollover: bool = False
    include_in_forecasting: bool = True

    @validator('end_date')
    def end_date_must_be_after_start_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v

    @validator('critical_threshold')
    def critical_must_be_gte_warning(cls, v, values):
        if 'warning_threshold' in values and v < values['warning_threshold']:
            raise ValueError('critical_threshold must be >= warning_threshold')
        return v


class BudgetCreate(BudgetBase):
    """Schema for creating budgets."""
    budget_items: List[BudgetItemCreate] = []
    created_from_template: Optional[str] = None
    tags: Optional[List[str]] = None


class BudgetUpdate(BaseModel):
    """Schema for updating budgets."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[BudgetStatus] = None
    warning_threshold: Optional[float] = Field(None, ge=0.1, le=1.0)
    critical_threshold: Optional[float] = Field(None, ge=0.1, le=2.0)
    auto_rollover: Optional[bool] = None
    include_in_forecasting: Optional[bool] = None
    tags: Optional[List[str]] = None


class BudgetResponse(BudgetBase):
    """Schema for budget responses."""
    id: int
    user_id: int
    status: BudgetStatus
    total_income_budget: float
    total_expense_budget: float
    created_from_template: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    budget_items: List[BudgetItemResponse] = []

    class Config:
        from_attributes = True


# Budget Analysis Schemas
class BudgetActualBase(BaseModel):
    """Base schema for budget actuals."""
    category: str
    subcategory: Optional[str] = None
    is_income: bool = False
    actual_amount: float
    transaction_count: int = 0


class BudgetActualResponse(BudgetActualBase):
    """Schema for budget actual responses."""
    id: int
    budget_id: int
    period_start: datetime
    period_end: datetime
    budgeted_amount: float
    variance_amount: float
    variance_percentage: float
    variance_type: VarianceType
    last_transaction_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CategoryVariance(BaseModel):
    """Schema for category-level variance analysis."""
    category: str
    subcategory: Optional[str] = None
    budgeted: float
    actual: float
    variance_amount: float
    variance_percentage: float
    variance_type: VarianceType
    transaction_count: int
    trend: Optional[str] = None  # "improving", "worsening", "stable"


class BudgetVarianceAnalysis(BaseModel):
    """Comprehensive budget variance analysis."""
    budget_id: int
    period_start: datetime
    period_end: datetime
    
    # Overall summary
    total_income_budgeted: float
    total_income_actual: float
    total_expense_budgeted: float
    total_expense_actual: float
    net_variance_amount: float
    net_variance_percentage: float
    
    # Category breakdown
    category_variances: List[CategoryVariance]
    
    # Analysis insights
    over_budget_categories: List[str]
    under_budget_categories: List[str]
    warning_categories: List[str]  # Categories approaching limits
    critical_categories: List[str]  # Categories over limits
    
    # Recommendations
    recommendations: List[str]
    forecast_accuracy: Optional[Dict[str, float]] = None


# Budget Templates
class BudgetTemplateBase(BaseModel):
    """Base schema for budget templates."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: str = Field(..., min_length=1, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    budget_type: BudgetType
    is_public: bool = False
    tags: Optional[List[str]] = None


class BudgetTemplateCreate(BudgetTemplateBase):
    """Schema for creating budget templates."""
    template_data: Dict[str, Any]  # Budget structure and items


class BudgetTemplateResponse(BudgetTemplateBase):
    """Schema for budget template responses."""
    id: int
    creator_user_id: int
    template_data: Dict[str, Any]
    is_system: bool
    usage_count: int
    rating: Optional[float] = None
    version: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Budget Goals
class BudgetGoalBase(BaseModel):
    """Base schema for budget goals."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    goal_type: str = Field(..., pattern="^(savings|debt_reduction|investment)$")
    target_amount: float = Field(..., gt=0)
    target_date: datetime
    monthly_contribution: Optional[float] = Field(None, gt=0)
    auto_adjust: bool = True
    priority: int = Field(default=1, ge=1, le=5)


class BudgetGoalCreate(BudgetGoalBase):
    """Schema for creating budget goals."""
    budget_id: Optional[int] = None


class BudgetGoalUpdate(BaseModel):
    """Schema for updating budget goals."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    target_amount: Optional[float] = Field(None, gt=0)
    target_date: Optional[datetime] = None
    monthly_contribution: Optional[float] = Field(None, gt=0)
    auto_adjust: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    status: Optional[str] = Field(None, pattern="^(active|completed|paused)$")


class BudgetGoalResponse(BudgetGoalBase):
    """Schema for budget goal responses."""
    id: int
    user_id: int
    budget_id: Optional[int] = None
    current_amount: float
    progress_percentage: float
    projected_completion_date: Optional[datetime] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Budget Analytics and Reporting
class BudgetSummary(BaseModel):
    """High-level budget summary."""
    total_budgets: int
    active_budgets: int
    total_budgeted_income: float
    total_budgeted_expenses: float
    total_actual_income: float
    total_actual_expenses: float
    overall_variance_percentage: float
    categories_over_budget: int
    categories_on_track: int


class BudgetForecast(BaseModel):
    """Budget forecasting results."""
    budget_id: int
    forecast_period: str  # "next_month", "next_quarter", etc.
    forecasted_income: float
    forecasted_expenses: float
    predicted_variance: float
    confidence_level: float
    risk_factors: List[str]
    recommendations: List[str]


class BudgetPerformanceMetrics(BaseModel):
    """Budget performance metrics."""
    accuracy_score: float  # How accurate have forecasts been
    variance_stability: float  # How stable are variances over time
    budget_adherence_rate: float  # % of categories within budget
    forecasting_improvement: float  # Trend in forecasting accuracy
    user_engagement_score: float  # How actively user manages budget


# Request/Response Models for API endpoints
class BudgetListRequest(BaseModel):
    """Request parameters for listing budgets."""
    status: Optional[BudgetStatus] = None
    budget_type: Optional[BudgetType] = None
    include_archived: bool = False
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class BudgetAnalysisRequest(BaseModel):
    """Request for budget analysis."""
    budget_id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_forecasting: bool = True
    detailed_breakdown: bool = False


class BulkBudgetItemUpdate(BaseModel):
    """Schema for bulk updating budget items."""
    item_updates: List[Dict[str, Any]]  # List of {id: int, updates: BudgetItemUpdate}


class BudgetComparisonRequest(BaseModel):
    """Request for comparing budgets."""
    budget_ids: List[int] = Field(..., min_items=2, max_items=5)
    comparison_period: Optional[str] = "month"  # "month", "quarter", "year"


class BudgetComparisonResponse(BaseModel):
    """Response for budget comparison."""
    budgets: List[BudgetResponse]
    comparison_metrics: Dict[str, Any]
    variance_comparison: Dict[str, List[float]]
    performance_ranking: List[Dict[str, Any]]