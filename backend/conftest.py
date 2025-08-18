"""
Global pytest configuration and fixtures for FinGood backend testing.
Provides comprehensive test setup for database, authentication, and API testing.
"""

import pytest
import asyncio
import os
import secrets
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

import httpx
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Import application components
from app.core.database import Base, get_db
from app.core.config import Settings
from app.models.user import User
from app.models.transaction import Transaction
from main import app


# ================================
# TEST CONFIGURATION
# ================================

@pytest.fixture(scope="session")
def test_settings():
    """Create test-specific settings with secure configuration."""
    test_secret_key = secrets.token_urlsafe(32)
    test_csrf_key = secrets.token_urlsafe(32)
    
    with patch.dict(os.environ, {
        'SECRET_KEY': test_secret_key,
        'CSRF_SECRET_KEY': test_csrf_key,
        'DATABASE_URL': 'postgresql://testuser:testpass123456@localhost:5432/testdb',
        'REDIS_URL': 'redis://testuser:testpass123456@localhost:6379/1',
        'DEBUG': 'True'
    }):
        test_settings_instance = Settings()
        
        # Patch the global settings for security module
        import app.core.config
        with patch.object(app.core.config, 'settings', test_settings_instance):
            return test_settings_instance


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ================================
# DATABASE FIXTURES
# ================================

@pytest.fixture(scope="session")
def test_engine(test_settings):
    """Create test database engine with in-memory SQLite."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
        echo=False  # Set to True for SQL debugging
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db_session(test_engine):
    """Create a fresh database session for each test."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )
    
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def test_client(test_db_session, test_settings):
    """Create FastAPI test client with test database."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_test_client(test_db_session, test_settings):
    """Create async test client for async endpoint testing."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


# ================================
# USER AND AUTH FIXTURES
# ================================

@pytest.fixture
def test_user_data():
    """Standard test user data."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User",
        "company_name": "Test Company",
        "business_type": "Technology"
    }


@pytest.fixture
def test_user_admin_data():
    """Admin test user data."""
    return {
        "email": "admin@example.com",
        "password": "AdminPassword123!",
        "full_name": "Admin User",
        "company_name": "Admin Company",
        "business_type": "Administration",
        "is_admin": True
    }


@pytest.fixture
def test_user(test_db_session, test_user_data):
    """Create a test user in the database."""
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_password = pwd_context.hash(test_user_data["password"])
    
    user = User(
        email=test_user_data["email"],
        hashed_password=hashed_password,
        full_name=test_user_data["full_name"],
        company_name=test_user_data["company_name"],
        business_type=test_user_data["business_type"],
        is_active=True
    )
    
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    
    return user


@pytest.fixture
def test_admin_user(test_db_session, test_user_admin_data):
    """Create a test admin user in the database."""
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_password = pwd_context.hash(test_user_admin_data["password"])
    
    user = User(
        email=test_user_admin_data["email"],
        hashed_password=hashed_password,
        full_name=test_user_admin_data["full_name"],
        company_name=test_user_admin_data["company_name"],
        business_type=test_user_admin_data["business_type"],
        is_active=True,
        is_admin=True
    )
    
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    
    return user


@pytest.fixture
def test_access_token(test_user, test_settings):
    """Create a valid access token for testing."""
    from app.core.security import create_access_token
    return create_access_token({"sub": test_user.email})


@pytest.fixture
def test_admin_token(test_admin_user, test_settings):
    """Create a valid admin access token for testing."""
    from app.core.security import create_access_token
    return create_access_token({"sub": test_admin_user.email})


@pytest.fixture
def auth_headers(test_access_token):
    """Create authorization headers for API requests."""
    return {"Authorization": f"Bearer {test_access_token}"}


@pytest.fixture
def admin_headers(test_admin_token):
    """Create admin authorization headers for API requests."""
    return {"Authorization": f"Bearer {test_admin_token}"}


# ================================
# TRANSACTION DATA FIXTURES
# ================================

@pytest.fixture
def sample_transaction_data():
    """Standard transaction data for testing."""
    return {
        "date": "2024-01-15",
        "description": "Test Transaction",
        "amount": -50.00,
        "category": "Food & Dining",
        "account": "Checking"
    }


@pytest.fixture
def sample_transactions_batch():
    """Batch of sample transactions for testing."""
    return [
        {
            "date": "2024-01-15",
            "description": "Grocery Store",
            "amount": -85.50,
            "category": "Food & Dining",
            "account": "Checking"
        },
        {
            "date": "2024-01-14",
            "description": "Salary Deposit",
            "amount": 3500.00,
            "category": "Income",
            "account": "Checking"
        },
        {
            "date": "2024-01-13",
            "description": "Gas Station",
            "amount": -45.20,
            "category": "Transportation",
            "account": "Credit Card"
        },
        {
            "date": "2024-01-12",
            "description": "Coffee Shop",
            "amount": -4.75,
            "category": "Food & Dining",
            "account": "Debit Card"
        }
    ]


@pytest.fixture
def test_transaction(test_db_session, test_user, sample_transaction_data):
    """Create a test transaction in the database."""
    from datetime import datetime
    
    transaction = Transaction(
        user_id=test_user.id,
        date=datetime.strptime(sample_transaction_data["date"], "%Y-%m-%d").date(),
        description=sample_transaction_data["description"],
        amount=sample_transaction_data["amount"],
        category=sample_transaction_data["category"],
        account=sample_transaction_data["account"]
    )
    
    test_db_session.add(transaction)
    test_db_session.commit()
    test_db_session.refresh(transaction)
    
    return transaction


# ================================
# MOCK FIXTURES
# ================================

@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    mock_redis = MagicMock()
    with patch('app.core.database.redis_client', mock_redis):
        yield mock_redis


@pytest.fixture
def mock_ollama():
    """Mock Ollama AI service for testing."""
    mock_ollama = MagicMock()
    mock_ollama.generate.return_value = {
        'response': 'Food & Dining',
        'confidence': 0.95
    }
    
    with patch('app.services.categorization.ollama_client', mock_ollama):
        yield mock_ollama


@pytest.fixture
def mock_file_upload():
    """Mock file upload for testing."""
    from io import BytesIO
    
    csv_content = """Date,Description,Amount,Account
