"""
Budget Management API endpoints for FinGood Financial Platform

This module provides comprehensive budget management capabilities including:
- Budget creation and management
- Variance analysis and reporting
- Budget forecasting with ML integration
- Goal-based budgeting
- Template management
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.cookie_auth import get_current_user_from_cookie
from app.core.audit_logger import security_audit_logger
from app.models.user import User
from app.models.budget import Budget, BudgetItem, BudgetStatus, BudgetType
from app.schemas.budget import (
    BudgetCreate, BudgetUpdate, BudgetResponse, BudgetListRequest,
    BudgetItemCreate, BudgetItemUpdate, BudgetItemResponse,
    BudgetVarianceAnalysis, BudgetAnalysisRequest, BudgetSummary,
    BudgetForecast, BudgetPerformanceMetrics, BudgetGoalCreate,
    BudgetGoalUpdate, BudgetGoalResponse, BudgetTemplateCreate,
    BudgetTemplateResponse, BudgetComparisonRequest, BudgetComparisonResponse
)
from app.services.budget_analyzer import BudgetAnalyzer

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=BudgetResponse)
async def create_budget(
    budget_data: BudgetCreate,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Create a new budget with optional items.
    
    Features:
    - Supports multiple budget types (monthly, quarterly, annual, project, goal-based)
    - Automatic total calculations
    - Integration with forecasting for intelligent defaults
    - Template-based creation support
    """
    try:
        # Create budget
        budget = Budget(
            user_id=current_user.id,
            name=budget_data.name,
            description=budget_data.description,
            budget_type=budget_data.budget_type,
            status=BudgetStatus.DRAFT,
            start_date=budget_data.start_date,
            end_date=budget_data.end_date,
            warning_threshold=budget_data.warning_threshold,
            critical_threshold=budget_data.critical_threshold,
            auto_rollover=budget_data.auto_rollover,
            include_in_forecasting=budget_data.include_in_forecasting,
            created_from_template=budget_data.created_from_template,
            tags=budget_data.tags or []
        )
        
        db.add(budget)
        db.flush()  # Get the budget ID
        
        # Create budget items
        total_income = 0.0
        total_expenses = 0.0
        
        for item_data in budget_data.budget_items:
            budget_item = BudgetItem(
                budget_id=budget.id,
                category=item_data.category,
                subcategory=item_data.subcategory,
                is_income=item_data.is_income,
                budgeted_amount=item_data.budgeted_amount,
                monthly_breakdown=item_data.monthly_breakdown,
                use_historical_data=item_data.use_historical_data,
                forecast_method=item_data.forecast_method.value,
                notes=item_data.notes,
                priority=item_data.priority
            )
            
            db.add(budget_item)
            
            # Update totals
            if item_data.is_income:
                total_income += item_data.budgeted_amount
            else:
                total_expenses += item_data.budgeted_amount
        
        # Update budget totals
        budget.total_income_budget = total_income
        budget.total_expense_budget = total_expenses
        
        db.commit()
        db.refresh(budget)
        
        # Log budget creation
        security_audit_logger.info(
            "Budget created",
            extra={
                "user_id": current_user.id,
                "budget_id": budget.id,
                "budget_name": budget.name,
                "budget_type": budget.budget_type.value,
                "total_income": total_income,
                "total_expenses": total_expenses
            }
        )
        
        logger.info(f"Budget created: {budget.name} (ID: {budget.id}) for user {current_user.id}")
        
        return budget
        
    except Exception as e:
        logger.error(f"Budget creation failed: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create budget"
        )


