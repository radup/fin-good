"""
Financial Compliance Monitor for FinGood Application

This module provides real-time compliance monitoring, regulatory flag management,
and data integrity verification for financial operations. It implements
comprehensive compliance checks for SOX, PCI DSS, FFIEC, GLBA, and other
financial regulations.
"""

import json
import logging
import hashlib
import hmac
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, List, Union, Set, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
import asyncio
from collections import defaultdict
import re

from app.core.financial_audit_logger import (
    FinancialOperationType, 
    FinancialAuditRisk,
    FinancialDataSensitivity,
    get_financial_audit_logger
)
from app.core.compliance_logger import (
    RegulatoryFramework,
    ComplianceRisk,
    get_compliance_logger
)


class ComplianceViolationType(Enum):
    """Types of compliance violations"""
    
    # SOX Violations
    SOX_UNAUTHORIZED_CHANGE = "sox_unauthorized_change"
    SOX_MISSING_APPROVAL = "sox_missing_approval"
    SOX_INADEQUATE_CONTROLS = "sox_inadequate_controls"
    SOX_SEGREGATION_VIOLATION = "sox_segregation_violation"
    
    # PCI DSS Violations
    PCI_UNAUTHORIZED_ACCESS = "pci_unauthorized_access"
    PCI_DATA_EXPOSURE = "pci_data_exposure"
    PCI_WEAK_ENCRYPTION = "pci_weak_encryption"
    PCI_AUDIT_LOG_FAILURE = "pci_audit_log_failure"
    
    # FFIEC Violations
    FFIEC_RISK_MANAGEMENT = "ffiec_risk_management"
    FFIEC_DATA_INTEGRITY = "ffiec_data_integrity"
    FFIEC_INCIDENT_RESPONSE = "ffiec_incident_response"
    
    # GLBA Violations
    GLBA_PRIVACY_BREACH = "glba_privacy_breach"
    GLBA_SAFEGUARDS_FAILURE = "glba_safeguards_failure"
    GLBA_DATA_SHARING = "glba_data_sharing"
    
    # BSA/AML Violations
    BSA_SUSPICIOUS_ACTIVITY = "bsa_suspicious_activity"
    BSA_RECORD_KEEPING = "bsa_record_keeping"
    BSA_REPORTING_FAILURE = "bsa_reporting_failure"
    
    # GDPR Violations
    GDPR_UNAUTHORIZED_PROCESSING = "gdpr_unauthorized_processing"
    GDPR_DATA_RETENTION = "gdpr_data_retention"
    GDPR_CONSENT_VIOLATION = "gdpr_consent_violation"
    
    # General Financial Violations
    FINANCIAL_FRAUD_INDICATOR = "financial_fraud_indicator"
    MONEY_LAUNDERING_RISK = "money_laundering_risk"
    HIGH_RISK_TRANSACTION = "high_risk_transaction"
    DATA_INTEGRITY_VIOLATION = "data_integrity_violation"


