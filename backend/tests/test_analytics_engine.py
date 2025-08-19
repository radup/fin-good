"""
Comprehensive Test Suite for Analytics Engine

This test suite provides complete coverage for the analytics engine functionality,
including KPI calculations, time-series analysis, caching, and data formatting.

Test Categories:
- Unit tests for individual components
- Integration tests for complete workflows
- Performance tests for caching and large datasets
- Error handling and edge case testing
- Security tests for user isolation
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock
from freezegun import freeze_time

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.transaction import Transaction, Category, CategorizationRule
from app.services.analytics_engine import (
    AnalyticsEngine, KPICalculator, TimeSeriesAnalyzer, ChartDataFormatter,
    AnalyticsCache, AnalyticsDateRange, TimeRange, ChartType, KPIMetric,
    ChartData, ChartDataPoint, AnalyticsSummary
)
from app.core.exceptions import ValidationException, SystemException

class TestAnalyticsDateRange:
    """Test date range creation and validation"""
    
    @freeze_time("2024-03-15 12:00:00")
    def test_from_time_range_last_7_days(self):
        """Test 7-day date range creation"""
        date_range = AnalyticsDateRange.from_time_range(TimeRange.LAST_7_DAYS)
        
        assert date_range.range_type == TimeRange.LAST_7_DAYS
        assert date_range.end_date.date() == datetime(2024, 3, 15).date()
        assert date_range.start_date.date() == datetime(2024, 3, 8).date()
        assert (date_range.end_date - date_range.start_date).days == 7

    @freeze_time("2024-03-15 12:00:00")
    def test_from_time_range_last_30_days(self):
        """Test 30-day date range creation"""
        date_range = AnalyticsDateRange.from_time_range(TimeRange.LAST_30_DAYS)
        
        assert date_range.range_type == TimeRange.LAST_30_DAYS
        assert (date_range.end_date - date_range.start_date).days == 30

    @freeze_time("2024-03-15 12:00:00")
    def test_from_time_range_year_to_date(self):
        """Test year-to-date range creation"""
        date_range = AnalyticsDateRange.from_time_range(TimeRange.YEAR_TO_DATE)
        
        assert date_range.range_type == TimeRange.YEAR_TO_DATE
        assert date_range.start_date.date() == datetime(2024, 1, 1).date()
        assert date_range.end_date.date() == datetime(2024, 3, 15).date()

    def test_custom_date_range(self):
        """Test custom date range creation"""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 2, 1)
        
        date_range = AnalyticsDateRange.from_time_range(
            TimeRange.CUSTOM, 
            custom_start=start, 
            custom_end=end
        )
        
        assert date_range.range_type == TimeRange.CUSTOM
        assert date_range.start_date == start
        assert date_range.end_date == end

    def test_custom_date_range_missing_dates(self):
        """Test custom date range without required dates"""
        with pytest.raises(ValidationException, match="Custom date range requires start and end dates"):
            AnalyticsDateRange.from_time_range(TimeRange.CUSTOM)

class TestAnalyticsCache:
    """Test Redis caching functionality"""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        with patch('app.services.analytics_engine.redis') as mock_redis_module:
            mock_client = Mock()
            mock_redis_module.from_url.return_value = mock_client
            yield mock_client

    def test_cache_initialization_success(self, mock_redis):
        """Test successful cache initialization"""
        mock_redis.ping.return_value = True
        
        cache = AnalyticsCache()
        
        assert cache.redis_client == mock_redis
        assert cache.cache_prefix == "fingood:analytics"
        assert cache.default_ttl == 3600

    def test_cache_initialization_failure(self, mock_redis):
        """Test cache initialization failure"""
        mock_redis.ping.side_effect = Exception("Redis connection failed")
        
        cache = AnalyticsCache()
        
        assert cache.redis_client is None

    @pytest.mark.asyncio
    async def test_cache_get_hit(self, mock_redis):
        """Test cache hit scenario"""
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = '{"data": {"test": "value"}, "cached_at": "2024-03-15T12:00:00"}'
        
        cache = AnalyticsCache()
        result = await cache.get(123, "test_operation", param1="value1")
        
        assert result is not None
        assert result["data"]["test"] == "value"

    @pytest.mark.asyncio
    async def test_cache_get_miss(self, mock_redis):
        """Test cache miss scenario"""
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = None
        
        cache = AnalyticsCache()
        result = await cache.get(123, "test_operation", param1="value1")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_set_success(self, mock_redis):
        """Test successful cache set"""
        mock_redis.ping.return_value = True
        
        cache = AnalyticsCache()
        data = {"test": "value"}
        result = await cache.set(123, "test_operation", data, ttl=1800, param1="value1")
        
        assert result is True
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_invalidate_user_cache(self, mock_redis):
        """Test user cache invalidation"""
        mock_redis.ping.return_value = True
        mock_redis.keys.return_value = ["key1", "key2", "key3"]
        mock_redis.delete.return_value = 3
        
        cache = AnalyticsCache()
        deleted_count = await cache.invalidate_user_cache(123)
        
        assert deleted_count == 3
        mock_redis.keys.assert_called_with("fingood:analytics:user:123:*")
        mock_redis.delete.assert_called_with("key1", "key2", "key3")

class TestKPICalculator:
    """Test KPI calculation functionality"""
    
    @pytest.fixture
    def sample_transactions(self, db_session, sample_user):
        """Create sample transactions for testing"""
        base_date = datetime(2024, 3, 1)
        transactions = []
        
        # Income transactions
        for i in range(5):
            transaction = Transaction(
                user_id=sample_user.id,
                date=base_date + timedelta(days=i*2),
                amount=1000.00 + (i * 100),
                description=f"Income transaction {i+1}",
                vendor=f"Income Source {i+1}",
                category="Salary",
                is_income=True,
                is_categorized=True,
                confidence_score=0.95,
                source="csv"
            )
            transactions.append(transaction)
            db_session.add(transaction)
        
        # Expense transactions
        categories = ["Food", "Transportation", "Utilities", "Entertainment", "Shopping"]
        for i in range(10):
            transaction = Transaction(
                user_id=sample_user.id,
                date=base_date + timedelta(days=i),
                amount=-(50.00 + (i * 25)),  # Negative for expenses
                description=f"Expense transaction {i+1}",
                vendor=f"Vendor {i+1}",
                category=categories[i % len(categories)],
                is_income=False,
                is_categorized=True,
                confidence_score=0.85 + (i * 0.01),
                source="csv"
            )
            transactions.append(transaction)
            db_session.add(transaction)
        
        # Some uncategorized transactions
        for i in range(3):
            transaction = Transaction(
                user_id=sample_user.id,
                date=base_date + timedelta(days=i+15),
                amount=-(25.00 + (i * 10)),
                description=f"Uncategorized expense {i+1}",
                vendor=f"Unknown Vendor {i+1}",
                category=None,
                is_income=False,
                is_categorized=False,
                source="csv"
            )
            transactions.append(transaction)
            db_session.add(transaction)
        
        db_session.commit()
        return transactions

    @pytest.mark.asyncio
    async def test_calculate_cash_flow_summary(self, db_session, sample_user, sample_transactions):
        """Test cash flow summary calculation"""
        cache = Mock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock(return_value=True)
        
        calculator = KPICalculator(db_session, cache)
        date_range = AnalyticsDateRange.from_time_range(TimeRange.LAST_30_DAYS)
        
        result = await calculator.calculate_cash_flow_summary(sample_user.id, date_range)
        
        # Verify structure
        assert "period" in result
        assert "totals" in result
        assert "averages" in result
        assert "counts" in result
        assert "comparisons" in result
        
        # Verify calculations
        assert result["totals"]["total_income"] > 0
        assert result["totals"]["total_expenses"] > 0
        assert result["totals"]["net_cash_flow"] == result["totals"]["total_income"] - result["totals"]["total_expenses"]
        assert result["counts"]["total_transactions"] > 0
        
        # Verify cache was called
        cache.get.assert_called_once()
        cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculate_cash_flow_summary_cached(self, db_session, sample_user):
        """Test cash flow summary with cached data"""
        cached_data = {
            "data": {
                "totals": {"total_income": 5000, "total_expenses": 2000, "net_cash_flow": 3000},
                "cached": True
            }
        }
        
        cache = Mock()
        cache.get = AsyncMock(return_value=cached_data)
        cache.set = AsyncMock()
        
        calculator = KPICalculator(db_session, cache)
        date_range = AnalyticsDateRange.from_time_range(TimeRange.LAST_30_DAYS)
        
        result = await calculator.calculate_cash_flow_summary(sample_user.id, date_range)
        
        assert result["cached"] is True
        assert result["totals"]["total_income"] == 5000
        
        # Verify cache.set was not called (data was cached)
        cache.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_spending_by_category(self, db_session, sample_user, sample_transactions):
        """Test spending by category calculation"""
        cache = Mock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock(return_value=True)
        
        calculator = KPICalculator(db_session, cache)
        date_range = AnalyticsDateRange.from_time_range(TimeRange.LAST_30_DAYS)
        
        result = await calculator.get_spending_by_category(sample_user.id, date_range)
        
        # Verify structure
        assert "period" in result
        assert "summary" in result
        assert "categories" in result
        
        # Verify data
        assert result["summary"]["total_spending"] > 0
        assert len(result["categories"]) > 0
        
        # Verify category data structure
        for category in result["categories"]:
            assert "category" in category
            assert "total_amount" in category
            assert "transaction_count" in category
            assert "percentage" in category

    @pytest.mark.asyncio
    async def test_analyze_vendor_spending(self, db_session, sample_user, sample_transactions):
        """Test vendor spending analysis"""
        cache = Mock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock(return_value=True)
        
        calculator = KPICalculator(db_session, cache)
        date_range = AnalyticsDateRange.from_time_range(TimeRange.LAST_30_DAYS)
        
        result = await calculator.analyze_vendor_spending(sample_user.id, date_range)
        
        # Verify structure
        assert "period" in result
        assert "summary" in result
        assert "vendors" in result
        
        # Verify data
        assert result["summary"]["unique_vendors"] > 0
        assert len(result["vendors"]) > 0
        
        # Verify vendor data structure
        for vendor in result["vendors"]:
            assert "vendor" in vendor
            assert "total_amount" in vendor
            assert "transaction_count" in vendor
            assert "frequency_per_day" in vendor

    @pytest.mark.asyncio
    async def test_kpi_calculator_with_no_transactions(self, db_session, sample_user):
        """Test KPI calculator with user having no transactions"""
        cache = Mock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock(return_value=True)
        
        calculator = KPICalculator(db_session, cache)
        date_range = AnalyticsDateRange.from_time_range(TimeRange.LAST_30_DAYS)
        
        result = await calculator.calculate_cash_flow_summary(sample_user.id, date_range)
        
        # Should handle zero transactions gracefully
        assert result["totals"]["total_income"] == 0
        assert result["totals"]["total_expenses"] == 0
        assert result["totals"]["net_cash_flow"] == 0
        assert result["counts"]["total_transactions"] == 0

class TestTimeSeriesAnalyzer:
    """Test time-series analysis functionality"""
    
    @pytest.fixture
    def time_series_transactions(self, db_session, sample_user):
        """Create transactions spanning multiple months for time-series testing"""
        transactions = []
        base_date = datetime(2024, 1, 1)
        
        # Create transactions for 6 months
        for month in range(6):
            month_start = base_date.replace(month=month+1)
            
            # Monthly income (increasing trend)
            income_amount = 3000 + (month * 200)  # Growing income
            income_tx = Transaction(
                user_id=sample_user.id,
                date=month_start + timedelta(days=1),
                amount=income_amount,
                description=f"Monthly salary {month+1}",
                vendor="Employer",
                category="Salary",
                is_income=True,
                is_categorized=True,
                source="csv"
            )
            transactions.append(income_tx)
            db_session.add(income_tx)
            
            # Monthly expenses (varying amounts)
            expense_amounts = [500, 600, 450, 700, 550, 650]  # Realistic variation
            expense_tx = Transaction(
                user_id=sample_user.id,
                date=month_start + timedelta(days=15),
                amount=-expense_amounts[month],
                description=f"Monthly expenses {month+1}",
                vendor=f"Expense Vendor {month+1}",
                category="Living Expenses",
                is_income=False,
                is_categorized=True,
                source="csv"
            )
            transactions.append(expense_tx)
            db_session.add(expense_tx)
        
        db_session.commit()
        return transactions

    @pytest.mark.asyncio
    async def test_get_monthly_trends(self, db_session, sample_user, time_series_transactions):
        """Test monthly trends calculation"""
        cache = Mock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock(return_value=True)
        
        analyzer = TimeSeriesAnalyzer(db_session, cache)
        date_range = AnalyticsDateRange.from_time_range(TimeRange.LAST_6_MONTHS)
        
        result = await analyzer.get_monthly_trends(sample_user.id, date_range)
        
        # Verify structure
        assert "period" in result
        assert "summary" in result
        assert "monthly_data" in result
        
        # Verify data
        assert result["period"]["total_months"] > 0
        assert len(result["monthly_data"]) > 0
        assert result["summary"]["total_income"] > 0
        
        # Verify monthly data structure
        for month_data in result["monthly_data"]:
            assert "year" in month_data
            assert "month" in month_data
            assert "income" in month_data
            assert "expenses" in month_data
            assert "net_flow" in month_data
            assert "transaction_count" in month_data

    @pytest.mark.asyncio
    async def test_monthly_trends_with_growth_calculation(self, db_session, sample_user, time_series_transactions):
        """Test monthly trends with growth rate calculation"""
        cache = Mock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock(return_value=True)
        
        analyzer = TimeSeriesAnalyzer(db_session, cache)
        date_range = AnalyticsDateRange.from_time_range(TimeRange.LAST_6_MONTHS)
        
        result = await analyzer.get_monthly_trends(sample_user.id, date_range)
        
        # Check that growth calculations are present for months after the first
        monthly_data = result["monthly_data"]
        if len(monthly_data) > 1:
            for i in range(1, len(monthly_data)):
                month = monthly_data[i]
                assert "growth" in month
                assert "income_growth" in month["growth"]
                assert "expense_growth" in month["growth"]

    def test_calculate_trend_increasing(self):
        """Test trend calculation for increasing values"""
        analyzer = TimeSeriesAnalyzer(None, None)
        values = [100, 120, 140, 160, 180]  # Clear increasing trend
        
        trend = analyzer._calculate_trend(values)
        
        assert trend == "increasing"

    def test_calculate_trend_decreasing(self):
        """Test trend calculation for decreasing values"""
        analyzer = TimeSeriesAnalyzer(None, None)
        values = [180, 160, 140, 120, 100]  # Clear decreasing trend
        
        trend = analyzer._calculate_trend(values)
        
        assert trend == "decreasing"

    def test_calculate_trend_stable(self):
        """Test trend calculation for stable values"""
        analyzer = TimeSeriesAnalyzer(None, None)
        values = [100, 102, 98, 101, 99]  # Relatively stable
        
        trend = analyzer._calculate_trend(values)
        
        assert trend == "stable"

class TestChartDataFormatter:
    """Test chart data formatting functionality"""
    
    def test_format_cash_flow_chart(self):
        """Test cash flow chart formatting"""
        cash_flow_data = {
            "totals": {
                "total_income": 5000.0,
                "total_expenses": 2000.0,
                "net_cash_flow": 3000.0
            },
            "counts": {
                "income_transactions": 5,
                "expense_transactions": 10,
                "total_transactions": 15
            },
            "period": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
            "comparisons": {"previous_period": {}}
        }
        
        chart_data = ChartDataFormatter.format_cash_flow_chart(cash_flow_data)
        
        assert chart_data.chart_type == ChartType.BAR
        assert chart_data.title == "Cash Flow Summary"
        assert len(chart_data.data_points) == 3
        assert chart_data.x_axis_label == "Type"
        assert chart_data.y_axis_label == "Amount ($)"
        
        # Verify data points
        labels = [dp.label for dp in chart_data.data_points]
        assert "Income" in labels
        assert "Expenses" in labels
        assert "Net Flow" in labels

    def test_format_category_spending_chart(self):
        """Test category spending chart formatting"""
        category_data = {
            "categories": [
                {"category": "Food", "total_amount": 800.0, "percentage": 40.0, "transaction_count": 10},
                {"category": "Transport", "total_amount": 600.0, "percentage": 30.0, "transaction_count": 8},
                {"category": "Entertainment", "total_amount": 400.0, "percentage": 20.0, "transaction_count": 5}
            ],
            "period": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
            "summary": {"total_spending": 2000.0}
        }
        
        chart_data = ChartDataFormatter.format_category_spending_chart(category_data)
        
        assert chart_data.chart_type == ChartType.PIE
        assert chart_data.title == "Spending by Category"
        assert len(chart_data.data_points) == 3
        
        # Verify data points have required metadata
        for dp in chart_data.data_points:
            assert "percentage" in dp.metadata
            assert "transaction_count" in dp.metadata

    def test_format_monthly_trends_chart(self):
        """Test monthly trends chart formatting"""
        trends_data = {
            "monthly_data": [
                {
                    "month_name": "January 2024",
                    "date": "2024-01-01T00:00:00",
                    "net_flow": 2500.0,
                    "income": 3000.0,
                    "expenses": 500.0,
                    "transaction_count": 15
                },
                {
                    "month_name": "February 2024",
                    "date": "2024-02-01T00:00:00",
                    "net_flow": 2800.0,
                    "income": 3200.0,
                    "expenses": 400.0,
                    "transaction_count": 18
                }
            ],
            "period": {"start_date": "2024-01-01", "end_date": "2024-02-29"},
            "summary": {"income_trend": "increasing"}
        }
        
        chart_data = ChartDataFormatter.format_monthly_trends_chart(trends_data)
        
        assert chart_data.chart_type == ChartType.LINE
        assert chart_data.title == "Monthly Cash Flow Trends"
        assert len(chart_data.data_points) == 2
        assert chart_data.x_axis_label == "Month"
        assert chart_data.y_axis_label == "Net Cash Flow ($)"
        
        # Verify data points have dates
        for dp in chart_data.data_points:
            assert dp.date is not None
            assert isinstance(dp.date, datetime)

class TestAnalyticsEngine:
    """Test main analytics engine functionality"""
    
    @pytest.mark.asyncio
    async def test_get_complete_analytics_summary(self, db_session, sample_user, sample_transactions):
        """Test complete analytics summary generation"""
        engine = AnalyticsEngine(db_session)
        
        # Mock the cache to avoid Redis dependency in tests
        with patch.object(engine.cache, 'get', new=AsyncMock(return_value=None)), \
             patch.object(engine.cache, 'set', new=AsyncMock(return_value=True)):
            
            summary = await engine.get_complete_analytics_summary(
                sample_user.id, 
                TimeRange.LAST_30_DAYS
            )
        
        # Verify summary structure
        assert isinstance(summary, AnalyticsSummary)
        assert len(summary.kpis) > 0
        assert len(summary.charts) > 0
        assert summary.date_range is not None
        assert summary.generated_at is not None
        
        # Verify KPIs
        kpi_names = [kpi.name for kpi in summary.kpis]
        assert "Total Income" in kpi_names
        assert "Total Expenses" in kpi_names
        assert "Net Cash Flow" in kpi_names
        assert "Categorization Rate" in kpi_names
        
        # Verify charts
        chart_titles = [chart.title for chart in summary.charts]
        assert "Cash Flow Summary" in chart_titles
        assert "Spending by Category" in chart_titles
        assert "Monthly Cash Flow Trends" in chart_titles

    @pytest.mark.asyncio
    async def test_analytics_summary_with_invalid_user(self, db_session):
        """Test analytics summary with non-existent user"""
        engine = AnalyticsEngine(db_session)
        
        with pytest.raises(ValidationException, match="User 99999 not found"):
            await engine.get_complete_analytics_summary(99999, TimeRange.LAST_30_DAYS)

    @pytest.mark.asyncio
    async def test_analytics_summary_with_custom_date_range(self, db_session, sample_user, sample_transactions):
        """Test analytics summary with custom date range"""
        engine = AnalyticsEngine(db_session)
        
        start_date = datetime(2024, 3, 1)
        end_date = datetime(2024, 3, 15)
        
        with patch.object(engine.cache, 'get', new=AsyncMock(return_value=None)), \
             patch.object(engine.cache, 'set', new=AsyncMock(return_value=True)):
            
            summary = await engine.get_complete_analytics_summary(
                sample_user.id,
                TimeRange.CUSTOM,
                custom_start=start_date,
                custom_end=end_date
            )
        
        assert summary.date_range.range_type == TimeRange.CUSTOM
        assert summary.date_range.start_date == start_date
        assert summary.date_range.end_date == end_date

    def test_get_change_direction(self, db_session):
        """Test change direction calculation"""
        engine = AnalyticsEngine(db_session)
        
        assert engine._get_change_direction(5.0) == "up"
        assert engine._get_change_direction(-5.0) == "down"
        assert engine._get_change_direction(0.5) == "neutral"
        assert engine._get_change_direction(None) is None

    @pytest.mark.asyncio
    async def test_invalidate_user_analytics_cache(self, db_session, sample_user):
        """Test user cache invalidation"""
        engine = AnalyticsEngine(db_session)
        
        with patch.object(engine.cache, 'invalidate_user_cache', new=AsyncMock(return_value=5)):
            deleted_count = await engine.invalidate_user_analytics_cache(sample_user.id)
            
            assert deleted_count == 5
            engine.cache.invalidate_user_cache.assert_called_once_with(sample_user.id)

    @pytest.mark.asyncio
    async def test_get_categorization_quality_metrics(self, db_session, sample_user, sample_transactions):
        """Test categorization quality metrics calculation"""
        engine = AnalyticsEngine(db_session)
        date_range = AnalyticsDateRange.from_time_range(TimeRange.LAST_30_DAYS)
        
        result = await engine.get_categorization_quality_metrics(sample_user.id, date_range)
        
        # Verify structure
        assert "period" in result
        assert "summary" in result
        assert "confidence_metrics" in result
        
        # Verify data
        assert result["summary"]["total_transactions"] > 0
        assert result["summary"]["categorization_rate"] >= 0
        assert "avg_confidence" in result["confidence_metrics"]

class TestAnalyticsEngineErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_kpi_calculator_database_error(self, sample_user):
        """Test KPI calculator with database error"""
        # Mock database session that raises an exception
        mock_db = Mock()
        mock_db.query.side_effect = Exception("Database connection error")
        
        cache = Mock()
        cache.get = AsyncMock(return_value=None)
        
        calculator = KPICalculator(mock_db, cache)
        date_range = AnalyticsDateRange.from_time_range(TimeRange.LAST_30_DAYS)
        
        with pytest.raises(SystemException, match="Failed to calculate cash flow summary"):
            await calculator.calculate_cash_flow_summary(sample_user.id, date_range)

    @pytest.mark.asyncio
    async def test_analytics_engine_with_redis_failure(self, db_session, sample_user):
        """Test analytics engine with Redis connection failure"""
        # Create engine with failed Redis connection
        engine = AnalyticsEngine(db_session)
        engine.cache.redis_client = None  # Simulate Redis failure
        
        # Should still work without caching
        with patch.object(engine.kpi_calculator, 'calculate_cash_flow_summary') as mock_cash_flow, \
             patch.object(engine.kpi_calculator, 'get_spending_by_category') as mock_category, \
             patch.object(engine.kpi_calculator, 'analyze_vendor_spending') as mock_vendor, \
             patch.object(engine.time_series_analyzer, 'get_monthly_trends') as mock_trends:
            
            # Mock return values
            mock_cash_flow.return_value = {
                "totals": {"total_income": 5000, "total_expenses": 2000, "net_cash_flow": 3000},
                "counts": {"income_transactions": 5, "expense_transactions": 10, "total_transactions": 15},
                "period": {},
                "comparisons": {"percentage_changes": {"income_change": None, "expense_change": None, "net_change": None}},
                "averages": {}
            }
            mock_category.return_value = {"summary": {"categorization_rate": 85, "category_count": 5}, "categories": []}
            mock_vendor.return_value = {"summary": {"unique_vendors": 10, "avg_spending_per_vendor": 200}}
            mock_trends.return_value = {"monthly_data": [], "summary": {}}
            
            summary = await engine.get_complete_analytics_summary(sample_user.id, TimeRange.LAST_30_DAYS)
            
            assert summary is not None
            assert summary.cache_info["cache_enabled"] is False

class TestAnalyticsEngineUserIsolation:
    """Test user data isolation in analytics"""
    
    @pytest.fixture
    def multi_user_transactions(self, db_session):
        """Create transactions for multiple users"""
        # Create two users
        user1 = User(email="user1@test.com", hashed_password="hashed")
        user2 = User(email="user2@test.com", hashed_password="hashed")
        db_session.add(user1)
        db_session.add(user2)
        db_session.commit()
        
        # Create transactions for user1
        for i in range(5):
            tx1 = Transaction(
                user_id=user1.id,
                date=datetime(2024, 3, i+1),
                amount=1000.0,
                description=f"User1 transaction {i+1}",
                is_income=True,
                is_categorized=True,
                source="csv"
            )
            db_session.add(tx1)
        
        # Create transactions for user2
        for i in range(3):
            tx2 = Transaction(
                user_id=user2.id,
                date=datetime(2024, 3, i+1),
                amount=500.0,
                description=f"User2 transaction {i+1}",
                is_income=True,
                is_categorized=True,
                source="csv"
            )
            db_session.add(tx2)
        
        db_session.commit()
        return user1, user2

    @pytest.mark.asyncio
    async def test_user_data_isolation(self, db_session, multi_user_transactions):
        """Test that users only see their own data in analytics"""
        user1, user2 = multi_user_transactions
        
        engine = AnalyticsEngine(db_session)
        
        with patch.object(engine.cache, 'get', new=AsyncMock(return_value=None)), \
             patch.object(engine.cache, 'set', new=AsyncMock(return_value=True)):
            
            # Get analytics for both users
            summary1 = await engine.get_complete_analytics_summary(user1.id, TimeRange.LAST_30_DAYS)
            summary2 = await engine.get_complete_analytics_summary(user2.id, TimeRange.LAST_30_DAYS)
            
            # User1 should have higher income (5 transactions of $1000 each)
            user1_income = next(kpi for kpi in summary1.kpis if kpi.name == "Total Income")
            user2_income = next(kpi for kpi in summary2.kpis if kpi.name == "Total Income")
            
            assert user1_income.value == 5000.0  # 5 * $1000
            assert user2_income.value == 1500.0  # 3 * $500
            
            # Verify complete isolation
            assert user1_income.value != user2_income.value

class TestAnalyticsEnginePerformance:
    """Test performance aspects of analytics engine"""
    
    @pytest.fixture
    def large_transaction_dataset(self, db_session, sample_user):
        """Create a large dataset for performance testing"""
        transactions = []
        base_date = datetime(2024, 1, 1)
        
        # Create 1000 transactions over 30 days
        for i in range(1000):
            transaction = Transaction(
                user_id=sample_user.id,
                date=base_date + timedelta(days=i % 30),
                amount=100.0 + (i % 500),
                description=f"Transaction {i+1}",
                vendor=f"Vendor {i % 50}",  # 50 different vendors
                category=f"Category {i % 10}",  # 10 different categories
                is_income=i % 5 == 0,  # Every 5th transaction is income
                is_categorized=True,
                confidence_score=0.8 + (i % 20) * 0.01,
                source="csv"
            )
            transactions.append(transaction)
            db_session.add(transaction)
        
        db_session.commit()
        return transactions

    @pytest.mark.asyncio
    async def test_analytics_performance_with_large_dataset(self, db_session, sample_user, large_transaction_dataset):
        """Test analytics performance with large transaction dataset"""
        engine = AnalyticsEngine(db_session)
        
        with patch.object(engine.cache, 'get', new=AsyncMock(return_value=None)), \
             patch.object(engine.cache, 'set', new=AsyncMock(return_value=True)):
            
            start_time = datetime.now()
            
            summary = await engine.get_complete_analytics_summary(
                sample_user.id, 
                TimeRange.LAST_30_DAYS
            )
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Performance assertion - should complete within reasonable time
            assert execution_time < 5.0  # Should complete in under 5 seconds
            assert summary is not None
            assert len(summary.kpis) > 0
            assert len(summary.charts) > 0

    @pytest.mark.asyncio
    async def test_cache_performance_benefit(self, db_session, sample_user, large_transaction_dataset):
        """Test that caching provides performance benefits"""
        engine = AnalyticsEngine(db_session)
        
        # First call - no cache
        with patch.object(engine.cache, 'get', new=AsyncMock(return_value=None)), \
             patch.object(engine.cache, 'set', new=AsyncMock(return_value=True)):
            
            start_time = datetime.now()
            await engine.get_complete_analytics_summary(sample_user.id, TimeRange.LAST_30_DAYS)
            first_call_time = (datetime.now() - start_time).total_seconds()
        
        # Second call - with cache
        cached_cash_flow = {"data": {"totals": {"total_income": 5000, "total_expenses": 2000, "net_cash_flow": 3000}}}
        cached_category = {"data": {"summary": {"categorization_rate": 85}, "categories": []}}
        cached_vendor = {"data": {"summary": {"unique_vendors": 10}, "vendors": []}}
        cached_trends = {"data": {"monthly_data": [], "summary": {}}}
        
        cache_responses = [cached_cash_flow, cached_category, cached_vendor, cached_trends]
        
        with patch.object(engine.cache, 'get', new=AsyncMock(side_effect=cache_responses)):
            start_time = datetime.now()
            await engine.get_complete_analytics_summary(sample_user.id, TimeRange.LAST_30_DAYS)
            cached_call_time = (datetime.now() - start_time).total_seconds()
        
        # Cached call should be significantly faster
        assert cached_call_time < first_call_time * 0.5  # At least 50% faster with cache

if __name__ == "__main__":
    pytest.main([__file__, "-v"])