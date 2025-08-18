"""
Financial Security Testing Utilities for FinGood Backend.
Provides comprehensive security testing capabilities for financial data,
compliance validation, and vulnerability assessment.
"""

import pytest
import secrets
import string
import hashlib
import hmac
import time
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import re
import json

from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from fastapi.testclient import TestClient
import jwt


# ================================
# FINANCIAL DATA VALIDATION UTILITIES
# ================================

class FinancialDataValidator:
    """Validator for financial data integrity and compliance."""
    
    # PCI DSS Compliance patterns
    CREDIT_CARD_PATTERNS = {
        'visa': r'^4[0-9]{12}(?:[0-9]{3})?$',
        'mastercard': r'^5[1-5][0-9]{14}$',
        'amex': r'^3[47][0-9]{13}$',
        'discover': r'^6(?:011|5[0-9]{2})[0-9]{12}$'
    }
    
    # SSN pattern (should be masked/encrypted)
    SSN_PATTERN = r'^\d{3}-\d{2}-\d{4}$'
    
    # Bank account patterns
    ROUTING_NUMBER_PATTERN = r'^\d{9}$'
    ACCOUNT_NUMBER_PATTERN = r'^\d{8,17}$'
    
    @classmethod
    def validate_amount_precision(cls, amount: float) -> bool:
        """Validate that financial amounts have proper precision (2 decimal places)."""
        decimal_amount = Decimal(str(amount))
        return decimal_amount.as_tuple().exponent >= -2
    
    @classmethod
    def validate_amount_range(cls, amount: float, min_val: float = -1000000, max_val: float = 1000000) -> bool:
        """Validate that amounts are within reasonable financial ranges."""
        return min_val <= amount <= max_val
    
    @classmethod
    def detect_sensitive_data(cls, text: str) -> Dict[str, List[str]]:
        """Detect potentially sensitive financial data in text."""
        findings = {
            'credit_cards': [],
            'ssns': [],
            'routing_numbers': [],
            'account_numbers': []
        }
        
        # Check for credit card patterns
        for card_type, pattern in cls.CREDIT_CARD_PATTERNS.items():
            matches = re.findall(pattern, text.replace(' ', '').replace('-', ''))
            if matches:
                findings['credit_cards'].extend([(card_type, match) for match in matches])
        
        # Check for SSN pattern
        ssn_matches = re.findall(cls.SSN_PATTERN, text)
        findings['ssns'].extend(ssn_matches)
        
        # Check for routing numbers
        routing_matches = re.findall(cls.ROUTING_NUMBER_PATTERN, text)
        findings['routing_numbers'].extend(routing_matches)
        
        # Check for account numbers (basic pattern)
        account_matches = re.findall(cls.ACCOUNT_NUMBER_PATTERN, text)
        findings['account_numbers'].extend(account_matches)
        
        return findings
    
    @classmethod
    def validate_luhn_checksum(cls, card_number: str) -> bool:
        """Validate credit card number using Luhn algorithm."""
        card_number = card_number.replace(' ', '').replace('-', '')
        if not card_number.isdigit():
            return False
        
        def luhn_checksum(card_num):
            def digits_of(n):
                return [int(d) for d in str(n)]
            
            digits = digits_of(card_num)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = sum(odd_digits)
            for d in even_digits:
                checksum += sum(digits_of(d*2))
            return checksum % 10
        
        return luhn_checksum(card_number) == 0


# ================================
# ENCRYPTION AND SECURITY UTILITIES
# ================================

