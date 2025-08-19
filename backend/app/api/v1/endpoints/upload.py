from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import pandas as pd
import io
import uuid
import hashlib
from datetime import datetime
import logging

from app.core.database import get_db
from app.core.config import settings
from app.core.audit_logger import security_audit_logger
from app.core.error_sanitizer import error_sanitizer, create_secure_error_response
from app.schemas.error import ErrorCategory, ErrorSeverity
from app.core.exceptions import ValidationException, SystemException
from app.models.user import User
from app.models.transaction import Transaction
from app.core.cookie_auth import get_current_user_from_cookie
from app.services.categorization import CategorizationService
from app.services.csv_parser import CSVParser, ParsingResult
from app.services.file_validator import FileValidator, ValidationResult, ThreatLevel
from app.services.malware_scanner import scan_file_for_malware
from app.services.upload_monitor import check_upload_allowed, record_upload
from app.services.content_sanitizer import sanitize_csv_content, SanitizationLevel
from app.services.simple_sandbox_analyzer import analyze_file_in_sandbox, AnalysisType
from app.core.websocket_manager import (
    emit_validation_progress,
    emit_scanning_progress,
    emit_parsing_progress,
    emit_database_progress,
    emit_categorization_progress
)
from app.core.background_jobs import job_manager, JobPriority, JobState

router = APIRouter()
logger = logging.getLogger(__name__)

# Constants for secure hash handling
HASH_DISPLAY_LENGTH = 16

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

