"""
Comprehensive test suite for Transaction Bulk Operations Service

Tests cover all bulk operation types with security, validation, 
and transaction integrity verification.
"""

import pytest
import uuid
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.transaction import Transaction
from app.models.user import User
from app.services.transaction_operations import (
    TransactionBulkOperations, BulkUpdateRequest, BulkOperationType,
    BulkOperationStatus, BulkOperationLimits, UndoOperation
)
from app.core.exceptions import ValidationException, BusinessLogicException


class TestBulkOperationsService:
    """Test suite for TransactionBulkOperations service"""
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock user for testing"""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        return user
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        db = Mock(spec=Session)
        return db
    
    @pytest.fixture
    def bulk_ops_service(self, mock_db, mock_user):
        """Create bulk operations service instance"""
        with patch('app.services.transaction_operations.security_audit_logger') as mock_logger:
            service = TransactionBulkOperations(mock_db, mock_user)
            service.audit_logger = mock_logger
            return service
    
    @pytest.fixture
    def sample_transactions(self, mock_user):
        """Create sample transactions for testing"""
        transactions = []
        for i in range(5):
            txn = Mock(spec=Transaction)
            txn.id = i + 1
            txn.user_id = mock_user.id
            txn.category = "Food"
            txn.subcategory = "Restaurants" 
            txn.description = f"Test transaction {i}"
            txn.vendor = f"Vendor {i}"
            txn.amount = Decimal("100.50")
            txn.is_categorized = True
            txn.confidence_score = 0.85
            txn.updated_at = datetime.utcnow()
            transactions.append(txn)
        return transactions

    def test_service_initialization(self, mock_db, mock_user):
        """Test service initializes correctly"""
        with patch('app.services.transaction_operations.security_audit_logger'):
            service = TransactionBulkOperations(mock_db, mock_user)
            
            assert service.db == mock_db
            assert service.user == mock_user
            assert service._undo_stack == []
            assert service.max_undo_operations == BulkOperationLimits.MAX_UNDO_OPERATIONS

    @pytest.mark.asyncio
    async def test_validate_bulk_request_valid(self, bulk_ops_service):
        """Test validation passes for valid bulk request"""
        request = BulkUpdateRequest(
            transaction_ids=[1, 2, 3],
            operation_type=BulkOperationType.UPDATE_CATEGORY,
            updates={"category": "Business Expenses"}
        )
        
        # Should not raise exception
        await bulk_ops_service._validate_bulk_request(request)

    @pytest.mark.asyncio 
    async def test_validate_bulk_request_empty_ids(self, bulk_ops_service):
        """Test validation fails for empty transaction IDs"""
        request = BulkUpdateRequest(
            transaction_ids=[],
            operation_type=BulkOperationType.UPDATE_CATEGORY,
            updates={"category": "Business Expenses"}
        )
        
        with pytest.raises(ValidationException, match="Transaction IDs list cannot be empty"):
            await bulk_ops_service._validate_bulk_request(request)

    @pytest.mark.asyncio
    async def test_validate_bulk_request_too_many_transactions(self, bulk_ops_service):
        """Test validation fails for too many transactions"""
        # Create request with more than the limit
        large_id_list = list(range(1, BulkOperationLimits.MAX_TRANSACTIONS_PER_OPERATION + 2))
        request = BulkUpdateRequest(
            transaction_ids=large_id_list,
            operation_type=BulkOperationType.UPDATE_CATEGORY,
            updates={"category": "Business Expenses"}
        )
        
        with pytest.raises(ValidationException, match="Bulk operations limited to"):
            await bulk_ops_service._validate_bulk_request(request)

    @pytest.mark.asyncio
    async def test_validate_bulk_request_invalid_ids(self, bulk_ops_service):
        """Test validation fails for invalid transaction IDs"""
        request = BulkUpdateRequest(
            transaction_ids=[1, -5, "invalid", 0, 2**32],  # Mix of invalid IDs
            operation_type=BulkOperationType.UPDATE_CATEGORY,
            updates={"category": "Business Expenses"}
        )
        
        with pytest.raises(ValidationException, match="Invalid transaction IDs"):
            await bulk_ops_service._validate_bulk_request(request)

    @pytest.mark.asyncio
    async def test_validate_category_update(self, bulk_ops_service):
        """Test category update validation"""
        # Valid category
        await bulk_ops_service._validate_operation_updates(
            BulkOperationType.UPDATE_CATEGORY,
            {"category": "Valid Category"}
        )
        
        # Missing category
        with pytest.raises(ValidationException, match="Category update requires 'category' field"):
            await bulk_ops_service._validate_operation_updates(
                BulkOperationType.UPDATE_CATEGORY,
                {}
            )
        
        # Empty category
        with pytest.raises(ValidationException, match="Category cannot be empty"):
            await bulk_ops_service._validate_operation_updates(
                BulkOperationType.UPDATE_CATEGORY,
                {"category": "   "}
            )
        
        # Category too long
        long_category = "x" * (BulkOperationLimits.MAX_CATEGORY_LENGTH + 1)
        with pytest.raises(ValidationException, match="Category name too long"):
            await bulk_ops_service._validate_operation_updates(
                BulkOperationType.UPDATE_CATEGORY,
                {"category": long_category}
            )

    @pytest.mark.asyncio
    async def test_validate_amount_update(self, bulk_ops_service):
        """Test amount update validation"""
        # Valid amount
        await bulk_ops_service._validate_operation_updates(
            BulkOperationType.UPDATE_AMOUNT,
            {"amount": "123.45"}
        )
        
        # Missing amount
        with pytest.raises(ValidationException, match="Amount update requires 'amount' field"):
            await bulk_ops_service._validate_operation_updates(
                BulkOperationType.UPDATE_AMOUNT,
                {}
            )
        
        # Invalid amount format
        with pytest.raises(ValidationException, match="Invalid amount format"):
            await bulk_ops_service._validate_operation_updates(
                BulkOperationType.UPDATE_AMOUNT,
                {"amount": "not_a_number"}
            )
        
        # Amount too large
        with pytest.raises(ValidationException, match="Amount exceeds maximum allowed value"):
            await bulk_ops_service._validate_operation_updates(
                BulkOperationType.UPDATE_AMOUNT,
                {"amount": "1000000000000.00"}
            )
        
        # Too many decimal places
        with pytest.raises(ValidationException, match="Amount precision limited to 2 decimal places"):
            await bulk_ops_service._validate_operation_updates(
                BulkOperationType.UPDATE_AMOUNT,
                {"amount": "123.456"}
            )

    @pytest.mark.asyncio
    async def test_validate_description_update(self, bulk_ops_service):
        """Test description update validation"""
        # Valid description
        await bulk_ops_service._validate_operation_updates(
            BulkOperationType.UPDATE_DESCRIPTION,
            {"description": "Valid description"}
        )
        
        # Description too long
        long_desc = "x" * (BulkOperationLimits.MAX_DESCRIPTION_LENGTH + 1)
        with pytest.raises(ValidationException, match="Description too long"):
            await bulk_ops_service._validate_operation_updates(
                BulkOperationType.UPDATE_DESCRIPTION,
                {"description": long_desc}
            )

    @pytest.mark.asyncio
    async def test_get_user_transactions_success(self, bulk_ops_service, sample_transactions):
        """Test retrieving user transactions successfully"""
        # Mock database query
        bulk_ops_service.db.query.return_value.filter.return_value.all.return_value = sample_transactions
        
        transaction_ids = [1, 2, 3]
        result = await bulk_ops_service._get_user_transactions(transaction_ids)
        
        assert result == sample_transactions
        bulk_ops_service.db.query.assert_called_once_with(Transaction)

    @pytest.mark.asyncio
    async def test_get_user_transactions_database_error(self, bulk_ops_service):
        """Test database error handling in get_user_transactions"""
        # Mock database error
        bulk_ops_service.db.query.side_effect = SQLAlchemyError("Database error")
        
        with pytest.raises(BusinessLogicException, match="Database error while fetching transactions"):
            await bulk_ops_service._get_user_transactions([1, 2, 3])

    @pytest.mark.asyncio
    async def test_create_backup(self, bulk_ops_service, sample_transactions):
        """Test creating backup of transaction data"""
        backup = await bulk_ops_service._create_backup(sample_transactions)
        
        assert len(backup) == len(sample_transactions)
        for i, txn in enumerate(sample_transactions):
            assert backup[txn.id]["category"] == txn.category
            assert backup[txn.id]["description"] == txn.description
            assert backup[txn.id]["amount"] == str(txn.amount)
            assert backup[txn.id]["is_categorized"] == txn.is_categorized

    @pytest.mark.asyncio
    async def test_execute_operation_category_update(self, bulk_ops_service, sample_transactions):
        """Test executing category update operation"""
        operation_type = BulkOperationType.UPDATE_CATEGORY
        updates = {"category": "New Category"}
        
        successful_ids, errors = await bulk_ops_service._execute_operation(
            sample_transactions, operation_type, updates
        )
        
        assert len(successful_ids) == len(sample_transactions)
        assert len(errors) == 0
        
        # Verify all transactions were updated
        for txn in sample_transactions:
            assert txn.category == "New Category"
            assert txn.is_categorized == True
            assert txn.confidence_score == 1.0  # Manual categorization

    @pytest.mark.asyncio
    async def test_execute_operation_amount_update(self, bulk_ops_service, sample_transactions):
        """Test executing amount update operation"""
        operation_type = BulkOperationType.UPDATE_AMOUNT
        updates = {"amount": "250.75"}
        
        successful_ids, errors = await bulk_ops_service._execute_operation(
            sample_transactions, operation_type, updates
        )
        
        assert len(successful_ids) == len(sample_transactions)
        assert len(errors) == 0
        
        # Verify all transactions were updated
        for txn in sample_transactions:
            assert txn.amount == Decimal("250.75")

    @pytest.mark.asyncio
    async def test_execute_operation_delete(self, bulk_ops_service, sample_transactions):
        """Test executing delete operation"""
        operation_type = BulkOperationType.DELETE
        updates = {}
        
        successful_ids, errors = await bulk_ops_service._execute_operation(
            sample_transactions, operation_type, updates
        )
        
        assert len(successful_ids) == len(sample_transactions)
        assert len(errors) == 0
        
        # Verify all transactions were marked for deletion
        for txn in sample_transactions:
            bulk_ops_service.db.delete.assert_any_call(txn)

    @pytest.mark.asyncio
    async def test_execute_operation_with_errors(self, bulk_ops_service, sample_transactions):
        """Test executing operation with some failures"""
        # Make one transaction fail
        sample_transactions[2].category = None  # This should cause an error
        
        operation_type = BulkOperationType.UPDATE_CATEGORY
        updates = {"category": "New Category"}
        
        with patch('app.core.security_utils.input_sanitizer.sanitize_string') as mock_sanitize:
            # Make the sanitizer raise an exception for one transaction
            def side_effect(value):
                if value == "New Category":
                    raise ValueError("Sanitization failed")
                return value
            mock_sanitize.side_effect = side_effect
            
            successful_ids, errors = await bulk_ops_service._execute_operation(
                sample_transactions, operation_type, updates
            )
        
        # Should have some errors
        assert len(errors) > 0
        assert len(successful_ids) < len(sample_transactions)

    def test_store_undo_operation(self, bulk_ops_service):
        """Test storing undo operation"""
        operation_id = "test_operation"
        backup_data = {1: {"category": "Old Category"}, 2: {"category": "Another Category"}}
        operation_type = BulkOperationType.UPDATE_CATEGORY
        
        bulk_ops_service._store_undo_operation(operation_id, backup_data, operation_type)
        
        assert len(bulk_ops_service._undo_stack) == 1
        undo_op = bulk_ops_service._undo_stack[0]
        assert undo_op.operation_id == operation_id
        assert undo_op.original_data == backup_data
        assert undo_op.operation_type == operation_type
        assert undo_op.user_id == bulk_ops_service.user.id

    def test_undo_stack_limit(self, bulk_ops_service):
        """Test undo stack respects maximum limit"""
        # Add operations beyond the limit
        for i in range(BulkOperationLimits.MAX_UNDO_OPERATIONS + 5):
            bulk_ops_service._store_undo_operation(
                f"op_{i}", {1: {"category": f"Cat_{i}"}}, BulkOperationType.UPDATE_CATEGORY
            )
        
        # Should only keep the maximum number
        assert len(bulk_ops_service._undo_stack) == BulkOperationLimits.MAX_UNDO_OPERATIONS
        
        # Should have the most recent operations
        last_op = bulk_ops_service._undo_stack[-1]
        assert "op_" in last_op.operation_id

    @pytest.mark.asyncio
    async def test_undo_last_operation_no_operations(self, bulk_ops_service):
        """Test undo fails when no operations are available"""
        with pytest.raises(BusinessLogicException, match="No operations available to undo"):
            await bulk_ops_service.undo_last_operation()

    @pytest.mark.asyncio
    async def test_undo_delete_operation_fails(self, bulk_ops_service):
        """Test undo fails for delete operations"""
        # Add a delete operation to undo stack
        bulk_ops_service._store_undo_operation(
            "delete_op", {1: {"category": "Old"}}, BulkOperationType.DELETE
        )
        
        with pytest.raises(BusinessLogicException, match="Cannot undo delete operations"):
            await bulk_ops_service.undo_last_operation()

    @pytest.mark.asyncio 
    async def test_undo_last_operation_success(self, bulk_ops_service, sample_transactions):
        """Test successful undo operation"""
        # Setup: Add undo operation to stack
        backup_data = {1: {"category": "Old Category", "amount": "100.00", "is_categorized": False}}
        bulk_ops_service._store_undo_operation(
            "test_op", backup_data, BulkOperationType.UPDATE_CATEGORY
        )
        
        # Mock database query to return the transaction
        bulk_ops_service.db.query.return_value.filter.return_value.all.return_value = [sample_transactions[0]]
        
        result = await bulk_ops_service.undo_last_operation()
        
        assert result.status == BulkOperationStatus.COMPLETED
        assert result.successful_count == 1
        assert result.failed_count == 0
        assert len(bulk_ops_service._undo_stack) == 0  # Operation should be removed from stack

    def test_get_undo_history(self, bulk_ops_service):
        """Test retrieving undo history"""
        # Add some operations
        for i in range(3):
            bulk_ops_service._store_undo_operation(
                f"op_{i}", {1: {"category": f"Cat_{i}"}}, BulkOperationType.UPDATE_CATEGORY
            )
        
        history = bulk_ops_service.get_undo_history(limit=5)
        
        assert len(history) == 3
        # Should be in reverse chronological order (most recent first)
        assert history[0]["operation_id"] == "op_2"
        assert history[1]["operation_id"] == "op_1"
        assert history[2]["operation_id"] == "op_0"
        
        for item in history:
            assert "operation_type" in item
            assert "timestamp" in item
            assert "transaction_count" in item
            assert "can_undo" in item

    @pytest.mark.asyncio
    async def test_get_bulk_operation_stats(self, bulk_ops_service):
        """Test retrieving bulk operation statistics"""
        # Add some operations to stack
        bulk_ops_service._store_undo_operation(
            "op1", {1: {"category": "Cat1"}}, BulkOperationType.UPDATE_CATEGORY
        )
        bulk_ops_service._store_undo_operation(
            "op2", {2: {"description": "Desc2"}}, BulkOperationType.UPDATE_DESCRIPTION
        )
        bulk_ops_service._store_undo_operation(
            "op3", {3: {"category": "Cat3"}}, BulkOperationType.UPDATE_CATEGORY
        )
        
        stats = await bulk_ops_service.get_bulk_operation_stats()
        
        assert stats["total_bulk_operations"] == 3
        assert stats["operations_by_type"]["update_category"] == 2
        assert stats["operations_by_type"]["update_description"] == 1
        assert stats["total_transactions_affected"] == 3
        assert stats["undo_operations_available"] == 3
        assert stats["max_undo_operations"] == BulkOperationLimits.MAX_UNDO_OPERATIONS


class TestBulkOperationsIntegration:
    """Integration tests for the complete bulk operations workflow"""
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock user for testing"""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        return user
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session with transaction management"""
        db = Mock(spec=Session)
        return db
    
    @pytest.fixture
    def sample_transactions(self, mock_user):
        """Create sample transactions for testing"""
        transactions = []
        for i in range(3):
            txn = Mock(spec=Transaction)
            txn.id = i + 1
            txn.user_id = mock_user.id
            txn.category = "Food"
            txn.subcategory = "Restaurants"
            txn.description = f"Transaction {i}"
            txn.vendor = f"Vendor {i}"
            txn.amount = Decimal("50.00")
            txn.is_categorized = False
            txn.confidence_score = 0.5
            txn.updated_at = datetime.utcnow()
            transactions.append(txn)
        return transactions

    @pytest.mark.asyncio
    async def test_complete_bulk_update_workflow(self, mock_db, mock_user, sample_transactions):
        """Test complete bulk update operation workflow"""
        with patch('app.services.transaction_operations.security_audit_logger') as mock_logger:
            bulk_ops = TransactionBulkOperations(mock_db, mock_user)
            bulk_ops.audit_logger = mock_logger
            
            # Mock database query
            mock_db.query.return_value.filter.return_value.all.return_value = sample_transactions
            
            # Create bulk update request
            request = BulkUpdateRequest(
                transaction_ids=[1, 2, 3],
                operation_type=BulkOperationType.UPDATE_CATEGORY,
                updates={"category": "Business Expenses"},
                validate_before_execute=True,
                create_backup=True
            )
            
            # Execute the bulk operation
            with patch('app.services.transaction_operations.financial_transaction') as mock_decorator:
                # Make the decorator pass through the function call
                mock_decorator.side_effect = lambda func: func
                
                result = await bulk_ops.execute_bulk_update(request)
            
            # Verify results
            assert result.status == BulkOperationStatus.COMPLETED
            assert result.successful_count == 3
            assert result.failed_count == 0
            assert len(result.affected_transaction_ids) == 3
            assert result.operation_type == BulkOperationType.UPDATE_CATEGORY
            
            # Verify transactions were updated
            for txn in sample_transactions:
                assert txn.category == "Business Expenses"
                assert txn.is_categorized == True
                assert txn.confidence_score == 1.0
            
            # Verify backup was created (undo operation available)
            assert len(bulk_ops._undo_stack) == 1
            
            # Verify audit logging
            assert mock_logger.info.call_count >= 2  # Start and completion logs

    @pytest.mark.asyncio
    async def test_bulk_operation_with_validation_failure(self, mock_db, mock_user):
        """Test bulk operation fails validation properly"""
        with patch('app.services.transaction_operations.security_audit_logger'):
            bulk_ops = TransactionBulkOperations(mock_db, mock_user)
            
            # Create invalid request (empty transaction IDs)
            request = BulkUpdateRequest(
                transaction_ids=[],
                operation_type=BulkOperationType.UPDATE_CATEGORY,
                updates={"category": "Business Expenses"}
            )
            
            with pytest.raises(ValidationException):
                await bulk_ops.execute_bulk_update(request)

    @pytest.mark.asyncio
    async def test_bulk_operation_rollback_on_error(self, mock_db, mock_user, sample_transactions):
        """Test bulk operation rolls back on database error"""
        with patch('app.services.transaction_operations.security_audit_logger'):
            bulk_ops = TransactionBulkOperations(mock_db, mock_user)
            
            # Mock database query to succeed initially but fail during execution
            mock_db.query.return_value.filter.return_value.all.return_value = sample_transactions
            
            request = BulkUpdateRequest(
                transaction_ids=[1, 2, 3],
                operation_type=BulkOperationType.UPDATE_CATEGORY,
                updates={"category": "Business Expenses"}
            )
            
            # Mock a database error during execution
            with patch('app.core.security_utils.input_sanitizer.sanitize_string', 
                      side_effect=SQLAlchemyError("Database connection failed")):
                
                with patch('app.services.transaction_operations.financial_transaction') as mock_decorator:
                    mock_decorator.side_effect = lambda func: func
                    
                    with pytest.raises(SQLAlchemyError):
                        await bulk_ops.execute_bulk_update(request)


if __name__ == "__main__":
    pytest.main([__file__])