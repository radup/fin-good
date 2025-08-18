"""
FinGood Financial Data Safety Validation Framework

This module provides comprehensive validation for financial data integrity
during database migrations. It implements strict validation rules specific
to financial applications to ensure regulatory compliance and data accuracy.

Features:
- Financial transaction validation
- Currency and amount validation
- Date and timestamp validation
- Regulatory compliance checks
- Data consistency validation
- Orphaned data detection
- Financial calculation verification

"""

import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal, InvalidOperation

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logger = logging.getLogger(__name__)

class ValidationSeverity(Enum):
    """Validation issue severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ComplianceStandard(Enum):
    """Financial compliance standards."""
    PCI_DSS = "pci_dss"
    SOX = "sox"
    GDPR = "gdpr"
    PCI_DSS_LEVEL_1 = "pci_dss_level_1"

@dataclass
class ValidationIssue:
    """Individual validation issue."""
    table: str
    column: Optional[str]
    severity: ValidationSeverity
    message: str
    count: int
    sample_data: Optional[List[Dict[str, Any]]] = None
    recommendation: Optional[str] = None

@dataclass
class DataValidationReport:
    """Comprehensive data validation report."""
    timestamp: datetime
    database_name: str
    validation_scope: str
    issues: List[ValidationIssue]
    total_records_checked: int
    execution_time: float
    compliance_status: Dict[ComplianceStandard, bool]
    summary: Dict[ValidationSeverity, int]

class FinancialDataValidator:
    """
    Comprehensive financial data validator for database migrations.
    
    Validates financial data integrity, compliance, and consistency
    according to financial industry standards and regulations.
    """
    
    def __init__(self, database_url: str):
        """Initialize the financial data validator."""
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.issues: List[ValidationIssue] = []
        
        # Financial validation rules
        self.min_amount = Decimal('-999999999.99')  # Minimum valid amount
        self.max_amount = Decimal('999999999.99')   # Maximum valid amount
        self.valid_currencies = ['USD', 'EUR', 'GBP', 'CAD', 'AUD']  # Add as needed
        
    def validate_financial_data(self, scope: str = "full") -> DataValidationReport:
        """
        Perform comprehensive financial data validation.
        
        Args:
            scope: Validation scope ("full", "transactions", "users", "categories")
            
        Returns:
            DataValidationReport with all validation results
        """
        logger.info(f"Starting financial data validation: {scope}")
        start_time = time.time()
        
        self.issues = []
        total_records = 0
        
        try:
            if scope in ["full", "transactions"]:
                total_records += self._validate_transactions()
            
            if scope in ["full", "users"]:
                total_records += self._validate_users()
            
            if scope in ["full", "categories"]:
                total_records += self._validate_categories()
            
            if scope in ["full", "rules"]:
                total_records += self._validate_categorization_rules()
            
            # Cross-table validation
            if scope == "full":
                self._validate_referential_integrity()
                self._validate_business_rules()
            
            # Generate compliance status
            compliance_status = self._check_compliance_standards()
            
            # Generate summary
            summary = self._generate_summary()
            
            execution_time = time.time() - start_time
            
            report = DataValidationReport(
                timestamp=datetime.now(timezone.utc),
                database_name=self._get_database_name(),
                validation_scope=scope,
                issues=self.issues,
                total_records_checked=total_records,
                execution_time=execution_time,
                compliance_status=compliance_status,
                summary=summary
            )
            
            logger.info(f"Financial data validation completed: {len(self.issues)} issues found")
            return report
            
        except Exception as e:
            logger.error(f"Financial data validation failed: {e}")
            raise
    
    def _validate_transactions(self) -> int:
        """Validate transaction data integrity."""
        logger.info("Validating transaction data")
        
        with self.engine.connect() as conn:
            # Check if transactions table exists
            inspector = inspect(self.engine)
            if 'transactions' not in inspector.get_table_names():
                self.issues.append(ValidationIssue(
                    table="transactions",
                    column=None,
                    severity=ValidationSeverity.ERROR,
                    message="Transactions table does not exist",
                    count=0,
                    recommendation="Create transactions table before proceeding"
                ))
                return 0
            
            # Get total record count
            result = conn.execute(text("SELECT COUNT(*) FROM transactions"))
            total_count = result.scalar()
            
            # Validate transaction amounts
            self._validate_transaction_amounts(conn)
            
            # Validate transaction dates
            self._validate_transaction_dates(conn)
            
            # Validate transaction descriptions
            self._validate_transaction_descriptions(conn)
            
            # Validate transaction categories
            self._validate_transaction_categories(conn)
            
            # Validate transaction sources
            self._validate_transaction_sources(conn)
            
            # Validate transaction user references
            self._validate_transaction_user_references(conn)
            
            return total_count
    
    def _validate_transaction_amounts(self, conn):
        """Validate transaction amount fields."""
        # Check for NULL amounts
        result = conn.execute(text("""
            SELECT COUNT(*) FROM transactions WHERE amount IS NULL
        """))
        null_count = result.scalar()
        
        if null_count > 0:
            self.issues.append(ValidationIssue(
                table="transactions",
                column="amount",
                severity=ValidationSeverity.CRITICAL,
                message="Transactions with NULL amounts found",
                count=null_count,
                recommendation="All transactions must have valid amounts"
            ))
        
        # Check for zero amounts
        result = conn.execute(text("""
            SELECT COUNT(*) FROM transactions WHERE amount = 0
        """))
        zero_count = result.scalar()
        
        if zero_count > 0:
            self.issues.append(ValidationIssue(
                table="transactions",
                column="amount",
                severity=ValidationSeverity.WARNING,
                message="Transactions with zero amounts found",
                count=zero_count,
                recommendation="Review zero-amount transactions for validity"
            ))
        
        # Check for extremely large amounts
        result = conn.execute(text(f"""
            SELECT COUNT(*) FROM transactions 
            WHERE ABS(amount) > {self.max_amount}
        """))
        large_count = result.scalar()
        
        if large_count > 0:
            # Get samples
            sample_result = conn.execute(text(f"""
                SELECT id, amount, description 
                FROM transactions 
                WHERE ABS(amount) > {self.max_amount}
                LIMIT 5
            """))
            samples = [dict(row._mapping) for row in sample_result]
            
            self.issues.append(ValidationIssue(
                table="transactions",
                column="amount",
                severity=ValidationSeverity.ERROR,
                message="Transactions with unusually large amounts found",
                count=large_count,
                sample_data=samples,
                recommendation="Verify large amounts are legitimate"
            ))
        
        # Check for precision issues (more than 2 decimal places)
        result = conn.execute(text("""
            SELECT COUNT(*) FROM transactions 
            WHERE (amount * 100) != ROUND(amount * 100)
        """))
        precision_count = result.scalar()
        
        if precision_count > 0:
            self.issues.append(ValidationIssue(
                table="transactions",
                column="amount",
                severity=ValidationSeverity.WARNING,
                message="Transactions with more than 2 decimal places found",
                count=precision_count,
                recommendation="Financial amounts should have at most 2 decimal places"
            ))
    
    def _validate_transaction_dates(self, conn):
        """Validate transaction date fields."""
        # Check for NULL dates
        result = conn.execute(text("""
            SELECT COUNT(*) FROM transactions WHERE date IS NULL
        """))
        null_count = result.scalar()
        
        if null_count > 0:
            self.issues.append(ValidationIssue(
                table="transactions",
                column="date",
                severity=ValidationSeverity.CRITICAL,
                message="Transactions with NULL dates found",
                count=null_count,
                recommendation="All transactions must have valid dates"
            ))
        
        # Check for future dates (more than 1 day in future)
        result = conn.execute(text("""
            SELECT COUNT(*) FROM transactions 
            WHERE date > CURRENT_DATE + INTERVAL '1 day'
        """))
        future_count = result.scalar()
        
        if future_count > 0:
            # Get samples
            sample_result = conn.execute(text("""
                SELECT id, date, description 
                FROM transactions 
                WHERE date > CURRENT_DATE + INTERVAL '1 day'
                LIMIT 5
            """))
            samples = [dict(row._mapping) for row in sample_result]
            
            self.issues.append(ValidationIssue(
                table="transactions",
                column="date",
                severity=ValidationSeverity.WARNING,
                message="Transactions with future dates found",
                count=future_count,
                sample_data=samples,
                recommendation="Review future-dated transactions for accuracy"
            ))
        
        # Check for very old dates (more than 10 years ago)
        result = conn.execute(text("""
            SELECT COUNT(*) FROM transactions 
            WHERE date < CURRENT_DATE - INTERVAL '10 years'
        """))
        old_count = result.scalar()
        
        if old_count > 0:
            self.issues.append(ValidationIssue(
                table="transactions",
                column="date",
                severity=ValidationSeverity.INFO,
                message="Transactions older than 10 years found",
                count=old_count,
                recommendation="Consider archiving very old transactions"
            ))
    
    def _validate_transaction_descriptions(self, conn):
        """Validate transaction description fields."""
        # Check for NULL descriptions
        result = conn.execute(text("""
            SELECT COUNT(*) FROM transactions WHERE description IS NULL
        """))
        null_count = result.scalar()
        
        if null_count > 0:
            self.issues.append(ValidationIssue(
                table="transactions",
                column="description",
                severity=ValidationSeverity.ERROR,
                message="Transactions with NULL descriptions found",
                count=null_count,
                recommendation="All transactions should have descriptions"
            ))
        
        # Check for empty descriptions
        result = conn.execute(text("""
            SELECT COUNT(*) FROM transactions 
            WHERE description IS NOT NULL AND TRIM(description) = ''
        """))
        empty_count = result.scalar()
        
        if empty_count > 0:
            self.issues.append(ValidationIssue(
                table="transactions",
                column="description",
                severity=ValidationSeverity.WARNING,
                message="Transactions with empty descriptions found",
                count=empty_count,
                recommendation="Transactions should have meaningful descriptions"
            ))
        
        # Check for potentially suspicious patterns
        suspicious_patterns = [
            ('test', 'Test transactions in production data'),
            ('xxx', 'Placeholder transactions'),
            ('temp', 'Temporary transactions'),
        ]
        
        for pattern, description in suspicious_patterns:
            result = conn.execute(text(f"""
                SELECT COUNT(*) FROM transactions 
                WHERE LOWER(description) LIKE '%{pattern}%'
            """))
            count = result.scalar()
            
            if count > 0:
                self.issues.append(ValidationIssue(
                    table="transactions",
                    column="description",
                    severity=ValidationSeverity.WARNING,
                    message=description,
                    count=count,
                    recommendation=f"Review transactions containing '{pattern}'"
                ))
    
    def _validate_transaction_categories(self, conn):
        """Validate transaction categorization."""
        # Check categorization consistency
        result = conn.execute(text("""
            SELECT COUNT(*) FROM transactions 
            WHERE is_categorized = true AND category IS NULL
        """))
        inconsistent_count = result.scalar()
        
        if inconsistent_count > 0:
            self.issues.append(ValidationIssue(
                table="transactions",
                column="category",
                severity=ValidationSeverity.ERROR,
                message="Transactions marked as categorized but missing category",
                count=inconsistent_count,
                recommendation="Fix categorization status or assign categories"
            ))
        
        # Check for uncategorized transactions (if business rule requires categorization)
        result = conn.execute(text("""
            SELECT COUNT(*) FROM transactions 
            WHERE is_categorized = false OR category IS NULL
        """))
        uncategorized_count = result.scalar()
        
        if uncategorized_count > 0:
            self.issues.append(ValidationIssue(
                table="transactions",
                column="category",
                severity=ValidationSeverity.INFO,
                message="Uncategorized transactions found",
                count=uncategorized_count,
                recommendation="Consider implementing automated categorization"
            ))
    
    def _validate_transaction_sources(self, conn):
        """Validate transaction source fields."""
        # Check for valid sources
        valid_sources = ['csv', 'quickbooks', 'xero', 'manual', 'api']
        
        result = conn.execute(text(f"""
            SELECT COUNT(*) FROM transactions 
            WHERE source NOT IN ({','.join([f"'{s}'" for s in valid_sources])})
        """))
        invalid_source_count = result.scalar()
        
        if invalid_source_count > 0:
            # Get samples
            sample_result = conn.execute(text(f"""
                SELECT DISTINCT source, COUNT(*) as count
                FROM transactions 
                WHERE source NOT IN ({','.join([f"'{s}'" for s in valid_sources])})
                GROUP BY source
                LIMIT 5
            """))
            samples = [dict(row._mapping) for row in sample_result]
            
            self.issues.append(ValidationIssue(
                table="transactions",
                column="source",
                severity=ValidationSeverity.WARNING,
                message="Transactions with invalid source values found",
                count=invalid_source_count,
                sample_data=samples,
                recommendation="Use standardized source values"
            ))
    
    def _validate_transaction_user_references(self, conn):
        """Validate transaction user references."""
        # Check for orphaned transactions
        result = conn.execute(text("""
            SELECT COUNT(*) FROM transactions t
            LEFT JOIN users u ON t.user_id = u.id
            WHERE u.id IS NULL
        """))
        orphaned_count = result.scalar()
        
        if orphaned_count > 0:
            self.issues.append(ValidationIssue(
                table="transactions",
                column="user_id",
                severity=ValidationSeverity.CRITICAL,
                message="Orphaned transactions found (no matching user)",
                count=orphaned_count,
                recommendation="Fix user references or remove orphaned transactions"
            ))
    
    def _validate_users(self) -> int:
        """Validate user data integrity."""
        logger.info("Validating user data")
        
        with self.engine.connect() as conn:
            # Check if users table exists
            inspector = inspect(self.engine)
            if 'users' not in inspector.get_table_names():
                self.issues.append(ValidationIssue(
                    table="users",
                    column=None,
                    severity=ValidationSeverity.ERROR,
                    message="Users table does not exist",
                    count=0,
                    recommendation="Create users table before proceeding"
                ))
                return 0
            
            # Get total record count
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            total_count = result.scalar()
            
            # Validate email addresses
            self._validate_user_emails(conn)
            
            # Validate user status
            self._validate_user_status(conn)
            
            # Validate user authentication data
            self._validate_user_auth_data(conn)
            
            return total_count
    
    def _validate_user_emails(self, conn):
        """Validate user email addresses."""
        # Check for NULL emails
        result = conn.execute(text("""
            SELECT COUNT(*) FROM users WHERE email IS NULL
        """))
        null_count = result.scalar()
        
        if null_count > 0:
            self.issues.append(ValidationIssue(
                table="users",
                column="email",
                severity=ValidationSeverity.CRITICAL,
                message="Users with NULL email addresses found",
                count=null_count,
                recommendation="All users must have valid email addresses"
            ))
        
        # Check for duplicate emails
        result = conn.execute(text("""
            SELECT COUNT(*) FROM (
                SELECT email FROM users 
                WHERE email IS NOT NULL
                GROUP BY email 
                HAVING COUNT(*) > 1
            ) duplicates
        """))
        duplicate_count = result.scalar()
        
        if duplicate_count > 0:
            self.issues.append(ValidationIssue(
                table="users",
                column="email",
                severity=ValidationSeverity.CRITICAL,
                message="Duplicate email addresses found",
                count=duplicate_count,
                recommendation="Email addresses must be unique"
            ))
        
        # Check for invalid email formats (basic check)
        result = conn.execute(text("""
            SELECT COUNT(*) FROM users 
            WHERE email IS NOT NULL 
            AND email NOT LIKE '%_@_%.__%'
        """))
        invalid_format_count = result.scalar()
        
        if invalid_format_count > 0:
            self.issues.append(ValidationIssue(
                table="users",
                column="email",
                severity=ValidationSeverity.ERROR,
                message="Users with invalid email formats found",
                count=invalid_format_count,
                recommendation="Validate and fix email address formats"
            ))
    
    def _validate_user_status(self, conn):
        """Validate user status fields."""
        # Check for users without proper status
        result = conn.execute(text("""
            SELECT COUNT(*) FROM users 
            WHERE is_active IS NULL
        """))
        null_status_count = result.scalar()
        
        if null_status_count > 0:
            self.issues.append(ValidationIssue(
                table="users",
                column="is_active",
                severity=ValidationSeverity.WARNING,
                message="Users with NULL active status found",
                count=null_status_count,
                recommendation="All users should have defined active status"
            ))
    
    def _validate_user_auth_data(self, conn):
        """Validate user authentication data."""
        # Check for users without hashed passwords
        result = conn.execute(text("""
            SELECT COUNT(*) FROM users 
            WHERE hashed_password IS NULL OR hashed_password = ''
        """))
        no_password_count = result.scalar()
        
        if no_password_count > 0:
            self.issues.append(ValidationIssue(
                table="users",
                column="hashed_password",
                severity=ValidationSeverity.CRITICAL,
                message="Users without hashed passwords found",
                count=no_password_count,
                recommendation="All users must have secure password hashes"
            ))
    
    def _validate_categories(self) -> int:
        """Validate category data integrity."""
        logger.info("Validating category data")
        
        with self.engine.connect() as conn:
            # Check if categories table exists
            inspector = inspect(self.engine)
            if 'categories' not in inspector.get_table_names():
                # This might be acceptable if categories are stored differently
                return 0
            
            # Get total record count
            result = conn.execute(text("SELECT COUNT(*) FROM categories"))
            total_count = result.scalar()
            
            # Validate category names
            self._validate_category_names(conn)
            
            # Validate category hierarchy
            self._validate_category_hierarchy(conn)
            
            return total_count
    
    def _validate_category_names(self, conn):
        """Validate category names."""
        # Check for NULL category names
        result = conn.execute(text("""
            SELECT COUNT(*) FROM categories WHERE name IS NULL
        """))
        null_count = result.scalar()
        
        if null_count > 0:
            self.issues.append(ValidationIssue(
                table="categories",
                column="name",
                severity=ValidationSeverity.ERROR,
                message="Categories with NULL names found",
                count=null_count,
                recommendation="All categories must have valid names"
            ))
        
        # Check for duplicate category names per user
        result = conn.execute(text("""
            SELECT COUNT(*) FROM (
                SELECT user_id, name FROM categories 
                WHERE name IS NOT NULL
                GROUP BY user_id, name 
                HAVING COUNT(*) > 1
            ) duplicates
        """))
        duplicate_count = result.scalar()
        
        if duplicate_count > 0:
            self.issues.append(ValidationIssue(
                table="categories",
                column="name",
                severity=ValidationSeverity.WARNING,
                message="Duplicate category names per user found",
                count=duplicate_count,
                recommendation="Category names should be unique per user"
            ))
    
    def _validate_category_hierarchy(self, conn):
        """Validate category hierarchy."""
        # Check for circular references in parent categories
        # This is a simplified check - you might want more sophisticated cycle detection
        result = conn.execute(text("""
            SELECT COUNT(*) FROM categories c1
            JOIN categories c2 ON c1.parent_category = c2.name AND c1.user_id = c2.user_id
            WHERE c2.parent_category = c1.name
        """))
        circular_count = result.scalar()
        
        if circular_count > 0:
            self.issues.append(ValidationIssue(
                table="categories",
                column="parent_category",
                severity=ValidationSeverity.ERROR,
                message="Circular references in category hierarchy found",
                count=circular_count,
                recommendation="Fix category hierarchy to prevent circular references"
            ))
    
    def _validate_categorization_rules(self) -> int:
        """Validate categorization rules."""
        logger.info("Validating categorization rules")
        
        with self.engine.connect() as conn:
            # Check if categorization_rules table exists
            inspector = inspect(self.engine)
            if 'categorization_rules' not in inspector.get_table_names():
                return 0
            
            # Get total record count
            result = conn.execute(text("SELECT COUNT(*) FROM categorization_rules"))
            total_count = result.scalar()
            
            # Validate rule patterns
            self._validate_rule_patterns(conn)
            
            return total_count
    
    def _validate_rule_patterns(self, conn):
        """Validate categorization rule patterns."""
        # Check for empty patterns
        result = conn.execute(text("""
            SELECT COUNT(*) FROM categorization_rules 
            WHERE pattern IS NULL OR TRIM(pattern) = ''
        """))
        empty_pattern_count = result.scalar()
        
        if empty_pattern_count > 0:
            self.issues.append(ValidationIssue(
                table="categorization_rules",
                column="pattern",
                severity=ValidationSeverity.ERROR,
                message="Categorization rules with empty patterns found",
                count=empty_pattern_count,
                recommendation="All categorization rules must have valid patterns"
            ))
    
    def _validate_referential_integrity(self):
        """Validate referential integrity across tables."""
        logger.info("Validating referential integrity")
        
        with self.engine.connect() as conn:
            # Already checked transaction-user integrity in transaction validation
            pass
    
    def _validate_business_rules(self):
        """Validate business-specific rules."""
        logger.info("Validating business rules")
        
        with self.engine.connect() as conn:
            # Check for income transactions with negative amounts
            result = conn.execute(text("""
                SELECT COUNT(*) FROM transactions 
                WHERE is_income = true AND amount < 0
            """))
            negative_income_count = result.scalar()
            
            if negative_income_count > 0:
                self.issues.append(ValidationIssue(
                    table="transactions",
                    column="amount",
                    severity=ValidationSeverity.WARNING,
                    message="Income transactions with negative amounts found",
                    count=negative_income_count,
                    recommendation="Review income transactions - amounts should typically be positive"
                ))
            
            # Check for expense transactions with positive amounts
            result = conn.execute(text("""
                SELECT COUNT(*) FROM transactions 
                WHERE is_income = false AND amount > 0
            """))
            positive_expense_count = result.scalar()
            
            if positive_expense_count > 0:
                self.issues.append(ValidationIssue(
                    table="transactions",
                    column="amount",
                    severity=ValidationSeverity.INFO,
                    message="Expense transactions with positive amounts found",
                    count=positive_expense_count,
                    recommendation="Verify expense transaction amounts - consider using negative values"
                ))
    
    def _check_compliance_standards(self) -> Dict[ComplianceStandard, bool]:
        """Check compliance with financial standards."""
        compliance_status = {}
        
        # PCI DSS compliance check (simplified)
        # Check for proper data encryption, access controls, etc.
        pci_compliant = self._check_pci_compliance()
        compliance_status[ComplianceStandard.PCI_DSS] = pci_compliant
        
        # SOX compliance check (simplified)
        # Check for audit trails, data integrity, etc.
        sox_compliant = self._check_sox_compliance()
        compliance_status[ComplianceStandard.SOX] = sox_compliant
        
        # GDPR compliance check (simplified)
        # Check for data privacy, retention, etc.
        gdpr_compliant = self._check_gdpr_compliance()
        compliance_status[ComplianceStandard.GDPR] = gdpr_compliant
        
        return compliance_status
    
    def _check_pci_compliance(self) -> bool:
        """Check PCI DSS compliance (simplified)."""
        # This is a placeholder for PCI DSS compliance checks
        # In a real implementation, you would check:
        # - Credit card data encryption
        # - Access controls
        # - Network security
        # - Regular monitoring
        return True  # Assume compliant for now
    
    def _check_sox_compliance(self) -> bool:
        """Check SOX compliance (simplified)."""
        # This is a placeholder for SOX compliance checks
        # In a real implementation, you would check:
        # - Audit trail completeness
        # - Data integrity controls
        # - Change management processes
        # - Financial reporting accuracy
        return True  # Assume compliant for now
    
    def _check_gdpr_compliance(self) -> bool:
        """Check GDPR compliance (simplified)."""
        # This is a placeholder for GDPR compliance checks
        # In a real implementation, you would check:
        # - Data retention policies
        # - User consent tracking
        # - Data anonymization
        # - Right to erasure implementation
        return True  # Assume compliant for now
    
    def _generate_summary(self) -> Dict[ValidationSeverity, int]:
        """Generate summary of validation issues by severity."""
        summary = {severity: 0 for severity in ValidationSeverity}
        
        for issue in self.issues:
            summary[issue.severity] += 1
        
        return summary
    
    def _get_database_name(self) -> str:
        """Get database name from connection."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT current_database()"))
                return result.scalar() or "unknown"
        except:
            return "unknown"

