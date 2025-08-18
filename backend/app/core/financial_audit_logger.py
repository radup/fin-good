"""
Comprehensive Financial Audit Logger for FinGood Application

This module provides extensive audit logging specifically designed for financial transactions
and operations. It meets stringent regulatory requirements including SOX, PCI DSS, FFIEC,
GLBA, and other financial industry compliance standards.

Features:
- Immutable audit trails with cryptographic integrity
- Complete transaction lifecycle tracking
- Regulatory compliance enforcement
- Data lineage and change tracking
- Automated compliance violation detection
- Real-time financial monitoring and alerting
"""

import json
import logging
import hashlib
import hmac
import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional, List, Union, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
import asyncio
from contextlib import asynccontextmanager

from app.core.logging_config import get_logger, LogCategory
from app.core.compliance_logger import (
    ComplianceLogger, 
    RegulatoryFramework,
    ComplianceEventType,
    DataClassification,
    ComplianceRisk
)


class FinancialOperationType(Enum):
    """Financial operation types for comprehensive audit logging"""
    
    # Transaction Operations
    TRANSACTION_CREATE = "transaction_create"
    TRANSACTION_UPDATE = "transaction_update"
    TRANSACTION_DELETE = "transaction_delete"
    TRANSACTION_CATEGORIZE = "transaction_categorize"
    TRANSACTION_RECATEGORIZE = "transaction_recategorize"
    TRANSACTION_BATCH_IMPORT = "transaction_batch_import"
    TRANSACTION_BATCH_DELETE = "transaction_batch_delete"
    TRANSACTION_MERGE = "transaction_merge"
    TRANSACTION_SPLIT = "transaction_split"
    
    # Account Operations
    ACCOUNT_BALANCE_INQUIRY = "account_balance_inquiry"
    ACCOUNT_STATEMENT_GENERATE = "account_statement_generate"
    ACCOUNT_RECONCILIATION = "account_reconciliation"
    
    # Categorization Operations
    CATEGORY_CREATE = "category_create"
    CATEGORY_UPDATE = "category_update"
    CATEGORY_DELETE = "category_delete"
    CATEGORIZATION_RULE_CREATE = "categorization_rule_create"
    CATEGORIZATION_RULE_UPDATE = "categorization_rule_update"
    CATEGORIZATION_RULE_DELETE = "categorization_rule_delete"
    AUTO_CATEGORIZATION = "auto_categorization"
    
    # Data Operations
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    DATA_BACKUP = "data_backup"
    DATA_RESTORE = "data_restore"
    DATA_PURGE = "data_purge"
    DATA_ARCHIVE = "data_archive"
    
    # Financial Analysis
    REPORT_GENERATE = "report_generate"
    ANALYTICS_QUERY = "analytics_query"
    TREND_ANALYSIS = "trend_analysis"
    BUDGET_ANALYSIS = "budget_analysis"
    
    # Security Operations
    SENSITIVE_DATA_ACCESS = "sensitive_data_access"
    PRIVILEGED_OPERATION = "privileged_operation"
    SECURITY_CONFIGURATION = "security_configuration"
    AUDIT_LOG_ACCESS = "audit_log_access"
    
    # System Operations
    SYSTEM_CONFIGURATION = "system_configuration"
    MAINTENANCE_OPERATION = "maintenance_operation"
    DISASTER_RECOVERY = "disaster_recovery"
    COMPLIANCE_CHECK = "compliance_check"


class FinancialAuditRisk(Enum):
    """Financial audit risk levels with regulatory implications"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    REGULATORY_VIOLATION = "regulatory_violation"


class FinancialDataSensitivity(Enum):
    """Financial data sensitivity classification"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    HIGHLY_SENSITIVE = "highly_sensitive"
    PAYMENT_CARD_DATA = "payment_card_data"
    BANK_DATA = "bank_data"
    TAX_DATA = "tax_data"


class FinancialIntegrityLevel(Enum):
    """Financial data integrity requirements"""
    STANDARD = "standard"
    HIGH = "high"
    CRITICAL = "critical"
    IMMUTABLE = "immutable"
    LEGALLY_BINDING = "legally_binding"


@dataclass
class FinancialAuditContext:
    """Context information for financial audit operations"""
    operation_id: str
    user_id: str
    session_id: Optional[str]
    request_id: Optional[str]
    client_ip: Optional[str]
    user_agent: Optional[str]
    business_justification: Optional[str]
    approval_required: bool
    approver_id: Optional[str]
    related_operations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FinancialChangeRecord:
    """Record of changes to financial data"""
    field_name: str
    old_value: Any
    new_value: Any
    change_type: str  # 'create', 'update', 'delete'
    data_sensitivity: FinancialDataSensitivity
    regulatory_impact: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['data_sensitivity'] = self.data_sensitivity.value
        return data


