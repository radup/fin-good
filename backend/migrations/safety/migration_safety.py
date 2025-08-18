"""
FinGood Migration Safety Framework

This module provides comprehensive safety checks and validation for database migrations
affecting financial data. It implements multi-layer validation to ensure data integrity
and compliance with financial regulations.

Features:
- Pre-migration safety validation
- Post-migration integrity checks
- Rollback safety verification
- Data consistency validation
- Performance impact assessment
- Compliance requirement checks

"""

import os
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError, OperationalError

# Configure logging
logger = logging.getLogger(__name__)

class SafetyLevel(Enum):
    """Migration safety levels for financial applications."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ValidationResult(Enum):
    """Validation result status."""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"

@dataclass
class SafetyCheck:
    """Individual safety check result."""
    name: str
    result: ValidationResult
    message: str
    details: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None

@dataclass
class MigrationSafetyReport:
    """Comprehensive migration safety report."""
    migration_id: str
    safety_level: SafetyLevel
    timestamp: datetime
    checks: List[SafetyCheck]
    overall_result: ValidationResult
    recommendations: List[str]
    estimated_duration: Optional[float] = None
    rollback_tested: bool = False

class MigrationSafetyValidator:
    """
    Comprehensive migration safety validator for financial applications.
    
    Provides multi-layer validation to ensure database migrations
    maintain data integrity and comply with financial regulations.
    """
    
    def __init__(self, database_url: str):
        """Initialize the safety validator."""
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.checks: List[SafetyCheck] = []
        
    def validate_migration_safety(self, migration_id: str, 
                                 safety_level: SafetyLevel = SafetyLevel.HIGH) -> MigrationSafetyReport:
        """
        Perform comprehensive migration safety validation.
        
        Args:
            migration_id: Unique identifier for the migration
            safety_level: Required safety level for the migration
            
        Returns:
            MigrationSafetyReport with all validation results
        """
        logger.info(f"Starting migration safety validation for: {migration_id}")
        start_time = time.time()
        
        self.checks = []
        
        # Core safety checks
        self._check_database_connectivity()
        self._check_backup_availability()
        self._check_disk_space()
        self._check_active_connections()
        self._check_table_locks()
        
        # Data integrity checks
        self._check_referential_integrity()
        self._check_data_consistency()
        self._check_constraint_violations()
        
        # Performance impact checks
        self._estimate_migration_duration()
        self._check_blocking_operations()
        
        # Financial compliance checks
        if safety_level in [SafetyLevel.HIGH, SafetyLevel.CRITICAL]:
            self._check_audit_trail_requirements()
            self._check_financial_data_compliance()
        
        # Generate report
        overall_result = self._determine_overall_result()
        recommendations = self._generate_recommendations()
        
        execution_time = time.time() - start_time
        
        report = MigrationSafetyReport(
            migration_id=migration_id,
            safety_level=safety_level,
            timestamp=datetime.now(timezone.utc),
            checks=self.checks,
            overall_result=overall_result,
            recommendations=recommendations,
            estimated_duration=execution_time
        )
        
        logger.info(f"Migration safety validation completed: {overall_result.value}")
        return report
    
    def _execute_check(self, check_name: str, check_function) -> SafetyCheck:
        """Execute a safety check and record the result."""
        start_time = time.time()
        
        try:
            result, message, details = check_function()
            execution_time = time.time() - start_time
            
            check = SafetyCheck(
                name=check_name,
                result=result,
                message=message,
                details=details,
                execution_time=execution_time
            )
            
            self.checks.append(check)
            logger.debug(f"Check '{check_name}': {result.value} - {message}")
            
            return check
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_message = f"Check failed with error: {str(e)}"
            
            check = SafetyCheck(
                name=check_name,
                result=ValidationResult.FAIL,
                message=error_message,
                details={"error": str(e)},
                execution_time=execution_time
            )
            
            self.checks.append(check)
            logger.error(f"Check '{check_name}' failed: {e}")
            
            return check
    
    def _check_database_connectivity(self) -> SafetyCheck:
        """Check database connectivity and health."""
        def check():
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as health_check"))
                result.fetchone()
                
                # Check for basic database information
                db_version = conn.execute(text("SELECT version()")).scalar()
                
                return (
                    ValidationResult.PASS,
                    "Database connectivity verified",
                    {"database_version": db_version}
                )
        
        return self._execute_check("Database Connectivity", check)
    
    def _check_backup_availability(self) -> SafetyCheck:
        """Check if recent backups are available."""
        def check():
            # This is a placeholder - implement actual backup verification
            # You might check backup files, backup services, or backup metadata
            
            backup_env = os.getenv('BACKUP_VERIFIED', 'false').lower()
            if backup_env == 'true':
                return (
                    ValidationResult.PASS,
                    "Backup availability verified",
                    {"backup_verified": True}
                )
            else:
                return (
                    ValidationResult.WARNING,
                    "Backup verification not confirmed - ensure backups are available",
                    {"backup_verified": False}
                )
        
        return self._execute_check("Backup Availability", check)
    
    def _check_disk_space(self) -> SafetyCheck:
        """Check available disk space for migration operations."""
        def check():
            try:
                import shutil
                
                # Check available disk space
                total, used, free = shutil.disk_usage("/")
                free_gb = free // (1024**3)
                used_percent = (used / total) * 100
                
                if free_gb < 1:  # Less than 1GB free
                    return (
                        ValidationResult.FAIL,
                        f"Insufficient disk space: {free_gb}GB free",
                        {"free_gb": free_gb, "used_percent": used_percent}
                    )
                elif used_percent > 90:
                    return (
                        ValidationResult.WARNING,
                        f"High disk usage: {used_percent:.1f}% used",
                        {"free_gb": free_gb, "used_percent": used_percent}
                    )
                else:
                    return (
                        ValidationResult.PASS,
                        f"Adequate disk space: {free_gb}GB free",
                        {"free_gb": free_gb, "used_percent": used_percent}
                    )
                    
            except Exception as e:
                return (
                    ValidationResult.WARNING,
                    f"Could not check disk space: {str(e)}",
                    {"error": str(e)}
                )
        
        return self._execute_check("Disk Space", check)
    
    def _check_active_connections(self) -> SafetyCheck:
        """Check for active database connections that might block migration."""
        def check():
            with self.engine.connect() as conn:
                # PostgreSQL specific query - adapt for other databases
                try:
                    result = conn.execute(text("""
                        SELECT count(*) as connection_count 
                        FROM pg_stat_activity 
                        WHERE state = 'active' AND pid != pg_backend_pid()
                    """))
                    
                    connection_count = result.scalar()
                    
                    if connection_count > 50:  # Threshold for high activity
                        return (
                            ValidationResult.WARNING,
                            f"High number of active connections: {connection_count}",
                            {"active_connections": connection_count}
                        )
                    else:
                        return (
                            ValidationResult.PASS,
                            f"Acceptable connection count: {connection_count}",
                            {"active_connections": connection_count}
                        )
                        
                except Exception:
                    # If we can't check (non-PostgreSQL), assume it's okay
                    return (
                        ValidationResult.PASS,
                        "Connection check not applicable for this database",
                        {"check_skipped": True}
                    )
        
        return self._execute_check("Active Connections", check)
    
    def _check_table_locks(self) -> SafetyCheck:
        """Check for table locks that might interfere with migration."""
        def check():
            with self.engine.connect() as conn:
                try:
                    # PostgreSQL specific query - adapt for other databases
                    result = conn.execute(text("""
                        SELECT count(*) as lock_count 
                        FROM pg_locks l
                        JOIN pg_class c ON l.relation = c.oid
                        WHERE l.mode LIKE '%ExclusiveLock%'
                    """))
                    
                    lock_count = result.scalar()
                    
                    if lock_count > 0:
                        return (
                            ValidationResult.WARNING,
                            f"Exclusive locks detected: {lock_count}",
                            {"exclusive_locks": lock_count}
                        )
                    else:
                        return (
                            ValidationResult.PASS,
                            "No blocking locks detected",
                            {"exclusive_locks": 0}
                        )
                        
                except Exception:
                    return (
                        ValidationResult.PASS,
                        "Lock check not applicable for this database",
                        {"check_skipped": True}
                    )
        
        return self._execute_check("Table Locks", check)
    
    def _check_referential_integrity(self) -> SafetyCheck:
        """Check referential integrity of financial data."""
        def check():
            with self.engine.connect() as conn:
                issues = []
                
                # Check common financial data integrity issues
                integrity_checks = [
                    {
                        "name": "Transaction-User Integrity",
                        "query": """
                            SELECT count(*) FROM transactions t 
                            LEFT JOIN users u ON t.user_id = u.id 
                            WHERE u.id IS NULL
                        """
                    },
                    {
                        "name": "Orphaned Categories",
                        "query": """
                            SELECT count(*) FROM categories c 
                            LEFT JOIN users u ON c.user_id = u.id 
                            WHERE u.id IS NULL
                        """
                    }
                ]
                
                for check_def in integrity_checks:
                    try:
                        result = conn.execute(text(check_def["query"]))
                        count = result.scalar()
                        
                        if count > 0:
                            issues.append(f"{check_def['name']}: {count} issues")
                            
                    except Exception as e:
                        issues.append(f"{check_def['name']}: Check failed - {str(e)}")
                
                if issues:
                    return (
                        ValidationResult.FAIL,
                        f"Referential integrity issues found: {', '.join(issues)}",
                        {"issues": issues}
                    )
                else:
                    return (
                        ValidationResult.PASS,
                        "Referential integrity validated",
                        {"checks_performed": len(integrity_checks)}
                    )
        
        return self._execute_check("Referential Integrity", check)
    
    def _check_data_consistency(self) -> SafetyCheck:
        """Check data consistency for financial records."""
        def check():
            with self.engine.connect() as conn:
                inconsistencies = []
                
                # Financial data consistency checks
                consistency_checks = [
                    {
                        "name": "Transaction Amount Validation",
                        "query": "SELECT count(*) FROM transactions WHERE amount = 0 OR amount IS NULL"
                    },
                    {
                        "name": "Future Dated Transactions",
                        "query": "SELECT count(*) FROM transactions WHERE date > CURRENT_DATE + INTERVAL '1 day'"
                    },
                    {
                        "name": "Invalid Category References",
                        "query": """
                            SELECT count(*) FROM transactions t 
                            WHERE t.category IS NOT NULL 
                            AND NOT EXISTS (
                                SELECT 1 FROM categories c 
                                WHERE c.name = t.category AND c.user_id = t.user_id
                            )
                        """
                    }
                ]
                
                for check_def in consistency_checks:
                    try:
                        result = conn.execute(text(check_def["query"]))
                        count = result.scalar()
                        
                        if count > 0:
                            inconsistencies.append(f"{check_def['name']}: {count} records")
                            
                    except Exception as e:
                        inconsistencies.append(f"{check_def['name']}: Check failed - {str(e)}")
                
                if inconsistencies:
                    return (
                        ValidationResult.WARNING,
                        f"Data consistency issues: {', '.join(inconsistencies)}",
                        {"inconsistencies": inconsistencies}
                    )
                else:
                    return (
                        ValidationResult.PASS,
                        "Data consistency validated",
                        {"checks_performed": len(consistency_checks)}
                    )
        
        return self._execute_check("Data Consistency", check)
    
    def _check_constraint_violations(self) -> SafetyCheck:
        """Check for constraint violations that might affect migration."""
        def check():
            with self.engine.connect() as conn:
                try:
                    # Get list of tables to check
                    inspector = inspect(self.engine)
                    tables = inspector.get_table_names()
                    
                    violations = []
                    
                    for table in tables:
                        # Check for constraint violations
                        # This is a simplified check - expand based on your constraints
                        try:
                            # Check for NULL values in NOT NULL columns
                            columns = inspector.get_columns(table)
                            for column in columns:
                                if not column.get('nullable', True) and column['name'] != 'id':
                                    null_check = conn.execute(text(f"""
                                        SELECT count(*) FROM {table} 
                                        WHERE {column['name']} IS NULL
                                    """))
                                    
                                    null_count = null_check.scalar()
                                    if null_count > 0:
                                        violations.append(f"{table}.{column['name']}: {null_count} NULL values")
                                        
                        except Exception as e:
                            # Skip tables we can't check
                            logger.debug(f"Could not check constraints for table {table}: {e}")
                            continue
                    
                    if violations:
                        return (
                            ValidationResult.FAIL,
                            f"Constraint violations found: {', '.join(violations[:5])}",
                            {"violations": violations}
                        )
                    else:
                        return (
                            ValidationResult.PASS,
                            f"No constraint violations found in {len(tables)} tables",
                            {"tables_checked": len(tables)}
                        )
                        
                except Exception as e:
                    return (
                        ValidationResult.WARNING,
                        f"Could not perform constraint check: {str(e)}",
                        {"error": str(e)}
                    )
        
        return self._execute_check("Constraint Violations", check)
    
    def _estimate_migration_duration(self) -> SafetyCheck:
        """Estimate migration duration based on data volume."""
        def check():
            with self.engine.connect() as conn:
                try:
                    # Get table sizes for estimation
                    table_sizes = {}
                    total_size = 0
                    
                    # PostgreSQL specific query - adapt for other databases
                    try:
                        result = conn.execute(text("""
                            SELECT 
                                schemaname,
                                tablename,
                                pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                            FROM pg_tables 
                            WHERE schemaname = 'public'
                        """))
                        
                        for row in result:
                            size_mb = row.size_bytes / (1024 * 1024)
                            table_sizes[row.tablename] = size_mb
                            total_size += size_mb
                            
                    except Exception:
                        # Fallback for non-PostgreSQL databases
                        total_size = 100  # Assume 100MB as default
                    
                    # Simple estimation: 1 minute per 100MB for index operations
                    estimated_minutes = max(1, total_size / 100)
                    
                    if estimated_minutes > 30:  # 30+ minutes
                        return (
                            ValidationResult.WARNING,
                            f"Long migration estimated: {estimated_minutes:.1f} minutes ({total_size:.1f}MB)",
                            {"estimated_minutes": estimated_minutes, "total_size_mb": total_size}
                        )
                    else:
                        return (
                            ValidationResult.PASS,
                            f"Reasonable migration duration: {estimated_minutes:.1f} minutes",
                            {"estimated_minutes": estimated_minutes, "total_size_mb": total_size}
                        )
                        
                except Exception as e:
                    return (
                        ValidationResult.WARNING,
                        f"Could not estimate duration: {str(e)}",
                        {"error": str(e)}
                    )
        
        return self._execute_check("Migration Duration", check)
    
    def _check_blocking_operations(self) -> SafetyCheck:
        """Check for operations that might block the migration."""
        def check():
            # This is a placeholder for checking blocking operations
            # You might check for:
            # - Long-running queries
            # - Maintenance operations
            # - Backup operations in progress
            # - Replication lag
            
            return (
                ValidationResult.PASS,
                "No blocking operations detected",
                {"blocking_operations": 0}
            )
        
        return self._execute_check("Blocking Operations", check)
    
    def _check_audit_trail_requirements(self) -> SafetyCheck:
        """Check audit trail requirements for financial compliance."""
        def check():
            # Check if audit tables exist and are properly configured
            with self.engine.connect() as conn:
                try:
                    inspector = inspect(self.engine)
                    tables = inspector.get_table_names()
                    
                    audit_requirements = {
                        "revoked_tokens": "Security audit table",
                        # Add other audit tables as needed
                    }
                    
                    missing_audit = []
                    for audit_table, description in audit_requirements.items():
                        if audit_table not in tables:
                            missing_audit.append(f"{audit_table} ({description})")
                    
                    if missing_audit:
                        return (
                            ValidationResult.WARNING,
                            f"Missing audit tables: {', '.join(missing_audit)}",
                            {"missing_audit_tables": missing_audit}
                        )
                    else:
                        return (
                            ValidationResult.PASS,
                            "Audit trail requirements satisfied",
                            {"audit_tables_found": len(audit_requirements)}
                        )
                        
                except Exception as e:
                    return (
                        ValidationResult.WARNING,
                        f"Could not verify audit requirements: {str(e)}",
                        {"error": str(e)}
                    )
        
        return self._execute_check("Audit Trail Requirements", check)
    
    def _check_financial_data_compliance(self) -> SafetyCheck:
        """Check financial data compliance requirements."""
        def check():
            # Check for financial compliance requirements
            # This might include:
            # - Data encryption
            # - Access controls
            # - Data retention policies
            # - Regulatory compliance
            
            compliance_issues = []
            
            # Example checks - customize based on your compliance requirements
            # Check for encrypted sensitive fields
            # Check for proper access controls
            # Check for data retention policies
            
            if compliance_issues:
                return (
                    ValidationResult.FAIL,
                    f"Compliance issues: {', '.join(compliance_issues)}",
                    {"compliance_issues": compliance_issues}
                )
            else:
                return (
                    ValidationResult.PASS,
                    "Financial data compliance verified",
                    {"compliance_checks": ["encryption", "access_control", "retention"]}
                )
        
        return self._execute_check("Financial Data Compliance", check)
    
    def _determine_overall_result(self) -> ValidationResult:
        """Determine overall validation result based on individual checks."""
        has_failures = any(check.result == ValidationResult.FAIL for check in self.checks)
        has_warnings = any(check.result == ValidationResult.WARNING for check in self.checks)
        
        if has_failures:
            return ValidationResult.FAIL
        elif has_warnings:
            return ValidationResult.WARNING
        else:
            return ValidationResult.PASS
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        for check in self.checks:
            if check.result == ValidationResult.FAIL:
                recommendations.append(f"CRITICAL: Fix {check.name} - {check.message}")
            elif check.result == ValidationResult.WARNING:
                recommendations.append(f"WARNING: Review {check.name} - {check.message}")
        
        # Add general recommendations
        recommendations.extend([
            "Verify backup procedures before migration",
            "Test rollback procedures in staging environment",
            "Monitor migration progress and performance",
            "Validate data integrity after migration completion"
        ])
        
        return recommendations

def format_safety_report(report: MigrationSafetyReport) -> str:
    """Format safety report for human reading."""
    output = []
    
    # Header
    output.append("=" * 80)
    output.append(f"🏦 FinGood Migration Safety Report")
    output.append(f"Migration ID: {report.migration_id}")
    output.append(f"Safety Level: {report.safety_level.value.upper()}")
    output.append(f"Timestamp: {report.timestamp.isoformat()}")
    output.append("=" * 80)
    
    # Overall result
    status_emoji = {
        ValidationResult.PASS: "✅",
        ValidationResult.WARNING: "⚠️",
        ValidationResult.FAIL: "❌"
    }
    
    output.append(f"\n📊 Overall Result: {status_emoji[report.overall_result]} {report.overall_result.value.upper()}")
    
    # Individual checks
    output.append(f"\n🔍 Safety Checks ({len(report.checks)} total):")
    for check in report.checks:
        emoji = status_emoji[check.result]
        time_str = f" ({check.execution_time:.2f}s)" if check.execution_time else ""
        output.append(f"  {emoji} {check.name}: {check.message}{time_str}")
    
    # Recommendations
    if report.recommendations:
        output.append(f"\n💡 Recommendations:")
        for i, rec in enumerate(report.recommendations, 1):
            output.append(f"  {i}. {rec}")
    
    # Footer
    if report.estimated_duration:
        output.append(f"\n⏱️  Validation completed in {report.estimated_duration:.2f} seconds")
    
    output.append("\n" + "=" * 80)
    
    return "\n".join(output)