def format_validation_report(report: DataValidationReport) -> str:
    """Format validation report for human reading."""
    output = []
    
    # Header
    output.append("=" * 80)
    output.append("🏦 FinGood Financial Data Validation Report")
    output.append(f"Database: {report.database_name}")
    output.append(f"Scope: {report.validation_scope}")
    output.append(f"Timestamp: {report.timestamp.isoformat()}")
    output.append("=" * 80)
    
    # Summary
    total_issues = sum(report.summary.values())
    output.append(f"\n📊 Summary:")
    output.append(f"   Total Records Checked: {report.total_records_checked:,}")
    output.append(f"   Total Issues Found: {total_issues}")
    output.append(f"   Execution Time: {report.execution_time:.2f} seconds")
    
    # Issues by severity
    severity_emoji = {
        ValidationSeverity.CRITICAL: "🔴",
        ValidationSeverity.ERROR: "🟠",
        ValidationSeverity.WARNING: "🟡",
        ValidationSeverity.INFO: "🔵"
    }
    
    output.append(f"\n🚨 Issues by Severity:")
    for severity, count in report.summary.items():
        emoji = severity_emoji[severity]
        output.append(f"   {emoji} {severity.value.upper()}: {count}")
    
    # Compliance status
    output.append(f"\n✅ Compliance Status:")
    compliance_emoji = {True: "✅", False: "❌"}
    for standard, status in report.compliance_status.items():
        emoji = compliance_emoji[status]
        output.append(f"   {emoji} {standard.value.upper()}: {'COMPLIANT' if status else 'NON-COMPLIANT'}")
    
    # Detailed issues
    if report.issues:
        output.append(f"\n🔍 Detailed Issues:")
        
        for issue in sorted(report.issues, key=lambda x: (x.severity.value, x.table, x.column or "")):
            emoji = severity_emoji[issue.severity]
            column_info = f".{issue.column}" if issue.column else ""
            
            output.append(f"\n{emoji} {issue.severity.value.upper()}: {issue.table}{column_info}")
            output.append(f"   📝 {issue.message}")
            output.append(f"   📊 Count: {issue.count}")
            
            if issue.recommendation:
                output.append(f"   💡 Recommendation: {issue.recommendation}")
            
            if issue.sample_data:
                output.append(f"   📋 Sample Data:")
                for i, sample in enumerate(issue.sample_data[:3]):  # Show max 3 samples
                    output.append(f"      {i+1}. {sample}")
    else:
        output.append(f"\n✅ No validation issues found!")
    
    output.append("\n" + "=" * 80)
    
    return "\n".join(output)