@router.post("/csv")
async def upload_csv(
    request: Request,
    file: UploadFile = File(...),
    batch_id: Optional[str] = None,
    force_sync: bool = False,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Upload and process CSV file with intelligent async/sync routing.
    
    This endpoint automatically routes files based on size:
    - Small files (< 5MB): Processed synchronously for immediate results
    - Large files (>= 5MB): Automatically routed to async processing unless force_sync=True
    
    Features SHA256 hash-based duplicate prevention:
    - Each file's content is hashed using SHA256
    - Hash serves as batch_id for tracking and deduplication
    - Rejects duplicates with HTTP 409 and clear error message
    - Maintains existing DELETE /api/v1/transactions/import-batch/{hash} functionality
    
    Parameters:
    - force_sync: If True, forces synchronous processing even for large files
    
    Security measures include file validation, malware scanning, content sanitization,
    and comprehensive audit logging for financial compliance.
    """
    
    file_validator = FileValidator()
    start_time = datetime.utcnow()
    
    # Basic file validation
    if not file.filename:
        security_audit_logger.log_file_upload_failure(
            user_id=str(current_user.id),
            filename="<no filename>",
            file_size=0,
            error="No filename provided",
            request=request
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )
    
    try:
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Log upload attempt
        security_audit_logger.log_file_upload_attempt(
            user_id=str(current_user.id),
            filename=file.filename,
            file_size=file_size,
            timestamp=start_time,
            request=request
        )
        
        logger.info(f"Processing file upload: {file.filename}, size: {file_size} bytes, user: {current_user.id}")
        
        # Intelligent routing: Large files (>=5MB) go to async processing unless forced sync
        ASYNC_THRESHOLD = 5 * 1024 * 1024  # 5MB
        should_process_async = file_size >= ASYNC_THRESHOLD and not force_sync
        
        if should_process_async:
            logger.info(f"Routing large file ({file_size} bytes) to async processing for user {current_user.id}")
            
            # Route to async processing - delegate to the async endpoint logic
            try:
                # Validate priority (default to normal for auto-routed files)
                job_priority = JobPriority.NORMAL
                
                # Basic file type validation (early check)
                if not file.filename.lower().endswith('.csv'):
                    security_audit_logger.log_file_upload_failure(
                        user_id=str(current_user.id),
                        filename=file.filename,
                        file_size=file_size,
                        error="Invalid file extension",
                        request=request
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Only CSV files are supported"
                    )
                
                # Basic size validation (should already pass but double-check)
                max_size = settings.MAX_FILE_SIZE
                if file_size > max_size:
                    security_audit_logger.log_file_size_violation(
                        user_id=str(current_user.id),
                        filename=file.filename,
                        file_size=file_size,
                        max_allowed=max_size,
                        request=request
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"File too large. Maximum size: {max_size / (1024*1024):.1f} MB"
                    )
                
                # Check user job limits
                user_jobs = await job_manager.get_user_jobs(str(current_user.id), limit=50)
                active_jobs = [job for job in user_jobs if job.state in ['queued', 'started', 'processing']]
                
                if len(active_jobs) >= settings.MAX_CONCURRENT_JOBS_PER_USER:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Too many active jobs. Maximum concurrent jobs: {settings.MAX_CONCURRENT_JOBS_PER_USER}"
                    )
                
                # Generate SHA256 file hash for batch_id (duplicate prevention)
                if not batch_id:
                    file_hash = calculate_file_hash_streaming(content)
                    batch_id = file_hash
                    
                    logger.info(f"Generated SHA256 hash for {file.filename}: {truncate_hash_for_display(file_hash)} (size: {file_size} bytes)")
                    
                    # Early duplicate detection
                    existing_upload = db.query(Transaction).filter(
                        Transaction.user_id == current_user.id,
                        Transaction.import_batch == file_hash
                    ).first()
                    
                    if existing_upload:
                        security_audit_logger.log_file_upload_failure(
                            user_id=str(current_user.id),
                            filename=file.filename,
                            file_size=file_size,
                            error=f"Duplicate file upload detected - hash: {truncate_hash_for_display(file_hash)}",
                            request=request
                        )
                        
                        logger.warning(f"Duplicate file upload rejected for user {current_user.id}: hash {truncate_hash_for_display(file_hash)}")
                        
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail={
                                "message": "This file has already been uploaded",
                                "duplicate_batch_id": file_hash,
                                "error_code": "DUPLICATE_FILE_UPLOAD",
                                "suggested_action": f"Use DELETE /api/v1/transactions/import-batch/{file_hash} to remove the previous upload before re-uploading"
                            }
                        )
                
                # Get client info for monitoring
                client_ip = request.client.host if request.client else None
                user_agent = request.headers.get("User-Agent")
                
                # Queue the background job
                job_id = await job_manager.queue_csv_upload_job(
                    user_id=str(current_user.id),
                    file_content=content,
                    filename=file.filename,
                    file_size=file_size,
                    batch_id=batch_id,
                    client_ip=client_ip,
                    user_agent=user_agent,
                    priority=job_priority
                )
                
                # Estimate processing time based on file size
                estimated_time_minutes = max(1, file_size / (1024 * 1024))  # Rough estimate: 1 minute per MB
                if file_size > 5 * 1024 * 1024:  # Files > 5MB get longer estimates
                    estimated_time_minutes *= 1.5
                
                processing_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Return async response with routing information
                return {
                    "message": "Large file automatically routed to background processing",
                    "processing_mode": "async",
                    "routing_reason": f"File size ({file_size:,} bytes) exceeds sync threshold ({ASYNC_THRESHOLD:,} bytes)",
                    "job_id": job_id,
                    "batch_id": batch_id,
                    "file_hash": batch_id,
                    "status": "queued",
                    "priority": job_priority.value,
                    "file_info": {
                        "filename": file.filename,
                        "file_size": file_size,
                        "estimated_processing_time_minutes": round(estimated_time_minutes, 1)
                    },
                    "tracking": {
                        "status_endpoint": f"/api/v1/upload/jobs/{job_id}/status",
                        "progress_endpoint": f"/api/v1/upload/jobs/{job_id}/progress",
                        "cancel_endpoint": f"/api/v1/upload/jobs/{job_id}/cancel",
                        "websocket_updates": "Connect to WebSocket for real-time progress"
                    },
                    "queue_info": {
                        "position_estimate": "Processing will begin shortly",
                        "active_jobs": len(active_jobs),
                        "max_concurrent": settings.MAX_CONCURRENT_JOBS_PER_USER
                    },
                    "performance": {
                        "queue_time": processing_time,
                        "estimated_total_time_minutes": round(estimated_time_minutes, 1)
                    },
                    "instructions": {
                        "monitoring": "Use the provided tracking endpoints to monitor progress",
                        "websocket": "Connect to WebSocket for real-time updates",
                        "completion": "You'll receive a completion notification via WebSocket",
                        "force_sync": "Add '?force_sync=true' to force synchronous processing for large files"
                    }
                }
                
            except HTTPException:
                # Re-raise HTTP exceptions
                raise
            except Exception as e:
                # Create sanitized error response for unexpected errors
                error_detail = create_secure_error_response(
                    exception=e,
                    error_code="ASYNC_ROUTING_ERROR",
                    error_category=ErrorCategory.SYSTEM_ERROR,
                    correlation_id=str(uuid.uuid4()),
                    user_message="Failed to route large file to background processing. Please try again.",
                    suggested_action="If the problem persists, try adding '?force_sync=true' to process the file synchronously."
                )
                
                security_audit_logger.log_file_upload_failure(
                    user_id=str(current_user.id),
                    filename=file.filename,
                    file_size=file_size,
                    error=f"Async routing error: {error_detail.correlation_id}",
                    request=request
                )
                
                logger.error(f"Failed to route large file to async processing: {error_detail.correlation_id}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_detail.user_message
                )
        
        # Continue with synchronous processing for small files or forced sync
        if should_process_async:
            logger.info(f"Large file forced to sync processing by user request: {file.filename}")
        else:
            logger.info(f"Processing small file ({file_size} bytes) synchronously: {file.filename}")
        
        # Get client info for monitoring
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("User-Agent")
        
        # Step 1: Check upload permissions and rate limits
        upload_allowed, deny_reason = await check_upload_allowed(
            user_id=str(current_user.id),
            filename=file.filename,
            file_size=file_size,
            file_content=content,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        if not upload_allowed:
            await record_upload(
                user_id=str(current_user.id),
                filename=file.filename,
                file_size=file_size,
                file_content=content,
                success=False,
                ip_address=client_ip,
                user_agent=user_agent,
                error=deny_reason
            )
            
            security_audit_logger.log_file_upload_failure(
                user_id=str(current_user.id),
                filename=file.filename,
                file_size=file_size,
                error=f"Upload denied: {deny_reason}",
                request=request
            )
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=deny_reason
            )
        
        # Generate SHA256 file hash for batch_id (replaces UUID for duplicate prevention)
        if not batch_id:
            # Compute hash early for security and performance with streaming for memory efficiency
            file_hash = calculate_file_hash_streaming(content)
            batch_id = file_hash
            
            logger.info(f"Generated SHA256 hash for {file.filename}: {truncate_hash_for_display(file_hash)} (size: {file_size} bytes)")
            
            # Early duplicate detection - check before any processing for optimal performance
            existing_upload = db.query(Transaction).filter(
                Transaction.user_id == current_user.id,
                Transaction.import_batch == file_hash
            ).first()
            
            if existing_upload:
                # Log security event for duplicate attempt
                security_audit_logger.log_file_upload_failure(
                    user_id=str(current_user.id),
                    filename=file.filename,
                    file_size=file_size,
                    error=f"Duplicate file upload detected - hash: {truncate_hash_for_display(file_hash)}",
                    request=request
                )
                
                logger.warning(f"Duplicate file upload rejected for user {current_user.id}: hash {truncate_hash_for_display(file_hash)}")
                
                # Secure error response with actionable information
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "message": "This file has already been uploaded",
                        "duplicate_batch_id": file_hash,
                        "error_code": "DUPLICATE_FILE_UPLOAD",
                        "suggested_action": f"Use DELETE /api/v1/transactions/import-batch/{file_hash} to remove the previous upload before re-uploading"
                    }
                )
        
        # Emit initial progress
        await emit_validation_progress(
            batch_id=batch_id,
            progress=5.0,
            message="Starting file upload process",
            user_id=str(current_user.id),
            details={"filename": file.filename, "size": file_size}
        )
        
        # Step 2: Comprehensive file validation
        await emit_validation_progress(
            batch_id=batch_id,
            progress=10.0,
            message="Validating file format and structure",
            user_id=str(current_user.id)
        )
        
        validation_result = await file_validator.validate_file(
            file_content=content,
            filename=file.filename,
            user_id=str(current_user.id)
        )
        
        await emit_validation_progress(
            batch_id=batch_id,
            progress=20.0,
            message="File validation completed",
            user_id=str(current_user.id),
            details={"threat_level": validation_result.threat_level.value}
        )
        
        # Handle validation results
        if validation_result.validation_result == ValidationResult.REJECTED:
            security_audit_logger.log_file_rejected(
                user_id=str(current_user.id),
                filename=file.filename,
                reason="Failed security validation",
                threat_indicators=validation_result.errors,
                request=request
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "File failed security validation",
                    "errors": validation_result.errors,
                    "threat_level": validation_result.threat_level.value
                }
            )
        
        elif validation_result.validation_result == ValidationResult.QUARANTINED:
            security_audit_logger.log_file_quarantined(
                user_id=str(current_user.id),
                filename=file.filename,
                quarantine_id=validation_result.quarantine_id,
                reason="Suspicious content detected",
                request=request
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "File quarantined due to suspicious content",
                    "quarantine_id": validation_result.quarantine_id,
                    "warnings": validation_result.warnings,
                    "threat_level": validation_result.threat_level.value
                }
            )
        
        # Step 2: Malware scanning
        await emit_scanning_progress(
            batch_id=batch_id,
            progress=25.0,
            message="Scanning file for malware and threats",
            user_id=str(current_user.id)
        )
        
        malware_scan_result = await scan_file_for_malware(
            file_content=content,
            filename=file.filename,
            user_id=str(current_user.id)
        )
        

        
        await emit_scanning_progress(
            batch_id=batch_id,
            progress=40.0,
            message="Malware scan completed - file is clean",
            user_id=str(current_user.id),
            details={
                "threats_detected": len(malware_scan_result.threats_detected),
                "scan_engines": malware_scan_result.total_engines
            }
        )
        
        if not malware_scan_result.is_clean:
            security_audit_logger.log_malware_detected(
                user_id=str(current_user.id),
                filename=file.filename,
                malware_type="multiple_engines",
                signature=f"{len(malware_scan_result.threats_detected)} threats detected",
                request=request
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Malware detected in file",
                    "threats": [
                        {
                            "engine": threat.engine.value,
                            "threat_type": threat.threat_type.value if threat.threat_type else None,
                            "threat_name": threat.threat_name,
                            "confidence": threat.confidence_score
                        }
                        for threat in malware_scan_result.threats_detected
                    ],
                    "scan_engines": malware_scan_result.total_engines,
                    "highest_confidence": malware_scan_result.highest_confidence
                }
            )
        
        # Step 2a: Sandbox analysis for suspicious files
        if validation_result.threat_level in [ThreatLevel.MEDIUM, ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            sandbox_result = await analyze_file_in_sandbox(
                file_content=content,
                filename=file.filename,
                user_id=str(current_user.id),
                analysis_type=AnalysisType.BEHAVIORAL
            )
            
            if sandbox_result.get("threat_detected", False):
                security_audit_logger.log_sandbox_analysis_threat(
                    user_id=str(current_user.id),
                    filename=file.filename,
                    risk_level="medium",  # Simple analyzer doesn't provide risk level
                    threats=sandbox_result.get("behavioral_indicators", []),
                    request=request
                )
                
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": "File failed sandbox analysis",
                        "risk_level": "medium",
                        "threats_detected": sandbox_result.get("behavioral_indicators", []),
                        "behavioral_indicators": sandbox_result.get("behavioral_indicators", [])
                    }
                )
        else:
            # Quick static analysis for safe files
            sandbox_result = await analyze_file_in_sandbox(
                file_content=content,
                filename=file.filename,
                user_id=str(current_user.id),
                analysis_type=AnalysisType.STATIC
            )
        
        # Step 3: File type specific validation
        if not file.filename.lower().endswith('.csv'):
            security_audit_logger.log_file_upload_failure(
                user_id=str(current_user.id),
                filename=file.filename,
                file_size=file_size,
                error="Invalid file extension",
                request=request
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only CSV files are supported"
            )
        
        # Step 4: Size validation with enhanced limits
        max_size = settings.MAX_FILE_SIZE
        if file_size > max_size:
            security_audit_logger.log_file_size_violation(
                user_id=str(current_user.id),
                filename=file.filename,
                file_size=file_size,
                max_allowed=max_size,
                request=request
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {max_size / (1024*1024):.1f} MB"
            )
        
        # Step 5: Content sanitization and CSV parsing
        try:
            # Decode content with encoding validation
            try:
                content_str = content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    content_str = content.decode('latin-1')
                    logger.warning(f"File {file.filename} uses non-UTF-8 encoding")
                except UnicodeDecodeError as e:
                    # Log original error for developers
                    error_detail = create_secure_error_response(
                        exception=e,
                        error_code="FILE_ENCODING_ERROR",
                        error_category=ErrorCategory.VALIDATION,
                        correlation_id=str(uuid.uuid4()),
                        user_message="File encoding error. Please ensure the file is UTF-8 encoded.",
                        suggested_action="Save the file as UTF-8 encoded and try uploading again."
                    )
                    
                    security_audit_logger.log_file_upload_failure(
                        user_id=str(current_user.id),
                        filename=file.filename,
                        file_size=file_size,
                        error=f"Encoding error: {error_detail.correlation_id}",
                        request=request
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=error_detail.user_message
                    )
            
            # Step 5a: Sanitize content for security
            sanitization_result = await sanitize_csv_content(
                content=content_str,
                filename=file.filename,
                user_id=str(current_user.id),
                level=SanitizationLevel.STRICT
            )
            
            if not sanitization_result.is_safe:
                security_audit_logger.log_content_sanitization_failure(
                    user_id=str(current_user.id),
                    filename=file.filename,
                    security_issues=sanitization_result.security_issues,
                    request=request
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": "Content sanitization failed - file contains unsafe content",
                        "security_issues": sanitization_result.security_issues,
                        "modifications_attempted": len(sanitization_result.modifications_made)
                    }
                )
            
            # Use sanitized content for processing
            content_str = sanitization_result.sanitized_content
            
            logger.info(f"Content sanitization completed: {len(sanitization_result.modifications_made)} modifications made")
            
            # Parse CSV with enhanced security
            try:
                df = pd.read_csv(io.StringIO(content_str))
            except pd.errors.ParserError as e:
                logger.warning(f"Standard CSV parsing failed: {e}. Trying flexible parsing...")
                try:
                    df = pd.read_csv(
                        io.StringIO(content_str),
                        sep=None,
                        engine='python',
                        quoting=3,
                        on_bad_lines='warn'
                    )
                except Exception as e2:
                    # Create sanitized error response
                    error_detail = create_secure_error_response(
                        exception=e2,
                        error_code="CSV_PARSING_ERROR",
                        error_category=ErrorCategory.VALIDATION,
                        correlation_id=str(uuid.uuid4()),
                        user_message="Could not parse CSV file. Please check the file format and try again.",
                        suggested_action="Ensure the file is a valid CSV with proper formatting."
                    )
                    
                    security_audit_logger.log_file_upload_failure(
                        user_id=str(current_user.id),
                        filename=file.filename,
                        file_size=file_size,
                        error=f"CSV parsing failed: {error_detail.correlation_id}",
                        request=request
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=error_detail.user_message
                    )
            
            if df.empty:
                security_audit_logger.log_file_upload_failure(
                    user_id=str(current_user.id),
                    filename=file.filename,
                    file_size=file_size,
                    error="Empty CSV file",
                    request=request
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="CSV file is empty"
                )
            
            logger.info(f"CSV loaded successfully: {len(df)} rows, {len(df.columns)} columns")
            
        except pd.errors.EmptyDataError:
            security_audit_logger.log_file_upload_failure(
                user_id=str(current_user.id),
                filename=file.filename,
                file_size=file_size,
                error="Empty CSV data",
                request=request
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file contains no data"
            )
        
        # Step 6: Parse and validate CSV structure
        await emit_parsing_progress(
            batch_id=batch_id,
            progress=50.0,
            message="Parsing CSV data and validating structure",
            user_id=str(current_user.id),
            details={"rows": len(df), "columns": len(df.columns)}
        )
        
        parser = CSVParser()
        parsing_result: ParsingResult = parser.parse_dataframe(df)
        
        await emit_parsing_progress(
            batch_id=batch_id,
            progress=60.0,
            message="CSV parsing completed successfully",
            user_id=str(current_user.id),
            details={
                "successful_parsing": len(parsing_result.transactions),
                "failed_parsing": len(parsing_result.errors),
                "warnings": len(parsing_result.warnings)
            }
        )
        
        # Check for security violations in parsing
        security_errors = [error for error in parsing_result.errors if error.get('type') == 'security_violation']
        if security_errors:
            security_audit_logger.log_suspicious_file_content(
                user_id=str(current_user.id),
                filename=file.filename,
                content_indicators=[error['message'] for error in security_errors],
                request=request
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "CSV contains suspicious content",
                    "security_violations": security_errors
                }
            )
        
        logger.info(f"CSV parsing completed: {parsing_result.statistics}")
        
        # Step 7: Process transactions
        processed_count = 0
        db_errors = []
        total_transactions = len(parsing_result.transactions)
        
        await emit_database_progress(
            batch_id=batch_id,
            progress=65.0,
            message="Starting database insertion of transactions",
            user_id=str(current_user.id),
            details={"total": total_transactions}
        )
        
        for transaction_data in parsing_result.transactions:
            try:
                transaction = Transaction(
                    user_id=current_user.id,
                    date=transaction_data['date'],
                    amount=transaction_data['amount'],
                    description=transaction_data['description'],
                    vendor=transaction_data.get('vendor'),
                    source='csv',
                    import_batch=batch_id,
                    raw_data=transaction_data.get('raw_data', {}),
                    meta_data={
                        'filename': file.filename,
                        'import_date': datetime.utcnow().isoformat(),
                        'validation_passed': True,
                        'malware_scan_clean': True
                    },
                    is_income=transaction_data.get('is_income', False)
                )
                
                db.add(transaction)
                processed_count += 1
                
                # Emit progress every 10% or every 50 transactions
                if processed_count % max(1, total_transactions // 10) == 0 or processed_count % 50 == 0:
                    progress = 65.0 + (processed_count / total_transactions) * 10  # 65% to 75%
                    await emit_database_progress(
                        batch_id=batch_id,
                        progress=progress,
                        message=f"Processing transactions ({processed_count}/{total_transactions})",
                        user_id=str(current_user.id),
                        details={"processed": processed_count, "total": total_transactions, "errors": len(db_errors)}
                    )
                
            except Exception as e:
                # Sanitize database error before storing
                sanitized_message = error_sanitizer.sanitize_error_message(str(e))
                db_error = {
                    'row_number': transaction_data.get('row_number'),
                    'error_type': 'database_error',
                    'message': 'Transaction processing failed',
                    'correlation_id': str(uuid.uuid4())
                }
                db_errors.append(db_error)
                
                # Log original error for developers with correlation ID
                error_sanitizer.log_original_error(
                    exception=e,
                    correlation_id=db_error['correlation_id'],
                    request_context={
                        'user_id': current_user.id,
                        'filename': file.filename,
                        'row_number': transaction_data.get('row_number')
                    }
                )
                logger.error(f"Database error for row {transaction_data.get('row_number')}: {db_error['correlation_id']}")
        
        # Step 8: Commit to database
        await emit_database_progress(
            batch_id=batch_id,
            progress=75.0,
            message="Committing transactions to database",
            user_id=str(current_user.id),
            details={"processed": processed_count, "errors": len(db_errors)}
        )
        
        try:
            db.commit()
            logger.info(f"Successfully committed {processed_count} transactions")
            
            await emit_database_progress(
                batch_id=batch_id,
                progress=80.0,
                message="Database commit completed successfully",
                user_id=str(current_user.id),
                details={"processed": processed_count}
            )
        except Exception as e:
            db.rollback()
            
            # Create sanitized error response
            error_detail = create_secure_error_response(
                exception=e,
                error_code="DATABASE_COMMIT_ERROR",
                error_category=ErrorCategory.SYSTEM_ERROR,
                correlation_id=str(uuid.uuid4()),
                user_message="Failed to save transactions. Please try again.",
                suggested_action="If the problem persists, please contact support."
            )
            
            security_audit_logger.log_file_upload_failure(
                user_id=str(current_user.id),
                filename=file.filename,
                file_size=file_size,
                error=f"Database commit failed: {error_detail.correlation_id}",
                request=request
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_detail.user_message
            )
        
        # Step 9: Apply categorization
        await emit_categorization_progress(
            batch_id=batch_id,
            progress=85.0,
            message="Starting transaction categorization",
            user_id=str(current_user.id),
            details={"transactions_to_categorize": processed_count}
        )
        
        categorization_service = CategorizationService(db)
        categorization_result = await categorization_service.categorize_user_transactions(
            current_user.id, batch_id
        )
        categorized_count = categorization_result['rule_categorized'] + categorization_result['ml_categorized']
        
        await emit_categorization_progress(
            batch_id=batch_id,
            progress=95.0,
            message="Transaction categorization completed",
            user_id=str(current_user.id),
            details={
                "categorized_count": categorized_count,
                "categorization_rate": round((categorized_count / processed_count * 100), 2) if processed_count > 0 else 0
            }
        )
        
        # Step 10: Log successful upload
        security_audit_logger.log_file_upload_success(
            user_id=str(current_user.id),
            filename=file.filename,
            file_size=file_size,
            batch_id=batch_id,
            processed_count=processed_count,
            request=request
        )
        
        # Prepare comprehensive response
        all_errors = parsing_result.errors + db_errors
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        response_data = {
            "message": "File uploaded and processed successfully",
            "processing_mode": "sync",
            "batch_id": batch_id,
            "file_hash": batch_id,  # For transparency - batch_id is now the file hash
            "file_info": {
                "filename": file.filename,
                "file_size": file_size,
                "total_rows": len(df),
                "validation_passed": True,
                "threat_level": validation_result.threat_level.value,
                "malware_scan_clean": malware_scan_result.is_clean,
                "duplicate_prevention": "SHA256 hash-based"
            },
            "security_validation": {
                "validation_duration": validation_result.scan_duration,
                "malware_scan_duration": malware_scan_result.scan_duration,
                "scan_engines_used": malware_scan_result.total_engines,
                "validation_checks": validation_result.validation_checks,
                "warnings": validation_result.warnings
            },
            "content_sanitization": {
                "sanitization_level": sanitization_result.sanitization_level.value,
                "modifications_made": len(sanitization_result.modifications_made),
                "security_issues_resolved": len(sanitization_result.security_issues),
                "size_reduction": sanitization_result.original_size - sanitization_result.sanitized_size,
                "is_content_safe": sanitization_result.is_safe
            },
            "sandbox_analysis": {
                "analysis_type": sandbox_result.get("analysis_type", "static"),
                "risk_level": "low",  # Simple analyzer always returns low risk
                "is_safe": not sandbox_result.get("threat_detected", False),
                "threats_detected": len(sandbox_result.get("behavioral_indicators", [])),
                "behavioral_indicators": len(sandbox_result.get("behavioral_indicators", [])),
                "analysis_duration": sandbox_result.get("analysis_duration", 0.001),
                "static_analysis_findings": 0,  # Simple analyzer doesn't provide this
                "errors": 0  # Simple analyzer doesn't provide this
            },
            "parsing_results": {
                "successful_parsing": len(parsing_result.transactions),
                "failed_parsing": len(parsing_result.errors),
                "success_rate": parsing_result.statistics['success_rate'],
                "warning_count": len(parsing_result.warnings)
            },
            "database_results": {
                "processed_count": processed_count,
                "database_errors": len(db_errors)
            },
            "categorization_results": {
                "categorized_count": categorized_count,
                "categorization_rate": round((categorized_count / processed_count * 100), 2) if processed_count > 0 else 0
            },
            "statistics": parsing_result.statistics,
            "errors": all_errors,
            "warnings": parsing_result.warnings,
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
                "duplicate_prevention": "SHA256_HASH_BASED",
                "file_hash": truncate_hash_for_display(batch_id)  # Truncated hash for response
            }
        }
        
        # Final progress update
        await emit_categorization_progress(
            batch_id=batch_id,
            progress=100.0,
            message="Upload completed successfully",
            user_id=str(current_user.id),
            details={
                "total_transactions": processed_count,
                "categorized_count": categorized_count,
                "overall_success_rate": response_data['summary']['overall_success_rate']
            }
        )
        
        logger.info(f"Upload completed successfully for user {current_user.id}: {response_data['summary']}")
        
        return response_data
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        
        # Create sanitized error response for unexpected errors
        error_detail = create_secure_error_response(
            exception=e,
            error_code="FILE_PROCESSING_ERROR",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4()),
            user_message="An unexpected error occurred while processing your file.",
            suggested_action="Please try again. If the problem persists, contact support."
        )
        
        # Log unexpected errors with correlation ID
        security_audit_logger.log_file_upload_failure(
            user_id=str(current_user.id),
            filename=file.filename,
            file_size=len(content) if 'content' in locals() else 0,
            error=f"Unexpected error: {error_detail.correlation_id}",
            request=request
        )
        logger.error(f"Unexpected error processing file {file.filename}: {error_detail.correlation_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail.user_message
        )

@router.get("/status/{batch_id}")
async def get_upload_status(
    batch_id: str,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Get detailed status of uploaded batch
    """
    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.import_batch == batch_id
    ).all()
    
    if not transactions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )
    
    total_count = len(transactions)
    categorized_count = sum(1 for t in transactions if t.is_categorized)
    processed_count = sum(1 for t in transactions if t.is_processed)
    
    # Calculate additional statistics
    income_count = sum(1 for t in transactions if t.is_income)
    expense_count = total_count - income_count
    
    total_income = sum(t.amount for t in transactions if t.is_income)
    total_expenses = sum(abs(t.amount) for t in transactions if not t.is_income)
    
    # Category breakdown
    categories = {}
    for transaction in transactions:
        if transaction.category and not transaction.is_income:
            category = transaction.category
            amount = abs(transaction.amount)
            categories[category] = categories.get(category, 0) + amount
    
    return {
        "batch_id": batch_id,
        "total_count": total_count,
        "categorized_count": categorized_count,
        "processed_count": processed_count,
        "categorization_rate": round((categorized_count / total_count * 100), 2) if total_count > 0 else 0,
        "status": "completed" if processed_count == total_count else "processing",
        "transaction_summary": {
            "income_count": income_count,
            "expense_count": expense_count,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_amount": total_income - total_expenses
        },
        "categories": categories,
        "date_range": {
            "earliest": min(t.date for t in transactions).isoformat() if transactions else None,
            "latest": max(t.date for t in transactions).isoformat() if transactions else None
        }
    }

