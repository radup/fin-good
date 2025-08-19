"""
Export API endpoints for FinGood Financial Platform

This module provides comprehensive export functionality including:
- Multi-format exports (CSV, Excel, PDF, JSON)
- Background job processing with progress tracking
- Template management for PDF exports
- Export history and download management
- Security and audit compliance
"""

import hashlib
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status, BackgroundTasks, Query
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.audit_logger import security_audit_logger
from app.core.background_jobs import JobPriority
from app.core.config import settings
from app.core.error_handlers import create_error_response
from app.core.rate_limiting import RateLimiter
from app.core.security_utils import input_sanitizer
from app.models.export_job import ExportJob, ExportTemplate
from app.models.user import User
from app.schemas.export import (
    ExportFormat, ExportRequest, ExportJobResponse, ExportProgress,
    ExportFilterParams, ExportColumnsConfig, ExportOptionsConfig,
    ExportHistoryEntry, ExportStatus
)
from app.services.export_engine import EnhancedExportEngine

logger = logging.getLogger(__name__)
router = APIRouter()

# Rate limiting for export operations
export_rate_limiter = RateLimiter(
    max_requests=10,  # 10 export requests
    window_seconds=300,  # per 5 minutes
    key_func=lambda request: f"export:{request.state.user.id}"
)

download_rate_limiter = RateLimiter(
    max_requests=50,  # 50 downloads
    window_seconds=300,  # per 5 minutes
    key_func=lambda request: f"export_download:{request.client.host}"
)


@router.post("/create", response_model=ExportJobResponse)
async def create_export_job(
    export_request: ExportRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new export job for background processing.
    
    This endpoint creates an export job that will be processed asynchronously.
    The job supports multiple formats (CSV, Excel, PDF, JSON) with comprehensive
    filtering and formatting options.
    """
    try:
        # Apply rate limiting
        if not export_rate_limiter.is_allowed(request):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Export rate limit exceeded. Please try again later."
            )
        
        # Validate and sanitize export name
        export_name = None
        if export_request.export_name:
            export_name = input_sanitizer.sanitize_financial_input(
                export_request.export_name,
                field_name="export_name",
                max_length=100,
                remove_pii=True
            )
        
        # Determine job priority based on user tier and export size
        user_tier = getattr(current_user, 'tier', 'free')
        if hasattr(export_request.filters, 'estimated_size'):
            if export_request.filters.estimated_size > 100000:
                priority = JobPriority.LOW
            elif export_request.filters.estimated_size > 10000:
                priority = JobPriority.NORMAL
            else:
                priority = JobPriority.HIGH
        else:
            priority = JobPriority.HIGH if user_tier in ['premium', 'enterprise'] else JobPriority.NORMAL
        
        # Create export engine and submit job
        export_engine = EnhancedExportEngine(db)
        
        job_response = await export_engine.create_export_job(
            user_id=current_user.id,
            export_format=export_request.export_format,
            filters=export_request.filters,
            columns_config=export_request.columns,
            options_config=export_request.options,
            export_name=export_name,
            priority=priority
        )
        
        # Log export request for audit
        security_audit_logger.info(
            "Export job created via API",
            extra={
                "user_id": current_user.id,
                "job_id": job_response.job_id,
                "export_format": export_request.export_format.value,
                "client_ip": request.client.host,
                "user_agent": request.headers.get("user-agent", ""),
                "estimated_records": job_response.estimated_records
            }
        )
        
        return job_response
        
    except ValueError as e:
        logger.error(f"Export validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Export job creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create export job"
        )


@router.get("/progress/{job_id}", response_model=ExportProgress)
async def get_export_progress(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the progress of an export job.
    
    Returns real-time progress information including completion percentage,
    current operation, and estimated completion time.
    """
    try:
        # Validate job ID format
        if not job_id or len(job_id) != 36:  # UUID length
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid job ID format"
            )
        
        export_engine = EnhancedExportEngine(db)
        progress = export_engine.get_export_progress(job_id, current_user.id)
        
        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export job not found or access denied"
            )
        
        return progress
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get export progress for job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve export progress"
        )


