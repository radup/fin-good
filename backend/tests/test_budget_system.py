"""
Comprehensive tests for Budget Analysis System

This test suite covers all aspects of the budget management system including:
- Budget CRUD operations
- Variance analysis and reporting
- Forecasting integration
- Performance metrics
- API endpoints
- Data integrity and security
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.budget import (
    Budget, BudgetItem, BudgetActual, BudgetVarianceReport,
    BudgetType, BudgetStatus, VarianceType
)
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.budget import BudgetCreate, BudgetItemCreate, ForecastMethod
from app.services.budget_analyzer import BudgetAnalyzer


class TestBudgetModels:
    """Test budget model functionality and relationships."""
    
    def test_budget_creation(self, db_session: Session, test_user: User):
        """Test basic budget creation."""
        budget = Budget(
            user_id=test_user.id,
            name="Test Budget 2024",
            description="Monthly budget for testing",
            budget_type=BudgetType.MONTHLY,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            total_income_budget=5000.0,
            total_expense_budget=4000.0
        )
        
        db_session.add(budget)
        db_session.commit()
        db_session.refresh(budget)
        
        assert budget.id is not None
        assert budget.name == "Test Budget 2024"
        assert budget.status == BudgetStatus.DRAFT
        assert budget.user_id == test_user.id
    
    def test_budget_item_relationships(self, db_session: Session, test_budget: Budget):
        """Test budget item creation and relationships."""
        # Create income item
        income_item = BudgetItem(
            budget_id=test_budget.id,
            category="Income",
            subcategory="Salary",
            is_income=True,
            budgeted_amount=5000.0,
            use_historical_data=True,
            forecast_method="prophet"
        )
        
        # Create expense item
        expense_item = BudgetItem(
            budget_id=test_budget.id,
            category="Food",
            subcategory="Groceries",
            is_income=False,
            budgeted_amount=800.0,
            use_historical_data=True,
            forecast_method="prophet"
        )
        
        db_session.add_all([income_item, expense_item])
        db_session.commit()
        
        # Test relationships
        assert len(test_budget.budget_items) == 2
        assert income_item.budget == test_budget
        assert expense_item.budget == test_budget
        
        # Test categorization
        income_items = [item for item in test_budget.budget_items if item.is_income]
        expense_items = [item for item in test_budget.budget_items if not item.is_income]
        
        assert len(income_items) == 1
        assert len(expense_items) == 1
        assert income_items[0].category == "Income"
        assert expense_items[0].category == "Food"
    
    def test_budget_actual_variance_calculation(self, db_session: Session, test_budget: Budget):
        """Test budget actual records and variance calculations."""
        # Create budget item
        budget_item = BudgetItem(
            budget_id=test_budget.id,
            category="Food",
            is_income=False,
            budgeted_amount=800.0
        )
        db_session.add(budget_item)
        db_session.commit()
        
        # Create actual record
        actual = BudgetActual(
            budget_id=test_budget.id,
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
            category="Food",
            is_income=False,
            actual_amount=950.0,
            transaction_count=25,
            budgeted_amount=800.0,
            variance_amount=150.0,  # 950 - 800
            variance_percentage=18.75,  # (150/800) * 100
            variance_type=VarianceType.UNFAVORABLE
        )
        
        db_session.add(actual)
        db_session.commit()
        
        # Test calculations
        assert actual.variance_amount == 150.0
        assert actual.variance_percentage == 18.75
        assert actual.variance_type == VarianceType.UNFAVORABLE
        assert actual.budget == test_budget


class TestBudgetAnalyzer:
    """Test budget analyzer service functionality."""
    
    def test_budget_analyzer_initialization(self, db_session: Session):
        """Test budget analyzer initialization."""
        analyzer = BudgetAnalyzer(db_session)
        assert analyzer.db == db_session
        assert analyzer.forecasting_engine is not None
    
    def test_budget_summary_calculation(self, db_session: Session, test_user: User, test_budget: Budget):
        """Test budget summary calculation."""
        # Create budget items
        income_item = BudgetItem(
            budget_id=test_budget.id,
            category="Income",
            is_income=True,
            budgeted_amount=5000.0
        )
        expense_item = BudgetItem(
            budget_id=test_budget.id,
            category="Food",
            is_income=False,
            budgeted_amount=800.0
        )
        
        db_session.add_all([income_item, expense_item])
        db_session.commit()
        
        # Update budget totals
        test_budget.total_income_budget = 5000.0
        test_budget.total_expense_budget = 800.0
        test_budget.status = BudgetStatus.ACTIVE
        db_session.commit()
        
        # Test budget summary
        analyzer = BudgetAnalyzer(db_session)
        summary = analyzer.get_budget_summary(test_user.id)
        
        assert summary.total_budgets == 1
        assert summary.active_budgets == 1
        assert summary.total_budgeted_income == 5000.0
        assert summary.total_budgeted_expenses == 800.0
    
    def test_variance_analysis_with_transactions(
        self, 
        db_session: Session, 
        test_user: User, 
        test_budget: Budget
    ):
        """Test variance analysis with actual transaction data."""
        # Create budget item
        budget_item = BudgetItem(
            budget_id=test_budget.id,
            category="Food",
            subcategory="Groceries",
            is_income=False,
            budgeted_amount=800.0
        )
        db_session.add(budget_item)
        
        # Create test transactions
        transactions = [
            Transaction(
                user_id=test_user.id,
                date=datetime(2024, 1, 5),
                amount=-150.0,
                description="Grocery store",
                category="Food",
                subcategory="Groceries",
                is_income=False,
                source="csv"
            ),
            Transaction(
                user_id=test_user.id,
                date=datetime(2024, 1, 15),
                amount=-200.0,
                description="Supermarket",
                category="Food",
                subcategory="Groceries",
                is_income=False,
                source="csv"
            ),
            Transaction(
                user_id=test_user.id,
                date=datetime(2024, 1, 25),
                amount=-250.0,
                description="Organic market",
                category="Food",
                subcategory="Groceries",
                is_income=False,
                source="csv"
            )
        ]
        
        db_session.add_all(transactions)
        db_session.commit()
        
        # Perform variance analysis
        analyzer = BudgetAnalyzer(db_session)
        analysis = analyzer.analyze_budget_variance(
            budget_id=test_budget.id,
            user_id=test_user.id,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31)
        )
        
        # Verify analysis results
        assert analysis.budget_id == test_budget.id
        assert len(analysis.category_variances) >= 1
        
        # Find food category variance
        food_variance = next(
            (cv for cv in analysis.category_variances if cv.category == "Food"), 
            None
        )
        assert food_variance is not None
        assert food_variance.actual == 600.0  # 150 + 200 + 250
        assert food_variance.budgeted == 800.0
        assert food_variance.variance_amount == -200.0  # Under budget
        assert food_variance.variance_type == VarianceType.FAVORABLE
    
    def test_performance_metrics_calculation(self, db_session: Session, test_user: User, test_budget: Budget):
        """Test performance metrics calculation."""
        # Create budget items and variance reports
        test_budget.status = BudgetStatus.ACTIVE
        db_session.commit()
        
        # Create variance report
        variance_report = BudgetVarianceReport(
            budget_id=test_budget.id,
            report_date=datetime.utcnow(),
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
            total_income_budgeted=5000.0,
            total_income_actual=4800.0,
            total_expense_budgeted=4000.0,
            total_expense_actual=4200.0,
            net_variance_amount=-400.0,
            net_variance_percentage=-10.0,
            forecast_accuracy={"overall_accuracy": 0.8, "category_accuracies": [0.7, 0.8, 0.9]}
        )
        
        db_session.add(variance_report)
        db_session.commit()
        
        # Calculate performance metrics
        analyzer = BudgetAnalyzer(db_session)
        metrics = analyzer.calculate_performance_metrics(test_user.id)
        
        assert 0 <= metrics.accuracy_score <= 1
        assert 0 <= metrics.variance_stability <= 1
        assert 0 <= metrics.budget_adherence_rate <= 1
        assert isinstance(metrics.forecasting_improvement, float)
        assert 0 <= metrics.user_engagement_score <= 1


class TestBudgetAPI:
    """Test budget API endpoints."""
    
    def test_create_budget_endpoint(self, client: TestClient, auth_headers: dict):
        """Test budget creation via API."""
        budget_data = {
            "name": "API Test Budget",
            "description": "Budget created via API test",
            "budget_type": "monthly",
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-01-31T23:59:59",
            "warning_threshold": 0.85,
            "critical_threshold": 1.0,
            "budget_items": [
                {
                    "category": "Income",
                    "subcategory": "Salary",
                    "is_income": True,
                    "budgeted_amount": 5000.0,
                    "forecast_method": "prophet"
                },
                {
                    "category": "Food",
                    "subcategory": "Groceries",
                    "is_income": False,
                    "budgeted_amount": 800.0,
                    "forecast_method": "prophet"
                }
            ]
        }
        
        response = client.post(
            "/api/v1/budget/",
            json=budget_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "API Test Budget"
        assert data["budget_type"] == "monthly"
        assert data["status"] == "draft"
        assert len(data["budget_items"]) == 2
        assert data["total_income_budget"] == 5000.0
        assert data["total_expense_budget"] == 800.0
    
    def test_list_budgets_endpoint(self, client: TestClient, auth_headers: dict):
        """Test budget listing via API."""
        response = client.get(
            "/api/v1/budget/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_budget_analysis_endpoint(self, client: TestClient, auth_headers: dict, test_budget_id: int):
        """Test budget variance analysis via API."""
        response = client.post(
            f"/api/v1/budget/{test_budget_id}/analyze",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "budget_id" in data
        assert "category_variances" in data
        assert "recommendations" in data
        assert data["budget_id"] == test_budget_id
    
    def test_budget_summary_endpoint(self, client: TestClient, auth_headers: dict):
        """Test budget summary via API."""
        response = client.get(
            "/api/v1/budget/summary/overview",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_budgets" in data
        assert "total_budgeted_income" in data
        assert "total_budgeted_expenses" in data
        assert "overall_variance_percentage" in data
    
    def test_budget_forecast_endpoint(self, client: TestClient, auth_headers: dict, test_budget_id: int):
        """Test budget forecasting via API."""
        response = client.post(
            f"/api/v1/budget/{test_budget_id}/forecast?forecast_period=next_month",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "budget_id" in data
        assert "forecasted_income" in data
        assert "forecasted_expenses" in data
        assert "confidence_level" in data
        assert "recommendations" in data
        assert data["budget_id"] == test_budget_id
    
    def test_performance_metrics_endpoint(self, client: TestClient, auth_headers: dict):
        """Test performance metrics via API."""
        response = client.get(
            "/api/v1/budget/performance/metrics",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "accuracy_score" in data
        assert "variance_stability" in data
        assert "budget_adherence_rate" in data
        assert "user_engagement_score" in data
    
    def test_budget_activation_endpoint(self, client: TestClient, auth_headers: dict, test_budget_id: int):
        """Test budget activation via API."""
        response = client.post(
            f"/api/v1/budget/{test_budget_id}/activate",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "activated successfully" in data["message"]
    
    def test_budget_copy_endpoint(self, client: TestClient, auth_headers: dict, test_budget_id: int):
        """Test budget copying via API."""
        response = client.post(
            f"/api/v1/budget/{test_budget_id}/copy?new_name=Copied Budget&copy_items=true",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Copied Budget"
        assert data["status"] == "draft"
        assert "Copy of" in data["description"]
    
    def test_budget_access_control(self, client: TestClient, auth_headers: dict):
        """Test budget access control and security."""
        # Try to access non-existent budget
        response = client.get(
            "/api/v1/budget/99999",
            headers=auth_headers
        )
        assert response.status_code == 404
        
        # Try to access without authentication
        response = client.get("/api/v1/budget/")
        assert response.status_code in [401, 403]


class TestBudgetItemAPI:
    """Test budget item management API endpoints."""
    
    def test_add_budget_item(self, client: TestClient, auth_headers: dict, test_budget_id: int):
        """Test adding budget item via API."""
        item_data = {
            "category": "Transportation",
            "subcategory": "Gas",
            "is_income": False,
            "budgeted_amount": 300.0,
            "forecast_method": "prophet",
            "notes": "Monthly gas budget"
        }
        
        response = client.post(
            f"/api/v1/budget/{test_budget_id}/items",
            json=item_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "Transportation"
        assert data["budgeted_amount"] == 300.0
        assert data["budget_id"] == test_budget_id
    
    def test_update_budget_item(
        self, 
        client: TestClient, 
        auth_headers: dict, 
        test_budget_id: int,
        test_budget_item_id: int
    ):
        """Test updating budget item via API."""
        update_data = {
            "budgeted_amount": 350.0,
            "notes": "Updated gas budget for higher prices"
        }
        
        response = client.put(
            f"/api/v1/budget/{test_budget_id}/items/{test_budget_item_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["budgeted_amount"] == 350.0
        assert "Updated gas budget" in data["notes"]
    
    def test_delete_budget_item(
        self, 
        client: TestClient, 
        auth_headers: dict, 
        test_budget_id: int,
        test_budget_item_id: int
    ):
        """Test deleting budget item via API."""
        response = client.delete(
            f"/api/v1/budget/{test_budget_id}/items/{test_budget_item_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]


class TestBudgetValidation:
    """Test budget validation and error handling."""
    
    def test_invalid_budget_dates(self, client: TestClient, auth_headers: dict):
        """Test validation of invalid budget dates."""
        budget_data = {
            "name": "Invalid Date Budget",
            "budget_type": "monthly",
            "start_date": "2024-01-31T00:00:00",
            "end_date": "2024-01-01T00:00:00",  # End before start
            "budget_items": []
        }
        
        response = client.post(
            "/api/v1/budget/",
            json=budget_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_invalid_threshold_values(self, client: TestClient, auth_headers: dict):
        """Test validation of invalid threshold values."""
        budget_data = {
            "name": "Invalid Threshold Budget",
            "budget_type": "monthly",
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-01-31T00:00:00",
            "warning_threshold": 1.2,
            "critical_threshold": 0.8,  # Critical < Warning
            "budget_items": []
        }
        
        response = client.post(
            "/api/v1/budget/",
            json=budget_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_negative_budget_amounts(self, client: TestClient, auth_headers: dict):
        """Test validation of negative budget amounts."""
        budget_data = {
            "name": "Negative Amount Budget",
            "budget_type": "monthly",
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-01-31T00:00:00",
            "budget_items": [
                {
                    "category": "Invalid",
                    "is_income": False,
                    "budgeted_amount": -100.0,  # Negative amount
                    "forecast_method": "prophet"
                }
            ]
        }
        
        response = client.post(
            "/api/v1/budget/",
            json=budget_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error


# Test fixtures and utilities
@pytest.fixture
def test_budget(db_session: Session, test_user: User) -> Budget:
    """Create a test budget."""
    budget = Budget(
        user_id=test_user.id,
        name="Test Budget",
        description="Budget for testing",
        budget_type=BudgetType.MONTHLY,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31),
        total_income_budget=5000.0,
        total_expense_budget=4000.0
    )
    
    db_session.add(budget)
    db_session.commit()
    db_session.refresh(budget)
    return budget


@pytest.fixture
def test_budget_id(test_budget: Budget) -> int:
    """Get test budget ID."""
    return test_budget.id


@pytest.fixture
def test_budget_item(db_session: Session, test_budget: Budget) -> BudgetItem:
    """Create a test budget item."""
    item = BudgetItem(
        budget_id=test_budget.id,
        category="Food",
        subcategory="Groceries",
        is_income=False,
        budgeted_amount=800.0,
        use_historical_data=True,
        forecast_method="prophet"
    )
    
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


@pytest.fixture
def test_budget_item_id(test_budget_item: BudgetItem) -> int:
    """Get test budget item ID."""
    return test_budget_item.id


# Performance and Integration Tests
class TestBudgetPerformance:
    """Test budget system performance and scalability."""
    
    def test_large_budget_creation_performance(self, db_session: Session, test_user: User):
        """Test performance with large number of budget items."""
        budget = Budget(
            user_id=test_user.id,
            name="Large Budget Test",
            budget_type=BudgetType.ANNUAL,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31)
        )
        
        db_session.add(budget)
        db_session.flush()
        
        # Create 100 budget items
        import time
        start_time = time.time()
        
        items = []
        for i in range(100):
            item = BudgetItem(
                budget_id=budget.id,
                category=f"Category_{i % 10}",
                subcategory=f"Subcategory_{i}",
                is_income=i % 5 == 0,  # Every 5th item is income
                budgeted_amount=float(100 + i),
                use_historical_data=True,
                forecast_method="prophet"
            )
            items.append(item)
        
        db_session.add_all(items)
        db_session.commit()
        
        creation_time = time.time() - start_time
        assert creation_time < 5.0  # Should complete within 5 seconds
        assert len(budget.budget_items) == 100
    
    def test_variance_analysis_performance(self, db_session: Session, test_user: User, test_budget: Budget):
        """Test variance analysis performance with large datasets."""
        # Create many budget items
        for i in range(50):
            item = BudgetItem(
                budget_id=test_budget.id,
                category=f"Category_{i}",
                is_income=i % 5 == 0,
                budgeted_amount=float(100 + i)
            )
            db_session.add(item)
        
        # Create many transactions
        for i in range(1000):
            transaction = Transaction(
                user_id=test_user.id,
                date=datetime(2024, 1, 1) + timedelta(days=i % 30),
                amount=float(-50 - (i % 100)),
                description=f"Transaction {i}",
                category=f"Category_{i % 50}",
                is_income=i % 5 == 0,
                source="test"
            )
            db_session.add(transaction)
        
        db_session.commit()
        
        # Test variance analysis performance
        import time
        start_time = time.time()
        
        analyzer = BudgetAnalyzer(db_session)
        analysis = analyzer.analyze_budget_variance(
            budget_id=test_budget.id,
            user_id=test_user.id
        )
        
        analysis_time = time.time() - start_time
        assert analysis_time < 10.0  # Should complete within 10 seconds
        assert analysis.budget_id == test_budget.id
        assert len(analysis.category_variances) > 0


if __name__ == "__main__":
    # Run tests with: python -m pytest tests/test_budget_system.py -v
    pytest.main([__file__, "-v"])