"""
Enhanced Export Engine for FinGood Financial Platform

This module provides a comprehensive export system that builds on the existing export service
with advanced features including:
- Multi-format exports (CSV, Excel, PDF, JSON)
- Background job processing with RQ
- Template-based PDF generation
- Large dataset streaming
- Security and audit compliance
- Progress tracking with WebSocket updates
"""

import asyncio
import hashlib
import json
import logging
import os
import tempfile
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from jinja2 import Template
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.platypus.tableofcontents import TableOfContents
from sqlalchemy.orm import Session
from weasyprint import HTML, CSS

from app.core.audit_logger import security_audit_logger
from app.core.background_jobs import job_manager, JobType, JobState, JobProgress, JobResult, JobPriority
from app.core.config import settings
from app.core.database import get_db
from app.core.security_utils import input_sanitizer
from app.models.export_job import ExportJob, ExportTemplate
from app.models.transaction import Transaction, Category
from app.models.user import User
from app.schemas.export import (
    ExportFormat, ExportStatus, ExportFilterParams, ExportColumnsConfig,
    ExportOptionsConfig, ExportSummary, ExportProgress, ExportJobResponse
)
from app.services.export_service import ExportDataProcessor, ExportSecurityValidator

logger = logging.getLogger(__name__)


class ExportFormatters:
    """Enhanced format-specific exporters with PDF support and advanced features."""
    
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self.security_validator = ExportSecurityValidator()
    
    async def generate_pdf_export(
        self,
        transactions: List[Transaction],
        columns_config: ExportColumnsConfig,
        options_config: ExportOptionsConfig,
        output_path: str,
        template_config: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, int]:
        """Generate professional PDF export with template support."""
        processor = ExportDataProcessor(columns_config, options_config)
        
        # Get user information for PDF header
        user = self.db.query(User).filter(User.id == self.user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Process transactions data
        records = []
        for transaction in transactions:
            record = processor.process_transaction_record(transaction)
            records.append(record)
            
            # Yield control for large datasets
            if len(records) % 1000 == 0:
                await asyncio.sleep(0)
        
        if not records:
            raise ValueError("No transactions to export")
        
        # Use template-based PDF generation if template provided
        if template_config and template_config.get('use_html_template', False):
            return await self._generate_html_pdf(
                records, user, template_config, output_path, options_config
            )
        else:
            return await self._generate_reportlab_pdf(
                records, user, output_path, options_config
            )
    
    async def _generate_html_pdf(
        self,
        records: List[Dict[str, Any]],
        user: User,
        template_config: Dict[str, Any],
        output_path: str,
        options_config: ExportOptionsConfig
    ) -> Tuple[str, int]:
        """Generate PDF using HTML template with weasyprint."""
        
        # Default HTML template
        default_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{{ title }}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }
                .company-name { font-size: 24px; font-weight: bold; color: #2c3e50; }
                .report-title { font-size: 18px; color: #34495e; margin-top: 10px; }
                .meta-info { font-size: 12px; color: #7f8c8d; margin-top: 10px; }
                .summary { background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 5px; }
                .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
                .summary-item { text-align: center; }
                .summary-label { font-size: 12px; color: #6c757d; text-transform: uppercase; }
                .summary-value { font-size: 18px; font-weight: bold; color: #2c3e50; }
                .transactions-table { width: 100%; border-collapse: collapse; font-size: 10px; }
                .transactions-table th { background: #2c3e50; color: white; padding: 8px; text-align: left; }
                .transactions-table td { padding: 6px 8px; border-bottom: 1px solid #dee2e6; }
                .transactions-table tr:nth-child(even) { background: #f8f9fa; }
                .amount-positive { color: #28a745; }
                .amount-negative { color: #dc3545; }
                .footer { margin-top: 40px; font-size: 10px; color: #6c757d; text-align: center; }
                @media print { body { margin: 20px; } }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="company-name">{{ company_name }}</div>
                <div class="report-title">{{ title }}</div>
                <div class="meta-info">
                    Generated on {{ export_date }} | {{ total_records }} transactions
                    {% if date_range %}| Period: {{ date_range.from_date }} to {{ date_range.to_date }}{% endif %}
                </div>
            </div>
            
            {% if summary %}
            <div class="summary">
                <h3>Summary</h3>
                <div class="summary-grid">
                    <div class="summary-item">
                        <div class="summary-label">Total Transactions</div>
                        <div class="summary-value">{{ summary.total_records }}</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-label">Total Income</div>
                        <div class="summary-value amount-positive">${{ "%.2f"|format(summary.total_income) }}</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-label">Total Expenses</div>
                        <div class="summary-value amount-negative">${{ "%.2f"|format(summary.total_expenses) }}</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-label">Net Amount</div>
                        <div class="summary-value">${{ "%.2f"|format(summary.net_amount) }}</div>
                    </div>
                </div>
            </div>
            {% endif %}
            
            <h3>Transaction Details</h3>
            <table class="transactions-table">
                <thead>
                    <tr>
                        {% for header in headers %}
                        <th>{{ header }}</th>
                        {% endfor %}
                    </tr>
                </thead>
                <tbody>
                    {% for record in records %}
                    <tr>
                        {% for header in headers %}
                        <td class="{% if header == 'Amount' and record[header]|float < 0 %}amount-negative{% elif header == 'Amount' and record[header]|float > 0 %}amount-positive{% endif %}">
                            {{ record[header] or '' }}
                        </td>
                        {% endfor %}
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            
            <div class="footer">
                <p>This report was generated by FinGood Financial Intelligence Platform</p>
                <p>Report ID: {{ report_id }} | User: {{ user_email }}</p>
            </div>
        </body>
        </html>
        """
        
        # Use custom template if provided, otherwise use default
        template_html = template_config.get('html_template', default_template)
        
        # Calculate summary statistics
        total_income = sum(float(r['Amount'].replace('$', '').replace(',', '')) 
                          for r in records if r.get('Amount') and float(r['Amount'].replace('$', '').replace(',', '')) > 0)
        total_expenses = abs(sum(float(r['Amount'].replace('$', '').replace(',', '')) 
                               for r in records if r.get('Amount') and float(r['Amount'].replace('$', '').replace(',', '')) < 0))
        net_amount = total_income - total_expenses
        
        # Prepare template context
        context = {
            'title': template_config.get('title', 'Transaction Report'),
            'company_name': template_config.get('company_name', 'FinGood Financial Intelligence'),
            'export_date': datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC'),
            'total_records': len(records),
            'records': records,
            'headers': list(records[0].keys()) if records else [],
            'user_email': user.email,
            'report_id': str(uuid.uuid4()),
            'summary': {
                'total_records': len(records),
                'total_income': total_income,
                'total_expenses': total_expenses,
                'net_amount': net_amount
            } if template_config.get('include_summary', True) else None,
            'date_range': template_config.get('date_range')
        }
        
        # Render template
        template = Template(template_html)
        html_content = template.render(**context)
        
        # Generate PDF with weasyprint
        html_doc = HTML(string=html_content)
        css_styles = CSS(string="""
            @page { 
                margin: 1in; 
                @top-right { content: "Page " counter(page) " of " counter(pages); }
            }
        """)
        
        html_doc.write_pdf(output_path, stylesheets=[css_styles])
        
        file_size = os.path.getsize(output_path)
        return output_path, file_size
    
    async def _generate_reportlab_pdf(
        self,
        records: List[Dict[str, Any]],
        user: User,
        output_path: str,
        options_config: ExportOptionsConfig
    ) -> Tuple[str, int]:
        """Generate PDF using ReportLab for high-performance generation."""
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build story (content elements)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.HexColor('#2c3e50')
        )
        story.append(Paragraph("FinGood Transaction Report", title_style))
        
        # Report metadata
        meta_data = [
            f"Generated: {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}",
            f"User: {user.email}",
            f"Total Transactions: {len(records):,}",
            f"Report ID: {str(uuid.uuid4())}"
        ]
        
        for meta in meta_data:
            story.append(Paragraph(meta, styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # Summary statistics
        if records:
            amounts = []
            for record in records:
                amount_str = record.get('Amount', '0')
                try:
                    # Remove currency symbols and parse amount
                    clean_amount = amount_str.replace('$', '').replace(',', '')
                    amounts.append(float(clean_amount))
                except (ValueError, AttributeError):
                    amounts.append(0.0)
            
            total_income = sum(a for a in amounts if a > 0)
            total_expenses = abs(sum(a for a in amounts if a < 0))
            net_amount = total_income - total_expenses
            
            summary_data = [
                ['Summary', ''],
                ['Total Income', f'${total_income:,.2f}'],
                ['Total Expenses', f'${total_expenses:,.2f}'],
                ['Net Amount', f'${net_amount:,.2f}'],
                ['Average Transaction', f'${sum(amounts)/len(amounts):,.2f}' if amounts else '$0.00']
            ]
            
            summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 30))
        
        # Transaction table
        if records:
            headers = list(records[0].keys())
            
            # Limit columns for PDF readability
            max_columns = 6
            if len(headers) > max_columns:
                headers = headers[:max_columns]
            
            # Create table data
            table_data = [headers]
            
            for record in records:
                row = [str(record.get(header, ''))[:30] for header in headers]  # Truncate long values
                table_data.append(row)
                
                # Limit rows for performance (can be configured)
                if len(table_data) > 1000:  # Max 1000 rows
                    table_data.append(['... (additional transactions truncated for PDF size)'] + [''] * (len(headers) - 1))
                    break
            
            # Calculate column widths
            col_width = (letter[0] - 144) / len(headers)  # Available width divided by columns
            col_widths = [col_width] * len(headers)
            
            transaction_table = Table(table_data, colWidths=col_widths)
            transaction_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            
            story.append(Paragraph("Transaction Details", styles['Heading2']))
            story.append(Spacer(1, 12))
            story.append(transaction_table)
        
        # Build PDF
        doc.build(story)
        
        file_size = os.path.getsize(output_path)
        return output_path, file_size


class EnhancedExportEngine:
    """
    Enhanced Export Engine for FinGood platform with advanced features.
    
    Features:
    - Multi-format exports (CSV, Excel, PDF, JSON)
    - Background job processing
    - Template system for PDF reports
    - Large dataset streaming
    - Progress tracking
    - Export history management
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.exports_dir = Path(settings.UPLOAD_DIR) / "exports"
        self.exports_dir.mkdir(exist_ok=True)
        self.templates_dir = self.exports_dir / "templates"
        self.templates_dir.mkdir(exist_ok=True)
        
    async def create_export_job(
        self,
        user_id: int,
        export_format: ExportFormat,
        filters: Optional[ExportFilterParams] = None,
        columns_config: Optional[ExportColumnsConfig] = None,
        options_config: Optional[ExportOptionsConfig] = None,
        export_name: Optional[str] = None,
        template_id: Optional[str] = None,
        priority: JobPriority = JobPriority.NORMAL
    ) -> ExportJobResponse:
        """Create and queue an export job."""
        
        # Validate user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Set defaults
        if columns_config is None:
            columns_config = ExportColumnsConfig()
        if options_config is None:
            options_config = ExportOptionsConfig()
        
        # Generate job ID and create database record
        job_id = str(uuid.uuid4())
        
        # Create export job record
        export_job = ExportJob(
            job_id=job_id,
            user_id=user_id,
            export_format=export_format.value,
            export_type="transactions",
            export_name=export_name,
            status="pending",
            filters=filters.dict() if filters else None,
            columns_config=columns_config.dict(),
            options_config=options_config.dict(),
            expires_at=datetime.utcnow() + timedelta(hours=24),
            client_ip="127.0.0.1",  # Will be set by API endpoint
            user_agent="FinGood Export Engine"
        )
        
        # Estimate record count
        from app.services.export_service import ExportGenerator
        generator = ExportGenerator(self.db, user_id)
        query = generator.build_query(filters)
        estimated_records = query.count()
        
        export_job.estimated_records = estimated_records
        
        # Validate export size
        user_tier = getattr(user, 'tier', 'free')
        ExportSecurityValidator.validate_export_size(estimated_records, user_tier)
        
        # Save to database
        self.db.add(export_job)
        self.db.commit()
        self.db.refresh(export_job)
        
        # Queue background job
        try:
            await self._queue_export_job(export_job, template_id, priority)
        except Exception as e:
            # Mark job as failed if queueing fails
            export_job.mark_failed(f"Failed to queue job: {str(e)}")
            self.db.commit()
            raise
        
        # Log export request
        security_audit_logger.info(
            "Export job created",
            extra={
                "job_id": job_id,
                "user_id": user_id,
                "export_format": export_format.value,
                "estimated_records": estimated_records,
                "template_id": template_id
            }
        )
        
        return ExportJobResponse(
            job_id=job_id,
            status=ExportStatus.PENDING,
            estimated_records=estimated_records,
            estimated_completion_time=datetime.utcnow() + timedelta(minutes=5),
            created_at=export_job.created_at,
            message="Export job queued successfully"
        )
    
    async def _queue_export_job(
        self,
        export_job: ExportJob,
        template_id: Optional[str] = None,
        priority: JobPriority = JobPriority.NORMAL
    ) -> None:
        """Queue the export job for background processing."""
        
        job_data = {
            'export_job_id': export_job.id,
            'job_id': export_job.job_id,
            'user_id': export_job.user_id,
            'export_format': export_job.export_format,
            'filters': export_job.filters,
            'columns_config': export_job.columns_config,
            'options_config': export_job.options_config,
            'export_name': export_job.export_name,
            'template_id': template_id,
            'created_at': export_job.created_at.isoformat()
        }
        
        # Use job manager to queue the job
        queue = job_manager.queues[priority]
        rq_job = queue.enqueue(
            process_export_job,
            job_data,
            job_id=export_job.job_id,
            job_timeout='60m',  # 1 hour timeout for large exports
            retry_count=2,
            meta={'user_id': export_job.user_id, 'export_format': export_job.export_format}
        )
        
        logger.info(f"Queued export job {export_job.job_id} with priority {priority.value}")
    
    def get_export_progress(self, job_id: str, user_id: int) -> Optional[ExportProgress]:
        """Get export job progress."""
        export_job = self.db.query(ExportJob).filter(
            ExportJob.job_id == job_id,
            ExportJob.user_id == user_id
        ).first()
        
        if not export_job:
            return None
        
        return ExportProgress(
            job_id=job_id,
            status=ExportStatus(export_job.status),
            progress_percentage=float(export_job.progress_percentage),
            records_processed=export_job.records_processed,
            total_records=export_job.total_records or export_job.estimated_records,
            current_operation=export_job.current_operation or "Processing...",
            started_at=export_job.started_at or export_job.created_at,
            estimated_completion=export_job.estimated_completion_time,
            error_message=export_job.error_message
        )
    
    def get_export_download_info(self, job_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """Get download information for completed export."""
        export_job = self.db.query(ExportJob).filter(
            ExportJob.job_id == job_id,
            ExportJob.user_id == user_id,
            ExportJob.status == "completed"
        ).first()
        
        if not export_job or not export_job.is_downloadable:
            return None
        
        # Generate secure download token if needed
        if not export_job.download_token:
            export_job.download_token = hashlib.sha256(
                f"{job_id}{user_id}{export_job.created_at}".encode()
            ).hexdigest()
            self.db.commit()
        
        return {
            'download_url': f"/api/v1/export/download/{export_job.download_token}",
            'file_name': export_job.file_name,
            'file_size': export_job.file_size_bytes,
            'expires_at': export_job.expires_at,
            'download_count': export_job.download_count
        }
    
    def get_user_export_history(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's export history."""
        export_jobs = self.db.query(ExportJob).filter(
            ExportJob.user_id == user_id
        ).order_by(
            ExportJob.created_at.desc()
        ).limit(limit).all()
        
        history = []
        for job in export_jobs:
            history.append({
                'job_id': job.job_id,
                'export_name': job.export_name,
                'export_format': job.export_format,
                'status': job.status,
                'created_at': job.created_at,
                'completed_at': job.completed_at,
                'expires_at': job.expires_at,
                'total_records': job.total_records or job.estimated_records,
                'file_size_bytes': job.file_size_bytes,
                'download_count': job.download_count,
                'is_downloadable': job.is_downloadable,
                'error_message': job.error_message
            })
        
        return history
    
    async def cleanup_expired_exports(self):
        """Clean up expired export files and database records."""
        expired_jobs = self.db.query(ExportJob).filter(
            ExportJob.expires_at < datetime.utcnow(),
            ExportJob.auto_cleanup == True
        ).all()
        
        cleaned_count = 0
        for job in expired_jobs:
            try:
                # Remove file if exists
                if job.file_path and os.path.exists(job.file_path):
                    os.remove(job.file_path)
                    logger.info(f"Removed expired export file: {job.file_path}")
                
                # Remove database record
                self.db.delete(job)
                cleaned_count += 1
                
            except Exception as e:
                logger.error(f"Failed to cleanup export job {job.job_id}: {e}")
        
        if cleaned_count > 0:
            self.db.commit()
            logger.info(f"Cleaned up {cleaned_count} expired export jobs")
        
        return cleaned_count


async def process_export_job(job_data: Dict[str, Any]) -> JobResult:
    """Background worker function for processing export jobs."""
    start_time = datetime.utcnow()
    job_id = job_data['job_id']
    export_job_id = job_data['export_job_id']
    user_id = job_data['user_id']
    
    logger.info(f"Starting export job {job_id} for user {user_id}")
    
    db = next(get_db())
    try:
        # Get export job from database
        export_job = db.query(ExportJob).filter(ExportJob.id == export_job_id).first()
        if not export_job:
            raise ValueError("Export job not found")
        
        # Mark job as started
        export_job.mark_started()
        db.commit()
        
        # Create formatters
        formatters = ExportFormatters(db, user_id)
        
        # Build query and get transactions
        from app.services.export_service import ExportGenerator
        generator = ExportGenerator(db, user_id)
        
        filters = ExportFilterParams(**job_data['filters']) if job_data['filters'] else None
        query = generator.build_query(filters)
        transactions = query.all()
        
        export_job.total_records = len(transactions)
        export_job.update_progress(20.0, "Loading transaction data")
        db.commit()
        
        # Prepare configurations
        columns_config = ExportColumnsConfig(**job_data['columns_config'])
        options_config = ExportOptionsConfig(**job_data['options_config'])
        
        # Generate filename
        export_name = job_data['export_name'] or f"transactions_export_{datetime.utcnow().strftime('%Y%m%d')}"
        filename = ExportSecurityValidator.sanitize_filename(f"{export_name}.{job_data['export_format']}")
        file_path = Path(settings.UPLOAD_DIR) / "exports" / filename
        
        export_job.update_progress(40.0, "Generating export file")
        db.commit()
        
        # Generate export based on format
        if job_data['export_format'] == 'csv':
            output_path, file_size = await generator.generate_csv_export(
                transactions, columns_config, options_config, str(file_path)
            )
        elif job_data['export_format'] == 'excel':
            output_path, file_size = await generator.generate_excel_export(
                transactions, columns_config, options_config, str(file_path.with_suffix('.xlsx'))
            )
        elif job_data['export_format'] == 'json':
            output_path, file_size = await generator.generate_json_export(
                transactions, columns_config, options_config, str(file_path)
            )
        elif job_data['export_format'] == 'pdf':
            # Get template config if template_id provided
            template_config = None
            if job_data.get('template_id'):
                template = db.query(ExportTemplate).filter(
                    ExportTemplate.template_id == job_data['template_id'],
                    ExportTemplate.user_id == user_id
                ).first()
                if template:
                    template_config = template.template_config
            
            output_path, file_size = await formatters.generate_pdf_export(
                transactions, columns_config, options_config, str(file_path.with_suffix('.pdf')), template_config
            )
        else:
            raise ValueError(f"Unsupported export format: {job_data['export_format']}")
        
        export_job.update_progress(80.0, "Finalizing export")
        db.commit()
        
        # Generate file hash for integrity
        with open(output_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        
        # Generate download URL and token
        download_token = hashlib.sha256(
            f"{job_id}{user_id}{datetime.utcnow()}".encode()
        ).hexdigest()
        download_url = f"/api/v1/export/download/{download_token}"
        
        # Mark job as completed
        export_job.mark_completed(
            file_path=output_path,
            file_size=file_size,
            file_hash=file_hash,
            download_url=download_url,
            download_token=download_token
        )
        export_job.file_name = os.path.basename(output_path)
        db.commit()
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Log success
        security_audit_logger.info(
            "Export job completed successfully",
            extra={
                "job_id": job_id,
                "user_id": user_id,
                "export_format": job_data['export_format'],
                "records_exported": len(transactions),
                "file_size": file_size,
                "processing_time": processing_time
            }
        )
        
        logger.info(f"Export job {job_id} completed successfully: {len(transactions)} records exported")
        
        return JobResult(
            success=True,
            data={
                'export_job_id': export_job_id,
                'file_path': output_path,
                'file_size': file_size,
                'records_exported': len(transactions),
                'download_url': download_url,
                'download_token': download_token
            },
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Export job {job_id} failed: {e}")
        
        # Mark job as failed
        try:
            export_job = db.query(ExportJob).filter(ExportJob.id == export_job_id).first()
            if export_job:
                export_job.mark_failed(str(e))
                db.commit()
        except Exception as update_error:
            logger.error(f"Failed to update job status: {update_error}")
        
        return JobResult(
            success=False,
            error_message=str(e),
            error_code="EXPORT_PROCESSING_ERROR",
            correlation_id=job_id,
            processing_time=(datetime.utcnow() - start_time).total_seconds()
        )
    
    finally:
        db.close()