2024-01-15,Test Transaction,-50.00,Checking
2024-01-14,Another Transaction,100.00,Savings
"""
    
    return BytesIO(csv_content.encode())


# ================================
# ERROR TESTING FIXTURES
# ================================

@pytest.fixture
def database_error_mock():
    """Mock database errors for testing error handling."""
    from sqlalchemy.exc import SQLAlchemyError
    
    def raise_db_error(*args, **kwargs):
        raise SQLAlchemyError("Database connection failed")
    
    return raise_db_error


@pytest.fixture
def network_error_mock():
    """Mock network errors for testing external service failures."""
    import requests
    
    def raise_network_error(*args, **kwargs):
        raise requests.exceptions.ConnectionError("Network connection failed")
    
    return raise_network_error


@pytest.fixture
def expired_token():
    """Create an expired token for testing token validation."""
    from app.core.security import jwt_manager
    
    # Create token that expired 1 hour ago
    return jwt_manager.create_access_token(
        {"sub": "test@example.com"}, 
        expires_delta=timedelta(seconds=-1)
    )


@pytest.fixture
def invalid_token():
    """Create an invalid token for testing."""
    return "invalid.jwt.token"


# ================================
# PERFORMANCE TESTING FIXTURES
# ================================

@pytest.fixture
def performance_test_data():
    """Large dataset for performance testing."""
    return [
        {
            "date": f"2024-01-{i:02d}",
            "description": f"Transaction {i}",
            "amount": float(i * 10.50),
            "category": "Test Category",
            "account": "Test Account"
        }
        for i in range(1, 1001)  # 1000 transactions
    ]


# ================================
# SECURITY TESTING FIXTURES
# ================================

@pytest.fixture
def malicious_payloads():
    """Common malicious payloads for security testing."""
    return {
        "sql_injection": [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users --"
        ],
        "xss": [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//"
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ]
    }


# ================================
# TEST UTILITIES
# ================================

@pytest.fixture
def assert_error_response():
    """Utility function to assert error responses."""
    def _assert_error_response(response, status_code, error_message=None):
        assert response.status_code == status_code
        response_data = response.json()
        assert "detail" in response_data
        if error_message:
            assert error_message in response_data["detail"]
    
    return _assert_error_response


@pytest.fixture
def assert_success_response():
    """Utility function to assert successful responses."""
    def _assert_success_response(response, expected_keys=None):
        assert response.status_code in [200, 201, 202]
        response_data = response.json()
        if expected_keys:
            for key in expected_keys:
                assert key in response_data
    
    return _assert_success_response


# ================================
# CLEANUP FIXTURES
# ================================

@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Automatically clean up test files after each test."""
    yield
    
    # Clean up any test files created during testing
    import glob
    test_files = glob.glob("test_*")
    for file in test_files:
        try:
            os.remove(file)
        except FileNotFoundError:
            pass


# ================================
# PYTEST HOOKS
# ================================

def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Set test environment variable
    os.environ["TESTING"] = "true"
    
    # Configure logging for tests
    import logging
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def pytest_unconfigure(config):
    """Clean up after all tests complete."""
    # Remove test environment variable
    if "TESTING" in os.environ:
        del os.environ["TESTING"]


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(test_db_session):
    """Automatically provide database access to all tests."""
    pass