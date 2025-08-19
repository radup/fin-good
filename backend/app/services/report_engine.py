"""
Report Engine Service for FinGood Financial Platform

This module provides the core report generation functionality with template support,
scheduling, and multiple output formats.
"""

import logging
import os
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.core.config import settings
from app.core.background_jobs import JobPriority
from app.models.user import User
from app.models.transaction import Transaction
from app.schemas.report import (
    ReportRequest, ReportJobResponse, ReportProgress, ReportTemplate,
    ReportSchedule, ReportStatus, ReportFormat, ReportType
)

logger = logging.getLogger(__name__)

class ReportEngine:
    """
    Core report generation engine with template support and scheduling.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.reports_dir = Path(settings.REPORTS_DIR) if hasattr(settings, 'REPORTS_DIR') else Path("./reports")
        self.reports_dir.mkdir(exist_ok=True)
    
    async def create_report_job(self, job_data: Dict[str, Any]) -> str:
        """
        Create a new report generation job.
        
        Args:
            job_data: Dictionary containing job parameters
            
        Returns:
            str: Job ID for tracking
        """
        try:
            job_id = str(uuid.uuid4())
            
            # Store job metadata (in a real implementation, this would be in a database)
            job_metadata = {
                "job_id": job_id,
                "user_id": job_data["user_id"],
                "report_name": job_data["report_name"],
                "report_type": job_data["report_type"],
                "template_id": job_data.get("template_id"),
                "output_format": job_data["output_format"],
                "parameters": job_data["parameters"],
                "status": ReportStatus.PENDING,
                "created_at": datetime.utcnow().isoformat(),
                "progress": 0,
                "current_step": "Initializing report generation"
            }
            
            # Store job metadata (simplified - in production, use database)
            job_file = self.reports_dir / f"{job_id}.json"
            with open(job_file, 'w') as f:
                json.dump(job_metadata, f, indent=2)
            
            # Queue background job for report generation
            from app.core.background_jobs import BackgroundJobManager
            job_manager = BackgroundJobManager()
            
            await job_manager.queue_job(
                "generate_report",
                job_id=job_id,
                priority=JobPriority.NORMAL,
                **job_data
            )
            
            logger.info(f"Created report job {job_id} for user {job_data['user_id']}")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to create report job: {e}")
            raise
    
    async def get_user_templates(self, user_id: int) -> List[ReportTemplate]:
        """
        Get available report templates for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List[ReportTemplate]: Available templates
        """
        try:
            # System templates (available to all users)
            system_templates = [
                ReportTemplate(
                    template_id="financial_summary_default",
                    name="Financial Summary",
                    description="Standard financial summary report",
                    report_type=ReportType.FINANCIAL_SUMMARY,
                    parameters={
                        "include_charts": True,
                        "include_comparisons": True,
                        "date_range": "last_30_days"
                    },
                    is_system=True,
                    created_at=datetime.utcnow(),
                    version="1.0"
                ),
                ReportTemplate(
                    template_id="spending_analysis_default",
                    name="Spending Analysis",
                    description="Detailed spending analysis report",
                    report_type=ReportType.SPENDING_ANALYSIS,
                    parameters={
                        "include_category_breakdown": True,
                        "include_vendor_analysis": True,
                        "include_trends": True
                    },
                    is_system=True,
                    created_at=datetime.utcnow(),
                    version="1.0"
                ),
                ReportTemplate(
                    template_id="category_breakdown_default",
                    name="Category Breakdown",
                    description="Spending breakdown by category",
                    report_type=ReportType.CATEGORY_BREAKDOWN,
                    parameters={
                        "include_percentages": True,
                        "include_charts": True,
                        "limit_categories": 10
                    },
                    is_system=True,
                    created_at=datetime.utcnow(),
                    version="1.0"
                )
            ]
            
            # User-specific templates (in a real implementation, these would come from database)
            user_templates = []
            
            # Combine system and user templates
            all_templates = system_templates + user_templates
            
            logger.info(f"Retrieved {len(all_templates)} templates for user {user_id}")
            return all_templates
            
        except Exception as e:
            logger.error(f"Failed to get templates for user {user_id}: {e}")
            raise
    
    async def get_report_progress(self, job_id: str, user_id: int) -> Optional[ReportProgress]:
        """
        Get the progress of a report generation job.
        
        Args:
            job_id: Job ID
            user_id: User ID for authorization
            
        Returns:
            Optional[ReportProgress]: Progress information
        """
        try:
            # Load job metadata
            job_file = self.reports_dir / f"{job_id}.json"
            if not job_file.exists():
                return None
            
            with open(job_file, 'r') as f:
                job_metadata = json.load(f)
            
            # Verify user ownership
            if job_metadata.get("user_id") != user_id:
                logger.warning(f"User {user_id} attempted to access job {job_id} owned by user {job_metadata.get('user_id')}")
                return None
            
            # Create progress response
            progress = ReportProgress(
                job_id=job_id,
                status=ReportStatus(job_metadata.get("status", "pending")),
                progress_percentage=job_metadata.get("progress", 0),
                current_step=job_metadata.get("current_step", "Unknown"),
                message=job_metadata.get("message", "Processing"),
                estimated_completion=job_metadata.get("estimated_completion"),
                total_records=job_metadata.get("total_records"),
                processed_records=job_metadata.get("processed_records")
            )
            
            return progress
            
        except Exception as e:
            logger.error(f"Failed to get progress for job {job_id}: {e}")
            return None
    
    async def get_report_file(self, download_token: str) -> Optional[str]:
        """
        Get the file path for a completed report using download token.
        
        Args:
            download_token: Secure download token
            
        Returns:
            Optional[str]: File path if found
        """
        try:
            # In a real implementation, this would validate the token and return the file path
            # For now, we'll use a simplified approach
            
            # Look for files with the token in the name
            for file_path in self.reports_dir.glob(f"*{download_token}*"):
                if file_path.is_file() and file_path.suffix in ['.pdf', '.xlsx', '.html', '.csv', '.json']:
                    return str(file_path)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get report file for token {download_token}: {e}")
            return None
    
    async def get_user_report_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """
        Get the user's report generation history.
        
        Args:
            user_id: User ID
            limit: Maximum number of records to return
            
        Returns:
            List[Dict]: Report history entries
        """
        try:
            # In a real implementation, this would query a database
            # For now, we'll return a simplified mock response
            
            history = []
            for i in range(min(limit, 5)):  # Mock data
                history.append({
                    "job_id": f"job_{i}_{user_id}",
                    "report_name": f"Report {i+1}",
                    "report_type": ReportType.FINANCIAL_SUMMARY,
                    "output_format": ReportFormat.PDF,
                    "status": ReportStatus.COMPLETED,
                    "created_at": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                    "completed_at": (datetime.utcnow() - timedelta(days=i, hours=1)).isoformat(),
                    "file_size_bytes": 1024 * (i + 1),
                    "download_count": i,
                    "error_message": None
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get report history for user {user_id}: {e}")
            return []
    
    async def schedule_report(self, user_id: int, schedule_data: Dict[str, Any]) -> str:
        """
        Schedule a recurring report.
        
        Args:
            user_id: User ID
            schedule_data: Scheduling parameters
            
        Returns:
            str: Schedule ID
        """
        try:
            schedule_id = str(uuid.uuid4())
            
            # Store schedule metadata
            schedule_metadata = {
                "schedule_id": schedule_id,
                "user_id": user_id,
                "report_type": schedule_data["report_type"],
                "frequency": schedule_data["frequency"],
                "start_date": schedule_data["start_date"],
                "end_date": schedule_data.get("end_date"),
                "parameters": schedule_data.get("parameters", {}),
                "output_format": schedule_data.get("output_format", ReportFormat.PDF),
                "template_id": schedule_data.get("template_id"),
                "email_recipients": schedule_data.get("email_recipients", []),
                "active": schedule_data.get("active", True),
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Store schedule metadata
            schedule_file = self.reports_dir / f"schedule_{schedule_id}.json"
            with open(schedule_file, 'w') as f:
                json.dump(schedule_metadata, f, indent=2)
            
            logger.info(f"Created report schedule {schedule_id} for user {user_id}")
            return schedule_id
            
        except Exception as e:
            logger.error(f"Failed to schedule report for user {user_id}: {e}")
            raise
    
    async def cancel_report_job(self, job_id: str, user_id: int) -> bool:
        """
        Cancel a pending or in-progress report job.
        
        Args:
            job_id: Job ID
            user_id: User ID for authorization
            
        Returns:
            bool: True if cancelled successfully
        """
        try:
            # Load job metadata
            job_file = self.reports_dir / f"{job_id}.json"
            if not job_file.exists():
                return False
            
            with open(job_file, 'r') as f:
                job_metadata = json.load(f)
            
            # Verify user ownership
            if job_metadata.get("user_id") != user_id:
                logger.warning(f"User {user_id} attempted to cancel job {job_id} owned by user {job_metadata.get('user_id')}")
                return False
            
            # Check if job can be cancelled
            current_status = job_metadata.get("status")
            if current_status not in [ReportStatus.PENDING, ReportStatus.PROCESSING]:
                logger.info(f"Job {job_id} cannot be cancelled (status: {current_status})")
                return False
            
            # Update job status
            job_metadata["status"] = ReportStatus.CANCELLED
            job_metadata["cancelled_at"] = datetime.utcnow().isoformat()
            job_metadata["message"] = "Job cancelled by user"
            
            # Save updated metadata
            with open(job_file, 'w') as f:
                json.dump(job_metadata, f, indent=2)
            
            # Cancel background job if it exists
            from app.core.background_jobs import BackgroundJobManager
            job_manager = BackgroundJobManager()
            await job_manager.cancel_job(job_id)
            
            logger.info(f"Cancelled report job {job_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel report job {job_id}: {e}")
            return False
    
    async def generate_report_content(self, report_type: ReportType, parameters: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """
        Generate the actual report content based on type and parameters.
        
        Args:
            report_type: Type of report to generate
            parameters: Report parameters
            user_id: User ID
            
        Returns:
            Dict[str, Any]: Report content
        """
        try:
            if report_type == ReportType.FINANCIAL_SUMMARY:
                return await self._generate_financial_summary(parameters, user_id)
            elif report_type == ReportType.SPENDING_ANALYSIS:
                return await self._generate_spending_analysis(parameters, user_id)
            elif report_type == ReportType.CATEGORY_BREAKDOWN:
                return await self._generate_category_breakdown(parameters, user_id)
            elif report_type == ReportType.VENDOR_ANALYSIS:
                return await self._generate_vendor_analysis(parameters, user_id)
            elif report_type == ReportType.CASH_FLOW:
                return await self._generate_cash_flow(parameters, user_id)
            else:
                raise ValueError(f"Unsupported report type: {report_type}")
                
        except Exception as e:
            logger.error(f"Failed to generate {report_type} report for user {user_id}: {e}")
            raise
    
    async def _generate_financial_summary(self, parameters: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Generate financial summary report."""
        # Get user's transaction data
        transactions = self.db.query(Transaction).filter(
            Transaction.user_id == user_id
        ).all()
        
        # Calculate summary metrics
        total_income = sum(t.amount for t in transactions if t.is_income)
        total_expenses = sum(abs(t.amount) for t in transactions if not t.is_income)
        net_income = total_income - total_expenses
        
        return {
            "report_type": "financial_summary",
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_income": float(total_income),
                "total_expenses": float(total_expenses),
                "net_income": float(net_income),
                "transaction_count": len(transactions)
            },
            "parameters": parameters
        }
    
    async def _generate_spending_analysis(self, parameters: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Generate spending analysis report."""
        # Get spending transactions
        expenses = self.db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False
        ).all()
        
        # Analyze spending patterns
        category_spending = {}
        for expense in expenses:
            category = expense.category or "Uncategorized"
            if category not in category_spending:
                category_spending[category] = 0
            category_spending[category] += abs(expense.amount)
        
        return {
            "report_type": "spending_analysis",
            "generated_at": datetime.utcnow().isoformat(),
            "spending_by_category": category_spending,
            "total_spending": sum(category_spending.values()),
            "parameters": parameters
        }
    
    async def _generate_category_breakdown(self, parameters: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Generate category breakdown report."""
        # Similar to spending analysis but focused on categories
        return await self._generate_spending_analysis(parameters, user_id)
    
    async def _generate_vendor_analysis(self, parameters: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Generate vendor analysis report."""
        # Get vendor spending data
        vendor_spending = {}
        expenses = self.db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False,
            Transaction.vendor.isnot(None)
        ).all()
        
        for expense in expenses:
            vendor = expense.vendor
            if vendor not in vendor_spending:
                vendor_spending[vendor] = {"total": 0, "count": 0}
            vendor_spending[vendor]["total"] += abs(expense.amount)
            vendor_spending[vendor]["count"] += 1
        
        return {
            "report_type": "vendor_analysis",
            "generated_at": datetime.utcnow().isoformat(),
            "vendor_spending": vendor_spending,
            "parameters": parameters
        }
    
    async def _generate_cash_flow(self, parameters: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Generate cash flow report."""
        # Get transactions with dates
        transactions = self.db.query(Transaction).filter(
            Transaction.user_id == user_id
        ).order_by(Transaction.date).all()
        
        # Group by month
        monthly_flow = {}
        for transaction in transactions:
            month_key = transaction.date.strftime("%Y-%m")
            if month_key not in monthly_flow:
                monthly_flow[month_key] = {"income": 0, "expenses": 0}
            
            if transaction.is_income:
                monthly_flow[month_key]["income"] += transaction.amount
            else:
                monthly_flow[month_key]["expenses"] += abs(transaction.amount)
        
        return {
            "report_type": "cash_flow",
            "generated_at": datetime.utcnow().isoformat(),
            "monthly_cash_flow": monthly_flow,
            "parameters": parameters
        }
