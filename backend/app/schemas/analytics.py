"""
Enhanced Analytics Schemas for FinGood
Comprehensive data models for business intelligence and financial analysis endpoints.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from decimal import Decimal
from enum import Enum

class PeriodType(str, Enum):
    """Supported period types for analytics"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class TrendDirection(str, Enum):
    """Trend direction indicators"""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"

class RiskLevel(str, Enum):
    """Risk levels for anomaly detection"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class AnalyticsConfig(BaseModel):
    """Configuration for analytics queries"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    start_date: datetime = Field(..., description="Analysis start date")
    end_date: datetime = Field(..., description="Analysis end date")
    period: Optional[PeriodType] = Field(None, description="Aggregation period")
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, values):
        """Ensure end date is after start date"""
        if 'start_date' in values and v < values['start_date']:
            raise ValueError("End date must be after start date")
        return v

# Cash Flow Analysis Models

class CashFlowPeriod(BaseModel):
    """Cash flow data for a specific period"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    period: datetime = Field(..., description="Period start date")
    income: Decimal = Field(..., description="Total income for period")
    expenses: Decimal = Field(..., description="Total expenses for period")
    net_flow: Decimal = Field(..., description="Net cash flow (income - expenses)")
    income_transactions: int = Field(..., ge=0, description="Number of income transactions")
    expense_transactions: int = Field(..., ge=0, description="Number of expense transactions")
    avg_income_transaction: Decimal = Field(..., description="Average income transaction amount")
    avg_expense_transaction: Decimal = Field(..., description="Average expense transaction amount")
    income_moving_avg: Optional[Decimal] = Field(None, description="3-period moving average for income")
    expense_moving_avg: Optional[Decimal] = Field(None, description="3-period moving average for expenses")

class FinancialHealthMetrics(BaseModel):
    """Financial health and stability metrics"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    expense_ratio: Decimal = Field(..., description="Expenses as percentage of income")
    savings_rate: Decimal = Field(..., description="Savings as percentage of income")
    cash_flow_volatility: Optional[Decimal] = Field(None, description="Standard deviation of net cash flows")
    financial_stability: str = Field(..., description="Overall financial stability assessment")

class CashFlowSummary(BaseModel):
    """Cash flow analysis summary"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    total_income: Decimal = Field(..., description="Total income for period")
    total_expenses: Decimal = Field(..., description="Total expenses for period")
    net_total: Decimal = Field(..., description="Net total (income - expenses)")
    average_income: Decimal = Field(..., description="Average income per period")
    average_expenses: Decimal = Field(..., description="Average expenses per period")
    income_growth_rate: Optional[Decimal] = Field(None, description="Income growth rate percentage")
    expense_growth_rate: Optional[Decimal] = Field(None, description="Expense growth rate percentage")

class CashFlowAnalysis(BaseModel):
    """Complete cash flow analysis response"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    analysis_config: AnalyticsConfig = Field(..., description="Analysis configuration")
    cash_flow_data: List[CashFlowPeriod] = Field(..., description="Period-by-period cash flow data")
    summary: CashFlowSummary = Field(..., description="Overall summary metrics")
    financial_health: FinancialHealthMetrics = Field(..., description="Financial health assessment")

# Category Analysis Models

class MonthlyTrendData(BaseModel):
    """Monthly trend data for a category"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    month: datetime = Field(..., description="Month")
    amount: Decimal = Field(..., description="Total amount for month")
    transaction_count: int = Field(..., ge=0, description="Number of transactions")

class MovingAverageData(BaseModel):
    """Moving average data point"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    month: datetime = Field(..., description="Month")
    moving_avg: Decimal = Field(..., description="Moving average value")

class TrendAnalysis(BaseModel):
    """Trend analysis for a category"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    growth_rate: Optional[Decimal] = Field(None, description="Growth rate percentage")
    seasonal_variance: Optional[Decimal] = Field(None, description="Seasonal variance measure")
    trend_direction: TrendDirection = Field(..., description="Overall trend direction")

class CategoryInsight(BaseModel):
    """Comprehensive insight data for a category"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    total_amount: Decimal = Field(..., description="Total amount spent in category")
    transaction_count: int = Field(..., ge=0, description="Total number of transactions")
    average_transaction: Decimal = Field(..., description="Average transaction amount")
    first_transaction: datetime = Field(..., description="Date of first transaction")
    last_transaction: datetime = Field(..., description="Date of last transaction")
    monthly_data: List[MonthlyTrendData] = Field(..., description="Monthly spending data")
    moving_averages: List[MovingAverageData] = Field(..., description="Moving average data")
    trend_analysis: TrendAnalysis = Field(..., description="Trend analysis results")
    percentage_of_total: Decimal = Field(..., description="Percentage of total spending")

