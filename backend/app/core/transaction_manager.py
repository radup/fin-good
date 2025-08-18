"""
Comprehensive database transaction manager for financial operations.
Provides robust transaction handling with automatic rollback on errors,
savepoint management, and comprehensive logging for data integrity.
"""

import logging
from contextlib import contextmanager
from typing import Any, Dict, Optional, Union, Callable, TypeVar, Generator
from functools import wraps
import traceback
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy.exc import (
    SQLAlchemyError, 
    IntegrityError, 
    OperationalError, 
    DisconnectionError,
    DataError,
    InvalidRequestError
)
from sqlalchemy import text

from app.core.database import get_db, SessionLocal
from app.core.audit_logger import SecurityAuditLogger

# Set up logging
logger = logging.getLogger(__name__)

# Type variable for decorated functions
F = TypeVar('F', bound=Callable[..., Any])


class TransactionStatus(Enum):
    """Transaction status enumeration for tracking"""
    STARTED = "started"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class TransactionError(Exception):
    """Custom exception for transaction-related errors"""
    def __init__(self, message: str, original_error: Optional[Exception] = None, transaction_id: Optional[str] = None):
        self.message = message
        self.original_error = original_error
        self.transaction_id = transaction_id
        super().__init__(message)


class SavepointManager:
    """Manages savepoints within transactions for nested rollback scenarios"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.savepoints: Dict[str, str] = {}
        self.savepoint_counter = 0
    
    def create_savepoint(self, name: Optional[str] = None) -> str:
        """Create a savepoint and return its name"""
        if name is None:
            self.savepoint_counter += 1
            name = f"sp_{self.savepoint_counter}_{uuid.uuid4().hex[:8]}"
        
        try:
            self.db_session.execute(text(f"SAVEPOINT {name}"))
            self.savepoints[name] = name
            logger.debug(f"Created savepoint: {name}")
            return name
        except SQLAlchemyError as e:
            logger.error(f"Failed to create savepoint {name}: {str(e)}")
            raise TransactionError(f"Failed to create savepoint: {str(e)}", e)
    
    def rollback_to_savepoint(self, name: str):
        """Rollback to a specific savepoint"""
        if name not in self.savepoints:
            raise TransactionError(f"Savepoint {name} not found")
        
        try:
            self.db_session.execute(text(f"ROLLBACK TO SAVEPOINT {name}"))
            logger.info(f"Rolled back to savepoint: {name}")
        except SQLAlchemyError as e:
            logger.error(f"Failed to rollback to savepoint {name}: {str(e)}")
            raise TransactionError(f"Failed to rollback to savepoint: {str(e)}", e)
    
    def release_savepoint(self, name: str):
        """Release a savepoint"""
        if name not in self.savepoints:
            return
        
        try:
            self.db_session.execute(text(f"RELEASE SAVEPOINT {name}"))
            del self.savepoints[name]
            logger.debug(f"Released savepoint: {name}")
        except SQLAlchemyError as e:
            logger.warning(f"Failed to release savepoint {name}: {str(e)}")


class TransactionManager:
    """
    Comprehensive transaction manager for financial operations.
    Provides automatic rollback, logging, and integrity guarantees.
    """
    
    def __init__(self, db_session: Optional[Session] = None, user_id: Optional[int] = None):
        self.db_session = db_session
        self.user_id = user_id
        self.transaction_id = str(uuid.uuid4())
        self.start_time = datetime.utcnow()
        self.status = TransactionStatus.STARTED
        self.savepoint_manager: Optional[SavepointManager] = None
        self.audit_logger = SecurityAuditLogger()
        
        # Track transaction metadata
        self.metadata: Dict[str, Any] = {
            'transaction_id': self.transaction_id,
            'user_id': user_id,
            'start_time': self.start_time,
            'operations': []
        }
    
    @contextmanager
    def transaction(
        self, 
        db_session: Optional[Session] = None,
        isolation_level: Optional[str] = None
    ) -> Generator['TransactionManager', None, None]:
        """
        Context manager for database transactions with automatic rollback on errors.
        
        Args:
            db_session: Optional database session, creates new one if not provided
            isolation_level: Optional isolation level for the transaction
        
        Yields:
            TransactionManager instance
        
        Raises:
            TransactionError: On transaction failures
        """
        session_created = False
        
        try:
            # Use provided session or create new one
            if db_session is None:
                self.db_session = SessionLocal()
                session_created = True
            else:
                self.db_session = db_session
            
            # Set isolation level if specified
            if isolation_level:
                self.db_session.execute(text(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}"))
            
            # Initialize savepoint manager
            self.savepoint_manager = SavepointManager(self.db_session)
            
            # Log transaction start
            self._log_transaction_start()
            
            # Begin transaction
            if session_created:
                self.db_session.begin()
            
            yield self
            
            # Commit if we reach here without exceptions
            self._commit_transaction()
            
        except Exception as e:
            # Rollback on any exception
            self._rollback_transaction(e)
            raise
        
        finally:
            # Clean up session if we created it
            if session_created and self.db_session:
                try:
                    self.db_session.close()
                except Exception as e:
                    logger.warning(f"Error closing session: {str(e)}")
    
    def add_operation(self, operation_type: str, details: Dict[str, Any]):
        """Add operation to transaction log"""
        operation = {
            'type': operation_type,
            'details': details,
            'timestamp': datetime.utcnow()
        }
        self.metadata['operations'].append(operation)
    
    def create_savepoint(self, name: Optional[str] = None) -> str:
        """Create a savepoint for nested rollback scenarios"""
        if not self.savepoint_manager:
            raise TransactionError("Savepoint manager not initialized")
        
        savepoint_name = self.savepoint_manager.create_savepoint(name)
        self.add_operation('create_savepoint', {'name': savepoint_name})
        return savepoint_name
    
    def rollback_to_savepoint(self, name: str):
        """Rollback to a specific savepoint"""
        if not self.savepoint_manager:
            raise TransactionError("Savepoint manager not initialized")
        
        self.savepoint_manager.rollback_to_savepoint(name)
        self.add_operation('rollback_to_savepoint', {'name': name})
    
    def release_savepoint(self, name: str):
        """Release a savepoint"""
        if not self.savepoint_manager:
            raise TransactionError("Savepoint manager not initialized")
        
        self.savepoint_manager.release_savepoint(name)
        self.add_operation('release_savepoint', {'name': name})
    
    def _commit_transaction(self):
        """Commit the transaction with logging"""
        try:
            if self.db_session:
                self.db_session.commit()
            
            self.status = TransactionStatus.COMMITTED
            self._log_transaction_end()
            
            logger.info(f"Transaction {self.transaction_id} committed successfully")
            
        except SQLAlchemyError as e:
            self.status = TransactionStatus.FAILED
            logger.error(f"Failed to commit transaction {self.transaction_id}: {str(e)}")
            raise TransactionError(f"Transaction commit failed: {str(e)}", e, self.transaction_id)
    
    def _rollback_transaction(self, error: Exception):
        """Rollback the transaction with comprehensive logging"""
        try:
            if self.db_session:
                self.db_session.rollback()
            
            self.status = TransactionStatus.ROLLED_BACK
            self.metadata['error'] = {
                'type': type(error).__name__,
                'message': str(error),
                'traceback': traceback.format_exc()
            }
            
            self._log_transaction_rollback(error)
            
            logger.error(f"Transaction {self.transaction_id} rolled back due to error: {str(error)}")
            
        except Exception as rollback_error:
            self.status = TransactionStatus.FAILED
            logger.critical(
                f"CRITICAL: Failed to rollback transaction {self.transaction_id}. "
                f"Original error: {str(error)}. Rollback error: {str(rollback_error)}"
            )
            # This is a critical error - database may be in inconsistent state
            raise TransactionError(
                f"Critical: Failed to rollback transaction: {str(rollback_error)}", 
                rollback_error, 
                self.transaction_id
            )
    
    def _log_transaction_start(self):
        """Log transaction start"""
        logger.info(f"Starting transaction {self.transaction_id} for user {self.user_id}")
        
        # Audit log for security
        if self.user_id:
            self.audit_logger.log_event(
                event_type="transaction_start",
                user_id=self.user_id,
                details={
                    'transaction_id': self.transaction_id,
                    'start_time': self.start_time.isoformat()
                }
            )
    
    def _log_transaction_end(self):
        """Log successful transaction completion"""
        end_time = datetime.utcnow()
        duration = (end_time - self.start_time).total_seconds()
        
        self.metadata['end_time'] = end_time
        self.metadata['duration_seconds'] = duration
        self.metadata['status'] = self.status.value
        
        logger.info(
            f"Transaction {self.transaction_id} completed successfully. "
            f"Duration: {duration:.3f}s, Operations: {len(self.metadata['operations'])}"
        )
        
        # Audit log
        if self.user_id:
            self.audit_logger.log_event(
                event_type="transaction_commit",
                user_id=self.user_id,
                details={
                    'transaction_id': self.transaction_id,
                    'duration_seconds': duration,
                    'operations_count': len(self.metadata['operations'])
                }
            )
    
    def _log_transaction_rollback(self, error: Exception):
        """Log transaction rollback with error details"""
        end_time = datetime.utcnow()
        duration = (end_time - self.start_time).total_seconds()
        
        self.metadata['end_time'] = end_time
        self.metadata['duration_seconds'] = duration
        self.metadata['status'] = self.status.value
        
        logger.error(
            f"Transaction {self.transaction_id} rolled back. "
            f"Duration: {duration:.3f}s, Error: {type(error).__name__}: {str(error)}"
        )
        
        # Audit log for security monitoring
        if self.user_id:
            self.audit_logger.log_event(
                event_type="transaction_rollback",
                user_id=self.user_id,
                details={
                    'transaction_id': self.transaction_id,
                    'duration_seconds': duration,
                    'error_type': type(error).__name__,
                    'error_message': str(error),
                    'operations_count': len(self.metadata['operations'])
                }
            )


def with_transaction(
    isolation_level: Optional[str] = None,
    user_id_param: str = "user_id",
    db_param: str = "db"
):
    """
    Decorator to automatically wrap functions in database transactions.
    
    Args:
        isolation_level: Transaction isolation level
        user_id_param: Parameter name for user ID (for audit logging)
        db_param: Parameter name for database session
    
    Example:
        @with_transaction(isolation_level="SERIALIZABLE")
        async def transfer_funds(user_id: int, from_account: int, to_account: int, amount: float, db: Session):
            # This function will automatically be wrapped in a transaction
            # with rollback on any exception
            pass
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user_id and db_session from function parameters
            user_id = kwargs.get(user_id_param)
            db_session = kwargs.get(db_param)
            
            if not db_session:
                raise ValueError(f"Function {func.__name__} must have a '{db_param}' parameter")
            
            # Create transaction manager
            tx_manager = TransactionManager(user_id=user_id)
            
            # Execute function within transaction
            with tx_manager.transaction(db_session=db_session, isolation_level=isolation_level):
                # Add transaction manager to kwargs for functions that need it
                kwargs['tx_manager'] = tx_manager
                return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def with_savepoint():
    """
    Decorator to wrap a function execution in a savepoint.
    The function must be called within an existing transaction context.
    
    Example:
        @with_savepoint()
        async def risky_operation(tx_manager: TransactionManager, ...):
            # This operation will be wrapped in a savepoint
            # If it fails, only this operation will be rolled back
            pass
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            tx_manager = kwargs.get('tx_manager')
            
            if not tx_manager or not isinstance(tx_manager, TransactionManager):
                raise ValueError(f"Function {func.__name__} requires a TransactionManager in kwargs")
            
            # Create savepoint
            savepoint_name = tx_manager.create_savepoint(f"{func.__name__}_{uuid.uuid4().hex[:8]}")
            
            try:
                result = await func(*args, **kwargs)
                # Release savepoint on success
                tx_manager.release_savepoint(savepoint_name)
                return result
            
            except Exception as e:
                # Rollback to savepoint on error
                tx_manager.rollback_to_savepoint(savepoint_name)
                logger.warning(f"Rolled back to savepoint {savepoint_name} due to error in {func.__name__}: {str(e)}")
                raise
        
        return wrapper
    
    return decorator


# Utility functions for common transaction patterns
@contextmanager
def financial_transaction(
    user_id: int,
    operation_type: str,
    db_session: Optional[Session] = None
) -> Generator[TransactionManager, None, None]:
    """
    Context manager specifically for financial operations.
    Uses SERIALIZABLE isolation level for maximum consistency.
    
    Args:
        user_id: User performing the operation
        operation_type: Type of financial operation (for logging)
        db_session: Optional database session
    
    Example:
        with financial_transaction(user_id=123, operation_type="fund_transfer") as tx:
            # Perform financial operations here
            # Automatic rollback on any error
            pass
    """
    tx_manager = TransactionManager(user_id=user_id)
    
    with tx_manager.transaction(db_session=db_session, isolation_level="SERIALIZABLE"):
        tx_manager.add_operation('financial_operation_start', {
            'operation_type': operation_type,
            'user_id': user_id
        })
        
        yield tx_manager


def validate_transaction_integrity(db_session: Session) -> Dict[str, Any]:
    """
    Validate database integrity after transaction operations.
    Returns validation results.
    
    Args:
        db_session: Database session to validate
    
    Returns:
        Dictionary with validation results
    """
    validation_results = {
        'status': 'valid',
        'checks': [],
        'errors': []
    }
    
    try:
        # Check basic connectivity
        db_session.execute(text("SELECT 1"))
        validation_results['checks'].append('database_connectivity')
        
        # Check transaction state
        if db_session.in_transaction():
            validation_results['checks'].append('transaction_active')
        else:
            validation_results['checks'].append('transaction_inactive')
        
        # Additional integrity checks can be added here
        # - Check for orphaned records
        # - Validate foreign key constraints
        # - Check balance calculations
        
        logger.debug(f"Transaction integrity validation passed: {validation_results}")
        
    except Exception as e:
        validation_results['status'] = 'invalid'
        validation_results['errors'].append({
            'type': type(e).__name__,
            'message': str(e)
        })
        logger.error(f"Transaction integrity validation failed: {str(e)}")
    
    return validation_results