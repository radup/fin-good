"""
Compliance Logging Module for FinGood Financial Application

This module provides specialized logging for financial regulatory compliance
including PCI DSS, SOX, GDPR, CCPA, and other financial industry standards.
Ensures proper audit trails, data retention, and regulatory reporting.
"""

import json
import logging
import hashlib
import hmac
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from dataclasses import dataclass, asdict
from uuid import uuid4
import asyncio

from app.core.logging_config import get_logger, LogCategory


class RegulatoryFramework(Enum):
    """Supported regulatory frameworks"""
    PCI_DSS = "PCI_DSS"
    SOX = "SOX"
    GDPR = "GDPR"
    CCPA = "CCPA"
    FFIEC = "FFIEC"
    GLBA = "GLBA"
    BSA_AML = "BSA_AML"
    COSO = "COSO"
    ISO_27001 = "ISO_27001"
    NIST = "NIST"


class ComplianceEventType(Enum):
    """Types of compliance events"""
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_DELETION = "data_deletion"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    PRIVILEGED_ACCESS = "privileged_access"
    AUTHENTICATION_EVENT = "authentication_event"
    AUTHORIZATION_EVENT = "authorization_event"
    FINANCIAL_TRANSACTION = "financial_transaction"
    SYSTEM_CONFIGURATION = "system_configuration"
    SECURITY_INCIDENT = "security_incident"
    PRIVACY_EVENT = "privacy_event"
    CONSENT_MANAGEMENT = "consent_management"
    DATA_BREACH = "data_breach"
    AUDIT_LOG_ACCESS = "audit_log_access"
    BACKUP_RESTORE = "backup_restore"
    ENCRYPTION_EVENT = "encryption_event"
    KEY_MANAGEMENT = "key_management"


class DataClassification(Enum):
    """Data classification levels for compliance"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    PCI_DATA = "pci_data"
    PII = "pii"
    PHI = "phi"
    FINANCIAL = "financial"


class ComplianceRisk(Enum):
    """Compliance risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ComplianceEvent:
    """Comprehensive compliance event record"""
    event_id: str
    timestamp: str
    event_type: ComplianceEventType
    regulatory_frameworks: List[RegulatoryFramework]
    data_classification: DataClassification
    risk_level: ComplianceRisk
    
    # Actor information
    user_id: Optional[str]
    user_role: Optional[str]
    session_id: Optional[str]
    client_ip: Optional[str]
    user_agent: Optional[str]
    
    # Event details
    resource_type: str
    resource_id: Optional[str]
    action_performed: str
    outcome: str
    
    # Data handling
    data_subject_id: Optional[str]  # For GDPR compliance
    data_types_accessed: List[str]
    data_retention_period: Optional[int]  # In years
    legal_basis: Optional[str]  # For GDPR
    
    # Technical details
    system_component: str
    method: Optional[str]
    endpoint: Optional[str]
    request_id: Optional[str]
    
    # Compliance metadata
    controls_applied: List[str]
    approval_required: bool
    approver_id: Optional[str]
    business_justification: Optional[str]
    
    # Error and exception handling
    error_code: Optional[str]
    error_message: Optional[str]
    
    # Additional context
    additional_data: Optional[Dict[str, Any]]
    
    # Integrity and verification
    integrity_hash: Optional[str]
    digital_signature: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        
        # Convert enums to strings
        data['event_type'] = self.event_type.value
        data['regulatory_frameworks'] = [rf.value for rf in self.regulatory_frameworks]
        data['data_classification'] = self.data_classification.value
        data['risk_level'] = self.risk_level.value
        
        return data


