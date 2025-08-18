"""
Transaction Audit Logger for FinGood Financial Application

This module provides comprehensive transaction logging and audit trails
to meet financial compliance requirements including PCI DSS, SOX, GDPR,
and other regulatory frameworks. All sensitive data is properly masked
or encrypted while maintaining audit integrity.
"""

import json
import logging
import hashlib
import hmac
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from dataclasses import dataclass, asdict
from uuid import uuid4
import asyncio

from app.core.logging_config import get_logger, LogCategory


class TransactionType(Enum):
    """Transaction types for audit logging"""
    ACCOUNT_CREATE = "account_create"
    ACCOUNT_UPDATE = "account_update"
    ACCOUNT_DELETE = "account_delete"
    TRANSACTION_CREATE = "transaction_create"
    TRANSACTION_UPDATE = "transaction_update"
    TRANSACTION_DELETE = "transaction_delete"
    BALANCE_INQUIRY = "balance_inquiry"
    TRANSFER = "transfer"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    PAYMENT = "payment"
    REFUND = "refund"
    CATEGORIZATION = "categorization"
    BUDGET_CREATE = "budget_create"
    BUDGET_UPDATE = "budget_update"
    REPORT_GENERATE = "report_generate"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    FILE_UPLOAD = "file_upload"
    FILE_PROCESS = "file_process"


class TransactionOutcome(Enum):
    """Transaction outcomes for audit purposes"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    PENDING = "pending"
    CANCELLED = "cancelled"
    ERROR = "error"
    VALIDATION_FAILED = "validation_failed"
    AUTHORIZATION_FAILED = "authorization_failed"
    INSUFFICIENT_FUNDS = "insufficient_funds"
    DUPLICATE = "duplicate"


class DataSensitivity(Enum):
    """Data sensitivity classification for compliance"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    TOP_SECRET = "top_secret"


@dataclass
class TransactionAuditRecord:
    """Structured transaction audit record for compliance"""
    audit_id: str
    timestamp: str
    transaction_type: TransactionType
    outcome: TransactionOutcome
    user_id: str
    session_id: Optional[str]
    request_id: Optional[str]
    client_ip: Optional[str]
    user_agent: Optional[str]
    resource_type: str
    resource_id: Optional[str]
    action_performed: str
    affected_records: List[str]
    before_values: Optional[Dict[str, Any]]
    after_values: Optional[Dict[str, Any]]
    amount: Optional[Decimal]
    currency: Optional[str]
    account_id: Optional[str]
    counterparty_id: Optional[str]
    authorization_level: str
    data_sensitivity: DataSensitivity
    compliance_flags: List[str]
    error_code: Optional[str]
    error_message: Optional[str]
    processing_duration_ms: Optional[float]
    integrity_hash: str
    retention_period_years: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        
        # Convert enums to strings
        data['transaction_type'] = self.transaction_type.value
        data['outcome'] = self.outcome.value
        data['data_sensitivity'] = self.data_sensitivity.value
        
        # Convert Decimal to string for JSON serialization
        if self.amount is not None:
            data['amount'] = str(self.amount)
        
        return data