@router.get("/download/{download_token}")
async def download_export_file(
    download_token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Download a completed export file using a secure download token.
    
    This endpoint provides secure file downloads with token validation,
    audit logging, and automatic cleanup of expired files.
    """
    try:
        # Apply download rate limiting
        if not download_rate_limiter.is_allowed(request):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Download rate limit exceeded. Please try again later."
            )
        
        # Validate token format
        if not download_token or len(download_token) != 64:  # SHA256 hash length
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid download token"
            )
        
        # Find export job by download token
        export_job = db.query(ExportJob).filter(
            ExportJob.download_token == download_token,
            ExportJob.status == "completed"
        ).first()
        
        if not export_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export file not found or download token expired"
            )
        
        # Check if export has expired
        if export_job.is_expired:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Export file has expired and is no longer available"
            )
        
        # Check if file exists
        if not export_job.file_path or not os.path.exists(export_job.file_path):
            logger.error(f"Export file not found: {export_job.file_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export file not found on server"
            )
        
        # Update download count and last downloaded timestamp
        export_job.increment_download_count()
        db.commit()
        
        # Log download for audit
        security_audit_logger.info(
            "Export file downloaded",
            extra={
                "user_id": export_job.user_id,
                "job_id": export_job.job_id,
                "download_token": download_token,
                "client_ip": request.client.host,
                "user_agent": request.headers.get("user-agent", ""),
                "download_count": export_job.download_count,
                "file_size": export_job.file_size_bytes
            }
        )
        
        # Prepare file response
        file_path = Path(export_job.file_path)
        filename = export_job.file_name or file_path.name
        
        # Set appropriate media type based on file extension
        media_type_map = {
            '.csv': 'text/csv',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.json': 'application/json',
            '.pdf': 'application/pdf',
            '.gz': 'application/gzip'
        }
        
        media_type = media_type_map.get(file_path.suffix.lower(), 'application/octet-stream')
        
        return FileResponse(
            path=export_job.file_path,
            filename=filename,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Export-Job-ID": export_job.job_id,
                "X-File-Hash": export_job.file_hash or "",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download failed for token {download_token}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download export file"
        )


@router.get("/history", response_model=List[ExportHistoryEntry])
async def get_export_history(
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the user's export history.
    
    Returns a list of all export jobs created by the current user,
    including completed, failed, and in-progress exports.
    """
    try:
        export_engine = EnhancedExportEngine(db)
        history = export_engine.get_user_export_history(current_user.id, limit)
        
        # Convert to response format
        history_entries = []
        for item in history:
            history_entries.append(ExportHistoryEntry(
                job_id=item['job_id'],
                export_name=item['export_name'],
                export_format=ExportFormat(item['export_format']),
                status=ExportStatus(item['status']),
                created_at=item['created_at'],
                completed_at=item['completed_at'],
                expires_at=item['expires_at'],
                total_records=item['total_records'],
                file_size_bytes=item['file_size_bytes'],
                download_count=item['download_count'],
                download_url=f"/api/v1/export/download/{item['job_id']}" if item['is_downloadable'] else None,
                error_message=item['error_message']
            ))
        
        return history_entries
        
    except Exception as e:
        logger.error(f"Failed to get export history for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve export history"
        )


@router.delete("/cancel/{job_id}")
async def cancel_export_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancel a pending or in-progress export job.
    
    Only the user who created the job can cancel it, and only jobs
    that are still in progress can be cancelled.
    """
    try:
        # Validate job ID format
        if not job_id or len(job_id) != 36:  # UUID length
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid job ID format"
            )
        
        # Find and validate export job
        export_job = db.query(ExportJob).filter(
            ExportJob.job_id == job_id,
            ExportJob.user_id == current_user.id
        ).first()
        
        if not export_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export job not found"
            )
        
        # Check if job can be cancelled
        if export_job.is_terminal_state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel job in {export_job.status} state"
            )
        
        # Cancel the job
        export_job.mark_cancelled()
        db.commit()
        
        # Try to cancel the background job as well
        from app.core.background_jobs import job_manager
        try:
            await job_manager.cancel_job(job_id, str(current_user.id))
        except Exception as e:
            logger.warning(f"Failed to cancel background job {job_id}: {e}")
        
        # Log cancellation
        security_audit_logger.info(
            "Export job cancelled by user",
            extra={
                "user_id": current_user.id,
                "job_id": job_id,
                "previous_status": export_job.status
            }
        )
        
        return {"message": "Export job cancelled successfully", "job_id": job_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel export job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel export job"
        )


@router.get("/formats", response_model=Dict[str, Dict[str, str]])
async def get_supported_formats():
    """
    Get information about supported export formats.
    
    Returns details about each supported format including
    file extensions, descriptions, and capabilities.
    """
    return {
        "csv": {
            "extension": "csv",
            "description": "Comma-separated values format, compatible with Excel and other tools",
            "features": ["Custom delimiters", "UTF-8 with BOM", "Streaming for large datasets", "Compression"],
            "max_records": "1,000,000+",
            "typical_use": "Data analysis, spreadsheet import, automated processing"
        },
        "excel": {
            "extension": "xlsx",
            "description": "Microsoft Excel format with multiple sheets and formatting",
            "features": ["Multiple sheets", "Charts and graphs", "Conditional formatting", "Summary tables"],
            "max_records": "500,000",
            "typical_use": "Business reports, presentations, detailed analysis"
        },
        "json": {
            "extension": "json",
            "description": "JavaScript Object Notation format with rich metadata",
            "features": ["Structured data", "Metadata inclusion", "Category analytics", "API integration"],
            "max_records": "1,000,000+",
            "typical_use": "API integration, data backup, programmatic processing"
        },
        "pdf": {
            "extension": "pdf",
            "description": "Portable Document Format for professional reports",
            "features": ["Professional layouts", "Custom templates", "Summary statistics", "Print-ready"],
            "max_records": "10,000 (recommended)",
            "typical_use": "Financial reports, presentations, official documentation"
        }
    }


@router.get("/templates", response_model=List[Dict[str, str]])
async def get_export_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get available export templates for the current user.
    
    Templates are used primarily for PDF exports to provide
    consistent branding and formatting.
    """
    try:
        # Get user templates and public templates
        templates = db.query(ExportTemplate).filter(
            (ExportTemplate.user_id == current_user.id) |
            (ExportTemplate.is_public == True) |
            (ExportTemplate.is_system == True)
        ).order_by(
            ExportTemplate.is_system.desc(),
            ExportTemplate.is_public.desc(),
            ExportTemplate.name
        ).all()
        
        template_list = []
        for template in templates:
            template_list.append({
                "template_id": template.template_id,
                "name": template.name,
                "description": template.description,
                "template_type": template.template_type,
                "is_system": template.is_system,
                "is_public": template.is_public,
                "usage_count": template.usage_count,
                "created_at": template.created_at.isoformat()
            })
        
        return template_list
        
    except Exception as e:
        logger.error(f"Failed to get export templates for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve export templates"
        )


@router.post("/cleanup")
async def cleanup_expired_exports(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually trigger cleanup of expired export files.
    
    This endpoint allows users to clean up their expired exports
    and is also used by system administrators for maintenance.
    """
    try:
        # Check if user has admin privileges for system-wide cleanup
        user_tier = getattr(current_user, 'tier', 'free')
        is_admin = user_tier in ['admin', 'enterprise']
        
        export_engine = EnhancedExportEngine(db)
        
        # Run cleanup in background
        if is_admin:
            background_tasks.add_task(export_engine.cleanup_expired_exports)
            message = "System-wide cleanup initiated"
        else:
            # For non-admin users, only clean their own exports
            user_exports = db.query(ExportJob).filter(
                ExportJob.user_id == current_user.id,
                ExportJob.expires_at < datetime.utcnow(),
                ExportJob.auto_cleanup == True
            ).count()
            
            if user_exports > 0:
                background_tasks.add_task(export_engine.cleanup_expired_exports)
                message = f"Cleanup initiated for {user_exports} expired exports"
            else:
                message = "No expired exports found for cleanup"
        
        # Log cleanup request
        security_audit_logger.info(
            "Export cleanup requested",
            extra={
                "user_id": current_user.id,
                "is_admin": is_admin,
                "request_type": "manual_cleanup"
            }
        )
        
        return {"message": message}
        
    except Exception as e:
        logger.error(f"Export cleanup failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate export cleanup"
        )


@router.get("/stats", response_model=Dict[str, int])
async def get_export_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get export statistics for the current user.
    
    Returns counts of exports by status and other usage metrics.
    """
    try:
        # Get export counts by status
        stats = {}
        
        for status_value in ["pending", "processing", "completed", "failed", "cancelled"]:
            count = db.query(ExportJob).filter(
                ExportJob.user_id == current_user.id,
                ExportJob.status == status_value
            ).count()
            stats[f"{status_value}_count"] = count
        
        # Get total exports
        stats["total_exports"] = db.query(ExportJob).filter(
            ExportJob.user_id == current_user.id
        ).count()
        
        # Get exports in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        stats["exports_last_30_days"] = db.query(ExportJob).filter(
            ExportJob.user_id == current_user.id,
            ExportJob.created_at >= thirty_days_ago
        ).count()
        
        # Get total download count
        total_downloads = db.query(ExportJob).filter(
            ExportJob.user_id == current_user.id
        ).with_entities(ExportJob.download_count).all()
        
        stats["total_downloads"] = sum(row[0] or 0 for row in total_downloads)
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get export stats for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve export statistics"
        )


# Admin endpoints (require appropriate permissions)
@router.get("/admin/queue-stats", response_model=Dict[str, any])
async def get_export_queue_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get export queue statistics (admin only).
    
    Returns information about the background job queues
    and overall system performance.
    """
    try:
        # Check admin permissions
        user_tier = getattr(current_user, 'tier', 'free')
        if user_tier not in ['admin', 'enterprise']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        from app.core.background_jobs import job_manager
        queue_stats = job_manager.get_queue_stats()
        
        return queue_stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get queue stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve queue statistics"
        )


# Error handlers for this router
@router.exception_handler(Exception)
async def export_exception_handler(request: Request, exc: Exception):
    """Handle export-specific exceptions."""
    logger.error(f"Export API error: {exc}", extra={"path": str(request.url)})
    
    return create_error_response(
        error_code="EXPORT_ERROR",
        message="An error occurred during export processing",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )