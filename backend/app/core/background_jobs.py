"""
Background Job System for FinGood Financial Platform

This module implements a production-ready async job queue system using RQ (Redis Queue)
for processing file uploads and other background tasks. The system maintains all existing
security features while providing scalable async processing.

Key Features:
- Redis-based job queue with RQ
- Comprehensive job status tracking and progress updates
- Full security pipeline preservation (validation, malware scanning, etc.)
- Error handling and retry logic
- WebSocket progress notifications
- Job monitoring and management
- Production-ready logging and monitoring

Architecture:
- Job Queue: RQ with Redis backend
- Job Status: Redis-based with structured data
- Progress Tracking: Real-time updates via WebSocket
- Error Handling: Comprehensive retry and failure management
- Security: Full preservation of existing validation pipeline
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

import redis
from rq import Queue, Worker, get_current_job
from rq.job import Job, JobStatus
from rq.exceptions import InvalidJobOperation
import pandas as pd
import io

from app.core.config import settings
from app.core.database import get_db
from app.core.audit_logger import security_audit_logger
from app.core.error_sanitizer import error_sanitizer, create_secure_error_response
from app.schemas.error import ErrorCategory, ErrorSeverity
from app.core.exceptions import ValidationException, SystemException
from app.services.categorization import CategorizationService
from app.services.csv_parser import CSVParser, ParsingResult
from app.services.file_validator import FileValidator, ValidationResult, ThreatLevel
from app.services.malware_scanner import scan_file_for_malware
from app.services.upload_monitor import check_upload_allowed, record_upload
from app.services.content_sanitizer import sanitize_csv_content, SanitizationLevel
from app.services.simple_sandbox_analyzer import analyze_file_in_sandbox, AnalysisType
from app.models.user import User
from app.models.transaction import Transaction
from app.core.websocket_manager import (
    emit_validation_progress,
    emit_scanning_progress,
    emit_parsing_progress,
    emit_database_progress,
    emit_categorization_progress
)

logger = logging.getLogger(__name__)

# Job Status and Types
class JobType(str, Enum):
    """Supported background job types"""
    CSV_UPLOAD = "csv_upload"
    BULK_CATEGORIZATION = "bulk_categorization"
    DATA_EXPORT = "data_export"
    BATCH_DELETE = "batch_delete"

class JobState(str, Enum):
    """Job execution states"""
    QUEUED = "queued"
    STARTED = "started"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class JobPriority(str, Enum):
    """Job priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class JobProgress:
    """Structured job progress tracking"""
    job_id: str
    job_type: JobType
    state: JobState
    progress_percentage: float
    current_step: str
    message: str
    details: Dict[str, Any]
    user_id: str
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_info: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class JobResult:
    """Structured job result data"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    correlation_id: Optional[str] = None
    processing_time: Optional[float] = None
    statistics: Optional[Dict[str, Any]] = None

class BackgroundJobManager:
    """
    Production-ready background job manager for FinGood platform.
    
    Handles job queuing, status tracking, progress updates, and comprehensive
    error handling while maintaining all existing security features.
    """
    
    def __init__(self):
        """Initialize the job manager with Redis connection and RQ queues"""
        try:
            # Initialize Redis connection
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=30,
                socket_connect_timeout=30,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )
            
            # Test Redis connection
            self.redis_client.ping()
            logger.info("Successfully connected to Redis for background jobs")
            
            # Initialize RQ queues with different priorities
            self.queues = {
                JobPriority.CRITICAL: Queue('critical', connection=self.redis_client),
                JobPriority.HIGH: Queue('high', connection=self.redis_client),
                JobPriority.NORMAL: Queue('default', connection=self.redis_client),
                JobPriority.LOW: Queue('low', connection=self.redis_client)
            }
            
            # Job status tracking keys
            self.job_status_key_prefix = "fingood:job:status"
            self.job_progress_key_prefix = "fingood:job:progress"
            self.user_jobs_key_prefix = "fingood:user:jobs"
            
            logger.info(f"Background job manager initialized with {len(self.queues)} priority queues")
            
        except redis.RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise SystemException(
                message="Failed to initialize background job system",
                code="REDIS_CONNECTION_ERROR"
            )
    
    def _get_job_status_key(self, job_id: str) -> str:
        """Get Redis key for job status"""
        return f"{self.job_status_key_prefix}:{job_id}"
    
    def _get_job_progress_key(self, job_id: str) -> str:
        """Get Redis key for job progress"""
        return f"{self.job_progress_key_prefix}:{job_id}"
    
    def _get_user_jobs_key(self, user_id: str) -> str:
        """Get Redis key for user's jobs"""
        return f"{self.user_jobs_key_prefix}:{user_id}"
    
    async def queue_csv_upload_job(
        self,
        user_id: str,
        file_content: bytes,
        filename: str,
        file_size: int,
        batch_id: Optional[str] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        priority: JobPriority = JobPriority.NORMAL
    ) -> str:
        """
        Queue a CSV upload job for background processing.
        
        Args:
            user_id: User ID for the upload
            file_content: Raw file content bytes
            filename: Original filename
            file_size: File size in bytes
            batch_id: Optional batch ID (will generate if not provided)
            client_ip: Client IP address for audit logging
            user_agent: Client user agent for audit logging
            priority: Job priority level
            
        Returns:
            str: Job ID for tracking
            
        Raises:
            ValidationException: If job parameters are invalid
            SystemException: If job queueing fails
        """
        try:
            # Generate job ID and batch ID if needed
            job_id = str(uuid.uuid4())
            if not batch_id:
                import hashlib
                file_hash = hashlib.sha256(file_content).hexdigest()
                batch_id = file_hash
            
            # Prepare job data
            job_data = {
                'job_id': job_id,
                'user_id': user_id,
                'file_content': file_content.hex(),  # Convert to hex for JSON serialization
                'filename': filename,
                'file_size': file_size,
                'batch_id': batch_id,
                'client_ip': client_ip,
                'user_agent': user_agent,
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Initialize job progress
            progress = JobProgress(
                job_id=job_id,
                job_type=JobType.CSV_UPLOAD,
                state=JobState.QUEUED,
                progress_percentage=0.0,
                current_step="queued",
                message="Upload job queued for processing",
                details={'filename': filename, 'file_size': file_size, 'batch_id': batch_id},
                user_id=user_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Store initial progress
            await self._store_job_progress(progress)
            
            # Queue the job
            queue = self.queues[priority]
            rq_job = queue.enqueue(
                process_csv_upload_job,
                job_data,
                job_id=job_id,
                job_timeout='30m',  # 30 minute timeout for large files
                retry_count=3,
                meta={'user_id': user_id, 'filename': filename, 'priority': priority.value}
            )
            
            # Track job for user
            user_jobs_key = self._get_user_jobs_key(user_id)
            self.redis_client.sadd(user_jobs_key, job_id)
            self.redis_client.expire(user_jobs_key, 86400)  # 24 hour expiry
            
            logger.info(f"Queued CSV upload job {job_id} for user {user_id} with priority {priority.value}")
            
            # Log audit event
            security_audit_logger.log_file_upload_attempt(
                user_id=user_id,
                filename=filename,
                file_size=file_size,
                timestamp=datetime.utcnow(),
                request=None  # Will be available in the background job
            )
            
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to queue CSV upload job: {e}")
            raise SystemException(
                message="Failed to queue upload job",
                code="JOB_QUEUE_ERROR"
            )
    
    async def _store_job_progress(self, progress: JobProgress) -> None:
        """Store job progress in Redis"""
        try:
            progress_key = self._get_job_progress_key(progress.job_id)
            progress_data = asdict(progress)
            
            # Convert datetime objects to ISO format for JSON serialization
            for key, value in progress_data.items():
                if isinstance(value, datetime):
                    progress_data[key] = value.isoformat() if value else None
            
            # Store with 24 hour expiry
            self.redis_client.setex(
                progress_key,
                86400,  # 24 hours
                json.dumps(progress_data, default=str)
            )
            
            # Emit WebSocket update if user is connected
            if progress.state == JobState.PROCESSING:
                await self._emit_websocket_progress(progress)
                
        except Exception as e:
            logger.error(f"Failed to store job progress for {progress.job_id}: {e}")
    
    async def _emit_websocket_progress(self, progress: JobProgress) -> None:
        """Emit progress update via WebSocket"""
        try:
            # Map job progress to appropriate WebSocket event based on current step
            step = progress.current_step.lower()
            
            if 'validation' in step:
                await emit_validation_progress(
                    batch_id=progress.details.get('batch_id', progress.job_id),
                    progress=progress.progress_percentage,
                    message=progress.message,
                    user_id=progress.user_id,
                    details=progress.details
                )
            elif 'scanning' in step or 'malware' in step:
                await emit_scanning_progress(
                    batch_id=progress.details.get('batch_id', progress.job_id),
                    progress=progress.progress_percentage,
                    message=progress.message,
                    user_id=progress.user_id,
                    details=progress.details
                )
            elif 'parsing' in step:
                await emit_parsing_progress(
                    batch_id=progress.details.get('batch_id', progress.job_id),
                    progress=progress.progress_percentage,
                    message=progress.message,
                    user_id=progress.user_id,
                    details=progress.details
                )
            elif 'database' in step:
                await emit_database_progress(
                    batch_id=progress.details.get('batch_id', progress.job_id),
                    progress=progress.progress_percentage,
                    message=progress.message,
                    user_id=progress.user_id,
                    details=progress.details
                )
            elif 'categorization' in step:
                await emit_categorization_progress(
                    batch_id=progress.details.get('batch_id', progress.job_id),
                    progress=progress.progress_percentage,
                    message=progress.message,
                    user_id=progress.user_id,
                    details=progress.details
                )
                
        except Exception as e:
            logger.error(f"Failed to emit WebSocket progress for job {progress.job_id}: {e}")
    
    async def get_job_status(self, job_id: str) -> Optional[JobProgress]:
        """Get current job status and progress"""
        try:
            progress_key = self._get_job_progress_key(job_id)
            progress_data = self.redis_client.get(progress_key)
            
            if not progress_data:
                return None
            
            data = json.loads(progress_data)
            
            # Convert ISO datetime strings back to datetime objects
            for key in ['created_at', 'updated_at', 'started_at', 'completed_at']:
                if data.get(key):
                    data[key] = datetime.fromisoformat(data[key])
            
            return JobProgress(**data)
            
        except Exception as e:
            logger.error(f"Failed to get job status for {job_id}: {e}")
            return None
    
    async def get_user_jobs(self, user_id: str, limit: int = 50) -> List[JobProgress]:
        """Get all jobs for a user"""
        try:
            user_jobs_key = self._get_user_jobs_key(user_id)
            job_ids = self.redis_client.smembers(user_jobs_key)
            
            jobs = []
            for job_id in job_ids:
                if len(jobs) >= limit:
                    break
                    
                job_status = await self.get_job_status(job_id)
                if job_status:
                    jobs.append(job_status)
            
            # Sort by created_at descending
            jobs.sort(key=lambda x: x.created_at, reverse=True)
            return jobs
            
        except Exception as e:
            logger.error(f"Failed to get user jobs for {user_id}: {e}")
            return []
    
    async def cancel_job(self, job_id: str, user_id: str) -> bool:
        """Cancel a queued or running job"""
        try:
            # Check if user owns the job
            job_status = await self.get_job_status(job_id)
            if not job_status or job_status.user_id != user_id:
                return False
            
            # Try to cancel the RQ job
            try:
                job = Job.fetch(job_id, connection=self.redis_client)
                job.cancel()
            except Exception:
                pass  # Job might not exist in RQ anymore
            
            # Update job status
            job_status.state = JobState.CANCELLED
            job_status.updated_at = datetime.utcnow()
            job_status.message = "Job cancelled by user"
            
            await self._store_job_progress(job_status)
            
            logger.info(f"Cancelled job {job_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {e}")
            return False
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get comprehensive queue statistics"""
        try:
            stats = {}
            
            for priority, queue in self.queues.items():
                stats[priority.value] = {
                    'name': queue.name,
                    'length': len(queue),
                    'scheduled_count': queue.scheduled_job_registry.count,
                    'started_count': queue.started_job_registry.count,
                    'finished_count': queue.finished_job_registry.count,
                    'failed_count': queue.failed_job_registry.count,
                    'deferred_count': queue.deferred_job_registry.count
                }
            
            return {
                'queues': stats,
                'total_queued': sum(len(q) for q in self.queues.values()),
                'redis_info': {
                    'used_memory': self.redis_client.info()['used_memory_human'],
                    'connected_clients': self.redis_client.info()['connected_clients']
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {'error': str(e)}

# Global job manager instance
job_manager = BackgroundJobManager()

# Background job worker functions
def process_csv_upload_job(job_data: Dict[str, Any]) -> JobResult:
    """
    Background worker function for processing CSV uploads.
    
    This function maintains the complete security pipeline from the original
    synchronous upload endpoint while running in a background worker.
    
    Args:
        job_data: Job data containing file content and metadata
        
    Returns:
        JobResult: Structured result with success/failure information
    """
    start_time = datetime.utcnow()
    job_id = job_data['job_id']
    user_id = job_data['user_id']
    filename = job_data['filename']
    
    logger.info(f"Starting CSV upload job {job_id} for user {user_id}")
    
    try:
        # Get current RQ job for progress tracking
        current_job = get_current_job()
        
        # Initialize progress tracking
        async def update_progress(
            state: JobState,
            percentage: float,
            step: str,
            message: str,
            details: Optional[Dict[str, Any]] = None
        ):
            progress = JobProgress(
                job_id=job_id,
                job_type=JobType.CSV_UPLOAD,
                state=state,
                progress_percentage=percentage,
                current_step=step,
                message=message,
                details=details or {},
                user_id=user_id,
                created_at=datetime.fromisoformat(job_data['created_at']),
                updated_at=datetime.utcnow(),
                started_at=datetime.utcnow() if state == JobState.STARTED else None
            )
            
            # Store progress and emit WebSocket update
            await job_manager._store_job_progress(progress)
        
        # Start processing
        asyncio.run(update_progress(
            JobState.STARTED,
            5.0,
            "started",
            "Starting file upload processing",
            {'filename': filename, 'file_size': job_data['file_size']}
        ))
        
        # Convert hex content back to bytes
        file_content = bytes.fromhex(job_data['file_content'])
        file_size = job_data['file_size']
        batch_id = job_data['batch_id']
        
        # Get database session
        db = next(get_db())
        
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValidationException("User not found")
            
            # Step 1: Check upload permissions and rate limits
            asyncio.run(update_progress(
                JobState.PROCESSING,
                10.0,
                "upload_validation",
                "Checking upload permissions and rate limits"
            ))
            
            upload_allowed, deny_reason = asyncio.run(check_upload_allowed(
                user_id=user_id,
                filename=filename,
                file_size=file_size,
                file_content=file_content,
                ip_address=job_data.get('client_ip'),
                user_agent=job_data.get('user_agent')
            ))
            
            if not upload_allowed:
                asyncio.run(record_upload(
                    user_id=user_id,
                    filename=filename,
                    file_size=file_size,
                    file_content=file_content,
                    success=False,
                    ip_address=job_data.get('client_ip'),
                    user_agent=job_data.get('user_agent'),
                    error=deny_reason
                ))
                
                raise ValidationException(f"Upload denied: {deny_reason}")
            
            # Step 2: Comprehensive file validation
            asyncio.run(update_progress(
                JobState.PROCESSING,
                20.0,
                "file_validation",
                "Validating file format and structure"
            ))
            
            file_validator = FileValidator()
            validation_result = asyncio.run(file_validator.validate_file(
                file_content=file_content,
                filename=filename,
                user_id=user_id
            ))
            
            if validation_result.validation_result == ValidationResult.REJECTED:
                raise ValidationException(f"File validation failed: {validation_result.errors}")
            
            # Step 3: Malware scanning
            asyncio.run(update_progress(
                JobState.PROCESSING,
                30.0,
                "malware_scanning",
                "Scanning file for malware and threats"
            ))
            
            malware_scan_result = asyncio.run(scan_file_for_malware(
                file_content=file_content,
                filename=filename,
                user_id=user_id
            ))
            
            if not malware_scan_result.is_clean:
                raise ValidationException(f"Malware detected: {malware_scan_result.threats_detected}")
            
            # Step 4: Sandbox analysis for suspicious files
            if validation_result.threat_level in [ThreatLevel.MEDIUM, ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                asyncio.run(update_progress(
                    JobState.PROCESSING,
                    35.0,
                    "sandbox_analysis",
                    "Performing behavioral analysis"
                ))
                
                sandbox_result = asyncio.run(analyze_file_in_sandbox(
                    file_content=file_content,
                    filename=filename,
                    user_id=user_id,
                    analysis_type=AnalysisType.BEHAVIORAL
                ))
                
                if sandbox_result.get("threat_detected", False):
                    raise ValidationException(f"Sandbox analysis failed: {sandbox_result}")
            
            # Step 5: Content sanitization and CSV parsing
            asyncio.run(update_progress(
                JobState.PROCESSING,
                40.0,
                "content_processing",
                "Processing and sanitizing file content"
            ))
            
            # Decode content
            try:
                content_str = file_content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    content_str = file_content.decode('latin-1')
                    logger.warning(f"File {filename} uses non-UTF-8 encoding")
                except UnicodeDecodeError:
                    raise ValidationException("File encoding error. Please ensure the file is UTF-8 encoded.")
            
            # Sanitize content
            sanitization_result = asyncio.run(sanitize_csv_content(
                content=content_str,
                filename=filename,
                user_id=user_id,
                level=SanitizationLevel.STRICT
            ))
            
            if not sanitization_result.is_safe:
                raise ValidationException(f"Content sanitization failed: {sanitization_result.security_issues}")
            
            content_str = sanitization_result.sanitized_content
            
            # Parse CSV
            asyncio.run(update_progress(
                JobState.PROCESSING,
                50.0,
                "csv_parsing",
                "Parsing CSV data and validating structure"
            ))
            
            try:
                df = pd.read_csv(io.StringIO(content_str))
            except Exception as e:
                raise ValidationException(f"CSV parsing failed: {str(e)}")
            
            if df.empty:
                raise ValidationException("CSV file is empty")
            
            # Parse transactions
            parser = CSVParser()
            parsing_result: ParsingResult = parser.parse_dataframe(df)
            
            asyncio.run(update_progress(
                JobState.PROCESSING,
                60.0,
                "transaction_parsing",
                f"Parsed {len(parsing_result.transactions)} transactions",
                {
                    'successful_parsing': len(parsing_result.transactions),
                    'failed_parsing': len(parsing_result.errors),
                    'warnings': len(parsing_result.warnings)
                }
            ))
            
            # Step 6: Database insertion
            asyncio.run(update_progress(
                JobState.PROCESSING,
                70.0,
                "database_insertion",
                "Saving transactions to database"
            ))
            
            processed_count = 0
            db_errors = []
            total_transactions = len(parsing_result.transactions)
            
            for transaction_data in parsing_result.transactions:
                try:
                    transaction = Transaction(
                        user_id=user.id,
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
                            'processed_via_background_job': True,
                            'job_id': job_id
                        },
                        is_income=transaction_data.get('is_income', False)
                    )
                    
                    db.add(transaction)
                    processed_count += 1
                    
                    # Update progress every 10% or every 50 transactions
                    if processed_count % max(1, total_transactions // 10) == 0 or processed_count % 50 == 0:
                        progress_percentage = 70.0 + (processed_count / total_transactions) * 10  # 70% to 80%
                        asyncio.run(update_progress(
                            JobState.PROCESSING,
                            progress_percentage,
                            "database_insertion",
                            f"Processing transactions ({processed_count}/{total_transactions})",
                            {'processed': processed_count, 'total': total_transactions, 'errors': len(db_errors)}
                        ))
                
                except Exception as e:
                    sanitized_message = error_sanitizer.sanitize_error_message(str(e))
                    db_error = {
                        'row_number': transaction_data.get('row_number'),
                        'error_type': 'database_error',
                        'message': 'Transaction processing failed',
                        'correlation_id': str(uuid.uuid4())
                    }
                    db_errors.append(db_error)
                    logger.error(f"Database error for row {transaction_data.get('row_number')}: {db_error['correlation_id']}")
            
            # Commit to database
            asyncio.run(update_progress(
                JobState.PROCESSING,
                80.0,
                "database_commit",
                "Committing transactions to database"
            ))
            
            db.commit()
            logger.info(f"Successfully committed {processed_count} transactions")
            
            # Step 7: Apply categorization
            asyncio.run(update_progress(
                JobState.PROCESSING,
                85.0,
                "categorization",
                "Starting transaction categorization"
            ))
            
            categorization_service = CategorizationService(db)
            categorization_result = asyncio.run(categorization_service.categorize_user_transactions(
                user.id, batch_id
            ))
            categorized_count = categorization_result['rule_categorized'] + categorization_result['ml_categorized']
            
            # Step 8: Complete processing
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            asyncio.run(update_progress(
                JobState.COMPLETED,
                100.0,
                "completed",
                "Upload completed successfully",
                {
                    'total_transactions': processed_count,
                    'categorized_count': categorized_count,
                    'processing_time': processing_time,
                    'overall_success_rate': round((processed_count / len(df) * 100), 2) if len(df) > 0 else 0
                }
            ))
            
            # Log successful upload
            security_audit_logger.log_file_upload_success(
                user_id=user_id,
                filename=filename,
                file_size=file_size,
                batch_id=batch_id,
                processed_count=processed_count,
                request=None
            )
            
            # Record successful upload
            asyncio.run(record_upload(
                user_id=user_id,
                filename=filename,
                file_size=file_size,
                file_content=file_content,
                success=True,
                ip_address=job_data.get('client_ip'),
                user_agent=job_data.get('user_agent')
            ))
            
            logger.info(f"Completed CSV upload job {job_id} successfully: {processed_count} transactions processed")
            
            return JobResult(
                success=True,
                data={
                    'batch_id': batch_id,
                    'file_hash': batch_id,
                    'processed_count': processed_count,
                    'categorized_count': categorized_count,
                    'categorization_rate': round((categorized_count / processed_count * 100), 2) if processed_count > 0 else 0,
                    'parsing_results': {
                        'successful_parsing': len(parsing_result.transactions),
                        'failed_parsing': len(parsing_result.errors),
                        'success_rate': parsing_result.statistics['success_rate'],
                        'warning_count': len(parsing_result.warnings)
                    },
                    'security_validation': {
                        'validation_passed': True,
                        'threat_level': validation_result.threat_level.value,
                        'malware_scan_clean': malware_scan_result.is_clean,
                        'content_safe': sanitization_result.is_safe
                    }
                },
                processing_time=processing_time,
                statistics=parsing_result.statistics
            )
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"CSV upload job {job_id} failed: {e}")
        
        # Update job status to failed
        try:
            asyncio.run(update_progress(
                JobState.FAILED,
                0.0,
                "failed",
                f"Upload failed: {str(e)}",
                {'error': str(e)}
            ))
        except:
            pass  # Don't let progress update failure mask the original error
        
        # Log failure
        security_audit_logger.log_file_upload_failure(
            user_id=user_id,
            filename=filename,
            file_size=job_data.get('file_size', 0),
            error=f"Background job failed: {str(e)}",
            request=None
        )
        
        return JobResult(
            success=False,
            error_message=str(e),
            error_code="JOB_PROCESSING_ERROR",
            correlation_id=job_id,
            processing_time=(datetime.utcnow() - start_time).total_seconds()
        )

def start_worker(queue_names: List[str] = None) -> None:
    """
    Start RQ worker for processing background jobs.
    
    Args:
        queue_names: List of queue names to process (default: all queues)
    """
    try:
        redis_conn = redis.from_url(settings.REDIS_URL)
        
        if queue_names is None:
            queue_names = ['critical', 'high', 'default', 'low']
        
        queues = [Queue(name, connection=redis_conn) for name in queue_names]
        
        logger.info(f"Starting worker for queues: {queue_names}")
        
        worker = Worker(queues, connection=redis_conn)
        worker.work(with_scheduler=True)
        
    except Exception as e:
        logger.error(f"Failed to start worker: {e}")
        raise

if __name__ == "__main__":
    # CLI entry point for starting workers
    import sys
    
    if len(sys.argv) > 1:
        queue_names = sys.argv[1].split(',')
    else:
        queue_names = None
    
    start_worker(queue_names)