"""
Cash Flow Forecasting Engine

Advanced ML-based forecasting system for predicting future cash flows,
seasonal patterns, and financial trends with confidence intervals.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import json
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
import os

from app.models.transaction import Transaction
from app.models.user import User
from app.core.exceptions import ValidationException, BusinessLogicException
from app.core.security_utils import input_sanitizer
from app.core.audit_logger import security_audit_logger
from app.services.analytics_engine import AnalyticsEngine


class ForecastHorizon(Enum):
    """Forecast time horizons"""
    WEEKLY = "7_days"
    MONTHLY = "30_days"
    BIMONTHLY = "60_days"
    QUARTERLY = "90_days"
    CUSTOM = "custom"


class ForecastType(Enum):
    """Types of forecasts"""
    CASH_FLOW = "cash_flow"
    REVENUE = "revenue"
    EXPENSES = "expenses"
    NET_INCOME = "net_income"
    CATEGORY_SPECIFIC = "category_specific"


class SeasonalPattern(Enum):
    """Seasonal pattern types"""
    NONE = "none"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class TrendDirection(Enum):
    """Trend directions"""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"


@dataclass
class ForecastResult:
    """Forecast result data structure"""
    forecast_id: str
    user_id: int
    forecast_type: str
    horizon_days: int
    predictions: List[Dict[str, Any]]  # [{date, value, confidence_lower, confidence_upper}]
    confidence_score: float
    seasonal_pattern: str
    trend_direction: str
    model_accuracy: float
    created_at: datetime
    metadata: Dict[str, Any]


@dataclass
class SeasonalAnalysis:
    """Seasonal analysis results"""
    pattern_type: str
    strength: float  # 0-1
    period_days: int
    seasonal_factors: Dict[str, float]
    confidence: float


@dataclass
class TrendAnalysis:
    """Trend analysis results"""
    direction: str
    strength: float  # 0-1 
    slope: float
    volatility: float
    trend_confidence: float


class ForecastingLimits:
    """Forecasting operation limits"""
    MAX_FORECAST_DAYS = 365
    MIN_HISTORICAL_DAYS = 30
    MAX_TRANSACTIONS_ANALYZE = 50000
    MIN_CONFIDENCE_THRESHOLD = 0.3
    MAX_FORECASTS_PER_USER = 100


class ForecastingEngine:
    """Advanced cash flow forecasting engine with ML capabilities"""
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.analytics = AnalyticsEngine(db)
        self.scaler = StandardScaler()
        self.models_cache = {}
        
    def generate_forecast(
        self,
        user_id: int,
        forecast_type: ForecastType,
        horizon: ForecastHorizon,
        custom_days: Optional[int] = None,
        category_filter: Optional[str] = None
    ) -> ForecastResult:
        """Generate comprehensive forecast with confidence intervals"""
        try:
            # Validate inputs
            self._validate_forecast_request(user_id, forecast_type, horizon, custom_days)
            
            # Get horizon days
            horizon_days = self._get_horizon_days(horizon, custom_days)
            
            # Load historical data
            historical_data = self._load_historical_data(
                user_id, forecast_type, category_filter, horizon_days
            )
            
            if len(historical_data) < ForecastingLimits.MIN_HISTORICAL_DAYS:
                raise ValidationException(
                    f"Insufficient historical data. Need at least {ForecastingLimits.MIN_HISTORICAL_DAYS} days"
                )
            
            # Perform seasonal analysis
            seasonal_analysis = self._analyze_seasonality(historical_data)
            
            # Perform trend analysis  
            trend_analysis = self._analyze_trends(historical_data)
            
            # Generate predictions
            predictions = self._generate_predictions(
                historical_data, horizon_days, seasonal_analysis, trend_analysis
            )
            
            # Calculate model accuracy
            accuracy = self._calculate_model_accuracy(historical_data)
            
            # Create forecast result
            forecast_result = ForecastResult(
                forecast_id=f"forecast_{user_id}_{int(datetime.utcnow().timestamp())}",
                user_id=user_id,
                forecast_type=forecast_type.value,
                horizon_days=horizon_days,
                predictions=predictions,
                confidence_score=self._calculate_overall_confidence(
                    seasonal_analysis, trend_analysis, accuracy
                ),
                seasonal_pattern=seasonal_analysis.pattern_type,
                trend_direction=trend_analysis.direction,
                model_accuracy=accuracy,
                created_at=datetime.utcnow(),
                metadata={
                    "seasonal_strength": seasonal_analysis.strength,
                    "trend_strength": trend_analysis.strength,
                    "volatility": trend_analysis.volatility,
                    "data_points": len(historical_data),
                    "category_filter": category_filter
                }
            )
            
            # Store forecast
            self._store_forecast(forecast_result)
            
            # Audit log
            security_audit_logger.log_forecast_generation(
                user_id=user_id,
                forecast_type=forecast_type.value,
                timeframe=f"{horizon_days}_days",
                result="success",
                processing_time=None
            )
            
            return forecast_result
            
        except Exception as e:
            self.logger.error(f"Forecast generation failed for user {user_id}: {str(e)}")
            raise BusinessLogicException(
                message=f"Failed to generate forecast: {str(e)}", 
                code="FORECAST_GENERATION_ERROR"
            )
    
    def _validate_forecast_request(
        self,
        user_id: int,
        forecast_type: ForecastType,
        horizon: ForecastHorizon,
        custom_days: Optional[int]
    ) -> None:
        """Validate forecast request parameters"""
        if horizon == ForecastHorizon.CUSTOM and not custom_days:
            raise ValidationException("Custom days required for custom horizon")
            
        if custom_days and custom_days > ForecastingLimits.MAX_FORECAST_DAYS:
            raise ValidationException(
                f"Forecast horizon cannot exceed {ForecastingLimits.MAX_FORECAST_DAYS} days"
            )
    
    def _get_horizon_days(self, horizon: ForecastHorizon, custom_days: Optional[int]) -> int:
        """Get number of days for forecast horizon"""
        if horizon == ForecastHorizon.CUSTOM:
            return custom_days or 30
        
        horizon_map = {
            ForecastHorizon.WEEKLY: 7,
            ForecastHorizon.MONTHLY: 30,
            ForecastHorizon.BIMONTHLY: 60,
            ForecastHorizon.QUARTERLY: 90
        }
        
        return horizon_map.get(horizon, 30)
    
    def _load_historical_data(
        self,
        user_id: int,
        forecast_type: ForecastType,
        category_filter: Optional[str],
        horizon_days: int
    ) -> pd.DataFrame:
        """Load and prepare historical transaction data"""
        # Load historical data (at least 3x the forecast horizon)
        # For demo purposes, use 2 years of data to work with historical samples
        lookback_days = max(730, horizon_days * 3)  # 2 years or 3x horizon
        start_date = datetime.utcnow() - timedelta(days=lookback_days)
        
        query = (
            self.db.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .filter(Transaction.date >= start_date)
            .order_by(Transaction.date)
        )
        
        if category_filter:
            query = query.filter(Transaction.category == category_filter)
        
        transactions = query.limit(ForecastingLimits.MAX_TRANSACTIONS_ANALYZE).all()
        
        # Convert to DataFrame for time series analysis
        data = []
        for txn in transactions:
            amount = float(txn.amount)
            if forecast_type == ForecastType.REVENUE and amount < 0:
                continue
            elif forecast_type == ForecastType.EXPENSES and amount > 0:
                continue
            elif forecast_type == ForecastType.NET_INCOME:
                amount = amount  # Keep as-is
            elif forecast_type == ForecastType.CASH_FLOW:
                amount = amount  # Keep as-is
            
            data.append({
                'date': txn.date,
                'amount': amount,
                'category': txn.category,
                'description': txn.description
            })
        
        df = pd.DataFrame(data)
        if df.empty:
            return df
            
        # Aggregate by day
        df['date'] = pd.to_datetime(df['date'])
        daily_data = df.groupby('date')['amount'].sum().reset_index()
        
        # Fill missing dates with zero
        date_range = pd.date_range(start=daily_data['date'].min(), 
                                 end=daily_data['date'].max(), 
                                 freq='D')
        daily_data = daily_data.set_index('date').reindex(date_range, fill_value=0).reset_index()
        daily_data.columns = ['date', 'amount']
        
        return daily_data
    
    def _analyze_seasonality(self, data: pd.DataFrame) -> SeasonalAnalysis:
        """Analyze seasonal patterns in the data"""
        if len(data) < 14:  # Need at least 2 weeks
            return SeasonalAnalysis(
                pattern_type=SeasonalPattern.NONE.value,
                strength=0.0,
                period_days=0,
                seasonal_factors={},
                confidence=0.0
            )
        
        # Simple seasonal analysis using day of week and day of month
        data['dayofweek'] = pd.to_datetime(data['date']).dt.dayofweek
        data['dayofmonth'] = pd.to_datetime(data['date']).dt.day
        
        # Weekly seasonality
        weekly_means = data.groupby('dayofweek')['amount'].mean()
        weekly_std = data.groupby('dayofweek')['amount'].std()
        weekly_variation = weekly_std.sum() / abs(weekly_means.sum()) if weekly_means.sum() != 0 else 0
        
        # Monthly seasonality (simplified)
        monthly_means = data.groupby('dayofmonth')['amount'].mean()
        monthly_std = data.groupby('dayofmonth')['amount'].std()
        monthly_variation = monthly_std.sum() / abs(monthly_means.sum()) if monthly_means.sum() != 0 else 0
        
        # Determine dominant pattern
        if weekly_variation > monthly_variation and weekly_variation > 0.1:
            pattern_type = SeasonalPattern.WEEKLY.value
            strength = min(weekly_variation, 1.0)
            period_days = 7
            factors = {str(i): float(weekly_means.iloc[i]) for i in range(7)}
        elif monthly_variation > 0.1:
            pattern_type = SeasonalPattern.MONTHLY.value
            strength = min(monthly_variation, 1.0)
            period_days = 30
            factors = {str(i): float(monthly_means.iloc[i]) for i in range(min(31, len(monthly_means)))}
        else:
            pattern_type = SeasonalPattern.NONE.value
            strength = 0.0
            period_days = 0
            factors = {}
        
        confidence = min(strength * 2, 1.0)  # Higher variation = higher confidence in pattern
        
        return SeasonalAnalysis(
            pattern_type=pattern_type,
            strength=strength,
            period_days=period_days,
            seasonal_factors=factors,
            confidence=confidence
        )
    
    def _analyze_trends(self, data: pd.DataFrame) -> TrendAnalysis:
        """Analyze trends in the data"""
        if len(data) < 7:
            return TrendAnalysis(
                direction=TrendDirection.STABLE.value,
                strength=0.0,
                slope=0.0,
                volatility=0.0,
                trend_confidence=0.0
            )
        
        # Calculate trend using linear regression
        x = np.arange(len(data))
        y = data['amount'].values
        
        # Linear regression
        slope, intercept = np.polyfit(x, y, 1)
        
        # Calculate R-squared for trend strength
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Determine trend direction
        if slope > 0.01:
            direction = TrendDirection.INCREASING.value
        elif slope < -0.01:
            direction = TrendDirection.DECREASING.value
        else:
            direction = TrendDirection.STABLE.value
        
        # Calculate volatility
        volatility = np.std(y) / (abs(np.mean(y)) + 1e-6)
        
        # High volatility indicates unstable trend
        if volatility > 1.0:
            direction = TrendDirection.VOLATILE.value
        
        strength = min(abs(r_squared), 1.0)
        trend_confidence = strength * (1 - min(volatility, 1.0))
        
        return TrendAnalysis(
            direction=direction,
            strength=strength,
            slope=float(slope),
            volatility=float(volatility),
            trend_confidence=float(trend_confidence)
        )
    
    def _generate_predictions(
        self,
        data: pd.DataFrame,
        horizon_days: int,
        seasonal_analysis: SeasonalAnalysis,
        trend_analysis: TrendAnalysis
    ) -> List[Dict[str, Any]]:
        """Generate predictions with confidence intervals"""
        if len(data) == 0:
            return []
        
        predictions = []
        last_date = data['date'].max()
        
        # Simple forecasting model combining trend and seasonality
        base_value = data['amount'].tail(7).mean()  # Use last week as base
        
        for day in range(1, horizon_days + 1):
            pred_date = last_date + timedelta(days=day)
            
            # Trend component
            trend_component = trend_analysis.slope * day if trend_analysis.strength > 0.3 else 0
            
            # Seasonal component
            seasonal_component = 0
            if seasonal_analysis.strength > 0.2:
                if seasonal_analysis.pattern_type == SeasonalPattern.WEEKLY.value:
                    day_of_week = pred_date.weekday()
                    seasonal_component = seasonal_analysis.seasonal_factors.get(str(day_of_week), 0) - base_value
                
            # Base prediction
            prediction = base_value + trend_component + seasonal_component
            
            # Confidence intervals (simplified)
            volatility = trend_analysis.volatility
            confidence_range = abs(prediction) * (0.1 + volatility * 0.3)
            
            predictions.append({
                'date': pred_date.isoformat(),
                'value': round(float(prediction), 2),
                'confidence_lower': round(float(prediction - confidence_range), 2),
                'confidence_upper': round(float(prediction + confidence_range), 2),
                'trend_component': round(float(trend_component), 2),
                'seasonal_component': round(float(seasonal_component), 2)
            })
        
        return predictions
    
    def _calculate_model_accuracy(self, data: pd.DataFrame) -> float:
        """Calculate model accuracy using backtesting"""
        if len(data) < 14:
            return 0.5  # Default accuracy for insufficient data
        
        # Simple backtesting: use last 7 days as test set
        train_data = data.iloc[:-7]
        test_data = data.iloc[-7:]
        
        if len(train_data) == 0:
            return 0.5
        
        # Simple prediction using moving average
        window = min(7, len(train_data))
        predictions = []
        actuals = []
        
        for i in range(len(test_data)):
            # Predict using moving average of training data
            pred = train_data['amount'].tail(window).mean()
            actual = test_data.iloc[i]['amount']
            
            predictions.append(pred)
            actuals.append(actual)
        
        # Calculate MAPE (Mean Absolute Percentage Error)
        mape = np.mean([abs(a - p) / (abs(a) + 1e-6) for a, p in zip(actuals, predictions)])
        accuracy = max(0, 1 - mape)
        
        return min(accuracy, 1.0)
    
    def _calculate_overall_confidence(
        self,
        seasonal_analysis: SeasonalAnalysis,
        trend_analysis: TrendAnalysis,
        accuracy: float
    ) -> float:
        """Calculate overall forecast confidence"""
        base_confidence = accuracy
        
        # Boost confidence if we have strong patterns
        if seasonal_analysis.strength > 0.5:
            base_confidence += 0.1
        
        if trend_analysis.trend_confidence > 0.5:
            base_confidence += 0.1
        
        # Reduce confidence for high volatility
        if trend_analysis.volatility > 0.8:
            base_confidence *= 0.7
        
        return max(ForecastingLimits.MIN_CONFIDENCE_THRESHOLD, min(base_confidence, 1.0))
    
    def _store_forecast(self, forecast_result: ForecastResult) -> None:
        """Store forecast result for future reference"""
        # This would typically store in a forecasts table
        # For now, we'll use the analytics engine
        try:
            self.analytics.store_custom_metric(
                user_id=forecast_result.user_id,
                metric_name=f"forecast_{forecast_result.forecast_type}",
                metric_value=forecast_result.confidence_score,
                metadata={
                    "forecast_id": forecast_result.forecast_id,
                    "horizon_days": forecast_result.horizon_days,
                    "predictions_count": len(forecast_result.predictions)
                }
            )
        except Exception as e:
            self.logger.warning(f"Failed to store forecast analytics: {str(e)}")
    
    def get_forecast_accuracy_history(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get forecast accuracy history for a user"""
        try:
            # This would query stored forecasts and compare with actual results
            # Simplified implementation
            return {
                "user_id": user_id,
                "period_days": days,
                "average_accuracy": 0.75,  # Placeholder
                "forecast_count": 10,      # Placeholder
                "accuracy_trend": "improving",
                "best_forecast_type": "cash_flow",
                "accuracy_by_horizon": {
                    "7_days": 0.85,
                    "30_days": 0.75,
                    "60_days": 0.65,
                    "90_days": 0.55
                }
            }
        except Exception as e:
            self.logger.error(f"Failed to get accuracy history: {str(e)}")
            raise BusinessLogicException(
                message="Failed to retrieve forecast accuracy history",
                code="FORECAST_ACCURACY_ERROR"
            )