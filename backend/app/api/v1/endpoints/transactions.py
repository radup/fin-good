from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

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
from app.schemas.transaction import TransactionResponse, TransactionUpdate
from app.core.financial_validators import validate_and_secure_sort_parameters
from app.core.exceptions import ValidationException

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
        query = query.filter(Transaction.vendor.ilike(f"%{vendor}%"))
    
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
        query = query.filter(Transaction.vendor.ilike(f"%{vendor}%"))
    
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
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Re-run categorization on all uncategorized transactions"""
    categorization_service = CategorizationService(db)
    categorized_count = await categorization_service.categorize_user_transactions(current_user.id)
    
    return {
        "message": f"Categorized {categorized_count} transactions",
        "categorized_count": categorized_count
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