@router.get("/validation-rules")
async def get_validation_rules():
    """
    Get information about supported CSV formats and validation rules
    """
    return {
        "supported_formats": {
            "file_types": ["CSV"],
            "encoding": ["UTF-8"],
            "max_file_size": f"{settings.MAX_FILE_SIZE / (1024*1024):.1f} MB"
        },
        "required_columns": ["date", "amount", "description"],
        "optional_columns": ["vendor", "reference"],
        "supported_date_formats": [
            "YYYY-MM-DD", "MM/DD/YYYY", "DD/MM/YYYY", "YYYY/MM/DD",
            "MM-DD-YYYY", "DD-MM-YYYY", "MMM DD, YYYY", "MMMM DD, YYYY",
            "YYYY-MM-DD HH:MM:SS", "MM/DD/YYYY HH:MM:SS",
            "YYYYMMDD", "MMDDYYYY", "DDMMYYYY"
        ],
        "supported_amount_formats": [
            "1234.56", "1,234.56", "1234,56", "$1234.56", "€1234.56",
            "1234.56 USD", "USD 1234.56", "+1234.56", "-1234.56"
        ],
        "validation_rules": {
            "date_validation": "Dates must be between 2000-01-01 and current date",
            "amount_validation": "Amounts must be numeric and non-zero",
            "description_validation": "Descriptions must be non-empty and at least 3 characters",
            "vendor_validation": "Vendor is optional but must be non-empty if provided"
        },
        "warnings": {
            "large_amount": "Amounts over $1,000,000 will trigger a warning",
            "future_date": "Future dates will trigger a warning",
            "old_date": "Dates before 2000 will trigger a warning",
            "short_description": "Descriptions under 3 characters will trigger a warning",
            "zero_amount": "Zero amounts will trigger a warning"
        }
    }

