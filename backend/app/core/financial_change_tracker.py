"""
Financial Change Tracker for FinGood Application

This module provides comprehensive change tracking for financial transactions
and related data, enabling complete audit trails with before/after values,
data lineage tracking, and regulatory compliance.
"""

import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, Optional, List, Union, Set, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from copy import deepcopy
import hashlib

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.core.financial_audit_logger import (
    FinancialChangeRecord, 
    FinancialDataSensitivity,
    FinancialOperationType,
    get_financial_audit_logger
)


class ChangeType(Enum):
    """Types of changes that can be tracked"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    BULK_UPDATE = "bulk_update"
    BULK_DELETE = "bulk_delete"
    CATEGORIZATION = "categorization"
    RECATEGORIZATION = "recategorization"
    IMPORT = "import"
    EXPORT = "export"


class FieldSensitivity(Enum):
    """Sensitivity levels for individual fields"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    HIGHLY_SENSITIVE = "highly_sensitive"
    FINANCIAL_CRITICAL = "financial_critical"
    REGULATORY_PROTECTED = "regulatory_protected"


@dataclass
class FieldMetadata:
    """Metadata about a tracked field"""
    field_name: str
    data_type: str
    sensitivity: FieldSensitivity
    regulatory_implications: List[str]
    masking_required: bool
    audit_required: bool
    immutable_after_create: bool
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['sensitivity'] = self.sensitivity.value
        return data


@dataclass
class ChangeEvent:
    """Represents a single change event"""
    field_name: str
    old_value: Any
    new_value: Any
    change_type: ChangeType
    timestamp: datetime
    user_id: str
    session_id: Optional[str]
    request_id: Optional[str]
    field_metadata: FieldMetadata
    validation_errors: List[str]
    business_impact: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['change_type'] = self.change_type.value
        data['timestamp'] = self.timestamp.isoformat()
        data['field_metadata'] = self.field_metadata.to_dict()
        
        # Convert Decimal to string for JSON serialization
        if isinstance(self.old_value, Decimal):
            data['old_value'] = str(self.old_value)
        if isinstance(self.new_value, Decimal):
            data['new_value'] = str(self.new_value)
            
        return data


@dataclass
class TransactionChangeSet:
    """Complete set of changes for a transaction"""
    transaction_id: str
    change_set_id: str
    operation_type: FinancialOperationType
    timestamp: datetime
    user_id: str
    session_id: Optional[str]
    request_id: Optional[str]
    changes: List[ChangeEvent]
    before_state: Dict[str, Any]
    after_state: Dict[str, Any]
    validation_status: str
    business_justification: Optional[str]
    approval_status: Optional[str]
    approver_id: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['operation_type'] = self.operation_type.value
        data['timestamp'] = self.timestamp.isoformat()
        data['changes'] = [change.to_dict() for change in self.changes]
        return data


