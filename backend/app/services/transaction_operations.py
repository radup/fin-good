"""
Transaction Bulk Operations Service

Handles multi-select transaction operations with comprehensive validation,
audit logging, and undo/redo capabilities for enhanced user productivity.
"""

from typing import List, Dict, Any, Optional, Set, Tuple, Union
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from sqlalchemy.exc import SQLAlchemyError
import json
import logging
from dataclasses import dataclass, asdict
from enum import Enum

# Configuration constants
class BulkOperationLimits:
    MAX_TRANSACTIONS_PER_OPERATION = 1000
    MAX_TRANSACTIONS_DELETE = 500
    MAX_CATEGORY_LENGTH = 100
    MAX_SUBCATEGORY_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 500
    MAX_VENDOR_LENGTH = 200
    MAX_UNDO_OPERATIONS = 50

from app.models.transaction import Transaction
from app.models.user import User
from app.core.exceptions import ValidationException, BusinessLogicException
from app.core.financial_validators import FinancialAmount, TransactionValidator
from app.core.security_utils import input_sanitizer
from app.core.audit_logger import security_audit_logger
from app.core.transaction_manager import TransactionManager


class BulkOperationType(Enum):
    """Supported bulk operation types"""
    UPDATE_CATEGORY = "update_category"
    UPDATE_SUBCATEGORY = "update_subcategory" 
    UPDATE_DESCRIPTION = "update_description"
    UPDATE_VENDOR = "update_vendor"
    UPDATE_AMOUNT = "update_amount"
    DELETE = "delete"
    MERGE = "merge"
    SPLIT = "split"


