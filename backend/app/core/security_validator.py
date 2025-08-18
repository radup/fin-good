"""
Security Configuration Validator for FinGood Financial Application

Validates security configuration settings to ensure compliance with
financial application security requirements and regulatory standards.

CRITICAL SECURITY: This validator ensures all security configurations
meet the minimum requirements for financial data protection.
"""

from typing import List, Dict, Optional, Tuple
import re
import urllib.parse
from dataclasses import dataclass
from enum import Enum

from app.core.logging_config import get_logger, LogCategory


class SecurityLevel(Enum):
    """Security levels for different deployment environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Represents a security validation issue."""
    severity: ValidationSeverity
    category: str
    message: str
    recommendation: str
    setting_name: Optional[str] = None


class SecurityConfigValidator:
    """
    Comprehensive Security Configuration Validator
    
    Validates all security-related configuration settings to ensure
    they meet financial application security requirements.
    """
    
    def __init__(self, security_level: SecurityLevel = SecurityLevel.PRODUCTION):
        self.security_level = security_level
        self.logger = get_logger('fingood.security.validator', LogCategory.SECURITY)
        self.issues: List[ValidationIssue] = []
    
    def validate_all(self, settings) -> Tuple[bool, List[ValidationIssue]]:
        """
        Validate all security configurations.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        self.issues = []
        
        # Validate different security aspects
        self._validate_https_configuration(settings)
        self._validate_security_headers(settings)
        self._validate_cookie_security(settings)
        self._validate_csrf_protection(settings)
        self._validate_cors_configuration(settings)
        self._validate_authentication_security(settings)
        self._validate_encryption_settings(settings)
        self._validate_logging_security(settings)
        self._validate_rate_limiting(settings)
        self._validate_database_security(settings)
        self._validate_redis_security(settings)
        
        # Check for critical issues
        critical_issues = [issue for issue in self.issues if issue.severity == ValidationSeverity.CRITICAL]
        has_critical_issues = len(critical_issues) > 0
        
        # Log validation results
        self._log_validation_results()
        
        return not has_critical_issues, self.issues
    
    def _add_issue(self, severity: ValidationSeverity, category: str, message: str, 
                   recommendation: str, setting_name: Optional[str] = None):
        """Add a validation issue."""
        issue = ValidationIssue(
            severity=severity,
            category=category,
            message=message,
            recommendation=recommendation,
            setting_name=setting_name
        )
        self.issues.append(issue)
    
    def _validate_https_configuration(self, settings):
        """Validate HTTPS and TLS configuration."""
        if not hasattr(settings, 'ENFORCE_HTTPS'):
            self._add_issue(
                ValidationSeverity.CRITICAL,
                "HTTPS",
                "ENFORCE_HTTPS setting is missing",
                "Add ENFORCE_HTTPS=True to configuration",
                "ENFORCE_HTTPS"
            )
            return
        
        if self.security_level == SecurityLevel.PRODUCTION and not settings.ENFORCE_HTTPS:
            self._add_issue(
                ValidationSeverity.CRITICAL,
                "HTTPS",
                "HTTPS enforcement is disabled in production",
                "Set ENFORCE_HTTPS=True for production deployment",
                "ENFORCE_HTTPS"
            )
        
        # Validate HSTS settings
        if hasattr(settings, 'HSTS_MAX_AGE'):
            if settings.HSTS_MAX_AGE < 31536000:  # 1 year
                self._add_issue(
                    ValidationSeverity.WARNING,
                    "HTTPS",
                    f"HSTS max-age is too short: {settings.HSTS_MAX_AGE} seconds",
                    "Set HSTS_MAX_AGE to at least 31536000 (1 year) for better security",
                    "HSTS_MAX_AGE"
                )
        
        if hasattr(settings, 'HSTS_INCLUDE_SUBDOMAINS') and not settings.HSTS_INCLUDE_SUBDOMAINS:
            self._add_issue(
                ValidationSeverity.WARNING,
                "HTTPS",
                "HSTS includeSubDomains is disabled",
                "Enable HSTS_INCLUDE_SUBDOMAINS for comprehensive protection",
                "HSTS_INCLUDE_SUBDOMAINS"
            )
    
    def _validate_security_headers(self, settings):
        """Validate security headers configuration."""
        if not hasattr(settings, 'ENABLE_SECURITY_HEADERS'):
            self._add_issue(
                ValidationSeverity.CRITICAL,
                "Security Headers",
                "Security headers are not configured",
                "Add ENABLE_SECURITY_HEADERS=True to configuration",
                "ENABLE_SECURITY_HEADERS"
            )
            return
        
        if not settings.ENABLE_SECURITY_HEADERS:
            self._add_issue(
                ValidationSeverity.CRITICAL,
                "Security Headers",
                "Security headers are disabled",
                "Enable security headers with ENABLE_SECURITY_HEADERS=True",
                "ENABLE_SECURITY_HEADERS"
            )
        
        # Validate CSP configuration
        if hasattr(settings, 'CUSTOM_CSP_POLICY') and settings.CUSTOM_CSP_POLICY:
            self._validate_csp_policy(settings.CUSTOM_CSP_POLICY)
        
        # Validate frame options
        if hasattr(settings, 'ALLOWED_FRAME_ORIGINS') and settings.ALLOWED_FRAME_ORIGINS:
            for origin in settings.ALLOWED_FRAME_ORIGINS:
                if not origin.startswith('https://'):
                    self._add_issue(
                        ValidationSeverity.ERROR,
                        "Security Headers",
                        f"Non-HTTPS frame origin allowed: {origin}",
                        "Only allow HTTPS origins for frame embedding",
                        "ALLOWED_FRAME_ORIGINS"
                    )
    
    def _validate_csp_policy(self, csp_policy: str):
        """Validate Content Security Policy."""
        dangerous_directives = [
            "'unsafe-eval'",
            "'unsafe-inline'",
            "data:",
            "*"
        ]
        
        for directive in dangerous_directives:
            if directive in csp_policy:
                severity = ValidationSeverity.ERROR if directive in ["'unsafe-eval'", "*"] else ValidationSeverity.WARNING
                self._add_issue(
                    severity,
                    "Content Security Policy",
                    f"Potentially dangerous CSP directive: {directive}",
                    f"Review and restrict the use of {directive} in CSP policy",
                    "CUSTOM_CSP_POLICY"
                )
    
    def _validate_cookie_security(self, settings):
        """Validate cookie security settings."""
        if hasattr(settings, 'COOKIE_SECURE') and not settings.COOKIE_SECURE:
            if self.security_level == SecurityLevel.PRODUCTION:
                self._add_issue(
                    ValidationSeverity.CRITICAL,
                    "Cookie Security",
                    "Secure cookies are disabled in production",
                    "Set COOKIE_SECURE=True for production deployment",
                    "COOKIE_SECURE"
                )
        
        if hasattr(settings, 'COOKIE_HTTPONLY') and not settings.COOKIE_HTTPONLY:
            self._add_issue(
                ValidationSeverity.ERROR,
                "Cookie Security",
                "HttpOnly cookies are disabled",
                "Enable COOKIE_HTTPONLY=True to prevent XSS attacks",
                "COOKIE_HTTPONLY"
            )
        
        if hasattr(settings, 'COOKIE_SAMESITE'):
            if settings.COOKIE_SAMESITE.lower() not in ['strict', 'lax']:
                self._add_issue(
                    ValidationSeverity.WARNING,
                    "Cookie Security",
                    f"Weak SameSite setting: {settings.COOKIE_SAMESITE}",
                    "Use 'strict' or 'lax' for COOKIE_SAMESITE",
                    "COOKIE_SAMESITE"
                )
    
    def _validate_csrf_protection(self, settings):
        """Validate CSRF protection settings."""
        if not hasattr(settings, 'CSRF_SECRET_KEY') or not settings.CSRF_SECRET_KEY:
            self._add_issue(
                ValidationSeverity.CRITICAL,
                "CSRF Protection",
                "CSRF secret key is not configured",
                "Configure CSRF_SECRET_KEY with a secure random value",
                "CSRF_SECRET_KEY"
            )
        
        if hasattr(settings, 'CSRF_TOKEN_EXPIRE_MINUTES'):
            if settings.CSRF_TOKEN_EXPIRE_MINUTES > 120:  # 2 hours
                self._add_issue(
                    ValidationSeverity.WARNING,
                    "CSRF Protection",
                    f"CSRF token expiry too long: {settings.CSRF_TOKEN_EXPIRE_MINUTES} minutes",
                    "Consider reducing CSRF token expiry to 60-120 minutes",
                    "CSRF_TOKEN_EXPIRE_MINUTES"
                )
    
    def _validate_cors_configuration(self, settings):
        """Validate CORS configuration."""
        if hasattr(settings, 'ALLOWED_HOSTS'):
            for host in settings.ALLOWED_HOSTS:
                parsed = urllib.parse.urlparse(host)
                
                # Check for wildcard origins
                if host == "*":
                    self._add_issue(
                        ValidationSeverity.CRITICAL,
                        "CORS",
                        "Wildcard CORS origin allowed",
                        "Replace '*' with specific allowed origins",
                        "ALLOWED_HOSTS"
                    )
                
                # Check for non-HTTPS origins in production
                if self.security_level == SecurityLevel.PRODUCTION and parsed.scheme == "http":
                    if parsed.hostname not in ['localhost', '127.0.0.1']:
                        self._add_issue(
                            ValidationSeverity.ERROR,
                            "CORS",
                            f"Non-HTTPS CORS origin in production: {host}",
                            "Use HTTPS origins for production deployment",
                            "ALLOWED_HOSTS"
                        )
    
    def _validate_authentication_security(self, settings):
        """Validate authentication security settings."""
        if not hasattr(settings, 'SECRET_KEY') or not settings.SECRET_KEY:
            self._add_issue(
                ValidationSeverity.CRITICAL,
                "Authentication",
                "SECRET_KEY is not configured",
                "Configure SECRET_KEY with a secure random value",
                "SECRET_KEY"
            )
        
        if hasattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES'):
            if settings.ACCESS_TOKEN_EXPIRE_MINUTES > 60:  # 1 hour
                self._add_issue(
                    ValidationSeverity.WARNING,
                    "Authentication",
                    f"Token expiry too long: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes",
                    "Consider reducing token expiry for financial applications",
                    "ACCESS_TOKEN_EXPIRE_MINUTES"
                )
        
        if hasattr(settings, 'ALGORITHM') and settings.ALGORITHM not in ['HS256', 'RS256', 'ES256']:
            self._add_issue(
                ValidationSeverity.ERROR,
                "Authentication",
                f"Weak JWT algorithm: {settings.ALGORITHM}",
                "Use HS256, RS256, or ES256 for JWT signing",
                "ALGORITHM"
            )
    
    def _validate_encryption_settings(self, settings):
        """Validate encryption and cryptographic settings."""
        # Check for strong secret keys
        secret_key_fields = ['SECRET_KEY', 'CSRF_SECRET_KEY', 'COMPLIANCE_SECRET_KEY']
        
        for field in secret_key_fields:
            if hasattr(settings, field):
                key_value = getattr(settings, field)
                if key_value and len(key_value) < 32:
                    self._add_issue(
                        ValidationSeverity.ERROR,
                        "Encryption",
                        f"{field} is too short: {len(key_value)} characters",
                        f"Use at least 32 characters for {field}",
                        field
                    )
    
    def _validate_logging_security(self, settings):
        """Validate logging security settings."""
        if hasattr(settings, 'LOG_REQUEST_BODIES') and settings.LOG_REQUEST_BODIES:
            self._add_issue(
                ValidationSeverity.WARNING,
                "Logging Security",
                "Request body logging is enabled",
                "Disable LOG_REQUEST_BODIES to prevent sensitive data exposure",
                "LOG_REQUEST_BODIES"
            )
        
        if hasattr(settings, 'LOG_RESPONSE_BODIES') and settings.LOG_RESPONSE_BODIES:
            self._add_issue(
                ValidationSeverity.WARNING,
                "Logging Security",
                "Response body logging is enabled",
                "Disable LOG_RESPONSE_BODIES to prevent sensitive data exposure",
                "LOG_RESPONSE_BODIES"
            )
        
        if hasattr(settings, 'MASK_SENSITIVE_DATA') and not settings.MASK_SENSITIVE_DATA:
            self._add_issue(
                ValidationSeverity.ERROR,
                "Logging Security",
                "Sensitive data masking is disabled",
                "Enable MASK_SENSITIVE_DATA=True to protect sensitive information",
                "MASK_SENSITIVE_DATA"
            )
    
    def _validate_rate_limiting(self, settings):
        """Validate rate limiting configuration."""
        if hasattr(settings, 'ENABLE_RATE_LIMITING') and not settings.ENABLE_RATE_LIMITING:
            self._add_issue(
                ValidationSeverity.WARNING,
                "Rate Limiting",
                "Rate limiting is disabled",
                "Enable rate limiting to prevent abuse",
                "ENABLE_RATE_LIMITING"
            )
        
        # Check for reasonable rate limits
        rate_limit_fields = {
            'AUTH_REQUESTS_PER_MINUTE': (5, 10),
            'DEFAULT_REQUESTS_PER_MINUTE': (60, 120),
            'BRUTE_FORCE_ATTEMPTS_PER_MINUTE': (3, 5)
        }
        
        for field, (min_val, max_val) in rate_limit_fields.items():
            if hasattr(settings, field):
                value = getattr(settings, field)
                if value > max_val:
                    self._add_issue(
                        ValidationSeverity.WARNING,
                        "Rate Limiting",
                        f"{field} is too high: {value}",
                        f"Consider setting {field} between {min_val} and {max_val}",
                        field
                    )
    
    def _validate_database_security(self, settings):
        """Validate database security configuration."""
        if hasattr(settings, 'DATABASE_URL') and settings.DATABASE_URL:
            parsed = urllib.parse.urlparse(settings.DATABASE_URL)
            
            # Check for secure connection
            if parsed.scheme == 'postgresql' and self.security_level == SecurityLevel.PRODUCTION:
                self._add_issue(
                    ValidationSeverity.WARNING,
                    "Database Security",
                    "Database connection may not be encrypted",
                    "Consider using postgresql+psycopg2 with SSL parameters",
                    "DATABASE_URL"
                )
            
            # Check for localhost in production
            if (self.security_level == SecurityLevel.PRODUCTION and 
                parsed.hostname in ['localhost', '127.0.0.1']):
                self._add_issue(
                    ValidationSeverity.WARNING,
                    "Database Security",
                    "Using localhost database in production",
                    "Use a dedicated database server for production",
                    "DATABASE_URL"
                )
    
    def _validate_redis_security(self, settings):
        """Validate Redis security configuration."""
        if hasattr(settings, 'REDIS_URL') and settings.REDIS_URL:
            parsed = urllib.parse.urlparse(settings.REDIS_URL)
            
            # Check for TLS encryption
            if (parsed.scheme == 'redis' and self.security_level == SecurityLevel.PRODUCTION and
                parsed.hostname not in ['localhost', '127.0.0.1']):
                self._add_issue(
                    ValidationSeverity.WARNING,
                    "Redis Security",
                    "Redis connection is not encrypted",
                    "Use rediss:// scheme for TLS encryption in production",
                    "REDIS_URL"
                )
            
            # Check for authentication
            if not parsed.password and self.security_level == SecurityLevel.PRODUCTION:
                self._add_issue(
                    ValidationSeverity.ERROR,
                    "Redis Security",
                    "Redis connection has no authentication",
                    "Configure Redis authentication for production",
                    "REDIS_URL"
                )
    
    def _log_validation_results(self):
        """Log validation results."""
        total_issues = len(self.issues)
        critical_count = len([i for i in self.issues if i.severity == ValidationSeverity.CRITICAL])
        error_count = len([i for i in self.issues if i.severity == ValidationSeverity.ERROR])
        warning_count = len([i for i in self.issues if i.severity == ValidationSeverity.WARNING])
        
        if total_issues == 0:
            self.logger.info("Security configuration validation passed", extra={
                'security_level': self.security_level.value,
                'issues_found': 0
            })
        else:
            self.logger.warning(f"Security configuration validation found {total_issues} issues", extra={
                'security_level': self.security_level.value,
                'total_issues': total_issues,
                'critical_issues': critical_count,
                'error_issues': error_count,
                'warning_issues': warning_count
            })
            
            # Log each critical issue
            for issue in self.issues:
                if issue.severity == ValidationSeverity.CRITICAL:
                    self.logger.critical(f"CRITICAL: {issue.message}", extra={
                        'category': issue.category,
                        'setting_name': issue.setting_name,
                        'recommendation': issue.recommendation
                    })
    
    def generate_report(self) -> str:
        """Generate a human-readable security validation report."""
        if not self.issues:
            return "✅ Security configuration validation passed - no issues found."
        
        report_lines = [
            f"🔐 Security Configuration Validation Report",
            f"Security Level: {self.security_level.value}",
            f"Total Issues: {len(self.issues)}",
            ""
        ]
        
        # Group issues by severity
        by_severity = {}
        for issue in self.issues:
            if issue.severity not in by_severity:
                by_severity[issue.severity] = []
            by_severity[issue.severity].append(issue)
        
        # Report by severity
        severity_order = [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR, 
                         ValidationSeverity.WARNING, ValidationSeverity.INFO]
        
        for severity in severity_order:
            if severity not in by_severity:
                continue
            
            issues = by_severity[severity]
            severity_symbol = {
                ValidationSeverity.CRITICAL: "🚨",
                ValidationSeverity.ERROR: "❌",
                ValidationSeverity.WARNING: "⚠️",
                ValidationSeverity.INFO: "ℹ️"
            }[severity]
            
            report_lines.append(f"{severity_symbol} {severity.value.upper()} ({len(issues)} issues)")
            report_lines.append("-" * 50)
            
            for issue in issues:
                report_lines.append(f"Category: {issue.category}")
                if issue.setting_name:
                    report_lines.append(f"Setting: {issue.setting_name}")
                report_lines.append(f"Issue: {issue.message}")
                report_lines.append(f"Recommendation: {issue.recommendation}")
                report_lines.append("")
        
        return "\n".join(report_lines)


def validate_security_configuration(settings, security_level: SecurityLevel = SecurityLevel.PRODUCTION) -> Tuple[bool, str]:
    """
    Validate security configuration and return results.
    
    Args:
        settings: Configuration settings object
        security_level: Security level for validation
    
    Returns:
        Tuple of (is_valid, report_text)
    """
    validator = SecurityConfigValidator(security_level)
    is_valid, issues = validator.validate_all(settings)
    report = validator.generate_report()
    
    return is_valid, report