@router.post("/csv/async")
async def upload_csv_async(
    request: Request,
    file: UploadFile = File(...),
    batch_id: Optional[str] = None,
    priority: Optional[str] = "normal",
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Upload and process CSV file asynchronously using background job queue.
    
    This endpoint queues the file processing as a background job and returns immediately
    with a job ID for tracking progress. The same comprehensive security validation and
    processing pipeline is maintained, but execution happens asynchronously.
    
    Features:
    - Immediate response with job ID for tracking
    - Background processing with progress updates
    - Same security measures as synchronous upload
    - WebSocket progress notifications
    - Comprehensive error handling and retry logic
    - Job priority support for urgent uploads
    
    Priority levels:
    - critical: Highest priority, processed immediately
    - high: High priority, processed before normal jobs  
    - normal: Default priority (recommended)
    - low: Lower priority, processed when resources available
    
    Returns:
    - job_id: Unique identifier for tracking the background job
    - status: Initial job status
    - estimated_processing_time: Estimated time to completion
    - tracking_endpoints: URLs for monitoring progress
    """
    
    start_time = datetime.utcnow()
    
    # Basic file validation
    if not file.filename:
        security_audit_logger.log_file_upload_failure(
            user_id=str(current_user.id),
            filename="<no filename>",
            file_size=0,
            error="No filename provided",
            request=request
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )
    
    try:
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Log upload attempt
        security_audit_logger.log_file_upload_attempt(
            user_id=str(current_user.id),
            filename=file.filename,
            file_size=file_size,
            timestamp=start_time,
            request=request
        )
        
        logger.info(f"Processing async file upload: {file.filename}, size: {file_size} bytes, user: {current_user.id}")
        
        # Validate priority
        try:
            job_priority = JobPriority(priority.lower())
        except ValueError:
            job_priority = JobPriority.NORMAL
        
        # Basic file type validation (early check)
        if not file.filename.lower().endswith('.csv'):
            security_audit_logger.log_file_upload_failure(
                user_id=str(current_user.id),
                filename=file.filename,
                file_size=file_size,
                error="Invalid file extension",
                request=request
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only CSV files are supported"
            )
        
        # Basic size validation (early check)
        max_size = settings.MAX_FILE_SIZE
        if file_size > max_size:
            security_audit_logger.log_file_size_violation(
                user_id=str(current_user.id),
                filename=file.filename,
                file_size=file_size,
                max_allowed=max_size,
                request=request
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {max_size / (1024*1024):.1f} MB"
            )
        
        # Check user job limits
        user_jobs = await job_manager.get_user_jobs(str(current_user.id), limit=50)
        active_jobs = [job for job in user_jobs if job.state in ['queued', 'started', 'processing']]
        
        if len(active_jobs) >= settings.MAX_CONCURRENT_JOBS_PER_USER:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many active jobs. Maximum concurrent jobs: {settings.MAX_CONCURRENT_JOBS_PER_USER}"
            )
        
        # Generate SHA256 file hash for batch_id (duplicate prevention)
        if not batch_id:
            file_hash = calculate_file_hash_streaming(content)
            batch_id = file_hash
            
            logger.info(f"Generated SHA256 hash for {file.filename}: {truncate_hash_for_display(file_hash)} (size: {file_size} bytes)")
            
            # Early duplicate detection
            existing_upload = db.query(Transaction).filter(
                Transaction.user_id == current_user.id,
                Transaction.import_batch == file_hash
            ).first()
            
            if existing_upload:
                security_audit_logger.log_file_upload_failure(
                    user_id=str(current_user.id),
                    filename=file.filename,
                    file_size=file_size,
                    error=f"Duplicate file upload detected - hash: {truncate_hash_for_display(file_hash)}",
                    request=request
                )
                
                logger.warning(f"Duplicate file upload rejected for user {current_user.id}: hash {truncate_hash_for_display(file_hash)}")
                
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "message": "This file has already been uploaded",
                        "duplicate_batch_id": file_hash,
                        "error_code": "DUPLICATE_FILE_UPLOAD",
                        "suggested_action": f"Use DELETE /api/v1/transactions/import-batch/{file_hash} to remove the previous upload before re-uploading"
                    }
                )
        
        # Get client info for monitoring
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("User-Agent")
        
        # Queue the background job
        job_id = await job_manager.queue_csv_upload_job(
            user_id=str(current_user.id),
            file_content=content,
            filename=file.filename,
            file_size=file_size,
            batch_id=batch_id,
            client_ip=client_ip,
            user_agent=user_agent,
            priority=job_priority
        )
        
        # Estimate processing time based on file size
        estimated_time_minutes = max(1, file_size / (1024 * 1024))  # Rough estimate: 1 minute per MB
        if file_size > 5 * 1024 * 1024:  # Files > 5MB get longer estimates
            estimated_time_minutes *= 1.5
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        response_data = {
            "message": "File upload queued for background processing",
            "job_id": job_id,
            "batch_id": batch_id,
            "file_hash": batch_id,
            "status": "queued",
            "priority": job_priority.value,
            "file_info": {
                "filename": file.filename,
                "file_size": file_size,
                "estimated_processing_time_minutes": round(estimated_time_minutes, 1)
            },
            "tracking": {
                "status_endpoint": f"/api/v1/upload/jobs/{job_id}/status",
                "progress_endpoint": f"/api/v1/upload/jobs/{job_id}/progress",
                "cancel_endpoint": f"/api/v1/upload/jobs/{job_id}/cancel",
                "websocket_updates": "Connect to WebSocket for real-time progress"
            },
            "queue_info": {
                "position_estimate": "Processing will begin shortly",
                "active_jobs": len(active_jobs),
                "max_concurrent": settings.MAX_CONCURRENT_JOBS_PER_USER
            },
            "performance": {
                "queue_time": processing_time,
                "estimated_total_time_minutes": round(estimated_time_minutes, 1)
            },
            "instructions": {
                "monitoring": "Use the provided tracking endpoints to monitor progress",
                "websocket": "Connect to WebSocket for real-time updates",
                "completion": "You'll receive a completion notification via WebSocket"
            }
        }
        
        logger.info(f"Queued async CSV upload job {job_id} for user {current_user.id}")
        
        return response_data
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Create sanitized error response for unexpected errors
        error_detail = create_secure_error_response(
            exception=e,
            error_code="JOB_QUEUE_ERROR",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4()),
            user_message="Failed to queue upload job. Please try again.",
            suggested_action="If the problem persists, try the synchronous upload endpoint."
        )
        
        security_audit_logger.log_file_upload_failure(
            user_id=str(current_user.id),
            filename=file.filename,
            file_size=len(content) if 'content' in locals() else 0,
            error=f"Job queue error: {error_detail.correlation_id}",
            request=request
        )
        
        logger.error(f"Failed to queue upload job for file {file.filename}: {error_detail.correlation_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail.user_message
        )

@router.get("/jobs/{job_id}/status")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Get detailed status and progress of a background upload job.
    
    Returns comprehensive job information including:
    - Current status and progress percentage
    - Processing details and error information
    - Performance metrics and timing
    - Result data when completed
    """
    try:
        job_progress = await job_manager.get_job_status(job_id)
        
        if not job_progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Verify user owns this job
        if job_progress.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"  # Don't reveal job exists to unauthorized user
            )
        
        # Calculate elapsed time and estimated completion
        elapsed_time = (datetime.utcnow() - job_progress.created_at).total_seconds()
        
        # Estimate remaining time based on progress
        estimated_remaining = None
        if job_progress.progress_percentage > 0 and job_progress.state == JobState.PROCESSING:
            estimated_total = elapsed_time / (job_progress.progress_percentage / 100.0)
            estimated_remaining = max(0, estimated_total - elapsed_time)
        
        response_data = {
            "job_id": job_id,
            "status": job_progress.state.value,
            "progress": {
                "percentage": job_progress.progress_percentage,
                "current_step": job_progress.current_step,
                "message": job_progress.message,
                "details": job_progress.details
            },
            "timing": {
                "created_at": job_progress.created_at.isoformat(),
                "updated_at": job_progress.updated_at.isoformat(),
                "started_at": job_progress.started_at.isoformat() if job_progress.started_at else None,
                "completed_at": job_progress.completed_at.isoformat() if job_progress.completed_at else None,
                "elapsed_seconds": round(elapsed_time, 2),
                "estimated_remaining_seconds": round(estimated_remaining, 2) if estimated_remaining else None
            },
            "job_info": {
                "job_type": job_progress.job_type.value,
                "retry_count": job_progress.retry_count,
                "max_retries": job_progress.max_retries
            }
        }
        
        # Add error information if job failed
        if job_progress.error_info:
            response_data["error"] = {
                "message": job_progress.error_info.get("message", "Job failed"),
                "error_code": job_progress.error_info.get("error_code"),
                "correlation_id": job_progress.error_info.get("correlation_id")
            }
        
        # Add completion data for completed jobs
        if job_progress.state == JobState.COMPLETED and job_progress.details:
            response_data["result"] = {
                "batch_id": job_progress.details.get("batch_id"),
                "total_transactions": job_progress.details.get("total_transactions"),
                "categorized_count": job_progress.details.get("categorized_count"),
                "processing_time": job_progress.details.get("processing_time"),
                "overall_success_rate": job_progress.details.get("overall_success_rate")
            }
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status for {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job status"
        )