class FinancialFieldRegistry:
    """Registry of financial fields and their metadata"""
    
    def __init__(self):
        self.field_metadata: Dict[str, FieldMetadata] = {}
        self._initialize_transaction_fields()
        self._initialize_category_fields()
        self._initialize_user_fields()
    
    def _initialize_transaction_fields(self):
        """Initialize transaction field metadata"""
        transaction_fields = {
            'id': FieldMetadata(
                field_name='id',
                data_type='integer',
                sensitivity=FieldSensitivity.INTERNAL,
                regulatory_implications=['SOX', 'FFIEC'],
                masking_required=False,
                audit_required=True,
                immutable_after_create=True
            ),
            'amount': FieldMetadata(
                field_name='amount',
                data_type='decimal',
                sensitivity=FieldSensitivity.FINANCIAL_CRITICAL,
                regulatory_implications=['SOX', 'FFIEC', 'BSA'],
                masking_required=True,
                audit_required=True,
                immutable_after_create=False
            ),
            'description': FieldMetadata(
                field_name='description',
                data_type='text',
                sensitivity=FieldSensitivity.CONFIDENTIAL,
                regulatory_implications=['SOX'],
                masking_required=False,
                audit_required=True,
                immutable_after_create=False
            ),
            'vendor': FieldMetadata(
                field_name='vendor',
                data_type='string',
                sensitivity=FieldSensitivity.CONFIDENTIAL,
                regulatory_implications=['SOX'],
                masking_required=False,
                audit_required=True,
                immutable_after_create=False
            ),
            'category': FieldMetadata(
                field_name='category',
                data_type='string',
                sensitivity=FieldSensitivity.INTERNAL,
                regulatory_implications=['SOX'],
                masking_required=False,
                audit_required=True,
                immutable_after_create=False
            ),
            'subcategory': FieldMetadata(
                field_name='subcategory',
                data_type='string',
                sensitivity=FieldSensitivity.INTERNAL,
                regulatory_implications=['SOX'],
                masking_required=False,
                audit_required=True,
                immutable_after_create=False
            ),
            'date': FieldMetadata(
                field_name='date',
                data_type='datetime',
                sensitivity=FieldSensitivity.FINANCIAL_CRITICAL,
                regulatory_implications=['SOX', 'FFIEC'],
                masking_required=False,
                audit_required=True,
                immutable_after_create=False
            ),
            'is_income': FieldMetadata(
                field_name='is_income',
                data_type='boolean',
                sensitivity=FieldSensitivity.FINANCIAL_CRITICAL,
                regulatory_implications=['SOX'],
                masking_required=False,
                audit_required=True,
                immutable_after_create=False
            ),
            'source': FieldMetadata(
                field_name='source',
                data_type='string',
                sensitivity=FieldSensitivity.INTERNAL,
                regulatory_implications=['SOX'],
                masking_required=False,
                audit_required=True,
                immutable_after_create=True
            ),
            'source_id': FieldMetadata(
                field_name='source_id',
                data_type='string',
                sensitivity=FieldSensitivity.INTERNAL,
                regulatory_implications=['SOX'],
                masking_required=False,
                audit_required=True,
                immutable_after_create=True
            ),
            'import_batch': FieldMetadata(
                field_name='import_batch',
                data_type='string',
                sensitivity=FieldSensitivity.INTERNAL,
                regulatory_implications=['SOX'],
                masking_required=False,
                audit_required=True,
                immutable_after_create=True
            ),
            'raw_data': FieldMetadata(
                field_name='raw_data',
                data_type='json',
                sensitivity=FieldSensitivity.CONFIDENTIAL,
                regulatory_implications=['SOX'],
                masking_required=True,
                audit_required=True,
                immutable_after_create=True
            ),
            'meta_data': FieldMetadata(
                field_name='meta_data',
                data_type='json',
                sensitivity=FieldSensitivity.INTERNAL,
                regulatory_implications=['SOX'],
                masking_required=False,
                audit_required=True,
                immutable_after_create=False
            )
        }
        
        for field_name, metadata in transaction_fields.items():
            self.register_field(f"transaction.{field_name}", metadata)
    
    def _initialize_category_fields(self):
        """Initialize category field metadata"""
        category_fields = {
            'id': FieldMetadata(
                field_name='id',
                data_type='integer',
                sensitivity=FieldSensitivity.INTERNAL,
                regulatory_implications=[],
                masking_required=False,
                audit_required=True,
                immutable_after_create=True
            ),
            'name': FieldMetadata(
                field_name='name',
                data_type='string',
                sensitivity=FieldSensitivity.INTERNAL,
                regulatory_implications=[],
                masking_required=False,
                audit_required=True,
                immutable_after_create=False
            ),
            'parent_category': FieldMetadata(
                field_name='parent_category',
                data_type='string',
                sensitivity=FieldSensitivity.INTERNAL,
                regulatory_implications=[],
                masking_required=False,
                audit_required=True,
                immutable_after_create=False
            )
        }
        
        for field_name, metadata in category_fields.items():
            self.register_field(f"category.{field_name}", metadata)
    
    def _initialize_user_fields(self):
        """Initialize user field metadata"""
        user_fields = {
            'id': FieldMetadata(
                field_name='id',
                data_type='integer',
                sensitivity=FieldSensitivity.INTERNAL,
                regulatory_implications=['GDPR', 'CCPA'],
                masking_required=False,
                audit_required=True,
                immutable_after_create=True
            ),
            'email': FieldMetadata(
                field_name='email',
                data_type='string',
                sensitivity=FieldSensitivity.REGULATORY_PROTECTED,
                regulatory_implications=['GDPR', 'CCPA'],
                masking_required=True,
                audit_required=True,
                immutable_after_create=False
            ),
            'is_active': FieldMetadata(
                field_name='is_active',
                data_type='boolean',
                sensitivity=FieldSensitivity.CONFIDENTIAL,
                regulatory_implications=['GDPR'],
                masking_required=False,
                audit_required=True,
                immutable_after_create=False
            )
        }
        
        for field_name, metadata in user_fields.items():
            self.register_field(f"user.{field_name}", metadata)
    
    def register_field(self, field_key: str, metadata: FieldMetadata):
        """Register field metadata"""
        self.field_metadata[field_key] = metadata
    
    def get_field_metadata(self, entity_type: str, field_name: str) -> Optional[FieldMetadata]:
        """Get field metadata"""
        field_key = f"{entity_type}.{field_name}"
        return self.field_metadata.get(field_key)
    
    def get_sensitive_fields(self, entity_type: str) -> List[str]:
        """Get list of sensitive fields for an entity type"""
        sensitive_fields = []
        prefix = f"{entity_type}."
        
        for field_key, metadata in self.field_metadata.items():
            if field_key.startswith(prefix) and metadata.sensitivity in [
                FieldSensitivity.HIGHLY_SENSITIVE,
                FieldSensitivity.FINANCIAL_CRITICAL,
                FieldSensitivity.REGULATORY_PROTECTED
            ]:
                sensitive_fields.append(metadata.field_name)
        
        return sensitive_fields