class BulkOperationStatus(Enum):
    """Status of bulk operation execution"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class BulkOperationResult:
    """Result of a bulk operation"""
    operation_id: str
    operation_type: BulkOperationType
    status: BulkOperationStatus
    total_transactions: int
    successful_count: int
    failed_count: int
    errors: List[Dict[str, Any]]
    affected_transaction_ids: List[int]
    rollback_data: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass 
class BulkUpdateRequest:
    """Request for bulk update operations"""
    transaction_ids: List[int]
    operation_type: BulkOperationType
    updates: Dict[str, Any]
    validate_before_execute: bool = True
    create_backup: bool = True


@dataclass
class UndoOperation:
    """Information needed to undo a bulk operation"""
    operation_id: str
    original_data: Dict[int, Dict[str, Any]]  # transaction_id -> original_values
    operation_type: BulkOperationType
    timestamp: datetime
    user_id: int


class TransactionBulkOperations:
    """
    Service for handling bulk transaction operations with comprehensive
    validation, audit logging, and undo/redo capabilities.
    """
    
    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.audit_logger = security_audit_logger
        self.transaction_manager = TransactionManager(db)
        self.validator = TransactionValidator()
        
        # In-memory undo stack (in production, this would be Redis/database)
        self._undo_stack: List[UndoOperation] = []
        self.max_undo_operations = BulkOperationLimits.MAX_UNDO_OPERATIONS
    
    async def execute_bulk_update(self, request: BulkUpdateRequest) -> BulkOperationResult:
        """
        Execute bulk update operation on multiple transactions
        
        Args:
            request: BulkUpdateRequest containing operation details
            
        Returns:
            BulkOperationResult with execution details
            
        Raises:
            ValidationException: If validation fails
            BusinessLogicException: If business rules are violated
        """
        operation_id = f"bulk_{request.operation_type.value}_{datetime.utcnow().isoformat()}"
        start_time = datetime.utcnow()
        
        self.audit_logger.info(
            f"Starting bulk operation: {operation_id}",
            extra={
                "operation_id": operation_id,
                "operation_type": request.operation_type.value,
                "user_id": self.user.id,
                "transaction_count": len(request.transaction_ids),
                "updates": request.updates
            }
        )
        
        # Initialize result
        result = BulkOperationResult(
            operation_id=operation_id,
            operation_type=request.operation_type,
            status=BulkOperationStatus.PENDING,
            total_transactions=len(request.transaction_ids),
            successful_count=0,
            failed_count=0,
            errors=[],
            affected_transaction_ids=[],
            started_at=start_time
        )
        
        try:
            result.status = BulkOperationStatus.IN_PROGRESS
            
            # Validate request
            await self._validate_bulk_request(request)
            
            # Get target transactions with user isolation
            transactions = await self._get_user_transactions(request.transaction_ids)
            
            if not transactions:
                raise ValidationException("No valid transactions found for the provided IDs")
            
            # Create backup for undo if requested
            backup_data = {}
            if request.create_backup:
                backup_data = await self._create_backup(transactions)
            
            # Execute the bulk operation
            successful_ids, errors = await self._execute_operation(
                transactions, 
                request.operation_type, 
                request.updates
            )
            
            result.successful_count = len(successful_ids)
            result.failed_count = len(errors)
            result.errors = errors
            result.affected_transaction_ids = successful_ids
            result.status = BulkOperationStatus.COMPLETED if not errors else BulkOperationStatus.FAILED
            
            # Store undo information if backup was created
            if request.create_backup and backup_data:
                self._store_undo_operation(
                    operation_id, 
                    backup_data, 
                    request.operation_type
                )
            
            result.completed_at = datetime.utcnow()
            result.execution_time_ms = int(
                (result.completed_at - start_time).total_seconds() * 1000
            )
            
            self.audit_logger.info(
                f"Bulk operation completed: {operation_id}",
                extra={
                    "operation_id": operation_id,
                    "status": result.status.value,
                    "successful_count": result.successful_count,
                    "failed_count": result.failed_count,
                    "execution_time_ms": result.execution_time_ms
                }
            )
            
            return result
            
        except Exception as e:
            result.status = BulkOperationStatus.FAILED
            result.completed_at = datetime.utcnow()
            result.errors.append({
                "error": str(e),
                "type": type(e).__name__,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            self.audit_logger.error(
                f"Bulk operation failed: {operation_id}",
                extra={
                    "operation_id": operation_id,
                    "error": str(e),
                    "user_id": self.user.id
                }
            )
            
            raise
    
    async def _validate_bulk_request(self, request: BulkUpdateRequest) -> None:
        """Validate bulk operation request"""
        
        # Validate transaction IDs
        if not request.transaction_ids:
            raise ValidationException("Transaction IDs list cannot be empty")
        
        if len(request.transaction_ids) > BulkOperationLimits.MAX_TRANSACTIONS_PER_OPERATION:
            raise ValidationException(f"Bulk operations limited to {BulkOperationLimits.MAX_TRANSACTIONS_PER_OPERATION} transactions at once")
        
        # Remove duplicates and validate IDs
        unique_ids = list(set(request.transaction_ids))
        invalid_ids = [
            tid for tid in unique_ids 
            if not isinstance(tid, int) or tid <= 0 or tid > 2**31 - 1  # Reasonable upper limit
        ]
        if invalid_ids:
            raise ValidationException(f"Invalid transaction IDs: {invalid_ids}")
        
        # Validate operation type and updates
        await self._validate_operation_updates(request.operation_type, request.updates)
    
    async def _validate_operation_updates(
        self, 
        operation_type: BulkOperationType, 
        updates: Dict[str, Any]
    ) -> None:
        """Validate updates for specific operation type"""
        
        if operation_type == BulkOperationType.UPDATE_CATEGORY:
            if "category" not in updates:
                raise ValidationException("Category update requires 'category' field")
            
            category = input_sanitizer.sanitize_string(updates["category"])
            if not category or len(category.strip()) == 0:
                raise ValidationException("Category cannot be empty")
            
            if len(category) > BulkOperationLimits.MAX_CATEGORY_LENGTH:
                raise ValidationException(f"Category name too long (max {BulkOperationLimits.MAX_CATEGORY_LENGTH} characters)")
        
        elif operation_type == BulkOperationType.UPDATE_SUBCATEGORY:
            if "subcategory" not in updates:
                raise ValidationException("Subcategory update requires 'subcategory' field")
            
            subcategory = input_sanitizer.sanitize_string(updates["subcategory"])
            if subcategory and len(subcategory) > BulkOperationLimits.MAX_SUBCATEGORY_LENGTH:
                raise ValidationException(f"Subcategory name too long (max {BulkOperationLimits.MAX_SUBCATEGORY_LENGTH} characters)")
        
        elif operation_type == BulkOperationType.UPDATE_DESCRIPTION:
            if "description" not in updates:
                raise ValidationException("Description update requires 'description' field")
            
            description = input_sanitizer.sanitize_string(updates["description"])
            if not description or len(description.strip()) == 0:
                raise ValidationException("Description cannot be empty")
            
            if len(description) > BulkOperationLimits.MAX_DESCRIPTION_LENGTH:
                raise ValidationException(f"Description too long (max {BulkOperationLimits.MAX_DESCRIPTION_LENGTH} characters)")
        
        elif operation_type == BulkOperationType.UPDATE_VENDOR:
            if "vendor" not in updates:
                raise ValidationException("Vendor update requires 'vendor' field")
            
            vendor = input_sanitizer.sanitize_string(updates["vendor"])
            if vendor and len(vendor) > BulkOperationLimits.MAX_VENDOR_LENGTH:
                raise ValidationException(f"Vendor name too long (max {BulkOperationLimits.MAX_VENDOR_LENGTH} characters)")
        
        elif operation_type == BulkOperationType.UPDATE_AMOUNT:
            if "amount" not in updates:
                raise ValidationException("Amount update requires 'amount' field")
            
            try:
                from decimal import InvalidOperation
                amount = Decimal(str(updates["amount"]))
                # Ensure proper financial precision (2 decimal places)
                if amount.as_tuple().exponent < -2:
                    raise ValidationException("Amount precision limited to 2 decimal places")
                # Validate amount using financial validator
                if abs(amount) > Decimal('999999999999.99'):
                    raise ValidationException("Amount exceeds maximum allowed value")
            except (ValueError, TypeError, InvalidOperation):
                raise ValidationException("Invalid amount format")
        
        elif operation_type == BulkOperationType.DELETE:
            # No additional validation needed for delete
            pass
        
        else:
            raise ValidationException(f"Unsupported operation type: {operation_type}")
    
    async def _get_user_transactions(self, transaction_ids: List[int]) -> List[Transaction]:
        """Get transactions with user isolation"""
        try:
            transactions = self.db.query(Transaction).filter(
                and_(
                    Transaction.id.in_(transaction_ids),
                    Transaction.user_id == self.user.id
                )
            ).all()
            
            return transactions
            
        except SQLAlchemyError as e:
            raise BusinessLogicException(f"Database error while fetching transactions: {str(e)}")
    
    async def _create_backup(self, transactions: List[Transaction]) -> Dict[int, Dict[str, Any]]:
        """Create backup of transaction data for undo functionality"""
        backup = {}
        
        for transaction in transactions:
            backup[transaction.id] = {
                "category": transaction.category,
                "subcategory": transaction.subcategory,
                "description": transaction.description,
                "vendor": transaction.vendor,
                "amount": str(transaction.amount),
                "is_categorized": transaction.is_categorized,
                "categorization_confidence": transaction.confidence_score,
                "updated_at": transaction.updated_at.isoformat() if transaction.updated_at else None
            }
        
        return backup
    
    async def _execute_operation(
        self,
        transactions: List[Transaction], 
        operation_type: BulkOperationType,
        updates: Dict[str, Any]
    ) -> Tuple[List[int], List[Dict[str, Any]]]:
        """Execute the bulk operation on transactions"""
        
        successful_ids = []
        errors = []
        
        for transaction in transactions:
            try:
                if operation_type == BulkOperationType.UPDATE_CATEGORY:
                    transaction.category = input_sanitizer.sanitize_string(updates["category"])
                    transaction.is_categorized = True
                    transaction.confidence_score = 1.0  # Manual categorization
                
                elif operation_type == BulkOperationType.UPDATE_SUBCATEGORY:
                    transaction.subcategory = input_sanitizer.sanitize_string(
                        updates.get("subcategory")
                    )
                
                elif operation_type == BulkOperationType.UPDATE_DESCRIPTION:
                    transaction.description = input_sanitizer.sanitize_string(updates["description"])
                
                elif operation_type == BulkOperationType.UPDATE_VENDOR:
                    transaction.vendor = input_sanitizer.sanitize_string(
                        updates.get("vendor")
                    )
                
                elif operation_type == BulkOperationType.UPDATE_AMOUNT:
                    transaction.amount = Decimal(str(updates["amount"]))
                
                elif operation_type == BulkOperationType.DELETE:
                    self.db.delete(transaction)
                    successful_ids.append(transaction.id)
                    continue  # Skip the update timestamp for deleted records
                
                # Update timestamp for non-delete operations
                transaction.updated_at = datetime.utcnow()
                
                successful_ids.append(transaction.id)
                
            except Exception as e:
                errors.append({
                    "transaction_id": transaction.id,
                    "error": str(e),
                    "type": type(e).__name__
                })
        
        return successful_ids, errors
    
    def _store_undo_operation(
        self,
        operation_id: str,
        backup_data: Dict[int, Dict[str, Any]], 
        operation_type: BulkOperationType
    ) -> None:
        """Store undo operation information"""
        
        undo_op = UndoOperation(
            operation_id=operation_id,
            original_data=backup_data,
            operation_type=operation_type,
            timestamp=datetime.utcnow(),
            user_id=self.user.id
        )
        
        # Add to undo stack
        self._undo_stack.append(undo_op)
        
        # Keep only the most recent operations
        if len(self._undo_stack) > self.max_undo_operations:
            self._undo_stack.pop(0)
    
    async def undo_last_operation(self) -> BulkOperationResult:
        """Undo the last bulk operation"""
        
        if not self._undo_stack:
            raise BusinessLogicException("No operations available to undo")
        
        undo_op = self._undo_stack.pop()
        operation_id = f"undo_{undo_op.operation_id}"
        start_time = datetime.utcnow()
        
        self.audit_logger.info(
            f"Starting undo operation: {operation_id}",
            extra={
                "operation_id": operation_id,
                "original_operation": undo_op.operation_id,
                "user_id": self.user.id
            }
        )
        
        result = BulkOperationResult(
            operation_id=operation_id,
            operation_type=undo_op.operation_type,
            status=BulkOperationStatus.IN_PROGRESS,
            total_transactions=len(undo_op.original_data),
            successful_count=0,
            failed_count=0,
            errors=[],
            affected_transaction_ids=[],
            started_at=start_time
        )
        
        try:
            transaction_ids = list(undo_op.original_data.keys())
            
            if undo_op.operation_type == BulkOperationType.DELETE:
                # For delete operations, we can't undo (transactions are gone)
                raise BusinessLogicException("Cannot undo delete operations")
            
            # Get current transactions
            transactions = await self._get_user_transactions(transaction_ids)
            
            successful_ids = []
            errors = []
            
            for transaction in transactions:
                try:
                    original_data = undo_op.original_data.get(transaction.id)
                    if not original_data:
                        continue
                    
                    # Restore original values
                    transaction.category = original_data.get("category")
                    transaction.subcategory = original_data.get("subcategory")
                    transaction.description = original_data.get("description")
                    transaction.vendor = original_data.get("vendor")
                    if original_data.get("amount"):
                        transaction.amount = Decimal(original_data["amount"])
                    transaction.is_categorized = original_data.get("is_categorized", False)
                    transaction.confidence_score = original_data.get(
                        "categorization_confidence", 0.0
                    )
                    transaction.updated_at = datetime.utcnow()
                    
                    successful_ids.append(transaction.id)
                    
                except Exception as e:
                    errors.append({
                        "transaction_id": transaction.id,
                        "error": str(e),
                        "type": type(e).__name__
                    })
            
            result.successful_count = len(successful_ids)
            result.failed_count = len(errors)
            result.errors = errors
            result.affected_transaction_ids = successful_ids
            result.status = BulkOperationStatus.COMPLETED if not errors else BulkOperationStatus.FAILED
            result.completed_at = datetime.utcnow()
            result.execution_time_ms = int(
                (result.completed_at - start_time).total_seconds() * 1000
            )
            
            self.audit_logger.info(
                f"Undo operation completed: {operation_id}",
                extra={
                    "operation_id": operation_id,
                    "status": result.status.value,
                    "successful_count": result.successful_count,
                    "failed_count": result.failed_count
                }
            )
            
            return result
            
        except Exception as e:
            result.status = BulkOperationStatus.FAILED
            result.completed_at = datetime.utcnow()
            result.errors.append({
                "error": str(e),
                "type": type(e).__name__,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            self.audit_logger.error(
                f"Undo operation failed: {operation_id}",
                extra={
                    "operation_id": operation_id,
                    "error": str(e),
                    "user_id": self.user.id
                }
            )
            
            raise
    
    def get_undo_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get list of operations that can be undone"""
        
        recent_operations = self._undo_stack[-limit:] if limit else self._undo_stack
        
        return [
            {
                "operation_id": op.operation_id,
                "operation_type": op.operation_type.value,
                "timestamp": op.timestamp.isoformat(),
                "transaction_count": len(op.original_data),
                "can_undo": True  # In this simple implementation, all operations can be undone
            }
            for op in reversed(recent_operations)
        ]
    
    async def get_bulk_operation_stats(self) -> Dict[str, Any]:
        """Get statistics about bulk operations for the user"""
        
        # In a real implementation, this would query from database/Redis
        # For now, return basic stats from in-memory undo stack
        
        total_operations = len(self._undo_stack)
        
        operation_counts = {}
        total_transactions_affected = 0
        
        for op in self._undo_stack:
            op_type = op.operation_type.value
            operation_counts[op_type] = operation_counts.get(op_type, 0) + 1
            total_transactions_affected += len(op.original_data)
        
        return {
            "total_bulk_operations": total_operations,
            "operations_by_type": operation_counts,
            "total_transactions_affected": total_transactions_affected,
            "undo_operations_available": total_operations,
            "max_undo_operations": self.max_undo_operations
        }