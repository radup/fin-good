"""
Comprehensive tests for Enhanced Categorization API

This test suite covers all the new categorization endpoints including:
- Bulk categorization
- Confidence scoring
- User feedback tracking
- Category suggestions
- Auto-improvement
- Performance metrics
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.models.transaction import Transaction, CategorizationRule
from app.services.categorization import CategorizationService
from app.services.ml_categorization import MLCategorizationService, MLCategoryPrediction
from tests.conftest import create_test_user, create_test_transaction, get_test_db

client = TestClient(app)

class TestBulkCategorization:
    """Test bulk categorization functionality"""
    
    def test_bulk_categorize_transactions_success(self, test_db: Session, test_user: User):
        """Test successful bulk categorization of transactions"""
        # Create test transactions
        transactions = []
        for i in range(5):
            transaction = create_test_transaction(
                test_db, test_user.id,
                description=f"Test transaction {i}",
                amount=100.0 + i,
                is_categorized=False
            )
            transactions.append(transaction)
        
        transaction_ids = [t.id for t in transactions]
        
        with patch.object(CategorizationService, 'categorize_transactions_by_ids') as mock_categorize:
            mock_categorize.return_value = {
                'total_transactions': 5,
                'rule_categorized': 3,
                'ml_categorized': 2,
                'failed_categorizations': 0,
                'success_rate': 1.0,
                'processing_time': 1.5
            }
            
            response = client.post(
                "/api/v1/transactions/categorize/bulk",
                params={"transaction_ids": transaction_ids, "use_ml_fallback": True},
                headers={"Cookie": f"fingood_auth=test_token_{test_user.id}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_transactions"] == 5
            assert data["rule_categorized"] == 3
            assert data["ml_categorized"] == 2
            assert data["success_rate"] == 1.0
            assert "processing_time" in data
    
    def test_bulk_categorize_empty_transaction_list(self, test_db: Session, test_user: User):
        """Test bulk categorization with empty transaction list"""
        response = client.post(
            "/api/v1/transactions/categorize/bulk",
            params={"transaction_ids": []},
            headers={"Cookie": f"fingood_auth=test_token_{test_user.id}"}
        )
        
        assert response.status_code == 400
        assert "At least one transaction ID must be provided" in response.json()["detail"]
    
    def test_bulk_categorize_too_many_transactions(self, test_db: Session, test_user: User):
        """Test bulk categorization with too many transactions"""
        transaction_ids = list(range(1001))  # More than 1000
        
        response = client.post(
            "/api/v1/transactions/categorize/bulk",
            params={"transaction_ids": transaction_ids},
            headers={"Cookie": f"fingood_auth=test_token_{test_user.id}"}
        )
        
        assert response.status_code == 400
        assert "Maximum 1000 transactions" in response.json()["detail"]
    
    def test_bulk_categorize_invalid_transaction_ids(self, test_db: Session, test_user: User):
        """Test bulk categorization with invalid transaction IDs"""
        # Create one valid transaction
        transaction = create_test_transaction(test_db, test_user.id)
        
        # Use mix of valid and invalid IDs
        transaction_ids = [transaction.id, 99999, 99998]
        
        response = client.post(
            "/api/v1/transactions/categorize/bulk",
            params={"transaction_ids": transaction_ids},
            headers={"Cookie": f"fingood_auth=test_token_{test_user.id}"}
        )
        
        assert response.status_code == 400
        assert "Some transaction IDs are invalid" in response.json()["detail"]

class TestCategorizationConfidence:
    """Test categorization confidence scoring"""
    
    def test_get_categorization_confidence_success(self, test_db: Session, test_user: User):
        """Test successful confidence score retrieval"""
        # Create a categorized transaction
        transaction = create_test_transaction(
            test_db, test_user.id,
            category="Food & Dining",
            subcategory="Restaurants",
            confidence_score=0.85,
            is_categorized=True,
            meta_data={
                'categorization_method': 'ml',
                'ml_reasoning': 'Based on description pattern matching',
                'rule_id': 123
            }
        )
        
        with patch.object(CategorizationService, 'get_categorization_confidence') as mock_confidence:
            mock_confidence.return_value = {
                'confidence_breakdown': {
                    'ml_confidence': 0.85,
                    'ml_reasoning': 'Based on description pattern matching'
                },
                'alternatives': [
                    {'category': 'Food & Dining', 'subcategory': 'Fast Food', 'confidence': 0.75},
                    {'category': 'Food & Dining', 'subcategory': 'Groceries', 'confidence': 0.65}
                ],
                'rule_applied': None
            }
            
            response = client.get(
                f"/api/v1/transactions/categorize/confidence/{transaction.id}",
                headers={"Cookie": f"fingood_auth=test_token_{test_user.id}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["transaction_id"] == transaction.id
            assert data["current_category"] == "Food & Dining"
            assert data["confidence_score"] == 0.85
            assert data["categorization_method"] == "ml"
            assert "confidence_breakdown" in data
            assert "alternative_categories" in data
    
    def test_get_categorization_confidence_transaction_not_found(self, test_db: Session, test_user: User):
        """Test confidence score for non-existent transaction"""
        response = client.get(
            "/api/v1/transactions/categorize/confidence/99999",
            headers={"Cookie": f"fingood_auth=test_token_{test_user.id}"}
        )
        
        assert response.status_code == 404
        assert "Transaction not found" in response.json()["detail"]

class TestCategorizationFeedback:
    """Test categorization feedback functionality"""
    
    def test_submit_categorization_feedback_correct(self, test_db: Session, test_user: User):
        """Test submitting correct feedback"""
        transaction = create_test_transaction(test_db, test_user.id)
        
        with patch.object(CategorizationService, 'submit_categorization_feedback') as mock_feedback:
            mock_feedback.return_value = {
                'feedback_id': 'test-feedback-id',
                'impact': 'marked_verified',
                'ml_learning': False
            }
            
            response = client.post(
                "/api/v1/transactions/categorize/feedback",
                params={
                    "transaction_id": transaction.id,
                    "feedback_type": "correct",
                    "feedback_comment": "This categorization is accurate"
                },
                headers={"Cookie": f"fingood_auth=test_token_{test_user.id}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["feedback_id"] == "test-feedback-id"
            assert data["feedback_type"] == "correct"
            assert data["impact"] == "marked_verified"
    
    def test_submit_categorization_feedback_suggest_alternative(self, test_db: Session, test_user: User):
        """Test submitting feedback with alternative suggestion"""
        transaction = create_test_transaction(test_db, test_user.id)
        
        with patch.object(CategorizationService, 'submit_categorization_feedback') as mock_feedback:
            mock_feedback.return_value = {
                'feedback_id': 'test-feedback-id',
                'impact': 'category_applied_and_rule_created',
                'ml_learning': True
            }
            
            response = client.post(
                "/api/v1/transactions/categorize/feedback",
                params={
                    "transaction_id": transaction.id,
                    "feedback_type": "suggest_alternative",
                    "suggested_category": "Transportation",
                    "suggested_subcategory": "Public Transit",
                    "feedback_comment": "This should be transportation"
                },
                headers={"Cookie": f"fingood_auth=test_token_{test_user.id}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["feedback_type"] == "suggest_alternative"
            assert data["impact"] == "category_applied_and_rule_created"
            assert data["ml_learning"] == True
    
    def test_submit_categorization_feedback_invalid_type(self, test_db: Session, test_user: User):
        """Test submitting feedback with invalid feedback type"""
        transaction = create_test_transaction(test_db, test_user.id)
        
        response = client.post(
            "/api/v1/transactions/categorize/feedback",
            params={
                "transaction_id": transaction.id,
                "feedback_type": "invalid_type"
            },
            headers={"Cookie": f"fingood_auth=test_token_{test_user.id}"}
        )
        
        assert response.status_code == 400
        assert "Invalid feedback_type" in response.json()["detail"]
    
    def test_submit_categorization_feedback_missing_category(self, test_db: Session, test_user: User):
        """Test submitting suggest_alternative feedback without suggested category"""
        transaction = create_test_transaction(test_db, test_user.id)
        
        response = client.post(
            "/api/v1/transactions/categorize/feedback",
            params={
                "transaction_id": transaction.id,
                "feedback_type": "suggest_alternative"
            },
            headers={"Cookie": f"fingood_auth=test_token_{test_user.id}"}
        )
        
        assert response.status_code == 400
        assert "suggested_category is required" in response.json()["detail"]

class TestCategorySuggestions:
    """Test category suggestion functionality"""
    
    def test_get_category_suggestions_success(self, test_db: Session, test_user: User):
        """Test successful category suggestions retrieval"""
        transaction = create_test_transaction(
            test_db, test_user.id,
            description="Starbucks coffee purchase",
            amount=5.50
        )
        
        with patch.object(CategorizationService, 'get_category_suggestions') as mock_suggestions:
            mock_suggestions.return_value = {
                'suggestions': [
                    {
                        'category': 'Food & Dining',
                        'subcategory': 'Coffee Shops',
                        'confidence': 0.95,
                        'method': 'rule',
                        'rule_id': 1,
                        'rule_name': 'Coffee shop rule'
                    },
                    {
                        'category': 'Food & Dining',
                        'subcategory': 'Restaurants',
                        'confidence': 0.75,
                        'method': 'ml',
                        'reasoning': 'Based on vendor name pattern'
                    }
                ],
                'rule_matches': [
                    {
                        'category': 'Food & Dining',
                        'subcategory': 'Coffee Shops',
                        'confidence': 0.95,
                        'method': 'rule',
                        'rule_id': 1,
                        'rule_name': 'Coffee shop rule',
                        'pattern': 'starbucks'
                    }
                ],
                'ml_predictions': [
                    {
                        'category': 'Food & Dining',
                        'subcategory': 'Restaurants',
                        'confidence': 0.75,
                        'method': 'ml',
                        'reasoning': 'Based on vendor name pattern'
                    }
                ],
                'confidence_threshold': 0.6,
                'total_suggestions': 2
            }
            
            response = client.get(
                f"/api/v1/transactions/categorize/suggestions/{transaction.id}",
                params={"include_ml": True, "include_rules": True},
                headers={"Cookie": f"fingood_auth=test_token_{test_user.id}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["transaction_id"] == transaction.id
            assert data["description"] == "Starbucks coffee purchase"
            assert len(data["suggestions"]) == 2
            assert data["suggestions"][0]["confidence"] == 0.95
            assert data["confidence_threshold"] == 0.6
    
    def test_get_category_suggestions_transaction_not_found(self, test_db: Session, test_user: User):
        """Test category suggestions for non-existent transaction"""
        response = client.get(
            "/api/v1/transactions/categorize/suggestions/99999",
            headers={"Cookie": f"fingood_auth=test_token_{test_user.id}"}
        )
        
        assert response.status_code == 404
        assert "Transaction not found" in response.json()["detail"]

class TestAutoImprovement:
    """Test categorization auto-improvement functionality"""
    
    def test_auto_improve_categorization_success(self, test_db: Session, test_user: User):
        """Test successful auto-improvement of categorization"""
        with patch.object(CategorizationService, 'auto_improve_categorization') as mock_improve:
            mock_improve.return_value = {
                'rules_created': 3,
                'rules_updated': 2,
                'ml_improvements': 1,
                'transactions_reprocessed': 15,
                'improvement_score': 0.75,
                'processing_time': 2.5
            }
            
            response = client.post(
                "/api/v1/transactions/categorize/auto-improve",
                params={
                    "batch_id": "test-batch-123",
                    "min_confidence_threshold": 0.6
                },
                headers={"Cookie": f"fingood_auth=test_token_{test_user.id}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["rules_created"] == 3
            assert data["rules_updated"] == 2
            assert data["transactions_reprocessed"] == 15
            assert data["improvement_score"] == 0.75
            assert "processing_time" in data
    
    def test_auto_improve_categorization_invalid_threshold(self, test_db: Session, test_user: User):
        """Test auto-improvement with invalid confidence threshold"""
        response = client.post(
            "/api/v1/transactions/categorize/auto-improve",
            params={"min_confidence_threshold": 1.5},  # Invalid: > 1.0
            headers={"Cookie": f"fingood_auth=test_token_{test_user.id}"}
        )
        
        assert response.status_code == 422  # Validation error

class TestPerformanceMetrics:
    """Test categorization performance metrics"""
    
    def test_get_categorization_performance_success(self, test_db: Session, test_user: User):
        """Test successful performance metrics retrieval"""
        # Create test transactions with various categorization states
        create_test_transaction(test_db, test_user.id, category="Food", is_categorized=True, confidence_score=0.9)
        create_test_transaction(test_db, test_user.id, category="Transport", is_categorized=True, confidence_score=0.7)
        create_test_transaction(test_db, test_user.id, is_categorized=False)
        
        with patch.object(CategorizationService, 'get_categorization_performance') as mock_performance:
            mock_performance.return_value = {
                'overall': {
                    'total_transactions': 3,
                    'categorized_count': 2,
                    'uncategorized_count': 1,
                    'categorization_rate': 0.67,
                    'average_confidence': 0.8
                },
                'methods': {
                    'rule_based': 1,
                    'ml_based': 1,
                    'user_corrected': 0,
                    'unknown': 0
                },
                'confidence_distribution': {
                    'high': 1,
                    'medium': 1,
                    'low': 0
                },
                'categories': {
                    'Food': {
                        'count': 1,
                        'total_amount': 100.0,
                        'average_confidence': 0.9
                    },
                    'Transport': {
                        'count': 1,
                        'total_amount': 50.0,
                        'average_confidence': 0.7
                    }
                },
                'trends': {},
                'feedback': {
                    'total_feedback': 5,
                    'correct_feedback': 3,
                    'incorrect_feedback': 1,
                    'suggestions_feedback': 1
                }
            }
            
            response = client.get(
                "/api/v1/transactions/categorize/performance",
                params={
                    "start_date": "2024-01-01T00:00:00",
                    "end_date": "2024-12-31T23:59:59"
                },
                headers={"Cookie": f"fingood_auth=test_token_{test_user.id}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == test_user.id
            assert data["overall_metrics"]["total_transactions"] == 3
            assert data["overall_metrics"]["categorization_rate"] == 0.67
            assert data["method_breakdown"]["rule_based"] == 1
            assert data["method_breakdown"]["ml_based"] == 1
            assert data["confidence_distribution"]["high"] == 1
            assert data["confidence_distribution"]["medium"] == 1
            assert "Food" in data["category_performance"]
            assert "Transport" in data["category_performance"]
            assert data["feedback_analysis"]["total_feedback"] == 5

class TestIntegrationScenarios:
    """Test integration scenarios for enhanced categorization"""
    
    def test_full_categorization_workflow(self, test_db: Session, test_user: User):
        """Test complete categorization workflow"""
        # 1. Create uncategorized transactions
        transactions = []
        for i in range(3):
            transaction = create_test_transaction(
                test_db, test_user.id,
                description=f"Test transaction {i}",
                is_categorized=False
            )
            transactions.append(transaction)
        
        transaction_ids = [t.id for t in transactions]
        
        # 2. Bulk categorize
        with patch.object(CategorizationService, 'categorize_transactions_by_ids') as mock_bulk:
            mock_bulk.return_value = {
                'total_transactions': 3,
                'rule_categorized': 2,
                'ml_categorized': 1,
                'failed_categorizations': 0,
                'success_rate': 1.0,
                'processing_time': 1.0
            }
            
            response = client.post(
                "/api/v1/transactions/categorize/bulk",
                params={"transaction_ids": transaction_ids},
                headers={"Cookie": f"fingood_auth=test_token_{test_user.id}"}
            )
            
            assert response.status_code == 200
        
        # 3. Get confidence for one transaction
        transaction = transactions[0]
        with patch.object(CategorizationService, 'get_categorization_confidence') as mock_confidence:
            mock_confidence.return_value = {
                'confidence_breakdown': {'ml_confidence': 0.85},
                'alternatives': [],
                'rule_applied': None
            }
            
            response = client.get(
                f"/api/v1/transactions/categorize/confidence/{transaction.id}",
                headers={"Cookie": f"fingood_auth=test_token_{test_user.id}"}
            )
            
            assert response.status_code == 200
        
        # 4. Submit feedback
        with patch.object(CategorizationService, 'submit_categorization_feedback') as mock_feedback:
            mock_feedback.return_value = {
                'feedback_id': 'test-id',
                'impact': 'marked_verified',
                'ml_learning': False
            }
            
            response = client.post(
                "/api/v1/transactions/categorize/feedback",
                params={
                    "transaction_id": transaction.id,
                    "feedback_type": "correct"
                },
                headers={"Cookie": f"fingood_auth=test_token_{test_user.id}"}
            )
            
            assert response.status_code == 200
        
        # 5. Get performance metrics
        with patch.object(CategorizationService, 'get_categorization_performance') as mock_performance:
            mock_performance.return_value = {
                'overall': {'total_transactions': 3, 'categorized_count': 3, 'categorization_rate': 1.0},
                'methods': {'rule_based': 2, 'ml_based': 1},
                'confidence_distribution': {'high': 2, 'medium': 1, 'low': 0},
                'categories': {},
                'trends': {},
                'feedback': {'total_feedback': 1, 'correct_feedback': 1}
            }
            
            response = client.get(
                "/api/v1/transactions/categorize/performance",
                headers={"Cookie": f"fingood_auth=test_token_{test_user.id}"}
            )
            
            assert response.status_code == 200

class TestErrorHandling:
    """Test error handling for enhanced categorization endpoints"""
    
    def test_database_connection_error(self, test_db: Session, test_user: User):
        """Test handling of database connection errors"""
        with patch.object(CategorizationService, 'categorize_transactions_by_ids') as mock_categorize:
            mock_categorize.side_effect = Exception("Database connection failed")
            
            response = client.post(
                "/api/v1/transactions/categorize/bulk",
                params={"transaction_ids": [1, 2, 3]},
                headers={"Cookie": f"fingood_auth=test_token_{test_user.id}"}
            )
            
            assert response.status_code == 500
    
    def test_ml_service_unavailable(self, test_db: Session, test_user: User):
        """Test handling of ML service unavailability"""
        transaction = create_test_transaction(test_db, test_user.id)
        
        with patch.object(CategorizationService, 'get_category_suggestions') as mock_suggestions:
            mock_suggestions.side_effect = Exception("ML service unavailable")
            
            response = client.get(
                f"/api/v1/transactions/categorize/suggestions/{transaction.id}",
                headers={"Cookie": f"fingood_auth=test_token_{test_user.id}"}
            )
            
            assert response.status_code == 500
    
    def test_invalid_user_access(self, test_db: Session, test_user: User):
        """Test handling of invalid user access"""
        # Create transaction for different user
        other_user = create_test_user(test_db, email="other@example.com")
        transaction = create_test_transaction(test_db, other_user.id)
        
        # Try to access with different user
        response = client.get(
            f"/api/v1/transactions/categorize/confidence/{transaction.id}",
            headers={"Cookie": f"fingood_auth=test_token_{test_user.id}"}
        )
        
        assert response.status_code == 404
        assert "Transaction not found" in response.json()["detail"]

if __name__ == "__main__":
    pytest.main([__file__])
