"""
Security Utilities for Input Sanitization and SQL Injection Prevention

Comprehensive security tools for protecting financial applications from
common attack vectors including SQL injection, XSS, CSRF, and data exfiltration.
"""

import re
import html
import logging
import hashlib
import secrets
from typing import Any, Dict, List, Optional, Union, Pattern
from urllib.parse import quote, unquote
from datetime import datetime, timedelta
try:
    import bleach
    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False
    bleach = None
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import ValidationException
from app.schemas.error import FieldError

logger = logging.getLogger(__name__)


class SQLInjectionPrevention:
    """Advanced SQL injection detection and prevention utilities"""
    
    def __init__(self):
        # Comprehensive SQL injection patterns
        self.injection_patterns = [
            # Classic SQL injection patterns
            r"('|(\\'))+.*(\\')?(;|--|\s)",  # Quote-based injection
            r"(;|\s)(union|select|insert|update|delete|drop|create|alter|exec|execute)\s+",  # SQL keywords
            r"(;|\s)(or|and)\s+\d+\s*[=<>!]+\s*\d+",  # Boolean-based injection
            r"(;|\s)(or|and)\s+['\"][^'\"]*['\"][\s]*[=<>!]+[\s]*['\"][^'\"]*['\"]",  # String boolean injection
            
            # Time-based blind injection
            r"(;|\s)(waitfor|delay|sleep|benchmark)\s*[\(]",  # Time functions
            r"(;|\s)pg_sleep\s*\(",  # PostgreSQL sleep
            r"(;|\s)dbms_pipe\.receive_message\s*\(",  # Oracle delay
            
            # File operations and data exfiltration
            r"(;|\s)(load_file|into\s+outfile|dumpfile|load\s+data)\s+",  # MySQL file ops
            r"(;|\s)(copy|\\copy)\s+.*\s+(from|to)\s+",  # PostgreSQL copy
            r"(;|\s)xp_cmdshell\s*\(",  # SQL Server command execution
            
            # Information gathering
            r"(;|\s)(information_schema|sys\.|pg_|mysql\.)",  # Schema enumeration
            r"(;|\s)(version|user|database|schema)\s*\(\s*\)",  # System functions
            r"(;|\s)(@@version|@@servername|@@user)",  # SQL Server globals
            
            # Advanced techniques
            r"(;|\s)cast\s*\([^)]*as\s+",  # Type casting for error-based injection
            r"(;|\s)convert\s*\(",  # Type conversion
            r"(;|\s)(extractvalue|updatexml)\s*\(",  # XML functions for error-based
            r"(;|\s)group_concat\s*\(",  # MySQL concatenation
            r"(;|\s)string_agg\s*\(",  # PostgreSQL concatenation
            
            # SQL comments and obfuscation
            r"\/\*.*?\*\/",  # Block comments
            r"--[^\r\n]*",  # Line comments
            r"#[^\r\n]*",  # MySQL comments
            r"\bor\s+\w+\s*=\s*\w+\s*--",  # Comment-based bypass
            
            # Encoded injection attempts
            r"%27|%22|%2D%2D|%3B|%7C",  # URL encoded characters
            r"\\x27|\\x22|\\x2D|\\x3B",  # Hex encoded characters
            
            # Stacked queries
            r";[\s]*\w+[\s]*[=]",  # Assignment after semicolon
            r";[\s]*(declare|set)\s+",  # Variable declarations
            
            # NoSQL injection patterns
            r"\$where|\$regex|\$ne|\$gt|\$lt|\$in|\$nin",  # MongoDB operators
            r"this\.|Object\.|eval\(",  # JavaScript injection in NoSQL
        ]
        
        # Pre-compile patterns for performance
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE | re.MULTILINE | re.DOTALL) 
            for pattern in self.injection_patterns
        ]
        
        # Dangerous SQL keywords that should never appear in user input
        self.dangerous_keywords = {
            'select', 'insert', 'update', 'delete', 'drop', 'create', 'alter',
            'exec', 'execute', 'union', 'declare', 'cast', 'convert', 'xp_',
            'sp_', 'load_file', 'into outfile', 'dumpfile', 'information_schema',
            'pg_', 'mysql.', 'sys.', 'waitfor', 'delay', 'sleep', 'benchmark'
        }
    
    def is_sql_injection_attempt(self, value: str, strict_mode: bool = True) -> bool:
        """
        Detect potential SQL injection attempts in user input
        
        Args:
            value: Input string to analyze
            strict_mode: If True, uses more aggressive detection
        
        Returns:
            True if potential SQL injection detected
        """
        
        if not isinstance(value, str) or len(value) < 2:
            return False
        
        # Normalize input for analysis
        normalized = value.lower().strip()
        
        # Check against compiled patterns
        for pattern in self.compiled_patterns:
            if pattern.search(normalized):
                logger.warning(
                    f"SQL injection pattern detected: {pattern.pattern}",
                    extra={"input_value": value[:100], "pattern_matched": True}
                )
                return True
        
        # Keyword-based detection
        if strict_mode:
            for keyword in self.dangerous_keywords:
                if keyword in normalized:
                    # Additional context check to reduce false positives
                    if self._has_sql_context(normalized, keyword):
                        logger.warning(
                            f"Dangerous SQL keyword detected: {keyword}",
                            extra={"input_value": value[:100], "keyword": keyword}
                        )
                        return True
        
        return False
    
    def _has_sql_context(self, text: str, keyword: str) -> bool:
        """Check if keyword appears in SQL context (reduces false positives)"""
        
        # Look for SQL-like syntax around the keyword
        keyword_index = text.find(keyword)
        if keyword_index == -1:
            return False
        
        # Check surrounding context
        start = max(0, keyword_index - 10)
        end = min(len(text), keyword_index + len(keyword) + 10)
        context = text[start:end]
        
        # Look for SQL operators and syntax
        sql_indicators = [
            r'\s+(from|where|and|or|join|on|set|values)\s+',
            r'[=<>!]+',
            r'[\(\),;]',
            r'\s+(table|column|database|schema)\s+'
        ]
        
        for indicator in sql_indicators:
            if re.search(indicator, context, re.IGNORECASE):
                return True
        
        return False
    
    def sanitize_sql_parameter(self, value: str, max_length: int = 1000) -> str:
        """
        Sanitize a parameter that will be used in SQL queries
        
        Args:
            value: Input value to sanitize
            max_length: Maximum allowed length
        
        Returns:
            Sanitized string safe for SQL use
        """
        
        if not isinstance(value, str):
            value = str(value)
        
        # Length validation
        if len(value) > max_length:
            raise ValidationException(
                message="Input too long",
                field_errors=[FieldError(
                    field="parameter",
                    message=f"Input cannot exceed {max_length} characters",
                    code="INPUT_TOO_LONG",
                    value=len(value)
                )]
            )
        
        # Remove null bytes and control characters
        value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
        
        # SQL injection check
        if self.is_sql_injection_attempt(value):
            raise ValidationException(
                message="Potentially dangerous input detected",
                field_errors=[FieldError(
                    field="parameter",
                    message="Input contains patterns that could be dangerous",
                    code="SECURITY_VIOLATION",
                    value="[REDACTED]"
                )]
            )
        
        return value
    
    def validate_sql_identifier(self, identifier: str) -> str:
        """
        Validate and sanitize SQL identifiers (table names, column names)
        
        Args:
            identifier: SQL identifier to validate
        
        Returns:
            Sanitized identifier safe for SQL use
        """
        
        if not identifier:
            raise ValueError("SQL identifier cannot be empty")
        
        # Remove spaces and convert to lowercase for consistency
        clean_identifier = identifier.strip().lower()
        
        # Must start with letter or underscore
        if not re.match(r'^[a-z_][a-z0-9_]*$', clean_identifier):
            raise ValueError("SQL identifier must start with letter or underscore and contain only letters, numbers, and underscores")
        
        # Length limits (PostgreSQL standard)
        if len(clean_identifier) > 63:
            raise ValueError("SQL identifier cannot exceed 63 characters")
        
        # Reserved word check (basic set)
        reserved_words = {
            'select', 'from', 'where', 'insert', 'update', 'delete', 'create',
            'drop', 'alter', 'table', 'index', 'view', 'database', 'schema',
            'user', 'order', 'group', 'having', 'union', 'join', 'inner',
            'outer', 'left', 'right', 'on', 'as', 'and', 'or', 'not', 'null',
            'true', 'false', 'default', 'primary', 'foreign', 'key', 'unique',
            'constraint', 'check', 'references'
        }
        
        if clean_identifier in reserved_words:
            raise ValueError(f"'{clean_identifier}' is a reserved SQL keyword")
        
        return clean_identifier


