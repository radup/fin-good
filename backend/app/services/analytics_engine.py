"""
Analytics Engine for FinGood Financial Platform

This module provides comprehensive analytics and KPI calculation services for financial data.
It implements efficient database queries, Redis caching, and standardized data formatting
for charts and reports.

Key Features:
- Financial KPI calculations (cash flow, spending patterns, growth metrics)
- Time-series analysis with trend detection
- Category and vendor analytics
- Categorization quality metrics
- Redis caching for performance optimization
- Standardized chart data formatting
- User-specific analytics with security isolation

Architecture:
- AnalyticsEngine: Main service class
- KPICalculator: Specific financial calculations
- TimeSeriesAnalyzer: Time-based analytics
- ChartDataFormatter: Frontend data formatting
- AnalyticsCache: Redis caching layer
"""

import json
import logging
import hashlib
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum

import redis
from sqlalchemy import func, and_, or_, text, extract
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ValidationException, SystemException
from app.models.transaction import Transaction, Category, CategorizationRule
from app.models.user import User

logger = logging.getLogger(__name__)

# Data structures for analytics
class TimeRange(str, Enum):
    """Supported time ranges for analytics"""
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    LAST_6_MONTHS = "last_6_months"
    LAST_YEAR = "last_year"
    YEAR_TO_DATE = "year_to_date"
    ALL_TIME = "all_time"
    CUSTOM = "custom"