@router.get("/", response_model=List[BudgetResponse])
async def list_budgets(
    status_filter: Optional[BudgetStatus] = Query(None, alias="status"),
    budget_type: Optional[BudgetType] = Query(None),
    include_archived: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """
    List user's budgets with filtering and pagination.
    
    Features:
    - Filter by status, type, archived status
    - Pagination support
    - Includes budget items and summary statistics
    """
    try:
        query = db.query(Budget).filter(Budget.user_id == current_user.id)
        
        # Apply filters
        if status_filter:
            query = query.filter(Budget.status == status_filter)
        
        if budget_type:
            query = query.filter(Budget.budget_type == budget_type)
        
        if not include_archived:
            query = query.filter(Budget.status != BudgetStatus.ARCHIVED)
        
        # Apply pagination
        budgets = query.order_by(Budget.created_at.desc()).offset(offset).limit(limit).all()
        
        return budgets
        
    except Exception as e:
        logger.error(f"Budget listing failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve budgets"
        )


@router.get("/{budget_id}", response_model=BudgetResponse)
async def get_budget(
    budget_id: int,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Get detailed budget information including all items and statistics."""
    try:
        budget = db.query(Budget).filter(
            Budget.id == budget_id,
            Budget.user_id == current_user.id
        ).first()
        
        if not budget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Budget not found"
            )
        
        return budget
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Budget retrieval failed for budget {budget_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve budget"
        )


@router.put("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: int,
    budget_data: BudgetUpdate,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Update budget information and settings."""
    try:
        budget = db.query(Budget).filter(
            Budget.id == budget_id,
            Budget.user_id == current_user.id
        ).first()
        
        if not budget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Budget not found"
            )
        
        # Update fields if provided
        update_data = budget_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(budget, field, value)
        
        budget.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(budget)
        
        # Log budget update
        security_audit_logger.info(
            "Budget updated",
            extra={
                "user_id": current_user.id,
                "budget_id": budget.id,
                "updated_fields": list(update_data.keys())
            }
        )
        
        return budget
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Budget update failed for budget {budget_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update budget"
        )


@router.delete("/{budget_id}")
async def delete_budget(
    budget_id: int,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Delete a budget and all associated data."""
    try:
        budget = db.query(Budget).filter(
            Budget.id == budget_id,
            Budget.user_id == current_user.id
        ).first()
        
        if not budget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Budget not found"
            )
        
        budget_name = budget.name
        
        # Delete budget (cascade will handle related items)
        db.delete(budget)
        db.commit()
        
        # Log budget deletion
        security_audit_logger.info(
            "Budget deleted",
            extra={
                "user_id": current_user.id,
                "budget_id": budget_id,
                "budget_name": budget_name
            }
        )
        
        return {"message": f"Budget '{budget_name}' deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Budget deletion failed for budget {budget_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete budget"
        )


@router.post("/{budget_id}/items", response_model=BudgetItemResponse)
async def add_budget_item(
    budget_id: int,
    item_data: BudgetItemCreate,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Add a new item to an existing budget."""
    try:
        budget = db.query(Budget).filter(
            Budget.id == budget_id,
            Budget.user_id == current_user.id
        ).first()
        
        if not budget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Budget not found"
            )
        
        # Create budget item
        budget_item = BudgetItem(
            budget_id=budget_id,
            category=item_data.category,
            subcategory=item_data.subcategory,
            is_income=item_data.is_income,
            budgeted_amount=item_data.budgeted_amount,
            monthly_breakdown=item_data.monthly_breakdown,
            use_historical_data=item_data.use_historical_data,
            forecast_method=item_data.forecast_method.value,
            notes=item_data.notes,
            priority=item_data.priority
        )
        
        db.add(budget_item)
        
        # Update budget totals
        if item_data.is_income:
            budget.total_income_budget += item_data.budgeted_amount
        else:
            budget.total_expense_budget += item_data.budgeted_amount
        
        budget.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(budget_item)
        
        return budget_item
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Budget item creation failed: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add budget item"
        )


@router.put("/{budget_id}/items/{item_id}", response_model=BudgetItemResponse)
async def update_budget_item(
    budget_id: int,
    item_id: int,
    item_data: BudgetItemUpdate,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Update a budget item."""
    try:
        # Verify budget ownership
        budget = db.query(Budget).filter(
            Budget.id == budget_id,
            Budget.user_id == current_user.id
        ).first()
        
        if not budget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Budget not found"
            )
        
        # Get budget item
        budget_item = db.query(BudgetItem).filter(
            BudgetItem.id == item_id,
            BudgetItem.budget_id == budget_id
        ).first()
        
        if not budget_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Budget item not found"
            )
        
        # Store old amount for total recalculation
        old_amount = budget_item.budgeted_amount
        old_is_income = budget_item.is_income
        
        # Update fields
        update_data = item_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "forecast_method" and value:
                setattr(budget_item, field, value.value)
            else:
                setattr(budget_item, field, value)
        
        budget_item.updated_at = datetime.utcnow()
        
        # Update budget totals if amount or type changed
        if "budgeted_amount" in update_data or "is_income" in update_data:
            # Remove old amount
            if old_is_income:
                budget.total_income_budget -= old_amount
            else:
                budget.total_expense_budget -= old_amount
            
            # Add new amount
            if budget_item.is_income:
                budget.total_income_budget += budget_item.budgeted_amount
            else:
                budget.total_expense_budget += budget_item.budgeted_amount
            
            budget.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(budget_item)
        
        return budget_item
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Budget item update failed: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update budget item"
        )


@router.delete("/{budget_id}/items/{item_id}")
async def delete_budget_item(
    budget_id: int,
    item_id: int,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Delete a budget item."""
    try:
        # Verify budget ownership
        budget = db.query(Budget).filter(
            Budget.id == budget_id,
            Budget.user_id == current_user.id
        ).first()
        
        if not budget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Budget not found"
            )
        
        # Get budget item
        budget_item = db.query(BudgetItem).filter(
            BudgetItem.id == item_id,
            BudgetItem.budget_id == budget_id
        ).first()
        
        if not budget_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Budget item not found"
            )
        
        # Update budget totals
        if budget_item.is_income:
            budget.total_income_budget -= budget_item.budgeted_amount
        else:
            budget.total_expense_budget -= budget_item.budgeted_amount
        
        budget.updated_at = datetime.utcnow()
        
        # Delete item
        db.delete(budget_item)
        db.commit()
        
        return {"message": "Budget item deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Budget item deletion failed: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete budget item"
        )