class CategoryInsightsSummary(BaseModel):
    """Summary of category insights analysis"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    total_spending: Decimal = Field(..., description="Total spending across all categories")
    top_category: Optional[str] = Field(None, description="Highest spending category")
    most_frequent_category: Optional[str] = Field(None, description="Category with most transactions")
    average_category_spend: Decimal = Field(..., description="Average spending per category")

class CategoryInsightsResponse(BaseModel):
    """Complete category insights response"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    analysis_config: AnalyticsConfig = Field(..., description="Analysis configuration")
    category_insights: Dict[str, CategoryInsight] = Field(..., description="Insights by category")
    summary: CategoryInsightsSummary = Field(..., description="Overall summary")

# Vendor Analysis Models

class VendorInsight(BaseModel):
    """Comprehensive vendor analysis data"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    vendor: str = Field(..., description="Vendor name")
    total_spent: Decimal = Field(..., description="Total amount spent at vendor")
    transaction_count: int = Field(..., ge=0, description="Number of transactions")
    average_transaction: Decimal = Field(..., description="Average transaction amount")
    min_transaction: Decimal = Field(..., description="Minimum transaction amount")
    max_transaction: Decimal = Field(..., description="Maximum transaction amount")
    first_transaction: datetime = Field(..., description="Date of first transaction")
    last_transaction: datetime = Field(..., description="Date of last transaction")
    primary_category: Optional[str] = Field(None, description="Most common category for vendor")
    transaction_frequency: Decimal = Field(..., description="Average transactions per month")
    spending_consistency: str = Field(..., description="Spending pattern consistency")
    percentage_of_spending: Decimal = Field(..., description="Percentage of total spending")

class SpendingPatterns(BaseModel):
    """Analysis of vendor spending patterns"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    regular_vendors: int = Field(..., ge=0, description="Number of regularly visited vendors")
    occasional_vendors: int = Field(..., ge=0, description="Number of occasionally visited vendors")
    one_time_vendors: int = Field(..., ge=0, description="Number of one-time vendors")
    top_vendor: Optional[str] = Field(None, description="Top spending vendor")
    vendor_concentration: Decimal = Field(..., description="Concentration of spending at top vendor")

class VendorAnalysisSummary(BaseModel):
    """Summary of vendor analysis"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    total_vendor_spending: Decimal = Field(..., description="Total spending at analyzed vendors")
    average_vendor_spend: Decimal = Field(..., description="Average spending per vendor")
    total_unique_vendors: int = Field(..., ge=0, description="Total number of unique vendors")

class VendorAnalysisResponse(BaseModel):
    """Complete vendor analysis response"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    analysis_config: AnalyticsConfig = Field(..., description="Analysis configuration")
    vendor_insights: List[VendorInsight] = Field(..., description="Vendor analysis data")
    spending_patterns: SpendingPatterns = Field(..., description="Spending pattern analysis")
    summary: VendorAnalysisSummary = Field(..., description="Overall summary")

# Anomaly Detection Models

class AnomalyTransaction(BaseModel):
    """Transaction flagged as anomalous"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    transaction_id: int = Field(..., description="Transaction ID")
    date: datetime = Field(..., description="Transaction date")
    amount: Decimal = Field(..., description="Transaction amount")
    description: str = Field(..., description="Transaction description")
    vendor: Optional[str] = Field(None, description="Vendor name")
    category: Optional[str] = Field(None, description="Transaction category")
    anomaly_types: List[str] = Field(..., description="Types of anomalies detected")
    risk_level: RiskLevel = Field(..., description="Risk level assessment")
    anomaly_score: float = Field(..., ge=0, description="Anomaly severity score")
    explanation: str = Field(..., description="Human-readable explanation")

class AnomalySummary(BaseModel):
    """Summary of anomaly detection results"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    total_anomalies: int = Field(..., ge=0, description="Total number of anomalies detected")
    high_risk_count: int = Field(..., ge=0, description="Number of high-risk anomalies")
    medium_risk_count: int = Field(..., ge=0, description="Number of medium-risk anomalies")
    low_risk_count: int = Field(..., ge=0, description="Number of low-risk anomalies")
    anomaly_rate: float = Field(..., ge=0, le=100, description="Percentage of transactions flagged as anomalous")

class AnomalyDetectionResponse(BaseModel):
    """Complete anomaly detection response"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    analysis_config: AnalyticsConfig = Field(..., description="Analysis configuration")
    anomalies: List[AnomalyTransaction] = Field(..., description="Detected anomalous transactions")
    summary: AnomalySummary = Field(..., description="Summary of results")
    recommendations: List[str] = Field(..., description="Actionable recommendations")

# Comparative Analysis Models

class PeriodComparison(BaseModel):
    """Comparison between two periods"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    base: Union[Decimal, int] = Field(..., description="Base period value")
    compare: Union[Decimal, int] = Field(..., description="Comparison period value")
    change_amount: Union[Decimal, int] = Field(..., description="Absolute change")
    change_percent: Decimal = Field(..., description="Percentage change")

