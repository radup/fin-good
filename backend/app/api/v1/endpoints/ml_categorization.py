from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import uuid

from app.core.database import get_db
from app.core.error_sanitizer import create_secure_error_response
from app.schemas.error import ErrorCategory
from app.models.user import User
from app.models.transaction import Transaction
from app.core.cookie_auth import get_current_user_from_cookie
from app.services.categorization import CategorizationService

router = APIRouter()

@router.post("/{transaction_id}/categorize")
async def categorize_transaction_with_ml(
    transaction_id: int,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Categorize a single transaction using ML (real-time)"""
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    categorization_service = CategorizationService(db)
    
    try:
        result = await categorization_service.categorize_single_transaction(
            transaction, 
            use_ml_fallback=True
        )
        
        return {
            "transaction_id": transaction_id,
            "categorization_result": result
        }
        
    except Exception as e:
        error_detail = create_secure_error_response(
            exception=e,
            error_code="ML_CATEGORIZATION_FAILED",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4())
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ML categorization failed: {error_detail.correlation_id}"
        )

@router.get("/{transaction_id}/suggestions")
async def get_ml_category_suggestions(
    transaction_id: int,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Get ML category suggestions for a transaction without applying them"""
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    categorization_service = CategorizationService(db)
    
    try:
        suggestions = await categorization_service.suggest_categories_for_transaction(transaction)
        
        return {
            "transaction_id": transaction_id,
            "transaction_details": {
                "description": transaction.description,
                "vendor": transaction.vendor,
                "amount": transaction.amount
            },
            "suggestions": suggestions
        }
        
    except Exception as e:
        error_detail = create_secure_error_response(
            exception=e,
            error_code="ML_SUGGESTIONS_FAILED",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4())
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ML suggestions: {error_detail.correlation_id}"
        )

@router.get("/performance-metrics")
async def get_ml_performance_metrics(
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Get ML categorization performance metrics"""
    categorization_service = CategorizationService(db)
    
    try:
        metrics = await categorization_service.get_ml_performance_metrics()
        
        return {
            "user_id": current_user.id,
            "ml_performance": metrics
        }
        
    except Exception as e:
        error_detail = create_secure_error_response(
            exception=e,
            error_code="ML_METRICS_FAILED",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4())
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ML metrics: {error_detail.correlation_id}"
        )

@router.get("/health-status")
async def get_ml_health_status(
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Get ML service health status"""
    categorization_service = CategorizationService(db)
    
    try:
        health_status = await categorization_service.get_ml_health_status()
        
        return {
            "user_id": current_user.id,
            "ml_health": health_status
        }
        
    except Exception as e:
        error_detail = create_secure_error_response(
            exception=e,
            error_code="ML_HEALTH_CHECK_FAILED",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4())
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check ML health: {error_detail.correlation_id}"
        )

@router.get("/training-data")
async def get_training_data(
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Generate training data from user's categorized transactions"""
    categorization_service = CategorizationService(db)
    
    try:
        training_data = await categorization_service.generate_training_data(current_user.id)
        
        return {
            "user_id": current_user.id,
            "training_data_count": len(training_data),
            "training_data": training_data
        }
        
    except Exception as e:
        error_detail = create_secure_error_response(
            exception=e,
            error_code="TRAINING_DATA_FAILED",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4())
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate training data: {error_detail.correlation_id}"
        )