@router.post("/{budget_id}/analyze", response_model=BudgetVarianceAnalysis)
async def analyze_budget_variance(
    budget_id: int,
    analysis_request: Optional[BudgetAnalysisRequest] = None,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Perform comprehensive budget variance analysis.
    
    Features:
    - Real-time actual vs budgeted comparison
    - Category-level variance breakdown
    - Trend analysis and alerts
    - Predictive insights
    """
    try:
        analyzer = BudgetAnalyzer(db)
        
        start_date = analysis_request.start_date if analysis_request else None
        end_date = analysis_request.end_date if analysis_request else None
        
        analysis = analyzer.analyze_budget_variance(
            budget_id=budget_id,
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date
        )
        
        return analysis
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Budget variance analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze budget variance"
        )


@router.get("/summary/overview", response_model=BudgetSummary)
async def get_budget_summary(
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Get high-level budget summary across all user budgets."""
    try:
        analyzer = BudgetAnalyzer(db)
        summary = analyzer.get_budget_summary(current_user.id)
        
        return summary
        
    except Exception as e:
        logger.error(f"Budget summary failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate budget summary"
        )


@router.post("/{budget_id}/forecast", response_model=BudgetForecast)
async def generate_budget_forecast(
    budget_id: int,
    forecast_period: str = Query("next_month", regex="^(next_month|next_quarter|next_year)$"),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Generate ML-powered budget forecast.
    
    Features:
    - Integration with forecasting engine
    - Confidence scoring
    - Risk factor identification
    - Actionable recommendations
    """
    try:
        analyzer = BudgetAnalyzer(db)
        
        forecast = analyzer.generate_budget_forecast(
            budget_id=budget_id,
            user_id=current_user.id,
            forecast_period=forecast_period
        )
        
        return forecast
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Budget forecast failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate budget forecast"
        )


@router.get("/performance/metrics", response_model=BudgetPerformanceMetrics)
async def get_performance_metrics(
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Get comprehensive budget performance metrics."""
    try:
        analyzer = BudgetAnalyzer(db)
        metrics = analyzer.calculate_performance_metrics(current_user.id)
        
        return metrics
        
    except Exception as e:
        logger.error(f"Performance metrics calculation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate performance metrics"
        )


@router.post("/{budget_id}/activate")
async def activate_budget(
    budget_id: int,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Activate a draft budget to start tracking."""
    try:
        budget = db.query(Budget).filter(
            Budget.id == budget_id,
            Budget.user_id == current_user.id
        ).first()
        
        if not budget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Budget not found"
            )
        
        if budget.status != BudgetStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only draft budgets can be activated"
            )
        
        budget.status = BudgetStatus.ACTIVE
        budget.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Log budget activation
        security_audit_logger.info(
            "Budget activated",
            extra={
                "user_id": current_user.id,
                "budget_id": budget_id,
                "budget_name": budget.name
            }
        )
        
        return {"message": f"Budget '{budget.name}' activated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Budget activation failed: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate budget"
        )


@router.post("/{budget_id}/copy", response_model=BudgetResponse)
async def copy_budget(
    budget_id: int,
    new_name: str = Query(..., min_length=1, max_length=200),
    copy_items: bool = Query(True),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Create a copy of an existing budget."""
    try:
        # Get original budget
        original_budget = db.query(Budget).filter(
            Budget.id == budget_id,
            Budget.user_id == current_user.id
        ).first()
        
        if not original_budget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Budget not found"
            )
        
        # Create new budget copy
        new_budget = Budget(
            user_id=current_user.id,
            name=new_name,
            description=f"Copy of {original_budget.name}",
            budget_type=original_budget.budget_type,
            status=BudgetStatus.DRAFT,
            start_date=original_budget.start_date,
            end_date=original_budget.end_date,
            total_income_budget=original_budget.total_income_budget,
            total_expense_budget=original_budget.total_expense_budget,
            warning_threshold=original_budget.warning_threshold,
            critical_threshold=original_budget.critical_threshold,
            auto_rollover=original_budget.auto_rollover,
            include_in_forecasting=original_budget.include_in_forecasting,
            tags=original_budget.tags
        )
        
        db.add(new_budget)
        db.flush()
        
        # Copy budget items if requested
        if copy_items:
            original_items = db.query(BudgetItem).filter(
                BudgetItem.budget_id == budget_id
            ).all()
            
            for item in original_items:
                new_item = BudgetItem(
                    budget_id=new_budget.id,
                    category=item.category,
                    subcategory=item.subcategory,
                    is_income=item.is_income,
                    budgeted_amount=item.budgeted_amount,
                    monthly_breakdown=item.monthly_breakdown,
                    use_historical_data=item.use_historical_data,
                    forecast_method=item.forecast_method,
                    notes=item.notes,
                    priority=item.priority
                )
                db.add(new_item)
        
        db.commit()
        db.refresh(new_budget)
        
        return new_budget
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Budget copy failed: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to copy budget"
        )