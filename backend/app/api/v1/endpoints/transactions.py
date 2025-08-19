from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta, date
import os
from pathlib import Path

from app.core.database import get_db
from app.core.transaction_manager import (
    TransactionManager, 
    financial_transaction, 
    with_transaction, 
    TransactionError
)
from app.core.error_sanitizer import error_sanitizer, create_secure_error_response
from app.schemas.error import ErrorCategory, ErrorSeverity
import uuid
from app.models.user import User
from app.models.transaction import Transaction
from app.core.cookie_auth import get_current_user_from_cookie
from app.services.categorization import CategorizationService
from app.services.export_service import ExportService
from app.schemas.transaction import TransactionResponse, TransactionUpdate
from app.schemas.export import (
    ExportFormat, ExportRequest, ExportJobResponse, ExportProgress, 
    ExportFilterParams, ExportColumnsConfig, ExportOptionsConfig
)
from app.core.financial_validators import validate_and_secure_sort_parameters
from app.core.exceptions import ValidationException
from app.core.rate_limiter import get_rate_limiter, RateLimitType, RateLimitTier, rate_limit
from app.core.audit_logger import security_audit_logger
from fastapi import Request

router = APIRouter()

@router.get("/", response_model=List[TransactionResponse])
async def get_transactions(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=1000, description="Number of records to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    subcategory: Optional[str] = Query(None, description="Filter by subcategory"),
    vendor: Optional[str] = Query(None, description="Filter by vendor"),
    description: Optional[str] = Query(None, description="Filter by description (partial match)"),
    start_date: Optional[datetime] = Query(None, description="Filter transactions from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter transactions until this date"),
    is_income: Optional[bool] = Query(None, description="Filter by income/expense"),
    is_categorized: Optional[bool] = Query(None, description="Filter by categorization status"),
    min_amount: Optional[float] = Query(None, description="Minimum amount"),
    max_amount: Optional[float] = Query(None, description="Maximum amount"),
    sort_by: str = Query("date", description="Sort field (validated): date, amount, description, vendor, category, subcategory, is_income, is_categorized, confidence_score, created_at, updated_at"),
    sort_order: str = Query("desc", description="Sort order (validated): asc, desc"),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Get user transactions with optional filtering and pagination"""
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)
    
    # Apply filters
    if category:
        query = query.filter(Transaction.category == category)
    
    if subcategory:
        query = query.filter(Transaction.subcategory == subcategory)
    
    if vendor:
        # Search in both vendor and description fields for more flexible search
        query = query.filter(
            or_(
                Transaction.vendor.ilike(f"%{vendor}%"),
                Transaction.description.ilike(f"%{vendor}%")
            )
        )
    
    if description:
        query = query.filter(Transaction.description.ilike(f"%{description}%"))
    
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    
    if is_income is not None:
        query = query.filter(Transaction.is_income == is_income)
    
    if is_categorized is not None:
        query = query.filter(Transaction.is_categorized == is_categorized)
    
    if min_amount is not None:
        query = query.filter(Transaction.amount >= min_amount)
    
    if max_amount is not None:
        query = query.filter(Transaction.amount <= max_amount)
    
    # Apply secure sorting with comprehensive validation
    try:
        # Validate and secure sort parameters
        validated_field, validated_order = validate_and_secure_sort_parameters(
            sort_by=sort_by,
            sort_order=sort_order,
            model_type='transaction',
            user_id=current_user.id,
            request_context={
                "endpoint": "get_transactions",
                "skip": skip,
                "limit": limit,
                "filters_applied": {
                    "category": category is not None,
                    "vendor": vendor is not None,
                    "date_range": start_date is not None or end_date is not None
                }
            }
        )
        
        # Get the validated field from the Transaction model
        sort_field = getattr(Transaction, validated_field)
        
        # Apply ordering based on validated parameters
        if validated_order == "asc":
            query = query.order_by(sort_field.asc())
        else:
            query = query.order_by(sort_field.desc())
            
    except ValidationException as e:
        # Return HTTP 400 for validation errors with detailed field information
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": e.message,
                "field_errors": [
                    {
                        "field": error.field,
                        "message": error.message,
                        "code": error.code
                    } for error in e.field_errors
                ]
            }
        )
    except Exception as e:
        # For unexpected errors, log and use secure defaults
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error in sort validation: {str(e)}")
        
        # Use secure default sorting
        query = query.order_by(Transaction.date.desc())
    
    # Apply pagination
    transactions = query.offset(skip).limit(limit).all()
    return transactions

@router.get("/count")
async def get_transaction_count(
    category: Optional[str] = Query(None, description="Filter by category"),
    subcategory: Optional[str] = Query(None, description="Filter by subcategory"),
    vendor: Optional[str] = Query(None, description="Filter by vendor"),
    description: Optional[str] = Query(None, description="Filter by description (partial match)"),
    start_date: Optional[datetime] = Query(None, description="Filter transactions from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter transactions until this date"),
    is_income: Optional[bool] = Query(None, description="Filter by income/expense"),
    is_categorized: Optional[bool] = Query(None, description="Filter by categorization status"),
    min_amount: Optional[float] = Query(None, description="Minimum amount"),
    max_amount: Optional[float] = Query(None, description="Maximum amount"),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Get total count of transactions matching the filters"""
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)
    
    # Apply the same filters as the main endpoint
    if category:
        query = query.filter(Transaction.category == category)
    
    if subcategory:
        query = query.filter(Transaction.subcategory == subcategory)
    
    if vendor:
        # Search in both vendor and description fields for more flexible search
        query = query.filter(
            or_(
                Transaction.vendor.ilike(f"%{vendor}%"),
                Transaction.description.ilike(f"%{vendor}%")
            )
        )
    
    if description:
        query = query.filter(Transaction.description.ilike(f"%{description}%"))
    
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    
    if is_income is not None:
        query = query.filter(Transaction.is_income == is_income)
    
    if is_categorized is not None:
        query = query.filter(Transaction.is_categorized == is_categorized)
    
    if min_amount is not None:
        query = query.filter(Transaction.amount >= min_amount)
    
    if max_amount is not None:
        query = query.filter(Transaction.amount <= max_amount)
    
    count = query.count()
    return {"count": count}

