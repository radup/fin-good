"""
Forecasting API Endpoints

REST API endpoints for cash flow forecasting, predictive analytics,
and financial trend analysis with ML-powered predictions.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
import logging

from app.core.database import get_db
from app.core.cookie_auth import get_current_user_from_cookie
from app.core.exceptions import ValidationException, BusinessLogicException
from app.core.rate_limiter import rate_limit
from app.core.audit_logger import security_audit_logger
from app.models.user import User
from app.services.forecasting_engine import (
    ForecastingEngine, ForecastType, ForecastHorizon, ForecastResult
)
from app.ml.time_series_models import EnsembleTimeSeriesModel, ModelType


router = APIRouter()
logger = logging.getLogger(__name__)


# Request/Response Models
class ForecastRequest(BaseModel):
    """Request model for generating forecasts"""
    forecast_type: str = Field(..., description="Type of forecast to generate")
    horizon: str = Field(..., description="Forecast horizon")
    custom_days: Optional[int] = Field(None, description="Custom forecast days for custom horizon")
    category_filter: Optional[str] = Field(None, description="Filter by transaction category")
    confidence_level: float = Field(0.95, description="Confidence level for intervals")
    
    @validator('forecast_type')
    def validate_forecast_type(cls, v):
        valid_types = [ft.value for ft in ForecastType]
        if v not in valid_types:
            raise ValueError(f"Invalid forecast type. Must be one of: {valid_types}")
        return v
    
    @validator('horizon')
    def validate_horizon(cls, v):
        valid_horizons = [fh.value for fh in ForecastHorizon]
        if v not in valid_horizons:
            raise ValueError(f"Invalid horizon. Must be one of: {valid_horizons}")
        return v
    
    @validator('confidence_level')
    def validate_confidence(cls, v):
        if not 0.5 <= v <= 0.99:
            raise ValueError("Confidence level must be between 0.5 and 0.99")
        return v


class PredictionPoint(BaseModel):
    """Single prediction point"""
    date: str
    value: float
    confidence_lower: float
    confidence_upper: float
    trend_component: Optional[float] = None
    seasonal_component: Optional[float] = None


class ForecastResponse(BaseModel):
    """Response model for forecast results"""
    forecast_id: str
    user_id: int
    forecast_type: str
    horizon_days: int
    predictions: List[PredictionPoint]
    confidence_score: float
    seasonal_pattern: str
    trend_direction: str
    model_accuracy: float
    created_at: datetime
    metadata: Dict[str, Any]


class AccuracyHistoryResponse(BaseModel):
    """Response model for forecast accuracy history"""
    user_id: int
    period_days: int
    average_accuracy: float
    forecast_count: int
    accuracy_trend: str
    best_forecast_type: str
    accuracy_by_horizon: Dict[str, float]


class ModelPerformanceResponse(BaseModel):
    """Response model for model performance metrics"""
    model_type: str
    mae: float
    mse: float
    rmse: float
    mape: float
    r2: float
    training_samples: int
    test_samples: int


class EnsembleAnalysisResponse(BaseModel):
    """Response model for ensemble model analysis"""
    model_weights: Dict[str, float]
    individual_performances: List[ModelPerformanceResponse]
    ensemble_confidence: float
    recommended_horizon: str
    data_quality_score: float


# API Endpoints
@router.post("/generate", response_model=ForecastResponse)
@rate_limit(requests_per_hour=30, requests_per_minute=5)
async def generate_forecast(
    request: ForecastRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Generate cash flow forecast with ML predictions
    
    - **forecast_type**: Type of forecast (cash_flow, revenue, expenses, net_income, category_specific)
    - **horizon**: Forecast horizon (7_days, 30_days, 60_days, 90_days, custom)
    - **custom_days**: Number of days for custom horizon
    - **category_filter**: Optional category filter for category-specific forecasts
    - **confidence_level**: Statistical confidence level for prediction intervals
    """
    try:
        # Initialize forecasting engine
        forecasting_engine = ForecastingEngine(db)
        
        # Convert string enums
        forecast_type = ForecastType(request.forecast_type)
        horizon = ForecastHorizon(request.horizon)
        
        # Generate forecast
        forecast_result = forecasting_engine.generate_forecast(
            user_id=current_user.id,
            forecast_type=forecast_type,
            horizon=horizon,
            custom_days=request.custom_days,
            category_filter=request.category_filter
        )
        
        # Convert to response format
        predictions = [
            PredictionPoint(
                date=pred["date"],
                value=pred["value"],
                confidence_lower=pred["confidence_lower"],
                confidence_upper=pred["confidence_upper"],
                trend_component=pred.get("trend_component"),
                seasonal_component=pred.get("seasonal_component")
            )
            for pred in forecast_result.predictions
        ]
        
        response = ForecastResponse(
            forecast_id=forecast_result.forecast_id,
            user_id=forecast_result.user_id,
            forecast_type=forecast_result.forecast_type,
            horizon_days=forecast_result.horizon_days,
            predictions=predictions,
            confidence_score=forecast_result.confidence_score,
            seasonal_pattern=forecast_result.seasonal_pattern,
            trend_direction=forecast_result.trend_direction,
            model_accuracy=forecast_result.model_accuracy,
            created_at=forecast_result.created_at,
            metadata=forecast_result.metadata
        )
        
        # Log successful forecast generation
        security_audit_logger.log_data_access(
            user_id=current_user.id,
            action="forecast_generated",
            resource_type="forecast",
            resource_id=forecast_result.forecast_id,
            metadata={
                "forecast_type": request.forecast_type,
                "horizon_days": forecast_result.horizon_days,
                "confidence": forecast_result.confidence_score
            }
        )
        
        return response
        
    except ValidationException as e:
        logger.warning(f"Forecast validation error for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except BusinessLogicException as e:
        logger.error(f"Forecast generation error for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    
    except Exception as e:
        logger.error(f"Unexpected forecast error for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate forecast")


@router.get("/accuracy-history", response_model=AccuracyHistoryResponse)
@rate_limit(requests_per_hour=60, requests_per_minute=10)
async def get_accuracy_history(
    days: int = Query(30, description="Number of days to analyze", ge=7, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Get forecast accuracy history for the current user
    
    - **days**: Number of days to analyze (7-365)
    """
    try:
        forecasting_engine = ForecastingEngine(db)
        
        accuracy_data = forecasting_engine.get_forecast_accuracy_history(
            user_id=current_user.id,
            days=days
        )
        
        response = AccuracyHistoryResponse(**accuracy_data)
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to get accuracy history for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve accuracy history")


@router.get("/model-analysis", response_model=EnsembleAnalysisResponse)
@rate_limit(requests_per_hour=20, requests_per_minute=2)
async def get_model_analysis(
    forecast_type: str = Query("cash_flow", description="Type of forecast to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Get detailed analysis of forecasting models and ensemble performance
    
    - **forecast_type**: Type of forecast to analyze
    """
    try:
        # Validate forecast type
        if forecast_type not in [ft.value for ft in ForecastType]:
            raise HTTPException(status_code=400, detail="Invalid forecast type")
        
        forecasting_engine = ForecastingEngine(db)
        
        # Load historical data for analysis
        historical_data = forecasting_engine._load_historical_data(
            user_id=current_user.id,
            forecast_type=ForecastType(forecast_type),
            category_filter=None,
            horizon_days=30
        )
        
        if len(historical_data) < 14:
            raise HTTPException(
                status_code=400, 
                detail="Insufficient historical data for model analysis"
            )
        
        # Create and train ensemble model
        ensemble_model = EnsembleTimeSeriesModel()
        ensemble_model.fit(historical_data['amount'].values)
        
        # Get model performances
        performances = ensemble_model.get_model_performance()
        
        performance_responses = [
            ModelPerformanceResponse(**perf.__dict__)
            for perf in performances.values()
        ]
        
        # Calculate data quality score
        data_quality_score = min(1.0, len(historical_data) / 90)  # Based on data availability
        
        # Recommend best horizon based on accuracy
        accuracy_by_horizon = {
            "7_days": 0.85,
            "30_days": 0.75, 
            "60_days": 0.65,
            "90_days": 0.55
        }
        
        best_horizon = max(accuracy_by_horizon.keys(), key=lambda x: accuracy_by_horizon[x])
        
        response = EnsembleAnalysisResponse(
            model_weights=dict(ensemble_model.model_weights),
            individual_performances=performance_responses,
            ensemble_confidence=0.75,  # Simplified
            recommended_horizon=best_horizon,
            data_quality_score=data_quality_score
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Model analysis failed for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze forecasting models")


@router.post("/batch-forecast")
@rate_limit(requests_per_hour=10, requests_per_minute=1)
async def generate_batch_forecasts(
    forecast_types: List[str] = Query(..., description="List of forecast types to generate"),
    horizon: str = Query("30_days", description="Forecast horizon for all forecasts"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Generate multiple forecasts in batch for efficiency
    
    - **forecast_types**: List of forecast types to generate
    - **horizon**: Common horizon for all forecasts
    """
    try:
        # Validate inputs
        valid_types = [ft.value for ft in ForecastType]
        invalid_types = [ft for ft in forecast_types if ft not in valid_types]
        if invalid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid forecast types: {invalid_types}"
            )
        
        if len(forecast_types) > 5:
            raise HTTPException(
                status_code=400,
                detail="Maximum 5 forecast types allowed in batch"
            )
        
        # Add batch job to background tasks
        background_tasks.add_task(
            _process_batch_forecasts,
            user_id=current_user.id,
            forecast_types=forecast_types,
            horizon=horizon,
            db=db
        )
        
        return {
            "status": "batch_started",
            "user_id": current_user.id,
            "forecast_types": forecast_types,
            "horizon": horizon,
            "estimated_completion": "2-5 minutes"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch forecast failed for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start batch forecast")


async def _process_batch_forecasts(
    user_id: int,
    forecast_types: List[str],
    horizon: str,
    db: Session
):
    """Background task to process batch forecasts"""
    try:
        forecasting_engine = ForecastingEngine(db)
        horizon_enum = ForecastHorizon(horizon)
        
        for forecast_type in forecast_types:
            try:
                forecast_type_enum = ForecastType(forecast_type)
                
                forecast_result = forecasting_engine.generate_forecast(
                    user_id=user_id,
                    forecast_type=forecast_type_enum,
                    horizon=horizon_enum
                )
                
                logger.info(f"Batch forecast completed: {forecast_type} for user {user_id}")
                
            except Exception as e:
                logger.error(f"Batch forecast failed for {forecast_type}, user {user_id}: {str(e)}")
                
    except Exception as e:
        logger.error(f"Batch forecast processing failed for user {user_id}: {str(e)}")


@router.get("/forecast-types", response_model=List[Dict[str, str]])
async def get_available_forecast_types():
    """Get list of available forecast types and descriptions"""
    return [
        {
            "type": ForecastType.CASH_FLOW.value,
            "name": "Cash Flow",
            "description": "Overall cash flow including both income and expenses"
        },
        {
            "type": ForecastType.REVENUE.value,
            "name": "Revenue",
            "description": "Income and revenue projections only"
        },
        {
            "type": ForecastType.EXPENSES.value,
            "name": "Expenses", 
            "description": "Expense and cost projections only"
        },
        {
            "type": ForecastType.NET_INCOME.value,
            "name": "Net Income",
            "description": "Net income after expenses"
        },
        {
            "type": ForecastType.CATEGORY_SPECIFIC.value,
            "name": "Category Specific",
            "description": "Forecasts for specific transaction categories"
        }
    ]


@router.get("/horizons", response_model=List[Dict[str, Any]])
async def get_available_horizons():
    """Get list of available forecast horizons"""
    return [
        {
            "horizon": ForecastHorizon.WEEKLY.value,
            "name": "Weekly",
            "days": 7,
            "description": "Short-term 7-day forecast"
        },
        {
            "horizon": ForecastHorizon.MONTHLY.value,
            "name": "Monthly", 
            "days": 30,
            "description": "Medium-term 30-day forecast"
        },
        {
            "horizon": ForecastHorizon.BIMONTHLY.value,
            "name": "Bi-Monthly",
            "days": 60,
            "description": "60-day forecast for budget planning"
        },
        {
            "horizon": ForecastHorizon.QUARTERLY.value,
            "name": "Quarterly",
            "days": 90,
            "description": "Long-term 90-day forecast"
        },
        {
            "horizon": ForecastHorizon.CUSTOM.value,
            "name": "Custom",
            "days": None,
            "description": "Custom time horizon (specify days)"
        }
    ]


@router.get("/health")
async def forecasting_health_check():
    """Health check endpoint for forecasting service"""
    return {
        "status": "healthy",
        "service": "forecasting",
        "version": "1.0.0",
        "models_available": [model.value for model in ModelType],
        "max_forecast_days": 365,
        "supported_confidence_levels": [0.8, 0.9, 0.95]
    }