class XSSPrevention:
    """Cross-Site Scripting (XSS) prevention utilities"""
    
    def __init__(self):
        # Configure bleach for HTML sanitization
        self.allowed_tags = []  # No HTML tags allowed in financial data
        self.allowed_attributes = {}
        self.allowed_protocols = ['http', 'https', 'mailto']
        
        # XSS patterns
        self.xss_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',  # Javascript protocol
            r'on\w+\s*=',  # Event handlers
            r'<iframe[^>]*>.*?</iframe>',  # Iframes
            r'<object[^>]*>.*?</object>',  # Objects
            r'<embed[^>]*>.*?</embed>',  # Embeds
            r'<link[^>]*>',  # Link tags
            r'<meta[^>]*>',  # Meta tags
            r'expression\s*\(',  # CSS expressions
            r'url\s*\(\s*[\'"]?javascript:',  # CSS javascript URLs
        ]
        
        self.compiled_xss_patterns = [
            re.compile(pattern, re.IGNORECASE | re.DOTALL) 
            for pattern in self.xss_patterns
        ]
    
    def is_xss_attempt(self, value: str) -> bool:
        """Detect potential XSS attempts"""
        
        if not isinstance(value, str):
            return False
        
        # Check for XSS patterns
        for pattern in self.compiled_xss_patterns:
            if pattern.search(value):
                return True
        
        return False
    
    def sanitize_html_input(self, value: str, allow_basic_formatting: bool = False) -> str:
        """
        Sanitize HTML input to prevent XSS attacks
        
        Args:
            value: Input string to sanitize
            allow_basic_formatting: Whether to allow basic HTML formatting
        
        Returns:
            Sanitized string safe for display
        """
        
        if not isinstance(value, str):
            value = str(value)
        
        # HTML entity decode first
        value = html.unescape(value)
        
        # Configure allowed tags for basic formatting if requested
        allowed_tags = ['b', 'i', 'u', 'strong', 'em'] if allow_basic_formatting else []
        allowed_attributes = {'*': ['title']} if allow_basic_formatting else {}
        
        # Clean HTML using bleach if available, otherwise use html.escape
        if BLEACH_AVAILABLE and bleach:
            cleaned = bleach.clean(
                value,
                tags=allowed_tags,
                attributes=allowed_attributes,
                protocols=self.allowed_protocols,
                strip=True
            )
        else:
            # Fallback to basic HTML escaping if bleach is not available
            cleaned = html.escape(value, quote=True)
        
        # Additional XSS check
        if self.is_xss_attempt(cleaned):
            raise ValidationException(
                message="Potentially dangerous HTML content detected",
                field_errors=[FieldError(
                    field="content",
                    message="Input contains patterns that could be dangerous",
                    code="XSS_VIOLATION",
                    value="[REDACTED]"
                )]
            )
        
        return cleaned
    
    def sanitize_url(self, url: str) -> str:
        """Sanitize URL input to prevent XSS and other attacks"""
        
        if not url:
            return ""
        
        # Basic URL validation
        if not re.match(r'^https?://', url, re.IGNORECASE):
            raise ValueError("URL must start with http:// or https://")
        
        # Check for dangerous protocols
        dangerous_protocols = ['javascript:', 'data:', 'vbscript:', 'file:', 'ftp:']
        url_lower = url.lower()
        
        for protocol in dangerous_protocols:
            if protocol in url_lower:
                raise ValidationException(
                    message="Dangerous URL protocol detected",
                    field_errors=[FieldError(
                        field="url",
                        message=f"Protocol '{protocol}' is not allowed",
                        code="DANGEROUS_PROTOCOL",
                        value=protocol
                    )]
                )
        
        # URL encode for safety
        return quote(url, safe=':/?#[]@!$&\'()*+,;=')


