"""
Test utilities and helper functions for FinGood backend testing.
Provides common functionality for API testing, data generation, and assertions.
"""

import json
import secrets
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
import tempfile
import os

import pytest
from faker import Faker
from factory import Factory, Sequence, LazyAttribute, SubFactory
from factory.alchemy import SQLAlchemyModelFactory
import httpx
from fastapi.testclient import TestClient

# Initialize Faker for test data generation
fake = Faker()


# ================================
# DATA FACTORIES
# ================================

class UserFactory(SQLAlchemyModelFactory):
    """Factory for generating test user data."""
    
    class Meta:
        model = None  # Will be set when importing models
        sqlalchemy_session_persistence = "commit"
    
    email = Sequence(lambda n: f"user{n}@example.com")
    first_name = LazyAttribute(lambda obj: fake.first_name())
    last_name = LazyAttribute(lambda obj: fake.last_name())
    is_active = True
    is_admin = False
    created_at = LazyAttribute(lambda obj: fake.date_time_this_year())


class TransactionFactory(SQLAlchemyModelFactory):
    """Factory for generating test transaction data."""
    
    class Meta:
        model = None  # Will be set when importing models
        sqlalchemy_session_persistence = "commit"
    
    date = LazyAttribute(lambda obj: fake.date_this_year())
    description = LazyAttribute(lambda obj: fake.sentence(nb_words=4))
    amount = LazyAttribute(lambda obj: Decimal(str(fake.pydecimal(left_digits=4, right_digits=2))))
    category = LazyAttribute(lambda obj: fake.random_element([
        "Food & Dining", "Transportation", "Shopping", "Entertainment",
        "Bills & Utilities", "Income", "Healthcare", "Travel"
    ]))
    account = LazyAttribute(lambda obj: fake.random_element([
        "Checking", "Savings", "Credit Card", "Debit Card"
    ]))
    created_at = LazyAttribute(lambda obj: fake.date_time_this_year())


# ================================
# API TEST HELPERS
# ================================