class ComplianceDataMasker:
    """
    Masks sensitive financial data for compliance while preserving
    audit trail integrity and enabling investigation when needed.
    """
    
    # PCI DSS data elements that must be protected
    PCI_SENSITIVE_FIELDS = {
        'card_number', 'cvv', 'pin', 'magnetic_stripe', 'chip_data',
        'card_verification_value', 'cvc', 'security_code'
    }
    
    # Financial data that requires special handling
    FINANCIAL_SENSITIVE_FIELDS = {
        'account_number', 'routing_number', 'iban', 'swift_code',
        'bank_account', 'ssn', 'tax_id', 'social_security_number'
    }
    
    # Personal data subject to GDPR/privacy regulations
    PERSONAL_SENSITIVE_FIELDS = {
        'email', 'phone', 'address', 'full_name', 'date_of_birth',
        'driver_license', 'passport', 'national_id'
    }
    
    @classmethod
    def mask_sensitive_data(
        cls, 
        data: Dict[str, Any], 
        preserve_audit_fields: bool = True
    ) -> Dict[str, Any]:
        """
        Mask sensitive data while preserving audit trail integrity
        
        Args:
            data: Data dictionary to mask
            preserve_audit_fields: Whether to preserve certain fields for audit
            
        Returns:
            Masked data dictionary
        """
        if not isinstance(data, dict):
            return data
        
        masked_data = {}
        
        for key, value in data.items():
            key_lower = key.lower()
            
            # Recursively mask nested dictionaries
            if isinstance(value, dict):
                masked_data[key] = cls.mask_sensitive_data(value, preserve_audit_fields)
            elif isinstance(value, list):
                masked_data[key] = [
                    cls.mask_sensitive_data(item, preserve_audit_fields) 
                    if isinstance(item, dict) else cls._mask_value(key, item)
                    for item in value
                ]
            else:
                masked_data[key] = cls._mask_value(key, value)
        
        return masked_data
    
    @classmethod
    def _mask_value(cls, field_name: str, value: Any) -> Any:
        """Mask individual field value based on sensitivity"""
        if value is None:
            return None
        
        field_lower = field_name.lower()
        value_str = str(value)
        
        # PCI DSS protected data - must be fully masked
        if any(sensitive in field_lower for sensitive in cls.PCI_SENSITIVE_FIELDS):
            if 'card' in field_lower or 'number' in field_lower:
                # Show last 4 digits for card numbers
                if len(value_str) >= 4:
                    return '*' * (len(value_str) - 4) + value_str[-4:]
                else:
                    return '*' * len(value_str)
            else:
                return '***PROTECTED***'
        
        # Financial sensitive data - partial masking
        elif any(sensitive in field_lower for sensitive in cls.FINANCIAL_SENSITIVE_FIELDS):
            if 'account' in field_lower and len(value_str) >= 4:
                return '****' + value_str[-4:]
            elif 'routing' in field_lower:
                return '***' + value_str[-3:] if len(value_str) >= 3 else '***'
            elif 'ssn' in field_lower or 'social' in field_lower:
                return 'XXX-XX-' + value_str[-4:] if len(value_str) >= 4 else 'XXX-XX-XXXX'
            else:
                return '***MASKED***'
        
        # Personal data - GDPR compliance
        elif any(sensitive in field_lower for sensitive in cls.PERSONAL_SENSITIVE_FIELDS):
            if 'email' in field_lower and '@' in value_str:
                parts = value_str.split('@')
                return f"{parts[0][:2]}***@{parts[1]}"
            elif 'phone' in field_lower:
                return f"***-***-{value_str[-4:]}" if len(value_str) >= 4 else "***-***-****"
            elif 'name' in field_lower:
                # Keep first and last character for audit correlation
                if len(value_str) > 2:
                    return f"{value_str[0]}***{value_str[-1]}"
                else:
                    return "***"
            else:
                return '***PRIVATE***'
        
        # Amount fields - precision masking for privacy
        elif 'amount' in field_lower or 'balance' in field_lower:
            try:
                amount = Decimal(str(value))
                # Round to nearest dollar for privacy while preserving audit value
                rounded = amount.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
                return f"~{rounded}"
            except:
                return value
        
        return value
    
    @classmethod
    def create_data_hash(cls, data: Dict[str, Any], secret_key: str) -> str:
        """
        Create HMAC hash of data for integrity verification
        
        Args:
            data: Data to hash
            secret_key: Secret key for HMAC
            
        Returns:
            HMAC hash string
        """
        # Sort data for consistent hashing
        sorted_data = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hmac.new(
            secret_key.encode(),
            sorted_data.encode(),
            hashlib.sha256
        ).hexdigest()


