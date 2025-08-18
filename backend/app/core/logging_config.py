"""
Comprehensive Logging Configuration for FinGood Financial Application

This module provides structured, secure, and compliant logging for financial applications,
including audit trails, performance monitoring, security event logging, and compliance features.
Designed to meet PCI DSS, SOX, and other financial regulatory requirements.
"""

import json
import logging
import logging.config
import logging.handlers
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from contextvars import ContextVar
from dataclasses import dataclass, asdict
from enum import Enum

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
session_id_var: ContextVar[Optional[str]] = ContextVar('session_id', default=None)


class LogLevel(Enum):
    """Standard log levels with numeric values"""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class LogCategory(Enum):
    """Log categories for structured logging"""
    APPLICATION = "application"
    SECURITY = "security"
    AUDIT = "audit"
    TRANSACTION = "transaction"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"
    SYSTEM = "system"
    DATABASE = "database"
    API = "api"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    FILE_UPLOAD = "file_upload"
    DATA_PROCESSING = "data_processing"
    ERROR = "error"


@dataclass
class LogContext:
    """Context information for structured logging"""
    timestamp: str
    level: str
    category: LogCategory
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    correlation_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None


class SensitiveDataFilter:
    """
    Filter to remove or mask sensitive data from log messages
    for compliance with financial data protection requirements.
    """
    
    # Patterns for sensitive data that should be masked
    SENSITIVE_PATTERNS = [
        # Credit card numbers (basic pattern)
        (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '****-****-****-****'),
        # SSN patterns
        (r'\b\d{3}-\d{2}-\d{4}\b', '***-**-****'),
        # Email addresses (partial masking)
        (r'\b([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b', r'\1***@\2'),
        # Phone numbers
        (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '***-***-****'),
        # Account numbers (basic pattern)
        (r'\b[aA]ccount[:\s]*\d{6,}\b', 'Account: ******'),
        # Routing numbers
        (r'\b[rR]outing[:\s]*\d{9}\b', 'Routing: *********'),
    ]
    
    # Fields that should be completely removed or masked
    SENSITIVE_FIELDS = {
        'password', 'secret', 'token', 'key', 'ssn', 'social_security',
        'credit_card', 'account_number', 'routing_number', 'pin',
        'authorization', 'signature', 'private_key', 'api_key'
    }
    
    @classmethod
    def filter_sensitive_data(cls, data: Any) -> Any:
        """
        Filter sensitive data from log messages and structured data
        
        Args:
            data: The data to filter (string, dict, list, etc.)
            
        Returns:
            The filtered data with sensitive information masked
        """
        if isinstance(data, str):
            return cls._filter_string(data)
        elif isinstance(data, dict):
            return cls._filter_dict(data)
        elif isinstance(data, list):
            return [cls.filter_sensitive_data(item) for item in data]
        else:
            return data
    
    @classmethod
    def _filter_string(cls, text: str) -> str:
        """Filter sensitive patterns from string"""
        filtered_text = text
        for pattern, replacement in cls.SENSITIVE_PATTERNS:
            import re
            filtered_text = re.sub(pattern, replacement, filtered_text, flags=re.IGNORECASE)
        return filtered_text
    
    @classmethod
    def _filter_dict(cls, data: dict) -> dict:
        """Filter sensitive fields from dictionary"""
        filtered_data = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in cls.SENSITIVE_FIELDS):
                filtered_data[key] = '***MASKED***'
            else:
                filtered_data[key] = cls.filter_sensitive_data(value)
        return filtered_data