@router.get("/import-batches", response_model=List[dict])
async def list_import_batches(
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """List all import batches (files) for the current user with transaction counts"""
    # First get basic batch info
    batches = db.query(
        Transaction.import_batch,
        func.count(Transaction.id).label('transaction_count'),
        func.min(Transaction.created_at).label('import_date'),
        func.sum(Transaction.amount).label('total_amount')
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.import_batch.isnot(None)
    ).group_by(
        Transaction.import_batch
    ).order_by(
        func.min(Transaction.created_at).desc()
    ).all()
    
    # Then get filenames for each batch
    result = []
    for batch in batches:
        # Get filename from one transaction in the batch
        filename_transaction = db.query(Transaction).filter(
            Transaction.user_id == current_user.id,
            Transaction.import_batch == batch.import_batch
        ).first()
        
        filename = "Unknown File"
        if filename_transaction and filename_transaction.meta_data:
            filename = filename_transaction.meta_data.get('filename', 'Unknown File')
        
        result.append({
            "batch_id": batch.import_batch,
            "transaction_count": batch.transaction_count,
            "import_date": batch.import_date,
            "total_amount": float(batch.total_amount) if batch.total_amount else 0,
            "filename": filename
        })
    
    return result

@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Get a specific transaction"""
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    return transaction

@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: int,
    transaction_update: TransactionUpdate,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Update transaction categorization with comprehensive transaction management"""
    try:
        with financial_transaction(
            user_id=current_user.id, 
            operation_type="update_transaction_categorization",
            db_session=db
        ) as tx_manager:
            
            # Log the operation
            tx_manager.add_operation("update_transaction", {
                "transaction_id": transaction_id,
                "category": transaction_update.category,
                "subcategory": transaction_update.subcategory,
                "create_rule": transaction_update.create_rule
            })
            
            transaction = db.query(Transaction).filter(
                Transaction.id == transaction_id,
                Transaction.user_id == current_user.id
            ).first()
            
            if not transaction:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transaction not found"
                )
            
            # Create savepoint for transaction update
            update_savepoint = tx_manager.create_savepoint("transaction_update")
            
            try:
                # Update fields
                if transaction_update.category is not None:
                    transaction.category = transaction_update.category
                if transaction_update.subcategory is not None:
                    transaction.subcategory = transaction_update.subcategory
                
                transaction.is_categorized = True
                transaction.updated_at = datetime.utcnow()
                
                # Release savepoint after successful update
                tx_manager.release_savepoint(update_savepoint)
                
            except Exception as e:
                # Rollback to savepoint on update error
                tx_manager.rollback_to_savepoint(update_savepoint)
                # Create sanitized error for transaction failure
                error_detail = create_secure_error_response(
                    exception=e,
                    error_code="TRANSACTION_UPDATE_ERROR",
                    error_category=ErrorCategory.SYSTEM_ERROR,
                    correlation_id=str(uuid.uuid4())
                )
                raise TransactionError(f"Failed to update transaction: {error_detail.correlation_id}", e)
            
            # Create categorization rule from correction if requested
            new_rule_created = False
            if transaction_update.create_rule:
                rule_savepoint = tx_manager.create_savepoint("create_rule")
                try:
                    categorization_service = CategorizationService(db)
                    await categorization_service.create_rule_from_correction(
                        current_user.id,
                        transaction_id,
                        transaction.category,
                        transaction.subcategory
                    )
                    new_rule_created = True
                    tx_manager.release_savepoint(rule_savepoint)
                except Exception as e:
                    # Rollback rule creation but keep transaction update
                    tx_manager.rollback_to_savepoint(rule_savepoint)
                    # Log the error but don't fail the entire operation
                    # Sanitize error before logging
                    sanitized_error = error_sanitizer.sanitize_error_message(str(e))
                    tx_manager.add_operation("rule_creation_failed", {"error": sanitized_error})
            
            # Auto-categorize similar transactions
            auto_categorized_count = 0
            auto_cat_savepoint = tx_manager.create_savepoint("auto_categorize")
            try:
                categorization_service = CategorizationService(db)
                auto_categorized_count = await categorization_service._auto_categorize_similar_transactions(
                    current_user.id, 
                    transaction, 
                    transaction.category, 
                    transaction.subcategory
                )
                tx_manager.release_savepoint(auto_cat_savepoint)
            except Exception as e:
                # Rollback auto-categorization but keep main update
                tx_manager.rollback_to_savepoint(auto_cat_savepoint)
                # Sanitize error before logging
                sanitized_error = error_sanitizer.sanitize_error_message(str(e))
                tx_manager.add_operation("auto_categorization_failed", {"error": sanitized_error})
            
            # Transaction will be committed automatically by the context manager
            db.refresh(transaction)
            
            # Return response with auto-categorization info
            response_data = {
                "id": transaction.id,
                "user_id": transaction.user_id,
                "date": transaction.date,
                "amount": transaction.amount,
                "description": transaction.description,
                "vendor": transaction.vendor,
                "category": transaction.category,
                "subcategory": transaction.subcategory,
                "is_income": transaction.is_income,
                "source": transaction.source,
                "is_processed": transaction.is_processed,
                "is_categorized": transaction.is_categorized,
                "confidence_score": transaction.confidence_score,
                "created_at": transaction.created_at,
                "updated_at": transaction.updated_at,
                "auto_categorized_count": auto_categorized_count,
                "new_rule_created": new_rule_created
            }
            
            return response_data
            
    except HTTPException:
        # Re-raise HTTP exceptions without wrapping
        raise
    except Exception as e:
        # Create sanitized error response
        error_detail = create_secure_error_response(
            exception=e,
            error_code="TRANSACTION_UPDATE_FAILED",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4()),
            user_message="Failed to update transaction. Please try again.",
            suggested_action="If the problem persists, please contact support."
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail.user_message
        )

