"""
Report schemas for FinGood Financial Platform

This module defines Pydantic schemas for report generation, templates, and scheduling.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator

class ReportFormat(str, Enum):
    """Supported report output formats"""
    PDF = "pdf"
    EXCEL = "excel"
    HTML = "html"
    CSV = "csv"
    JSON = "json"

class ReportStatus(str, Enum):
    """Report job status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ReportType(str, Enum):
    """Types of reports"""
    FINANCIAL_SUMMARY = "financial_summary"
    SPENDING_ANALYSIS = "spending_analysis"
    CATEGORY_BREAKDOWN = "category_breakdown"
    VENDOR_ANALYSIS = "vendor_analysis"
    CASH_FLOW = "cash_flow"
    CUSTOM = "custom"

class ScheduleFrequency(str, Enum):
    """Report scheduling frequencies"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class ReportRequest(BaseModel):
    """Request model for creating a new report"""
    report_name: Optional[str] = Field(None, description="Name for the report")
    report_type: ReportType = Field(..., description="Type of report to generate")
    template_id: Optional[str] = Field(None, description="Template ID to use")
    output_format: ReportFormat = Field(ReportFormat.PDF, description="Output format")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Report parameters")
    schedule: Optional[Dict[str, Any]] = Field(None, description="Scheduling options")
    
    @validator('report_name')
    def validate_report_name(cls, v):
        if v is not None and len(v) > 100:
            raise ValueError('Report name must be 100 characters or less')
        return v
    
    @validator('parameters')
    def validate_parameters(cls, v):
        if not isinstance(v, dict):
            raise ValueError('Parameters must be a dictionary')
        return v

class ReportJobResponse(BaseModel):
    """Response model for report job creation"""
    job_id: str = Field(..., description="Unique job identifier")
    status: ReportStatus = Field(..., description="Current job status")
    message: str = Field(..., description="Status message")
    created_at: Optional[datetime] = Field(None, description="Job creation timestamp")

class ReportProgress(BaseModel):
    """Model for report generation progress"""
    job_id: str = Field(..., description="Job identifier")
    status: ReportStatus = Field(..., description="Current status")
    progress_percentage: float = Field(..., ge=0, le=100, description="Progress percentage")
    current_step: str = Field(..., description="Current processing step")
    message: str = Field(..., description="Progress message")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    total_records: Optional[int] = Field(None, description="Total records to process")
    processed_records: Optional[int] = Field(None, description="Records processed so far")

class ReportTemplate(BaseModel):
    """Model for report templates"""
    template_id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    report_type: ReportType = Field(..., description="Report type this template is for")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Default parameters")
    is_system: bool = Field(False, description="Whether this is a system template")
    created_by: Optional[str] = Field(None, description="User who created the template")
    created_at: datetime = Field(..., description="Template creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    version: str = Field("1.0", description="Template version")

class ReportSchedule(BaseModel):
    """Model for report scheduling"""
    report_type: ReportType = Field(..., description="Type of report to schedule")
    frequency: ScheduleFrequency = Field(..., description="How often to generate the report")
    start_date: datetime = Field(..., description="When to start scheduling")
    end_date: Optional[datetime] = Field(None, description="When to stop scheduling")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Report parameters")
    output_format: ReportFormat = Field(ReportFormat.PDF, description="Output format")
    template_id: Optional[str] = Field(None, description="Template to use")
    email_recipients: Optional[List[str]] = Field(None, description="Email recipients")
    active: bool = Field(True, description="Whether the schedule is active")
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v is not None and 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v
    
    @validator('email_recipients')
    def validate_email_recipients(cls, v):
        if v is not None:
            if len(v) > 10:
                raise ValueError('Maximum 10 email recipients allowed')
            # Basic email validation
            import re
            email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
            for email in v:
                if not email_pattern.match(email):
                    raise ValueError(f'Invalid email format: {email}')
        return v

class ReportDistribution(BaseModel):
    """Model for report distribution"""
    report_id: str = Field(..., description="Report identifier")
    distribution_type: str = Field(..., description="Type of distribution (email, download, etc.)")
    recipients: List[str] = Field(default_factory=list, description="Distribution recipients")
    sent_at: Optional[datetime] = Field(None, description="When the report was sent")
    status: str = Field("pending", description="Distribution status")
    error_message: Optional[str] = Field(None, description="Error message if failed")

class ReportHistoryEntry(BaseModel):
    """Model for report history entries"""
    job_id: str = Field(..., description="Job identifier")
    report_name: str = Field(..., description="Report name")
    report_type: ReportType = Field(..., description="Report type")
    output_format: ReportFormat = Field(..., description="Output format")
    status: ReportStatus = Field(..., description="Job status")
    created_at: datetime = Field(..., description="Creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    file_size_bytes: Optional[int] = Field(None, description="Generated file size")
    download_count: Optional[int] = Field(0, description="Number of downloads")
    error_message: Optional[str] = Field(None, description="Error message if failed")

class ReportStats(BaseModel):
    """Model for report statistics"""
    total_reports_generated: int = Field(..., description="Total reports generated")
    total_reports_failed: int = Field(..., description="Total reports that failed")
    average_generation_time: float = Field(..., description="Average generation time in seconds")
    most_popular_format: ReportFormat = Field(..., description="Most popular output format")
    most_popular_type: ReportType = Field(..., description="Most popular report type")
    total_file_size_generated: int = Field(..., description="Total file size generated in bytes")
    active_schedules: int = Field(..., description="Number of active scheduled reports")
