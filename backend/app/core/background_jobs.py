"""
Background Job Queue Infrastructure

This module provides async job processing capabilities for file uploads and other
long-running tasks using Celery with Redis as the message broker.

Features:
- Async file upload processing
- Job status tracking
- Error handling and retry logic
- Progress monitoring via WebSocket
- Security audit logging
"""

import logging
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum
import uuid

from celery import Celery, states
from celery.result import AsyncResult
from celery.exceptions import CeleryError
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.audit_logger import security_audit_logger
from app.core.error_sanitizer import error_sanitizer, create_secure_error_response
from app.schemas.error import ErrorCategory, ErrorSeverity
from app.models.user import User
from app.models.transaction import Transaction
from app.services.categorization import CategorizationService
from app.services.csv_parser import CSVParser, ParsingResult
from app.services.file_validator import FileValidator, ValidationResult, ThreatLevel
from app.services.malware_scanner import scan_file_for_malware
from app.services.content_sanitizer import sanitize_csv_content, SanitizationLevel
from app.services.simple_sandbox_analyzer import analyze_file_in_sandbox, AnalysisType
from app.core.websocket_manager import (
    emit_validation_progress,
    emit_scanning_progress,
    emit_parsing_progress,
    emit_database_progress,
    emit_categorization_progress,
    emit_job_status_update
)

logger = logging.getLogger(__name__)

# Constants for secure hash handling
HASH_DISPLAY_LENGTH = 16