class APITestHelper:
    """Helper class for API testing with common patterns."""
    
    def __init__(self, client: TestClient):
        self.client = client
    
    def login_user(self, email: str, password: str) -> Dict[str, str]:
        """Login a user and return authorization headers."""
        response = self.client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a user via API and return user data."""
        response = self.client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        return response.json()
    
    def get_with_auth(self, url: str, headers: Dict[str, str]) -> httpx.Response:
        """Make authenticated GET request."""
        return self.client.get(url, headers=headers)
    
    def post_with_auth(self, url: str, data: Dict[str, Any], headers: Dict[str, str]) -> httpx.Response:
        """Make authenticated POST request."""
        return self.client.post(url, json=data, headers=headers)
    
    def put_with_auth(self, url: str, data: Dict[str, Any], headers: Dict[str, str]) -> httpx.Response:
        """Make authenticated PUT request."""
        return self.client.put(url, json=data, headers=headers)
    
    def delete_with_auth(self, url: str, headers: Dict[str, str]) -> httpx.Response:
        """Make authenticated DELETE request."""
        return self.client.delete(url, headers=headers)


# ================================
# ASSERTION HELPERS
# ================================

def assert_api_error(response: httpx.Response, status_code: int, error_message: str = None):
    """Assert API error response format and content."""
    assert response.status_code == status_code
    error_data = response.json()
    assert "detail" in error_data
    if error_message:
        assert error_message.lower() in error_data["detail"].lower()


def assert_api_success(response: httpx.Response, expected_keys: List[str] = None):
    """Assert API success response format."""
    assert response.status_code in [200, 201, 202]
    data = response.json()
    if expected_keys:
        for key in expected_keys:
            assert key in data


def assert_transaction_data(transaction: Dict[str, Any], expected: Dict[str, Any]):
    """Assert transaction data matches expected format."""
    required_fields = ["id", "date", "description", "amount", "category", "account"]
    
    for field in required_fields:
        assert field in transaction
    
    if expected:
        for key, value in expected.items():
            if key == "amount":
                assert abs(float(transaction[key]) - float(value)) < 0.01
            elif key == "date":
                assert transaction[key] == str(value)
            else:
                assert transaction[key] == value


def assert_user_data(user: Dict[str, Any], expected: Dict[str, Any] = None):
    """Assert user data matches expected format."""
    required_fields = ["id", "email", "first_name", "last_name", "is_active"]
    
    for field in required_fields:
        assert field in user
    
    # Security check - password should never be returned
    assert "password" not in user
    assert "hashed_password" not in user
    
    if expected:
        for key, value in expected.items():
            if key not in ["password", "hashed_password"]:
                assert user[key] == value


# ================================
# ERROR SIMULATION HELPERS
# ================================

class ErrorSimulator:
    """Helper class for simulating various error conditions."""
    
    @staticmethod
    def database_connection_error():
        """Simulate database connection failure."""
        from sqlalchemy.exc import OperationalError
        raise OperationalError("Database connection failed", None, None)
    
    @staticmethod
    def database_integrity_error():
        """Simulate database integrity constraint violation."""
        from sqlalchemy.exc import IntegrityError
        raise IntegrityError("Constraint violation", None, None)
    
    @staticmethod
    def network_timeout_error():
        """Simulate network timeout."""
        import requests
        raise requests.exceptions.Timeout("Network request timed out")
    
    @staticmethod
    def external_service_error():
        """Simulate external service unavailability."""
        import requests
        raise requests.exceptions.ConnectionError("External service unavailable")
    
    @staticmethod
    def file_system_error():
        """Simulate file system error."""
        raise OSError("File system error")


# ================================
# SECURITY TEST HELPERS
# ================================

class SecurityTestHelper:
    """Helper class for security testing."""
    
    MALICIOUS_PAYLOADS = {
        "sql_injection": [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users --",
            "'; DELETE FROM transactions; --"
        ],
        "xss": [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//",
            "<iframe src='javascript:alert(1)'></iframe>"
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "....//....//....//etc/passwd"
        ],
        "command_injection": [
            "; cat /etc/passwd",
            "| ls -la",
            "&& rm -rf /",
            "$(cat /etc/passwd)"
        ]
    }
    
    @classmethod
    def get_malicious_payloads(cls, payload_type: str) -> List[str]:
        """Get list of malicious payloads for testing."""
        return cls.MALICIOUS_PAYLOADS.get(payload_type, [])
    
    @staticmethod
    def generate_weak_passwords() -> List[str]:
        """Generate list of weak passwords for testing."""
        return [
            "password",
            "123456",
            "qwerty",
            "abc123",
            "password123",
            "admin",
            "letmein",
            "welcome",
            "monkey",
            "dragon"
        ]
    
    @staticmethod
    def generate_strong_password() -> str:
        """Generate a strong password for testing."""
        return secrets.token_urlsafe(16) + "!A1"
    
    @staticmethod
    def create_expired_token() -> str:
        """Create an expired JWT token for testing."""
        import jwt
        from datetime import datetime, timedelta
        
        payload = {
            "sub": "test@example.com",
            "exp": datetime.utcnow() - timedelta(hours=1)
        }
        return jwt.encode(payload, "test-secret", algorithm="HS256")
    
    @staticmethod
    def create_malformed_token() -> str:
        """Create a malformed JWT token for testing."""
        return "invalid.jwt.token.format"


# ================================
# PERFORMANCE TEST HELPERS
# ================================

class PerformanceTestHelper:
    """Helper class for performance testing."""
    
    @staticmethod
    def generate_large_dataset(size: int = 1000) -> List[Dict[str, Any]]:
        """Generate large dataset for performance testing."""
        return [
            {
                "date": fake.date_this_year().isoformat(),
                "description": fake.sentence(nb_words=4),
                "amount": float(fake.pydecimal(left_digits=4, right_digits=2)),
                "category": fake.random_element([
                    "Food & Dining", "Transportation", "Shopping"
                ]),
                "account": fake.random_element(["Checking", "Savings"])
            }
            for _ in range(size)
        ]
    
    @staticmethod
    def time_api_call(client: TestClient, method: str, url: str, **kwargs):
        """Time an API call and return duration."""
        import time
        
        start_time = time.time()
        
        if method.upper() == "GET":
            response = client.get(url, **kwargs)
        elif method.upper() == "POST":
            response = client.post(url, **kwargs)
        elif method.upper() == "PUT":
            response = client.put(url, **kwargs)
        elif method.upper() == "DELETE":
            response = client.delete(url, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        duration = time.time() - start_time
        
        return response, duration


# ================================
# FILE TEST HELPERS
# ================================

class FileTestHelper:
    """Helper class for file upload testing."""
    
    @staticmethod
    def create_test_csv(content: List[Dict[str, Any]]) -> tempfile.NamedTemporaryFile:
        """Create a temporary CSV file for testing."""
        import csv
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        
        if content:
            fieldnames = content[0].keys()
            writer = csv.DictWriter(temp_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(content)
        
        temp_file.flush()
        return temp_file
    
    @staticmethod
    def create_malicious_file(file_type: str = "csv") -> tempfile.NamedTemporaryFile:
        """Create a malicious file for security testing."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix=f'.{file_type}', delete=False)
        
        if file_type == "csv":
            # CSV with potential injection
            temp_file.write("Date,Description,Amount\n")
            temp_file.write("2024-01-01,=cmd|'/c calc'!A0,100\n")
        
        temp_file.flush()
        return temp_file
    
    @staticmethod
    def cleanup_temp_file(file_path: str):
        """Clean up temporary test file."""
        try:
            os.unlink(file_path)
        except FileNotFoundError:
            pass