class StructuredJSONFormatter(logging.Formatter):
    """
    Custom JSON formatter that creates structured log entries
    with consistent format for SIEM integration and compliance.
    """
    
    def __init__(self, include_trace: bool = True, mask_sensitive: bool = True):
        super().__init__()
        self.include_trace = include_trace
        self.mask_sensitive = mask_sensitive
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        
        # Base log structure
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add request context if available
        request_id = request_id_var.get()
        user_id = user_id_var.get()
        session_id = session_id_var.get()
        
        if request_id:
            log_entry['request_id'] = request_id
        if user_id:
            log_entry['user_id'] = user_id
        if session_id:
            log_entry['session_id'] = session_id
        
        # Add trace information
        if self.include_trace and record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add custom fields from extra (with datetime serialization)
        for key, value in record.__dict__.items():
            if key not in {'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'getMessage'}:
                # Handle datetime serialization
                if isinstance(value, datetime):
                    log_entry[key] = value.isoformat()
                elif hasattr(value, '__dict__') and hasattr(value, 'isoformat'):
                    log_entry[key] = value.isoformat()
                else:
                    log_entry[key] = value
        
        # Filter sensitive data if enabled
        if self.mask_sensitive:
            log_entry = SensitiveDataFilter.filter_sensitive_data(log_entry)
        
        # Add compliance metadata
        log_entry['compliance'] = {
            'retention_required': True,
            'classification': self._classify_log_sensitivity(record),
            'audit_trail': record.levelno >= logging.WARNING
        }
        
        return json.dumps(log_entry, ensure_ascii=False, separators=(',', ':'))
    
    def _classify_log_sensitivity(self, record: logging.LogRecord) -> str:
        """Classify log sensitivity for compliance purposes"""
        if hasattr(record, 'category'):
            category = record.category
            if category in [LogCategory.SECURITY, LogCategory.AUDIT, LogCategory.TRANSACTION]:
                return 'sensitive'
            elif category in [LogCategory.COMPLIANCE, LogCategory.AUTHENTICATION]:
                return 'confidential'
        
        if record.levelno >= logging.ERROR:
            return 'sensitive'
        elif record.levelno >= logging.WARNING:
            return 'internal'
        else:
            return 'public'


class ComplianceFormatter(logging.Formatter):
    """
    Specialized formatter for compliance and audit logs
    that ensures all required fields are present for financial regulations.
    """
    
    REQUIRED_FIELDS = {
        'timestamp', 'level', 'event_type', 'user_id', 'session_id',
        'request_id', 'outcome', 'resource', 'action'
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format compliance log with all required fields"""
        
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'level': record.levelname,
            'event_type': getattr(record, 'event_type', 'unknown'),
            'user_id': getattr(record, 'user_id', user_id_var.get()),
            'session_id': getattr(record, 'session_id', session_id_var.get()),
            'request_id': getattr(record, 'request_id', request_id_var.get()),
            'outcome': getattr(record, 'outcome', 'unknown'),
            'resource': getattr(record, 'resource', 'unknown'),
            'action': getattr(record, 'action', 'unknown'),
            'message': record.getMessage(),
            'client_ip': getattr(record, 'client_ip', None),
            'user_agent': getattr(record, 'user_agent', None),
            'compliance_version': '1.0',
            'regulatory_framework': ['PCI_DSS', 'SOX', 'GDPR']
        }
        
        # Add additional fields from record
        for key, value in record.__dict__.items():
            if key.startswith('compliance_') or key.startswith('audit_'):
                log_entry[key] = value
        
        # Ensure data integrity hash for audit trail
        import hashlib
        content = json.dumps(log_entry, sort_keys=True, separators=(',', ':'))
        log_entry['integrity_hash'] = hashlib.sha256(content.encode()).hexdigest()[:16]
        
        return json.dumps(log_entry, ensure_ascii=False, separators=(',', ':'))


class PerformanceFormatter(logging.Formatter):
    """
    Specialized formatter for performance monitoring logs
    with metrics and timing information.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format performance log with metrics"""
        
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'level': record.levelname,
            'metric_type': getattr(record, 'metric_type', 'performance'),
            'request_id': getattr(record, 'request_id', request_id_var.get()),
            'duration_ms': getattr(record, 'duration_ms', None),
            'endpoint': getattr(record, 'endpoint', None),
            'method': getattr(record, 'method', None),
            'status_code': getattr(record, 'status_code', None),
            'response_size': getattr(record, 'response_size', None),
            'db_queries': getattr(record, 'db_queries', None),
            'db_duration_ms': getattr(record, 'db_duration_ms', None),
            'cache_hits': getattr(record, 'cache_hits', None),
            'cache_misses': getattr(record, 'cache_misses', None),
            'memory_usage_mb': getattr(record, 'memory_usage_mb', None),
            'cpu_usage_percent': getattr(record, 'cpu_usage_percent', None),
            'message': record.getMessage()
        }
        
        return json.dumps(log_entry, ensure_ascii=False, separators=(',', ':'))


class LoggingConfig:
    """
    Central logging configuration for the FinGood application
    with support for multiple log types, formatters, and handlers.
    """
    
    def __init__(self, 
                 log_level: str = "INFO",
                 log_dir: str = "logs",
                 enable_console: bool = True,
                 enable_file: bool = True,
                 enable_rotation: bool = True,
                 max_file_size: int = 100 * 1024 * 1024,  # 100MB
                 backup_count: int = 10,
                 enable_syslog: bool = False,
                 syslog_address: Optional[str] = None,
                 enable_remote_logging: bool = False,
                 remote_log_url: Optional[str] = None):
        
        self.log_level = log_level.upper()
        self.log_dir = Path(log_dir)
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.enable_rotation = enable_rotation
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.enable_syslog = enable_syslog
        self.syslog_address = syslog_address
        self.enable_remote_logging = enable_remote_logging
        self.remote_log_url = remote_log_url
        
        # Create log directories
        self._create_log_directories()
    
    def _create_log_directories(self):
        """Create necessary log directories"""
        directories = [
            self.log_dir,
            self.log_dir / "application",
            self.log_dir / "security",
            self.log_dir / "audit",
            self.log_dir / "transaction",
            self.log_dir / "performance",
            self.log_dir / "compliance",
            self.log_dir / "error"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        Generate logging configuration dictionary for logging.config.dictConfig
        
        Returns:
            Complete logging configuration dictionary
        """
        
        config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'structured_json': {
                    '()': StructuredJSONFormatter,
                    'include_trace': True,
                    'mask_sensitive': True
                },
                'compliance': {
                    '()': ComplianceFormatter
                },
                'performance': {
                    '()': PerformanceFormatter
                },
                'console': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                }
            },
            'handlers': {},
            'loggers': {
                # Root logger
                '': {
                    'level': self.log_level,
                    'handlers': []
                },
                # Application loggers
                'fingood': {
                    'level': self.log_level,
                    'handlers': ['application_file', 'error_file'],
                    'propagate': False
                },
                'fingood.security': {
                    'level': 'INFO',
                    'handlers': ['security_file', 'console'],
                    'propagate': False
                },
                'fingood.audit': {
                    'level': 'INFO',
                    'handlers': ['audit_file', 'compliance_file'],
                    'propagate': False
                },
                'fingood.transaction': {
                    'level': 'INFO',
                    'handlers': ['transaction_file', 'compliance_file'],
                    'propagate': False
                },
                'fingood.performance': {
                    'level': 'INFO',
                    'handlers': ['performance_file'],
                    'propagate': False
                },
                'fingood.compliance': {
                    'level': 'INFO',
                    'handlers': ['compliance_file'],
                    'propagate': False
                },
                # External library loggers
                'uvicorn': {
                    'level': 'INFO',
                    'handlers': ['application_file'],
                    'propagate': False
                },
                'sqlalchemy': {
                    'level': 'WARNING',
                    'handlers': ['application_file'],
                    'propagate': False
                }
            }
        }
        
        # Add console handler if enabled
        if self.enable_console:
            config['handlers']['console'] = {
                'class': 'logging.StreamHandler',
                'level': self.log_level,
                'formatter': 'console',
                'stream': 'ext://sys.stdout'
            }
            config['loggers']['']['handlers'].append('console')
        
        # Add file handlers if enabled
        if self.enable_file:
            self._add_file_handlers(config)
        
        # Add syslog handler if enabled
        if self.enable_syslog:
            self._add_syslog_handler(config)
        
        # Add remote logging if enabled
        if self.enable_remote_logging:
            self._add_remote_handler(config)
        
        return config
    
    def _add_file_handlers(self, config: Dict[str, Any]):
        """Add file handlers to configuration"""
        
        handlers = {
            'application_file': ('application/app.jsonl', 'structured_json'),
            'security_file': ('security/security.jsonl', 'structured_json'),
            'audit_file': ('audit/audit.jsonl', 'compliance'),
            'transaction_file': ('transaction/transactions.jsonl', 'compliance'),
            'performance_file': ('performance/performance.jsonl', 'performance'),
            'compliance_file': ('compliance/compliance.jsonl', 'compliance'),
            'error_file': ('error/errors.jsonl', 'structured_json')
        }
        
        for handler_name, (filename, formatter) in handlers.items():
            if self.enable_rotation:
                config['handlers'][handler_name] = {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'DEBUG',
                    'formatter': formatter,
                    'filename': str(self.log_dir / filename),
                    'maxBytes': self.max_file_size,
                    'backupCount': self.backup_count,
                    'encoding': 'utf-8'
                }
            else:
                config['handlers'][handler_name] = {
                    'class': 'logging.FileHandler',
                    'level': 'DEBUG',
                    'formatter': formatter,
                    'filename': str(self.log_dir / filename),
                    'encoding': 'utf-8'
                }
    
    def _add_syslog_handler(self, config: Dict[str, Any]):
        """Add syslog handler for centralized logging"""
        config['handlers']['syslog'] = {
            'class': 'logging.handlers.SysLogHandler',
            'level': 'INFO',
            'formatter': 'structured_json',
            'address': self.syslog_address or '/dev/log',
            'facility': 'local0'
        }
        
        # Add to security and compliance loggers
        config['loggers']['fingood.security']['handlers'].append('syslog')
        config['loggers']['fingood.compliance']['handlers'].append('syslog')
    
    def _add_remote_handler(self, config: Dict[str, Any]):
        """Add remote logging handler for SIEM integration"""
        if self.remote_log_url:
            config['handlers']['remote'] = {
                'class': 'logging.handlers.HTTPHandler',
                'level': 'WARNING',
                'formatter': 'structured_json',
                'host': self.remote_log_url,
                'url': '/logs',
                'method': 'POST'
            }
            
            # Add to critical loggers
            config['loggers']['fingood.security']['handlers'].append('remote')
            config['loggers']['fingood.compliance']['handlers'].append('remote')
    
    def setup_logging(self):
        """Configure logging for the application"""
        config = self.get_logging_config()
        logging.config.dictConfig(config)
        
        # Log successful configuration
        logger = logging.getLogger('fingood')
        logger.info(
            "Logging configuration initialized",
            extra={
                'category': LogCategory.SYSTEM.value,
                'log_level': self.log_level,
                'log_dir': str(self.log_dir),
                'handlers_enabled': {
                    'console': self.enable_console,
                    'file': self.enable_file,
                    'syslog': self.enable_syslog,
                    'remote': self.enable_remote_logging
                }
            }
        )