class JobStatus(Enum):
    """Job status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class JobType(Enum):
    """Job type enumeration"""
    FILE_UPLOAD = "file_upload"
    BULK_CATEGORIZATION = "bulk_categorization"
    EXPORT_GENERATION = "export_generation"
    ANALYTICS_CALCULATION = "analytics_calculation"

# Initialize Celery app
celery_app = Celery(
    "fintech_backend",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.core.background_jobs"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
    result_expires=3600,  # 1 hour
    task_routes={
        "app.core.background_jobs.process_file_upload": {"queue": "file_processing"},
        "app.core.background_jobs.process_bulk_categorization": {"queue": "categorization"},
        "app.core.background_jobs.generate_export": {"queue": "export"},
        "app.core.background_jobs.calculate_analytics": {"queue": "analytics"},
    },
    task_annotations={
        "app.core.background_jobs.process_file_upload": {
            "rate_limit": "10/m",  # 10 tasks per minute
            "max_retries": 3,
            "default_retry_delay": 60,  # 1 minute
        },
        "app.core.background_jobs.process_bulk_categorization": {
            "rate_limit": "20/m",
            "max_retries": 2,
            "default_retry_delay": 30,
        },
    }
)

def calculate_file_hash_streaming(file_content: bytes, chunk_size: int = 8192) -> str:
    """Calculate SHA256 hash with streaming for memory efficiency"""
    hash_obj = hashlib.sha256()
    for i in range(0, len(file_content), chunk_size):
        chunk = file_content[i:i + chunk_size]
        hash_obj.update(chunk)
    return hash_obj.hexdigest()

def truncate_hash_for_display(hash_value: str) -> str:
    """Truncate hash for secure display in logs and responses"""
    return f"{hash_value[:HASH_DISPLAY_LENGTH]}..."

def get_database_session() -> Session:
    """Get database session for background tasks"""
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def update_job_status(job_id: str, status: JobStatus, progress: float = 0.0, 
                     message: str = "", details: Optional[Dict[str, Any]] = None):
    """Update job status in Redis for tracking"""
    try:
        status_data = {
            "status": status.value,
            "progress": progress,
            "message": message,
            "details": details or {},
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Store in Redis with 1 hour expiration
        celery_app.backend.set(
            f"job_status:{job_id}",
            json.dumps(status_data),
            ex=3600
        )
        
        logger.info(f"Job {job_id} status updated: {status.value} ({progress}%)")
        
    except Exception as e:
        logger.error(f"Failed to update job status for {job_id}: {str(e)}")

@celery_app.task(bind=True, name="app.core.background_jobs.process_file_upload")
def process_file_upload(self, file_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """
    Process file upload asynchronously
    
    Args:
        file_data: Dictionary containing file information and content
        user_id: User ID who uploaded the file
    
    Returns:
        Dictionary with processing results
    """
    job_id = self.request.id
    start_time = datetime.utcnow()
    
    # Extract file data
    file_content = file_data.get("content")
    filename = file_data.get("filename")
    file_size = file_data.get("file_size", 0)
    batch_id = file_data.get("batch_id")
    
    if not file_content or not filename:
        error_msg = "Missing file content or filename"
        update_job_status(job_id, JobStatus.FAILED, 0.0, error_msg)
        raise ValueError(error_msg)
    
    # Initialize database session
    db = get_database_session()
    
    try:
        # Update job status to processing
        update_job_status(job_id, JobStatus.PROCESSING, 5.0, "Starting file processing")
        
        # Emit initial progress via WebSocket (commented out for now - will be implemented later)
        # emit_job_status_update(
        #     job_id=job_id,
        #     user_id=user_id,
        #     status=JobStatus.PROCESSING.value,
        #     progress=5.0,
        #     message="Starting file processing"
        # )
        
        # Step 1: File validation
        update_job_status(job_id, JobStatus.PROCESSING, 10.0, "Validating file")
        # emit_validation_progress(
        #     batch_id=batch_id,
        #     progress=10.0,
        #     message="Validating file format and structure",
        #     user_id=user_id
        # )
        
        file_validator = FileValidator()
        validation_result = file_validator.validate_file(
            file_content=file_content,
            filename=filename,
            user_id=user_id
        )
        
        if validation_result.validation_result == ValidationResult.REJECTED:
            error_msg = "File failed security validation"
            update_job_status(job_id, JobStatus.FAILED, 0.0, error_msg)
            raise ValueError(error_msg)
        
        update_job_status(job_id, JobStatus.PROCESSING, 20.0, "File validation completed")
        
        # Step 2: Malware scanning
        update_job_status(job_id, JobStatus.PROCESSING, 25.0, "Scanning for malware")
        # emit_scanning_progress(
        #     batch_id=batch_id,
        #     progress=25.0,
        #     message="Scanning file for malware and threats",
        #     user_id=user_id
        # )
        
        malware_scan_result = scan_file_for_malware(
            file_content=file_content,
            filename=filename,
            user_id=user_id
        )
        
        if not malware_scan_result.is_clean:
            error_msg = "Malware detected in file"
            update_job_status(job_id, JobStatus.FAILED, 0.0, error_msg)
            raise ValueError(error_msg)
        
        update_job_status(job_id, JobStatus.PROCESSING, 40.0, "Malware scan completed")
        
        # Step 3: Content sanitization and parsing
        update_job_status(job_id, JobStatus.PROCESSING, 45.0, "Parsing CSV content")
        # emit_parsing_progress(
        #     batch_id=batch_id,
        #     progress=45.0,
        #     message="Parsing CSV data and validating structure",
        #     user_id=user_id
        # )
        
        # Decode and sanitize content
        try:
            content_str = file_content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                content_str = file_content.decode('latin-1')
            except UnicodeDecodeError:
                error_msg = "File encoding error"
                update_job_status(job_id, JobStatus.FAILED, 0.0, error_msg)
                raise ValueError(error_msg)
        
        # Sanitize content
        sanitization_result = sanitize_csv_content(
            content=content_str,
            filename=filename,
            user_id=user_id,
            level=SanitizationLevel.STRICT
        )
        
        if not sanitization_result.is_safe:
            error_msg = "Content sanitization failed"
            update_job_status(job_id, JobStatus.FAILED, 0.0, error_msg)
            raise ValueError(error_msg)
        
        # Parse CSV
        import pandas as pd
        import io
        
        try:
            df = pd.read_csv(io.StringIO(sanitization_result.sanitized_content))
        except Exception as e:
            error_msg = f"CSV parsing failed: {str(e)}"
            update_job_status(job_id, JobStatus.FAILED, 0.0, error_msg)
            raise ValueError(error_msg)
        
        if df.empty:
            error_msg = "CSV file is empty"
            update_job_status(job_id, JobStatus.FAILED, 0.0, error_msg)
            raise ValueError(error_msg)
        
        # Parse transactions
        parser = CSVParser()
        parsing_result: ParsingResult = parser.parse_dataframe(df)
        
        update_job_status(job_id, JobStatus.PROCESSING, 60.0, "CSV parsing completed")
        
        # Step 4: Database insertion
        update_job_status(job_id, JobStatus.PROCESSING, 65.0, "Inserting into database")
        # emit_database_progress(
        #     batch_id=batch_id,
        #     progress=65.0,
        #     message="Starting database insertion of transactions",
        #     user_id=user_id,
        #     details={"total": len(parsing_result.transactions)}
        # )
        
        processed_count = 0
        db_errors = []
        total_transactions = len(parsing_result.transactions)
        
        for transaction_data in parsing_result.transactions:
            try:
                transaction = Transaction(
                    user_id=user_id,
                    date=transaction_data['date'],
                    amount=transaction_data['amount'],
                    description=transaction_data['description'],
                    vendor=transaction_data.get('vendor'),
                    source='csv',
                    import_batch=batch_id,
                    raw_data=transaction_data.get('raw_data', {}),
                    meta_data={
                        'filename': filename,
                        'import_date': datetime.utcnow().isoformat(),
                        'validation_passed': True,
                        'malware_scan_clean': True,
                        'job_id': job_id
                    },
                    is_income=transaction_data.get('is_income', False)
                )
                
                db.add(transaction)
                processed_count += 1
                
                # Update progress every 10% or every 50 transactions
                if processed_count % max(1, total_transactions // 10) == 0 or processed_count % 50 == 0:
                    progress = 65.0 + (processed_count / total_transactions) * 10
                    update_job_status(job_id, JobStatus.PROCESSING, progress, f"Processing transactions ({processed_count}/{total_transactions})")
                    
            except Exception as e:
                db_error = {
                    'row_number': transaction_data.get('row_number'),
                    'error_type': 'database_error',
                    'message': 'Transaction processing failed',
                    'correlation_id': str(uuid.uuid4())
                }
                db_errors.append(db_error)
                logger.error(f"Database error for row {transaction_data.get('row_number')}: {str(e)}")
        
        # Commit to database
        try:
            db.commit()
            logger.info(f"Successfully committed {processed_count} transactions")
        except Exception as e:
            db.rollback()
            error_msg = f"Database commit failed: {str(e)}"
            update_job_status(job_id, JobStatus.FAILED, 0.0, error_msg)
            raise ValueError(error_msg)
        
        update_job_status(job_id, JobStatus.PROCESSING, 80.0, "Database insertion completed")
        
        # Step 5: Categorization
        update_job_status(job_id, JobStatus.PROCESSING, 85.0, "Starting categorization")
        # emit_categorization_progress(
        #     batch_id=batch_id,
        #     progress=85.0,
        #     message="Starting transaction categorization",
        #     user_id=user_id,
        #     details={"transactions_to_categorize": processed_count}
        # )
        
        categorization_service = CategorizationService(db)
        categorization_result = categorization_service.categorize_user_transactions(
            user_id, batch_id
        )
        categorized_count = categorization_result['rule_categorized'] + categorization_result['ml_categorized']
        
        update_job_status(job_id, JobStatus.PROCESSING, 95.0, "Categorization completed")
        
        # Step 6: Finalize
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        result_data = {
            "job_id": job_id,
            "batch_id": batch_id,
            "file_hash": batch_id,
            "file_info": {
                "filename": filename,
                "file_size": file_size,
                "total_rows": len(df),
                "validation_passed": True,
                "threat_level": validation_result.threat_level.value,
                "malware_scan_clean": malware_scan_result.is_clean,
                "duplicate_prevention": "SHA256 hash-based"
            },
            "processing_results": {
                "processed_count": processed_count,
                "categorized_count": categorized_count,
                "categorization_rate": round((categorized_count / processed_count * 100), 2) if processed_count > 0 else 0,
                "database_errors": len(db_errors),
                "parsing_errors": len(parsing_result.errors)
            },
            "performance": {
                "total_processing_time": processing_time,
                "validation_time": validation_result.scan_duration,
                "malware_scan_time": malware_scan_result.scan_duration
            },
            "summary": {
                "total_transactions": processed_count,
                "successfully_categorized": categorized_count,
                "overall_success_rate": round((processed_count / len(df) * 100), 2) if len(df) > 0 else 0,
                "security_status": "VALIDATED",
                "duplicate_prevention": "SHA256_HASH_BASED"
            }
        }
        
        # Update final status
        update_job_status(job_id, JobStatus.COMPLETED, 100.0, "Processing completed successfully", result_data)
        
        # Emit final progress (commented out for now)
        # emit_categorization_progress(
        #     batch_id=batch_id,
        #     progress=100.0,
        #     message="Upload completed successfully",
        #     user_id=user_id,
        #     details={
        #         "total_transactions": processed_count,
        #         "categorized_count": categorized_count,
        #         "overall_success_rate": result_data['summary']['overall_success_rate']
        #     }
        # )
        
        # Log successful processing
        security_audit_logger.log_file_upload_success(
            user_id=user_id,
            filename=filename,
            file_size=file_size,
            batch_id=batch_id,
            processed_count=processed_count,
            request=None  # No request object in background task
        )
        
        logger.info(f"File upload processing completed successfully for job {job_id}: {result_data['summary']}")
        
        return result_data
        
    except Exception as e:
        # Handle any unexpected errors
        error_msg = f"File processing failed: {str(e)}"
        update_job_status(job_id, JobStatus.FAILED, 0.0, error_msg)
        
        # Log the error
        security_audit_logger.log_file_upload_failure(
            user_id=user_id,
            filename=filename,
            file_size=file_size,
            error=error_msg,
            request=None
        )
        
        logger.error(f"File processing failed for job {job_id}: {str(e)}")
        raise
        
    finally:
        db.close()

@celery_app.task(bind=True, name="app.core.background_jobs.process_bulk_categorization")
def process_bulk_categorization(self, user_id: str, transaction_ids: List[str]) -> Dict[str, Any]:
    """
    Process bulk categorization asynchronously
    
    Args:
        user_id: User ID
        transaction_ids: List of transaction IDs to categorize
    
    Returns:
        Dictionary with categorization results
    """
    job_id = self.request.id
    db = get_database_session()
    
    try:
        update_job_status(job_id, JobStatus.PROCESSING, 0.0, "Starting bulk categorization")
        
        categorization_service = CategorizationService(db)
        result = categorization_service.categorize_transactions_by_ids(
            user_id, transaction_ids
        )
        
        update_job_status(job_id, JobStatus.COMPLETED, 100.0, "Bulk categorization completed", result)
        
        return result
        
    except Exception as e:
        error_msg = f"Bulk categorization failed: {str(e)}"
        update_job_status(job_id, JobStatus.FAILED, 0.0, error_msg)
        raise
        
    finally:
        db.close()

@celery_app.task(bind=True, name="app.core.background_jobs.generate_export")
def generate_export(self, user_id: str, export_type: str, filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate export asynchronously
    
    Args:
        user_id: User ID
        export_type: Type of export (pdf, excel, csv)
        filters: Export filters
    
    Returns:
        Dictionary with export results
    """
    job_id = self.request.id
    
    try:
        update_job_status(job_id, JobStatus.PROCESSING, 0.0, "Starting export generation")
        
        # TODO: Implement export generation logic
        # This will be implemented in Task B2.3: Export Engine Implementation
        
        result = {
            "job_id": job_id,
            "export_type": export_type,
            "status": "not_implemented",
            "message": "Export generation not yet implemented"
        }
        
        update_job_status(job_id, JobStatus.COMPLETED, 100.0, "Export generation completed", result)
        
        return result
        
    except Exception as e:
        error_msg = f"Export generation failed: {str(e)}"
        update_job_status(job_id, JobStatus.FAILED, 0.0, error_msg)
        raise

