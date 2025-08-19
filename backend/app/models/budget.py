"""
Budget Analysis Models for FinGood Financial Platform

This module provides comprehensive budget tracking, analysis, and forecasting models.
Integrates with the existing transaction and forecasting systems to provide intelligent
budget management with variance analysis and predictive insights.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime, date
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Dict, Any, Optional, List


class BudgetType(PyEnum):
    """Types of budgets supported by the system."""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    PROJECT = "project"
    GOAL_BASED = "goal_based"


class BudgetStatus(PyEnum):
    """Budget status lifecycle."""
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    ARCHIVED = "archived"


class VarianceType(PyEnum):
    """Types of budget variance analysis."""
    FAVORABLE = "favorable"  # Under budget for expenses, over budget for income
    UNFAVORABLE = "unfavorable"  # Over budget for expenses, under budget for income
    ON_TARGET = "on_target"  # Within acceptable variance threshold


class Budget(Base):
    """
    Main budget entity supporting various budget types and periods.
    
    Features:
    - Flexible time periods (monthly, quarterly, annual, project-based)
    - Category-based budget allocation
    - Integration with forecasting engine
    - Variance tracking and analysis
    - Goal-based budgeting support
    """
    __tablename__ = "budgets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Budget identification
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    budget_type = Column(Enum(BudgetType), nullable=False, default=BudgetType.MONTHLY)
    status = Column(Enum(BudgetStatus), nullable=False, default=BudgetStatus.DRAFT)
    
    # Time period
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    # Budget totals
    total_income_budget = Column(Float, nullable=False, default=0.0)
    total_expense_budget = Column(Float, nullable=False, default=0.0)
    
    # Variance thresholds (percentage)
    warning_threshold = Column(Float, default=0.85)  # 85% of budget used
    critical_threshold = Column(Float, default=1.0)  # 100% of budget used
    
    # Configuration
    auto_rollover = Column(Boolean, default=False)  # Roll unused budget to next period
    include_in_forecasting = Column(Boolean, default=True)
    
    # Metadata
    created_from_template = Column(String(100), nullable=True)  # Template ID if created from template
    tags = Column(JSON, nullable=True)  # User-defined tags for organization
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="budgets")
    budget_items = relationship("BudgetItem", back_populates="budget", cascade="all, delete-orphan")
    budget_actuals = relationship("BudgetActual", back_populates="budget", cascade="all, delete-orphan")
    variance_reports = relationship("BudgetVarianceReport", back_populates="budget", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Budget(id={self.id}, name='{self.name}', type={self.budget_type.value})>"


class BudgetItem(Base):
    """
    Individual budget line items by category/subcategory.
    
    Features:
    - Category-based budget allocation
    - Income vs expense classification
    - Monthly breakdown for longer periods
    - Integration with forecasting models
    """
    __tablename__ = "budget_items"
    
    id = Column(Integer, primary_key=True, index=True)
    budget_id = Column(Integer, ForeignKey("budgets.id"), nullable=False)
    
    # Categorization (matches transaction categories)
    category = Column(String(100), nullable=False)
    subcategory = Column(String(100), nullable=True)
    is_income = Column(Boolean, default=False)
    
    # Budget amounts
    budgeted_amount = Column(Float, nullable=False)
    monthly_breakdown = Column(JSON, nullable=True)  # For quarterly/annual budgets
    
    # Forecasting integration
    use_historical_data = Column(Boolean, default=True)
    forecast_method = Column(String(50), default="prophet")  # "prophet", "linear", "manual"
    forecast_confidence = Column(Float, nullable=True)
    
    # Notes and metadata
    notes = Column(Text, nullable=True)
    priority = Column(Integer, default=1)  # 1=High, 2=Medium, 3=Low
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    budget = relationship("Budget", back_populates="budget_items")
    
    def __repr__(self):
        return f"<BudgetItem(id={self.id}, category='{self.category}', amount={self.budgeted_amount})>"


class BudgetActual(Base):
    """
    Tracks actual spending/income against budget items.
    
    Features:
    - Real-time tracking of actual vs budgeted amounts
    - Period-based aggregation (daily, weekly, monthly)
    - Integration with transaction data
    - Variance calculation and analysis
    """
    __tablename__ = "budget_actuals"
    
    id = Column(Integer, primary_key=True, index=True)
    budget_id = Column(Integer, ForeignKey("budgets.id"), nullable=False)
    
    # Period tracking
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Categorization (matches budget items)
    category = Column(String(100), nullable=False)
    subcategory = Column(String(100), nullable=True)
    is_income = Column(Boolean, default=False)
    
    # Actual amounts
    actual_amount = Column(Float, nullable=False, default=0.0)
    transaction_count = Column(Integer, default=0)
    
    # Variance calculation
    budgeted_amount = Column(Float, nullable=False)
    variance_amount = Column(Float, nullable=False)  # actual - budgeted
    variance_percentage = Column(Float, nullable=False)  # (variance / budgeted) * 100
    variance_type = Column(Enum(VarianceType), nullable=False)
    
    # Metadata
    last_transaction_date = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    budget = relationship("Budget", back_populates="budget_actuals")
    
    def __repr__(self):
        return f"<BudgetActual(id={self.id}, category='{self.category}', variance={self.variance_percentage:.1f}%)>"


class BudgetVarianceReport(Base):
    """
    Comprehensive variance analysis reports.
    
    Features:
    - Period-based variance analysis
    - Trend identification
    - Predictive variance forecasting
    - Alert generation for significant variances
    """
    __tablename__ = "budget_variance_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    budget_id = Column(Integer, ForeignKey("budgets.id"), nullable=False)
    
    # Report period
    report_date = Column(DateTime, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Overall variance summary
    total_income_budgeted = Column(Float, nullable=False, default=0.0)
    total_income_actual = Column(Float, nullable=False, default=0.0)
    total_expense_budgeted = Column(Float, nullable=False, default=0.0)
    total_expense_actual = Column(Float, nullable=False, default=0.0)
    
    # Net variance
    net_variance_amount = Column(Float, nullable=False)
    net_variance_percentage = Column(Float, nullable=False)
    
    # Detailed analysis
    category_variances = Column(JSON, nullable=True)  # Detailed breakdown by category
    trend_analysis = Column(JSON, nullable=True)  # Variance trends over time
    forecast_accuracy = Column(JSON, nullable=True)  # How accurate were forecasts
    
    # Alerts and recommendations
    variance_alerts = Column(JSON, nullable=True)  # Generated alerts
    recommendations = Column(JSON, nullable=True)  # AI-generated recommendations
    
    # Report metadata
    generated_by = Column(String(50), default="system")  # "system", "user", "scheduled"
    report_type = Column(String(50), default="standard")  # "standard", "detailed", "summary"
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    budget = relationship("Budget", back_populates="variance_reports")
    
    def __repr__(self):
        return f"<BudgetVarianceReport(id={self.id}, variance={self.net_variance_percentage:.1f}%)>"


class BudgetTemplate(Base):
    """
    Reusable budget templates for common scenarios.
    
    Features:
    - Pre-configured budget structures
    - Industry-specific templates
    - Personal budget templates
    - Sharing and community templates
    """
    __tablename__ = "budget_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    creator_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Template identification
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)  # "business", "personal", "project"
    industry = Column(String(100), nullable=True)  # For business templates
    
    # Template configuration
    template_data = Column(JSON, nullable=False)  # Budget structure and items
    budget_type = Column(Enum(BudgetType), nullable=False)
    
    # Sharing and usage
    is_public = Column(Boolean, default=False)
    is_system = Column(Boolean, default=False)  # System-provided templates
    usage_count = Column(Integer, default=0)
    rating = Column(Float, nullable=True)  # User ratings
    
    # Metadata
    tags = Column(JSON, nullable=True)
    version = Column(String(20), default="1.0")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    creator = relationship("User")
    
    def __repr__(self):
        return f"<BudgetTemplate(id={self.id}, name='{self.name}', category='{self.category}')>"


class BudgetGoal(Base):
    """
    Goal-based budgeting for specific financial objectives.
    
    Features:
    - Savings goals with target dates
    - Debt reduction goals
    - Investment goals
    - Progress tracking and forecasting
    """
    __tablename__ = "budget_goals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    budget_id = Column(Integer, ForeignKey("budgets.id"), nullable=True)  # Optional link to budget
    
    # Goal identification
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    goal_type = Column(String(50), nullable=False)  # "savings", "debt_reduction", "investment"
    
    # Goal parameters
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    target_date = Column(DateTime, nullable=False)
    
    # Progress tracking
    monthly_contribution = Column(Float, nullable=True)
    progress_percentage = Column(Float, default=0.0)
    projected_completion_date = Column(DateTime, nullable=True)
    
    # Configuration
    auto_adjust = Column(Boolean, default=True)  # Auto-adjust contributions based on progress
    priority = Column(Integer, default=1)  # Goal priority
    
    # Status
    status = Column(String(50), default="active")  # "active", "completed", "paused"
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    budget = relationship("Budget")
    
    def __repr__(self):
        return f"<BudgetGoal(id={self.id}, name='{self.name}', progress={self.progress_percentage:.1f}%)>"