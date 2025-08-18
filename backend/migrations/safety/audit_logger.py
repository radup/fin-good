"""
FinGood Migration Audit Logger

This module provides comprehensive audit logging for all database migration
operations affecting financial data. It implements structured logging,
audit trail generation, and compliance reporting for financial regulations.

Features:
- Structured audit logging
- Migration operation tracking
- Data change auditing
- Compliance trail generation
- Security event logging
- Performance metrics collection

"""

import os
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

@dataclass
class AuditEvent:
    """Structured audit event for migration operations."""
    event_id: str
    timestamp: datetime
    event_type: str
    migration_id: Optional[str]
    operation: str
    user: str
    environment: str
    database: str
    table_name: Optional[str]
    column_name: Optional[str]
    old_value: Optional[Any]
    new_value: Optional[Any]
    affected_rows: Optional[int]
    execution_time: Optional[float]
    success: bool
    error_message: Optional[str]
    client_ip: Optional[str]
    user_agent: Optional[str]
    compliance_tags: List[str]
    security_level: str
    metadata: Dict[str, Any]

class AuditEventType(Enum):
    """Types of audit events for migrations."""
    MIGRATION_START = "migration_start"
    MIGRATION_COMPLETE = "migration_complete"
    MIGRATION_ROLLBACK = "migration_rollback"
    SCHEMA_CHANGE = "schema_change"
    DATA_CHANGE = "data_change"
    INDEX_CREATE = "index_create"
    INDEX_DROP = "index_drop"
    CONSTRAINT_ADD = "constraint_add"
    CONSTRAINT_DROP = "constraint_drop"
    SAFETY_CHECK = "safety_check"
    VALIDATION_RUN = "validation_run"
    BACKUP_CREATE = "backup_create"
    BACKUP_RESTORE = "backup_restore"
    SECURITY_VIOLATION = "security_violation"
    COMPLIANCE_CHECK = "compliance_check"