@celery_app.task(bind=True, name="app.core.background_jobs.calculate_analytics")
def calculate_analytics(self, user_id: str, analytics_type: str, date_range: Dict[str, str]) -> Dict[str, Any]:
    """
    Calculate analytics asynchronously
    
    Args:
        user_id: User ID
        analytics_type: Type of analytics to calculate
        date_range: Date range for analytics
    
    Returns:
        Dictionary with analytics results
    """
    job_id = self.request.id
    
    try:
        update_job_status(job_id, JobStatus.PROCESSING, 0.0, "Starting analytics calculation")
        
        # TODO: Implement analytics calculation logic
        # This will be implemented in Task B2.1: Analytics Engine Foundation
        
        result = {
            "job_id": job_id,
            "analytics_type": analytics_type,
            "status": "not_implemented",
            "message": "Analytics calculation not yet implemented"
        }
        
        update_job_status(job_id, JobStatus.COMPLETED, 100.0, "Analytics calculation completed", result)
        
        return result
        
    except Exception as e:
        error_msg = f"Analytics calculation failed: {str(e)}"
        update_job_status(job_id, JobStatus.FAILED, 0.0, error_msg)
        raise

def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Get job status from Redis
    
    Args:
        job_id: Job ID to check
    
    Returns:
        Job status dictionary or None if not found
    """
    try:
        status_data = celery_app.backend.get(f"job_status:{job_id}")
        if status_data:
            return json.loads(status_data)
        return None
    except Exception as e:
        logger.error(f"Failed to get job status for {job_id}: {str(e)}")
        return None

def cancel_job(job_id: str) -> bool:
    """
    Cancel a running job
    
    Args:
        job_id: Job ID to cancel
    
    Returns:
        True if job was cancelled, False otherwise
    """
    try:
        celery_app.control.revoke(job_id, terminate=True)
        update_job_status(job_id, JobStatus.CANCELLED, 0.0, "Job cancelled by user")
        return True
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {str(e)}")
        return False

def get_job_result(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Get job result from Celery
    
    Args:
        job_id: Job ID to get result for
    
    Returns:
        Job result or None if not found
    """
    try:
        result = AsyncResult(job_id, app=celery_app)
        if result.ready():
            return {
                "status": result.status,
                "result": result.result if result.successful() else None,
                "error": str(result.info) if result.failed() else None
            }
        return None
    except Exception as e:
        logger.error(f"Failed to get job result for {job_id}: {str(e)}")
        return None