class ChartType(str, Enum):
    """Chart types for data formatting"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    DONUT = "donut"
    AREA = "area"
    SCATTER = "scatter"

@dataclass
class AnalyticsDateRange:
    """Date range for analytics queries"""
    start_date: datetime
    end_date: datetime
    range_type: TimeRange
    
    @classmethod
    def from_time_range(cls, time_range: TimeRange, custom_start: Optional[datetime] = None, custom_end: Optional[datetime] = None):
        """Create date range from time range enum"""
        now = datetime.utcnow()
        
        if time_range == TimeRange.LAST_7_DAYS:
            start_date = now - timedelta(days=7)
        elif time_range == TimeRange.LAST_30_DAYS:
            start_date = now - timedelta(days=30)
        elif time_range == TimeRange.LAST_90_DAYS:
            start_date = now - timedelta(days=90)
        elif time_range == TimeRange.LAST_6_MONTHS:
            start_date = now - timedelta(days=180)
        elif time_range == TimeRange.LAST_YEAR:
            start_date = now - timedelta(days=365)
        elif time_range == TimeRange.YEAR_TO_DATE:
            start_date = datetime(now.year, 1, 1)
        elif time_range == TimeRange.ALL_TIME:
            start_date = datetime(2000, 1, 1)  # Far back date
        elif time_range == TimeRange.CUSTOM:
            if not custom_start or not custom_end:
                raise ValidationException("Custom date range requires start and end dates")
            start_date = custom_start
        else:
            start_date = now - timedelta(days=30)  # Default fallback
        
        end_date = custom_end if time_range == TimeRange.CUSTOM else now
        
        return cls(start_date=start_date, end_date=end_date, range_type=time_range)

@dataclass
class KPIMetric:
    """Standard KPI metric structure"""
    name: str
    value: Union[float, int, str]
    formatted_value: str
    change_percentage: Optional[float] = None
    change_direction: Optional[str] = None  # "up", "down", "neutral"
    period_comparison: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ChartDataPoint:
    """Individual chart data point"""
    label: str
    value: Union[float, int]
    date: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ChartData:
    """Formatted chart data for frontend"""
    chart_type: ChartType
    title: str
    data_points: List[ChartDataPoint]
    x_axis_label: Optional[str] = None
    y_axis_label: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class AnalyticsSummary:
    """Complete analytics summary"""
    kpis: List[KPIMetric]
    charts: List[ChartData]
    date_range: AnalyticsDateRange
    cache_info: Optional[Dict[str, Any]] = None
    generated_at: datetime = None

    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.utcnow()

class AnalyticsCache:
    """Redis-based caching for analytics data"""
    
    def __init__(self):
        """Initialize Redis connection for analytics caching"""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=10,
                socket_connect_timeout=10
            )
            self.redis_client.ping()
            self.cache_prefix = "fingood:analytics"
            self.default_ttl = 3600  # 1 hour cache by default
            logger.info("Analytics cache initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize analytics cache: {e}")
            self.redis_client = None

    def _generate_cache_key(self, user_id: int, operation: str, **params) -> str:
        """Generate cache key for analytics operation"""
        # Create deterministic key from parameters
        params_str = json.dumps(params, sort_keys=True, default=str)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        return f"{self.cache_prefix}:user:{user_id}:{operation}:{params_hash}"

    async def get(self, user_id: int, operation: str, **params) -> Optional[Dict[str, Any]]:
        """Get cached analytics data"""
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key(user_id, operation, **params)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                logger.debug(f"Cache hit for {operation} (user {user_id})")
                return json.loads(cached_data)
            
            return None
        except Exception as e:
            logger.error(f"Failed to get from cache: {e}")
            return None

    async def set(self, user_id: int, operation: str, data: Dict[str, Any], ttl: Optional[int] = None, **params) -> bool:
        """Cache analytics data"""
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(user_id, operation, **params)
            cache_ttl = ttl or self.default_ttl
            
            # Add cache metadata
            cache_data = {
                "data": data,
                "cached_at": datetime.utcnow().isoformat(),
                "ttl": cache_ttl,
                "cache_key": cache_key
            }
            
            self.redis_client.setex(
                cache_key,
                cache_ttl,
                json.dumps(cache_data, default=str)
            )
            
            logger.debug(f"Cached {operation} for user {user_id} (TTL: {cache_ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Failed to cache data: {e}")
            return False

    async def invalidate_user_cache(self, user_id: int) -> int:
        """Invalidate all cached analytics for a user"""
        if not self.redis_client:
            return 0
        
        try:
            pattern = f"{self.cache_prefix}:user:{user_id}:*"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                deleted_count = self.redis_client.delete(*keys)
                logger.info(f"Invalidated {deleted_count} cache entries for user {user_id}")
                return deleted_count
            
            return 0
        except Exception as e:
            logger.error(f"Failed to invalidate cache for user {user_id}: {e}")
            return 0

class KPICalculator:
    """Financial KPI calculation utilities"""
    
    def __init__(self, db: Session, cache: AnalyticsCache):
        self.db = db
        self.cache = cache

    async def calculate_cash_flow_summary(self, user_id: int, date_range: AnalyticsDateRange) -> Dict[str, Any]:
        """Calculate comprehensive cash flow summary"""
        
        # Check cache first
        cached_result = await self.cache.get(
            user_id, "cash_flow_summary",
            start_date=date_range.start_date,
            end_date=date_range.end_date,
            range_type=date_range.range_type.value
        )
        
        if cached_result:
            return cached_result["data"]

        try:
            # Base query for transactions in date range
            base_query = self.db.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.date >= date_range.start_date,
                Transaction.date <= date_range.end_date
            )

            # Income calculations
            total_income = base_query.filter(Transaction.is_income == True).with_entities(
                func.coalesce(func.sum(Transaction.amount), 0)
            ).scalar() or 0

            # Expense calculations
            total_expenses = base_query.filter(Transaction.is_income == False).with_entities(
                func.coalesce(func.sum(func.abs(Transaction.amount)), 0)
            ).scalar() or 0

            # Net cash flow
            net_cash_flow = total_income - total_expenses

            # Transaction counts
            income_count = base_query.filter(Transaction.is_income == True).count()
            expense_count = base_query.filter(Transaction.is_income == False).count()
            total_transactions = income_count + expense_count

            # Average transaction amounts
            avg_income = total_income / income_count if income_count > 0 else 0
            avg_expense = total_expenses / expense_count if expense_count > 0 else 0

            # Calculate previous period comparison
            previous_period_days = (date_range.end_date - date_range.start_date).days
            previous_start = date_range.start_date - timedelta(days=previous_period_days)
            previous_end = date_range.start_date

            previous_query = self.db.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.date >= previous_start,
                Transaction.date < previous_end
            )

            previous_income = previous_query.filter(Transaction.is_income == True).with_entities(
                func.coalesce(func.sum(Transaction.amount), 0)
            ).scalar() or 0

            previous_expenses = previous_query.filter(Transaction.is_income == False).with_entities(
                func.coalesce(func.sum(func.abs(Transaction.amount)), 0)
            ).scalar() or 0

            previous_net = previous_income - previous_expenses

            # Calculate percentage changes
            income_change = ((total_income - previous_income) / previous_income * 100) if previous_income > 0 else None
            expense_change = ((total_expenses - previous_expenses) / previous_expenses * 100) if previous_expenses > 0 else None
            net_change = ((net_cash_flow - previous_net) / abs(previous_net) * 100) if previous_net != 0 else None

            result = {
                "period": {
                    "start_date": date_range.start_date.isoformat(),
                    "end_date": date_range.end_date.isoformat(),
                    "range_type": date_range.range_type.value,
                    "days": (date_range.end_date - date_range.start_date).days
                },
                "totals": {
                    "total_income": float(total_income),
                    "total_expenses": float(total_expenses),
                    "net_cash_flow": float(net_cash_flow),
                    "total_transactions": total_transactions
                },
                "averages": {
                    "avg_income_per_transaction": float(avg_income),
                    "avg_expense_per_transaction": float(avg_expense),
                    "avg_daily_income": float(total_income / max(1, (date_range.end_date - date_range.start_date).days)),
                    "avg_daily_expenses": float(total_expenses / max(1, (date_range.end_date - date_range.start_date).days))
                },
                "counts": {
                    "income_transactions": income_count,
                    "expense_transactions": expense_count,
                    "total_transactions": total_transactions
                },
                "comparisons": {
                    "previous_period": {
                        "income": float(previous_income),
                        "expenses": float(previous_expenses),
                        "net": float(previous_net)
                    },
                    "percentage_changes": {
                        "income_change": income_change,
                        "expense_change": expense_change,
                        "net_change": net_change
                    }
                },
                "calculated_at": datetime.utcnow().isoformat()
            }

            # Cache the result
            await self.cache.set(
                user_id, "cash_flow_summary", result, ttl=1800,  # 30 minutes
                start_date=date_range.start_date,
                end_date=date_range.end_date,
                range_type=date_range.range_type.value
            )

            return result

        except Exception as e:
            logger.error(f"Failed to calculate cash flow summary for user {user_id}: {e}")
            raise SystemException(
                message="Failed to calculate cash flow summary",
                code="ANALYTICS_CALCULATION_ERROR"
            )

    async def get_spending_by_category(self, user_id: int, date_range: AnalyticsDateRange, limit: int = 20) -> Dict[str, Any]:
        """Calculate spending breakdown by category"""
        
        # Check cache first
        cached_result = await self.cache.get(
            user_id, "spending_by_category",
            start_date=date_range.start_date,
            end_date=date_range.end_date,
            range_type=date_range.range_type.value,
            limit=limit
        )
        
        if cached_result:
            return cached_result["data"]

        try:
            # Query for expense transactions grouped by category
            category_spending = self.db.query(
                Transaction.category,
                func.sum(func.abs(Transaction.amount)).label('total_amount'),
                func.count(Transaction.id).label('transaction_count'),
                func.avg(func.abs(Transaction.amount)).label('avg_amount')
            ).filter(
                Transaction.user_id == user_id,
                Transaction.is_income == False,
                Transaction.date >= date_range.start_date,
                Transaction.date <= date_range.end_date,
                Transaction.category.isnot(None)
            ).group_by(Transaction.category).order_by(
                func.sum(func.abs(Transaction.amount)).desc()
            ).limit(limit).all()

            # Calculate totals
            total_categorized_spending = sum(float(row.total_amount) for row in category_spending)
            
            # Get uncategorized spending
            uncategorized_spending = self.db.query(
                func.coalesce(func.sum(func.abs(Transaction.amount)), 0)
            ).filter(
                Transaction.user_id == user_id,
                Transaction.is_income == False,
                Transaction.date >= date_range.start_date,
                Transaction.date <= date_range.end_date,
                or_(Transaction.category.is_(None), Transaction.category == '')
            ).scalar() or 0

            total_spending = total_categorized_spending + float(uncategorized_spending)

            # Format results
            categories = []
            for row in category_spending:
                percentage = (float(row.total_amount) / total_spending * 100) if total_spending > 0 else 0
                categories.append({
                    "category": row.category,
                    "total_amount": float(row.total_amount),
                    "transaction_count": row.transaction_count,
                    "avg_amount": float(row.avg_amount),
                    "percentage": round(percentage, 2)
                })

            # Add uncategorized if significant
            if uncategorized_spending > 0:
                uncategorized_percentage = (float(uncategorized_spending) / total_spending * 100) if total_spending > 0 else 0
                categories.append({
                    "category": "Uncategorized",
                    "total_amount": float(uncategorized_spending),
                    "transaction_count": self.db.query(Transaction).filter(
                        Transaction.user_id == user_id,
                        Transaction.is_income == False,
                        Transaction.date >= date_range.start_date,
                        Transaction.date <= date_range.end_date,
                        or_(Transaction.category.is_(None), Transaction.category == '')
                    ).count(),
                    "avg_amount": 0,  # Will calculate below
                    "percentage": round(uncategorized_percentage, 2)
                })

            result = {
                "period": {
                    "start_date": date_range.start_date.isoformat(),
                    "end_date": date_range.end_date.isoformat(),
                    "range_type": date_range.range_type.value
                },
                "summary": {
                    "total_spending": total_spending,
                    "total_categorized": total_categorized_spending,
                    "total_uncategorized": float(uncategorized_spending),
                    "categorization_rate": round((total_categorized_spending / total_spending * 100), 2) if total_spending > 0 else 0,
                    "category_count": len([c for c in categories if c["category"] != "Uncategorized"])
                },
                "categories": categories,
                "calculated_at": datetime.utcnow().isoformat()
            }

            # Cache the result
            await self.cache.set(
                user_id, "spending_by_category", result, ttl=1800,  # 30 minutes
                start_date=date_range.start_date,
                end_date=date_range.end_date,
                range_type=date_range.range_type.value,
                limit=limit
            )

            return result

        except Exception as e:
            logger.error(f"Failed to calculate spending by category for user {user_id}: {e}")
            raise SystemException(
                message="Failed to calculate category spending",
                code="ANALYTICS_CALCULATION_ERROR"
            )

    async def analyze_vendor_spending(self, user_id: int, date_range: AnalyticsDateRange, limit: int = 15) -> Dict[str, Any]:
        """Analyze spending patterns by vendor"""
        
        # Check cache first
        cached_result = await self.cache.get(
            user_id, "vendor_spending",
            start_date=date_range.start_date,
            end_date=date_range.end_date,
            range_type=date_range.range_type.value,
            limit=limit
        )
        
        if cached_result:
            return cached_result["data"]

        try:
            # Query for vendor spending
            vendor_spending = self.db.query(
                Transaction.vendor,
                func.sum(func.abs(Transaction.amount)).label('total_amount'),
                func.count(Transaction.id).label('transaction_count'),
                func.avg(func.abs(Transaction.amount)).label('avg_amount'),
                func.min(Transaction.date).label('first_transaction'),
                func.max(Transaction.date).label('last_transaction')
            ).filter(
                Transaction.user_id == user_id,
                Transaction.is_income == False,
                Transaction.date >= date_range.start_date,
                Transaction.date <= date_range.end_date,
                Transaction.vendor.isnot(None),
                Transaction.vendor != ''
            ).group_by(Transaction.vendor).order_by(
                func.sum(func.abs(Transaction.amount)).desc()
            ).limit(limit).all()

            # Calculate total spending for percentages
            total_vendor_spending = sum(float(row.total_amount) for row in vendor_spending)

            # Format results
            vendors = []
            for row in vendor_spending:
                percentage = (float(row.total_amount) / total_vendor_spending * 100) if total_vendor_spending > 0 else 0
                days_active = (row.last_transaction - row.first_transaction).days + 1
                frequency = row.transaction_count / days_active if days_active > 0 else 0
                
                vendors.append({
                    "vendor": row.vendor,
                    "total_amount": float(row.total_amount),
                    "transaction_count": row.transaction_count,
                    "avg_amount": float(row.avg_amount),
                    "percentage": round(percentage, 2),
                    "first_transaction": row.first_transaction.isoformat(),
                    "last_transaction": row.last_transaction.isoformat(),
                    "days_active": days_active,
                    "frequency_per_day": round(frequency, 3)
                })

            result = {
                "period": {
                    "start_date": date_range.start_date.isoformat(),
                    "end_date": date_range.end_date.isoformat(),
                    "range_type": date_range.range_type.value
                },
                "summary": {
                    "total_vendor_spending": total_vendor_spending,
                    "unique_vendors": len(vendors),
                    "avg_spending_per_vendor": total_vendor_spending / len(vendors) if vendors else 0
                },
                "vendors": vendors,
                "calculated_at": datetime.utcnow().isoformat()
            }

            # Cache the result
            await self.cache.set(
                user_id, "vendor_spending", result, ttl=1800,  # 30 minutes
                start_date=date_range.start_date,
                end_date=date_range.end_date,
                range_type=date_range.range_type.value,
                limit=limit
            )

            return result

        except Exception as e:
            logger.error(f"Failed to analyze vendor spending for user {user_id}: {e}")
            raise SystemException(
                message="Failed to analyze vendor spending",
                code="ANALYTICS_CALCULATION_ERROR"
            )

class TimeSeriesAnalyzer:
    """Time-series analysis utilities for financial data"""
    
    def __init__(self, db: Session, cache: AnalyticsCache):
        self.db = db
        self.cache = cache

    async def get_monthly_trends(self, user_id: int, date_range: AnalyticsDateRange) -> Dict[str, Any]:
        """Calculate monthly income/expense trends"""
        
        # Check cache first
        cached_result = await self.cache.get(
            user_id, "monthly_trends",
            start_date=date_range.start_date,
            end_date=date_range.end_date,
            range_type=date_range.range_type.value
        )
        
        if cached_result:
            return cached_result["data"]

        try:
            # Query for monthly aggregations
            monthly_data = self.db.query(
                extract('year', Transaction.date).label('year'),
                extract('month', Transaction.date).label('month'),
                func.sum(
                    func.case(
                        (Transaction.is_income == True, Transaction.amount),
                        else_=0
                    )
                ).label('income'),
                func.sum(
                    func.case(
                        (Transaction.is_income == False, func.abs(Transaction.amount)),
                        else_=0
                    )
                ).label('expenses'),
                func.count(Transaction.id).label('transaction_count')
            ).filter(
                Transaction.user_id == user_id,
                Transaction.date >= date_range.start_date,
                Transaction.date <= date_range.end_date
            ).group_by(
                extract('year', Transaction.date),
                extract('month', Transaction.date)
            ).order_by(
                extract('year', Transaction.date),
                extract('month', Transaction.date)
            ).all()

            # Format results
            months = []
            for row in monthly_data:
                month_date = datetime(int(row.year), int(row.month), 1)
                net_flow = float(row.income) - float(row.expenses)
                
                months.append({
                    "year": int(row.year),
                    "month": int(row.month),
                    "date": month_date.isoformat(),
                    "month_name": month_date.strftime("%B %Y"),
                    "income": float(row.income),
                    "expenses": float(row.expenses),
                    "net_flow": net_flow,
                    "transaction_count": row.transaction_count
                })

            # Calculate trends and growth rates
            if len(months) > 1:
                for i in range(1, len(months)):
                    prev_month = months[i-1]
                    curr_month = months[i]
                    
                    # Calculate month-over-month growth
                    income_growth = ((curr_month["income"] - prev_month["income"]) / prev_month["income"] * 100) if prev_month["income"] > 0 else None
                    expense_growth = ((curr_month["expenses"] - prev_month["expenses"]) / prev_month["expenses"] * 100) if prev_month["expenses"] > 0 else None
                    
                    curr_month["growth"] = {
                        "income_growth": income_growth,
                        "expense_growth": expense_growth
                    }

            # Calculate summary statistics
            total_months = len(months)
            if total_months > 0:
                total_income = sum(m["income"] for m in months)
                total_expenses = sum(m["expenses"] for m in months)
                avg_monthly_income = total_income / total_months
                avg_monthly_expenses = total_expenses / total_months
                
                # Calculate trend direction (simple linear regression slope)
                income_trend = self._calculate_trend([m["income"] for m in months])
                expense_trend = self._calculate_trend([m["expenses"] for m in months])
            else:
                total_income = total_expenses = avg_monthly_income = avg_monthly_expenses = 0
                income_trend = expense_trend = "stable"

            result = {
                "period": {
                    "start_date": date_range.start_date.isoformat(),
                    "end_date": date_range.end_date.isoformat(),
                    "range_type": date_range.range_type.value,
                    "total_months": total_months
                },
                "summary": {
                    "total_income": total_income,
                    "total_expenses": total_expenses,
                    "avg_monthly_income": avg_monthly_income,
                    "avg_monthly_expenses": avg_monthly_expenses,
                    "income_trend": income_trend,
                    "expense_trend": expense_trend
                },
                "monthly_data": months,
                "calculated_at": datetime.utcnow().isoformat()
            }

            # Cache the result
            await self.cache.set(
                user_id, "monthly_trends", result, ttl=3600,  # 1 hour
                start_date=date_range.start_date,
                end_date=date_range.end_date,
                range_type=date_range.range_type.value
            )

            return result

        except Exception as e:
            logger.error(f"Failed to calculate monthly trends for user {user_id}: {e}")
            raise SystemException(
                message="Failed to calculate monthly trends",
                code="ANALYTICS_CALCULATION_ERROR"
            )

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from list of values"""
        if len(values) < 2:
            return "stable"
        
        # Simple linear regression slope
        n = len(values)
        x_values = list(range(n))
        
        sum_x = sum(x_values)
        sum_y = sum(values)
        sum_xy = sum(x * y for x, y in zip(x_values, values))
        sum_x2 = sum(x * x for x in x_values)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        if slope > 0.05:  # Threshold for significant increase
            return "increasing"
        elif slope < -0.05:  # Threshold for significant decrease
            return "decreasing"
        else:
            return "stable"