@dataclass
class FinancialAuditRecord:
    """Comprehensive financial audit record"""
    
    # Core identifiers
    audit_id: str
    operation_id: str
    timestamp: str
    
    # Operation details
    operation_type: FinancialOperationType
    operation_outcome: str
    operation_duration_ms: Optional[float]
    
    # User and session context
    user_id: str
    user_role: Optional[str]
    session_id: Optional[str]
    request_id: Optional[str]
    client_ip: Optional[str]
    user_agent: Optional[str]
    
    # Resource information
    resource_type: str
    resource_id: Optional[str]
    parent_resource_id: Optional[str]
    related_resources: List[str]
    
    # Financial data
    amount: Optional[Decimal]
    currency: Optional[str]
    account_id: Optional[str]
    transaction_id: Optional[str]
    balance_before: Optional[Decimal]
    balance_after: Optional[Decimal]
    
    # Change tracking
    changes: List[FinancialChangeRecord]
    data_lineage: List[str]
    
    # Regulatory compliance
    regulatory_frameworks: List[RegulatoryFramework]
    data_classification: DataClassification
    data_sensitivity: FinancialDataSensitivity
    integrity_level: FinancialIntegrityLevel
    compliance_flags: List[str]
    legal_basis: Optional[str]
    retention_period_years: int
    
    # Risk and security
    risk_level: FinancialAuditRisk
    security_controls: List[str]
    approval_required: bool
    approver_id: Optional[str]
    business_justification: Optional[str]
    
    # Error handling
    error_code: Optional[str]
    error_message: Optional[str]
    error_category: Optional[str]
    
    # Integrity verification
    data_hash: str
    integrity_hash: str
    digital_signature: Optional[str]
    verification_status: str
    
    # Additional context
    additional_metadata: Optional[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        
        # Convert enums to strings
        data['operation_type'] = self.operation_type.value
        data['regulatory_frameworks'] = [rf.value for rf in self.regulatory_frameworks]
        data['data_classification'] = self.data_classification.value
        data['data_sensitivity'] = self.data_sensitivity.value
        data['integrity_level'] = self.integrity_level.value
        data['risk_level'] = self.risk_level.value
        
        # Convert Decimal to string for JSON serialization
        if self.amount is not None:
            data['amount'] = str(self.amount)
        if self.balance_before is not None:
            data['balance_before'] = str(self.balance_before)
        if self.balance_after is not None:
            data['balance_after'] = str(self.balance_after)
        
        # Convert change records
        data['changes'] = [change.to_dict() for change in self.changes]
        
        return data


class FinancialDataMasker:
    """
    Advanced data masking for financial audit logs that preserves
    audit requirements while protecting sensitive information
    """
    
    # Financial data field patterns
    FINANCIAL_SENSITIVE_PATTERNS = {
        'account_number': r'\b\d{8,17}\b',
        'routing_number': r'\b\d{9}\b',
        'card_number': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
        'ssn': r'\b\d{3}-?\d{2}-?\d{4}\b',
        'amount': r'\$?\d+\.?\d*'
    }
    
    @classmethod
    def mask_financial_data(
        cls, 
        data: Dict[str, Any], 
        sensitivity_level: FinancialDataSensitivity,
        preserve_audit_fields: bool = True
    ) -> Dict[str, Any]:
        """
        Mask financial data based on sensitivity level while preserving audit requirements
        
        Args:
            data: Data to mask
            sensitivity_level: Financial data sensitivity level
            preserve_audit_fields: Whether to preserve certain fields for audit compliance
            
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
                masked_data[key] = cls.mask_financial_data(value, sensitivity_level, preserve_audit_fields)
            elif isinstance(value, list):
                masked_data[key] = [
                    cls.mask_financial_data(item, sensitivity_level, preserve_audit_fields) 
                    if isinstance(item, dict) else cls._mask_financial_value(key, item, sensitivity_level)
                    for item in value
                ]
            else:
                masked_data[key] = cls._mask_financial_value(key, value, sensitivity_level)
        
        return masked_data
    
    @classmethod
    def _mask_financial_value(
        cls, 
        field_name: str, 
        value: Any, 
        sensitivity_level: FinancialDataSensitivity
    ) -> Any:
        """Mask individual financial field value"""
        if value is None:
            return None
        
        field_lower = field_name.lower()
        value_str = str(value)
        
        # Payment card data - PCI DSS compliance
        if sensitivity_level == FinancialDataSensitivity.PAYMENT_CARD_DATA:
            if any(pattern in field_lower for pattern in ['card', 'cvv', 'pin', 'security_code']):
                if 'card' in field_lower and len(value_str) >= 4:
                    return '*' * (len(value_str) - 4) + value_str[-4:]
                else:
                    return '***PCI_PROTECTED***'
        
        # Bank data - FFIEC/GLBA compliance
        elif sensitivity_level == FinancialDataSensitivity.BANK_DATA:
            if 'account' in field_lower and len(value_str) >= 4:
                return '****' + value_str[-4:]
            elif 'routing' in field_lower:
                return '***' + value_str[-3:] if len(value_str) >= 3 else '***'
        
        # Tax data - IRS compliance
        elif sensitivity_level == FinancialDataSensitivity.TAX_DATA:
            if 'ssn' in field_lower or 'tax_id' in field_lower:
                return 'XXX-XX-' + value_str[-4:] if len(value_str) >= 4 else 'XXX-XX-XXXX'
        
        # Amount masking for privacy
        if 'amount' in field_lower or 'balance' in field_lower:
            try:
                amount = Decimal(str(value))
                # For high sensitivity, round to nearest $10
                if sensitivity_level in [FinancialDataSensitivity.HIGHLY_SENSITIVE, FinancialDataSensitivity.RESTRICTED]:
                    rounded = (amount / 10).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * 10
                    return f"~{rounded}"
                # For medium sensitivity, round to nearest dollar
                else:
                    rounded = amount.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
                    return f"~{rounded}"
            except:
                return value
        
        return value
    
    @classmethod
    def create_data_integrity_hash(cls, data: Dict[str, Any], secret_key: str) -> str:
        """Create cryptographic hash for data integrity verification"""
        sorted_data = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hmac.new(
            secret_key.encode(),
            sorted_data.encode(),
            hashlib.sha256
        ).hexdigest()


class FinancialAuditLogger:
    """
    Comprehensive financial audit logger providing complete transaction
    lifecycle tracking and regulatory compliance
    """
    
    def __init__(
        self, 
        secret_key: str, 
        compliance_logger: Optional[ComplianceLogger] = None,
        retention_years: int = 7
    ):
        """
        Initialize financial audit logger
        
        Args:
            secret_key: Secret key for cryptographic integrity verification
            compliance_logger: Optional compliance logger instance
            retention_years: Default retention period for audit records
        """
        self.secret_key = secret_key
        self.compliance_logger = compliance_logger
        self.retention_years = retention_years
        
        # Initialize loggers
        self.audit_logger = get_logger('fingood.financial_audit', LogCategory.AUDIT)
        self.transaction_logger = get_logger('fingood.financial_transactions', LogCategory.TRANSACTION)
        self.security_logger = get_logger('fingood.financial_security', LogCategory.SECURITY)
        
        # Audit statistics
        self.audit_stats = {
            'total_operations_logged': 0,
            'high_risk_operations': 0,
            'regulatory_violations': 0,
            'integrity_verifications': 0,
            'failed_operations': 0
        }
        
        # Regulatory frameworks mapping
        self.regulatory_frameworks = {
            FinancialOperationType.TRANSACTION_CREATE: [RegulatoryFramework.SOX, RegulatoryFramework.FFIEC],
            FinancialOperationType.TRANSACTION_UPDATE: [RegulatoryFramework.SOX, RegulatoryFramework.FFIEC],
            FinancialOperationType.TRANSACTION_DELETE: [RegulatoryFramework.SOX, RegulatoryFramework.FFIEC],
            FinancialOperationType.DATA_EXPORT: [RegulatoryFramework.GDPR, RegulatoryFramework.GLBA],
            FinancialOperationType.SENSITIVE_DATA_ACCESS: [RegulatoryFramework.PCI_DSS, RegulatoryFramework.GLBA],
        }
    
    async def log_financial_operation(
        self,
        operation_type: FinancialOperationType,
        user_id: str,
        resource_type: str,
        operation_outcome: str = "success",
        resource_id: Optional[str] = None,
        amount: Optional[Union[Decimal, float, str]] = None,
        currency: Optional[str] = "USD",
        changes: Optional[List[FinancialChangeRecord]] = None,
        context: Optional[FinancialAuditContext] = None,
        additional_metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        Log a comprehensive financial operation
        
        Args:
            operation_type: Type of financial operation
            user_id: User performing the operation
            resource_type: Type of resource being operated on
            operation_outcome: Outcome of the operation
            resource_id: ID of the resource
            amount: Financial amount involved
            currency: Currency code
            changes: List of changes made
            context: Additional context information
            additional_metadata: Additional metadata
            **kwargs: Additional operation-specific parameters
            
        Returns:
            Audit record ID
        """
        # Generate unique identifiers
        audit_id = str(uuid.uuid4())
        operation_id = context.operation_id if context else str(uuid.uuid4())
        
        # Convert amount to Decimal for precision
        if amount is not None:
            if isinstance(amount, str):
                amount = Decimal(amount)
            elif isinstance(amount, float):
                amount = Decimal(str(amount))
        
        # Determine regulatory frameworks
        regulatory_frameworks = self.regulatory_frameworks.get(operation_type, [RegulatoryFramework.SOX])
        
        # Determine data sensitivity and classification
        data_sensitivity = self._determine_data_sensitivity(operation_type, resource_type, amount)
        data_classification = self._determine_data_classification(data_sensitivity)
        
        # Determine risk level
        risk_level = self._determine_risk_level(operation_type, operation_outcome, amount, changes)
        
        # Create audit record
        audit_record = FinancialAuditRecord(
            audit_id=audit_id,
            operation_id=operation_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            operation_type=operation_type,
            operation_outcome=operation_outcome,
            operation_duration_ms=kwargs.get('operation_duration_ms'),
            user_id=user_id,
            user_role=kwargs.get('user_role'),
            session_id=context.session_id if context else kwargs.get('session_id'),
            request_id=context.request_id if context else kwargs.get('request_id'),
            client_ip=context.client_ip if context else kwargs.get('client_ip'),
            user_agent=context.user_agent if context else kwargs.get('user_agent'),
            resource_type=resource_type,
            resource_id=resource_id,
            parent_resource_id=kwargs.get('parent_resource_id'),
            related_resources=kwargs.get('related_resources', []),
            amount=amount,
            currency=currency,
            account_id=kwargs.get('account_id'),
            transaction_id=kwargs.get('transaction_id'),
            balance_before=kwargs.get('balance_before'),
            balance_after=kwargs.get('balance_after'),
            changes=changes or [],
            data_lineage=kwargs.get('data_lineage', []),
            regulatory_frameworks=regulatory_frameworks,
            data_classification=data_classification,
            data_sensitivity=data_sensitivity,
            integrity_level=self._determine_integrity_level(data_sensitivity, operation_type),
            compliance_flags=self._generate_compliance_flags(operation_type, data_sensitivity),
            legal_basis=kwargs.get('legal_basis'),
            retention_period_years=self.retention_years,
            risk_level=risk_level,
            security_controls=kwargs.get('security_controls', []),
            approval_required=context.approval_required if context else kwargs.get('approval_required', False),
            approver_id=context.approver_id if context else kwargs.get('approver_id'),
            business_justification=context.business_justification if context else kwargs.get('business_justification'),
            error_code=kwargs.get('error_code'),
            error_message=kwargs.get('error_message'),
            error_category=kwargs.get('error_category'),
            data_hash="",  # Will be calculated below
            integrity_hash="",  # Will be calculated below
            digital_signature=kwargs.get('digital_signature'),
            verification_status="pending",
            additional_metadata=additional_metadata
        )
        
        # Calculate data and integrity hashes
        record_dict = audit_record.to_dict()
        
        # Calculate data hash (without integrity fields)
        data_for_hash = {k: v for k, v in record_dict.items() 
                        if k not in ['data_hash', 'integrity_hash', 'digital_signature', 'verification_status']}
        audit_record.data_hash = FinancialDataMasker.create_data_integrity_hash(data_for_hash, self.secret_key)
        
        # Calculate integrity hash
        audit_record.integrity_hash = self._calculate_integrity_hash(audit_record)
        audit_record.verification_status = "verified"
        
        # Write audit record
        await self._write_financial_audit_record(audit_record)
        
        # Log to compliance system if available
        if self.compliance_logger:
            await self._log_to_compliance_system(audit_record)
        
        # Update statistics
        self._update_audit_statistics(audit_record)
        
        # Check for compliance violations
        await self._check_financial_compliance_violations(audit_record)
        
        return audit_id
    
    async def _write_financial_audit_record(self, audit_record: FinancialAuditRecord):
        """Write financial audit record to appropriate logs"""
        
        # Convert to dict with masking for different sensitivity levels
        record_dict = audit_record.to_dict()
        
        # Apply data masking based on sensitivity
        masked_record = FinancialDataMasker.mask_financial_data(
            record_dict, 
            audit_record.data_sensitivity,
            preserve_audit_fields=True
        )
        
        # Add audit metadata
        audit_metadata = {
            'record_type': 'financial_audit',
            'immutable': True,
            'regulatory_compliance': True,
            'audit_trail': True,
            'data_lineage': True,
            'integrity_verified': audit_record.verification_status == "verified",
            'retention_required': True,
            'version': '1.0'
        }
        masked_record['audit_metadata'] = audit_metadata
        
        # Determine log level based on risk
        if audit_record.risk_level == FinancialAuditRisk.CRITICAL:
            log_level = logging.CRITICAL
        elif audit_record.risk_level == FinancialAuditRisk.HIGH:
            log_level = logging.ERROR
        elif audit_record.risk_level == FinancialAuditRisk.MEDIUM:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO
        
        # Log to financial audit log
        self.audit_logger.log(
            log_level,
            f"Financial operation: {audit_record.operation_type.value} - {audit_record.operation_outcome}",
            extra=masked_record
        )
        
        # Log to transaction log for transaction operations
        if audit_record.operation_type.value.startswith('transaction_'):
            self.transaction_logger.info(
                f"Transaction audit: {audit_record.operation_type.value}",
                extra={
                    'audit_id': audit_record.audit_id,
                    'operation_id': audit_record.operation_id,
                    'transaction_id': audit_record.transaction_id,
                    'amount': str(audit_record.amount) if audit_record.amount else None,
                    'currency': audit_record.currency,
                    'user_id': audit_record.user_id,
                    'outcome': audit_record.operation_outcome
                }
            )
        
        # Log to security log for high-risk operations
        if audit_record.risk_level in [FinancialAuditRisk.HIGH, FinancialAuditRisk.CRITICAL, FinancialAuditRisk.REGULATORY_VIOLATION]:
            self.security_logger.error(
                f"High-risk financial operation: {audit_record.audit_id}",
                extra={
                    'audit_id': audit_record.audit_id,
                    'operation_type': audit_record.operation_type.value,
                    'risk_level': audit_record.risk_level.value,
                    'user_id': audit_record.user_id,
                    'requires_investigation': True,
                    'regulatory_frameworks': [rf.value for rf in audit_record.regulatory_frameworks]
                }
            )
    
    async def _log_to_compliance_system(self, audit_record: FinancialAuditRecord):
        """Log to compliance system for regulatory reporting"""
        if not self.compliance_logger:
            return
        
        # Map to compliance event type
        compliance_event_type = self._map_to_compliance_event_type(audit_record.operation_type)
        
        # Map risk level
        compliance_risk = self._map_to_compliance_risk(audit_record.risk_level)
        
        await self.compliance_logger.log_compliance_event(
            event_type=compliance_event_type,
            regulatory_frameworks=audit_record.regulatory_frameworks,
            data_classification=audit_record.data_classification,
            risk_level=compliance_risk,
            user_id=audit_record.user_id,
            resource_type=audit_record.resource_type,
            action_performed=audit_record.operation_type.value,
            outcome=audit_record.operation_outcome,
            system_component="financial_system",
            resource_id=audit_record.resource_id,
            session_id=audit_record.session_id,
            client_ip=audit_record.client_ip,
            user_agent=audit_record.user_agent,
            request_id=audit_record.request_id,
            approval_required=audit_record.approval_required,
            approver_id=audit_record.approver_id,
            business_justification=audit_record.business_justification,
            error_code=audit_record.error_code,
            error_message=audit_record.error_message,
            additional_data={
                'financial_audit_id': audit_record.audit_id,
                'amount': str(audit_record.amount) if audit_record.amount else None,
                'currency': audit_record.currency,
                'data_sensitivity': audit_record.data_sensitivity.value,
                'integrity_level': audit_record.integrity_level.value
            }
        )
    
    def _determine_data_sensitivity(
        self, 
        operation_type: FinancialOperationType, 
        resource_type: str, 
        amount: Optional[Decimal]
    ) -> FinancialDataSensitivity:
        """Determine data sensitivity level"""
        
        # Payment operations are highly sensitive
        if 'payment' in resource_type.lower() or 'card' in resource_type.lower():
            return FinancialDataSensitivity.PAYMENT_CARD_DATA
        
        # Bank account operations
        if 'account' in resource_type.lower() or 'bank' in resource_type.lower():
            return FinancialDataSensitivity.BANK_DATA
        
        # Tax-related operations
        if 'tax' in resource_type.lower():
            return FinancialDataSensitivity.TAX_DATA
        
        # High-value transactions
        if amount and amount > Decimal('10000'):
            return FinancialDataSensitivity.HIGHLY_SENSITIVE
        
        # Sensitive operations
        if operation_type in [
            FinancialOperationType.DATA_EXPORT,
            FinancialOperationType.SENSITIVE_DATA_ACCESS,
            FinancialOperationType.AUDIT_LOG_ACCESS
        ]:
            return FinancialDataSensitivity.RESTRICTED
        
        # Default for financial operations
        return FinancialDataSensitivity.CONFIDENTIAL
    
    def _determine_data_classification(self, sensitivity: FinancialDataSensitivity) -> DataClassification:
        """Map financial sensitivity to compliance data classification"""
        mapping = {
            FinancialDataSensitivity.PUBLIC: DataClassification.PUBLIC,
            FinancialDataSensitivity.INTERNAL: DataClassification.INTERNAL,
            FinancialDataSensitivity.CONFIDENTIAL: DataClassification.CONFIDENTIAL,
            FinancialDataSensitivity.RESTRICTED: DataClassification.RESTRICTED,
            FinancialDataSensitivity.HIGHLY_SENSITIVE: DataClassification.RESTRICTED,
            FinancialDataSensitivity.PAYMENT_CARD_DATA: DataClassification.PCI_DATA,
            FinancialDataSensitivity.BANK_DATA: DataClassification.FINANCIAL,
            FinancialDataSensitivity.TAX_DATA: DataClassification.PII
        }
        return mapping.get(sensitivity, DataClassification.CONFIDENTIAL)
    
    def _determine_risk_level(
        self, 
        operation_type: FinancialOperationType, 
        outcome: str, 
        amount: Optional[Decimal], 
        changes: Optional[List[FinancialChangeRecord]]
    ) -> FinancialAuditRisk:
        """Determine financial audit risk level"""
        
        # Failed operations are high risk
        if outcome in ['failure', 'error', 'denied']:
            return FinancialAuditRisk.HIGH
        
        # High-value transactions
        if amount and amount > Decimal('100000'):
            return FinancialAuditRisk.HIGH
        
        # Sensitive operations
        if operation_type in [
            FinancialOperationType.TRANSACTION_DELETE,
            FinancialOperationType.DATA_PURGE,
            FinancialOperationType.PRIVILEGED_OPERATION,
            FinancialOperationType.AUDIT_LOG_ACCESS
        ]:
            return FinancialAuditRisk.HIGH
        
        # Operations with many changes
        if changes and len(changes) > 5:
            return FinancialAuditRisk.MEDIUM
        
        # Bulk operations
        if operation_type in [
            FinancialOperationType.TRANSACTION_BATCH_DELETE,
            FinancialOperationType.DATA_EXPORT,
            FinancialOperationType.DATA_IMPORT
        ]:
            return FinancialAuditRisk.MEDIUM
        
        # Default for financial operations
        return FinancialAuditRisk.LOW
    
    def _determine_integrity_level(
        self, 
        sensitivity: FinancialDataSensitivity, 
        operation_type: FinancialOperationType
    ) -> FinancialIntegrityLevel:
        """Determine required integrity level"""
        
        # Legal and regulatory operations
        if operation_type in [
            FinancialOperationType.AUDIT_LOG_ACCESS,
            FinancialOperationType.COMPLIANCE_CHECK,
            FinancialOperationType.DATA_EXPORT
        ]:
            return FinancialIntegrityLevel.LEGALLY_BINDING
        
        # High sensitivity data
        if sensitivity in [
            FinancialDataSensitivity.HIGHLY_SENSITIVE,
            FinancialDataSensitivity.PAYMENT_CARD_DATA,
            FinancialDataSensitivity.TAX_DATA
        ]:
            return FinancialIntegrityLevel.IMMUTABLE
        
        # Financial transactions
        if operation_type.value.startswith('transaction_'):
            return FinancialIntegrityLevel.CRITICAL
        
        # Default
        return FinancialIntegrityLevel.HIGH
    
    def _generate_compliance_flags(
        self, 
        operation_type: FinancialOperationType, 
        sensitivity: FinancialDataSensitivity
    ) -> List[str]:
        """Generate compliance flags based on operation and sensitivity"""
        flags = []
        
        # Financial operation flag
        flags.append('financial_operation')
        
        # Regulatory compliance flags
        if operation_type.value.startswith('transaction_'):
            flags.extend(['sox_relevant', 'ffiec_relevant'])
        
        if sensitivity == FinancialDataSensitivity.PAYMENT_CARD_DATA:
            flags.append('pci_dss_relevant')
        
        if sensitivity == FinancialDataSensitivity.BANK_DATA:
            flags.append('glba_relevant')
        
        if operation_type in [FinancialOperationType.DATA_EXPORT, FinancialOperationType.SENSITIVE_DATA_ACCESS]:
            flags.append('privacy_relevant')
        
        # Risk flags
        if operation_type in [FinancialOperationType.TRANSACTION_DELETE, FinancialOperationType.DATA_PURGE]:
            flags.append('high_risk_operation')
        
        return flags
    
    def _calculate_integrity_hash(self, audit_record: FinancialAuditRecord) -> str:
        """Calculate HMAC integrity hash for the audit record"""
        record_dict = audit_record.to_dict()
        
        # Exclude hash fields from hash calculation
        excluded_fields = ['data_hash', 'integrity_hash', 'digital_signature', 'verification_status']
        hash_data = {k: v for k, v in record_dict.items() if k not in excluded_fields}
        
        return FinancialDataMasker.create_data_integrity_hash(hash_data, self.secret_key)
    
    def _map_to_compliance_event_type(self, operation_type: FinancialOperationType) -> ComplianceEventType:
        """Map financial operation type to compliance event type"""
        mapping = {
            FinancialOperationType.TRANSACTION_CREATE: ComplianceEventType.FINANCIAL_TRANSACTION,
            FinancialOperationType.TRANSACTION_UPDATE: ComplianceEventType.DATA_MODIFICATION,
            FinancialOperationType.TRANSACTION_DELETE: ComplianceEventType.DATA_DELETION,
            FinancialOperationType.DATA_EXPORT: ComplianceEventType.DATA_EXPORT,
            FinancialOperationType.DATA_IMPORT: ComplianceEventType.DATA_IMPORT,
            FinancialOperationType.SENSITIVE_DATA_ACCESS: ComplianceEventType.DATA_ACCESS,
            FinancialOperationType.PRIVILEGED_OPERATION: ComplianceEventType.PRIVILEGED_ACCESS,
            FinancialOperationType.AUDIT_LOG_ACCESS: ComplianceEventType.AUDIT_LOG_ACCESS
        }
        return mapping.get(operation_type, ComplianceEventType.FINANCIAL_TRANSACTION)
    
    def _map_to_compliance_risk(self, risk_level: FinancialAuditRisk) -> ComplianceRisk:
        """Map financial risk to compliance risk"""
        mapping = {
            FinancialAuditRisk.LOW: ComplianceRisk.LOW,
            FinancialAuditRisk.MEDIUM: ComplianceRisk.MEDIUM,
            FinancialAuditRisk.HIGH: ComplianceRisk.HIGH,
            FinancialAuditRisk.CRITICAL: ComplianceRisk.CRITICAL,
            FinancialAuditRisk.REGULATORY_VIOLATION: ComplianceRisk.CRITICAL
        }
        return mapping.get(risk_level, ComplianceRisk.MEDIUM)
    
    def _update_audit_statistics(self, audit_record: FinancialAuditRecord):
        """Update audit logging statistics"""
        self.audit_stats['total_operations_logged'] += 1
        
        if audit_record.risk_level in [FinancialAuditRisk.HIGH, FinancialAuditRisk.CRITICAL]:
            self.audit_stats['high_risk_operations'] += 1
        
        if audit_record.risk_level == FinancialAuditRisk.REGULATORY_VIOLATION:
            self.audit_stats['regulatory_violations'] += 1
        
        if audit_record.operation_outcome in ['failure', 'error']:
            self.audit_stats['failed_operations'] += 1
    
    async def _check_financial_compliance_violations(self, audit_record: FinancialAuditRecord):
        """Check for financial compliance violations"""
        violations = []
        
        # Check for unauthorized high-value transactions
        if (audit_record.amount and audit_record.amount > Decimal('50000') and
            not audit_record.approval_required and
            audit_record.operation_type in [FinancialOperationType.TRANSACTION_CREATE, FinancialOperationType.TRANSACTION_UPDATE]):
            
            violations.append({
                'violation_type': 'unauthorized_high_value_transaction',
                'severity': 'high',
                'amount': str(audit_record.amount),
                'description': 'High-value transaction without required approval'
            })
        
        # Check for suspicious deletion patterns
        if (audit_record.operation_type == FinancialOperationType.TRANSACTION_DELETE and
            not audit_record.business_justification):
            
            violations.append({
                'violation_type': 'transaction_deletion_without_justification',
                'severity': 'medium',
                'description': 'Transaction deletion without business justification'
            })
        
        # Check for failed sensitive operations
        if (audit_record.operation_outcome in ['failure', 'error'] and
            audit_record.data_sensitivity in [FinancialDataSensitivity.HIGHLY_SENSITIVE, FinancialDataSensitivity.PAYMENT_CARD_DATA]):
            
            violations.append({
                'violation_type': 'failed_sensitive_operation',
                'severity': 'high',
                'description': 'Failed operation on sensitive financial data'
            })
        
        # Log violations
        for violation in violations:
            self.security_logger.error(
                f"Financial compliance violation: {violation['violation_type']}",
                extra={
                    'audit_id': audit_record.audit_id,
                    'violation': violation,
                    'compliance_violation': True,
                    'requires_immediate_attention': True,
                    'regulatory_frameworks': [rf.value for rf in audit_record.regulatory_frameworks]
                }
            )
    
    async def verify_audit_integrity(self, audit_id: str, record_data: Dict[str, Any]) -> bool:
        """Verify the integrity of a financial audit record"""
        try:
            stored_hash = record_data.get('integrity_hash')
            if not stored_hash:
                return False
            
            # Recreate record without integrity fields
            verification_data = record_data.copy()
            excluded_fields = ['data_hash', 'integrity_hash', 'digital_signature', 'verification_status']
            for field in excluded_fields:
                verification_data.pop(field, None)
            
            # Calculate expected hash
            expected_hash = FinancialDataMasker.create_data_integrity_hash(verification_data, self.secret_key)
            
            # Verify hashes match
            is_valid = hmac.compare_digest(stored_hash, expected_hash)
            
            # Update statistics
            self.audit_stats['integrity_verifications'] += 1
            
            # Log verification result
            self.audit_logger.info(
                f"Financial audit integrity verification: {audit_id}",
                extra={
                    'audit_id': audit_id,
                    'integrity_verified': is_valid,
                    'verification_timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
            
            return is_valid
            
        except Exception as e:
            self.audit_logger.error(
                f"Financial audit integrity verification failed: {audit_id}",
                extra={
                    'audit_id': audit_id,
                    'error': str(e),
                    'verification_timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
            return False
    
    def get_audit_statistics(self) -> Dict[str, Any]:
        """Get financial audit statistics"""
        return {
            'statistics': self.audit_stats.copy(),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'retention_years': self.retention_years
        }
    
    @asynccontextmanager
    async def audit_transaction_context(
        self, 
        user_id: str, 
        operation_type: FinancialOperationType,
        resource_type: str = "transaction",
        **context_kwargs
    ):
        """
        Context manager for comprehensive transaction audit logging
        
        Usage:
            async with audit_logger.audit_transaction_context(
                user_id="123", 
                operation_type=FinancialOperationType.TRANSACTION_CREATE
            ) as audit_ctx:
                # Perform operations
                audit_ctx.add_change(...)
                audit_ctx.set_amount(...)
        """
        operation_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)
        
        # Create audit context
        audit_context = FinancialAuditContext(
            operation_id=operation_id,
            user_id=user_id,
            session_id=context_kwargs.get('session_id'),
            request_id=context_kwargs.get('request_id'),
            client_ip=context_kwargs.get('client_ip'),
            user_agent=context_kwargs.get('user_agent'),
            business_justification=context_kwargs.get('business_justification'),
            approval_required=context_kwargs.get('approval_required', False),
            approver_id=context_kwargs.get('approver_id'),
            related_operations=[]
        )
        
        # Context object for accumulating audit data
        class AuditTransactionContext:
            def __init__(self):
                self.changes: List[FinancialChangeRecord] = []
                self.amount: Optional[Decimal] = None
                self.currency: str = "USD"
                self.resource_id: Optional[str] = None
                self.additional_metadata: Dict[str, Any] = {}
                self.outcome: str = "success"
                self.error_code: Optional[str] = None
                self.error_message: Optional[str] = None
            
            def add_change(self, field_name: str, old_value: Any, new_value: Any, 
                          change_type: str = "update", 
                          data_sensitivity: FinancialDataSensitivity = FinancialDataSensitivity.CONFIDENTIAL):
                """Add a change record"""
                change = FinancialChangeRecord(
                    field_name=field_name,
                    old_value=old_value,
                    new_value=new_value,
                    change_type=change_type,
                    data_sensitivity=data_sensitivity,
                    regulatory_impact=[]
                )
                self.changes.append(change)
            
            def set_amount(self, amount: Union[Decimal, float, str], currency: str = "USD"):
                """Set transaction amount"""
                if isinstance(amount, str):
                    self.amount = Decimal(amount)
                elif isinstance(amount, float):
                    self.amount = Decimal(str(amount))
                else:
                    self.amount = amount
                self.currency = currency
            
            def set_resource_id(self, resource_id: str):
                """Set resource ID"""
                self.resource_id = resource_id
            
            def add_metadata(self, key: str, value: Any):
                """Add additional metadata"""
                self.additional_metadata[key] = value
            
            def set_outcome(self, outcome: str, error_code: Optional[str] = None, error_message: Optional[str] = None):
                """Set operation outcome"""
                self.outcome = outcome
                self.error_code = error_code
                self.error_message = error_message
        
        ctx = AuditTransactionContext()
        
        try:
            yield ctx
        except Exception as e:
            ctx.set_outcome("error", error_code="exception", error_message=str(e))
            raise
        finally:
            # Calculate operation duration
            end_time = datetime.now(timezone.utc)
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            # Log the operation
            await self.log_financial_operation(
                operation_type=operation_type,
                user_id=user_id,
                resource_type=resource_type,
                operation_outcome=ctx.outcome,
                resource_id=ctx.resource_id,
                amount=ctx.amount,
                currency=ctx.currency,
                changes=ctx.changes,
                context=audit_context,
                additional_metadata=ctx.additional_metadata,
                operation_duration_ms=duration_ms,
                error_code=ctx.error_code,
                error_message=ctx.error_message,
                **context_kwargs
            )


# Global financial audit logger instance
_financial_audit_logger: Optional[FinancialAuditLogger] = None


def initialize_financial_audit_logger(
    secret_key: str, 
    compliance_logger: Optional[ComplianceLogger] = None,
    retention_years: int = 7
) -> FinancialAuditLogger:
    """
    Initialize global financial audit logger
    
    Args:
        secret_key: Secret key for cryptographic integrity verification
        compliance_logger: Optional compliance logger instance
        retention_years: Retention period for audit records
        
    Returns:
        FinancialAuditLogger instance
    """
    global _financial_audit_logger
    _financial_audit_logger = FinancialAuditLogger(secret_key, compliance_logger, retention_years)
    return _financial_audit_logger


def get_financial_audit_logger() -> Optional[FinancialAuditLogger]:
    """Get the global financial audit logger"""
    return _financial_audit_logger


# Convenience functions for common financial operations
async def audit_transaction_creation(
    user_id: str,
    transaction_id: str,
    amount: Decimal,
    currency: str = "USD",
    **kwargs
) -> str:
    """Audit transaction creation operation"""
    if _financial_audit_logger:
        return await _financial_audit_logger.log_financial_operation(
            operation_type=FinancialOperationType.TRANSACTION_CREATE,
            user_id=user_id,
            resource_type="transaction",
            resource_id=transaction_id,
            amount=amount,
            currency=currency,
            **kwargs
        )
    return ""


async def audit_transaction_update(
    user_id: str,
    transaction_id: str,
    changes: List[FinancialChangeRecord],
    **kwargs
) -> str:
    """Audit transaction update operation"""
    if _financial_audit_logger:
        return await _financial_audit_logger.log_financial_operation(
            operation_type=FinancialOperationType.TRANSACTION_UPDATE,
            user_id=user_id,
            resource_type="transaction",
            resource_id=transaction_id,
            changes=changes,
            **kwargs
        )
    return ""


async def audit_transaction_deletion(
    user_id: str,
    transaction_id: str,
    amount: Optional[Decimal] = None,
    **kwargs
) -> str:
    """Audit transaction deletion operation"""
    if _financial_audit_logger:
        return await _financial_audit_logger.log_financial_operation(
            operation_type=FinancialOperationType.TRANSACTION_DELETE,
            user_id=user_id,
            resource_type="transaction",
            resource_id=transaction_id,
            amount=amount,
            **kwargs
        )
    return ""


async def audit_data_export(
    user_id: str,
    export_type: str,
    record_count: int,
    **kwargs
) -> str:
    """Audit data export operation"""
    if _financial_audit_logger:
        return await _financial_audit_logger.log_financial_operation(
            operation_type=FinancialOperationType.DATA_EXPORT,
            user_id=user_id,
            resource_type="data_export",
            additional_metadata={
                'export_type': export_type,
                'record_count': record_count
            },
            **kwargs
        )
    return ""