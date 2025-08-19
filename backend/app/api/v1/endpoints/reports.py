"""
Report Builder API for FinGood Financial Platform

This module provides dynamic report generation capabilities building on the Analytics Engine.
It offers flexible report creation with custom filters, grouping, caching, and multiple
export formats for comprehensive financial analysis.

Key Features:
- Dynamic report generation with configurable parameters
- Custom date ranges, filters, and grouping options
- Redis caching for performance optimization
- Multiple export formats (JSON, CSV)
- User-specific reports with security isolation
- Comprehensive error handling and validation

Architecture:
- ReportBuilder: Main report generation service
- ReportDefinition: Configurable report parameters
- ReportCache: Redis-based caching system
- Export formatters for different output types
"""

import json
import logging
import hashlib
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import csv
import io

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
import redis

from app.core.database import get_db
from app.core.cookie_auth import get_current_user_from_cookie as get_current_user
from app.core.exceptions import ValidationException, SystemException
from app.core.config import settings
from app.models.user import User
from app.models.transaction import Transaction
from app.services.analytics_engine import (
    AnalyticsEngine, AnalyticsDateRange, TimeRange, 
    AnalyticsCache, KPICalculator, TimeSeriesAnalyzer, ChartDataFormatter
)
from app.core.error_sanitizer import error_sanitizer, create_secure_error_response
from app.core.audit_logger import security_audit_logger

logger = logging.getLogger(__name__)
router = APIRouter()

# Report configuration enums and models
class ReportType(str, Enum):
    """Available report types"""
    CASH_FLOW = "cash_flow"
    SPENDING_ANALYSIS = "spending_analysis"
    VENDOR_PERFORMANCE = "vendor_performance"
    CATEGORY_BREAKDOWN = "category_breakdown"
    MONTHLY_SUMMARY = "monthly_summary"
    QUARTERLY_SUMMARY = "quarterly_summary"
    CUSTOM_KPI = "custom_kpi"
    CATEGORIZATION_QUALITY = "categorization_quality"

class GroupBy(str, Enum):
    """Grouping options for reports"""
    NONE = "none"
    CATEGORY = "category"
    SUBCATEGORY = "subcategory"
    VENDOR = "vendor"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    WEEK = "week"

class ExportFormat(str, Enum):
    """Supported export formats"""
    JSON = "json"
    CSV = "csv"

class AggregationType(str, Enum):
    """Available aggregation functions"""
    SUM = "sum"
    AVG = "avg"
    COUNT = "count"
    MIN = "min"
    MAX = "max"

class ReportFilters(BaseModel):
    """Custom filters for report generation"""
    categories: Optional[List[str]] = Field(None, description="Filter by specific categories")
    vendors: Optional[List[str]] = Field(None, description="Filter by specific vendors")
    min_amount: Optional[float] = Field(None, ge=0, description="Minimum transaction amount")
    max_amount: Optional[float] = Field(None, ge=0, description="Maximum transaction amount")
    is_income: Optional[bool] = Field(None, description="Filter by income/expense type")
    is_categorized: Optional[bool] = Field(None, description="Filter by categorization status")
    description_contains: Optional[str] = Field(None, max_length=500, description="Filter by description content")

    @validator('max_amount')
    def validate_amount_range(cls, v, values):
        if v is not None and 'min_amount' in values and values['min_amount'] is not None:
            if v <= values['min_amount']:
                raise ValueError('max_amount must be greater than min_amount')
        return v