def get_logger(name: str, category: LogCategory = LogCategory.APPLICATION) -> logging.Logger:
    """
    Get a logger with the specified name and category
    
    Args:
        name: Logger name (usually module name)
        category: Log category for structured logging
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Add category as default extra
    class CategoryAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            kwargs.setdefault('extra', {})
            kwargs['extra']['category'] = category.value
            return msg, kwargs
    
    return CategoryAdapter(logger, {})


def set_request_context(request_id: str = None, user_id: str = None, session_id: str = None):
    """
    Set request context for logging correlation
    
    Args:
        request_id: Unique request identifier
        user_id: User identifier
        session_id: Session identifier
    """
    if request_id:
        request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)
    if session_id:
        session_id_var.set(session_id)


def clear_request_context():
    """Clear request context"""
    request_id_var.set(None)
    user_id_var.set(None)
    session_id_var.set(None)


def log_transaction(
    transaction_type: str,
    user_id: str,
    amount: float = None,
    currency: str = None,
    account_id: str = None,
    outcome: str = "success",
    details: Dict[str, Any] = None
):
    """
    Log transaction for audit trail and compliance
    
    Args:
        transaction_type: Type of transaction
        user_id: User performing transaction
        amount: Transaction amount (if applicable)
        currency: Currency code
        account_id: Account identifier
        outcome: Transaction outcome
        details: Additional transaction details
    """
    logger = logging.getLogger('fingood.transaction')
    
    log_data = {
        'event_type': 'transaction',
        'transaction_type': transaction_type,
        'user_id': user_id,
        'outcome': outcome,
        'resource': f'account_{account_id}' if account_id else 'unknown',
        'action': transaction_type,
        'compliance_required': True
    }
    
    if amount is not None:
        log_data['amount'] = amount
    if currency:
        log_data['currency'] = currency
    if details:
        log_data.update(details)
    
    logger.info(
        f"Transaction {transaction_type}: {outcome}",
        extra=log_data
    )


def log_security_event(
    event_type: str,
    risk_level: str,
    user_id: str = None,
    client_ip: str = None,
    outcome: str = None,
    details: Dict[str, Any] = None
):
    """
    Log security event for monitoring and compliance
    
    Args:
        event_type: Type of security event
        risk_level: Risk level (low, medium, high, critical)
        user_id: User identifier
        client_ip: Client IP address
        outcome: Event outcome
        details: Additional event details
    """
    logger = logging.getLogger('fingood.security')
    
    log_data = {
        'event_type': event_type,
        'risk_level': risk_level,
        'outcome': outcome or 'unknown',
        'resource': 'security_system',
        'action': event_type,
        'security_event': True
    }
    
    if user_id:
        log_data['user_id'] = user_id
    if client_ip:
        log_data['client_ip'] = client_ip
    if details:
        log_data.update(details)
    
    level = logging.CRITICAL if risk_level == 'critical' else \
            logging.ERROR if risk_level == 'high' else \
            logging.WARNING if risk_level == 'medium' else \
            logging.INFO
    
    logger.log(
        level,
        f"Security event {event_type}: {risk_level} risk",
        extra=log_data
    )


def log_performance_metric(
    metric_type: str,
    duration_ms: float,
    endpoint: str = None,
    additional_metrics: Dict[str, Any] = None
):
    """
    Log performance metric for monitoring
    
    Args:
        metric_type: Type of performance metric
        duration_ms: Duration in milliseconds
        endpoint: API endpoint
        additional_metrics: Additional performance data
    """
    logger = logging.getLogger('fingood.performance')
    
    log_data = {
        'metric_type': metric_type,
        'duration_ms': duration_ms,
        'endpoint': endpoint,
    }
    
    if additional_metrics:
        log_data.update(additional_metrics)
    
    logger.info(
        f"Performance metric {metric_type}: {duration_ms}ms",
        extra=log_data
    )


# Global logging configuration instance
_logging_config: Optional[LoggingConfig] = None


def initialize_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    **kwargs
) -> LoggingConfig:
    """
    Initialize global logging configuration
    
    Args:
        log_level: Logging level
        log_dir: Log directory path
        **kwargs: Additional configuration options
        
    Returns:
        LoggingConfig instance
    """
    global _logging_config
    _logging_config = LoggingConfig(log_level=log_level, log_dir=log_dir, **kwargs)
    _logging_config.setup_logging()
    return _logging_config


def get_logging_config() -> Optional[LoggingConfig]:
    """Get the global logging configuration"""
    return _logging_config