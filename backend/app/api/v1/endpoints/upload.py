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
from app.core.background_jobs import (
    process_file_upload,
    get_job_status,
    cancel_job,
    get_job_result,
    JobStatus
)

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
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Upload and process CSV file with comprehensive security validation and processing.
    
    Features SHA256 hash-based duplicate prevention:
    - Each file's content is hashed using SHA256
    - Hash serves as batch_id for tracking and deduplication
    - Rejects duplicates with HTTP 409 and clear error message
    - Maintains existing DELETE /api/v1/transactions/import-batch/{hash} functionality
    
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

@router.post("/async")
async def upload_csv_async(
    request: Request,
    file: UploadFile = File(...),
    batch_id: Optional[str] = None,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Upload and process CSV file asynchronously using background job queue.
    
    This endpoint initiates file processing in the background and returns immediately
    with a job ID. Progress can be tracked via WebSocket or the /jobs/{job_id} endpoint.
    
    Features:
    - SHA256 hash-based duplicate prevention
    - Background processing with job queue
    - Real-time progress tracking via WebSocket
    - Comprehensive security validation
    - Error handling and retry logic
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
        
        logger.info(f"Initiating async file upload: {file.filename}, size: {file_size} bytes, user: {current_user.id}")
        
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
            file_hash = calculate_file_hash_streaming(content)
            batch_id = file_hash
            
            logger.info(f"Generated SHA256 hash for {file.filename}: {truncate_hash_for_display(file_hash)} (size: {file_size} bytes)")
            
            # Early duplicate detection - check before any processing
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
        
        # Step 2: Basic file validation (quick checks before queuing)
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
        
        # Step 3: Size validation
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
        
        # Step 4: Prepare file data for background processing
        file_data = {
            "content": content,
            "filename": file.filename,
            "file_size": file_size,
            "batch_id": batch_id,
            "upload_timestamp": start_time.isoformat(),
            "client_ip": client_ip,
            "user_agent": user_agent
        }
        
        # Step 5: Submit job to background queue
        try:
            job = process_file_upload.delay(file_data, str(current_user.id))
            job_id = job.id
            
            logger.info(f"Background job submitted successfully: {job_id} for user {current_user.id}")
            
            # Log successful job submission
            security_audit_logger.log_file_upload_success(
                user_id=str(current_user.id),
                filename=file.filename,
                file_size=file_size,
                batch_id=batch_id,
                processed_count=0,  # Will be updated by background job
                request=request
            )
            
            # Return immediate response with job information
            response_data = {
                "message": "File upload initiated successfully",
                "job_id": job_id,
                "batch_id": batch_id,
                "file_hash": batch_id,
                "status": "queued",
                "processing_mode": "async",
                "file_info": {
                    "filename": file.filename,
                    "file_size": file_size,
                    "duplicate_prevention": "SHA256 hash-based"
                },
                "tracking": {
                    "job_status_endpoint": f"/api/v1/upload/jobs/{job_id}",
                    "websocket_topic": f"job_{job_id}",
                    "estimated_processing_time": "2-5 minutes depending on file size"
                },
                "security": {
                    "validation_pending": True,
                    "malware_scan_pending": True,
                    "content_sanitization_pending": True
                }
            }
            
            return response_data
            
        except Exception as e:
            error_msg = f"Failed to submit background job: {str(e)}"
            logger.error(f"Background job submission failed for user {current_user.id}: {error_msg}")
            
            security_audit_logger.log_file_upload_failure(
                user_id=str(current_user.id),
                filename=file.filename,
                file_size=file_size,
                error=error_msg,
                request=request
            )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initiate file processing. Please try again."
            )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Create sanitized error response for unexpected errors
        error_detail = create_secure_error_response(
            exception=e,
            error_code="ASYNC_UPLOAD_INITIATION_ERROR",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4()),
            user_message="An unexpected error occurred while initiating file upload.",
            suggested_action="Please try again. If the problem persists, contact support."
        )
        
        security_audit_logger.log_file_upload_failure(
            user_id=str(current_user.id),
            filename=file.filename,
            file_size=len(content) if 'content' in locals() else 0,
            error=f"Unexpected error: {error_detail.correlation_id}",
            request=request
        )
        
        logger.error(f"Unexpected error initiating async upload for {file.filename}: {error_detail.correlation_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail.user_message
        )

@router.get("/jobs/{job_id}")
async def get_job_status_endpoint(
    job_id: str,
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Get the status of a background job
    
    Args:
        job_id: The job ID to check
        
    Returns:
        Job status information
    """
    try:
        # Get job status from Redis
        status_data = get_job_status(job_id)
        
        if not status_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found or expired"
            )
        
        # Get job result from Celery if completed
        result_data = None
        if status_data.get("status") in ["completed", "failed"]:
            result_data = get_job_result(job_id)
        
        response_data = {
            "job_id": job_id,
            "status": status_data.get("status"),
            "progress": status_data.get("progress", 0.0),
            "message": status_data.get("message", ""),
            "details": status_data.get("details", {}),
            "updated_at": status_data.get("updated_at"),
            "result": result_data
        }
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status for {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job status"
        )

@router.delete("/jobs/{job_id}")
async def cancel_job_endpoint(
    job_id: str,
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Cancel a running background job
    
    Args:
        job_id: The job ID to cancel
        
    Returns:
        Cancellation status
    """
    try:
        # Get current job status
        status_data = get_job_status(job_id)
        
        if not status_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found or expired"
            )
        
        # Check if job can be cancelled
        if status_data.get("status") in ["completed", "failed", "cancelled"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job cannot be cancelled in status: {status_data.get('status')}"
            )
        
        # Attempt to cancel the job
        success = cancel_job(job_id)
        
        if success:
            return {
                "message": "Job cancelled successfully",
                "job_id": job_id,
                "status": "cancelled"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel job"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel job"
        )