class ReportDefinition(BaseModel):
    """Complete report configuration"""
    report_type: ReportType = Field(..., description="Type of report to generate")
    start_date: date = Field(..., description="Report start date")
    end_date: date = Field(..., description="Report end date")
    group_by: GroupBy = Field(GroupBy.NONE, description="Grouping option")
    aggregation: AggregationType = Field(AggregationType.SUM, description="Aggregation function")
    filters: Optional[ReportFilters] = Field(None, description="Custom filters")
    include_charts: bool = Field(True, description="Include chart data in response")
    export_format: ExportFormat = Field(ExportFormat.JSON, description="Export format")
    use_cache: bool = Field(True, description="Use cached results if available")

    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('end_date must be after start_date')
        
        # Limit to reasonable date ranges (max 2 years)
        if 'start_date' in values:
            max_range = timedelta(days=730)  # 2 years
            if v - values['start_date'] > max_range:
                raise ValueError('Date range cannot exceed 2 years')
        
        return v

class ReportResponse(BaseModel):
    """Standard report response format"""
    report_id: str
    report_type: str
    generated_at: datetime
    date_range: Dict[str, date]
    summary: Dict[str, Any]
    data: List[Dict[str, Any]]
    charts: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any]

class ReportBuilder:
    """
    Advanced report generation service that builds on the Analytics Engine
    to provide flexible, cacheable reports with custom filtering and grouping.
    """
    
    def __init__(self, db: Session, user: User):
        """Initialize report builder with database session and user context"""
        self.db = db
        self.user = user
        self.analytics = AnalyticsEngine(db)
        self.cache = AnalyticsCache()
        self.kpi_calculator = KPICalculator(db)
        self.time_analyzer = TimeSeriesAnalyzer(db)
        self.chart_formatter = ChartDataFormatter()
        
    def generate_report(self, definition: ReportDefinition) -> ReportResponse:
        """
        Generate a comprehensive report based on the provided definition
        
        Args:
            definition: Report configuration and parameters
            
        Returns:
            ReportResponse: Complete report with data, charts, and metadata
            
        Raises:
            ValidationException: Invalid report parameters
            SystemException: Report generation errors
        """
        try:
            # Generate unique report ID
            report_id = self._generate_report_id(definition)
            
            # Check cache if requested
            if definition.use_cache:
                cached_report = self._get_cached_report(report_id)
                if cached_report:
                    logger.info(f"Returning cached report {report_id} for user {self.user.id}")
                    return cached_report
            
            # Create date range for analytics
            date_range = AnalyticsDateRange(
                start_date=definition.start_date,
                end_date=definition.end_date
            )
            
            # Generate report data based on type
            report_data = self._generate_report_data(definition, date_range)
            
            # Generate charts if requested
            charts = None
            if definition.include_charts:
                charts = self._generate_chart_data(definition, report_data)
            
            # Create response
            response = ReportResponse(
                report_id=report_id,
                report_type=definition.report_type.value,
                generated_at=datetime.utcnow(),
                date_range={
                    "start_date": definition.start_date,
                    "end_date": definition.end_date
                },
                summary=self._generate_summary(definition, report_data),
                data=report_data,
                charts=charts,
                metadata=self._generate_metadata(definition)
            )
            
            # Cache the report
            if definition.use_cache:
                self._cache_report(report_id, response)
            
            # Log report generation
            security_audit_logger.log_event(
                "report_generated",
                user_id=self.user.id,
                details={
                    "report_id": report_id,
                    "report_type": definition.report_type.value,
                    "date_range": f"{definition.start_date} to {definition.end_date}",
                    "cached": False
                }
            )
            
            return response
            
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Report generation failed for user {self.user.id}: {e}")
            raise SystemException(
                message="Failed to generate report",
                code="REPORT_GENERATION_ERROR"
            )
    
    def _generate_report_id(self, definition: ReportDefinition) -> str:
        """Generate unique report ID based on definition parameters"""
        # Create hash of report parameters for consistent IDs
        params = {
            "user_id": self.user.id,
            "report_type": definition.report_type.value,
            "start_date": definition.start_date.isoformat(),
            "end_date": definition.end_date.isoformat(),
            "group_by": definition.group_by.value,
            "aggregation": definition.aggregation.value,
            "filters": definition.filters.dict() if definition.filters else None,
            "include_charts": definition.include_charts
        }
        
        param_string = json.dumps(params, sort_keys=True, default=str)
        return hashlib.sha256(param_string.encode()).hexdigest()[:16]
    
    def _generate_report_data(self, definition: ReportDefinition, date_range: AnalyticsDateRange) -> List[Dict[str, Any]]:
        """Generate the main report data based on report type and parameters"""
        
        if definition.report_type == ReportType.CASH_FLOW:
            return self._generate_cash_flow_report(definition, date_range)
        elif definition.report_type == ReportType.SPENDING_ANALYSIS:
            return self._generate_spending_analysis(definition, date_range)
        elif definition.report_type == ReportType.VENDOR_PERFORMANCE:
            return self._generate_vendor_performance(definition, date_range)
        elif definition.report_type == ReportType.CATEGORY_BREAKDOWN:
            return self._generate_category_breakdown(definition, date_range)
        elif definition.report_type == ReportType.MONTHLY_SUMMARY:
            return self._generate_monthly_summary(definition, date_range)
        elif definition.report_type == ReportType.QUARTERLY_SUMMARY:
            return self._generate_quarterly_summary(definition, date_range)
        elif definition.report_type == ReportType.CUSTOM_KPI:
            return self._generate_custom_kpi_report(definition, date_range)
        elif definition.report_type == ReportType.CATEGORIZATION_QUALITY:
            return self._generate_categorization_quality(definition, date_range)
        else:
            raise ValidationException(f"Unsupported report type: {definition.report_type}")
    
    def _generate_cash_flow_report(self, definition: ReportDefinition, date_range: AnalyticsDateRange) -> List[Dict[str, Any]]:
        """Generate cash flow analysis report"""
        # Use existing analytics engine cash flow calculation
        cash_flow_data = self.analytics.calculate_cash_flow_summary(self.user.id, date_range)
        
        # Apply custom filters if specified
        base_query = self.db.query(Transaction).filter(
            Transaction.user_id == self.user.id,
            Transaction.date >= date_range.start_date,
            Transaction.date <= date_range.end_date
        )
        
        if definition.filters:
            base_query = self._apply_filters(base_query, definition.filters)
        
        # Group and aggregate based on parameters
        if definition.group_by == GroupBy.MONTH:
            results = self._group_by_month(base_query, definition.aggregation)
        elif definition.group_by == GroupBy.QUARTER:
            results = self._group_by_quarter(base_query, definition.aggregation)
        elif definition.group_by == GroupBy.CATEGORY:
            results = self._group_by_category(base_query, definition.aggregation)
        else:
            # No grouping - return overall summary
            results = [{
                "period": f"{date_range.start_date} to {date_range.end_date}",
                "total_income": cash_flow_data.get("total_income", 0),
                "total_expenses": cash_flow_data.get("total_expenses", 0),
                "net_cash_flow": cash_flow_data.get("net_cash_flow", 0),
                "transaction_count": cash_flow_data.get("transaction_count", 0)
            }]
        
        return results
    
    def _generate_spending_analysis(self, definition: ReportDefinition, date_range: AnalyticsDateRange) -> List[Dict[str, Any]]:
        """Generate detailed spending analysis"""
        spending_data = self.analytics.calculate_spending_by_category(self.user.id, date_range)
        
        # Transform and group the spending data
        results = []
        for category_data in spending_data.get("categories", []):
            results.append({
                "category": category_data.get("category"),
                "total_spent": category_data.get("total_amount", 0),
                "transaction_count": category_data.get("transaction_count", 0),
                "average_transaction": category_data.get("average_amount", 0),
                "percentage_of_total": category_data.get("percentage", 0),
                "subcategories": category_data.get("subcategories", [])
            })
        
        # Apply grouping if specified
        if definition.group_by == GroupBy.MONTH:
            results = self._add_time_grouping(results, date_range, "month")
        elif definition.group_by == GroupBy.QUARTER:
            results = self._add_time_grouping(results, date_range, "quarter")
        
        return results
    
    def _generate_vendor_performance(self, definition: ReportDefinition, date_range: AnalyticsDateRange) -> List[Dict[str, Any]]:
        """Generate vendor performance analysis"""
        vendor_data = self.analytics.calculate_vendor_analysis(self.user.id, date_range)
        
        results = []
        for vendor in vendor_data.get("top_vendors", []):
            results.append({
                "vendor": vendor.get("vendor"),
                "total_spent": vendor.get("total_amount", 0),
                "transaction_count": vendor.get("transaction_count", 0),
                "average_transaction": vendor.get("average_amount", 0),
                "first_transaction": vendor.get("first_transaction"),
                "last_transaction": vendor.get("last_transaction"),
                "primary_category": vendor.get("primary_category"),
                "spending_trend": vendor.get("trend", "stable")
            })
        
        return results
    
    def _generate_category_breakdown(self, definition: ReportDefinition, date_range: AnalyticsDateRange) -> List[Dict[str, Any]]:
        """Generate detailed category breakdown"""
        category_data = self.analytics.calculate_spending_by_category(self.user.id, date_range)
        
        results = []
        for category in category_data.get("categories", []):
            category_result = {
                "category": category.get("category"),
                "total_amount": category.get("total_amount", 0),
                "transaction_count": category.get("transaction_count", 0),
                "percentage": category.get("percentage", 0),
                "subcategories": []
            }
            
            # Add subcategory details
            for subcat in category.get("subcategories", []):
                category_result["subcategories"].append({
                    "subcategory": subcat.get("subcategory"),
                    "amount": subcat.get("amount", 0),
                    "count": subcat.get("count", 0),
                    "percentage": subcat.get("percentage", 0)
                })
            
            results.append(category_result)
        
        return results
    
    def _generate_monthly_summary(self, definition: ReportDefinition, date_range: AnalyticsDateRange) -> List[Dict[str, Any]]:
        """Generate monthly financial summary"""
        monthly_data = self.time_analyzer.calculate_monthly_trends(self.user.id, date_range)
        
        results = []
        for month_data in monthly_data.get("monthly_data", []):
            results.append({
                "month": month_data.get("period"),
                "total_income": month_data.get("income", 0),
                "total_expenses": month_data.get("expenses", 0),
                "net_cash_flow": month_data.get("net_cash_flow", 0),
                "transaction_count": month_data.get("transaction_count", 0),
                "average_transaction": month_data.get("average_transaction", 0),
                "growth_rate": month_data.get("growth_rate", 0)
            })
        
        return results
    
    def _generate_quarterly_summary(self, definition: ReportDefinition, date_range: AnalyticsDateRange) -> List[Dict[str, Any]]:
        """Generate quarterly financial summary"""
        # Group monthly data into quarters
        monthly_data = self._generate_monthly_summary(definition, date_range)
        
        quarterly_results = {}
        for month in monthly_data:
            month_date = datetime.strptime(month["month"], "%Y-%m")
            quarter = f"Q{(month_date.month-1)//3 + 1} {month_date.year}"
            
            if quarter not in quarterly_results:
                quarterly_results[quarter] = {
                    "quarter": quarter,
                    "total_income": 0,
                    "total_expenses": 0,
                    "net_cash_flow": 0,
                    "transaction_count": 0,
                    "months": []
                }
            
            q_data = quarterly_results[quarter]
            q_data["total_income"] += month["total_income"]
            q_data["total_expenses"] += month["total_expenses"]
            q_data["net_cash_flow"] += month["net_cash_flow"]
            q_data["transaction_count"] += month["transaction_count"]
            q_data["months"].append(month["month"])
        
        return list(quarterly_results.values())
    
    def _generate_custom_kpi_report(self, definition: ReportDefinition, date_range: AnalyticsDateRange) -> List[Dict[str, Any]]:
        """Generate custom KPI report"""
        kpis = self.analytics.calculate_financial_kpis(self.user.id, date_range)
        
        return [{
            "kpi_name": "Financial Overview",
            "period": f"{date_range.start_date} to {date_range.end_date}",
            "metrics": {
                "total_income": kpis.get("total_income", 0),
                "total_expenses": kpis.get("total_expenses", 0),
                "net_cash_flow": kpis.get("net_cash_flow", 0),
                "savings_rate": kpis.get("savings_rate", 0),
                "expense_ratio": kpis.get("expense_ratio", 0),
                "transaction_volume": kpis.get("transaction_count", 0),
                "average_transaction_size": kpis.get("average_transaction_size", 0),
                "categorization_rate": kpis.get("categorization_rate", 0)
            }
        }]
    
    def _generate_categorization_quality(self, definition: ReportDefinition, date_range: AnalyticsDateRange) -> List[Dict[str, Any]]:
        """Generate categorization quality report"""
        quality_data = self.analytics.calculate_categorization_quality(self.user.id, date_range)
        
        return [{
            "metric": "Categorization Quality",
            "period": f"{date_range.start_date} to {date_range.end_date}",
            "overall_rate": quality_data.get("categorization_rate", 0),
            "rule_based_count": quality_data.get("rule_categorized", 0),
            "ml_based_count": quality_data.get("ml_categorized", 0),
            "manual_count": quality_data.get("manual_categorized", 0),
            "uncategorized_count": quality_data.get("uncategorized", 0),
            "confidence_distribution": quality_data.get("confidence_distribution", {}),
            "category_accuracy": quality_data.get("category_accuracy", [])
        }]
    
    def _apply_filters(self, query, filters: ReportFilters):
        """Apply custom filters to the base query"""
        if filters.categories:
            query = query.filter(Transaction.category.in_(filters.categories))
        
        if filters.vendors:
            query = query.filter(Transaction.vendor.in_(filters.vendors))
        
        if filters.min_amount is not None:
            query = query.filter(Transaction.amount >= filters.min_amount)
        
        if filters.max_amount is not None:
            query = query.filter(Transaction.amount <= filters.max_amount)
        
        if filters.is_income is not None:
            query = query.filter(Transaction.is_income == filters.is_income)
        
        if filters.is_categorized is not None:
            query = query.filter(Transaction.is_categorized == filters.is_categorized)
        
        if filters.description_contains:
            query = query.filter(Transaction.description.ilike(f"%{filters.description_contains}%"))
        
        return query
    
    def _group_by_month(self, query, aggregation: AggregationType) -> List[Dict[str, Any]]:
        """Group query results by month"""
        # Implementation for monthly grouping with aggregation
        from sqlalchemy import extract, func
        
        if aggregation == AggregationType.SUM:
            agg_func = func.sum(Transaction.amount)
        elif aggregation == AggregationType.AVG:
            agg_func = func.avg(Transaction.amount)
        elif aggregation == AggregationType.COUNT:
            agg_func = func.count(Transaction.id)
        elif aggregation == AggregationType.MIN:
            agg_func = func.min(Transaction.amount)
        elif aggregation == AggregationType.MAX:
            agg_func = func.max(Transaction.amount)
        
        results = query.group_by(
            extract('year', Transaction.date),
            extract('month', Transaction.date)
        ).with_entities(
            extract('year', Transaction.date).label('year'),
            extract('month', Transaction.date).label('month'),
            agg_func.label('value')
        ).all()
        
        return [
            {
                "period": f"{int(r.year)}-{int(r.month):02d}",
                "value": float(r.value) if r.value else 0
            }
            for r in results
        ]
    
    def _group_by_quarter(self, query, aggregation: AggregationType) -> List[Dict[str, Any]]:
        """Group query results by quarter"""
        monthly_results = self._group_by_month(query, aggregation)
        
        quarterly_results = {}
        for month in monthly_results:
            year, month_num = month["period"].split("-")
            quarter = f"Q{(int(month_num)-1)//3 + 1} {year}"
            
            if quarter not in quarterly_results:
                quarterly_results[quarter] = {"period": quarter, "value": 0}
            
            if aggregation == AggregationType.SUM or aggregation == AggregationType.COUNT:
                quarterly_results[quarter]["value"] += month["value"]
            elif aggregation == AggregationType.AVG:
                # For average, we need to recalculate
                quarterly_results[quarter]["value"] = (quarterly_results[quarter]["value"] + month["value"]) / 2
            elif aggregation == AggregationType.MIN:
                quarterly_results[quarter]["value"] = min(quarterly_results[quarter]["value"], month["value"])
            elif aggregation == AggregationType.MAX:
                quarterly_results[quarter]["value"] = max(quarterly_results[quarter]["value"], month["value"])
        
        return list(quarterly_results.values())
    
    def _group_by_category(self, query, aggregation: AggregationType) -> List[Dict[str, Any]]:
        """Group query results by category"""
        if aggregation == AggregationType.SUM:
            agg_func = func.sum(Transaction.amount)
        elif aggregation == AggregationType.AVG:
            agg_func = func.avg(Transaction.amount)
        elif aggregation == AggregationType.COUNT:
            agg_func = func.count(Transaction.id)
        elif aggregation == AggregationType.MIN:
            agg_func = func.min(Transaction.amount)
        elif aggregation == AggregationType.MAX:
            agg_func = func.max(Transaction.amount)
        
        results = query.group_by(Transaction.category).with_entities(
            Transaction.category,
            agg_func.label('value')
        ).all()
        
        return [
            {
                "category": r.category or "Uncategorized",
                "value": float(r.value) if r.value else 0
            }
            for r in results
        ]
    
    def _add_time_grouping(self, data: List[Dict[str, Any]], date_range: AnalyticsDateRange, period: str) -> List[Dict[str, Any]]:
        """Add time-based grouping to existing data"""
        # This would add temporal analysis to the existing data
        # For now, return the data as-is with period metadata
        for item in data:
            item["time_period"] = period
            item["date_range"] = {
                "start": date_range.start_date.isoformat(),
                "end": date_range.end_date.isoformat()
            }
        
        return data
    
    def _generate_chart_data(self, definition: ReportDefinition, report_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate chart data for the report"""
        charts = {}
        
        # Generate appropriate charts based on report type
        if definition.report_type == ReportType.CASH_FLOW:
            if definition.group_by in [GroupBy.MONTH, GroupBy.QUARTER]:
                # Line chart for cash flow over time
                charts["cash_flow_trend"] = self.chart_formatter.format_line_chart(
                    data=report_data,
                    x_field="period",
                    y_fields=["net_cash_flow"],
                    title="Cash Flow Trend"
                )
        
        elif definition.report_type == ReportType.SPENDING_ANALYSIS:
            # Pie chart for spending by category
            pie_data = [{"name": item["category"], "value": item["total_spent"]} for item in report_data[:10]]
            charts["spending_breakdown"] = self.chart_formatter.format_pie_chart(
                data=pie_data,
                title="Spending Breakdown by Category"
            )
        
        elif definition.report_type == ReportType.VENDOR_PERFORMANCE:
            # Bar chart for top vendors
            bar_data = [{"name": item["vendor"], "value": item["total_spent"]} for item in report_data[:15]]
            charts["top_vendors"] = self.chart_formatter.format_bar_chart(
                data=bar_data,
                title="Top Vendors by Spending"
            )
        
        elif definition.report_type == ReportType.CATEGORY_BREAKDOWN:
            # Horizontal bar chart for categories
            bar_data = [{"name": item["category"], "value": item["total_amount"]} for item in report_data]
            charts["category_breakdown"] = self.chart_formatter.format_bar_chart(
                data=bar_data,
                title="Spending by Category",
                orientation="horizontal"
            )
        
        return charts
    
    def _generate_summary(self, definition: ReportDefinition, report_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics for the report"""
        if not report_data:
            return {"total_records": 0, "summary": "No data available"}
        
        summary = {
            "total_records": len(report_data),
            "report_type": definition.report_type.value,
            "date_range_days": (definition.end_date - definition.start_date).days + 1,
            "group_by": definition.group_by.value,
            "aggregation": definition.aggregation.value
        }
        
        # Add type-specific summaries
        if definition.report_type == ReportType.CASH_FLOW:
            total_income = sum(item.get("total_income", 0) for item in report_data)
            total_expenses = sum(item.get("total_expenses", 0) for item in report_data)
            summary.update({
                "total_income": total_income,
                "total_expenses": total_expenses,
                "net_cash_flow": total_income - total_expenses
            })
        
        elif definition.report_type == ReportType.SPENDING_ANALYSIS:
            total_spent = sum(item.get("total_spent", 0) for item in report_data)
            total_transactions = sum(item.get("transaction_count", 0) for item in report_data)
            summary.update({
                "total_spent": total_spent,
                "total_transactions": total_transactions,
                "average_transaction": total_spent / total_transactions if total_transactions > 0 else 0
            })
        
        return summary
    
    def _generate_metadata(self, definition: ReportDefinition) -> Dict[str, Any]:
        """Generate metadata about the report"""
        return {
            "generated_by": "FinGood Report Builder",
            "user_id": self.user.id,
            "generation_timestamp": datetime.utcnow().isoformat(),
            "report_version": "1.0",
            "filters_applied": definition.filters is not None,
            "cache_enabled": definition.use_cache,
            "export_format": definition.export_format.value
        }
    
    def _get_cached_report(self, report_id: str) -> Optional[ReportResponse]:
        """Retrieve cached report if available"""
        try:
            cache_key = f"report:{self.user.id}:{report_id}"
            cached_data = self.cache.get(cache_key)
            
            if cached_data:
                return ReportResponse(**json.loads(cached_data))
            
        except Exception as e:
            logger.warning(f"Failed to retrieve cached report {report_id}: {e}")
        
        return None
    
    def _cache_report(self, report_id: str, report: ReportResponse) -> None:
        """Cache the generated report"""
        try:
            cache_key = f"report:{self.user.id}:{report_id}"
            cache_data = report.dict()
            
            # Convert dates to strings for JSON serialization
            if "date_range" in cache_data:
                for key, value in cache_data["date_range"].items():
                    if isinstance(value, date):
                        cache_data["date_range"][key] = value.isoformat()
            
            self.cache.set(
                cache_key,
                json.dumps(cache_data, default=str),
                ttl=3600  # 1 hour cache
            )
            
        except Exception as e:
            logger.warning(f"Failed to cache report {report_id}: {e}")

class ReportExporter:
    """Handle different export formats for reports"""
    
    @staticmethod
    def to_csv(report: ReportResponse) -> str:
        """Export report data to CSV format"""
        output = io.StringIO()
        
        if not report.data:
            return ""
        
        # Get field names from the first data item
        fieldnames = list(report.data[0].keys())
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in report.data:
            # Flatten nested dictionaries and convert to strings
            flattened_row = {}
            for key, value in row.items():
                if isinstance(value, (dict, list)):
                    flattened_row[key] = json.dumps(value)
                else:
                    flattened_row[key] = str(value) if value is not None else ""
            
            writer.writerow(flattened_row)
        
        return output.getvalue()

# API Endpoints

@router.post("/generate", response_model=Union[ReportResponse, str])
async def generate_report(
    definition: ReportDefinition,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a dynamic report based on the provided definition.
    
    This endpoint creates comprehensive financial reports with custom filtering,
    grouping, and export options. Reports are cached for performance and can
    include chart data for frontend visualization.
    """
    try:
        # Validate date range
        max_date_range = timedelta(days=730)  # 2 years max
        if (definition.end_date - definition.start_date) > max_date_range:
            raise HTTPException(
                status_code=400,
                detail="Date range cannot exceed 2 years"
            )
        
        # Create report builder
        report_builder = ReportBuilder(db, current_user)
        
        # Generate report
        report = report_builder.generate_report(definition)
        
        # Handle different export formats
        if definition.export_format == ExportFormat.CSV:
            csv_data = ReportExporter.to_csv(report)
            return csv_data
        
        return report
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SystemException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error generating report: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while generating the report"
        )

@router.get("/templates")
async def get_report_templates(
    current_user: User = Depends(get_current_user)
):
    """
    Get available report templates with pre-configured settings.
    
    Returns a list of common report configurations that users can customize
    and use as starting points for their custom reports.
    """
    templates = [
        {
            "id": "monthly_cash_flow",
            "name": "Monthly Cash Flow",
            "description": "Track income and expenses month by month",
            "report_type": ReportType.CASH_FLOW.value,
            "group_by": GroupBy.MONTH.value,
            "recommended_date_range": "last_12_months",
            "include_charts": True
        },
        {
            "id": "spending_by_category",
            "name": "Spending Analysis by Category",
            "description": "Breakdown of expenses by category",
            "report_type": ReportType.SPENDING_ANALYSIS.value,
            "group_by": GroupBy.CATEGORY.value,
            "recommended_date_range": "last_3_months",
            "include_charts": True
        },
        {
            "id": "vendor_performance",
            "name": "Vendor Performance Report",
            "description": "Analysis of spending patterns by vendor",
            "report_type": ReportType.VENDOR_PERFORMANCE.value,
            "group_by": GroupBy.VENDOR.value,
            "recommended_date_range": "last_6_months",
            "include_charts": True
        },
        {
            "id": "quarterly_summary",
            "name": "Quarterly Financial Summary",
            "description": "High-level quarterly financial overview",
            "report_type": ReportType.QUARTERLY_SUMMARY.value,
            "group_by": GroupBy.QUARTER.value,
            "recommended_date_range": "last_24_months",
            "include_charts": True
        },
        {
            "id": "categorization_quality",
            "name": "Categorization Quality Report",
            "description": "Analysis of AI categorization accuracy",
            "report_type": ReportType.CATEGORIZATION_QUALITY.value,
            "group_by": GroupBy.NONE.value,
            "recommended_date_range": "last_3_months",
            "include_charts": True
        }
    ]
    
    return {"templates": templates}

@router.delete("/cache/{report_id}")
async def clear_report_cache(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Clear cached report data for a specific report ID.
    
    This endpoint allows users to force regeneration of reports by clearing
    the cached version. Useful when underlying data has changed.
    """
    try:
        cache = AnalyticsCache()
        cache_key = f"report:{current_user.id}:{report_id}"
        
        if cache.delete(cache_key):
            return {"message": f"Cache cleared for report {report_id}"}
        else:
            return {"message": f"No cached data found for report {report_id}"}
            
    except Exception as e:
        logger.error(f"Error clearing cache for report {report_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to clear report cache"
        )

@router.get("/export-formats")
async def get_supported_export_formats():
    """Get list of supported export formats"""
    formats = [
        {
            "format": ExportFormat.JSON.value,
            "name": "JSON",
            "description": "JavaScript Object Notation - suitable for API consumption",
            "mime_type": "application/json"
        },
        {
            "format": ExportFormat.CSV.value,
            "name": "CSV",
            "description": "Comma Separated Values - suitable for spreadsheet import",
            "mime_type": "text/csv"
        }
    ]
    
    return {"supported_formats": formats}