class ChartDataFormatter:
    """Format analytics data for frontend charts"""
    
    @staticmethod
    def format_cash_flow_chart(cash_flow_data: Dict[str, Any]) -> ChartData:
        """Format cash flow data for bar chart"""
        return ChartData(
            chart_type=ChartType.BAR,
            title="Cash Flow Summary",
            data_points=[
                ChartDataPoint(
                    label="Income",
                    value=cash_flow_data["totals"]["total_income"],
                    metadata={"type": "income", "count": cash_flow_data["counts"]["income_transactions"]}
                ),
                ChartDataPoint(
                    label="Expenses",
                    value=cash_flow_data["totals"]["total_expenses"],
                    metadata={"type": "expenses", "count": cash_flow_data["counts"]["expense_transactions"]}
                ),
                ChartDataPoint(
                    label="Net Flow",
                    value=cash_flow_data["totals"]["net_cash_flow"],
                    metadata={"type": "net", "count": cash_flow_data["counts"]["total_transactions"]}
                )
            ],
            x_axis_label="Type",
            y_axis_label="Amount ($)",
            metadata={
                "period": cash_flow_data["period"],
                "comparisons": cash_flow_data["comparisons"]
            }
        )

    @staticmethod
    def format_category_spending_chart(category_data: Dict[str, Any]) -> ChartData:
        """Format category spending data for pie chart"""
        data_points = [
            ChartDataPoint(
                label=cat["category"],
                value=cat["total_amount"],
                metadata={
                    "percentage": cat["percentage"],
                    "transaction_count": cat["transaction_count"],
                    "avg_amount": cat.get("avg_amount", 0)
                }
            )
            for cat in category_data["categories"][:10]  # Top 10 categories for readability
        ]
        
        return ChartData(
            chart_type=ChartType.PIE,
            title="Spending by Category",
            data_points=data_points,
            metadata={
                "period": category_data["period"],
                "summary": category_data["summary"]
            }
        )

    @staticmethod
    def format_monthly_trends_chart(trends_data: Dict[str, Any]) -> ChartData:
        """Format monthly trends data for line chart"""
        data_points = [
            ChartDataPoint(
                label=month["month_name"],
                value=month["net_flow"],
                date=datetime.fromisoformat(month["date"]),
                metadata={
                    "income": month["income"],
                    "expenses": month["expenses"],
                    "transaction_count": month["transaction_count"],
                    "growth": month.get("growth", {})
                }
            )
            for month in trends_data["monthly_data"]
        ]
        
        return ChartData(
            chart_type=ChartType.LINE,
            title="Monthly Cash Flow Trends",
            data_points=data_points,
            x_axis_label="Month",
            y_axis_label="Net Cash Flow ($)",
            metadata={
                "period": trends_data["period"],
                "summary": trends_data["summary"]
            }
        )