class InputSanitizer:
    """Comprehensive input sanitization for financial applications"""
    
    def __init__(self):
        self.sql_prevention = SQLInjectionPrevention()
        self.xss_prevention = XSSPrevention()
        
        # Financial data specific patterns
        self.pii_patterns = [
            (r'\b\d{3}[\s\-]?\d{2}[\s\-]?\d{4}\b', '[SSN]'),  # SSN
            (r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b', '[CARD]'),  # Credit card
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),  # Email
            (r'\b\d{3}[\s\-]?\d{3}[\s\-]?\d{4}\b', '[PHONE]'),  # Phone
            (r'\b\d{9,12}\b', '[ACCOUNT]'),  # Account numbers
        ]
        
        self.compiled_pii_patterns = [
            (re.compile(pattern, re.IGNORECASE), replacement)
            for pattern, replacement in self.pii_patterns
        ]
    
    def sanitize_financial_input(
        self, 
        value: str, 
        field_name: str = "input",
        max_length: int = 1000,
        remove_pii: bool = True
    ) -> str:
        """
        Comprehensive sanitization for financial application inputs
        
        Args:
            value: Input value to sanitize
            field_name: Name of the field (for error reporting)
            max_length: Maximum allowed length
            remove_pii: Whether to remove/mask PII data
        
        Returns:
            Sanitized input safe for storage and processing
        """
        
        if not isinstance(value, str):
            value = str(value)
        
        original_length = len(value)
        
        # Length validation
        if original_length > max_length:
            raise ValidationException(
                message=f"Input too long for field '{field_name}'",
                field_errors=[FieldError(
                    field=field_name,
                    message=f"Cannot exceed {max_length} characters (got {original_length})",
                    code="INPUT_TOO_LONG",
                    value=original_length
                )]
            )
        
        # Remove null bytes and control characters
        value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
        
        # SQL injection check
        if self.sql_prevention.is_sql_injection_attempt(value):
            raise ValidationException(
                message=f"Security violation in field '{field_name}'",
                field_errors=[FieldError(
                    field=field_name,
                    message="Input contains potentially dangerous patterns",
                    code="SQL_INJECTION_ATTEMPT",
                    value="[REDACTED]"
                )]
            )
        
        # XSS prevention
        value = self.xss_prevention.sanitize_html_input(value)
        
        # PII removal/masking
        if remove_pii:
            for pattern, replacement in self.compiled_pii_patterns:
                value = pattern.sub(replacement, value)
        
        # Normalize whitespace
        value = re.sub(r'\s+', ' ', value).strip()
        
        return value
    
    def validate_and_sanitize_dict(
        self, 
        data: Dict[str, Any], 
        field_configs: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Validate and sanitize a dictionary of inputs
        
        Args:
            data: Dictionary of field names to values
            field_configs: Optional configuration for each field
        
        Returns:
            Dictionary with sanitized values
        """
        
        if not isinstance(data, dict):
            raise ValidationException(
                message="Input must be a dictionary",
                field_errors=[FieldError(
                    field="data",
                    message="Expected dictionary input",
                    code="INVALID_INPUT_TYPE",
                    value=type(data).__name__
                )]
            )
        
        sanitized_data = {}
        field_errors = []
        
        for field_name, value in data.items():
            try:
                # Get field-specific configuration
                config = field_configs.get(field_name, {}) if field_configs else {}
                max_length = config.get('max_length', 1000)
                remove_pii = config.get('remove_pii', True)
                
                if isinstance(value, str):
                    sanitized_value = self.sanitize_financial_input(
                        value, field_name, max_length, remove_pii
                    )
                else:
                    # For non-string values, perform basic validation
                    sanitized_value = value
                
                sanitized_data[field_name] = sanitized_value
                
            except ValidationException as e:
                field_errors.extend(e.field_errors)
            except Exception as e:
                field_errors.append(FieldError(
                    field=field_name,
                    message=str(e),
                    code="SANITIZATION_ERROR",
                    value=str(value)[:100] if value else None
                ))
        
        if field_errors:
            raise ValidationException(
                message="Input validation failed",
                field_errors=field_errors
            )
        
        return sanitized_data


class SecurityHeaderValidator:
    """Validate security-related headers and tokens"""
    
    def __init__(self):
        self.token_pattern = re.compile(r'^[A-Za-z0-9+/=_-]+$')
        self.csrf_token_length = 64
    
    def validate_csrf_token(self, token: str) -> bool:
        """Validate CSRF token format and structure"""
        
        if not token:
            return False
        
        # Check format
        if not self.token_pattern.match(token):
            return False
        
        # Check length (tokens should be sufficiently long)
        if len(token) < 32:
            return False
        
        return True
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key format"""
        
        if not api_key:
            return False
        
        # Basic format validation
        if not self.token_pattern.match(api_key):
            return False
        
        # Minimum length requirement
        if len(api_key) < 32:
            return False
        
        return True
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate a cryptographically secure token"""
        return secrets.token_urlsafe(length)


# Global instances for easy import
sql_injection_prevention = SQLInjectionPrevention()
xss_prevention = XSSPrevention()
input_sanitizer = InputSanitizer()
security_header_validator = SecurityHeaderValidator()