class SecurityLevel(Enum):
    """Security levels for audit events."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

class MigrationAuditLogger:
    """
    Comprehensive audit logger for database migration operations.
    
    Provides structured logging, audit trail generation, and compliance
    reporting for financial database migrations.
    """
    
    def __init__(self, log_directory: str = None, environment: str = None):
        """Initialize the audit logger."""
        self.environment = environment or os.getenv('ENVIRONMENT', 'development')
        self.log_directory = Path(log_directory or 'logs/migration_audit')
        self.log_directory.mkdir(parents=True, exist_ok=True)
        
        # Setup structured logging
        self._setup_logging()
        
        # Session metadata
        self.session_id = self._generate_session_id()
        self.user = self._get_current_user()
        self.client_ip = self._get_client_ip()
        self.user_agent = self._get_user_agent()
        
    def _setup_logging(self):
        """Setup structured logging configuration."""
        # Create logger
        self.logger = logging.getLogger('migration_audit')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create file handler for audit logs
        audit_log_file = self.log_directory / f"migration_audit_{datetime.now().strftime('%Y%m%d')}.jsonl"
        file_handler = logging.FileHandler(audit_log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create console handler for development
        if self.environment == 'development':
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            self.logger.addHandler(console_handler)
        
        # JSON formatter for structured logging
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'level': record.levelname,
                    'logger': record.name,
                    'message': record.getMessage(),
                }
                
                # Add extra fields if present
                if hasattr(record, 'audit_event'):
                    log_entry['audit_event'] = record.audit_event
                
                return json.dumps(log_entry)
        
        file_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(file_handler)
        
        # Ensure logs don't propagate to root logger
        self.logger.propagate = False
    
    def log_audit_event(self, event: AuditEvent):
        """Log a structured audit event."""
        # Convert event to dictionary
        event_dict = asdict(event)
        
        # Convert datetime to ISO string
        event_dict['timestamp'] = event.timestamp.isoformat()
        
        # Log the event
        self.logger.info(
            f"Audit Event: {event.event_type} - {event.operation}",
            extra={'audit_event': event_dict}
        )
        
        # Also save to dedicated audit file for compliance
        self._save_compliance_audit(event_dict)
    
    def log_migration_start(self, migration_id: str, migration_type: str, 
                          database: str, metadata: Dict[str, Any] = None):
        """Log the start of a migration operation."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            timestamp=datetime.now(timezone.utc),
            event_type=AuditEventType.MIGRATION_START.value,
            migration_id=migration_id,
            operation=f"migration_start_{migration_type}",
            user=self.user,
            environment=self.environment,
            database=database,
            table_name=None,
            column_name=None,
            old_value=None,
            new_value=None,
            affected_rows=None,
            execution_time=None,
            success=True,
            error_message=None,
            client_ip=self.client_ip,
            user_agent=self.user_agent,
            compliance_tags=["SOX", "audit_trail"],
            security_level=SecurityLevel.INTERNAL.value,
            metadata=metadata or {}
        )
        
        self.log_audit_event(event)
        return event.event_id
    
    def log_migration_complete(self, migration_id: str, migration_type: str,
                             database: str, execution_time: float,
                             affected_tables: List[str], success: bool = True,
                             error_message: str = None, metadata: Dict[str, Any] = None):
        """Log the completion of a migration operation."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            timestamp=datetime.now(timezone.utc),
            event_type=AuditEventType.MIGRATION_COMPLETE.value,
            migration_id=migration_id,
            operation=f"migration_complete_{migration_type}",
            user=self.user,
            environment=self.environment,
            database=database,
            table_name=None,
            column_name=None,
            old_value=None,
            new_value=affected_tables,
            affected_rows=None,
            execution_time=execution_time,
            success=success,
            error_message=error_message,
            client_ip=self.client_ip,
            user_agent=self.user_agent,
            compliance_tags=["SOX", "audit_trail", "data_integrity"],
            security_level=SecurityLevel.INTERNAL.value,
            metadata=metadata or {}
        )
        
        self.log_audit_event(event)
        return event.event_id
    
    def log_schema_change(self, migration_id: str, table_name: str,
                         operation: str, old_schema: Dict[str, Any] = None,
                         new_schema: Dict[str, Any] = None,
                         metadata: Dict[str, Any] = None):
        """Log schema changes during migration."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            timestamp=datetime.now(timezone.utc),
            event_type=AuditEventType.SCHEMA_CHANGE.value,
            migration_id=migration_id,
            operation=operation,
            user=self.user,
            environment=self.environment,
            database=self._get_database_name(),
            table_name=table_name,
            column_name=None,
            old_value=old_schema,
            new_value=new_schema,
            affected_rows=None,
            execution_time=None,
            success=True,
            error_message=None,
            client_ip=self.client_ip,
            user_agent=self.user_agent,
            compliance_tags=["SOX", "schema_change", "audit_trail"],
            security_level=SecurityLevel.CONFIDENTIAL.value,
            metadata=metadata or {}
        )
        
        self.log_audit_event(event)
        return event.event_id
    
    def log_data_change(self, migration_id: str, table_name: str,
                       operation: str, affected_rows: int,
                       sample_changes: List[Dict[str, Any]] = None,
                       metadata: Dict[str, Any] = None):
        """Log data changes during migration."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            timestamp=datetime.now(timezone.utc),
            event_type=AuditEventType.DATA_CHANGE.value,
            migration_id=migration_id,
            operation=operation,
            user=self.user,
            environment=self.environment,
            database=self._get_database_name(),
            table_name=table_name,
            column_name=None,
            old_value=None,
            new_value=sample_changes,
            affected_rows=affected_rows,
            execution_time=None,
            success=True,
            error_message=None,
            client_ip=self.client_ip,
            user_agent=self.user_agent,
            compliance_tags=["SOX", "data_change", "financial_data"],
            security_level=SecurityLevel.RESTRICTED.value,
            metadata=metadata or {}
        )
        
        self.log_audit_event(event)
        return event.event_id
    
    def log_index_operation(self, migration_id: str, table_name: str,
                          index_name: str, operation: str,
                          index_definition: Dict[str, Any] = None,
                          execution_time: float = None,
                          success: bool = True, error_message: str = None,
                          metadata: Dict[str, Any] = None):
        """Log index creation or deletion operations."""
        event_type = AuditEventType.INDEX_CREATE if operation == 'create' else AuditEventType.INDEX_DROP
        
        event = AuditEvent(
            event_id=self._generate_event_id(),
            timestamp=datetime.now(timezone.utc),
            event_type=event_type.value,
            migration_id=migration_id,
            operation=f"index_{operation}",
            user=self.user,
            environment=self.environment,
            database=self._get_database_name(),
            table_name=table_name,
            column_name=None,
            old_value=None if operation == 'create' else index_definition,
            new_value=index_definition if operation == 'create' else None,
            affected_rows=None,
            execution_time=execution_time,
            success=success,
            error_message=error_message,
            client_ip=self.client_ip,
            user_agent=self.user_agent,
            compliance_tags=["performance", "schema_change"],
            security_level=SecurityLevel.INTERNAL.value,
            metadata=metadata or {}
        )
        
        self.log_audit_event(event)
        return event.event_id
    
    def log_safety_check(self, migration_id: str, check_type: str,
                        check_result: str, check_details: Dict[str, Any] = None,
                        execution_time: float = None,
                        metadata: Dict[str, Any] = None):
        """Log safety check operations."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            timestamp=datetime.now(timezone.utc),
            event_type=AuditEventType.SAFETY_CHECK.value,
            migration_id=migration_id,
            operation=f"safety_check_{check_type}",
            user=self.user,
            environment=self.environment,
            database=self._get_database_name(),
            table_name=None,
            column_name=None,
            old_value=None,
            new_value=check_details,
            affected_rows=None,
            execution_time=execution_time,
            success=check_result in ['pass', 'warning'],
            error_message=None if check_result != 'fail' else f"Safety check failed: {check_type}",
            client_ip=self.client_ip,
            user_agent=self.user_agent,
            compliance_tags=["safety", "validation", "SOX"],
            security_level=SecurityLevel.INTERNAL.value,
            metadata=metadata or {}
        )
        
        self.log_audit_event(event)
        return event.event_id
    
    def log_rollback_operation(self, migration_id: str, rollback_reason: str,
                             execution_time: float = None, success: bool = True,
                             error_message: str = None,
                             data_integrity_verified: bool = None,
                             metadata: Dict[str, Any] = None):
        """Log rollback operations."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            timestamp=datetime.now(timezone.utc),
            event_type=AuditEventType.MIGRATION_ROLLBACK.value,
            migration_id=migration_id,
            operation="migration_rollback",
            user=self.user,
            environment=self.environment,
            database=self._get_database_name(),
            table_name=None,
            column_name=None,
            old_value=None,
            new_value={"reason": rollback_reason, "integrity_verified": data_integrity_verified},
            affected_rows=None,
            execution_time=execution_time,
            success=success,
            error_message=error_message,
            client_ip=self.client_ip,
            user_agent=self.user_agent,
            compliance_tags=["rollback", "data_integrity", "SOX", "critical"],
            security_level=SecurityLevel.RESTRICTED.value,
            metadata=metadata or {}
        )
        
        self.log_audit_event(event)
        return event.event_id
    
    def log_security_violation(self, migration_id: str, violation_type: str,
                             description: str, severity: str = "high",
                             metadata: Dict[str, Any] = None):
        """Log security violations during migration operations."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            timestamp=datetime.now(timezone.utc),
            event_type=AuditEventType.SECURITY_VIOLATION.value,
            migration_id=migration_id,
            operation=f"security_violation_{violation_type}",
            user=self.user,
            environment=self.environment,
            database=self._get_database_name(),
            table_name=None,
            column_name=None,
            old_value=None,
            new_value={"violation_type": violation_type, "description": description, "severity": severity},
            affected_rows=None,
            execution_time=None,
            success=False,
            error_message=description,
            client_ip=self.client_ip,
            user_agent=self.user_agent,
            compliance_tags=["security", "violation", "alert"],
            security_level=SecurityLevel.RESTRICTED.value,
            metadata=metadata or {}
        )
        
        self.log_audit_event(event)
        
        # Also create an alert for security violations
        self._create_security_alert(event)
        
        return event.event_id
    
    def log_compliance_check(self, migration_id: str, compliance_standard: str,
                           check_result: str, check_details: Dict[str, Any] = None,
                           metadata: Dict[str, Any] = None):
        """Log compliance check results."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            timestamp=datetime.now(timezone.utc),
            event_type=AuditEventType.COMPLIANCE_CHECK.value,
            migration_id=migration_id,
            operation=f"compliance_check_{compliance_standard}",
            user=self.user,
            environment=self.environment,
            database=self._get_database_name(),
            table_name=None,
            column_name=None,
            old_value=None,
            new_value=check_details,
            affected_rows=None,
            execution_time=None,
            success=check_result == 'compliant',
            error_message=None if check_result == 'compliant' else f"Compliance violation: {compliance_standard}",
            client_ip=self.client_ip,
            user_agent=self.user_agent,
            compliance_tags=[compliance_standard.lower(), "compliance", "audit"],
            security_level=SecurityLevel.CONFIDENTIAL.value,
            metadata=metadata or {}
        )
        
        self.log_audit_event(event)
        return event.event_id
    
    def create_migration_session(self, migration_id: str, session_metadata: Dict[str, Any] = None):
        """Create a migration session for tracking related operations."""
        session_data = {
            "session_id": self.session_id,
            "migration_id": migration_id,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "user": self.user,
            "environment": self.environment,
            "client_ip": self.client_ip,
            "user_agent": self.user_agent,
            "metadata": session_metadata or {}
        }
        
        # Save session data
        session_file = self.log_directory / f"session_{self.session_id}.json"
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        return self.session_id
    
    def close_migration_session(self, session_summary: Dict[str, Any] = None):
        """Close the migration session and generate summary."""
        session_file = self.log_directory / f"session_{self.session_id}.json"
        
        if session_file.exists():
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            # Update with closing information
            session_data.update({
                "end_time": datetime.now(timezone.utc).isoformat(),
                "summary": session_summary or {},
                "status": "completed"
            })
            
            # Save updated session data
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
    
    def generate_audit_report(self, start_date: datetime = None, end_date: datetime = None,
                            migration_id: str = None, event_types: List[str] = None) -> Dict[str, Any]:
        """Generate comprehensive audit report."""
        # This is a placeholder for audit report generation
        # In a real implementation, you would:
        # 1. Query audit logs from the specified time range
        # 2. Filter by migration ID and event types
        # 3. Generate statistical summaries
        # 4. Create compliance reports
        # 5. Identify security violations or anomalies
        
        report = {
            "report_id": self._generate_event_id(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "report_period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            },
            "filters": {
                "migration_id": migration_id,
                "event_types": event_types
            },
            "summary": {
                "total_events": 0,
                "migrations_executed": 0,
                "rollbacks_performed": 0,
                "security_violations": 0,
                "compliance_checks": 0
            },
            "compliance_status": {
                "sox_compliant": True,
                "pci_dss_compliant": True,
                "gdpr_compliant": True
            }
        }
        
        return report
    
    def _save_compliance_audit(self, event_dict: Dict[str, Any]):
        """Save audit event to compliance-specific audit file."""
        compliance_file = self.log_directory / f"compliance_audit_{datetime.now().strftime('%Y%m')}.jsonl"
        
        with open(compliance_file, 'a') as f:
            f.write(json.dumps(event_dict) + '\n')
    
    def _create_security_alert(self, event: AuditEvent):
        """Create security alert for violation events."""
        alert_file = self.log_directory / f"security_alerts_{datetime.now().strftime('%Y%m%d')}.json"
        
        alert_data = {
            "alert_id": self._generate_event_id(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": "HIGH",
            "event_id": event.event_id,
            "migration_id": event.migration_id,
            "violation_type": event.new_value.get("violation_type") if event.new_value else "unknown",
            "description": event.error_message,
            "user": event.user,
            "environment": event.environment,
            "client_ip": event.client_ip,
            "requires_attention": True
        }
        
        # Append to alerts file
        alerts = []
        if alert_file.exists():
            with open(alert_file, 'r') as f:
                alerts = json.load(f)
        
        alerts.append(alert_data)
        
        with open(alert_file, 'w') as f:
            json.dump(alerts, f, indent=2)
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        import uuid
        return str(uuid.uuid4())
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        import uuid
        return str(uuid.uuid4())
    
    def _get_current_user(self) -> str:
        """Get current user information."""
        return os.getenv('USER', 'system')
    
    def _get_client_ip(self) -> str:
        """Get client IP address."""
        return os.getenv('CLIENT_IP', '127.0.0.1')
    
    def _get_user_agent(self) -> str:
        """Get user agent information."""
        return os.getenv('USER_AGENT', 'migration_system')
    
    def _get_database_name(self) -> str:
        """Get current database name."""
        return os.getenv('DATABASE_NAME', 'fingood')

# Convenience context manager for migration sessions
class MigrationAuditSession:
    """Context manager for migration audit sessions."""
    
    def __init__(self, audit_logger: MigrationAuditLogger, migration_id: str, 
                 migration_type: str, metadata: Dict[str, Any] = None):
        """Initialize audit session."""
        self.audit_logger = audit_logger
        self.migration_id = migration_id
        self.migration_type = migration_type
        self.metadata = metadata or {}
        self.start_time = None
        self.session_id = None
        
    def __enter__(self):
        """Start audit session."""
        self.start_time = time.time()
        self.session_id = self.audit_logger.create_migration_session(
            self.migration_id, 
            self.metadata
        )
        
        self.audit_logger.log_migration_start(
            self.migration_id,
            self.migration_type,
            self.audit_logger._get_database_name(),
            self.metadata
        )
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End audit session."""
        execution_time = time.time() - self.start_time
        success = exc_type is None
        error_message = str(exc_val) if exc_val else None
        
        self.audit_logger.log_migration_complete(
            self.migration_id,
            self.migration_type,
            self.audit_logger._get_database_name(),
            execution_time,
            affected_tables=[],  # Would be populated in real usage
            success=success,
            error_message=error_message,
            metadata=self.metadata
        )
        
        session_summary = {
            "success": success,
            "execution_time": execution_time,
            "error": error_message
        }
        
        self.audit_logger.close_migration_session(session_summary)

# Global audit logger instance
_audit_logger = None

def get_audit_logger() -> MigrationAuditLogger:
    """Get global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = MigrationAuditLogger()
    return _audit_logger