class AnalyticsEngine:
    """Main analytics engine for financial data analysis"""
    
    def __init__(self, db: Session):
        """Initialize analytics engine with database session"""
        self.db = db
        self.cache = AnalyticsCache()
        self.kpi_calculator = KPICalculator(db, self.cache)
        self.time_series_analyzer = TimeSeriesAnalyzer(db, self.cache)
        self.chart_formatter = ChartDataFormatter()

    async def get_complete_analytics_summary(
        self, 
        user_id: int, 
        time_range: TimeRange = TimeRange.LAST_30_DAYS,
        custom_start: Optional[datetime] = None,
        custom_end: Optional[datetime] = None
    ) -> AnalyticsSummary:
        """Get complete analytics summary for a user"""
        
        try:
            # Validate user exists
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValidationException(f"User {user_id} not found")

            # Create date range
            date_range = AnalyticsDateRange.from_time_range(time_range, custom_start, custom_end)

            # Calculate all analytics in parallel
            cash_flow_data = await self.kpi_calculator.calculate_cash_flow_summary(user_id, date_range)
            category_data = await self.kpi_calculator.get_spending_by_category(user_id, date_range)
            vendor_data = await self.kpi_calculator.analyze_vendor_spending(user_id, date_range)
            trends_data = await self.time_series_analyzer.get_monthly_trends(user_id, date_range)

            # Create KPI metrics
            kpis = [
                KPIMetric(
                    name="Total Income",
                    value=cash_flow_data["totals"]["total_income"],
                    formatted_value=f"${cash_flow_data['totals']['total_income']:,.2f}",
                    change_percentage=cash_flow_data["comparisons"]["percentage_changes"]["income_change"],
                    change_direction=self._get_change_direction(cash_flow_data["comparisons"]["percentage_changes"]["income_change"]),
                    period_comparison="vs previous period"
                ),
                KPIMetric(
                    name="Total Expenses",
                    value=cash_flow_data["totals"]["total_expenses"],
                    formatted_value=f"${cash_flow_data['totals']['total_expenses']:,.2f}",
                    change_percentage=cash_flow_data["comparisons"]["percentage_changes"]["expense_change"],
                    change_direction=self._get_change_direction(cash_flow_data["comparisons"]["percentage_changes"]["expense_change"]),
                    period_comparison="vs previous period"
                ),
                KPIMetric(
                    name="Net Cash Flow",
                    value=cash_flow_data["totals"]["net_cash_flow"],
                    formatted_value=f"${cash_flow_data['totals']['net_cash_flow']:,.2f}",
                    change_percentage=cash_flow_data["comparisons"]["percentage_changes"]["net_change"],
                    change_direction=self._get_change_direction(cash_flow_data["comparisons"]["percentage_changes"]["net_change"]),
                    period_comparison="vs previous period"
                ),
                KPIMetric(
                    name="Categorization Rate",
                    value=category_data["summary"]["categorization_rate"],
                    formatted_value=f"{category_data['summary']['categorization_rate']:.1f}%",
                    metadata={"total_categories": category_data["summary"]["category_count"]}
                ),
                KPIMetric(
                    name="Unique Vendors",
                    value=vendor_data["summary"]["unique_vendors"],
                    formatted_value=str(vendor_data["summary"]["unique_vendors"]),
                    metadata={"avg_spending": vendor_data["summary"]["avg_spending_per_vendor"]}
                )
            ]

            # Create charts
            charts = [
                self.chart_formatter.format_cash_flow_chart(cash_flow_data),
                self.chart_formatter.format_category_spending_chart(category_data),
                self.chart_formatter.format_monthly_trends_chart(trends_data)
            ]

            return AnalyticsSummary(
                kpis=kpis,
                charts=charts,
                date_range=date_range,
                cache_info={
                    "cache_enabled": self.cache.redis_client is not None,
                    "cache_prefix": self.cache.cache_prefix
                }
            )

        except Exception as e:
            logger.error(f"Failed to generate analytics summary for user {user_id}: {e}")
            raise SystemException(
                message="Failed to generate analytics summary",
                code="ANALYTICS_SUMMARY_ERROR"
            )

    def _get_change_direction(self, change_percentage: Optional[float]) -> Optional[str]:
        """Determine change direction from percentage"""
        if change_percentage is None:
            return None
        elif change_percentage > 1:  # >1% increase
            return "up"
        elif change_percentage < -1:  # >1% decrease
            return "down"
        else:
            return "neutral"

    async def invalidate_user_analytics_cache(self, user_id: int) -> int:
        """Invalidate all cached analytics for a user (call after data changes)"""
        return await self.cache.invalidate_user_cache(user_id)

    async def get_categorization_quality_metrics(self, user_id: int, date_range: AnalyticsDateRange) -> Dict[str, Any]:
        """Calculate categorization quality and confidence metrics"""
        
        try:
            # Get categorization statistics
            total_transactions = self.db.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.date >= date_range.start_date,
                Transaction.date <= date_range.end_date
            ).count()

            categorized_transactions = self.db.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.date >= date_range.start_date,
                Transaction.date <= date_range.end_date,
                Transaction.is_categorized == True
            ).count()

            # Get confidence score distribution
            confidence_stats = self.db.query(
                func.avg(Transaction.confidence_score).label('avg_confidence'),
                func.min(Transaction.confidence_score).label('min_confidence'),
                func.max(Transaction.confidence_score).label('max_confidence'),
                func.count(Transaction.id).label('count_with_scores')
            ).filter(
                Transaction.user_id == user_id,
                Transaction.date >= date_range.start_date,
                Transaction.date <= date_range.end_date,
                Transaction.confidence_score.isnot(None)
            ).first()

            categorization_rate = (categorized_transactions / total_transactions * 100) if total_transactions > 0 else 0

            return {
                "period": {
                    "start_date": date_range.start_date.isoformat(),
                    "end_date": date_range.end_date.isoformat(),
                    "range_type": date_range.range_type.value
                },
                "summary": {
                    "total_transactions": total_transactions,
                    "categorized_transactions": categorized_transactions,
                    "uncategorized_transactions": total_transactions - categorized_transactions,
                    "categorization_rate": round(categorization_rate, 2)
                },
                "confidence_metrics": {
                    "avg_confidence": float(confidence_stats.avg_confidence) if confidence_stats.avg_confidence else None,
                    "min_confidence": float(confidence_stats.min_confidence) if confidence_stats.min_confidence else None,
                    "max_confidence": float(confidence_stats.max_confidence) if confidence_stats.max_confidence else None,
                    "transactions_with_scores": confidence_stats.count_with_scores
                },
                "calculated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to calculate categorization quality metrics for user {user_id}: {e}")
            raise SystemException(
                message="Failed to calculate categorization quality metrics",
                code="ANALYTICS_CALCULATION_ERROR"
            )