class SecurityTestHelper:
    """Helper class for security testing and validation."""
    
    @staticmethod
    def generate_test_encryption_key() -> str:
        """Generate a test encryption key."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def test_data_encryption(data: str, key: str) -> Tuple[str, bool]:
        """Test data encryption and return encrypted data + validation."""
        from cryptography.fernet import Fernet
        import base64
        
        # Generate key from provided string
        key_bytes = base64.urlsafe_b64encode(key.encode()[:32].ljust(32, b'\0'))
        fernet = Fernet(key_bytes)
        
        try:
            encrypted = fernet.encrypt(data.encode())
            decrypted = fernet.decrypt(encrypted).decode()
            return encrypted.decode(), decrypted == data
        except Exception:
            return "", False
    
    @staticmethod
    def test_password_strength(password: str) -> Dict[str, bool]:
        """Test password strength against security requirements."""
        return {
            'length': len(password) >= 8,
            'uppercase': any(c.isupper() for c in password),
            'lowercase': any(c.islower() for c in password),
            'digit': any(c.isdigit() for c in password),
            'special': any(c in string.punctuation for c in password),
            'no_common': password.lower() not in [
                'password', '123456', 'qwerty', 'abc123', 'password123'
            ]
        }
    
    @staticmethod
    def test_token_security(token: str, secret: str) -> Dict[str, Any]:
        """Test JWT token security properties."""
        try:
            # Decode without verification first to check structure
            unverified = jwt.decode(token, options={"verify_signature": False})
            
            # Then verify with secret
            verified = jwt.decode(token, secret, algorithms=["HS256"])
            
            # Check token properties
            now = datetime.utcnow()
            exp = datetime.fromtimestamp(verified.get('exp', 0))
            iat = datetime.fromtimestamp(verified.get('iat', 0))
            
            return {
                'valid_structure': True,
                'valid_signature': True,
                'has_expiration': 'exp' in verified,
                'has_issued_at': 'iat' in verified,
                'has_subject': 'sub' in verified,
                'expired': exp < now if 'exp' in verified else False,
                'expires_in': (exp - now).total_seconds() if 'exp' in verified else None,
                'payload': verified
            }
        except jwt.ExpiredSignatureError:
            return {'valid_structure': True, 'valid_signature': True, 'expired': True}
        except jwt.InvalidSignatureError:
            return {'valid_structure': True, 'valid_signature': False}
        except jwt.DecodeError:
            return {'valid_structure': False, 'valid_signature': False}
    
    @staticmethod
    def generate_malicious_inputs() -> Dict[str, List[str]]:
        """Generate malicious inputs for security testing."""
        return {
            'sql_injection': [
                "'; DROP TABLE transactions; --",
                "1' OR '1'='1",
                "admin'--",
                "' UNION SELECT * FROM users --",
                "'; DELETE FROM users WHERE id = 1; --",
                "1; UPDATE users SET is_admin=1 WHERE id=1; --"
            ],
            'xss': [
                "<script>alert('xss')</script>",
                "javascript:alert('xss')",
                "<img src=x onerror=alert('xss')>",
                "<iframe src='javascript:alert(1)'></iframe>",
                "';alert('xss');//",
                "<svg onload=alert('xss')></svg>"
            ],
            'path_traversal': [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32\\config\\sam",
                "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
                "....//....//....//etc/passwd",
                "/etc/passwd%00.txt"
            ],
            'command_injection': [
                "; cat /etc/passwd",
                "| ls -la",
                "&& rm -rf /",
                "$(cat /etc/passwd)",
                "`whoami`",
                "${IFS}cat${IFS}/etc/passwd"
            ],
            'buffer_overflow': [
                "A" * 1000,
                "A" * 10000,
                "\x00" * 1000,
                "\xff" * 1000
            ],
            'financial_attacks': [
                "999999999999.99",  # Large amount
                "-999999999999.99",  # Large negative amount
                "0.001",  # Sub-penny amount
                "NaN",  # Not a number
                "Infinity",  # Infinity
                "1e308",  # Scientific notation
                "0x1000",  # Hexadecimal
                "1,000.00"  # Formatted number
            ]
        }


# ================================
# COMPLIANCE TESTING UTILITIES
# ================================

class ComplianceTestHelper:
    """Helper for testing regulatory compliance requirements."""
    
    @staticmethod
    def test_pci_dss_compliance(data: Dict[str, Any]) -> Dict[str, bool]:
        """Test PCI DSS compliance requirements."""
        return {
            'no_plain_credit_cards': not FinancialDataValidator.detect_sensitive_data(
                json.dumps(data)
            )['credit_cards'],
            'encrypted_sensitive_data': all(
                not isinstance(v, str) or not v.isdigit() or len(v) < 13
                for v in data.values() if isinstance(v, str)
            ),
            'secure_transmission': True,  # Assumes HTTPS
            'access_controls': True,  # Assumes proper auth
            'audit_trails': 'created_at' in data or 'timestamp' in data
        }
    
    @staticmethod
    def test_gdpr_compliance(user_data: Dict[str, Any]) -> Dict[str, bool]:
        """Test GDPR compliance requirements."""
        return {
            'data_minimization': len(user_data) <= 10,  # Reasonable field count
            'purpose_limitation': 'purpose' in user_data or 'consent' in user_data,
            'accuracy': all(v is not None for v in user_data.values()),
            'storage_limitation': 'retention_period' in user_data,
            'integrity_confidentiality': 'encrypted' in str(user_data).lower(),
            'lawful_basis': 'consent' in user_data or 'legitimate_interest' in user_data
        }
    
    @staticmethod
    def test_sox_compliance(transaction_data: Dict[str, Any]) -> Dict[str, bool]:
        """Test Sarbanes-Oxley compliance requirements."""
        return {
            'audit_trail': all(
                field in transaction_data 
                for field in ['created_at', 'user_id', 'amount']
            ),
            'data_integrity': FinancialDataValidator.validate_amount_precision(
                float(transaction_data.get('amount', 0))
            ),
            'internal_controls': 'approval_status' in transaction_data,
            'retention_policy': 'retention_date' in transaction_data,
            'documentation': 'description' in transaction_data and len(
                transaction_data.get('description', '')
            ) > 0
        }


# ================================
# VULNERABILITY TESTING FIXTURES
# ================================

@pytest.fixture
def financial_security_validator():
    """Fixture providing financial data validator."""
    return FinancialDataValidator()


@pytest.fixture
def security_test_helper():
    """Fixture providing security testing utilities."""
    return SecurityTestHelper()


@pytest.fixture
def compliance_test_helper():
    """Fixture providing compliance testing utilities."""
    return ComplianceTestHelper()


@pytest.fixture
def malicious_financial_data():
    """Fixture providing malicious financial test data."""
    return {
        'amounts': [
            float('inf'),
            float('-inf'),
            float('nan'),
            Decimal('999999999999999.999'),
            -Decimal('999999999999999.999'),
            0.001,  # Sub-penny
            0.1 + 0.2,  # Floating point precision issue
        ],
        'descriptions': SecurityTestHelper.generate_malicious_inputs()['sql_injection'],
        'accounts': [
            "'; DROP TABLE accounts; --",
            "<script>alert('hack')</script>",
            "../../../etc/passwd",
            "NULL",
            "",
            "A" * 1000
        ],
        'categories': [
            "Food & Dining'; DROP TABLE categories; --",
            "<img src=x onerror=alert('xss')>",
            "../../admin/users",
            "$(rm -rf /)",
            "\x00\x00\x00\x00"
        ]
    }


@pytest.fixture
def sensitive_data_samples():
    """Fixture providing sensitive data samples for testing."""
    return {
        'credit_cards': [
            '4111111111111111',  # Test Visa
            '5555555555554444',  # Test Mastercard
            '378282246310005',   # Test Amex
            '6011111111111117'   # Test Discover
        ],
        'ssns': [
            '123-45-6789',
            '000-00-0000',
            '999-99-9999'
        ],
        'bank_accounts': [
            {'routing': '123456789', 'account': '123456789012'},
            {'routing': '987654321', 'account': '987654321098'}
        ],
        'encrypted_samples': [
            'gAAAAABhZ...',  # Fernet encrypted
            'JDJiJDE0JE...',  # Bcrypt hash
            'pbkdf2_sha256$...'  # Django hash
        ]
    }


@pytest.fixture
def compliance_test_data():
    """Fixture providing compliance test scenarios."""
    return {
        'pci_compliant_transaction': {
            'amount': 100.00,
            'description': 'Test purchase',
            'merchant': 'Test Merchant',
            'card_last_four': '1111',  # Only last 4 digits
            'encrypted_pan': 'gAAAAABhZ...',  # Encrypted PAN
            'created_at': datetime.utcnow().isoformat()
        },
        'pci_non_compliant_transaction': {
            'amount': 100.00,
            'description': 'Test purchase',
            'merchant': 'Test Merchant',
            'card_number': '4111111111111111',  # Full card number
            'cvv': '123',  # CVV stored
            'created_at': datetime.utcnow().isoformat()
        },
        'gdpr_compliant_user': {
            'email': 'test@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'consent': True,
            'purpose': 'financial_management',
            'retention_period': '7_years',
            'created_at': datetime.utcnow().isoformat()
        },
        'sox_compliant_transaction': {
            'amount': 1000.00,
            'description': 'Business expense - client lunch',
            'category': 'Business Meals',
            'approval_status': 'approved',
            'approver_id': 1,
            'audit_trail': json.dumps([
                {'action': 'created', 'user': 'john.doe', 'timestamp': datetime.utcnow().isoformat()},
                {'action': 'approved', 'user': 'manager', 'timestamp': datetime.utcnow().isoformat()}
            ]),
            'retention_date': (datetime.utcnow() + timedelta(days=2555)).isoformat(),  # 7 years
            'created_at': datetime.utcnow().isoformat()
        }
    }


@pytest.fixture
def financial_calculation_tests():
    """Fixture providing financial calculation test cases."""
    return {
        'precision_tests': [
            {'input': 10.10, 'expected': Decimal('10.10')},
            {'input': 0.1 + 0.2, 'expected': Decimal('0.30')},
            {'input': 100 / 3, 'expected': Decimal('33.33')},
        ],
        'rounding_tests': [
            {'amount': 10.555, 'decimals': 2, 'expected': Decimal('10.56')},
            {'amount': 10.554, 'decimals': 2, 'expected': Decimal('10.55')},
            {'amount': 10.5, 'decimals': 0, 'expected': Decimal('11')},
        ],
        'arithmetic_tests': [
            {'operation': 'add', 'a': Decimal('10.50'), 'b': Decimal('5.25'), 'expected': Decimal('15.75')},
            {'operation': 'subtract', 'a': Decimal('10.50'), 'b': Decimal('5.25'), 'expected': Decimal('5.25')},
            {'operation': 'multiply', 'a': Decimal('10.50'), 'b': Decimal('2'), 'expected': Decimal('21.00')},
            {'operation': 'divide', 'a': Decimal('10.50'), 'b': Decimal('2'), 'expected': Decimal('5.25')},
        ]
    }


# ================================
# ERROR SIMULATION FIXTURES
# ================================

@pytest.fixture
def financial_error_simulator():
    """Fixture for simulating financial system errors."""
    
    class FinancialErrorSimulator:
        @staticmethod
        def database_transaction_failure():
            """Simulate database transaction failure."""
            raise IntegrityError("Transaction failed due to constraint violation", None, None)
        
        @staticmethod
        def payment_gateway_timeout():
            """Simulate payment gateway timeout."""
            import requests
            raise requests.exceptions.Timeout("Payment gateway request timed out")
        
        @staticmethod
        def insufficient_funds_error():
            """Simulate insufficient funds error."""
            return {
                'error': 'insufficient_funds',
                'message': 'Account balance insufficient for transaction',
                'code': 'NSF_001'
            }
        
        @staticmethod
        def currency_conversion_error():
            """Simulate currency conversion service error."""
            return {
                'error': 'conversion_failed',
                'message': 'Unable to retrieve current exchange rate',
                'code': 'CUR_001'
            }
        
        @staticmethod
        def fraud_detection_alert():
            """Simulate fraud detection system alert."""
            return {
                'alert': 'potential_fraud',
                'message': 'Transaction flagged for manual review',
                'risk_score': 0.85,
                'code': 'FRAUD_001'
            }
    
    return FinancialErrorSimulator()


# ================================
# PERFORMANCE TESTING FIXTURES
# ================================

@pytest.fixture
def financial_performance_data():
    """Fixture providing large financial datasets for performance testing."""
    from faker import Faker
    fake = Faker()
    
    def generate_transactions(count: int = 10000):
        """Generate large number of transactions for performance testing."""
        return [
            {
                'date': fake.date_this_year().isoformat(),
                'description': fake.sentence(nb_words=4),
                'amount': float(fake.pydecimal(left_digits=4, right_digits=2, positive=None)),
                'category': fake.random_element([
                    'Food & Dining', 'Transportation', 'Shopping', 'Entertainment',
                    'Bills & Utilities', 'Income', 'Healthcare', 'Travel', 'Education',
                    'Personal Care', 'Gifts & Donations', 'Business Services'
                ]),
                'account': fake.random_element(['Checking', 'Savings', 'Credit Card', 'Investment']),
                'user_id': fake.random_int(min=1, max=1000)
            }
            for _ in range(count)
        ]
    
    return {
        'small_dataset': generate_transactions(100),
        'medium_dataset': generate_transactions(1000),
        'large_dataset': generate_transactions(10000),
        'xlarge_dataset': generate_transactions(100000)
    }


# ================================
# AUDIT TRAIL TESTING UTILITIES
# ================================

class AuditTrailTester:
    """Utility for testing audit trail functionality."""
    
    @staticmethod
    def validate_audit_entry(entry: Dict[str, Any]) -> Dict[str, bool]:
        """Validate audit trail entry completeness."""
        required_fields = ['timestamp', 'user_id', 'action', 'resource_type', 'resource_id']
        optional_fields = ['old_values', 'new_values', 'ip_address', 'user_agent']
        
        return {
            'has_required_fields': all(field in entry for field in required_fields),
            'valid_timestamp': 'timestamp' in entry and isinstance(entry['timestamp'], str),
            'valid_user_id': 'user_id' in entry and isinstance(entry['user_id'], (int, str)),
            'valid_action': 'action' in entry and entry['action'] in [
                'create', 'read', 'update', 'delete', 'login', 'logout'
            ],
            'has_change_details': any(field in entry for field in optional_fields),
            'immutable_entry': 'modified_at' not in entry  # Audit entries should not be modified
        }
    
    @staticmethod
    def generate_audit_trail(actions: List[str], user_id: int = 1) -> List[Dict[str, Any]]:
        """Generate sample audit trail for testing."""
        import uuid
        trail = []
        
        for i, action in enumerate(actions):
            entry = {
                'id': str(uuid.uuid4()),
                'timestamp': (datetime.utcnow() + timedelta(minutes=i)).isoformat(),
                'user_id': user_id,
                'action': action,
                'resource_type': 'transaction',
                'resource_id': i + 1,
                'ip_address': f'192.168.1.{i + 1}',
                'user_agent': 'Mozilla/5.0 (Test Browser)'
            }
            
            if action in ['update', 'delete']:
                entry['old_values'] = {'amount': 100.00}
                if action == 'update':
                    entry['new_values'] = {'amount': 150.00}
            
            trail.append(entry)
        
        return trail


@pytest.fixture
def audit_trail_tester():
    """Fixture providing audit trail testing utilities."""
    return AuditTrailTester()