class ComplianceLogger:
    """
    Comprehensive compliance logger for financial regulatory requirements.
    Provides audit trails, data lineage, and regulatory reporting capabilities.
    """
    
    # Retention periods by regulation (in years)
    RETENTION_PERIODS = {
        RegulatoryFramework.PCI_DSS: 1,
        RegulatoryFramework.SOX: 7,
        RegulatoryFramework.GDPR: 6,  # Generally, but varies by purpose
        RegulatoryFramework.CCPA: 2,
        RegulatoryFramework.FFIEC: 5,
        RegulatoryFramework.GLBA: 5,
        RegulatoryFramework.BSA_AML: 5,
        RegulatoryFramework.ISO_27001: 3
    }
    
    # Required controls by regulation
    REQUIRED_CONTROLS = {
        RegulatoryFramework.PCI_DSS: [
            'access_control', 'encryption', 'network_security', 
            'vulnerability_management', 'monitoring'
        ],
        RegulatoryFramework.SOX: [
            'access_control', 'change_management', 'data_integrity',
            'audit_trail', 'segregation_of_duties'
        ],
        RegulatoryFramework.GDPR: [
            'consent_management', 'data_minimization', 'encryption',
            'access_control', 'data_portability', 'right_to_erasure'
        ],
        RegulatoryFramework.CCPA: [
            'privacy_notice', 'opt_out', 'data_deletion',
            'data_disclosure', 'non_discrimination'
        ]
    }
    
    def __init__(self, secret_key: str, enable_digital_signatures: bool = False):
        """
        Initialize compliance logger
        
        Args:
            secret_key: Secret key for integrity verification
            enable_digital_signatures: Whether to enable digital signatures
        """
        self.secret_key = secret_key
        self.enable_digital_signatures = enable_digital_signatures
        
        # Initialize loggers
        self.compliance_logger = get_logger('fingood.compliance', LogCategory.COMPLIANCE)
        self.audit_logger = get_logger('fingood.audit', LogCategory.AUDIT)
        
        # Statistics tracking
        self.stats = {
            'events_logged': 0,
            'high_risk_events': 0,
            'gdpr_events': 0,
            'pci_events': 0,
            'sox_events': 0,
            'integrity_verifications': 0
        }
    
    async def log_compliance_event(
        self,
        event_type: ComplianceEventType,
        regulatory_frameworks: List[RegulatoryFramework],
        data_classification: DataClassification,
        risk_level: ComplianceRisk,
        user_id: Optional[str],
        resource_type: str,
        action_performed: str,
        outcome: str,
        system_component: str,
        
        # Optional parameters
        user_role: Optional[str] = None,
        session_id: Optional[str] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_id: Optional[str] = None,
        data_subject_id: Optional[str] = None,
        data_types_accessed: Optional[List[str]] = None,
        legal_basis: Optional[str] = None,
        method: Optional[str] = None,
        endpoint: Optional[str] = None,
        request_id: Optional[str] = None,
        controls_applied: Optional[List[str]] = None,
        approval_required: bool = False,
        approver_id: Optional[str] = None,
        business_justification: Optional[str] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log a compliance event with full regulatory context
        
        Returns:
            Event ID for tracking and correlation
        """
        
        # Generate unique event ID
        event_id = str(uuid4())
        
        # Determine retention period based on regulations
        retention_period = self._calculate_retention_period(regulatory_frameworks)
        
        # Apply default controls if not specified
        if controls_applied is None:
            controls_applied = self._get_required_controls(regulatory_frameworks)
        
        # Create compliance event
        event = ComplianceEvent(
            event_id=event_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            regulatory_frameworks=regulatory_frameworks,
            data_classification=data_classification,
            risk_level=risk_level,
            user_id=user_id,
            user_role=user_role,
            session_id=session_id,
            client_ip=client_ip,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            action_performed=action_performed,
            outcome=outcome,
            data_subject_id=data_subject_id,
            data_types_accessed=data_types_accessed or [],
            data_retention_period=retention_period,
            legal_basis=legal_basis,
            system_component=system_component,
            method=method,
            endpoint=endpoint,
            request_id=request_id,
            controls_applied=controls_applied,
            approval_required=approval_required,
            approver_id=approver_id,
            business_justification=business_justification,
            error_code=error_code,
            error_message=error_message,
            additional_data=additional_data
        )
        
        # Calculate integrity hash
        event.integrity_hash = self._calculate_integrity_hash(event)
        
        # Add digital signature if enabled
        if self.enable_digital_signatures:
            event.digital_signature = self._create_digital_signature(event)
        
        # Log the event
        await self._write_compliance_event(event)
        
        # Update statistics
        self._update_statistics(event)
        
        # Check for critical compliance violations
        await self._check_compliance_violations(event)
        
        return event_id
    
    async def _write_compliance_event(self, event: ComplianceEvent):
        """Write compliance event to appropriate logs"""
        
        event_dict = event.to_dict()
        
        # Add compliance metadata
        compliance_metadata = {
            'record_type': 'compliance_event',
            'immutable': True,
            'retention_required': True,
            'audit_trail': True,
            'regulatory_reporting': True,
            'data_lineage': True,
            'version': '1.0'
        }
        event_dict['compliance_metadata'] = compliance_metadata
        
        # Determine log level based on risk
        if event.risk_level == ComplianceRisk.CRITICAL:
            log_level = logging.CRITICAL
        elif event.risk_level == ComplianceRisk.HIGH:
            log_level = logging.ERROR
        elif event.risk_level == ComplianceRisk.MEDIUM:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO
        
        # Log to compliance log
        self.compliance_logger.log(
            log_level,
            f"Compliance event: {event.event_type.value} - {event.outcome}",
            extra=event_dict
        )
        
        # Log to audit log for high-risk events
        if event.risk_level in [ComplianceRisk.HIGH, ComplianceRisk.CRITICAL]:
            self.audit_logger.error(
                f"High-risk compliance event: {event.event_id}",
                extra={
                    'event_id': event.event_id,
                    'event_type': event.event_type.value,
                    'risk_level': event.risk_level.value,
                    'regulatory_frameworks': [rf.value for rf in event.regulatory_frameworks],
                    'user_id': event.user_id,
                    'resource_type': event.resource_type,
                    'requires_investigation': True
                }
            )
    
    def _calculate_retention_period(self, frameworks: List[RegulatoryFramework]) -> int:
        """Calculate required retention period based on regulations"""
        if not frameworks:
            return 7  # Default 7 years for financial data
        
        # Return the maximum retention period required
        return max(
            self.RETENTION_PERIODS.get(framework, 7) 
            for framework in frameworks
        )
    
    def _get_required_controls(self, frameworks: List[RegulatoryFramework]) -> List[str]:
        """Get required controls for given regulatory frameworks"""
        controls = set()
        for framework in frameworks:
            controls.update(self.REQUIRED_CONTROLS.get(framework, []))
        return list(controls)
    
    def _calculate_integrity_hash(self, event: ComplianceEvent) -> str:
        """Calculate HMAC integrity hash for the event"""
        # Create a copy without the hash fields
        event_dict = event.to_dict()
        event_dict.pop('integrity_hash', None)
        event_dict.pop('digital_signature', None)
        
        # Sort for consistent hashing
        event_json = json.dumps(event_dict, sort_keys=True, separators=(',', ':'))
        
        return hmac.new(
            self.secret_key.encode(),
            event_json.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _create_digital_signature(self, event: ComplianceEvent) -> str:
        """Create digital signature for the event (placeholder implementation)"""
        # In a real implementation, this would use proper digital signatures
        # with certificates and PKI infrastructure
        event_hash = self._calculate_integrity_hash(event)
        return f"digital_signature_{event_hash[:16]}"
    
    def _update_statistics(self, event: ComplianceEvent):
        """Update compliance logging statistics"""
        self.stats['events_logged'] += 1
        
        if event.risk_level in [ComplianceRisk.HIGH, ComplianceRisk.CRITICAL]:
            self.stats['high_risk_events'] += 1
        
        for framework in event.regulatory_frameworks:
            if framework == RegulatoryFramework.GDPR:
                self.stats['gdpr_events'] += 1
            elif framework == RegulatoryFramework.PCI_DSS:
                self.stats['pci_events'] += 1
            elif framework == RegulatoryFramework.SOX:
                self.stats['sox_events'] += 1
    
    async def _check_compliance_violations(self, event: ComplianceEvent):
        """Check for compliance violations and trigger alerts"""
        violations = []
        
        # Check for unauthorized access to sensitive data
        if (event.data_classification in [DataClassification.PCI_DATA, DataClassification.PII] and
            event.outcome == 'failure' and
            event.event_type == ComplianceEventType.DATA_ACCESS):
            
            violations.append({
                'violation_type': 'unauthorized_sensitive_data_access',
                'severity': 'high',
                'frameworks_affected': [rf.value for rf in event.regulatory_frameworks],
                'description': 'Attempted unauthorized access to sensitive data'
            })
        
        # Check for data deletion without proper authorization
        if (event.event_type == ComplianceEventType.DATA_DELETION and
            not event.approval_required and
            event.data_classification != DataClassification.PUBLIC):
            
            violations.append({
                'violation_type': 'data_deletion_without_approval',
                'severity': 'medium',
                'frameworks_affected': ['GDPR', 'SOX'],
                'description': 'Data deletion performed without required approval'
            })
        
        # Check for missing legal basis for GDPR events
        if (RegulatoryFramework.GDPR in event.regulatory_frameworks and
            event.data_classification == DataClassification.PII and
            not event.legal_basis):
            
            violations.append({
                'violation_type': 'missing_gdpr_legal_basis',
                'severity': 'high',
                'frameworks_affected': ['GDPR'],
                'description': 'GDPR-regulated activity without specified legal basis'
            })
        
        # Log violations
        for violation in violations:
            self.compliance_logger.error(
                f"Compliance violation detected: {violation['violation_type']}",
                extra={
                    'event_id': event.event_id,
                    'violation': violation,
                    'compliance_violation': True,
                    'requires_immediate_attention': True
                }
            )
    
    async def verify_event_integrity(self, event_id: str, event_data: Dict[str, Any]) -> bool:
        """
        Verify the integrity of a compliance event
        
        Args:
            event_id: Event ID to verify
            event_data: Event data to verify
            
        Returns:
            True if integrity is verified, False otherwise
        """
        try:
            stored_hash = event_data.get('integrity_hash')
            if not stored_hash:
                return False
            
            # Recreate event without integrity fields
            verification_data = event_data.copy()
            verification_data.pop('integrity_hash', None)
            verification_data.pop('digital_signature', None)
            
            # Calculate expected hash
            event_json = json.dumps(verification_data, sort_keys=True, separators=(',', ':'))
            expected_hash = hmac.new(
                self.secret_key.encode(),
                event_json.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Verify hashes match
            is_valid = hmac.compare_digest(stored_hash, expected_hash)
            
            # Update statistics
            self.stats['integrity_verifications'] += 1
            
            # Log verification result
            self.audit_logger.info(
                f"Compliance event integrity verification: {event_id}",
                extra={
                    'event_id': event_id,
                    'integrity_verified': is_valid,
                    'verification_timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
            
            return is_valid
            
        except Exception as e:
            self.audit_logger.error(
                f"Compliance event integrity verification failed: {event_id}",
                extra={
                    'event_id': event_id,
                    'error': str(e),
                    'verification_timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
            return False
    
    def get_compliance_statistics(self) -> Dict[str, Any]:
        """Get compliance logging statistics"""
        return {
            'statistics': self.stats.copy(),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'retention_periods': {rf.name: period for rf, period in self.RETENTION_PERIODS.items()},
            'supported_frameworks': [rf.value for rf in RegulatoryFramework]
        }
    
    async def generate_compliance_report(
        self,
        framework: RegulatoryFramework,
        start_date: datetime,
        end_date: datetime,
        include_statistics: bool = True
    ) -> Dict[str, Any]:
        """
        Generate compliance report for specific regulatory framework
        
        Args:
            framework: Regulatory framework to report on
            start_date: Report start date
            end_date: Report end date
            include_statistics: Whether to include statistical analysis
            
        Returns:
            Compliance report data
        """
        report = {
            'report_id': str(uuid4()),
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'framework': framework.value,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'retention_period_years': self.RETENTION_PERIODS.get(framework, 7),
            'required_controls': self.REQUIRED_CONTROLS.get(framework, [])
        }
        
        if include_statistics:
            # In a real implementation, this would query the actual log data
            report['statistics'] = {
                'total_events': 'query_from_logs',
                'high_risk_events': 'query_from_logs',
                'violations_detected': 'query_from_logs',
                'compliance_score': 'calculate_based_on_events'
            }
        
        # Log report generation
        self.compliance_logger.info(
            f"Compliance report generated for {framework.value}",
            extra={
                'report_id': report['report_id'],
                'framework': framework.value,
                'period_start': start_date.isoformat(),
                'period_end': end_date.isoformat(),
                'report_type': 'regulatory_compliance'
            }
        )
        
        return report


# Global compliance logger instance
_compliance_logger: Optional[ComplianceLogger] = None


def initialize_compliance_logger(secret_key: str, enable_digital_signatures: bool = False) -> ComplianceLogger:
    """
    Initialize global compliance logger
    
    Args:
        secret_key: Secret key for integrity verification
        enable_digital_signatures: Whether to enable digital signatures
        
    Returns:
        ComplianceLogger instance
    """
    global _compliance_logger
    _compliance_logger = ComplianceLogger(secret_key, enable_digital_signatures)
    return _compliance_logger


def get_compliance_logger() -> Optional[ComplianceLogger]:
    """Get the global compliance logger"""
    return _compliance_logger


# Convenience functions for common compliance events
async def log_pci_data_access(
    user_id: str,
    resource_id: str,
    outcome: str,
    **kwargs
) -> str:
    """Log PCI DSS data access event"""
    if _compliance_logger:
        return await _compliance_logger.log_compliance_event(
            event_type=ComplianceEventType.DATA_ACCESS,
            regulatory_frameworks=[RegulatoryFramework.PCI_DSS],
            data_classification=DataClassification.PCI_DATA,
            risk_level=ComplianceRisk.HIGH,
            user_id=user_id,
            resource_type="payment_data",
            resource_id=resource_id,
            action_performed="access_cardholder_data",
            outcome=outcome,
            system_component="payment_processing",
            **kwargs
        )
    return ""


async def log_gdpr_data_processing(
    user_id: str,
    data_subject_id: str,
    data_types: List[str],
    legal_basis: str,
    outcome: str,
    **kwargs
) -> str:
    """Log GDPR data processing event"""
    if _compliance_logger:
        return await _compliance_logger.log_compliance_event(
            event_type=ComplianceEventType.DATA_ACCESS,
            regulatory_frameworks=[RegulatoryFramework.GDPR],
            data_classification=DataClassification.PII,
            risk_level=ComplianceRisk.MEDIUM,
            user_id=user_id,
            resource_type="personal_data",
            action_performed="process_personal_data",
            outcome=outcome,
            system_component="data_processing",
            data_subject_id=data_subject_id,
            data_types_accessed=data_types,
            legal_basis=legal_basis,
            **kwargs
        )
    return ""


async def log_sox_financial_data_change(
    user_id: str,
    resource_id: str,
    approver_id: str,
    outcome: str,
    **kwargs
) -> str:
    """Log SOX financial data change event"""
    if _compliance_logger:
        return await _compliance_logger.log_compliance_event(
            event_type=ComplianceEventType.DATA_MODIFICATION,
            regulatory_frameworks=[RegulatoryFramework.SOX],
            data_classification=DataClassification.FINANCIAL,
            risk_level=ComplianceRisk.HIGH,
            user_id=user_id,
            resource_type="financial_record",
            resource_id=resource_id,
            action_performed="modify_financial_data",
            outcome=outcome,
            system_component="financial_system",
            approval_required=True,
            approver_id=approver_id,
            **kwargs
        )
    return ""