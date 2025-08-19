"""
Time Series Forecasting Models

Advanced time series models for financial forecasting including
ARIMA, exponential smoothing, and ensemble methods.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum
import logging
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
import joblib
import os


class ModelType(Enum):
    """Available time series model types"""
    SIMPLE_MOVING_AVERAGE = "sma"
    EXPONENTIAL_SMOOTHING = "exponential"
    LINEAR_REGRESSION = "linear"
    RANDOM_FOREST = "random_forest"
    ENSEMBLE = "ensemble"
    SEASONAL_NAIVE = "seasonal_naive"


class ModelPerformanceMetric(Enum):
    """Model performance metrics"""
    MAE = "mean_absolute_error"
    MSE = "mean_squared_error"
    RMSE = "root_mean_squared_error"
    MAPE = "mean_absolute_percentage_error"
    R2 = "r_squared"


@dataclass
class ModelPrediction:
    """Single model prediction with confidence"""
    value: float
    confidence_lower: float
    confidence_upper: float
    model_type: str
    confidence_score: float


@dataclass
class ModelPerformance:
    """Model performance metrics"""
    model_type: str
    mae: float
    mse: float
    rmse: float
    mape: float
    r2: float
    training_samples: int
    test_samples: int


@dataclass
class EnsemblePrediction:
    """Ensemble prediction combining multiple models"""
    value: float
    confidence_lower: float
    confidence_upper: float
    individual_predictions: List[ModelPrediction]
    model_weights: Dict[str, float]
    ensemble_confidence: float


class TimeSeriesLimits:
    """Time series modeling limits"""
    MIN_TRAINING_SAMPLES = 14
    MAX_TRAINING_SAMPLES = 1000
    MIN_SEASONAL_PERIOD = 7
    MAX_FORECAST_HORIZON = 90
    CONFIDENCE_LEVELS = [0.8, 0.9, 0.95]


class SimpleMovingAverageModel:
    """Simple Moving Average forecasting model"""
    
    def __init__(self, window_size: int = 7):
        self.window_size = window_size
        self.history = []
        self.is_trained = False
    
    def fit(self, data: np.ndarray) -> None:
        """Train the model with historical data"""
        self.history = data.tolist()
        self.is_trained = len(self.history) >= self.window_size
    
    def predict(self, steps: int = 1) -> List[float]:
        """Generate predictions for specified steps"""
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        predictions = []
        current_history = self.history.copy()
        
        for _ in range(steps):
            # Calculate moving average
            window = current_history[-self.window_size:]
            prediction = np.mean(window)
            predictions.append(float(prediction))
            current_history.append(prediction)
        
        return predictions
    
    def get_confidence_intervals(self, predictions: List[float], confidence: float = 0.95) -> Tuple[List[float], List[float]]:
        """Calculate confidence intervals for predictions"""
        if len(self.history) < self.window_size * 2:
            # Simple fallback for insufficient data
            std_error = np.std(self.history) if self.history else 1.0
        else:
            # Calculate prediction error from historical performance
            errors = []
            for i in range(self.window_size, len(self.history)):
                actual = self.history[i]
                predicted = np.mean(self.history[i-self.window_size:i])
                errors.append(abs(actual - predicted))
            std_error = np.std(errors) if errors else np.std(self.history)
        
        # Z-score for confidence level
        z_scores = {0.8: 1.28, 0.9: 1.645, 0.95: 1.96}
        z = z_scores.get(confidence, 1.96)
        
        margin = z * std_error
        lower = [p - margin for p in predictions]
        upper = [p + margin for p in predictions]
        
        return lower, upper


class ExponentialSmoothingModel:
    """Exponential Smoothing with trend and seasonality"""
    
    def __init__(self, alpha: float = 0.3, beta: float = 0.1, gamma: float = 0.1, seasonal_periods: int = 7):
        self.alpha = alpha  # Level smoothing
        self.beta = beta    # Trend smoothing  
        self.gamma = gamma  # Seasonal smoothing
        self.seasonal_periods = seasonal_periods
        self.level = 0
        self.trend = 0
        self.seasonal = [0] * seasonal_periods
        self.is_trained = False
        self.history = []
    
    def fit(self, data: np.ndarray) -> None:
        """Train the exponential smoothing model"""
        if len(data) < self.seasonal_periods * 2:
            raise ValueError(f"Need at least {self.seasonal_periods * 2} data points")
        
        self.history = data.tolist()
        
        # Initialize level and trend
        self.level = np.mean(data[:self.seasonal_periods])
        self.trend = (np.mean(data[self.seasonal_periods:self.seasonal_periods*2]) - 
                     np.mean(data[:self.seasonal_periods])) / self.seasonal_periods
        
        # Initialize seasonal components
        for i in range(self.seasonal_periods):
            seasonal_avg = np.mean([data[j] for j in range(i, len(data), self.seasonal_periods)])
            self.seasonal[i] = seasonal_avg - self.level
        
        # Update parameters through the data
        for i, value in enumerate(data):
            if i == 0:
                continue
                
            season_idx = i % self.seasonal_periods
            
            # Update level
            new_level = self.alpha * (value - self.seasonal[season_idx]) + (1 - self.alpha) * (self.level + self.trend)
            
            # Update trend
            new_trend = self.beta * (new_level - self.level) + (1 - self.beta) * self.trend
            
            # Update seasonal
            self.seasonal[season_idx] = self.gamma * (value - new_level) + (1 - self.gamma) * self.seasonal[season_idx]
            
            self.level = new_level
            self.trend = new_trend
        
        self.is_trained = True
    
    def predict(self, steps: int = 1) -> List[float]:
        """Generate predictions using exponential smoothing"""
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        predictions = []
        
        for h in range(1, steps + 1):
            season_idx = (len(self.history) + h - 1) % self.seasonal_periods
            forecast = self.level + h * self.trend + self.seasonal[season_idx]
            predictions.append(float(forecast))
        
        return predictions
    
    def get_confidence_intervals(self, predictions: List[float], confidence: float = 0.95) -> Tuple[List[float], List[float]]:
        """Calculate confidence intervals for exponential smoothing predictions"""
        # Simplified confidence intervals based on historical residuals
        residuals = []
        
        # Calculate in-sample residuals for error estimation
        fitted_values = []
        temp_level, temp_trend = self.level, self.trend
        temp_seasonal = self.seasonal.copy()
        
        for i in range(min(len(self.history), 50)):  # Use recent history
            season_idx = i % self.seasonal_periods
            fitted = temp_level + temp_trend + temp_seasonal[season_idx]
            fitted_values.append(fitted)
            residuals.append(abs(self.history[-(i+1)] - fitted))
        
        std_error = np.std(residuals) if residuals else np.std(self.history)
        
        z_scores = {0.8: 1.28, 0.9: 1.645, 0.95: 1.96}
        z = z_scores.get(confidence, 1.96)
        
        # Error grows with forecast horizon
        lower, upper = [], []
        for h, pred in enumerate(predictions, 1):
            margin = z * std_error * np.sqrt(h)  # Error increases with horizon
            lower.append(pred - margin)
            upper.append(pred + margin)
        
        return lower, upper


class LinearRegressionModel:
    """Linear regression with time-based features"""
    
    def __init__(self):
        self.model = Ridge(alpha=1.0)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = []
        self.history = []
    
    def _create_features(self, data: np.ndarray, start_index: int = 0) -> np.ndarray:
        """Create features for linear regression"""
        features = []
        
        for i in range(len(data)):
            feature_row = []
            
            # Time-based features
            time_idx = start_index + i
            feature_row.append(time_idx)  # Linear trend
            feature_row.append(time_idx ** 2)  # Quadratic trend
            
            # Day of week (cyclical)
            day_of_week = time_idx % 7
            feature_row.append(np.sin(2 * np.pi * day_of_week / 7))
            feature_row.append(np.cos(2 * np.pi * day_of_week / 7))
            
            # Day of month (cyclical)
            day_of_month = time_idx % 30
            feature_row.append(np.sin(2 * np.pi * day_of_month / 30))
            feature_row.append(np.cos(2 * np.pi * day_of_month / 30))
            
            # Lag features (if available)
            if i >= 1:
                feature_row.append(data[i-1])  # Previous day
            else:
                feature_row.append(0)
            
            if i >= 7:
                feature_row.append(data[i-7])  # Same day last week
            else:
                feature_row.append(0)
            
            features.append(feature_row)
        
        self.feature_names = [
            'time_linear', 'time_quadratic', 'dow_sin', 'dow_cos', 
            'dom_sin', 'dom_cos', 'lag_1', 'lag_7'
        ]
        
        return np.array(features)
    
    def fit(self, data: np.ndarray) -> None:
        """Train the linear regression model"""
        if len(data) < TimeSeriesLimits.MIN_TRAINING_SAMPLES:
            raise ValueError(f"Need at least {TimeSeriesLimits.MIN_TRAINING_SAMPLES} data points")
        
        self.history = data.tolist()
        
        # Create features
        X = self._create_features(data)
        y = data
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled, y)
        self.is_trained = True
    
    def predict(self, steps: int = 1) -> List[float]:
        """Generate predictions using linear regression"""
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        predictions = []
        extended_data = np.array(self.history.copy())
        
        for step in range(steps):
            # Create features for next time step
            time_idx = len(self.history) + step
            feature_row = []
            
            # Time features
            feature_row.append(time_idx)
            feature_row.append(time_idx ** 2)
            
            # Cyclical features
            day_of_week = time_idx % 7
            feature_row.append(np.sin(2 * np.pi * day_of_week / 7))
            feature_row.append(np.cos(2 * np.pi * day_of_week / 7))
            
            day_of_month = time_idx % 30
            feature_row.append(np.sin(2 * np.pi * day_of_month / 30))
            feature_row.append(np.cos(2 * np.pi * day_of_month / 30))
            
            # Lag features
            if len(extended_data) >= 1:
                feature_row.append(extended_data[-1])
            else:
                feature_row.append(0)
            
            if len(extended_data) >= 7:
                feature_row.append(extended_data[-7])
            else:
                feature_row.append(0)
            
            # Scale and predict
            X_new = self.scaler.transform([feature_row])
            prediction = self.model.predict(X_new)[0]
            
            predictions.append(float(prediction))
            extended_data = np.append(extended_data, prediction)
        
        return predictions
    
    def get_confidence_intervals(self, predictions: List[float], confidence: float = 0.95) -> Tuple[List[float], List[float]]:
        """Calculate confidence intervals for linear regression predictions"""
        # Use cross-validation residuals for error estimation
        X = self._create_features(np.array(self.history))
        X_scaled = self.scaler.transform(X)
        y_pred = self.model.predict(X_scaled)
        residuals = np.array(self.history) - y_pred
        
        std_error = np.std(residuals)
        
        z_scores = {0.8: 1.28, 0.9: 1.645, 0.95: 1.96}
        z = z_scores.get(confidence, 1.96)
        
        # Error grows with forecast horizon
        lower, upper = [], []
        for h, pred in enumerate(predictions, 1):
            margin = z * std_error * np.sqrt(1 + 1/len(self.history))  # Prediction interval
            lower.append(pred - margin)
            upper.append(pred + margin)
        
        return lower, upper


class EnsembleTimeSeriesModel:
    """Ensemble model combining multiple forecasting approaches"""
    
    def __init__(self):
        self.models = {
            ModelType.SIMPLE_MOVING_AVERAGE: SimpleMovingAverageModel(),
            ModelType.EXPONENTIAL_SMOOTHING: ExponentialSmoothingModel(),
            ModelType.LINEAR_REGRESSION: LinearRegressionModel()
        }
        self.model_weights = {}
        self.is_trained = False
        self.history = []
    
    def fit(self, data: np.ndarray) -> None:
        """Train all models and calculate ensemble weights"""
        if len(data) < TimeSeriesLimits.MIN_TRAINING_SAMPLES:
            raise ValueError(f"Need at least {TimeSeriesLimits.MIN_TRAINING_SAMPLES} data points")
        
        self.history = data.tolist()
        
        # Split data for training and validation
        split_idx = max(int(len(data) * 0.8), len(data) - 7)
        train_data = data[:split_idx]
        val_data = data[split_idx:]
        
        model_performances = {}
        
        for model_type, model in self.models.items():
            try:
                # Train model
                model.fit(train_data)
                
                # Validate on holdout set
                predictions = model.predict(len(val_data))
                mae = mean_absolute_error(val_data, predictions)
                
                model_performances[model_type] = 1 / (mae + 1e-6)  # Inverse error as weight
                
            except Exception as e:
                logging.warning(f"Model {model_type.value} failed: {str(e)}")
                model_performances[model_type] = 0
        
        # Normalize weights
        total_weight = sum(model_performances.values())
        if total_weight > 0:
            self.model_weights = {
                model_type: weight / total_weight 
                for model_type, weight in model_performances.items()
            }
        else:
            # Equal weights if all models failed
            self.model_weights = {
                model_type: 1.0 / len(self.models) 
                for model_type in self.models.keys()
            }
        
        # Retrain on full dataset
        for model_type, model in self.models.items():
            try:
                model.fit(data)
            except Exception as e:
                logging.warning(f"Full training failed for {model_type.value}: {str(e)}")
        
        self.is_trained = True
    
    def predict(self, steps: int = 1, confidence: float = 0.95) -> EnsemblePrediction:
        """Generate ensemble predictions with confidence intervals"""
        if not self.is_trained:
            raise ValueError("Ensemble not trained")
        
        individual_predictions = []
        weighted_values = []
        
        for model_type, model in self.models.items():
            try:
                predictions = model.predict(steps)
                confidence_lower, confidence_upper = model.get_confidence_intervals(predictions, confidence)
                
                weight = self.model_weights.get(model_type, 0)
                
                for i, (pred, lower, upper) in enumerate(zip(predictions, confidence_lower, confidence_upper)):
                    individual_pred = ModelPrediction(
                        value=pred,
                        confidence_lower=lower,
                        confidence_upper=upper,
                        model_type=model_type.value,
                        confidence_score=weight
                    )
                    
                    if i >= len(individual_predictions):
                        individual_predictions.append([])
                        weighted_values.append([])
                    
                    individual_predictions[i].append(individual_pred)
                    weighted_values[i].append(pred * weight)
                    
            except Exception as e:
                logging.warning(f"Prediction failed for {model_type.value}: {str(e)}")
        
        # Calculate ensemble predictions
        ensemble_predictions = []
        
        for i in range(steps):
            if i < len(weighted_values) and weighted_values[i]:
                ensemble_value = sum(weighted_values[i])
                
                # Calculate ensemble confidence intervals
                individual_lowers = [p.confidence_lower for p in individual_predictions[i]]
                individual_uppers = [p.confidence_upper for p in individual_predictions[i]]
                weights = [self.model_weights.get(ModelType(p.model_type), 0) for p in individual_predictions[i]]
                
                ensemble_lower = sum(l * w for l, w in zip(individual_lowers, weights))
                ensemble_upper = sum(u * w for u, w in zip(individual_uppers, weights))
                
                # Ensemble confidence is weighted average of individual confidences
                ensemble_confidence = sum(p.confidence_score for p in individual_predictions[i]) / len(individual_predictions[i])
                
                ensemble_predictions.append(EnsemblePrediction(
                    value=ensemble_value,
                    confidence_lower=ensemble_lower,
                    confidence_upper=ensemble_upper,
                    individual_predictions=individual_predictions[i],
                    model_weights=dict(self.model_weights),
                    ensemble_confidence=ensemble_confidence
                ))
            else:
                # Fallback if no predictions available
                ensemble_predictions.append(EnsemblePrediction(
                    value=0.0,
                    confidence_lower=0.0,
                    confidence_upper=0.0,
                    individual_predictions=[],
                    model_weights={},
                    ensemble_confidence=0.0
                ))
        
        return ensemble_predictions[0] if steps == 1 else ensemble_predictions
    
    def get_model_performance(self) -> Dict[str, ModelPerformance]:
        """Get performance metrics for each model"""
        if not self.is_trained or len(self.history) < 14:
            return {}
        
        # Use recent history for performance evaluation
        test_size = min(7, len(self.history) // 4)
        train_data = np.array(self.history[:-test_size])
        test_data = np.array(self.history[-test_size:])
        
        performances = {}
        
        for model_type, model in self.models.items():
            try:
                # Retrain on training portion
                temp_model = type(model)()
                if hasattr(temp_model, '__dict__'):
                    temp_model.__dict__.update(model.__dict__)
                
                temp_model.fit(train_data)
                predictions = temp_model.predict(len(test_data))
                
                # Calculate metrics
                mae = mean_absolute_error(test_data, predictions)
                mse = mean_squared_error(test_data, predictions)
                rmse = np.sqrt(mse)
                mape = np.mean(np.abs((test_data - predictions) / (test_data + 1e-6))) * 100
                r2 = r2_score(test_data, predictions) if len(test_data) > 1 else 0
                
                performances[model_type.value] = ModelPerformance(
                    model_type=model_type.value,
                    mae=float(mae),
                    mse=float(mse),
                    rmse=float(rmse),
                    mape=float(mape),
                    r2=float(r2),
                    training_samples=len(train_data),
                    test_samples=len(test_data)
                )
                
            except Exception as e:
                logging.warning(f"Performance calculation failed for {model_type.value}: {str(e)}")
        
        return performances