# ================================
# DATABASE TEST HELPERS
# ================================

class DatabaseTestHelper:
    """Helper class for database testing."""
    
    @staticmethod
    def count_records(session, model_class):
        """Count records in a table."""
        return session.query(model_class).count()
    
    @staticmethod
    def clear_table(session, model_class):
        """Clear all records from a table."""
        session.query(model_class).delete()
        session.commit()
    
    @staticmethod
    def create_test_data(session, model_class, count: int = 10):
        """Create test data using appropriate factory."""
        if model_class.__name__ == "User":
            return [UserFactory.create() for _ in range(count)]
        elif model_class.__name__ == "Transaction":
            return [TransactionFactory.create() for _ in range(count)]
        else:
            raise ValueError(f"No factory defined for {model_class.__name__}")


# ================================
# MOCK HELPERS
# ================================

class MockHelper:
    """Helper class for creating mocks."""
    
    @staticmethod
    def mock_redis_client():
        """Create a mock Redis client."""
        from unittest.mock import MagicMock
        
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        mock_redis.delete.return_value = 1
        mock_redis.exists.return_value = False
        
        return mock_redis
    
    @staticmethod
    def mock_ollama_client():
        """Create a mock Ollama AI client."""
        from unittest.mock import MagicMock
        
        mock_ollama = MagicMock()
        mock_ollama.generate.return_value = {
            'response': 'Food & Dining',
            'confidence': 0.95
        }
        
        return mock_ollama
    
    @staticmethod
    def mock_email_service():
        """Create a mock email service."""
        from unittest.mock import MagicMock
        
        mock_email = MagicMock()
        mock_email.send_email.return_value = True
        
        return mock_email


# ================================
# CONFIGURATION HELPERS
# ================================

def get_test_config():
    """Get test-specific configuration."""
    return {
        "SECRET_KEY": secrets.token_urlsafe(32),
        "DATABASE_URL": "sqlite:///./test.db",
        "REDIS_URL": "redis://localhost:6379/1",
        "DEBUG": True,
        "TESTING": True
    }