class ComplianceSeverity(Enum):
    """Severity levels for compliance violations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    REGULATORY_BREACH = "regulatory_breach"


@dataclass
class ComplianceRule:
    """Definition of a compliance rule"""
    rule_id: str
    rule_name: str
    regulation: RegulatoryFramework
    violation_type: ComplianceViolationType
    severity: ComplianceSeverity
    description: str
    check_function: str  # Name of the function to execute
    parameters: Dict[str, Any]
    active: bool
    threshold_values: Dict[str, Any]
    remediation_actions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['regulation'] = self.regulation.value
        data['violation_type'] = self.violation_type.value
        data['severity'] = self.severity.value
        return data


@dataclass
class ComplianceViolation:
    """Represents a compliance violation"""
    violation_id: str
    rule_id: str
    violation_type: ComplianceViolationType
    severity: ComplianceSeverity
    regulation: RegulatoryFramework
    timestamp: datetime
    user_id: Optional[str]
    transaction_id: Optional[str]
    operation_type: Optional[FinancialOperationType]
    description: str
    evidence: Dict[str, Any]
    risk_score: float
    immediate_action_required: bool
    remediation_deadline: Optional[datetime]
    status: str  # 'open', 'investigating', 'resolved', 'false_positive'
    assigned_to: Optional[str]
    resolution_notes: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['violation_type'] = self.violation_type.value
        data['severity'] = self.severity.value
        data['regulation'] = self.regulation.value
        data['timestamp'] = self.timestamp.isoformat()
        if self.operation_type:
            data['operation_type'] = self.operation_type.value
        if self.remediation_deadline:
            data['remediation_deadline'] = self.remediation_deadline.isoformat()
        return data


@dataclass
class IntegrityCheckResult:
    """Result of a data integrity check"""
    check_id: str
    entity_type: str
    entity_id: str
    check_type: str
    passed: bool
    expected_hash: Optional[str]
    actual_hash: Optional[str]
    timestamp: datetime
    details: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class FinancialComplianceMonitor:
    """
    Comprehensive financial compliance monitoring system
    """
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.logger = logging.getLogger('fingood.compliance_monitor')
        self.rules: Dict[str, ComplianceRule] = {}
        self.violations: List[ComplianceViolation] = []
        self.integrity_checks: List[IntegrityCheckResult] = []
        
        # Statistics
        self.stats = {
            'total_checks_performed': 0,
            'violations_detected': 0,
            'critical_violations': 0,
            'integrity_failures': 0,
            'rules_evaluated': 0
        }
        
        # Initialize compliance rules
        self._initialize_compliance_rules()
        
        # Fraud detection patterns
        self._initialize_fraud_patterns()
    
    def _initialize_compliance_rules(self):
        """Initialize comprehensive compliance rules"""
        
        # SOX Compliance Rules
        self._add_rule(ComplianceRule(
            rule_id="SOX-001",
            rule_name="High Value Transaction Approval",
            regulation=RegulatoryFramework.SOX,
            violation_type=ComplianceViolationType.SOX_MISSING_APPROVAL,
            severity=ComplianceSeverity.HIGH,
            description="Transactions over $10,000 require approval",
            check_function="check_high_value_approval",
            parameters={"threshold": 10000},
            active=True,
            threshold_values={"amount_threshold": 10000},
            remediation_actions=["Obtain retrospective approval", "Review approval process"]
        ))
        
        self._add_rule(ComplianceRule(
            rule_id="SOX-002",
            rule_name="Transaction Deletion Justification",
            regulation=RegulatoryFramework.SOX,
            violation_type=ComplianceViolationType.SOX_INADEQUATE_CONTROLS,
            severity=ComplianceSeverity.MEDIUM,
            description="Transaction deletions require business justification",
            check_function="check_deletion_justification",
            parameters={},
            active=True,
            threshold_values={},
            remediation_actions=["Provide business justification", "Document approval"]
        ))
        
        self._add_rule(ComplianceRule(
            rule_id="SOX-003",
            rule_name="Segregation of Duties",
            regulation=RegulatoryFramework.SOX,
            violation_type=ComplianceViolationType.SOX_SEGREGATION_VIOLATION,
            severity=ComplianceSeverity.HIGH,
            description="Users cannot approve their own transactions",
            check_function="check_segregation_of_duties",
            parameters={},
            active=True,
            threshold_values={},
            remediation_actions=["Assign different approver", "Review role assignments"]
        ))
        
        # PCI DSS Compliance Rules
        self._add_rule(ComplianceRule(
            rule_id="PCI-001",
            rule_name="Payment Data Access Control",
            regulation=RegulatoryFramework.PCI_DSS,
            violation_type=ComplianceViolationType.PCI_UNAUTHORIZED_ACCESS,
            severity=ComplianceSeverity.CRITICAL,
            description="Unauthorized access to payment card data",
            check_function="check_payment_data_access",
            parameters={},
            active=True,
            threshold_values={},
            remediation_actions=["Revoke access", "Conduct security review"]
        ))
        
        # FFIEC Compliance Rules
        self._add_rule(ComplianceRule(
            rule_id="FFIEC-001",
            rule_name="Data Integrity Verification",
            regulation=RegulatoryFramework.FFIEC,
            violation_type=ComplianceViolationType.FFIEC_DATA_INTEGRITY,
            severity=ComplianceSeverity.HIGH,
            description="Financial data integrity must be verified",
            check_function="check_data_integrity",
            parameters={},
            active=True,
            threshold_values={},
            remediation_actions=["Verify data integrity", "Restore from backup"]
        ))
        
        # BSA/AML Compliance Rules
        self._add_rule(ComplianceRule(
            rule_id="BSA-001",
            rule_name="Suspicious Transaction Pattern",
            regulation=RegulatoryFramework.BSA_AML,
            violation_type=ComplianceViolationType.BSA_SUSPICIOUS_ACTIVITY,
            severity=ComplianceSeverity.HIGH,
            description="Detect suspicious transaction patterns",
            check_function="check_suspicious_patterns",
            parameters={"pattern_threshold": 5},
            active=True,
            threshold_values={"pattern_count": 5},
            remediation_actions=["File SAR", "Conduct investigation"]
        ))
        
        # GLBA Compliance Rules
        self._add_rule(ComplianceRule(
            rule_id="GLBA-001",
            rule_name="Financial Privacy Protection",
            regulation=RegulatoryFramework.GLBA,
            violation_type=ComplianceViolationType.GLBA_PRIVACY_BREACH,
            severity=ComplianceSeverity.HIGH,
            description="Protect customer financial information",
            check_function="check_privacy_protection",
            parameters={},
            active=True,
            threshold_values={},
            remediation_actions=["Encrypt data", "Limit access"]
        ))
    
    def _initialize_fraud_patterns(self):
        """Initialize fraud detection patterns"""
        self.fraud_patterns = {
            'rapid_transactions': {
                'pattern': 'Multiple transactions in short time period',
                'threshold': 10,  # 10 transactions in 1 hour
                'risk_score': 0.7
            },
            'round_amounts': {
                'pattern': 'Frequent round number transactions',
                'threshold': 5,  # 5 round amounts in 24 hours
                'risk_score': 0.6
            },
            'unusual_vendors': {
                'pattern': 'Transactions with suspicious vendor names',
                'risk_score': 0.8
            },
            'amount_structuring': {
                'pattern': 'Amounts just below reporting thresholds',
                'threshold': 9999,  # Just below $10,000
                'risk_score': 0.9
            }
        }
    
    def _add_rule(self, rule: ComplianceRule):
        """Add a compliance rule to the monitor"""
        self.rules[rule.rule_id] = rule
    
    async def evaluate_operation(
        self,
        operation_type: FinancialOperationType,
        user_id: str,
        operation_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> List[ComplianceViolation]:
        """
        Evaluate an operation against all relevant compliance rules
        
        Args:
            operation_type: Type of financial operation
            user_id: User performing the operation
            operation_data: Data related to the operation
            context: Additional context information
            
        Returns:
            List of compliance violations found
        """
        violations = []
        context = context or {}
        
        for rule in self.rules.values():
            if not rule.active:
                continue
            
            self.stats['rules_evaluated'] += 1
            
            try:
                # Execute the compliance check
                violation = await self._execute_compliance_check(
                    rule, operation_type, user_id, operation_data, context
                )
                
                if violation:
                    violations.append(violation)
                    self.violations.append(violation)
                    self.stats['violations_detected'] += 1
                    
                    if violation.severity == ComplianceSeverity.CRITICAL:
                        self.stats['critical_violations'] += 1
                    
                    # Log the violation
                    await self._log_compliance_violation(violation)
                    
            except Exception as e:
                self.logger.error(f"Error executing compliance rule {rule.rule_id}: {e}")
        
        self.stats['total_checks_performed'] += 1
        return violations
    
    async def _execute_compliance_check(
        self,
        rule: ComplianceRule,
        operation_type: FinancialOperationType,
        user_id: str,
        operation_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[ComplianceViolation]:
        """Execute a specific compliance check"""
        
        check_function = getattr(self, rule.check_function, None)
        if not check_function:
            self.logger.warning(f"Check function {rule.check_function} not found")
            return None
        
        try:
            violation_detected = await check_function(
                rule, operation_type, user_id, operation_data, context
            )
            
            if violation_detected:
                return ComplianceViolation(
                    violation_id=self._generate_violation_id(),
                    rule_id=rule.rule_id,
                    violation_type=rule.violation_type,
                    severity=rule.severity,
                    regulation=rule.regulation,
                    timestamp=datetime.now(timezone.utc),
                    user_id=user_id,
                    transaction_id=operation_data.get('transaction_id'),
                    operation_type=operation_type,
                    description=violation_detected.get('description', rule.description),
                    evidence=violation_detected.get('evidence', {}),
                    risk_score=violation_detected.get('risk_score', 0.5),
                    immediate_action_required=violation_detected.get('immediate_action', False),
                    remediation_deadline=violation_detected.get('remediation_deadline'),
                    status='open',
                    assigned_to=None,
                    resolution_notes=None
                )
        except Exception as e:
            self.logger.error(f"Error in compliance check {rule.check_function}: {e}")
        
        return None
    
    async def check_high_value_approval(
        self,
        rule: ComplianceRule,
        operation_type: FinancialOperationType,
        user_id: str,
        operation_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check if high-value transactions have proper approval"""
        
        if operation_type not in [FinancialOperationType.TRANSACTION_CREATE, FinancialOperationType.TRANSACTION_UPDATE]:
            return None
        
        amount = operation_data.get('amount')
        if not amount:
            return None
        
        try:
            amount_decimal = Decimal(str(amount))
            threshold = Decimal(str(rule.parameters['threshold']))
            
            if amount_decimal >= threshold:
                approval_required = context.get('approval_required', False)
                approver_id = context.get('approver_id')
                
                if not approval_required or not approver_id:
                    return {
                        'description': f"Transaction of ${amount_decimal} requires approval (threshold: ${threshold})",
                        'evidence': {
                            'amount': str(amount_decimal),
                            'threshold': str(threshold),
                            'approval_required': approval_required,
                            'approver_id': approver_id
                        },
                        'risk_score': 0.8,
                        'immediate_action': True
                    }
        except (ValueError, TypeError):
            pass
        
        return None
    
    async def check_deletion_justification(
        self,
        rule: ComplianceRule,
        operation_type: FinancialOperationType,
        user_id: str,
        operation_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check if transaction deletions have business justification"""
        
        if operation_type not in [FinancialOperationType.TRANSACTION_DELETE, FinancialOperationType.TRANSACTION_BATCH_DELETE]:
            return None
        
        business_justification = context.get('business_justification')
        
        if not business_justification or len(business_justification.strip()) < 10:
            return {
                'description': "Transaction deletion requires business justification",
                'evidence': {
                    'operation_type': operation_type.value,
                    'justification_provided': bool(business_justification),
                    'justification_length': len(business_justification) if business_justification else 0
                },
                'risk_score': 0.6,
                'immediate_action': False
            }
        
        return None
    
    async def check_segregation_of_duties(
        self,
        rule: ComplianceRule,
        operation_type: FinancialOperationType,
        user_id: str,
        operation_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check segregation of duties compliance"""
        
        approver_id = context.get('approver_id')
        
        if approver_id and approver_id == user_id:
            return {
                'description': "User cannot approve their own transactions",
                'evidence': {
                    'user_id': user_id,
                    'approver_id': approver_id,
                    'self_approval': True
                },
                'risk_score': 0.9,
                'immediate_action': True
            }
        
        return None
    
    async def check_payment_data_access(
        self,
        rule: ComplianceRule,
        operation_type: FinancialOperationType,
        user_id: str,
        operation_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check for unauthorized payment data access"""
        
        if operation_type == FinancialOperationType.SENSITIVE_DATA_ACCESS:
            data_type = operation_data.get('data_type', '')
            
            if any(payment_term in data_type.lower() for payment_term in ['card', 'payment', 'cvv', 'pin']):
                user_role = context.get('user_role', '')
                authorized_roles = ['payment_processor', 'compliance_officer', 'admin']
                
                if user_role not in authorized_roles:
                    return {
                        'description': "Unauthorized access to payment card data",
                        'evidence': {
                            'user_id': user_id,
                            'user_role': user_role,
                            'data_type': data_type,
                            'authorized_roles': authorized_roles
                        },
                        'risk_score': 1.0,
                        'immediate_action': True
                    }
        
        return None
    
    async def check_data_integrity(
        self,
        rule: ComplianceRule,
        operation_type: FinancialOperationType,
        user_id: str,
        operation_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check data integrity for financial operations"""
        
        if operation_type in [FinancialOperationType.TRANSACTION_UPDATE, FinancialOperationType.TRANSACTION_DELETE]:
            # Verify data integrity hash if provided
            expected_hash = context.get('expected_integrity_hash')
            actual_data = operation_data.get('current_data', {})
            
            if expected_hash and actual_data:
                calculated_hash = self._calculate_data_hash(actual_data)
                
                if calculated_hash != expected_hash:
                    return {
                        'description': "Data integrity verification failed",
                        'evidence': {
                            'expected_hash': expected_hash,
                            'calculated_hash': calculated_hash,
                            'data_modified': True
                        },
                        'risk_score': 0.9,
                        'immediate_action': True
                    }
        
        return None
    
    async def check_suspicious_patterns(
        self,
        rule: ComplianceRule,
        operation_type: FinancialOperationType,
        user_id: str,
        operation_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check for suspicious transaction patterns"""
        
        if operation_type != FinancialOperationType.TRANSACTION_CREATE:
            return None
        
        # This would typically query recent transactions from the database
        # For now, we'll check the provided context for suspicious indicators
        
        suspicious_indicators = []
        risk_score = 0.0
        
        # Check for round amounts
        amount = operation_data.get('amount')
        if amount:
            try:
                amount_decimal = Decimal(str(amount))
                if amount_decimal % 100 == 0 and amount_decimal >= 1000:  # Round hundreds or thousands
                    suspicious_indicators.append("Round amount transaction")
                    risk_score += 0.3
            except (ValueError, TypeError):
                pass
        
        # Check for structuring (amounts just below reporting thresholds)
        if amount:
            try:
                amount_decimal = Decimal(str(amount))
                if 9900 <= amount_decimal <= 9999:
                    suspicious_indicators.append("Amount just below $10,000 threshold")
                    risk_score += 0.6
            except (ValueError, TypeError):
                pass
        
        # Check vendor name for suspicious patterns
        vendor = operation_data.get('vendor', '').lower()
        suspicious_vendor_patterns = ['cash', 'unknown', 'temp', 'test', 'dummy']
        if any(pattern in vendor for pattern in suspicious_vendor_patterns):
            suspicious_indicators.append("Suspicious vendor name")
            risk_score += 0.4
        
        # Check description for suspicious content
        description = operation_data.get('description', '').lower()
        suspicious_desc_patterns = ['cash withdraw', 'money transfer', 'wire', 'crypto']
        if any(pattern in description for pattern in suspicious_desc_patterns):
            suspicious_indicators.append("Suspicious transaction description")
            risk_score += 0.3
        
        if suspicious_indicators and risk_score >= 0.6:
            return {
                'description': f"Suspicious transaction pattern detected: {', '.join(suspicious_indicators)}",
                'evidence': {
                    'suspicious_indicators': suspicious_indicators,
                    'risk_score': risk_score,
                    'amount': str(amount) if amount else None,
                    'vendor': vendor,
                    'description': description
                },
                'risk_score': risk_score,
                'immediate_action': risk_score >= 0.8
            }
        
        return None
    
    async def check_privacy_protection(
        self,
        rule: ComplianceRule,
        operation_type: FinancialOperationType,
        user_id: str,
        operation_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check financial privacy protection compliance"""
        
        if operation_type == FinancialOperationType.DATA_EXPORT:
            # Check if personal financial information is being exported without proper controls
            export_type = operation_data.get('export_type', '')
            data_classification = context.get('data_classification', '')
            
            if 'financial' in data_classification.lower() or 'pii' in data_classification.lower():
                encryption_applied = context.get('encryption_applied', False)
                access_logging = context.get('access_logging', False)
                
                if not encryption_applied or not access_logging:
                    return {
                        'description': "Financial data export without adequate privacy protection",
                        'evidence': {
                            'export_type': export_type,
                            'data_classification': data_classification,
                            'encryption_applied': encryption_applied,
                            'access_logging': access_logging
                        },
                        'risk_score': 0.7,
                        'immediate_action': False
                    }
        
        return None
    
    async def verify_data_integrity(
        self,
        entity_type: str,
        entity_id: str,
        entity_data: Dict[str, Any],
        expected_hash: Optional[str] = None
    ) -> IntegrityCheckResult:
        """
        Verify data integrity for financial entities
        
        Args:
            entity_type: Type of entity (transaction, category, user)
            entity_id: Entity identifier
            entity_data: Current entity data
            expected_hash: Expected integrity hash
            
        Returns:
            IntegrityCheckResult
        """
        check_id = self._generate_check_id()
        calculated_hash = self._calculate_data_hash(entity_data)
        
        passed = True
        if expected_hash:
            passed = hmac.compare_digest(calculated_hash, expected_hash)
        
        result = IntegrityCheckResult(
            check_id=check_id,
            entity_type=entity_type,
            entity_id=entity_id,
            check_type="integrity_verification",
            passed=passed,
            expected_hash=expected_hash,
            actual_hash=calculated_hash,
            timestamp=datetime.now(timezone.utc),
            details={
                'entity_data_size': len(json.dumps(entity_data)),
                'hash_algorithm': 'HMAC-SHA256',
                'verification_method': 'cryptographic'
            }
        )
        
        self.integrity_checks.append(result)
        
        if not passed:
            self.stats['integrity_failures'] += 1
            
            # Create a compliance violation for integrity failure
            violation = ComplianceViolation(
                violation_id=self._generate_violation_id(),
                rule_id="INTEGRITY-001",
                violation_type=ComplianceViolationType.DATA_INTEGRITY_VIOLATION,
                severity=ComplianceSeverity.HIGH,
                regulation=RegulatoryFramework.FFIEC,
                timestamp=datetime.now(timezone.utc),
                user_id=None,
                transaction_id=entity_id if entity_type == 'transaction' else None,
                operation_type=None,
                description=f"Data integrity verification failed for {entity_type} {entity_id}",
                evidence={
                    'entity_type': entity_type,
                    'entity_id': entity_id,
                    'expected_hash': expected_hash,
                    'actual_hash': calculated_hash,
                    'check_id': check_id
                },
                risk_score=0.9,
                immediate_action_required=True,
                remediation_deadline=datetime.now(timezone.utc) + timedelta(hours=24),
                status='open',
                assigned_to=None,
                resolution_notes=None
            )
            
            self.violations.append(violation)
            await self._log_compliance_violation(violation)
        
        return result
    
    async def detect_fraud_indicators(
        self,
        user_id: str,
        operation_data: Dict[str, Any],
        historical_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Detect fraud indicators in financial operations
        
        Args:
            user_id: User identifier
            operation_data: Current operation data
            historical_data: Historical transaction data for pattern analysis
            
        Returns:
            Fraud detection results
        """
        fraud_indicators = []
        risk_score = 0.0
        
        # Analyze current transaction
        amount = operation_data.get('amount')
        vendor = operation_data.get('vendor', '').lower()
        description = operation_data.get('description', '').lower()
        timestamp = operation_data.get('timestamp')
        
        # Check for round amounts
        if amount:
            try:
                amount_decimal = Decimal(str(amount))
                if amount_decimal % 100 == 0 and amount_decimal >= 1000:
                    fraud_indicators.append({
                        'type': 'round_amount',
                        'description': 'Transaction amount is a round number',
                        'risk_contribution': 0.3
                    })
                    risk_score += 0.3
            except (ValueError, TypeError):
                pass
        
        # Check for suspicious vendor patterns
        suspicious_vendors = ['cash', 'unknown', 'temp', 'test', 'dummy', 'atm']
        if any(pattern in vendor for pattern in suspicious_vendors):
            fraud_indicators.append({
                'type': 'suspicious_vendor',
                'description': 'Vendor name matches suspicious pattern',
                'risk_contribution': 0.4
            })
            risk_score += 0.4
        
        # Check for suspicious descriptions
        suspicious_descriptions = ['cash withdraw', 'money transfer', 'wire', 'crypto', 'bitcoin']
        if any(pattern in description for pattern in suspicious_descriptions):
            fraud_indicators.append({
                'type': 'suspicious_description',
                'description': 'Transaction description contains suspicious terms',
                'risk_contribution': 0.3
            })
            risk_score += 0.3
        
        # Analyze historical patterns if provided
        if historical_data:
            # Check for rapid transaction patterns
            recent_transactions = [
                tx for tx in historical_data 
                if tx.get('timestamp') and self._is_recent(tx['timestamp'], hours=1)
            ]
            
            if len(recent_transactions) >= 10:
                fraud_indicators.append({
                    'type': 'rapid_transactions',
                    'description': f'{len(recent_transactions)} transactions in the last hour',
                    'risk_contribution': 0.6
                })
                risk_score += 0.6
            
            # Check for amount structuring
            if amount:
                try:
                    amount_decimal = Decimal(str(amount))
                    if 9900 <= amount_decimal <= 9999:
                        recent_similar = [
                            tx for tx in historical_data
                            if tx.get('amount') and 9900 <= Decimal(str(tx['amount'])) <= 9999
                            and self._is_recent(tx.get('timestamp'), days=7)
                        ]
                        
                        if len(recent_similar) >= 3:
                            fraud_indicators.append({
                                'type': 'amount_structuring',
                                'description': 'Multiple transactions just below $10,000 threshold',
                                'risk_contribution': 0.8
                            })
                            risk_score += 0.8
                except (ValueError, TypeError):
                    pass
        
        # Determine overall risk level
        if risk_score >= 0.8:
            risk_level = 'HIGH'
        elif risk_score >= 0.5:
            risk_level = 'MEDIUM'
        elif risk_score >= 0.3:
            risk_level = 'LOW'
        else:
            risk_level = 'MINIMAL'
        
        return {
            'fraud_indicators': fraud_indicators,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'immediate_investigation_required': risk_score >= 0.7,
            'recommended_actions': self._get_fraud_response_actions(risk_score),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def _calculate_data_hash(self, data: Dict[str, Any]) -> str:
        """Calculate HMAC hash for data integrity verification"""
        sorted_data = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hmac.new(
            self.secret_key.encode(),
            sorted_data.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _generate_violation_id(self) -> str:
        """Generate unique violation ID"""
        timestamp = datetime.now(timezone.utc).isoformat()
        data = f"violation:{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _generate_check_id(self) -> str:
        """Generate unique check ID"""
        timestamp = datetime.now(timezone.utc).isoformat()
        data = f"check:{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _is_recent(self, timestamp_str: str, hours: int = 24, days: int = 0) -> bool:
        """Check if a timestamp is within the specified time period"""
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours, days=days)
            return timestamp >= cutoff
        except (ValueError, TypeError):
            return False
    
    def _get_fraud_response_actions(self, risk_score: float) -> List[str]:
        """Get recommended actions based on fraud risk score"""
        if risk_score >= 0.8:
            return [
                "Immediately freeze related accounts",
                "Notify compliance team",
                "Conduct detailed investigation",
                "File suspicious activity report if required",
                "Review all recent transactions from user"
            ]
        elif risk_score >= 0.5:
            return [
                "Flag account for monitoring",
                "Require additional verification for future transactions",
                "Review transaction history",
                "Consider temporary limits"
            ]
        elif risk_score >= 0.3:
            return [
                "Add to monitoring list",
                "Document findings",
                "Increase transaction review frequency"
            ]
        else:
            return ["Continue normal monitoring"]
    
    async def _log_compliance_violation(self, violation: ComplianceViolation):
        """Log compliance violation to audit system"""
        self.logger.error(
            f"Compliance violation detected: {violation.violation_type.value}",
            extra={
                'violation_id': violation.violation_id,
                'rule_id': violation.rule_id,
                'severity': violation.severity.value,
                'regulation': violation.regulation.value,
                'user_id': violation.user_id,
                'transaction_id': violation.transaction_id,
                'risk_score': violation.risk_score,
                'immediate_action_required': violation.immediate_action_required,
                'evidence': violation.evidence
            }
        )
        
        # Also log to compliance logger if available
        compliance_logger = get_compliance_logger()
        if compliance_logger:
            await compliance_logger.log_compliance_event(
                event_type=self._map_violation_to_event_type(violation.violation_type),
                regulatory_frameworks=[violation.regulation],
                data_classification=self._determine_data_classification(violation),
                risk_level=self._map_severity_to_risk(violation.severity),
                user_id=violation.user_id,
                resource_type="financial_operation",
                resource_id=violation.transaction_id,
                action_performed=violation.violation_type.value,
                outcome="violation_detected",
                system_component="compliance_monitor",
                error_code=violation.violation_type.value,
                error_message=violation.description,
                additional_data=violation.evidence
            )
    
    def _map_violation_to_event_type(self, violation_type: ComplianceViolationType):
        """Map violation type to compliance event type"""
        from app.core.compliance_logger import ComplianceEventType
        
        mapping = {
            ComplianceViolationType.SOX_UNAUTHORIZED_CHANGE: ComplianceEventType.DATA_MODIFICATION,
            ComplianceViolationType.PCI_UNAUTHORIZED_ACCESS: ComplianceEventType.DATA_ACCESS,
            ComplianceViolationType.GLBA_PRIVACY_BREACH: ComplianceEventType.PRIVACY_EVENT,
            ComplianceViolationType.DATA_INTEGRITY_VIOLATION: ComplianceEventType.DATA_MODIFICATION
        }
        
        return mapping.get(violation_type, ComplianceEventType.SECURITY_INCIDENT)
    
    def _determine_data_classification(self, violation: ComplianceViolation):
        """Determine data classification based on violation"""
        from app.core.compliance_logger import DataClassification
        
        if violation.regulation == RegulatoryFramework.PCI_DSS:
            return DataClassification.PCI_DATA
        elif violation.regulation == RegulatoryFramework.GLBA:
            return DataClassification.FINANCIAL
        else:
            return DataClassification.CONFIDENTIAL
    
    def _map_severity_to_risk(self, severity: ComplianceSeverity):
        """Map compliance severity to risk level"""
        mapping = {
            ComplianceSeverity.LOW: ComplianceRisk.LOW,
            ComplianceSeverity.MEDIUM: ComplianceRisk.MEDIUM,
            ComplianceSeverity.HIGH: ComplianceRisk.HIGH,
            ComplianceSeverity.CRITICAL: ComplianceRisk.CRITICAL,
            ComplianceSeverity.REGULATORY_BREACH: ComplianceRisk.CRITICAL
        }
        return mapping.get(severity, ComplianceRisk.MEDIUM)
    
    def get_compliance_statistics(self) -> Dict[str, Any]:
        """Get compliance monitoring statistics"""
        return {
            'statistics': self.stats.copy(),
            'active_rules': len([r for r in self.rules.values() if r.active]),
            'total_rules': len(self.rules),
            'open_violations': len([v for v in self.violations if v.status == 'open']),
            'critical_violations': len([v for v in self.violations if v.severity == ComplianceSeverity.CRITICAL]),
            'recent_integrity_checks': len([c for c in self.integrity_checks if self._is_recent(c.timestamp.isoformat(), hours=24)]),
            'integrity_failure_rate': self.stats['integrity_failures'] / max(len(self.integrity_checks), 1),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


# Global compliance monitor instance
_compliance_monitor: Optional[FinancialComplianceMonitor] = None


def initialize_compliance_monitor(secret_key: str) -> FinancialComplianceMonitor:
    """
    Initialize global compliance monitor
    
    Args:
        secret_key: Secret key for integrity verification
        
    Returns:
        FinancialComplianceMonitor instance
    """
    global _compliance_monitor
    _compliance_monitor = FinancialComplianceMonitor(secret_key)
    return _compliance_monitor


def get_compliance_monitor() -> Optional[FinancialComplianceMonitor]:
    """Get the global compliance monitor"""
    return _compliance_monitor


# Convenience functions for common compliance checks
async def check_operation_compliance(
    operation_type: FinancialOperationType,
    user_id: str,
    operation_data: Dict[str, Any],
    **context
) -> List[ComplianceViolation]:
    """Check operation compliance"""
    if _compliance_monitor:
        return await _compliance_monitor.evaluate_operation(
            operation_type, user_id, operation_data, context
        )
    return []


async def verify_transaction_integrity(
    transaction_id: str,
    transaction_data: Dict[str, Any],
    expected_hash: Optional[str] = None
) -> IntegrityCheckResult:
    """Verify transaction data integrity"""
    if _compliance_monitor:
        return await _compliance_monitor.verify_data_integrity(
            "transaction", transaction_id, transaction_data, expected_hash
        )
    return IntegrityCheckResult(
        check_id="unknown",
        entity_type="transaction",
        entity_id=transaction_id,
        check_type="integrity_verification",
        passed=False,
        expected_hash=expected_hash,
        actual_hash=None,
        timestamp=datetime.now(timezone.utc),
        details={"error": "Compliance monitor not initialized"}
    )


async def detect_transaction_fraud(
    user_id: str,
    transaction_data: Dict[str, Any],
    historical_transactions: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Detect fraud indicators in transaction"""
    if _compliance_monitor:
        return await _compliance_monitor.detect_fraud_indicators(
            user_id, transaction_data, historical_transactions
        )
    return {
        'fraud_indicators': [],
        'risk_score': 0.0,
        'risk_level': 'UNKNOWN',
        'immediate_investigation_required': False,
        'recommended_actions': [],
        'error': 'Compliance monitor not initialized'
    }