class TransactionAuditLogger:
    """
    Comprehensive transaction audit logger for financial compliance.
    Provides secure, immutable audit trails with proper data protection.
    """
    
    def __init__(self, secret_key: str, retention_years: int = 7):
        """
        Initialize transaction audit logger
        
        Args:
            secret_key: Secret key for data integrity verification
            retention_years: Default retention period for audit records
        """
        self.secret_key = secret_key
        self.retention_years = retention_years
        self.logger = get_logger('fingood.transaction', LogCategory.TRANSACTION)
        
        # Initialize compliance logger
        self.compliance_logger = get_logger('fingood.compliance', LogCategory.COMPLIANCE)
        
        # Track audit statistics
        self.audit_stats = {
            'records_created': 0,
            'integrity_verifications': 0,
            'compliance_flags_raised': 0
        }
    
    async def log_transaction(
        self,
        transaction_type: TransactionType,
        outcome: TransactionOutcome,
        user_id: str,
        action_performed: str,
        resource_type: str = "transaction",
        resource_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        affected_records: Optional[List[str]] = None,
        before_values: Optional[Dict[str, Any]] = None,
        after_values: Optional[Dict[str, Any]] = None,
        amount: Optional[Union[Decimal, float, str]] = None,
        currency: Optional[str] = None,
        account_id: Optional[str] = None,
        counterparty_id: Optional[str] = None,
        authorization_level: str = "user",
        data_sensitivity: DataSensitivity = DataSensitivity.CONFIDENTIAL,
        compliance_flags: Optional[List[str]] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        processing_duration_ms: Optional[float] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log a transaction for audit trail and compliance
        
        Args:
            transaction_type: Type of transaction
            outcome: Transaction outcome
            user_id: User performing the transaction
            action_performed: Description of action
            resource_type: Type of resource affected
            resource_id: ID of the affected resource
            session_id: Session identifier
            request_id: Request identifier
            client_ip: Client IP address
            user_agent: User agent string
            affected_records: List of affected record IDs
            before_values: Values before the transaction
            after_values: Values after the transaction
            amount: Transaction amount
            currency: Currency code
            account_id: Account identifier
            counterparty_id: Counterparty identifier
            authorization_level: Authorization level required
            data_sensitivity: Data sensitivity classification
            compliance_flags: List of compliance flags
            error_code: Error code if applicable
            error_message: Error message if applicable
            processing_duration_ms: Processing duration in milliseconds
            additional_context: Additional context data
            
        Returns:
            Audit record ID
        """
        # Generate unique audit ID
        audit_id = str(uuid4())
        
        # Convert amount to Decimal for precision
        if amount is not None:
            if isinstance(amount, str):
                amount = Decimal(amount)
            elif isinstance(amount, float):
                amount = Decimal(str(amount))
        
        # Mask sensitive data in before/after values
        masked_before = ComplianceDataMasker.mask_sensitive_data(before_values or {})
        masked_after = ComplianceDataMasker.mask_sensitive_data(after_values or {})
        
        # Create audit record
        audit_record = TransactionAuditRecord(
            audit_id=audit_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            transaction_type=transaction_type,
            outcome=outcome,
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            client_ip=client_ip,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            action_performed=action_performed,
            affected_records=affected_records or [],
            before_values=masked_before,
            after_values=masked_after,
            amount=amount,
            currency=currency,
            account_id=account_id,
            counterparty_id=counterparty_id,
            authorization_level=authorization_level,
            data_sensitivity=data_sensitivity,
            compliance_flags=compliance_flags or [],
            error_code=error_code,
            error_message=error_message,
            processing_duration_ms=processing_duration_ms,
            integrity_hash="",  # Will be calculated below
            retention_period_years=self.retention_years
        )
        
        # Calculate integrity hash
        record_dict = audit_record.to_dict()
        del record_dict['integrity_hash']  # Exclude hash from hash calculation
        audit_record.integrity_hash = ComplianceDataMasker.create_data_hash(
            record_dict, self.secret_key
        )
        
        # Log the audit record
        await self._write_audit_record(audit_record, additional_context)
        
        # Update statistics
        self.audit_stats['records_created'] += 1
        if compliance_flags:
            self.audit_stats['compliance_flags_raised'] += len(compliance_flags)
        
        return audit_id
    
    async def _write_audit_record(
        self, 
        audit_record: TransactionAuditRecord,
        additional_context: Optional[Dict[str, Any]] = None
    ):
        """Write audit record to appropriate logs"""
        
        # Convert to dict for logging
        record_dict = audit_record.to_dict()
        
        # Add additional context if provided
        if additional_context:
            record_dict['additional_context'] = ComplianceDataMasker.mask_sensitive_data(
                additional_context
            )
        
        # Add compliance metadata
        compliance_metadata = {
            'regulatory_frameworks': ['PCI_DSS', 'SOX', 'GDPR', 'CCPA'],
            'audit_standard': 'ISO_27001',
            'data_classification': audit_record.data_sensitivity.value,
            'retention_required': True,
            'retention_period_years': audit_record.retention_period_years,
            'immutable_record': True,
            'audit_trail_version': '1.0'
        }
        record_dict['compliance_metadata'] = compliance_metadata
        
        # Log to transaction audit log
        self.logger.info(
            f"Transaction audit: {audit_record.transaction_type.value} - {audit_record.outcome.value}",
            extra=record_dict
        )
        
        # Log to compliance log for high-sensitivity transactions
        if (audit_record.data_sensitivity in [DataSensitivity.RESTRICTED, DataSensitivity.TOP_SECRET] 
            or audit_record.compliance_flags 
            or audit_record.outcome in [TransactionOutcome.FAILURE, TransactionOutcome.ERROR]):
            
            self.compliance_logger.warning(
                f"High-sensitivity transaction audit: {audit_record.audit_id}",
                extra={
                    'audit_id': audit_record.audit_id,
                    'transaction_type': audit_record.transaction_type.value,
                    'outcome': audit_record.outcome.value,
                    'user_id': audit_record.user_id,
                    'data_sensitivity': audit_record.data_sensitivity.value,
                    'compliance_flags': audit_record.compliance_flags,
                    'requires_investigation': audit_record.outcome in [
                        TransactionOutcome.FAILURE, TransactionOutcome.ERROR
                    ]
                }
            )
    
    async def verify_audit_integrity(self, audit_id: str, record_data: Dict[str, Any]) -> bool:
        """
        Verify the integrity of an audit record
        
        Args:
            audit_id: Audit record ID
            record_data: Record data to verify
            
        Returns:
            True if integrity is verified, False otherwise
        """
        try:
            # Extract the stored hash
            stored_hash = record_data.get('integrity_hash')
            if not stored_hash:
                return False
            
            # Recreate record without hash
            verification_data = record_data.copy()
            del verification_data['integrity_hash']
            
            # Calculate expected hash
            expected_hash = ComplianceDataMasker.create_data_hash(
                verification_data, self.secret_key
            )
            
            # Verify hashes match
            is_valid = hmac.compare_digest(stored_hash, expected_hash)
            
            # Update statistics
            self.audit_stats['integrity_verifications'] += 1
            
            # Log verification result
            self.compliance_logger.info(
                f"Audit integrity verification: {audit_id}",
                extra={
                    'audit_id': audit_id,
                    'integrity_verified': is_valid,
                    'verification_timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
            
            return is_valid
            
        except Exception as e:
            self.compliance_logger.error(
                f"Audit integrity verification failed: {audit_id}",
                extra={
                    'audit_id': audit_id,
                    'error': str(e),
                    'verification_timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
            return False
    
    def get_audit_statistics(self) -> Dict[str, Any]:
        """Get audit logging statistics"""
        return {
            'statistics': self.audit_stats.copy(),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'retention_years': self.retention_years
        }
    
    async def log_data_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        access_type: str,
        outcome: TransactionOutcome = TransactionOutcome.SUCCESS,
        data_sensitivity: DataSensitivity = DataSensitivity.CONFIDENTIAL,
        justification: Optional[str] = None
    ) -> str:
        """
        Log data access for compliance and audit purposes
        
        Args:
            user_id: User accessing the data
            resource_type: Type of resource accessed
            resource_id: ID of resource accessed
            access_type: Type of access (read, write, delete, export)
            outcome: Access outcome
            data_sensitivity: Sensitivity of accessed data
            justification: Business justification for access
            
        Returns:
            Audit record ID
        """
        return await self.log_transaction(
            transaction_type=TransactionType.BALANCE_INQUIRY,  # Generic data access
            outcome=outcome,
            user_id=user_id,
            action_performed=f"data_access_{access_type}",
            resource_type=resource_type,
            resource_id=resource_id,
            data_sensitivity=data_sensitivity,
            compliance_flags=['data_access', 'privacy_relevant'] if data_sensitivity in [
                DataSensitivity.CONFIDENTIAL, DataSensitivity.RESTRICTED
            ] else [],
            additional_context={
                'access_type': access_type,
                'justification': justification,
                'privacy_impact': data_sensitivity.value
            }
        )


# Global transaction audit logger instance
_transaction_audit_logger: Optional[TransactionAuditLogger] = None


def initialize_transaction_audit(secret_key: str, retention_years: int = 7) -> TransactionAuditLogger:
    """
    Initialize global transaction audit logger
    
    Args:
        secret_key: Secret key for integrity verification
        retention_years: Retention period for audit records
        
    Returns:
        TransactionAuditLogger instance
    """
    global _transaction_audit_logger
    _transaction_audit_logger = TransactionAuditLogger(secret_key, retention_years)
    return _transaction_audit_logger


def get_transaction_audit_logger() -> Optional[TransactionAuditLogger]:
    """Get the global transaction audit logger"""
    return _transaction_audit_logger


# Convenience functions for common transaction types
async def audit_user_login(user_id: str, outcome: TransactionOutcome, **kwargs) -> str:
    """Audit user login transaction"""
    if _transaction_audit_logger:
        return await _transaction_audit_logger.log_transaction(
            transaction_type=TransactionType.BALANCE_INQUIRY,  # Using as generic access
            outcome=outcome,
            user_id=user_id,
            action_performed="user_login",
            resource_type="authentication",
            **kwargs
        )
    return ""


async def audit_transaction_create(
    user_id: str, 
    transaction_id: str, 
    amount: Decimal, 
    currency: str,
    outcome: TransactionOutcome = TransactionOutcome.SUCCESS,
    **kwargs
) -> str:
    """Audit transaction creation"""
    if _transaction_audit_logger:
        return await _transaction_audit_logger.log_transaction(
            transaction_type=TransactionType.TRANSACTION_CREATE,
            outcome=outcome,
            user_id=user_id,
            action_performed="create_transaction",
            resource_type="transaction",
            resource_id=transaction_id,
            amount=amount,
            currency=currency,
            **kwargs
        )
    return ""


async def audit_file_upload(
    user_id: str, 
    filename: str, 
    file_size: int,
    outcome: TransactionOutcome = TransactionOutcome.SUCCESS,
    **kwargs
) -> str:
    """Audit file upload transaction"""
    if _transaction_audit_logger:
        return await _transaction_audit_logger.log_transaction(
            transaction_type=TransactionType.FILE_UPLOAD,
            outcome=outcome,
            user_id=user_id,
            action_performed="file_upload",
            resource_type="file",
            resource_id=filename,
            additional_context={
                'filename': filename,
                'file_size_bytes': file_size
            },
            **kwargs
        )
    return ""


async def audit_data_export(
    user_id: str, 
    export_type: str, 
    record_count: int,
    outcome: TransactionOutcome = TransactionOutcome.SUCCESS,
    **kwargs
) -> str:
    """Audit data export transaction"""
    if _transaction_audit_logger:
        return await _transaction_audit_logger.log_transaction(
            transaction_type=TransactionType.DATA_EXPORT,
            outcome=outcome,
            user_id=user_id,
            action_performed=f"export_{export_type}",
            resource_type="data_export",
            data_sensitivity=DataSensitivity.CONFIDENTIAL,
            compliance_flags=['data_export', 'privacy_relevant'],
            additional_context={
                'export_type': export_type,
                'record_count': record_count
            },
            **kwargs
        )
    return ""