class FinancialChangeTracker:
    """
    Comprehensive change tracker for financial data with audit compliance
    """
    
    def __init__(self, field_registry: Optional[FinancialFieldRegistry] = None):
        self.field_registry = field_registry or FinancialFieldRegistry()
        self.logger = logging.getLogger('fingood.change_tracker')
        self.pending_changes: Dict[str, List[ChangeEvent]] = {}
        self.change_sets: List[TransactionChangeSet] = []
    
    def track_entity_changes(
        self,
        entity_type: str,
        entity_before: Optional[Dict[str, Any]],
        entity_after: Optional[Dict[str, Any]],
        change_type: ChangeType,
        user_id: str,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        business_justification: Optional[str] = None
    ) -> List[ChangeEvent]:
        """
        Track changes to a financial entity
        
        Args:
            entity_type: Type of entity (transaction, category, user)
            entity_before: Entity state before changes
            entity_after: Entity state after changes
            change_type: Type of change operation
            user_id: User making the change
            session_id: Session identifier
            request_id: Request identifier
            business_justification: Business reason for the change
            
        Returns:
            List of change events
        """
        changes = []
        timestamp = datetime.now(timezone.utc)
        
        if change_type == ChangeType.CREATE:
            # For create operations, all fields are new
            if entity_after:
                for field_name, new_value in entity_after.items():
                    field_metadata = self.field_registry.get_field_metadata(entity_type, field_name)
                    if field_metadata and field_metadata.audit_required:
                        change_event = ChangeEvent(
                            field_name=field_name,
                            old_value=None,
                            new_value=new_value,
                            change_type=change_type,
                            timestamp=timestamp,
                            user_id=user_id,
                            session_id=session_id,
                            request_id=request_id,
                            field_metadata=field_metadata,
                            validation_errors=[],
                            business_impact=self._assess_business_impact(field_metadata, None, new_value)
                        )
                        changes.append(change_event)
        
        elif change_type == ChangeType.DELETE:
            # For delete operations, all fields are removed
            if entity_before:
                for field_name, old_value in entity_before.items():
                    field_metadata = self.field_registry.get_field_metadata(entity_type, field_name)
                    if field_metadata and field_metadata.audit_required:
                        change_event = ChangeEvent(
                            field_name=field_name,
                            old_value=old_value,
                            new_value=None,
                            change_type=change_type,
                            timestamp=timestamp,
                            user_id=user_id,
                            session_id=session_id,
                            request_id=request_id,
                            field_metadata=field_metadata,
                            validation_errors=[],
                            business_impact=self._assess_business_impact(field_metadata, old_value, None)
                        )
                        changes.append(change_event)
        
        else:
            # For update operations, compare before and after
            if entity_before and entity_after:
                all_fields = set(entity_before.keys()) | set(entity_after.keys())
                
                for field_name in all_fields:
                    old_value = entity_before.get(field_name)
                    new_value = entity_after.get(field_name)
                    
                    # Check if value actually changed
                    if self._values_differ(old_value, new_value):
                        field_metadata = self.field_registry.get_field_metadata(entity_type, field_name)
                        if field_metadata and field_metadata.audit_required:
                            
                            # Validate the change
                            validation_errors = self._validate_field_change(
                                field_metadata, old_value, new_value, change_type
                            )
                            
                            change_event = ChangeEvent(
                                field_name=field_name,
                                old_value=old_value,
                                new_value=new_value,
                                change_type=change_type,
                                timestamp=timestamp,
                                user_id=user_id,
                                session_id=session_id,
                                request_id=request_id,
                                field_metadata=field_metadata,
                                validation_errors=validation_errors,
                                business_impact=self._assess_business_impact(field_metadata, old_value, new_value)
                            )
                            changes.append(change_event)
        
        return changes
    
    def track_sqlalchemy_changes(
        self,
        db_session: Session,
        entity,
        change_type: ChangeType,
        user_id: str,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> List[ChangeEvent]:
        """
        Track changes to a SQLAlchemy entity
        
        Args:
            db_session: SQLAlchemy session
            entity: SQLAlchemy entity instance
            change_type: Type of change
            user_id: User making the change
            session_id: Session identifier
            request_id: Request identifier
            
        Returns:
            List of change events
        """
        entity_type = entity.__class__.__name__.lower()
        inspector = inspect(entity)
        
        if change_type == ChangeType.CREATE:
            # For new entities, get current state
            entity_after = self._get_entity_state(entity)
            return self.track_entity_changes(
                entity_type=entity_type,
                entity_before=None,
                entity_after=entity_after,
                change_type=change_type,
                user_id=user_id,
                session_id=session_id,
                request_id=request_id
            )
        
        elif change_type == ChangeType.DELETE:
            # For deleted entities, get current state as "before"
            entity_before = self._get_entity_state(entity)
            return self.track_entity_changes(
                entity_type=entity_type,
                entity_before=entity_before,
                entity_after=None,
                change_type=change_type,
                user_id=user_id,
                session_id=session_id,
                request_id=request_id
            )
        
        else:
            # For updates, compare original and current values
            entity_before = {}
            entity_after = {}
            
            for attr in inspector.attrs:
                attr_name = attr.key
                
                # Get original value (before changes)
                history = inspector.get_history(attr_name)
                if history.has_changes():
                    if history.deleted:
                        entity_before[attr_name] = history.deleted[0]
                    if history.added:
                        entity_after[attr_name] = history.added[0]
                    
                    # If no deleted value, get current value as "before"
                    if attr_name not in entity_before:
                        entity_before[attr_name] = getattr(entity, attr_name)
                    
                    # If no added value, get current value as "after"
                    if attr_name not in entity_after:
                        entity_after[attr_name] = getattr(entity, attr_name)
            
            return self.track_entity_changes(
                entity_type=entity_type,
                entity_before=entity_before,
                entity_after=entity_after,
                change_type=change_type,
                user_id=user_id,
                session_id=session_id,
                request_id=request_id
            )
    
    def create_change_set(
        self,
        transaction_id: str,
        operation_type: FinancialOperationType,
        changes: List[ChangeEvent],
        before_state: Dict[str, Any],
        after_state: Dict[str, Any],
        user_id: str,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        business_justification: Optional[str] = None,
        approval_status: Optional[str] = None,
        approver_id: Optional[str] = None
    ) -> TransactionChangeSet:
        """
        Create a comprehensive change set for a transaction
        
        Args:
            transaction_id: Transaction identifier
            operation_type: Financial operation type
            changes: List of individual change events
            before_state: Complete state before changes
            after_state: Complete state after changes
            user_id: User making changes
            session_id: Session identifier
            request_id: Request identifier
            business_justification: Business reason for changes
            approval_status: Approval status if required
            approver_id: ID of approver if required
            
        Returns:
            TransactionChangeSet instance
        """
        change_set = TransactionChangeSet(
            transaction_id=transaction_id,
            change_set_id=self._generate_change_set_id(transaction_id),
            operation_type=operation_type,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            changes=changes,
            before_state=before_state,
            after_state=after_state,
            validation_status=self._validate_change_set(changes),
            business_justification=business_justification,
            approval_status=approval_status,
            approver_id=approver_id
        )
        
        self.change_sets.append(change_set)
        return change_set
    
    async def convert_to_audit_records(self, changes: List[ChangeEvent]) -> List[FinancialChangeRecord]:
        """
        Convert change events to financial audit records
        
        Args:
            changes: List of change events
            
        Returns:
            List of FinancialChangeRecord instances
        """
        audit_records = []
        
        for change in changes:
            # Map field sensitivity to financial data sensitivity
            data_sensitivity = self._map_field_sensitivity(change.field_metadata.sensitivity)
            
            audit_record = FinancialChangeRecord(
                field_name=change.field_name,
                old_value=change.old_value,
                new_value=change.new_value,
                change_type=change.change_type.value,
                data_sensitivity=data_sensitivity,
                regulatory_impact=change.field_metadata.regulatory_implications
            )
            audit_records.append(audit_record)
        
        return audit_records
    
    def _get_entity_state(self, entity) -> Dict[str, Any]:
        """Get current state of an entity as a dictionary"""
        state = {}
        inspector = inspect(entity)
        
        for attr in inspector.attrs:
            attr_name = attr.key
            try:
                value = getattr(entity, attr_name)
                # Convert to JSON-serializable format
                if isinstance(value, datetime):
                    state[attr_name] = value.isoformat()
                elif isinstance(value, Decimal):
                    state[attr_name] = str(value)
                else:
                    state[attr_name] = value
            except Exception as e:
                # Skip attributes that can't be accessed
                self.logger.warning(f"Could not access attribute {attr_name}: {e}")
                continue
        
        return state
    
    def _values_differ(self, old_value: Any, new_value: Any) -> bool:
        """Check if two values are different"""
        # Handle None values
        if old_value is None and new_value is None:
            return False
        if old_value is None or new_value is None:
            return True
        
        # Handle Decimal values
        if isinstance(old_value, Decimal) and isinstance(new_value, Decimal):
            return old_value != new_value
        
        # Handle datetime values
        if isinstance(old_value, datetime) and isinstance(new_value, datetime):
            return old_value != new_value
        
        # Handle JSON/dict values
        if isinstance(old_value, dict) and isinstance(new_value, dict):
            return json.dumps(old_value, sort_keys=True) != json.dumps(new_value, sort_keys=True)
        
        # Default comparison
        return old_value != new_value
    
    def _validate_field_change(
        self,
        field_metadata: FieldMetadata,
        old_value: Any,
        new_value: Any,
        change_type: ChangeType
    ) -> List[str]:
        """Validate a field change and return any validation errors"""
        errors = []
        
        # Check if field is immutable after creation
        if (field_metadata.immutable_after_create and 
            change_type == ChangeType.UPDATE and 
            old_value is not None):
            errors.append(f"Field {field_metadata.field_name} is immutable after creation")
        
        # Check for suspicious amount changes
        if (field_metadata.field_name == 'amount' and 
            old_value is not None and new_value is not None):
            try:
                old_amount = Decimal(str(old_value))
                new_amount = Decimal(str(new_value))
                change_percent = abs((new_amount - old_amount) / old_amount) * 100
                
                if change_percent > 50:  # More than 50% change
                    errors.append(f"Large amount change detected: {change_percent:.1f}% change")
            except (ValueError, ZeroDivisionError):
                pass
        
        # Check for regulatory protected fields
        if (field_metadata.sensitivity == FieldSensitivity.REGULATORY_PROTECTED and
            change_type in [ChangeType.UPDATE, ChangeType.DELETE]):
            errors.append(f"Change to regulatory protected field {field_metadata.field_name} requires special approval")
        
        return errors
    
    def _assess_business_impact(
        self,
        field_metadata: FieldMetadata,
        old_value: Any,
        new_value: Any
    ) -> Optional[str]:
        """Assess the business impact of a field change"""
        
        # High impact changes
        if field_metadata.field_name == 'amount':
            return "Financial amount change - impacts accounting and reporting"
        
        if field_metadata.field_name in ['category', 'subcategory']:
            return "Categorization change - impacts budget tracking and reporting"
        
        if field_metadata.field_name == 'date':
            return "Transaction date change - impacts period reporting"
        
        if field_metadata.field_name == 'is_income':
            return "Income classification change - impacts cash flow analysis"
        
        # Medium impact changes
        if field_metadata.field_name in ['description', 'vendor']:
            return "Transaction details change - impacts identification and analysis"
        
        # Low impact changes
        return "Metadata change - minimal business impact"
    
    def _validate_change_set(self, changes: List[ChangeEvent]) -> str:
        """Validate a complete change set"""
        total_errors = sum(len(change.validation_errors) for change in changes)
        
        if total_errors == 0:
            return "valid"
        elif total_errors < 3:
            return "warning"
        else:
            return "invalid"
    
    def _generate_change_set_id(self, transaction_id: str) -> str:
        """Generate a unique change set ID"""
        timestamp = datetime.now(timezone.utc).isoformat()
        data = f"{transaction_id}:{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _map_field_sensitivity(self, field_sensitivity: FieldSensitivity) -> FinancialDataSensitivity:
        """Map field sensitivity to financial data sensitivity"""
        mapping = {
            FieldSensitivity.PUBLIC: FinancialDataSensitivity.PUBLIC,
            FieldSensitivity.INTERNAL: FinancialDataSensitivity.INTERNAL,
            FieldSensitivity.CONFIDENTIAL: FinancialDataSensitivity.CONFIDENTIAL,
            FieldSensitivity.HIGHLY_SENSITIVE: FinancialDataSensitivity.HIGHLY_SENSITIVE,
            FieldSensitivity.FINANCIAL_CRITICAL: FinancialDataSensitivity.HIGHLY_SENSITIVE,
            FieldSensitivity.REGULATORY_PROTECTED: FinancialDataSensitivity.RESTRICTED
        }
        return mapping.get(field_sensitivity, FinancialDataSensitivity.CONFIDENTIAL)
    
    def get_change_statistics(self) -> Dict[str, Any]:
        """Get change tracking statistics"""
        total_changes = sum(len(changes) for changes in self.pending_changes.values())
        sensitive_changes = 0
        
        for changes in self.pending_changes.values():
            for change in changes:
                if change.field_metadata.sensitivity in [
                    FieldSensitivity.HIGHLY_SENSITIVE,
                    FieldSensitivity.FINANCIAL_CRITICAL,
                    FieldSensitivity.REGULATORY_PROTECTED
                ]:
                    sensitive_changes += 1
        
        return {
            'total_changes_tracked': total_changes,
            'sensitive_changes': sensitive_changes,
            'change_sets_created': len(self.change_sets),
            'fields_registered': len(self.field_registry.field_metadata),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


# Global change tracker instance
_change_tracker: Optional[FinancialChangeTracker] = None


def initialize_financial_change_tracker(field_registry: Optional[FinancialFieldRegistry] = None) -> FinancialChangeTracker:
    """
    Initialize global financial change tracker
    
    Args:
        field_registry: Optional field registry instance
        
    Returns:
        FinancialChangeTracker instance
    """
    global _change_tracker
    _change_tracker = FinancialChangeTracker(field_registry)
    return _change_tracker


def get_financial_change_tracker() -> Optional[FinancialChangeTracker]:
    """Get the global financial change tracker"""
    return _change_tracker


# Convenience functions for common tracking scenarios
async def track_transaction_creation(
    transaction_data: Dict[str, Any],
    user_id: str,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None
) -> List[ChangeEvent]:
    """Track transaction creation"""
    if _change_tracker:
        return _change_tracker.track_entity_changes(
            entity_type="transaction",
            entity_before=None,
            entity_after=transaction_data,
            change_type=ChangeType.CREATE,
            user_id=user_id,
            session_id=session_id,
            request_id=request_id
        )
    return []


async def track_transaction_update(
    before_data: Dict[str, Any],
    after_data: Dict[str, Any],
    user_id: str,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    business_justification: Optional[str] = None
) -> List[ChangeEvent]:
    """Track transaction update"""
    if _change_tracker:
        return _change_tracker.track_entity_changes(
            entity_type="transaction",
            entity_before=before_data,
            entity_after=after_data,
            change_type=ChangeType.UPDATE,
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            business_justification=business_justification
        )
    return []


async def track_transaction_deletion(
    transaction_data: Dict[str, Any],
    user_id: str,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    business_justification: Optional[str] = None
) -> List[ChangeEvent]:
    """Track transaction deletion"""
    if _change_tracker:
        return _change_tracker.track_entity_changes(
            entity_type="transaction",
            entity_before=transaction_data,
            entity_after=None,
            change_type=ChangeType.DELETE,
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            business_justification=business_justification
        )
    return []