@router.get("/jobs/{job_id}/progress")
async def get_job_progress(
    job_id: str,
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Get real-time progress updates for a background upload job.
    
    Lightweight endpoint optimized for frequent polling to get
    just the essential progress information.
    """
    try:
        job_progress = await job_manager.get_job_status(job_id)
        
        if not job_progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Verify user owns this job
        if job_progress.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        return {
            "job_id": job_id,
            "status": job_progress.state.value,
            "progress_percentage": job_progress.progress_percentage,
            "current_step": job_progress.current_step,
            "message": job_progress.message,
            "updated_at": job_progress.updated_at.isoformat(),
            "is_complete": job_progress.state in [JobState.COMPLETED, JobState.FAILED, JobState.CANCELLED]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job progress for {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job progress"
        )

@router.post("/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Cancel a queued or running background upload job.
    
    Jobs can only be cancelled by the user who created them
    and only if they are in a cancellable state.
    """
    try:
        # Verify job exists and user owns it
        job_progress = await job_manager.get_job_status(job_id)
        
        if not job_progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        if job_progress.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Check if job can be cancelled
        if job_progress.state in [JobState.COMPLETED, JobState.FAILED, JobState.CANCELLED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel job in {job_progress.state.value} state"
            )
        
        # Attempt to cancel the job
        success = await job_manager.cancel_job(job_id, str(current_user.id))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to cancel job"
            )
        
        logger.info(f"Job {job_id} cancelled by user {current_user.id}")
        
        return {
            "message": "Job cancelled successfully",
            "job_id": job_id,
            "status": "cancelled",
            "cancelled_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel job"
        )

