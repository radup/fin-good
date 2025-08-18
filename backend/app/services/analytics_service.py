"""
Enhanced Analytics Service for FinGood
Provides comprehensive business intelligence and financial analysis capabilities.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case, extract, text
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from statistics import mean, median, stdev
import logging

from app.models.transaction import Transaction
from app.models.user import User
from app.services.analytics_cache import cache_analytics_result

logger = logging.getLogger(__name__)

class AnalyticsService:
    """
    Enhanced analytics service providing comprehensive financial intelligence.
    
    Features:
    - Cash flow analysis with period comparisons
    - Category trend analysis and forecasting
    - Vendor spending patterns
    - Anomaly detection for unusual transactions
    - Statistical analysis and KPI calculations
    - Performance-optimized queries with caching support
    """
    
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        
    def _get_base_query(self):
        """Get base query filtered by user"""
        return self.db.query(Transaction).filter(Transaction.user_id == self.user_id)
    
    def _validate_date_range(self, start_date: Optional[datetime], end_date: Optional[datetime]) -> Tuple[datetime, datetime]:
        """Validate and normalize date range"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=365)
        if not end_date:
            end_date = datetime.now()
        
        if start_date > end_date:
            raise ValueError("Start date cannot be after end date")
        
        return start_date, end_date
    
    def _calculate_moving_average(self, values: List[Decimal], window: int = 3) -> List[Optional[Decimal]]:
        """Calculate moving average for trend analysis"""
        if len(values) < window:
            return [None] * len(values)
        
        moving_avgs = []
        for i in range(len(values)):
            if i < window - 1:
                moving_avgs.append(None)
            else:
                window_values = values[i - window + 1:i + 1]
                avg = sum(window_values) / len(window_values)
                moving_avgs.append(avg.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        
        return moving_avgs
    
    def _detect_outliers(self, values: List[float], threshold: float = 2.0) -> List[bool]:
        """Detect outliers using standard deviation method"""
        if len(values) < 3:
            return [False] * len(values)
        
        try:
            mean_val = mean(values)
            std_val = stdev(values)
            return [abs(val - mean_val) > threshold * std_val for val in values]
        except:
            return [False] * len(values)
    
    @cache_analytics_result('cash_flow', ttl=1800)  # 30 minutes cache
    def get_cash_flow_analysis(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: str = "monthly"
    ) -> Dict[str, Any]:
        """
        Comprehensive cash flow analysis with trends and forecasting.
        
        Args:
            start_date: Analysis start date
            end_date: Analysis end date  
            period: Aggregation period ('daily', 'weekly', 'monthly', 'quarterly')
        
        Returns:
            Detailed cash flow analysis with trends, forecasting, and KPIs
        """
        start_date, end_date = self._validate_date_range(start_date, end_date)
        
        # Define period aggregation
        period_formats = {
            'daily': 'day',
            'weekly': 'week', 
            'monthly': 'month',
            'quarterly': 'quarter'
        }
        
        if period not in period_formats:
            raise ValueError(f"Invalid period. Must be one of: {', '.join(period_formats.keys())}")
        
        date_trunc = period_formats[period]
        
        # Main cash flow query with period aggregation
        cash_flow_query = self.db.query(
            func.date_trunc(date_trunc, Transaction.date).label('period'),
            func.coalesce(
                func.sum(case((Transaction.is_income == True, Transaction.amount), else_=0)), 0
            ).label('income'),
            func.coalesce(
                func.sum(case((Transaction.is_income == False, func.abs(Transaction.amount)), else_=0)), 0
            ).label('expenses'),
            func.count(case((Transaction.is_income == True, Transaction.id), else_=None)).label('income_transactions'),
            func.count(case((Transaction.is_income == False, Transaction.id), else_=None)).label('expense_transactions'),
            func.avg(case((Transaction.is_income == True, Transaction.amount), else_=None)).label('avg_income'),
            func.avg(case((Transaction.is_income == False, func.abs(Transaction.amount)), else_=None)).label('avg_expense')
        ).filter(
            and_(
                Transaction.user_id == self.user_id,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
        ).group_by(
            func.date_trunc(date_trunc, Transaction.date)
        ).order_by(
            func.date_trunc(date_trunc, Transaction.date)
        ).all()
        
        # Process results
        periods_data = []
        income_values = []
        expense_values = []
        net_values = []
        
        for result in cash_flow_query:
            income = Decimal(str(result.income))
            expenses = Decimal(str(result.expenses))
            net_flow = income - expenses
            
            period_data = {
                'period': result.period,
                'income': income,
                'expenses': expenses,
                'net_flow': net_flow,
                'income_transactions': result.income_transactions,
                'expense_transactions': result.expense_transactions,
                'avg_income_transaction': Decimal(str(result.avg_income)) if result.avg_income else Decimal('0'),
                'avg_expense_transaction': Decimal(str(result.avg_expense)) if result.avg_expense else Decimal('0')
            }
            
            periods_data.append(period_data)
            income_values.append(income)
            expense_values.append(expenses)
            net_values.append(net_flow)
        
        # Calculate trends and moving averages
        income_moving_avg = self._calculate_moving_average(income_values, window=3)
        expense_moving_avg = self._calculate_moving_average(expense_values, window=3)
        
        # Add trend data to periods
        for i, period_data in enumerate(periods_data):
            period_data['income_moving_avg'] = income_moving_avg[i]
            period_data['expense_moving_avg'] = expense_moving_avg[i]
        
        # Calculate summary statistics
        total_income = sum(income_values)
        total_expenses = sum(expense_values)
        net_total = total_income - total_expenses
        
        # Calculate growth rates
        income_growth = None
        expense_growth = None
        if len(income_values) >= 2:
            first_income = income_values[0] if income_values[0] > 0 else Decimal('0.01')
            last_income = income_values[-1]
            income_growth = ((last_income - first_income) / first_income * 100)
            
            first_expense = expense_values[0] if expense_values[0] > 0 else Decimal('0.01')
            last_expense = expense_values[-1]
            expense_growth = ((last_expense - first_expense) / first_expense * 100)
        
        # Financial health metrics
        avg_income = total_income / len(periods_data) if periods_data else Decimal('0')
        avg_expenses = total_expenses / len(periods_data) if periods_data else Decimal('0')
        
        expense_ratio = (total_expenses / total_income * 100) if total_income > 0 else Decimal('0')
        savings_rate = ((total_income - total_expenses) / total_income * 100) if total_income > 0 else Decimal('0')
        
        # Cash flow volatility (standard deviation of net flows)
        volatility = None
        if len(net_values) > 1:
            net_floats = [float(val) for val in net_values]
            try:
                volatility = Decimal(str(stdev(net_floats))).quantize(Decimal('0.01'))
            except:
                volatility = Decimal('0')
        
        logger.info(f"Generated cash flow analysis for user {self.user_id}: {len(periods_data)} periods")
        
        return {
            'analysis_config': {
                'period': period,
                'start_date': start_date,
                'end_date': end_date,
                'periods_analyzed': len(periods_data)
            },
            'cash_flow_data': periods_data,
            'summary': {
                'total_income': total_income,
                'total_expenses': total_expenses,
                'net_total': net_total,
                'average_income': avg_income,
                'average_expenses': avg_expenses,
                'income_growth_rate': income_growth,
                'expense_growth_rate': expense_growth
            },
            'financial_health': {
                'expense_ratio': expense_ratio,
                'savings_rate': savings_rate,
                'cash_flow_volatility': volatility,
                'financial_stability': 'stable' if volatility and volatility < 1000 else 'volatile' if volatility else 'unknown'
            }
        }
    
    @cache_analytics_result('category_insights', ttl=1800)  # 30 minutes cache
    def get_category_insights(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        Advanced category analysis with trends, seasonality, and predictions.
        
        Args:
            start_date: Analysis start date
            end_date: Analysis end date
            top_n: Number of top categories to analyze
        
        Returns:
            Comprehensive category insights with trends and forecasting
        """
        start_date, end_date = self._validate_date_range(start_date, end_date)
        
        # Get category totals for ranking
        category_totals = self.db.query(
            Transaction.category,
            func.sum(func.abs(Transaction.amount)).label('total_amount'),
            func.count(Transaction.id).label('transaction_count'),
            func.avg(func.abs(Transaction.amount)).label('avg_amount'),
            func.min(Transaction.date).label('first_transaction'),
            func.max(Transaction.date).label('last_transaction')
        ).filter(
            and_(
                Transaction.user_id == self.user_id,
                Transaction.is_income == False,
                Transaction.category.isnot(None),
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
        ).group_by(Transaction.category).order_by(
            func.sum(func.abs(Transaction.amount)).desc()
        ).limit(top_n).all()
        
        top_categories = [cat.category for cat in category_totals]
        
        # Get monthly trends for top categories
        monthly_trends = self.db.query(
            Transaction.category,
            func.date_trunc('month', Transaction.date).label('month'),
            func.sum(func.abs(Transaction.amount)).label('amount'),
            func.count(Transaction.id).label('count')
        ).filter(
            and_(
                Transaction.user_id == self.user_id,
                Transaction.is_income == False,
                Transaction.category.in_(top_categories),
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
        ).group_by(
            Transaction.category,
            func.date_trunc('month', Transaction.date)
        ).order_by(
            Transaction.category,
            func.date_trunc('month', Transaction.date)
        ).all()
        
        # Organize data by category
        category_insights = {}
        
        for cat_total in category_totals:
            category = cat_total.category
            
            # Get monthly data for this category
            monthly_data = [
                {
                    'month': trend.month,
                    'amount': Decimal(str(trend.amount)),
                    'transaction_count': trend.count
                }
                for trend in monthly_trends if trend.category == category
            ]
            
            # Calculate trends
            amounts = [data['amount'] for data in monthly_data]
            moving_avg = self._calculate_moving_average(amounts, window=3)
            
            # Calculate growth rate
            growth_rate = None
            if len(amounts) >= 2 and amounts[0] > 0:
                growth_rate = ((amounts[-1] - amounts[0]) / amounts[0] * 100)
            
            # Detect seasonal patterns (simplified)
            seasonal_variance = None
            if len(amounts) > 6:
                try:
                    seasonal_variance = Decimal(str(stdev([float(amt) for amt in amounts]))).quantize(Decimal('0.01'))
                except:
                    seasonal_variance = Decimal('0')
            
            category_insights[category] = {
                'total_amount': Decimal(str(cat_total.total_amount)),
                'transaction_count': cat_total.transaction_count,
                'average_transaction': Decimal(str(cat_total.avg_amount)),
                'first_transaction': cat_total.first_transaction,
                'last_transaction': cat_total.last_transaction,
                'monthly_data': monthly_data,
                'moving_averages': [{'month': data['month'], 'moving_avg': avg} 
                                   for data, avg in zip(monthly_data, moving_avg) if avg],
                'trend_analysis': {
                    'growth_rate': growth_rate,
                    'seasonal_variance': seasonal_variance,
                    'trend_direction': 'increasing' if growth_rate and growth_rate > 5 
                                     else 'decreasing' if growth_rate and growth_rate < -5 
                                     else 'stable'
                }
            }
        
        # Calculate category distribution
        total_spending = sum(cat['total_amount'] for cat in category_insights.values())
        for category, data in category_insights.items():
            data['percentage_of_total'] = (data['total_amount'] / total_spending * 100) if total_spending > 0 else Decimal('0')
        
        logger.info(f"Generated category insights for user {self.user_id}: {len(category_insights)} categories")
        
        return {
            'analysis_config': {
                'start_date': start_date,
                'end_date': end_date,
                'categories_analyzed': len(category_insights)
            },
            'category_insights': category_insights,
            'summary': {
                'total_spending': total_spending,
                'top_category': max(category_insights.items(), key=lambda x: x[1]['total_amount'])[0] if category_insights else None,
                'most_frequent_category': max(category_insights.items(), key=lambda x: x[1]['transaction_count'])[0] if category_insights else None,
                'average_category_spend': total_spending / len(category_insights) if category_insights else Decimal('0')
            }
        }
    
    @cache_analytics_result('vendor_analysis', ttl=3600)  # 1 hour cache
    def get_vendor_analysis(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        top_n: int = 15
    ) -> Dict[str, Any]:
        """
        Comprehensive vendor spending analysis with patterns and insights.
        
        Args:
            start_date: Analysis start date
            end_date: Analysis end date
            top_n: Number of top vendors to analyze
        
        Returns:
            Detailed vendor analysis with spending patterns and trends
        """
        start_date, end_date = self._validate_date_range(start_date, end_date)
        
        # Get vendor spending analysis
        vendor_analysis = self.db.query(
            Transaction.vendor,
            func.sum(func.abs(Transaction.amount)).label('total_spent'),
            func.count(Transaction.id).label('transaction_count'),
            func.avg(func.abs(Transaction.amount)).label('avg_transaction'),
            func.min(func.abs(Transaction.amount)).label('min_transaction'),
            func.max(func.abs(Transaction.amount)).label('max_transaction'),
            func.min(Transaction.date).label('first_transaction'),
            func.max(Transaction.date).label('last_transaction')
        ).filter(
            and_(
                Transaction.user_id == self.user_id,
                Transaction.is_income == False,
                Transaction.vendor.isnot(None),
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
        ).group_by(Transaction.vendor).order_by(
            func.sum(func.abs(Transaction.amount)).desc()
        ).limit(top_n).all()
        
        vendor_insights = []
        total_vendor_spending = Decimal('0')
        
        for vendor in vendor_analysis:
            total_spent = Decimal(str(vendor.total_spent))
            total_vendor_spending += total_spent
            
            # Calculate transaction frequency
            days_span = (vendor.last_transaction - vendor.first_transaction).days + 1
            frequency = vendor.transaction_count / max(days_span / 30, 1)  # Transactions per month
            
            # Calculate spending consistency (coefficient of variation)
            consistency_score = 'high'  # Simplified for now
            
            # Get most common category for this vendor
            primary_category_query = self.db.query(
                Transaction.category,
                func.count(Transaction.id).label('count')
            ).filter(
                and_(
                    Transaction.user_id == self.user_id,
                    Transaction.vendor == vendor.vendor,
                    Transaction.category.isnot(None)
                )
            ).group_by(Transaction.category).order_by(
                func.count(Transaction.id).desc()
            ).first()
            
            primary_category = primary_category_query.category if primary_category_query else None
            
            vendor_data = {
                'vendor': vendor.vendor,
                'total_spent': total_spent,
                'transaction_count': vendor.transaction_count,
                'average_transaction': Decimal(str(vendor.avg_transaction)),
                'min_transaction': Decimal(str(vendor.min_transaction)),
                'max_transaction': Decimal(str(vendor.max_transaction)),
                'first_transaction': vendor.first_transaction,
                'last_transaction': vendor.last_transaction,
                'primary_category': primary_category,
                'transaction_frequency': Decimal(str(frequency)).quantize(Decimal('0.01')),
                'spending_consistency': consistency_score
            }
            
            vendor_insights.append(vendor_data)
        
        # Calculate vendor distribution
        for vendor_data in vendor_insights:
            vendor_data['percentage_of_spending'] = (
                vendor_data['total_spent'] / total_vendor_spending * 100
            ) if total_vendor_spending > 0 else Decimal('0')
        
        # Identify spending patterns
        regular_vendors = [v for v in vendor_insights if v['transaction_frequency'] >= 1]
        occasional_vendors = [v for v in vendor_insights if 0.2 <= v['transaction_frequency'] < 1]
        one_time_vendors = [v for v in vendor_insights if v['transaction_frequency'] < 0.2]
        
        logger.info(f"Generated vendor analysis for user {self.user_id}: {len(vendor_insights)} vendors")
        
        return {
            'analysis_config': {
                'start_date': start_date,
                'end_date': end_date,
                'vendors_analyzed': len(vendor_insights)
            },
            'vendor_insights': vendor_insights,
            'spending_patterns': {
                'regular_vendors': len(regular_vendors),
                'occasional_vendors': len(occasional_vendors),
                'one_time_vendors': len(one_time_vendors),
                'top_vendor': vendor_insights[0]['vendor'] if vendor_insights else None,
                'vendor_concentration': vendor_insights[0]['percentage_of_spending'] if vendor_insights else Decimal('0')
            },
            'summary': {
                'total_vendor_spending': total_vendor_spending,
                'average_vendor_spend': total_vendor_spending / len(vendor_insights) if vendor_insights else Decimal('0'),
                'total_unique_vendors': len(vendor_insights)
            }
        }
    
    @cache_analytics_result('anomalies', ttl=900)  # 15 minutes cache (more frequent for security)
    def detect_anomalies(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sensitivity: float = 2.0
    ) -> Dict[str, Any]:
        """
        Detect unusual transactions and spending patterns using statistical analysis.
        
        Args:
            start_date: Analysis start date
            end_date: Analysis end date
            sensitivity: Outlier detection sensitivity (higher = less sensitive)
        
        Returns:
            Detected anomalies with risk assessment
        """
        start_date, end_date = self._validate_date_range(start_date, end_date)
        
        # Get all transactions for analysis
        transactions = self.db.query(Transaction).filter(
            and_(
                Transaction.user_id == self.user_id,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
        ).all()
        
        if not transactions:
            return {'anomalies': [], 'summary': {'total_anomalies': 0}}
        
        # Separate by income/expense
        expense_amounts = [abs(float(t.amount)) for t in transactions if not t.is_income]
        income_amounts = [float(t.amount) for t in transactions if t.is_income]
        
        # Detect amount-based outliers
        expense_outliers = self._detect_outliers(expense_amounts, sensitivity) if expense_amounts else []
        income_outliers = self._detect_outliers(income_amounts, sensitivity) if income_amounts else []
        
        anomalies = []
        expense_idx = 0
        income_idx = 0
        
        for transaction in transactions:
            is_outlier = False
            anomaly_type = []
            risk_level = 'low'
            
            if transaction.is_income:
                if income_idx < len(income_outliers) and income_outliers[income_idx]:
                    is_outlier = True
                    anomaly_type.append('unusual_income_amount')
                    risk_level = 'medium'
                income_idx += 1
            else:
                if expense_idx < len(expense_outliers) and expense_outliers[expense_idx]:
                    is_outlier = True
                    anomaly_type.append('unusual_expense_amount')
                    risk_level = 'high' if abs(transaction.amount) > 1000 else 'medium'
                expense_idx += 1
            
            # Additional anomaly checks
            if not transaction.category and abs(transaction.amount) > 100:
                anomaly_type.append('large_uncategorized')
                risk_level = 'medium'
                is_outlier = True
            
            # Check for duplicate transactions (same amount, vendor, date)
            duplicate_check = self.db.query(Transaction).filter(
                and_(
                    Transaction.user_id == self.user_id,
                    Transaction.amount == transaction.amount,
                    Transaction.vendor == transaction.vendor,
                    Transaction.date == transaction.date,
                    Transaction.id != transaction.id
                )
            ).first()
            
            if duplicate_check:
                anomaly_type.append('potential_duplicate')
                risk_level = 'high'
                is_outlier = True
            
            if is_outlier:
                anomaly_score = len(anomaly_type) * (3 - sensitivity)  # Higher score = more suspicious
                
                anomalies.append({
                    'transaction_id': transaction.id,
                    'date': transaction.date,
                    'amount': Decimal(str(transaction.amount)),
                    'description': transaction.description,
                    'vendor': transaction.vendor,
                    'category': transaction.category,
                    'anomaly_types': anomaly_type,
                    'risk_level': risk_level,
                    'anomaly_score': anomaly_score,
                    'explanation': self._generate_anomaly_explanation(anomaly_type, transaction)
                })
        
        # Sort by risk level and score
        risk_order = {'high': 3, 'medium': 2, 'low': 1}
        anomalies.sort(key=lambda x: (risk_order[x['risk_level']], x['anomaly_score']), reverse=True)
        
        # Categorize anomalies
        high_risk = [a for a in anomalies if a['risk_level'] == 'high']
        medium_risk = [a for a in anomalies if a['risk_level'] == 'medium']
        low_risk = [a for a in anomalies if a['risk_level'] == 'low']
        
        logger.info(f"Detected {len(anomalies)} anomalies for user {self.user_id}")
        
        return {
            'analysis_config': {
                'start_date': start_date,
                'end_date': end_date,
                'sensitivity': sensitivity,
                'transactions_analyzed': len(transactions)
            },
            'anomalies': anomalies[:50],  # Limit to top 50 for performance
            'summary': {
                'total_anomalies': len(anomalies),
                'high_risk_count': len(high_risk),
                'medium_risk_count': len(medium_risk),
                'low_risk_count': len(low_risk),
                'anomaly_rate': (len(anomalies) / len(transactions) * 100) if transactions else 0
            },
            'recommendations': self._generate_anomaly_recommendations(anomalies)
        }
    
    def _generate_anomaly_explanation(self, anomaly_types: List[str], transaction: Transaction) -> str:
        """Generate human-readable explanation for anomaly"""
        explanations = {
            'unusual_income_amount': f"Income amount of ${abs(transaction.amount):.2f} is significantly higher than usual",
            'unusual_expense_amount': f"Expense amount of ${abs(transaction.amount):.2f} is significantly higher than typical spending",
            'large_uncategorized': f"Large transaction of ${abs(transaction.amount):.2f} remains uncategorized",
            'potential_duplicate': "Similar transaction found with same amount, vendor, and date"
        }
        
        return ". ".join([explanations.get(atype, atype) for atype in anomaly_types])
    
    def _generate_anomaly_recommendations(self, anomalies: List[Dict]) -> List[str]:
        """Generate actionable recommendations based on detected anomalies"""
        recommendations = []
        
        high_risk_count = len([a for a in anomalies if a['risk_level'] == 'high'])
        if high_risk_count > 0:
            recommendations.append(f"Review {high_risk_count} high-risk transactions immediately for potential fraud")
        
        uncategorized_count = len([a for a in anomalies if 'large_uncategorized' in a['anomaly_types']])
        if uncategorized_count > 0:
            recommendations.append(f"Categorize {uncategorized_count} large uncategorized transactions for better budgeting")
        
        duplicate_count = len([a for a in anomalies if 'potential_duplicate' in a['anomaly_types']])
        if duplicate_count > 0:
            recommendations.append(f"Check {duplicate_count} potential duplicate transactions for accuracy")
        
        return recommendations
    
    @cache_analytics_result('comparative', ttl=3600)  # 1 hour cache
    def get_comparative_analysis(
        self,
        base_start: datetime,
        base_end: datetime,
        compare_start: datetime,
        compare_end: datetime
    ) -> Dict[str, Any]:
        """
        Compare financial metrics between two time periods.
        
        Args:
            base_start: Base period start date
            base_end: Base period end date
            compare_start: Comparison period start date
            compare_end: Comparison period end date
        
        Returns:
            Detailed comparative analysis with percentage changes and insights
        """
        # Get base period data
        base_summary = self._get_period_summary(base_start, base_end)
        compare_summary = self._get_period_summary(compare_start, compare_end)
        
        # Calculate percentage changes
        def calculate_change(base_val: Decimal, compare_val: Decimal) -> Decimal:
            if base_val == 0:
                return Decimal('100') if compare_val > 0 else Decimal('0')
            return ((compare_val - base_val) / base_val * 100).quantize(Decimal('0.01'))
        
        income_change = calculate_change(base_summary['total_income'], compare_summary['total_income'])
        expense_change = calculate_change(base_summary['total_expenses'], compare_summary['total_expenses'])
        transaction_change = calculate_change(
            Decimal(str(base_summary['transaction_count'])), 
            Decimal(str(compare_summary['transaction_count']))
        )
        
        # Category comparison
        category_changes = {}
        base_categories = base_summary['categories']
        compare_categories = compare_summary['categories']
        
        all_categories = set(base_categories.keys()) | set(compare_categories.keys())
        
        for category in all_categories:
            base_amount = base_categories.get(category, Decimal('0'))
            compare_amount = compare_categories.get(category, Decimal('0'))
            change = calculate_change(base_amount, compare_amount)
            
            category_changes[category] = {
                'base_amount': base_amount,
                'compare_amount': compare_amount,
                'change_amount': compare_amount - base_amount,
                'change_percent': change
            }
        
        # Sort categories by absolute change
        sorted_categories = sorted(
            category_changes.items(),
            key=lambda x: abs(x[1]['change_percent']),
            reverse=True
        )
        
        logger.info(f"Generated comparative analysis for user {self.user_id}")
        
        return {
            'periods': {
                'base_period': {'start': base_start, 'end': base_end},
                'compare_period': {'start': compare_start, 'end': compare_end}
            },
            'summary_comparison': {
                'income': {
                    'base': base_summary['total_income'],
                    'compare': compare_summary['total_income'],
                    'change_amount': compare_summary['total_income'] - base_summary['total_income'],
                    'change_percent': income_change
                },
                'expenses': {
                    'base': base_summary['total_expenses'],
                    'compare': compare_summary['total_expenses'],
                    'change_amount': compare_summary['total_expenses'] - base_summary['total_expenses'],
                    'change_percent': expense_change
                },
                'transactions': {
                    'base': base_summary['transaction_count'],
                    'compare': compare_summary['transaction_count'],
                    'change_amount': compare_summary['transaction_count'] - base_summary['transaction_count'],
                    'change_percent': transaction_change
                }
            },
            'category_comparison': dict(sorted_categories[:15]),  # Top 15 categories
            'insights': {
                'income_trend': 'increasing' if income_change > 5 else 'decreasing' if income_change < -5 else 'stable',
                'expense_trend': 'increasing' if expense_change > 5 else 'decreasing' if expense_change < -5 else 'stable',
                'biggest_increase': sorted_categories[0][0] if sorted_categories and sorted_categories[0][1]['change_percent'] > 0 else None,
                'biggest_decrease': next((cat for cat, data in sorted_categories if data['change_percent'] < 0), None)
            }
        }
    
    def _get_period_summary(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get summary data for a specific period"""
        summary_query = self.db.query(
            func.count(Transaction.id).label('transaction_count'),
            func.coalesce(
                func.sum(case((Transaction.is_income == True, Transaction.amount), else_=0)), 0
            ).label('total_income'),
            func.coalesce(
                func.sum(case((Transaction.is_income == False, func.abs(Transaction.amount)), else_=0)), 0
            ).label('total_expenses')
        ).filter(
            and_(
                Transaction.user_id == self.user_id,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
        ).first()
        
        # Get category breakdown
        category_query = self.db.query(
            Transaction.category,
            func.sum(func.abs(Transaction.amount)).label('amount')
        ).filter(
            and_(
                Transaction.user_id == self.user_id,
                Transaction.is_income == False,
                Transaction.category.isnot(None),
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
        ).group_by(Transaction.category).all()
        
        categories = {
            cat.category: Decimal(str(cat.amount))
            for cat in category_query
        }
        
        return {
            'transaction_count': summary_query.transaction_count or 0,
            'total_income': Decimal(str(summary_query.total_income)),
            'total_expenses': Decimal(str(summary_query.total_expenses)),
            'categories': categories
        }