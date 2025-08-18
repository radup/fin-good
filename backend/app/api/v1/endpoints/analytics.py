from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case, extract
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from app.core.database import get_db
from app.models.user import User
from app.models.transaction import Transaction
from app.core.cookie_auth import get_current_user_from_cookie
from app.schemas.transaction import TransactionSummary
from app.core.error_codes import ErrorCode
from app.core.exceptions import FinancialAnalyticsError

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/summary", response_model=TransactionSummary)
async def get_transaction_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Get transaction summary with totals and category breakdown using optimized SQL aggregation"""
    try:
        # Build base query with user filter
        base_query = db.query(Transaction).filter(Transaction.user_id == current_user.id)
        
        # Apply date filters
        if start_date:
            base_query = base_query.filter(Transaction.date >= start_date)
        if end_date:
            base_query = base_query.filter(Transaction.date <= end_date)
        
        # Single query to get all summary statistics using SQL aggregation
        summary_stats = db.query(
            func.count(Transaction.id).label('total_transactions'),
            func.coalesce(
                func.sum(
                    case(
                        (Transaction.is_income == True, Transaction.amount),
                        else_=0
                    )
                ), 0
            ).label('total_income'),
            func.coalesce(
                func.sum(
                    case(
                        (Transaction.is_income == False, func.abs(Transaction.amount)),
                        else_=0
                    )
                ), 0
            ).label('total_expenses'),
            func.sum(
                case(
                    (Transaction.is_categorized == True, 1),
                    else_=0
                )
            ).label('categorized_count')
        ).filter(Transaction.user_id == current_user.id)
        
        # Apply same date filters to summary query
        if start_date:
            summary_stats = summary_stats.filter(Transaction.date >= start_date)
        if end_date:
            summary_stats = summary_stats.filter(Transaction.date <= end_date)
        
        result = summary_stats.first()
        
        # Handle case where no transactions exist
        if not result or result.total_transactions == 0:
            return TransactionSummary(
                total_transactions=0,
                total_income=Decimal('0.00'),
                total_expenses=Decimal('0.00'),
                categorized_count=0,
                uncategorized_count=0,
                categories={}
            )
        
        # Calculate uncategorized count
        uncategorized_count = result.total_transactions - (result.categorized_count or 0)
        
        # Separate query for category breakdown (expenses only)
        category_query = db.query(
            Transaction.category,
            func.sum(func.abs(Transaction.amount)).label('amount')
        ).filter(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.is_income == False,
                Transaction.category.isnot(None)
            )
        )
        
        # Apply same date filters to category query
        if start_date:
            category_query = category_query.filter(Transaction.date >= start_date)
        if end_date:
            category_query = category_query.filter(Transaction.date <= end_date)
        
        category_results = category_query.group_by(Transaction.category).all()
        
        # Convert category results to dictionary with Decimal values
        categories = {
            cat.category: Decimal(str(cat.amount))
            for cat in category_results
        }
        
        logger.info(
            f"Generated transaction summary for user {current_user.id}: "
            f"{result.total_transactions} transactions, "
            f"${result.total_income} income, ${result.total_expenses} expenses"
        )
        
        return TransactionSummary(
            total_transactions=result.total_transactions,
            total_income=Decimal(str(result.total_income)),
            total_expenses=Decimal(str(result.total_expenses)),
            categorized_count=result.categorized_count or 0,
            uncategorized_count=uncategorized_count,
            categories=categories
        )
        
    except Exception as e:
        logger.error(f"Error generating transaction summary for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate transaction summary. Please try again."
        ) from e

@router.get("/monthly")
async def get_monthly_summary(
    year: int = Query(..., description="Year to analyze", ge=2000, le=2100),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Get monthly transaction summary for a year using optimized SQL aggregation"""
    try:
        # Validate year is reasonable
        current_year = datetime.now().year
        if year > current_year + 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Year {year} is too far in the future"
            )
        
        # Single optimized query to get all monthly data for the year
        monthly_stats = db.query(
            extract('month', Transaction.date).label('month'),
            func.count(Transaction.id).label('transaction_count'),
            func.coalesce(
                func.sum(
                    case(
                        (Transaction.is_income == True, Transaction.amount),
                        else_=0
                    )
                ), 0
            ).label('income'),
            func.coalesce(
                func.sum(
                    case(
                        (Transaction.is_income == False, func.abs(Transaction.amount)),
                        else_=0
                    )
                ), 0
            ).label('expenses')
        ).filter(
            and_(
                Transaction.user_id == current_user.id,
                extract('year', Transaction.date) == year
            )
        ).group_by(
            extract('month', Transaction.date)
        ).order_by(
            extract('month', Transaction.date)
        ).all()
        
        # Create a dictionary for quick lookup
        monthly_dict = {
            int(stat.month): {
                'month': int(stat.month),
                'year': year,
                'transaction_count': stat.transaction_count,
                'income': Decimal(str(stat.income)),
                'expenses': Decimal(str(stat.expenses)),
                'net': Decimal(str(stat.income)) - Decimal(str(stat.expenses))
            }
            for stat in monthly_stats
        }
        
        # Ensure all 12 months are represented (fill missing months with zeros)
        monthly_data = []
        for month in range(1, 13):
            if month in monthly_dict:
                monthly_data.append(monthly_dict[month])
            else:
                monthly_data.append({
                    'month': month,
                    'year': year,
                    'transaction_count': 0,
                    'income': Decimal('0.00'),
                    'expenses': Decimal('0.00'),
                    'net': Decimal('0.00')
                })
        
        # Calculate summary statistics
        total_transactions = sum(m['transaction_count'] for m in monthly_data)
        total_income = sum(m['income'] for m in monthly_data)
        total_expenses = sum(m['expenses'] for m in monthly_data)
        
        logger.info(
            f"Generated monthly summary for user {current_user.id}, year {year}: "
            f"{total_transactions} transactions, ${total_income} income, ${total_expenses} expenses"
        )
        
        return {
            'year': year,
            'monthly_data': monthly_data,
            'summary': {
                'total_transactions': total_transactions,
                'total_income': total_income,
                'total_expenses': total_expenses,
                'net_total': total_income - total_expenses
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating monthly summary for user {current_user.id}, year {year}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate monthly summary. Please try again."
        ) from e

@router.get("/top-categories")
async def get_top_categories(
    limit: int = Query(10, ge=1, le=50),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Get top spending categories with enhanced aggregation and error handling"""
    try:
        # Validate date range if provided
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date cannot be after end date"
            )
        
        # Optimized query with enhanced aggregation
        query = db.query(
            Transaction.category,
            func.sum(func.abs(Transaction.amount)).label('total_amount'),
            func.count(Transaction.id).label('transaction_count'),
            func.avg(func.abs(Transaction.amount)).label('avg_amount'),
            func.min(Transaction.date).label('first_transaction'),
            func.max(Transaction.date).label('last_transaction')
        ).filter(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.is_income == False,
                Transaction.category.isnot(None)
            )
        )
        
        # Apply date filters
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        
        results = query.group_by(Transaction.category).order_by(
            func.sum(func.abs(Transaction.amount)).desc()
        ).limit(limit).all()
        
        # Convert results to proper decimal format
        categories_data = []
        for result in results:
            categories_data.append({
                "category": result.category,
                "total_amount": Decimal(str(result.total_amount)),
                "transaction_count": result.transaction_count,
                "average_amount": Decimal(str(result.avg_amount)),
                "first_transaction": result.first_transaction,
                "last_transaction": result.last_transaction
            })
        
        # Calculate additional insights
        total_categories = len(categories_data)
        total_amount = sum(cat['total_amount'] for cat in categories_data)
        
        logger.info(
            f"Generated top {limit} categories for user {current_user.id}: "
            f"{total_categories} categories, ${total_amount} total spending"
        )
        
        return {
            "categories": categories_data,
            "summary": {
                "total_categories": total_categories,
                "total_amount": total_amount,
                "date_range": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating top categories for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate category analysis. Please try again."
        ) from e


@router.get("/trends")
async def get_spending_trends(
    period: str = Query("monthly", regex="^(daily|weekly|monthly|quarterly)$"),
    periods_count: int = Query(12, ge=1, le=60),
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Get spending trends over time with various period aggregations"""
    try:
        # Calculate the date range based on period
        current_date = datetime.now()
        
        if period == "daily":
            start_date = current_date - timedelta(days=periods_count)
            date_trunc = 'day'
        elif period == "weekly":
            start_date = current_date - timedelta(weeks=periods_count)
            date_trunc = 'week'
        elif period == "monthly":
            # Calculate months back
            start_date = current_date.replace(day=1)
            for _ in range(periods_count - 1):
                if start_date.month == 1:
                    start_date = start_date.replace(year=start_date.year - 1, month=12)
                else:
                    start_date = start_date.replace(month=start_date.month - 1)
            date_trunc = 'month'
        else:  # quarterly
            start_date = current_date - timedelta(days=periods_count * 90)
            date_trunc = 'quarter'
        
        # Build query with period aggregation
        query = db.query(
            func.date_trunc(date_trunc, Transaction.date).label('period'),
            func.count(Transaction.id).label('transaction_count'),
            func.coalesce(
                func.sum(
                    case(
                        (Transaction.is_income == True, Transaction.amount),
                        else_=0
                    )
                ), 0
            ).label('income'),
            func.coalesce(
                func.sum(
                    case(
                        (Transaction.is_income == False, func.abs(Transaction.amount)),
                        else_=0
                    )
                ), 0
            ).label('expenses')
        ).filter(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.date >= start_date
            )
        )
        
        # Add category filter if specified
        if category:
            query = query.filter(Transaction.category == category)
        
        results = query.group_by(
            func.date_trunc(date_trunc, Transaction.date)
        ).order_by(
            func.date_trunc(date_trunc, Transaction.date)
        ).all()
        
        trends_data = []
        for result in results:
            trends_data.append({
                'period': result.period,
                'transaction_count': result.transaction_count,
                'income': Decimal(str(result.income)),
                'expenses': Decimal(str(result.expenses)),
                'net': Decimal(str(result.income)) - Decimal(str(result.expenses))
            })
        
        # Calculate trend analysis
        if len(trends_data) >= 2:
            latest_expenses = trends_data[-1]['expenses']
            previous_expenses = trends_data[-2]['expenses']
            expense_change = ((latest_expenses - previous_expenses) / previous_expenses * 100) if previous_expenses > 0 else 0
        else:
            expense_change = 0
        
        logger.info(
            f"Generated {period} trends for user {current_user.id}: "
            f"{len(trends_data)} periods, category: {category or 'all'}"
        )
        
        return {
            'period_type': period,
            'periods_count': len(trends_data),
            'category_filter': category,
            'trends': trends_data,
            'analysis': {
                'expense_change_percent': Decimal(str(expense_change)),
                'date_range': {
                    'start_date': start_date,
                    'end_date': current_date
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating spending trends for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate spending trends. Please try again."
        ) from e


@router.get("/category-trends")
async def get_category_trends(
    months: int = Query(6, ge=1, le=24),
    top_categories: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Get category spending trends over time"""
    try:
        # Calculate date range
        current_date = datetime.now()
        start_date = current_date.replace(day=1)
        for _ in range(months - 1):
            if start_date.month == 1:
                start_date = start_date.replace(year=start_date.year - 1, month=12)
            else:
                start_date = start_date.replace(month=start_date.month - 1)
        
        # Get top categories first
        top_cats = db.query(
            Transaction.category,
            func.sum(func.abs(Transaction.amount)).label('total_amount')
        ).filter(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.is_income == False,
                Transaction.category.isnot(None),
                Transaction.date >= start_date
            )
        ).group_by(Transaction.category).order_by(
            func.sum(func.abs(Transaction.amount)).desc()
        ).limit(top_categories).all()
        
        top_category_names = [cat.category for cat in top_cats]
        
        # Get monthly trends for these categories
        category_trends = db.query(
            Transaction.category,
            func.date_trunc('month', Transaction.date).label('month'),
            func.sum(func.abs(Transaction.amount)).label('amount')
        ).filter(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.is_income == False,
                Transaction.category.in_(top_category_names),
                Transaction.date >= start_date
            )
        ).group_by(
            Transaction.category,
            func.date_trunc('month', Transaction.date)
        ).order_by(
            Transaction.category,
            func.date_trunc('month', Transaction.date)
        ).all()
        
        # Organize data by category
        category_data = {}
        for trend in category_trends:
            if trend.category not in category_data:
                category_data[trend.category] = []
            category_data[trend.category].append({
                'month': trend.month,
                'amount': Decimal(str(trend.amount))
            })
        
        logger.info(
            f"Generated category trends for user {current_user.id}: "
            f"{len(top_category_names)} categories over {months} months"
        )
        
        return {
            'months_analyzed': months,
            'top_categories_count': len(top_category_names),
            'date_range': {
                'start_date': start_date,
                'end_date': current_date
            },
            'category_trends': category_data,
            'top_categories': [
                {
                    'category': cat.category,
                    'total_amount': Decimal(str(cat.total_amount))
                }
                for cat in top_cats
            ]
        }
        
    except Exception as e:
        logger.error(f"Error generating category trends for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate category trends. Please try again."
        ) from e


@router.get("/budget-analysis")
async def get_budget_analysis(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2000, le=2100),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Get budget analysis comparing spending to historical averages"""
    try:
        # Default to current month/year if not specified
        current_date = datetime.now()
        target_month = month or current_date.month
        target_year = year or current_date.year
        
        # Calculate target month date range
        target_start = datetime(target_year, target_month, 1)
        if target_month == 12:
            target_end = datetime(target_year + 1, 1, 1) - timedelta(days=1)
        else:
            target_end = datetime(target_year, target_month + 1, 1) - timedelta(days=1)
        
        # Get current month spending by category
        current_spending = db.query(
            Transaction.category,
            func.sum(func.abs(Transaction.amount)).label('amount'),
            func.count(Transaction.id).label('transaction_count')
        ).filter(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.is_income == False,
                Transaction.category.isnot(None),
                Transaction.date >= target_start,
                Transaction.date <= target_end
            )
        ).group_by(Transaction.category).all()
        
        # Get historical averages (last 6 months, excluding current month)
        history_start = target_start - timedelta(days=180)  # Approximately 6 months
        
        historical_avg = db.query(
            Transaction.category,
            func.avg(
                func.sum(func.abs(Transaction.amount))
            ).over(partition_by=Transaction.category).label('avg_amount')
        ).filter(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.is_income == False,
                Transaction.category.isnot(None),
                Transaction.date >= history_start,
                Transaction.date < target_start
            )
        ).group_by(
            Transaction.category,
            func.date_trunc('month', Transaction.date)
        ).subquery()
        
        # Get the actual averages
        historical_averages = db.query(
            historical_avg.c.category,
            func.avg(historical_avg.c.avg_amount).label('avg_monthly_amount')
        ).group_by(historical_avg.c.category).all()
        
        # Create lookup for historical averages
        avg_lookup = {avg.category: Decimal(str(avg.avg_monthly_amount)) for avg in historical_averages}
        
        # Analyze budget performance
        budget_analysis = []
        total_current = Decimal('0')
        total_historical = Decimal('0')
        
        for spending in current_spending:
            category = spending.category
            current_amount = Decimal(str(spending.amount))
            historical_amount = avg_lookup.get(category, Decimal('0'))
            
            if historical_amount > 0:
                variance_percent = ((current_amount - historical_amount) / historical_amount * 100)
            else:
                variance_percent = 100 if current_amount > 0 else 0
            
            budget_analysis.append({
                'category': category,
                'current_spending': current_amount,
                'historical_average': historical_amount,
                'variance_amount': current_amount - historical_amount,
                'variance_percent': Decimal(str(variance_percent)),
                'transaction_count': spending.transaction_count,
                'status': 'over_budget' if variance_percent > 20 else 'under_budget' if variance_percent < -20 else 'on_track'
            })
            
            total_current += current_amount
            total_historical += historical_amount
        
        # Sort by highest variance
        budget_analysis.sort(key=lambda x: abs(x['variance_percent']), reverse=True)
        
        total_variance = ((total_current - total_historical) / total_historical * 100) if total_historical > 0 else 0
        
        logger.info(
            f"Generated budget analysis for user {current_user.id}: "
            f"{target_month}/{target_year}, {len(budget_analysis)} categories"
        )
        
        return {
            'analysis_period': {
                'month': target_month,
                'year': target_year,
                'start_date': target_start,
                'end_date': target_end
            },
            'overall_summary': {
                'total_current_spending': total_current,
                'total_historical_average': total_historical,
                'total_variance_amount': total_current - total_historical,
                'total_variance_percent': Decimal(str(total_variance)),
                'categories_analyzed': len(budget_analysis)
            },
            'category_analysis': budget_analysis
        }
        
    except Exception as e:
        logger.error(f"Error generating budget analysis for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate budget analysis. Please try again."
        ) from e