@router.get("/jobs")
async def get_user_jobs(
    current_user: User = Depends(get_current_user_from_cookie),
    limit: int = 20,
    status_filter: Optional[str] = None
):
    """
    Get all background upload jobs for the current user.
    
    Supports filtering by status and pagination for efficient
    job management and monitoring.
    """
    try:
        # Validate limit
        limit = min(max(1, limit), 100)  # Between 1 and 100
        
        # Get user's jobs
        user_jobs = await job_manager.get_user_jobs(str(current_user.id), limit=limit)
        
        # Filter by status if requested
        if status_filter:
            try:
                filter_state = JobState(status_filter.lower())
                user_jobs = [job for job in user_jobs if job.state == filter_state]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter: {status_filter}"
                )
        
        # Format response
        jobs_data = []
        for job in user_jobs:
            elapsed_time = (datetime.utcnow() - job.created_at).total_seconds()
            
            job_data = {
                "job_id": job.job_id,
                "job_type": job.job_type.value,
                "status": job.state.value,
                "progress_percentage": job.progress_percentage,
                "current_step": job.current_step,
                "message": job.message,
                "created_at": job.created_at.isoformat(),
                "updated_at": job.updated_at.isoformat(),
                "elapsed_seconds": round(elapsed_time, 2),
                "details": {
                    "filename": job.details.get("filename"),
                    "file_size": job.details.get("file_size"),
                    "batch_id": job.details.get("batch_id")
                }
            }
            
            # Add completion info for finished jobs
            if job.state == JobState.COMPLETED:
                job_data["result"] = {
                    "total_transactions": job.details.get("total_transactions"),
                    "categorized_count": job.details.get("categorized_count"),
                    "overall_success_rate": job.details.get("overall_success_rate")
                }
            elif job.state == JobState.FAILED and job.error_info:
                job_data["error"] = {
                    "message": job.error_info.get("message", "Job failed"),
                    "error_code": job.error_info.get("error_code")
                }
            
            jobs_data.append(job_data)
        
        # Get summary statistics
        total_jobs = len(user_jobs)
        status_counts = {}
        for job in user_jobs:
            status = job.state.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "jobs": jobs_data,
            "summary": {
                "total_jobs": total_jobs,
                "status_counts": status_counts,
                "limit": limit,
                "filtered_by": status_filter
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user jobs for {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve jobs"
        )

@router.get("/queue/stats")
async def get_queue_statistics(
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Get comprehensive queue statistics and system health information.
    
    Provides insight into job queue performance, capacity, and
    processing metrics for monitoring and capacity planning.
    """
    try:
        # Get queue statistics
        queue_stats = job_manager.get_queue_stats()
        
        # Get user's active jobs
        user_jobs = await job_manager.get_user_jobs(str(current_user.id), limit=50)
        user_active_jobs = [job for job in user_jobs if job.state in [JobState.QUEUED, JobState.STARTED, JobState.PROCESSING]]
        
        # Calculate user-specific statistics
        user_stats = {
            "active_jobs": len(user_active_jobs),
            "max_concurrent": settings.MAX_CONCURRENT_JOBS_PER_USER,
            "remaining_capacity": max(0, settings.MAX_CONCURRENT_JOBS_PER_USER - len(user_active_jobs))
        }
        
        return {
            "queue_statistics": queue_stats,
            "user_statistics": user_stats,
            "system_limits": {
                "max_concurrent_jobs_per_user": settings.MAX_CONCURRENT_JOBS_PER_USER,
                "max_jobs_per_user_per_hour": settings.MAX_JOBS_PER_USER_PER_HOUR,
                "job_timeout_minutes": settings.JOB_TIMEOUT_MINUTES,
                "max_job_retries": settings.MAX_JOB_RETRIES
            },
            "queue_health": {
                "status": "healthy" if queue_stats.get("total_queued", 0) < 1000 else "busy",
                "total_queued": queue_stats.get("total_queued", 0),
                "processing_capacity": "available" if user_stats["remaining_capacity"] > 0 else "at_limit"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get queue statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve queue statistics"
        )