@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Delete a transaction with comprehensive transaction management"""
    try:
        with financial_transaction(
            user_id=current_user.id, 
            operation_type="delete_transaction",
            db_session=db
        ) as tx_manager:
            
            transaction = db.query(Transaction).filter(
                Transaction.id == transaction_id,
                Transaction.user_id == current_user.id
            ).first()
            
            if not transaction:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transaction not found"
                )
            
            # Log the deletion operation with transaction details
            tx_manager.add_operation("delete_transaction", {
                "transaction_id": transaction_id,
                "amount": transaction.amount,
                "description": transaction.description,
                "date": transaction.date.isoformat() if transaction.date else None
            })
            
            db.delete(transaction)
            
            # Transaction will be committed automatically
            return {"message": "Transaction deleted successfully"}
            
    except HTTPException:
        # Re-raise HTTP exceptions without wrapping
        raise
    except Exception as e:
        # Create sanitized error response
        error_detail = create_secure_error_response(
            exception=e,
            error_code="TRANSACTION_DELETE_FAILED",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4()),
            user_message="Failed to delete transaction. Please try again.",
            suggested_action="If the problem persists, please contact support."
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail.user_message
        )

@router.post("/categorize")
async def categorize_transactions(
    use_ml_fallback: bool = Query(True, description="Use ML categorization for transactions not matched by rules"),
    batch_id: Optional[str] = Query(None, description="Only categorize transactions from specific import batch"),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Re-run categorization on all uncategorized transactions with ML fallback"""
    categorization_service = CategorizationService(db)
    result = await categorization_service.categorize_user_transactions(
        current_user.id, batch_id, use_ml_fallback
    )
    
    return {
        "message": f"Categorized {result['rule_categorized'] + result['ml_categorized']} of {result['total_transactions']} transactions",
        "total_transactions": result['total_transactions'],
        "rule_categorized": result['rule_categorized'],
        "ml_categorized": result['ml_categorized'],
        "failed_categorizations": result['failed_categorizations'],
        "success_rate": result['success_rate']
    }