class CategoryChange(BaseModel):
    """Category-specific comparison data"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    base_amount: Decimal = Field(..., description="Base period amount")
    compare_amount: Decimal = Field(..., description="Comparison period amount")
    change_amount: Decimal = Field(..., description="Absolute change")
    change_percent: Decimal = Field(..., description="Percentage change")

class ComparativePeriods(BaseModel):
    """Period definitions for comparison"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    base_period: Dict[str, datetime] = Field(..., description="Base period start/end dates")
    compare_period: Dict[str, datetime] = Field(..., description="Comparison period start/end dates")

class ComparisonSummary(BaseModel):
    """Summary of comparative analysis"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    income: PeriodComparison = Field(..., description="Income comparison")
    expenses: PeriodComparison = Field(..., description="Expense comparison")
    transactions: PeriodComparison = Field(..., description="Transaction count comparison")

class ComparisonInsights(BaseModel):
    """Insights from comparative analysis"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    income_trend: TrendDirection = Field(..., description="Income trend direction")
    expense_trend: TrendDirection = Field(..., description="Expense trend direction")
    biggest_increase: Optional[str] = Field(None, description="Category with biggest increase")
    biggest_decrease: Optional[str] = Field(None, description="Category with biggest decrease")

class ComparativeAnalysisResponse(BaseModel):
    """Complete comparative analysis response"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    periods: ComparativePeriods = Field(..., description="Period definitions")
    summary_comparison: ComparisonSummary = Field(..., description="High-level comparisons")
    category_comparison: Dict[str, CategoryChange] = Field(..., description="Category-level comparisons")
    insights: ComparisonInsights = Field(..., description="Analysis insights")

# Dashboard Data Models

class KPIMetric(BaseModel):
    """Key Performance Indicator metric"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    value: Decimal = Field(..., description="Current metric value")
    previous_value: Optional[Decimal] = Field(None, description="Previous period value")
    change_percent: Optional[Decimal] = Field(None, description="Percentage change")
    trend: Optional[TrendDirection] = Field(None, description="Trend direction")
    target: Optional[Decimal] = Field(None, description="Target value")
    status: Optional[str] = Field(None, description="Status indicator")

class DashboardChart(BaseModel):
    """Chart data for dashboard visualization"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    chart_type: str = Field(..., description="Type of chart")
    title: str = Field(..., description="Chart title")
    data: List[Dict[str, Any]] = Field(..., description="Chart data points")
    config: Optional[Dict[str, Any]] = Field(None, description="Chart configuration")

class DashboardAlerts(BaseModel):
    """Dashboard alerts and notifications"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    budget_alerts: List[str] = Field(default=[], description="Budget-related alerts")
    anomaly_alerts: List[str] = Field(default=[], description="Anomaly detection alerts")
    trend_alerts: List[str] = Field(default=[], description="Trend-based alerts")
    goal_alerts: List[str] = Field(default=[], description="Goal tracking alerts")

class DashboardData(BaseModel):
    """Comprehensive dashboard data"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    period: AnalyticsConfig = Field(..., description="Dashboard period configuration")
    kpis: Dict[str, KPIMetric] = Field(..., description="Key performance indicators")
    charts: List[DashboardChart] = Field(..., description="Dashboard charts")
    quick_stats: Dict[str, Union[str, int, Decimal]] = Field(..., description="Quick statistics")
    alerts: DashboardAlerts = Field(..., description="Dashboard alerts")
    last_updated: datetime = Field(..., description="Last update timestamp")

# Trend Analysis and Forecasting Models

class TrendDataPoint(BaseModel):
    """Single data point in trend analysis"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    period: datetime = Field(..., description="Period date")
    actual_value: Decimal = Field(..., description="Actual value")
    trend_value: Optional[Decimal] = Field(None, description="Trend line value")
    forecast_value: Optional[Decimal] = Field(None, description="Forecasted value")
    confidence_interval: Optional[Dict[str, Decimal]] = Field(None, description="Forecast confidence interval")

class ForecastMetrics(BaseModel):
    """Forecast quality and reliability metrics"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    accuracy_score: Optional[Decimal] = Field(None, ge=0, le=100, description="Forecast accuracy percentage")
    confidence_level: Optional[Decimal] = Field(None, ge=0, le=100, description="Confidence level")
    trend_strength: Optional[Decimal] = Field(None, description="Strength of trend")
    seasonality_detected: bool = Field(default=False, description="Whether seasonality was detected")
    forecast_horizon: int = Field(..., ge=1, description="Number of periods forecasted")

class TrendAnalysisResponse(BaseModel):
    """Complete trend analysis and forecasting response"""
    model_config = ConfigDict(json_encoders={Decimal: str})
    
    analysis_config: AnalyticsConfig = Field(..., description="Analysis configuration")
    trend_data: List[TrendDataPoint] = Field(..., description="Historical and forecasted data")
    forecast_metrics: ForecastMetrics = Field(..., description="Forecast quality metrics")
    insights: List[str] = Field(..., description="Key insights from trend analysis")
    recommendations: List[str] = Field(..., description="Actionable recommendations")