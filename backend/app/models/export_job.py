from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Index, ForeignKey, JSON, BigInteger, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class ExportJob(Base):
    """
    Model to track export job lifecycle and metadata.
    Supports large-scale financial data exports with comprehensive audit trail.
    """
    __tablename__ = "export_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(255), unique=True, index=True, nullable=False)  # UUID for job tracking
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Export configuration
    export_format = Column(String(20), nullable=False)  # csv, excel, pdf, json
    export_type = Column(String(50), nullable=False, default="transactions")  # transactions, reports
    export_name = Column(String(200), nullable=True)  # User-defined export name
    
    # Status tracking
    status = Column(String(20), nullable=False, default="pending")  # pending, processing, completed, failed, cancelled
    progress_percentage = Column(Numeric(5, 2), default=0.00)  # 0.00 to 100.00
    current_operation = Column(String(200), nullable=True)  # Current processing operation
    
    # Filter and configuration JSON
    filters = Column(JSON, nullable=True)  # ExportFilterParams as JSON
    columns_config = Column(JSON, nullable=True)  # ExportColumnsConfig as JSON
    options_config = Column(JSON, nullable=True)  # ExportOptionsConfig as JSON
    
    # Processing metrics
    estimated_records = Column(Integer, default=0)
    records_processed = Column(Integer, default=0)
    total_records = Column(Integer, default=0)
    processing_time_seconds = Column(Numeric(10, 3), nullable=True)  # Actual processing time
    
    # File information
    file_path = Column(String(500), nullable=True)  # Server file path
    file_name = Column(String(255), nullable=True)  # Original filename
    file_size_bytes = Column(BigInteger, nullable=True)  # File size in bytes
    file_hash = Column(String(64), nullable=True)  # SHA256 hash for integrity
    compressed = Column(Boolean, default=False)  # Whether file is compressed
    compression_ratio = Column(Numeric(5, 2), nullable=True)  # Compression ratio if compressed
    
    # Download tracking
    download_url = Column(String(500), nullable=True)  # Temporary download URL
    download_token = Column(String(255), nullable=True, index=True)  # Secure download token
    download_count = Column(Integer, default=0)  # Number of downloads
    last_downloaded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Expiry management
    expires_at = Column(DateTime(timezone=True), nullable=False)  # When download expires
    auto_cleanup = Column(Boolean, default=True)  # Automatically delete expired files
    
    # Audit and security
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)  # When processing started
    completed_at = Column(DateTime(timezone=True), nullable=True)  # When processing completed
    cancelled_at = Column(DateTime(timezone=True), nullable=True)  # When job was cancelled
    
    # Error tracking
    error_message = Column(Text, nullable=True)  # User-friendly error message
    error_details = Column(Text, nullable=True)  # Technical error details (for debugging)
    retry_count = Column(Integer, default=0)  # Number of retry attempts
    max_retries = Column(Integer, default=3)  # Maximum retry attempts
    
    # Client information for audit trail
    client_ip = Column(String(45), nullable=True)  # IPv4/IPv6
    user_agent = Column(Text, nullable=True)  # Browser/client info
    
    # Relationships
    user = relationship("User", backref="export_jobs")
    
    # Composite indexes for efficient queries
    __table_args__ = (
        Index('idx_export_jobs_user_status', 'user_id', 'status'),
        Index('idx_export_jobs_user_created', 'user_id', 'created_at'),
        Index('idx_export_jobs_status_created', 'status', 'created_at'),
        Index('idx_export_jobs_cleanup', 'expires_at', 'auto_cleanup'),
        Index('idx_export_jobs_download', 'download_token', 'expires_at'),
        Index('idx_export_jobs_processing', 'status', 'started_at'),
    )
    
    def __repr__(self):
        return f"<ExportJob(job_id='{self.job_id}', user_id={self.user_id}, status='{self.status}')>"
    
    @property
    def is_expired(self) -> bool:
        """Check if the export has expired."""
        return datetime.utcnow() > self.expires_at.replace(tzinfo=None)
    
    @property
    def is_downloadable(self) -> bool:
        """Check if the export is ready for download."""
        return (
            self.status == "completed" and 
            self.file_path is not None and 
            self.download_url is not None and 
            not self.is_expired
        )
    
    @property
    def is_processing(self) -> bool:
        """Check if the export is currently being processed."""
        return self.status in ["pending", "processing"]
    
    @property
    def is_terminal_state(self) -> bool:
        """Check if the export is in a terminal state (completed, failed, or cancelled)."""
        return self.status in ["completed", "failed", "cancelled"]
    
    @property
    def processing_duration(self) -> Optional[timedelta]:
        """Get the processing duration if available."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        elif self.started_at:
            return datetime.utcnow().replace(tzinfo=self.started_at.tzinfo) - self.started_at
        return None
    
    @property
    def estimated_completion_time(self) -> Optional[datetime]:
        """Estimate completion time based on current progress."""
        if self.status != "processing" or not self.started_at or self.progress_percentage <= 0:
            return None
        
        elapsed = datetime.utcnow().replace(tzinfo=self.started_at.tzinfo) - self.started_at
        estimated_total = elapsed / (self.progress_percentage / 100.0)
        return self.started_at + estimated_total
    
    def update_progress(self, percentage: float, operation: str = None, records_processed: int = None):
        """Update export progress."""
        self.progress_percentage = max(0.0, min(100.0, percentage))
        
        if operation:
            self.current_operation = operation
        
        if records_processed is not None:
            self.records_processed = records_processed
    
    def mark_started(self):
        """Mark the export as started."""
        self.status = "processing"
        self.started_at = func.now()
        self.progress_percentage = 0.0
    
    def mark_completed(self, file_path: str, file_size: int, file_hash: str, download_url: str, download_token: str):
        """Mark the export as completed."""
        self.status = "completed"
        self.completed_at = func.now()
        self.progress_percentage = 100.0
        self.file_path = file_path
        self.file_size_bytes = file_size
        self.file_hash = file_hash
        self.download_url = download_url
        self.download_token = download_token
        self.current_operation = "Completed"
    
    def mark_failed(self, error_message: str, error_details: str = None):
        """Mark the export as failed."""
        self.status = "failed"
        self.completed_at = func.now()
        self.error_message = error_message
        self.error_details = error_details
        self.current_operation = "Failed"
    
    def mark_cancelled(self):
        """Mark the export as cancelled."""
        self.status = "cancelled"
        self.cancelled_at = func.now()
        self.current_operation = "Cancelled"
    
    def increment_download_count(self):
        """Increment download count and update last downloaded timestamp."""
        self.download_count += 1
        self.last_downloaded_at = func.now()
    
    def can_retry(self) -> bool:
        """Check if the job can be retried."""
        return self.status == "failed" and self.retry_count < self.max_retries
    
    def increment_retry(self):
        """Increment retry count and reset for retry."""
        if self.can_retry():
            self.retry_count += 1
            self.status = "pending"
            self.error_message = None
            self.error_details = None
            self.progress_percentage = 0.0
            self.current_operation = "Retrying..."


class ExportTemplate(Base):
    """
    Model for storing export templates (especially for PDF generation).
    Allows users to create reusable export configurations.
    """
    __tablename__ = "export_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String(255), unique=True, index=True, nullable=False)  # UUID
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Template metadata
    name = Column(String(200), nullable=False)  # User-defined template name
    description = Column(Text, nullable=True)  # Template description
    template_type = Column(String(50), nullable=False, default="transaction_report")  # Type of template
    
    # Template configuration
    template_config = Column(JSON, nullable=False)  # Template configuration (filters, columns, options)
    is_public = Column(Boolean, default=False)  # Whether template can be used by other users
    is_system = Column(Boolean, default=False)  # System-provided template
    
    # Usage tracking
    usage_count = Column(Integer, default=0)  # Number of times used
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="export_templates")
    
    # Indexes
    __table_args__ = (
        Index('idx_export_templates_user', 'user_id', 'name'),
        Index('idx_export_templates_public', 'is_public', 'template_type'),
        Index('idx_export_templates_system', 'is_system', 'template_type'),
        Index('idx_export_templates_usage', 'usage_count', 'last_used_at'),
    )
    
    def __repr__(self):
        return f"<ExportTemplate(template_id='{self.template_id}', name='{self.name}')>"
    
    def increment_usage(self):
        """Increment usage count and update last used timestamp."""
        self.usage_count += 1
        self.last_used_at = func.now()