@router.post("/categorize/bulk")
@rate_limit(requests_per_hour=100, requests_per_minute=10)  # Strict limits for bulk operations
async def bulk_categorize_transactions(
    transaction_ids: List[int],
    use_ml_fallback: bool = Query(True, description="Use ML categorization for transactions not matched by rules"),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Bulk categorize specific transactions by ID
    
    This endpoint allows users to categorize multiple specific transactions at once,
    providing better control over the categorization process.
    """
    if not transaction_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one transaction ID must be provided"
        )
    
    if len(transaction_ids) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 1000 transactions can be categorized at once"
        )
    
    # Verify all transactions belong to the user
    transactions = db.query(Transaction).filter(
        Transaction.id.in_(transaction_ids),
        Transaction.user_id == current_user.id
    ).all()
    
    if len(transactions) != len(transaction_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some transaction IDs are invalid or do not belong to the user"
        )
    
    categorization_service = CategorizationService(db)
    result = await categorization_service.categorize_transactions_by_ids(
        current_user.id, transaction_ids, use_ml_fallback
    )
    
    # Audit logging for bulk categorization
    security_audit_logger.log_bulk_categorization(
        user_id=current_user.id,
        transaction_count=len(transaction_ids),
        method="bulk_categorization",
        processing_time=result.get('processing_time', 0),
        request=request
    )
    
    return {
        "message": f"Bulk categorization completed: {result['rule_categorized'] + result['ml_categorized']} of {result['total_transactions']} transactions categorized",
        "total_transactions": result['total_transactions'],
        "rule_categorized": result['rule_categorized'],
        "ml_categorized": result['ml_categorized'],
        "failed_categorizations": result['failed_categorizations'],
        "success_rate": result['success_rate'],
        "processing_time": result.get('processing_time', 0)
    }

@router.get("/categorize/confidence/{transaction_id}")
async def get_categorization_confidence(
    transaction_id: int,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Get categorization confidence score and alternatives for a specific transaction
    
    This endpoint provides detailed information about the categorization confidence
    and alternative categories that could be applied.
    """
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
    confidence_data = await categorization_service.get_categorization_confidence(
        transaction
    )
    
    return {
        "transaction_id": transaction_id,
        "current_category": transaction.category,
        "current_subcategory": transaction.subcategory,
        "confidence_score": transaction.confidence_score,
        "categorization_method": transaction.meta_data.get('categorization_method', 'unknown') if transaction.meta_data else 'unknown',
        "confidence_breakdown": confidence_data.get('confidence_breakdown', {}),
        "alternative_categories": confidence_data.get('alternatives', []),
        "ml_reasoning": transaction.meta_data.get('ml_reasoning') if transaction.meta_data else None,
        "rule_applied": confidence_data.get('rule_applied'),
        "last_categorized": transaction.updated_at.isoformat() if transaction.updated_at else None
    }

@router.post("/categorize/feedback")
@rate_limit(requests_per_hour=1000, requests_per_minute=100)  # Standard limits for feedback
async def submit_categorization_feedback(
    transaction_id: int,
    feedback_type: str = Query(..., description="Type of feedback: correct, incorrect, suggest_alternative"),
    suggested_category: Optional[str] = Query(None, description="Suggested category if feedback_type is suggest_alternative"),
    suggested_subcategory: Optional[str] = Query(None, description="Suggested subcategory if feedback_type is suggest_alternative"),
    feedback_comment: Optional[str] = Query(None, description="Additional feedback comment"),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Submit feedback on categorization accuracy
    
    This endpoint allows users to provide feedback on categorization results,
    which helps improve the ML model and rule-based categorization.
    """
    if feedback_type not in ['correct', 'incorrect', 'suggest_alternative']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid feedback_type. Must be one of: correct, incorrect, suggest_alternative"
        )
    
    if feedback_type == 'suggest_alternative' and not suggested_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="suggested_category is required when feedback_type is suggest_alternative"
        )
    
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
    feedback_result = await categorization_service.submit_categorization_feedback(
        transaction_id=transaction_id,
        user_id=current_user.id,
        feedback_type=feedback_type,
        suggested_category=suggested_category,
        suggested_subcategory=suggested_subcategory,
        feedback_comment=feedback_comment
    )
    
    # Audit logging for categorization feedback
    security_audit_logger.log_categorization_feedback(
        user_id=current_user.id,
        transaction_id=transaction_id,
        feedback_type=feedback_type,
        suggested_category=suggested_category,
        request=request
    )
    
    return {
        "message": "Categorization feedback submitted successfully",
        "feedback_id": feedback_result['feedback_id'],
        "transaction_id": transaction_id,
        "feedback_type": feedback_type,
        "impact": feedback_result.get('impact', 'feedback_recorded'),
        "ml_learning": feedback_result.get('ml_learning', False)
    }

@router.get("/categorize/suggestions/{transaction_id}")
async def get_category_suggestions(
    transaction_id: int,
    include_ml: bool = Query(True, description="Include ML-based suggestions"),
    include_rules: bool = Query(True, description="Include rule-based suggestions"),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Get category suggestions for a specific transaction
    
    This endpoint provides intelligent category suggestions based on both
    rule-based matching and ML predictions.
    """
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
    suggestions = await categorization_service.get_category_suggestions(
        transaction, include_ml=include_ml, include_rules=include_rules
    )
    
    return {
        "transaction_id": transaction_id,
        "description": transaction.description,
        "amount": transaction.amount,
        "current_category": transaction.category,
        "current_subcategory": transaction.subcategory,
        "suggestions": suggestions.get('suggestions', []),
        "rule_matches": suggestions.get('rule_matches', []),
        "ml_predictions": suggestions.get('ml_predictions', []),
        "confidence_threshold": suggestions.get('confidence_threshold', 0.6)
    }

@router.post("/categorize/auto-improve")
@rate_limit(requests_per_hour=50, requests_per_minute=5)  # Strict limits for auto-improvement
async def auto_improve_categorization(
    batch_id: Optional[str] = Query(None, description="Improve categorization for specific batch"),
    min_confidence_threshold: float = Query(0.5, ge=0.0, le=1.0, description="Minimum confidence threshold for improvements"),
    max_transactions: int = Query(1000, ge=1, le=10000, description="Maximum transactions to process (default: 1000)"),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Automatically improve categorization based on user feedback and patterns
    
    This endpoint analyzes user feedback and transaction patterns to
    automatically improve categorization rules and ML model performance.
    """
    categorization_service = CategorizationService(db)
    improvement_result = await categorization_service.auto_improve_categorization(
        user_id=current_user.id,
        batch_id=batch_id,
        min_confidence_threshold=min_confidence_threshold,
        max_transactions=max_transactions  # Add transaction limit
    )
    
    # Audit logging for auto-improvement
    security_audit_logger.log_bulk_categorization(
        user_id=current_user.id,
        transaction_count=improvement_result.get('transactions_reprocessed', 0),
        method="auto_improvement",
        processing_time=improvement_result.get('processing_time', 0),
        request=request
    )
    
    return {
        "message": "Categorization auto-improvement completed",
        "rules_created": improvement_result.get('rules_created', 0),
        "rules_updated": improvement_result.get('rules_updated', 0),
        "ml_model_improvements": improvement_result.get('ml_improvements', 0),
        "transactions_reprocessed": improvement_result.get('transactions_reprocessed', 0),
        "improvement_score": improvement_result.get('improvement_score', 0.0),
        "processing_time": improvement_result.get('processing_time', 0)
    }

@router.get("/categorize/performance")
async def get_categorization_performance(
    start_date: Optional[datetime] = Query(None, description="Start date for performance analysis"),
    end_date: Optional[datetime] = Query(None, description="End date for performance analysis"),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Get categorization performance metrics
    
    This endpoint provides detailed performance metrics for categorization,
    including accuracy rates, confidence distributions, and improvement trends.
    """
    categorization_service = CategorizationService(db)
    performance_data = await categorization_service.get_categorization_performance(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date
    )
    
    return {
        "user_id": current_user.id,
        "period": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None
        },
        "overall_metrics": performance_data.get('overall', {}),
        "method_breakdown": performance_data.get('methods', {}),
        "confidence_distribution": performance_data.get('confidence_distribution', {}),
        "category_performance": performance_data.get('categories', {}),
        "improvement_trends": performance_data.get('trends', {}),
        "feedback_analysis": performance_data.get('feedback', {})
    }

@router.get("/categories/available")
async def get_available_categories(
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Get all available categories and subcategories for the user"""
    categorization_service = CategorizationService(db)
    categories = categorization_service.get_available_categories(current_user.id)
    
    return {
        "categories": categories,
        "total_categories": len(categories)
    }

@router.put("/{transaction_id}/category")
async def update_transaction_category(
    transaction_id: int,
    category: str,
    subcategory: Optional[str] = None,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Update transaction category and auto-categorize similar transactions"""
    categorization_service = CategorizationService(db)
    
    try:
        result = await categorization_service.update_transaction_category(
            current_user.id,
            transaction_id,
            category,
            subcategory
        )
        
        return {
            "message": "Transaction category updated successfully",
            "transaction_updated": result["transaction_updated"],
            "auto_categorized_count": result["auto_categorized_count"],
            "new_rule_created": result["new_rule_created"]
        }
        
    except ValueError as e:
        # For 404 errors, use a generic message
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    except Exception as e:
        # Create sanitized error response
        error_detail = create_secure_error_response(
            exception=e,
            error_code="TRANSACTION_CATEGORY_UPDATE_FAILED",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4()),
            user_message="Failed to update transaction category. Please try again.",
            suggested_action="If the problem persists, please contact support."
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail.user_message
        )

@router.delete("/import-batch/{batch_id}")
async def delete_import_batch(
    batch_id: str,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Delete all transactions from a specific import batch with comprehensive transaction management"""
    try:
        with financial_transaction(
            user_id=current_user.id, 
            operation_type="delete_import_batch",
            db_session=db
        ) as tx_manager:
            
            # First, verify the batch exists and belongs to the user
            batch_transactions = db.query(Transaction).filter(
                Transaction.user_id == current_user.id,
                Transaction.import_batch == batch_id
            ).all()
            
            if not batch_transactions:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No transactions found for batch {batch_id}"
                )
            
            # Get transaction count and details before deletion
            transaction_count = len(batch_transactions)
            total_amount = sum(t.amount for t in batch_transactions)
            
            # Log the batch deletion operation
            tx_manager.add_operation("delete_import_batch", {
                "batch_id": batch_id,
                "transaction_count": transaction_count,
                "total_amount": total_amount,
                "transaction_ids": [t.id for t in batch_transactions]
            })
            
            # Delete all transactions in the batch with progress tracking
            deleted_count = 0
            for i, transaction in enumerate(batch_transactions):
                # Create savepoint for each deletion to ensure individual rollback capability
                delete_savepoint = tx_manager.create_savepoint(f"delete_transaction_{i}")
                try:
                    db.delete(transaction)
                    deleted_count += 1
                    tx_manager.release_savepoint(delete_savepoint)
                except Exception as e:
                    # Rollback individual transaction deletion
                    tx_manager.rollback_to_savepoint(delete_savepoint)
                    tx_manager.add_operation("transaction_deletion_failed", {
                        "transaction_id": transaction.id,
                        "error": error_sanitizer.sanitize_error_message(str(e))
                    })
                    # Continue with other deletions
            
            # If no transactions were successfully deleted, raise an error
            if deleted_count == 0:
                raise TransactionError("Failed to delete any transactions from the batch")
            
            # Transaction will be committed automatically
            return {
                "message": f"Successfully deleted {deleted_count} transactions from batch {batch_id}",
                "deleted_count": deleted_count,
                "total_count": transaction_count,
                "batch_id": batch_id
            }
            
    except HTTPException:
        # Re-raise HTTP exceptions without wrapping
        raise
    except Exception as e:
        # Create sanitized error response
        error_detail = create_secure_error_response(
            exception=e,
            error_code="BATCH_DELETE_FAILED",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4()),
            user_message="Failed to delete batch transactions. Please try again.",
            suggested_action="If the problem persists, please contact support."
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail.user_message
        )


# ====================== EXPORT ENDPOINTS ======================

@router.get("/export/csv")
async def export_transactions_csv(
    from_date: Optional[date] = Query(None, description="Start date for export (YYYY-MM-DD)"),
    to_date: Optional[date] = Query(None, description="End date for export (YYYY-MM-DD)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    subcategory: Optional[str] = Query(None, description="Filter by subcategory"),
    is_income: Optional[bool] = Query(None, description="Filter by income/expense type"),
    min_amount: Optional[float] = Query(None, description="Minimum amount filter"),
    max_amount: Optional[float] = Query(None, description="Maximum amount filter"),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db),
    rate_limiter = Depends(get_rate_limiter)
):
    """Export transactions as CSV with filtering support and rate limiting."""
    
    try:
        # Apply rate limiting (5 exports per hour for free tier)
        rate_limit_result = await rate_limiter.check_rate_limit(
            identifier=f"user_{current_user.id}",
            limit_type=RateLimitType.UPLOAD,  # Reuse upload limits for exports
            user_tier=getattr(current_user, 'tier', 'free')
        )
        
        if not rate_limit_result.allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "message": "Export rate limit exceeded",
                    "retry_after": rate_limit_result.retry_after,
                    "limit": rate_limit_result.limit,
                    "reset_time": rate_limit_result.reset_time.isoformat()
                }
            )
        
        # Build filters
        filters = ExportFilterParams(
            from_date=from_date,
            to_date=to_date,
            categories=[category] if category else None,
            subcategories=[subcategory] if subcategory else None,
            is_income=is_income,
            min_amount=min_amount,
            max_amount=max_amount
        )
        
        # Create export service and generate CSV
        export_service = ExportService(db)
        job_id = await export_service.create_export_job(
            user_id=current_user.id,
            export_format=ExportFormat.CSV,
            filters=filters,
            export_name="transactions_csv_export"
        )
        
        # For simple CSV exports, wait for completion and return file
        max_wait_time = 30  # 30 seconds max wait
        wait_interval = 1
        elapsed = 0
        
        while elapsed < max_wait_time:
            progress = export_service.get_export_progress(job_id, current_user.id)
            if not progress:
                break
            
            if progress.status.value == "completed":
                file_path = export_service.get_export_download_path(job_id, current_user.id)
                if file_path and os.path.exists(file_path):
                    filename = f"transactions_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
                    return FileResponse(
                        path=file_path,
                        filename=filename,
                        media_type="text/csv",
                        headers={"Content-Disposition": f"attachment; filename={filename}"}
                    )
                break
            elif progress.status.value == "failed":
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Export failed: {progress.error_message}"
                )
            
            import asyncio
            await asyncio.sleep(wait_interval)
            elapsed += wait_interval
        
        # If we get here, export is taking too long - return job ID for polling
        progress = export_service.get_export_progress(job_id, current_user.id)
        return ExportJobResponse(
            job_id=job_id,
            status="processing",
            estimated_records=progress.total_records if progress else 0,
            created_at=datetime.utcnow(),
            message="Export is processing. Use /export/status/{job_id} to check progress."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_detail = create_secure_error_response(
            exception=e,
            error_code="CSV_EXPORT_FAILED",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4()),
            user_message="Failed to export transactions to CSV. Please try again.",
            suggested_action="Reduce the date range or contact support if the problem persists."
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail.user_message
        )


@router.get("/export/excel")
async def export_transactions_excel(
    from_date: Optional[date] = Query(None, description="Start date for export (YYYY-MM-DD)"),
    to_date: Optional[date] = Query(None, description="End date for export (YYYY-MM-DD)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    subcategory: Optional[str] = Query(None, description="Filter by subcategory"),
    is_income: Optional[bool] = Query(None, description="Filter by income/expense type"),
    min_amount: Optional[float] = Query(None, description="Minimum amount filter"),
    max_amount: Optional[float] = Query(None, description="Maximum amount filter"),
    include_summary: bool = Query(True, description="Include summary sheet"),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db),
    rate_limiter = Depends(get_rate_limiter)
):
    """Export transactions as Excel workbook with multiple sheets and enhanced formatting."""
    
    try:
        # Apply rate limiting
        rate_limit_result = await rate_limiter.check_rate_limit(
            identifier=f"user_{current_user.id}",
            limit_type=RateLimitType.UPLOAD,
            user_tier=getattr(current_user, 'tier', 'free')
        )
        
        if not rate_limit_result.allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "message": "Export rate limit exceeded",
                    "retry_after": rate_limit_result.retry_after,
                    "limit": rate_limit_result.limit,
                    "reset_time": rate_limit_result.reset_time.isoformat()
                }
            )
        
        # Build filters
        filters = ExportFilterParams(
            from_date=from_date,
            to_date=to_date,
            categories=[category] if category else None,
            subcategories=[subcategory] if subcategory else None,
            is_income=is_income,
            min_amount=min_amount,
            max_amount=max_amount
        )
        
        # Configure Excel options
        options = ExportOptionsConfig(
            include_summary_sheet=include_summary,
            include_category_breakdown=True
        )
        
        # Create export job
        export_service = ExportService(db)
        job_id = await export_service.create_export_job(
            user_id=current_user.id,
            export_format=ExportFormat.EXCEL,
            filters=filters,
            options_config=options,
            export_name="transactions_excel_export"
        )
        
        # For Excel exports, return job ID since they can be large
        progress = export_service.get_export_progress(job_id, current_user.id)
        
        return ExportJobResponse(
            job_id=job_id,
            status=progress.status.value if progress else "pending",
            estimated_records=progress.total_records if progress else 0,
            created_at=datetime.utcnow(),
            message="Excel export started. Use /export/status/{job_id} to check progress and download when ready."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_detail = create_secure_error_response(
            exception=e,
            error_code="EXCEL_EXPORT_FAILED",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4()),
            user_message="Failed to export transactions to Excel. Please try again.",
            suggested_action="Reduce the date range or contact support if the problem persists."
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail.user_message
        )


@router.get("/export/json")
async def export_transactions_json(
    from_date: Optional[date] = Query(None, description="Start date for export (YYYY-MM-DD)"),
    to_date: Optional[date] = Query(None, description="End date for export (YYYY-MM-DD)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    subcategory: Optional[str] = Query(None, description="Filter by subcategory"),
    is_income: Optional[bool] = Query(None, description="Filter by income/expense type"),
    min_amount: Optional[float] = Query(None, description="Minimum amount filter"),
    max_amount: Optional[float] = Query(None, description="Maximum amount filter"),
    include_metadata: bool = Query(True, description="Include export metadata"),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db),
    rate_limiter = Depends(get_rate_limiter)
):
    """Export transactions as structured JSON with metadata."""
    
    try:
        # Apply rate limiting
        rate_limit_result = await rate_limiter.check_rate_limit(
            identifier=f"user_{current_user.id}",
            limit_type=RateLimitType.UPLOAD,
            user_tier=getattr(current_user, 'tier', 'free')
        )
        
        if not rate_limit_result.allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "message": "Export rate limit exceeded",
                    "retry_after": rate_limit_result.retry_after,
                    "limit": rate_limit_result.limit,
                    "reset_time": rate_limit_result.reset_time.isoformat()
                }
            )
        
        # Build filters
        filters = ExportFilterParams(
            from_date=from_date,
            to_date=to_date,
            categories=[category] if category else None,
            subcategories=[subcategory] if subcategory else None,
            is_income=is_income,
            min_amount=min_amount,
            max_amount=max_amount
        )
        
        # Configure JSON export to include all relevant data
        columns = ExportColumnsConfig(
            include_raw_data=include_metadata,
            include_meta_data=include_metadata,
            include_created_at=True,
            include_updated_at=True,
            include_confidence_score=True
        )
        
        # Create export job
        export_service = ExportService(db)
        job_id = await export_service.create_export_job(
            user_id=current_user.id,
            export_format=ExportFormat.JSON,
            filters=filters,
            columns_config=columns,
            export_name="transactions_json_export"
        )
        
        # For JSON, wait a bit since it's structured data
        max_wait_time = 20
        wait_interval = 1
        elapsed = 0
        
        while elapsed < max_wait_time:
            progress = export_service.get_export_progress(job_id, current_user.id)
            if not progress:
                break
            
            if progress.status.value == "completed":
                file_path = export_service.get_export_download_path(job_id, current_user.id)
                if file_path and os.path.exists(file_path):
                    filename = f"transactions_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
                    return FileResponse(
                        path=file_path,
                        filename=filename,
                        media_type="application/json",
                        headers={"Content-Disposition": f"attachment; filename={filename}"}
                    )
                break
            elif progress.status.value == "failed":
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Export failed: {progress.error_message}"
                )
            
            import asyncio
            await asyncio.sleep(wait_interval)
            elapsed += wait_interval
        
        # Return job ID for polling if still processing
        progress = export_service.get_export_progress(job_id, current_user.id)
        return ExportJobResponse(
            job_id=job_id,
            status="processing",
            estimated_records=progress.total_records if progress else 0,
            created_at=datetime.utcnow(),
            message="JSON export is processing. Use /export/status/{job_id} to check progress."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_detail = create_secure_error_response(
            exception=e,
            error_code="JSON_EXPORT_FAILED",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4()),
            user_message="Failed to export transactions to JSON. Please try again.",
            suggested_action="Reduce the date range or contact support if the problem persists."
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail.user_message
        )


@router.post("/export/custom", response_model=ExportJobResponse)
async def create_custom_export(
    export_request: ExportRequest,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db),
    rate_limiter = Depends(get_rate_limiter)
):
    """Create a custom export with comprehensive filtering and configuration options."""
    
    try:
        # Apply stricter rate limiting for custom exports
        rate_limit_result = await rate_limiter.check_rate_limit(
            identifier=f"user_{current_user.id}",
            limit_type=RateLimitType.ANALYTICS,  # Use analytics limits (more restrictive)
            user_tier=getattr(current_user, 'tier', 'free')
        )
        
        if not rate_limit_result.allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "message": "Custom export rate limit exceeded",
                    "retry_after": rate_limit_result.retry_after,
                    "limit": rate_limit_result.limit,
                    "reset_time": rate_limit_result.reset_time.isoformat()
                }
            )
        
        # Create export job with custom configuration
        export_service = ExportService(db)
        job_id = await export_service.create_export_job(
            user_id=current_user.id,
            export_format=export_request.export_format,
            filters=export_request.filters,
            columns_config=export_request.columns,
            options_config=export_request.options,
            export_name=export_request.export_name
        )
        
        # Get initial progress
        progress = export_service.get_export_progress(job_id, current_user.id)
        
        return ExportJobResponse(
            job_id=job_id,
            status=progress.status.value if progress else "pending",
            estimated_records=progress.total_records if progress else 0,
            estimated_completion_time=progress.estimated_completion if progress else None,
            created_at=datetime.utcnow(),
            message=f"Custom {export_request.export_format.value} export created. Use /export/status/{job_id} to monitor progress."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_detail = create_secure_error_response(
            exception=e,
            error_code="CUSTOM_EXPORT_FAILED",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4()),
            user_message="Failed to create custom export. Please try again.",
            suggested_action="Check your export configuration or contact support if the problem persists."
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail.user_message
        )


@router.get("/export/status/{job_id}", response_model=ExportProgress)
async def get_export_status(
    job_id: str,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Get the status and progress of an export job."""
    
    try:
        export_service = ExportService(db)
        progress = export_service.get_export_progress(job_id, current_user.id)
        
        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export job not found or access denied"
            )
        
        return progress
        
    except HTTPException:
        raise
    except Exception as e:
        error_detail = create_secure_error_response(
            exception=e,
            error_code="EXPORT_STATUS_FAILED",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4()),
            user_message="Failed to retrieve export status. Please try again."
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail.user_message
        )


@router.get("/export/download/{job_id}")
async def download_export(
    job_id: str,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Download a completed export file."""
    
    try:
        export_service = ExportService(db)
        
        # Check if export is completed and get file path
        progress = export_service.get_export_progress(job_id, current_user.id)
        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export job not found or access denied"
            )
        
        if progress.status.value != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Export is not ready for download. Current status: {progress.status.value}"
            )
        
        file_path = export_service.get_export_download_path(job_id, current_user.id)
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export file not found or has expired"
            )
        
        # Determine content type and filename based on file extension
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.csv':
            media_type = "text/csv"
            filename_suffix = ".csv"
        elif file_ext == '.xlsx':
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename_suffix = ".xlsx"
        elif file_ext == '.json':
            media_type = "application/json"
            filename_suffix = ".json"
        elif file_ext == '.gz':
            media_type = "application/gzip"
            filename_suffix = ".gz"
        else:
            media_type = "application/octet-stream"
            filename_suffix = ""
        
        # Generate secure filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"fingood_transactions_export_{timestamp}{filename_suffix}"
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_detail = create_secure_error_response(
            exception=e,
            error_code="EXPORT_DOWNLOAD_FAILED",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4()),
            user_message="Failed to download export file. Please try again."
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail.user_message
        )
