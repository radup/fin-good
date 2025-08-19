"""
Budget Analysis Service for FinGood Financial Platform

This service provides comprehensive budget analysis capabilities including:
- Variance analysis (actual vs budgeted amounts)
- Trend detection and forecasting
- Alert generation for budget overruns
- Integration with forecasting engine for predictive insights
- Automated budget recommendations
"""

import logging
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from app.models.budget import (
    Budget, BudgetItem, BudgetActual, BudgetVarianceReport, 
    BudgetGoal, BudgetType, BudgetStatus, VarianceType
)
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.budget import (
    BudgetVarianceAnalysis, CategoryVariance, BudgetSummary,
    BudgetForecast, BudgetPerformanceMetrics
)
from app.services.forecasting_engine import ForecastingEngine
from app.core.config import settings

logger = logging.getLogger(__name__)


class BudgetAnalyzer:
    """
    Core budget analysis engine providing comprehensive budget insights.
    
    Features:
    - Real-time variance tracking
    - Predictive budget analysis
    - Automated alert generation
    - Integration with forecasting models
    - Performance metrics calculation
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.forecasting_engine = ForecastingEngine(db)
        
    def analyze_budget_variance(
        self, 
        budget_id: int, 
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> BudgetVarianceAnalysis:
        """
        Perform comprehensive variance analysis for a budget.
        
        Args:
            budget_id: Budget to analyze
            user_id: User ID for security validation
            start_date: Analysis start date (defaults to budget start)
            end_date: Analysis end date (defaults to current date)
            
        Returns:
            Comprehensive variance analysis results
        """
        try:
            # Get budget and validate ownership
            budget = self.db.query(Budget).filter(
                Budget.id == budget_id,
                Budget.user_id == user_id
            ).first()
            
            if not budget:
                raise ValueError(f"Budget {budget_id} not found or access denied")
            
            # Set analysis period
            if not start_date:
                start_date = budget.start_date
            if not end_date:
                end_date = min(datetime.utcnow(), budget.end_date)
            
            logger.info(f"Analyzing budget variance for budget {budget_id}, period {start_date} to {end_date}")
            
            # Update actual amounts from transactions
            self._update_budget_actuals(budget, start_date, end_date)
            
            # Calculate overall variance
            total_income_budgeted, total_income_actual = self._calculate_income_totals(budget, start_date, end_date)
            total_expense_budgeted, total_expense_actual = self._calculate_expense_totals(budget, start_date, end_date)
            
            net_variance_amount = (total_income_actual - total_expense_actual) - (total_income_budgeted - total_expense_budgeted)
            net_variance_percentage = (net_variance_amount / max(total_income_budgeted - total_expense_budgeted, 1)) * 100
            
            # Analyze category-level variances
            category_variances = self._analyze_category_variances(budget, start_date, end_date)
            
            # Categorize variances
            over_budget_categories = [cv.category for cv in category_variances 
                                    if cv.variance_type == VarianceType.UNFAVORABLE and abs(cv.variance_percentage) > 10]
            under_budget_categories = [cv.category for cv in category_variances 
                                     if cv.variance_type == VarianceType.FAVORABLE and abs(cv.variance_percentage) > 10]
            warning_categories = [cv.category for cv in category_variances 
                                if not cv.is_income and cv.actual / max(cv.budgeted, 1) > budget.warning_threshold]
            critical_categories = [cv.category for cv in category_variances 
                                 if not cv.is_income and cv.actual / max(cv.budgeted, 1) > budget.critical_threshold]
            
            # Generate recommendations
            recommendations = self._generate_variance_recommendations(
                budget, category_variances, over_budget_categories, critical_categories
            )
            
            # Calculate forecast accuracy if available
            forecast_accuracy = self._calculate_forecast_accuracy(budget, start_date, end_date)
            
            analysis = BudgetVarianceAnalysis(
                budget_id=budget_id,
                period_start=start_date,
                period_end=end_date,
                total_income_budgeted=total_income_budgeted,
                total_income_actual=total_income_actual,
                total_expense_budgeted=total_expense_budgeted,
                total_expense_actual=total_expense_actual,
                net_variance_amount=net_variance_amount,
                net_variance_percentage=net_variance_percentage,
                category_variances=category_variances,
                over_budget_categories=over_budget_categories,
                under_budget_categories=under_budget_categories,
                warning_categories=warning_categories,
                critical_categories=critical_categories,
                recommendations=recommendations,
                forecast_accuracy=forecast_accuracy
            )
            
            # Save variance report
            self._save_variance_report(budget, analysis)
            
            logger.info(f"Budget variance analysis completed: {net_variance_percentage:.1f}% net variance")
            return analysis
            
        except Exception as e:
            logger.error(f"Budget variance analysis failed for budget {budget_id}: {e}")
            raise
    
    def get_budget_summary(self, user_id: int) -> BudgetSummary:
        """Get high-level summary of all user budgets."""
        try:
            # Get active budgets
            budgets = self.db.query(Budget).filter(
                Budget.user_id == user_id,
                Budget.status == BudgetStatus.ACTIVE
            ).all()
            
            total_budgets = len(budgets)
            active_budgets = len([b for b in budgets if b.status == BudgetStatus.ACTIVE])
            
            # Calculate totals
            total_budgeted_income = sum(b.total_income_budget for b in budgets)
            total_budgeted_expenses = sum(b.total_expense_budget for b in budgets)
            
            # Get actual amounts for current period
            total_actual_income = 0.0
            total_actual_expenses = 0.0
            categories_over_budget = 0
            categories_on_track = 0
            
            for budget in budgets:
                actuals = self.db.query(BudgetActual).filter(
                    BudgetActual.budget_id == budget.id,
                    BudgetActual.period_start >= budget.start_date,
                    BudgetActual.period_end <= datetime.utcnow()
                ).all()
                
                for actual in actuals:
                    if actual.is_income:
                        total_actual_income += actual.actual_amount
                    else:
                        total_actual_expenses += actual.actual_amount
                    
                    # Check if over budget
                    variance_ratio = abs(actual.variance_percentage) / 100
                    if variance_ratio > 0.1:  # More than 10% variance
                        if actual.variance_type == VarianceType.UNFAVORABLE:
                            categories_over_budget += 1
                        else:
                            categories_on_track += 1
                    else:
                        categories_on_track += 1
            
            # Calculate overall variance
            net_budgeted = total_budgeted_income - total_budgeted_expenses
            net_actual = total_actual_income - total_actual_expenses
            overall_variance_percentage = ((net_actual - net_budgeted) / max(net_budgeted, 1)) * 100 if net_budgeted != 0 else 0
            
            return BudgetSummary(
                total_budgets=total_budgets,
                active_budgets=active_budgets,
                total_budgeted_income=total_budgeted_income,
                total_budgeted_expenses=total_budgeted_expenses,
                total_actual_income=total_actual_income,
                total_actual_expenses=total_actual_expenses,
                overall_variance_percentage=overall_variance_percentage,
                categories_over_budget=categories_over_budget,
                categories_on_track=categories_on_track
            )
            
        except Exception as e:
            logger.error(f"Failed to get budget summary for user {user_id}: {e}")
            raise
    
    def generate_budget_forecast(
        self, 
        budget_id: int, 
        user_id: int,
        forecast_period: str = "next_month"
    ) -> BudgetForecast:
        """
        Generate forecasted budget performance using ML models.
        
        Args:
            budget_id: Budget to forecast
            user_id: User ID for security validation
            forecast_period: Period to forecast ("next_month", "next_quarter", etc.)
            
        Returns:
            Budget forecast with predictions and recommendations
        """
        try:
            budget = self.db.query(Budget).filter(
                Budget.id == budget_id,
                Budget.user_id == user_id
            ).first()
            
            if not budget:
                raise ValueError(f"Budget {budget_id} not found or access denied")
            
            logger.info(f"Generating budget forecast for budget {budget_id}, period: {forecast_period}")
            
            # Determine forecast period dates
            forecast_start, forecast_end = self._get_forecast_period_dates(forecast_period)
            
            # Get historical transaction data for forecasting
            historical_transactions = self.db.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.date >= budget.start_date - timedelta(days=365),  # 1 year of history
                Transaction.date <= datetime.utcnow()
            ).all()
            
            # Use forecasting engine to predict income and expenses
            forecasted_income = 0.0
            forecasted_expenses = 0.0
            confidence_scores = []
            risk_factors = []
            
            # Forecast by category
            budget_items = self.db.query(BudgetItem).filter(BudgetItem.budget_id == budget_id).all()
            
            for item in budget_items:
                category_transactions = [
                    t for t in historical_transactions 
                    if t.category == item.category and t.is_income == item.is_income
                ]
                
                if len(category_transactions) >= 5:  # Minimum data for forecasting
                    try:
                        # Use forecasting engine
                        forecast_result = self.forecasting_engine.forecast_cash_flow(
                            user_id=user_id,
                            forecast_horizon_days=30 if forecast_period == "next_month" else 90,
                            forecast_date=forecast_start
                        )
                        
                        # Extract relevant forecast for this category
                        category_forecast = self._extract_category_forecast(
                            forecast_result, item.category, item.is_income
                        )
                        
                        if item.is_income:
                            forecasted_income += category_forecast['amount']
                        else:
                            forecasted_expenses += category_forecast['amount']
                        
                        confidence_scores.append(category_forecast['confidence'])
                        
                    except Exception as e:
                        logger.warning(f"Forecasting failed for category {item.category}: {e}")
                        # Fallback to budget amount
                        if item.is_income:
                            forecasted_income += item.budgeted_amount
                        else:
                            forecasted_expenses += item.budgeted_amount
                        confidence_scores.append(0.5)  # Low confidence for fallback
                else:
                    # Use budgeted amount if insufficient historical data
                    if item.is_income:
                        forecasted_income += item.budgeted_amount
                    else:
                        forecasted_expenses += item.budgeted_amount
                    confidence_scores.append(0.3)  # Very low confidence
                    risk_factors.append(f"Insufficient historical data for {item.category}")
            
            # Calculate predicted variance
            predicted_net = forecasted_income - forecasted_expenses
            budgeted_net = budget.total_income_budget - budget.total_expense_budget
            predicted_variance = predicted_net - budgeted_net
            
            # Overall confidence level
            confidence_level = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5
            
            # Generate risk factors and recommendations
            if predicted_variance < -1000:  # Significant shortfall predicted
                risk_factors.append("Significant budget shortfall predicted")
            if confidence_level < 0.6:
                risk_factors.append("Low forecasting confidence due to limited data")
            
            recommendations = self._generate_forecast_recommendations(
                forecasted_income, forecasted_expenses, budget, predicted_variance, risk_factors
            )
            
            forecast = BudgetForecast(
                budget_id=budget_id,
                forecast_period=forecast_period,
                forecasted_income=forecasted_income,
                forecasted_expenses=forecasted_expenses,
                predicted_variance=predicted_variance,
                confidence_level=confidence_level,
                risk_factors=risk_factors,
                recommendations=recommendations
            )
            
            logger.info(f"Budget forecast completed: {predicted_variance:.2f} predicted variance, {confidence_level:.2f} confidence")
            return forecast
            
        except Exception as e:
            logger.error(f"Budget forecast generation failed for budget {budget_id}: {e}")
            raise
    
    def calculate_performance_metrics(self, user_id: int) -> BudgetPerformanceMetrics:
        """Calculate comprehensive budget performance metrics."""
        try:
            # Get all user budgets
            budgets = self.db.query(Budget).filter(Budget.user_id == user_id).all()
            
            if not budgets:
                return BudgetPerformanceMetrics(
                    accuracy_score=0.0,
                    variance_stability=0.0,
                    budget_adherence_rate=0.0,
                    forecasting_improvement=0.0,
                    user_engagement_score=0.0
                )
            
            # Calculate accuracy score (how accurate have forecasts been)
            accuracy_scores = []
            variance_percentages = []
            categories_within_budget = 0
            total_categories = 0
            
            for budget in budgets:
                variance_reports = self.db.query(BudgetVarianceReport).filter(
                    BudgetVarianceReport.budget_id == budget.id
                ).order_by(desc(BudgetVarianceReport.report_date)).limit(6).all()  # Last 6 reports
                
                for report in variance_reports:
                    # Extract forecast accuracy from report
                    if report.forecast_accuracy:
                        accuracy_scores.extend(report.forecast_accuracy.get('category_accuracies', []))
                    
                    # Track variance stability
                    variance_percentages.append(abs(report.net_variance_percentage))
                    
                    # Count categories within budget
                    if report.category_variances:
                        for category_data in report.category_variances.get('categories', []):
                            total_categories += 1
                            if abs(category_data.get('variance_percentage', 100)) <= 15:  # Within 15%
                                categories_within_budget += 1
            
            # Calculate metrics
            accuracy_score = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0.0
            variance_stability = 1.0 - (sum(variance_percentages) / len(variance_percentages) / 100) if variance_percentages else 0.0
            budget_adherence_rate = categories_within_budget / total_categories if total_categories > 0 else 0.0
            
            # Calculate forecasting improvement (trend in accuracy over time)
            forecasting_improvement = self._calculate_forecasting_trend(user_id)
            
            # Calculate user engagement score
            user_engagement_score = self._calculate_user_engagement(user_id)
            
            return BudgetPerformanceMetrics(
                accuracy_score=max(0.0, min(1.0, accuracy_score)),
                variance_stability=max(0.0, min(1.0, variance_stability)),
                budget_adherence_rate=max(0.0, min(1.0, budget_adherence_rate)),
                forecasting_improvement=forecasting_improvement,
                user_engagement_score=max(0.0, min(1.0, user_engagement_score))
            )
            
        except Exception as e:
            logger.error(f"Performance metrics calculation failed for user {user_id}: {e}")
            raise
    
    # Private helper methods
    
    def _update_budget_actuals(self, budget: Budget, start_date: datetime, end_date: datetime):
        """Update budget actual amounts from transaction data."""
        try:
            # Get budget items
            budget_items = self.db.query(BudgetItem).filter(BudgetItem.budget_id == budget.id).all()
            
            for item in budget_items:
                # Get transactions for this category
                transactions = self.db.query(Transaction).filter(
                    Transaction.user_id == budget.user_id,
                    Transaction.category == item.category,
                    Transaction.is_income == item.is_income,
                    Transaction.date >= start_date,
                    Transaction.date <= end_date
                ).all()
                
                # Calculate actuals
                actual_amount = sum(abs(t.amount) for t in transactions)
                transaction_count = len(transactions)
                
                # Calculate variance
                variance_amount = actual_amount - item.budgeted_amount
                variance_percentage = (variance_amount / max(item.budgeted_amount, 1)) * 100
                
                # Determine variance type
                if item.is_income:
                    variance_type = VarianceType.FAVORABLE if variance_amount >= 0 else VarianceType.UNFAVORABLE
                else:
                    variance_type = VarianceType.UNFAVORABLE if variance_amount > 0 else VarianceType.FAVORABLE
                
                if abs(variance_percentage) <= 5:  # Within 5%
                    variance_type = VarianceType.ON_TARGET
                
                # Update or create budget actual record
                actual_record = self.db.query(BudgetActual).filter(
                    BudgetActual.budget_id == budget.id,
                    BudgetActual.category == item.category,
                    BudgetActual.period_start == start_date,
                    BudgetActual.period_end == end_date
                ).first()
                
                if actual_record:
                    actual_record.actual_amount = actual_amount
                    actual_record.transaction_count = transaction_count
                    actual_record.variance_amount = variance_amount
                    actual_record.variance_percentage = variance_percentage
                    actual_record.variance_type = variance_type
                    actual_record.last_transaction_date = max([t.date for t in transactions]) if transactions else None
                    actual_record.updated_at = datetime.utcnow()
                else:
                    actual_record = BudgetActual(
                        budget_id=budget.id,
                        period_start=start_date,
                        period_end=end_date,
                        category=item.category,
                        subcategory=item.subcategory,
                        is_income=item.is_income,
                        actual_amount=actual_amount,
                        transaction_count=transaction_count,
                        budgeted_amount=item.budgeted_amount,
                        variance_amount=variance_amount,
                        variance_percentage=variance_percentage,
                        variance_type=variance_type,
                        last_transaction_date=max([t.date for t in transactions]) if transactions else None
                    )
                    self.db.add(actual_record)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update budget actuals: {e}")
            self.db.rollback()
            raise
    
    def _calculate_income_totals(self, budget: Budget, start_date: datetime, end_date: datetime) -> Tuple[float, float]:
        """Calculate total budgeted and actual income."""
        budget_items = self.db.query(BudgetItem).filter(
            BudgetItem.budget_id == budget.id,
            BudgetItem.is_income == True
        ).all()
        
        budgeted = sum(item.budgeted_amount for item in budget_items)
        
        actual_records = self.db.query(BudgetActual).filter(
            BudgetActual.budget_id == budget.id,
            BudgetActual.is_income == True,
            BudgetActual.period_start >= start_date,
            BudgetActual.period_end <= end_date
        ).all()
        
        actual = sum(record.actual_amount for record in actual_records)
        
        return budgeted, actual
    
    def _calculate_expense_totals(self, budget: Budget, start_date: datetime, end_date: datetime) -> Tuple[float, float]:
        """Calculate total budgeted and actual expenses."""
        budget_items = self.db.query(BudgetItem).filter(
            BudgetItem.budget_id == budget.id,
            BudgetItem.is_income == False
        ).all()
        
        budgeted = sum(item.budgeted_amount for item in budget_items)
        
        actual_records = self.db.query(BudgetActual).filter(
            BudgetActual.budget_id == budget.id,
            BudgetActual.is_income == False,
            BudgetActual.period_start >= start_date,
            BudgetActual.period_end <= end_date
        ).all()
        
        actual = sum(record.actual_amount for record in actual_records)
        
        return budgeted, actual
    
    def _analyze_category_variances(self, budget: Budget, start_date: datetime, end_date: datetime) -> List[CategoryVariance]:
        """Analyze variance for each budget category."""
        variances = []
        
        actual_records = self.db.query(BudgetActual).filter(
            BudgetActual.budget_id == budget.id,
            BudgetActual.period_start >= start_date,
            BudgetActual.period_end <= end_date
        ).all()
        
        for record in actual_records:
            # Determine trend (would need historical data for full implementation)
            trend = "stable"  # Simplified for now
            
            variance = CategoryVariance(
                category=record.category,
                subcategory=record.subcategory,
                budgeted=record.budgeted_amount,
                actual=record.actual_amount,
                variance_amount=record.variance_amount,
                variance_percentage=record.variance_percentage,
                variance_type=record.variance_type,
                transaction_count=record.transaction_count,
                trend=trend
            )
            variances.append(variance)
        
        return variances
    
    def _generate_variance_recommendations(
        self, 
        budget: Budget, 
        category_variances: List[CategoryVariance],
        over_budget_categories: List[str],
        critical_categories: List[str]
    ) -> List[str]:
        """Generate actionable recommendations based on variance analysis."""
        recommendations = []
        
        if critical_categories:
            recommendations.append(f"Immediate attention needed: {', '.join(critical_categories)} are significantly over budget")
        
        if over_budget_categories:
            recommendations.append(f"Consider reducing spending in: {', '.join(over_budget_categories)}")
        
        # Analyze specific patterns
        high_variance_categories = [cv for cv in category_variances if abs(cv.variance_percentage) > 25]
        if high_variance_categories:
            recommendations.append("Review budgeting assumptions for high-variance categories")
        
        # Income vs expense recommendations
        income_variances = [cv for cv in category_variances if cv.category.lower() in ['income', 'revenue', 'sales']]
        if any(cv.variance_type == VarianceType.UNFAVORABLE for cv in income_variances):
            recommendations.append("Consider strategies to increase income or review revenue projections")
        
        return recommendations
    
    def _calculate_forecast_accuracy(self, budget: Budget, start_date: datetime, end_date: datetime) -> Optional[Dict[str, float]]:
        """Calculate how accurate previous forecasts were."""
        # This would compare previous forecast predictions with actual results
        # Simplified implementation for now
        return {
            "overall_accuracy": 0.75,
            "income_accuracy": 0.80,
            "expense_accuracy": 0.70
        }
    
    def _save_variance_report(self, budget: Budget, analysis: BudgetVarianceAnalysis):
        """Save comprehensive variance report to database."""
        try:
            report = BudgetVarianceReport(
                budget_id=budget.id,
                report_date=datetime.utcnow(),
                period_start=analysis.period_start,
                period_end=analysis.period_end,
                total_income_budgeted=analysis.total_income_budgeted,
                total_income_actual=analysis.total_income_actual,
                total_expense_budgeted=analysis.total_expense_budgeted,
                total_expense_actual=analysis.total_expense_actual,
                net_variance_amount=analysis.net_variance_amount,
                net_variance_percentage=analysis.net_variance_percentage,
                category_variances={"categories": [cv.dict() for cv in analysis.category_variances]},
                variance_alerts={"alerts": analysis.recommendations},
                recommendations={"items": analysis.recommendations},
                generated_by="system",
                report_type="standard"
            )
            
            self.db.add(report)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to save variance report: {e}")
            self.db.rollback()
    
    def _get_forecast_period_dates(self, forecast_period: str) -> Tuple[datetime, datetime]:
        """Get start and end dates for forecast period."""
        now = datetime.utcnow()
        
        if forecast_period == "next_month":
            start = (now.replace(day=1) + timedelta(days=32)).replace(day=1)
            end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        elif forecast_period == "next_quarter":
            # Simplified quarter logic
            start = now + timedelta(days=90)
            end = start + timedelta(days=90)
        else:  # Default to next month
            start = (now.replace(day=1) + timedelta(days=32)).replace(day=1)
            end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        return start, end
    
    def _extract_category_forecast(self, forecast_result: Dict, category: str, is_income: bool) -> Dict[str, float]:
        """Extract category-specific forecast from forecasting engine results."""
        # This would integrate with the actual forecasting engine output
        # Simplified for now
        base_amount = forecast_result.get('total_forecast', 1000)
        return {
            'amount': base_amount * 0.1,  # Simplified allocation
            'confidence': forecast_result.get('confidence', 0.7)
        }
    
    def _generate_forecast_recommendations(
        self, 
        forecasted_income: float, 
        forecasted_expenses: float,
        budget: Budget,
        predicted_variance: float,
        risk_factors: List[str]
    ) -> List[str]:
        """Generate recommendations based on forecast results."""
        recommendations = []
        
        if predicted_variance < 0:
            recommendations.append(f"Budget shortfall of ${abs(predicted_variance):.2f} predicted")
            recommendations.append("Consider reducing discretionary expenses or increasing income")
        elif predicted_variance > budget.total_income_budget * 0.1:
            recommendations.append("Significant budget surplus predicted - consider additional investments")
        
        if len(risk_factors) > 2:
            recommendations.append("High uncertainty in forecast - monitor closely and adjust as needed")
        
        return recommendations
    
    def _calculate_forecasting_trend(self, user_id: int) -> float:
        """Calculate trend in forecasting accuracy over time."""
        # This would analyze historical forecast accuracy
        # Simplified implementation returning a trend score
        return 0.05  # 5% improvement
    
    def _calculate_user_engagement(self, user_id: int) -> float:
        """Calculate user engagement score based on budget management activity."""
        try:
            # Check budget creation and updates
            budget_count = self.db.query(Budget).filter(Budget.user_id == user_id).count()
            
            # Check recent activity (last 30 days)
            recent_updates = self.db.query(Budget).filter(
                Budget.user_id == user_id,
                Budget.updated_at >= datetime.utcnow() - timedelta(days=30)
            ).count()
            
            # Simple engagement score calculation
            engagement_score = min(1.0, (budget_count * 0.2 + recent_updates * 0.3))
            
            return engagement_score
            
        except Exception:
            return 0.5  # Default moderate engagement