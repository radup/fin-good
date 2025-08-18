"""
Security audit logging for FinGood financial application.
Provides comprehensive audit trails for authentication, authorization,
and security events as required for financial compliance.
"""

import json
import logging
import os
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path

from fastapi import Request


class SecurityEventType(Enum):
    """Types of security events for audit logging."""
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    TOKEN_CREATED = "token_created"
    TOKEN_VERIFIED = "token_verified"
    TOKEN_EXPIRED = "token_expired"
    TOKEN_INVALID = "token_invalid"
    TOKEN_REVOKED = "token_revoked"
    MASS_REVOCATION = "mass_revocation"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    ACCESS_DENIED = "access_denied"
    PASSWORD_CHANGE = "password_change"
    ACCOUNT_LOCKED = "account_locked"
    SECURITY_VIOLATION = "security_violation"
    FILE_UPLOAD_ATTEMPT = "file_upload_attempt"
    FILE_UPLOAD_SUCCESS = "file_upload_success"
    FILE_UPLOAD_FAILURE = "file_upload_failure"
    FILE_VALIDATION_SUCCESS = "file_validation_success"
    FILE_VALIDATION_FAILURE = "file_validation_failure"
    FILE_QUARANTINED = "file_quarantined"
    FILE_REJECTED = "file_rejected"
    MALWARE_DETECTED = "malware_detected"
    SUSPICIOUS_FILE_CONTENT = "suspicious_file_content"
    FILE_SIZE_VIOLATION = "file_size_violation"
    QUARANTINE_RELEASE = "quarantine_release"
    CONTENT_SANITIZATION_START = "content_sanitization_start"
    CONTENT_SANITIZATION_COMPLETE = "content_sanitization_complete"
    CONTENT_SANITIZATION_FAILURE = "content_sanitization_failure"
    CONTENT_SANITIZATION_ERROR = "content_sanitization_error"
    SANDBOX_ANALYSIS_START = "sandbox_analysis_start"
    SANDBOX_ANALYSIS_COMPLETE = "sandbox_analysis_complete"
    SANDBOX_ANALYSIS_THREAT = "sandbox_analysis_threat"
    SANDBOX_ANALYSIS_ERROR = "sandbox_analysis_error"


class RiskLevel(Enum):
    """Risk levels for security events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """Structure for security audit events."""
    event_type: SecurityEventType
    risk_level: RiskLevel
    timestamp: datetime
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    outcome: Optional[str] = None
    error_code: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        event_dict = asdict(self)
        event_dict['event_type'] = self.event_type.value
        event_dict['risk_level'] = self.risk_level.value
        event_dict['timestamp'] = self.timestamp.isoformat()
        return event_dict


class SecurityAuditLogger:
    """
    Comprehensive security audit logger for financial applications.
    Implements structured logging with JSON output for SIEM integration.
    """
    
    def __init__(self, log_level: int = logging.INFO):
        self.logger = logging.getLogger("fingood.security_audit")
        self.logger.setLevel(log_level)
        
        # Remove any existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create audit log directory
        audit_log_dir = Path("logs/audit")
        audit_log_dir.mkdir(parents=True, exist_ok=True)
        
        # File handler for audit logs (JSON format)
        file_handler = logging.FileHandler(
            audit_log_dir / "security_audit.jsonl",
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        
        # JSON formatter for structured logging
        json_formatter = logging.Formatter(
            '%(message)s'
        )
        file_handler.setFormatter(json_formatter)
        
        # Console handler for immediate visibility
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)  # Only show warnings+ on console
        
        console_formatter = logging.Formatter(
            '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Prevent propagation to avoid duplicate logs
        self.logger.propagate = False
    
    def log_event(self, event: SecurityEvent) -> None:
        """
        Log a security event with appropriate level based on risk.
        
        Args:
            event: Security event to log
        """
        # Convert event to JSON
        event_json = json.dumps(event.to_dict(), separators=(',', ':'))
        
        # Log at appropriate level based on risk
        if event.risk_level == RiskLevel.CRITICAL:
            self.logger.critical(event_json)
        elif event.risk_level == RiskLevel.HIGH:
            self.logger.error(event_json)
        elif event.risk_level == RiskLevel.MEDIUM:
            self.logger.warning(event_json)
        else:
            self.logger.info(event_json)
    
    def log_authentication_success(
        self, 
        user_id: int, 
        user_email: str,
        request: Optional[Request] = None,
        session_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log successful authentication."""
        event = SecurityEvent(
            event_type=SecurityEventType.AUTH_SUCCESS,
            risk_level=RiskLevel.LOW,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            user_email=user_email,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            session_id=session_id,
            request_id=self._get_request_id(request),
            details=details,
            outcome="success"
        )
        self.log_event(event)
    
    def log_authentication_failure(
        self, 
        attempted_email: str,
        request: Optional[Request] = None,
        reason: str = "invalid_credentials",
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log failed authentication attempt."""
        event = SecurityEvent(
            event_type=SecurityEventType.AUTH_FAILURE,
            risk_level=RiskLevel.MEDIUM,
            timestamp=datetime.utcnow(),
            user_email=attempted_email,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            request_id=self._get_request_id(request),
            details=details or {"reason": reason},
            outcome="failure",
            error_code=reason
        )
        self.log_event(event)
    
    def log_token_created(
        self, 
        user_id: int, 
        user_email: str,
        jti: str,
        expires_at: datetime,
        request: Optional[Request] = None
    ) -> None:
        """Log JWT token creation."""
        event = SecurityEvent(
            event_type=SecurityEventType.TOKEN_CREATED,
            risk_level=RiskLevel.LOW,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            user_email=user_email,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            request_id=self._get_request_id(request),
            details={
                "jti": jti,
                "expires_at": expires_at.isoformat()
            },
            outcome="success"
        )
        self.log_event(event)
    
    def log_token_verification_success(
        self, 
        user_id: int, 
        user_email: str,
        jti: str,
        request: Optional[Request] = None
    ) -> None:
        """Log successful token verification."""
        event = SecurityEvent(
            event_type=SecurityEventType.TOKEN_VERIFIED,
            risk_level=RiskLevel.LOW,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            user_email=user_email,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            request_id=self._get_request_id(request),
            details={"jti": jti},
            outcome="success"
        )
        self.log_event(event)
    
    def log_token_expired(
        self, 
        jti: Optional[str] = None,
        user_email: Optional[str] = None,
        request: Optional[Request] = None
    ) -> None:
        """Log expired token attempt."""
        event = SecurityEvent(
            event_type=SecurityEventType.TOKEN_EXPIRED,
            risk_level=RiskLevel.LOW,
            timestamp=datetime.utcnow(),
            user_email=user_email,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            request_id=self._get_request_id(request),
            details={"jti": jti} if jti else None,
            outcome="failure",
            error_code="token_expired"
        )
        self.log_event(event)
    
    def log_token_invalid(
        self, 
        jti: Optional[str] = None,
        user_email: Optional[str] = None,
        request: Optional[Request] = None,
        reason: str = "invalid_signature"
    ) -> None:
        """Log invalid token attempt."""
        event = SecurityEvent(
            event_type=SecurityEventType.TOKEN_INVALID,
            risk_level=RiskLevel.MEDIUM,
            timestamp=datetime.utcnow(),
            user_email=user_email,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            request_id=self._get_request_id(request),
            details={"jti": jti, "reason": reason} if jti else {"reason": reason},
            outcome="failure",
            error_code="token_invalid"
        )
        self.log_event(event)
    
    def log_token_revoked(
        self, 
        user_id: int,
        jti: str,
        reason: str,
        request: Optional[Request] = None
    ) -> None:
        """Log token revocation."""
        event = SecurityEvent(
            event_type=SecurityEventType.TOKEN_REVOKED,
            risk_level=RiskLevel.MEDIUM,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            request_id=self._get_request_id(request),
            details={"jti": jti, "reason": reason},
            outcome="success"
        )
        self.log_event(event)
    
    def log_mass_revocation(
        self, 
        user_id: int,
        reason: str,
        request: Optional[Request] = None
    ) -> None:
        """Log mass token revocation."""
        event = SecurityEvent(
            event_type=SecurityEventType.MASS_REVOCATION,
            risk_level=RiskLevel.HIGH,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            request_id=self._get_request_id(request),
            details={"reason": reason},
            outcome="success"
        )
        self.log_event(event)
    
    def log_suspicious_activity(
        self, 
        description: str,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        request: Optional[Request] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log suspicious activity."""
        event = SecurityEvent(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            risk_level=RiskLevel.HIGH,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            user_email=user_email,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            request_id=self._get_request_id(request),
            details=details or {"description": description},
            outcome="detected"
        )
        self.log_event(event)
    
    def log_access_denied(
        self, 
        resource: str,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        request: Optional[Request] = None,
        reason: str = "insufficient_permissions"
    ) -> None:
        """Log access denied events."""
        event = SecurityEvent(
            event_type=SecurityEventType.ACCESS_DENIED,
            risk_level=RiskLevel.MEDIUM,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            user_email=user_email,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            request_id=self._get_request_id(request),
            details={"resource": resource, "reason": reason},
            outcome="denied",
            error_code=reason
        )
        self.log_event(event)
    
    def log_security_violation(
        self, 
        violation_type: str,
        description: str,
        user_id: Optional[int] = None,
        request: Optional[Request] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log security violations."""
        event = SecurityEvent(
            event_type=SecurityEventType.SECURITY_VIOLATION,
            risk_level=RiskLevel.CRITICAL,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            request_id=self._get_request_id(request),
            details=details or {"violation_type": violation_type, "description": description},
            outcome="violation_detected"
        )
        self.log_event(event)
    
    def _get_client_ip(self, request: Optional[Request]) -> Optional[str]:
        """Extract client IP from request."""
        if not request:
            return None
        
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return None
    
    def _get_user_agent(self, request: Optional[Request]) -> Optional[str]:
        """Extract user agent from request."""
        if not request:
            return None
        return request.headers.get("User-Agent")
    
    def _get_request_id(self, request: Optional[Request]) -> Optional[str]:
        """Extract request ID from request."""
        if not request:
            return None
        
        # Check for various request ID headers
        for header in ["X-Request-ID", "X-Correlation-ID", "Request-ID"]:
            request_id = request.headers.get(header)
            if request_id:
                return request_id
        
        return None
    
    def log_file_upload_attempt(
        self,
        user_id: Optional[str],
        filename: str,
        file_size: int,
        timestamp: datetime,
        request: Optional[Request] = None
    ) -> None:
        """Log file upload attempt."""
        event = SecurityEvent(
            event_type=SecurityEventType.FILE_UPLOAD_ATTEMPT,
            risk_level=RiskLevel.LOW,
            timestamp=timestamp,
            user_id=user_id,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            request_id=self._get_request_id(request),
            details={
                "filename": filename,
                "file_size": file_size,
                "action": "upload_started"
            },
            outcome="initiated"
        )
        self.log_event(event)
    
    def log_file_upload_success(
        self,
        user_id: Optional[str],
        filename: str,
        file_size: int,
        batch_id: str,
        processed_count: int,
        request: Optional[Request] = None
    ) -> None:
        """Log successful file upload and processing."""
        event = SecurityEvent(
            event_type=SecurityEventType.FILE_UPLOAD_SUCCESS,
            risk_level=RiskLevel.LOW,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            request_id=self._get_request_id(request),
            details={
                "filename": filename,
                "file_size": file_size,
                "batch_id": batch_id,
                "processed_count": processed_count
            },
            outcome="success"
        )
        self.log_event(event)
    
    def log_file_upload_failure(
        self,
        user_id: Optional[str],
        filename: str,
        file_size: int,
        error: str,
        request: Optional[Request] = None
    ) -> None:
        """Log failed file upload."""
        event = SecurityEvent(
            event_type=SecurityEventType.FILE_UPLOAD_FAILURE,
            risk_level=RiskLevel.MEDIUM,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            request_id=self._get_request_id(request),
            details={
                "filename": filename,
                "file_size": file_size,
                "error": error
            },
            outcome="failure",
            error_code="upload_failed"
        )
        self.log_event(event)
    
    def log_file_validation_result(
        self,
        user_id: Optional[str],
        filename: str,
        validation_result: str,
        threat_level: str,
        errors: list,
        duration: float,
        request: Optional[Request] = None
    ) -> None:
        """Log file validation results."""
        risk_level_map = {
            "safe": RiskLevel.LOW,
            "low": RiskLevel.LOW,
            "medium": RiskLevel.MEDIUM,
            "high": RiskLevel.HIGH,
            "critical": RiskLevel.CRITICAL
        }
        
        event_type = (
            SecurityEventType.FILE_VALIDATION_SUCCESS 
            if validation_result == "approved" 
            else SecurityEventType.FILE_VALIDATION_FAILURE
        )
        
        event = SecurityEvent(
            event_type=event_type,
            risk_level=risk_level_map.get(threat_level, RiskLevel.MEDIUM),
            timestamp=datetime.utcnow(),
            user_id=user_id,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            request_id=self._get_request_id(request),
            details={
                "filename": filename,
                "validation_result": validation_result,
                "threat_level": threat_level,
                "errors": errors,
                "validation_duration": duration
            },
            outcome=validation_result
        )
        self.log_event(event)
    
    def log_file_quarantined(
        self,
        user_id: Optional[str],
        filename: str,
        quarantine_id: str,
        reason: str,
        request: Optional[Request] = None
    ) -> None:
        """Log file quarantine action."""
        event = SecurityEvent(
            event_type=SecurityEventType.FILE_QUARANTINED,
            risk_level=RiskLevel.HIGH,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            request_id=self._get_request_id(request),
            details={
                "filename": filename,
                "quarantine_id": quarantine_id,
                "reason": reason
            },
            outcome="quarantined"
        )
        self.log_event(event)
    
    def log_file_rejected(
        self,
        user_id: Optional[str],
        filename: str,
        reason: str,
        threat_indicators: list,
        request: Optional[Request] = None
    ) -> None:
        """Log file rejection."""
        event = SecurityEvent(
            event_type=SecurityEventType.FILE_REJECTED,
            risk_level=RiskLevel.HIGH,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            request_id=self._get_request_id(request),
            details={
                "filename": filename,
                "reason": reason,
                "threat_indicators": threat_indicators
            },
            outcome="rejected"
        )
        self.log_event(event)
    
    def log_malware_detected(
        self,
        user_id: Optional[str],
        filename: str,
        malware_type: str,
        signature: str,
        request: Optional[Request] = None
    ) -> None:
        """Log malware detection."""
        event = SecurityEvent(
            event_type=SecurityEventType.MALWARE_DETECTED,
            risk_level=RiskLevel.CRITICAL,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            request_id=self._get_request_id(request),
            details={
                "filename": filename,
                "malware_type": malware_type,
                "signature": signature
            },
            outcome="blocked"
        )
        self.log_event(event)
    
    def log_suspicious_file_content(
        self,
        user_id: Optional[str],
        filename: str,
        content_indicators: list,
        request: Optional[Request] = None
    ) -> None:
        """Log suspicious file content detection."""
        event = SecurityEvent(
            event_type=SecurityEventType.SUSPICIOUS_FILE_CONTENT,
            risk_level=RiskLevel.HIGH,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            request_id=self._get_request_id(request),
            details={
                "filename": filename,
                "content_indicators": content_indicators
            },
            outcome="flagged"
        )
        self.log_event(event)
    
    def log_file_size_violation(
        self,
        user_id: Optional[str],
        filename: str,
        file_size: int,
        max_allowed: int,
        request: Optional[Request] = None
    ) -> None:
        """Log file size violations."""
        event = SecurityEvent(
            event_type=SecurityEventType.FILE_SIZE_VIOLATION,
            risk_level=RiskLevel.MEDIUM,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            request_id=self._get_request_id(request),
            details={
                "filename": filename,
                "file_size": file_size,
                "max_allowed": max_allowed,
                "violation_amount": file_size - max_allowed
            },
            outcome="rejected",
            error_code="file_too_large"
        )
        self.log_event(event)
    
    def log_quarantine_release(
        self,
        user_id: str,
        quarantine_id: str,
        timestamp: datetime,
        request: Optional[Request] = None
    ) -> None:
        """Log file release from quarantine."""
        event = SecurityEvent(
            event_type=SecurityEventType.QUARANTINE_RELEASE,
            risk_level=RiskLevel.MEDIUM,
            timestamp=timestamp,
            user_id=user_id,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            request_id=self._get_request_id(request),
            details={
                "quarantine_id": quarantine_id,
                "action": "file_released"
            },
            outcome="released"
        )
        self.log_event(event)
    
    def log_file_validation_error(
        self,
        user_id: Optional[str],
        filename: str,
        error: str,
        request: Optional[Request] = None
    ) -> None:
        """Log file validation system errors."""
        event = SecurityEvent(
            event_type=SecurityEventType.SECURITY_VIOLATION,
            risk_level=RiskLevel.HIGH,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            request_id=self._get_request_id(request),
            details={
                "filename": filename,
                "validation_error": error,
                "subsystem": "file_validation"
            },
            outcome="system_error",
            error_code="validation_system_error"
        )
        self.log_event(event)
    
    def log_content_sanitization_start(
        self,
        user_id: Optional[str],
        filename: str,
        content_size: int,
        level: str,
        request: Optional[Request] = None
    ) -> None:
        """Log content sanitization start."""
        event = SecurityEvent(
            event_type=SecurityEventType.CONTENT_SANITIZATION_START,
            risk_level=RiskLevel.LOW,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            request_id=self._get_request_id(request),
            details={
                "filename": filename,
                "content_size": content_size,
                "sanitization_level": level,
                "subsystem": "content_sanitization"
            },
            outcome="sanitization_started"
        )
        self.log_event(event)
    
    def log_content_sanitization_complete(
        self,
        user_id: Optional[str],
        filename: str,
        original_size: int,
        sanitized_size: int,
        modifications_count: int,
        security_issues_count: int,
        is_safe: bool,
        request: Optional[Request] = None
    ) -> None:
        """Log content sanitization completion."""
        event = SecurityEvent(
            event_type=SecurityEventType.CONTENT_SANITIZATION_COMPLETE,
            risk_level=RiskLevel.LOW if is_safe else RiskLevel.MEDIUM,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            request_id=self._get_request_id(request),
            details={
                "filename": filename,
                "original_size": original_size,
                "sanitized_size": sanitized_size,
                "modifications_count": modifications_count,
                "security_issues_count": security_issues_count,
                "is_safe": is_safe,
                "subsystem": "content_sanitization"
            },
            outcome="sanitization_completed" if is_safe else "sanitization_completed_with_issues"
        )
        self.log_event(event)
    
    def log_content_sanitization_failure(
        self,
        user_id: Optional[str],
        filename: str,
        security_issues: list,
        request: Optional[Request] = None
    ) -> None:
        """Log content sanitization failure."""
        event = SecurityEvent(
            event_type=SecurityEventType.CONTENT_SANITIZATION_FAILURE,
            risk_level=RiskLevel.HIGH,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            request_id=self._get_request_id(request),
            details={
                "filename": filename,
                "security_issues": security_issues,
                "subsystem": "content_sanitization"
            },
            outcome="sanitization_failed",
            error_code="unsafe_content"
        )
        self.log_event(event)
    
    def log_content_sanitization_error(
        self,
        user_id: Optional[str],
        filename: str,
        error: str,
        request: Optional[Request] = None
    ) -> None:
        """Log content sanitization error."""
        event = SecurityEvent(
            event_type=SecurityEventType.CONTENT_SANITIZATION_ERROR,
            risk_level=RiskLevel.HIGH,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            request_id=self._get_request_id(request),
            details={
                "filename": filename,
                "error": error,
                "subsystem": "content_sanitization"
            },
            outcome="sanitization_error",
            error_code="sanitization_system_error"
        )
        self.log_event(event)
    
    def log_sandbox_analysis_start(
        self,
        user_id: Optional[str],
        filename: str,
        file_size: int,
        analysis_type: str,
        request: Optional[Request] = None
    ) -> None:
        """Log sandbox analysis start."""
        event = SecurityEvent(
            event_type=SecurityEventType.SANDBOX_ANALYSIS_START,
            risk_level=RiskLevel.LOW,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            request_id=self._get_request_id(request),
            details={
                "filename": filename,
                "file_size": file_size,
                "analysis_type": analysis_type,
                "subsystem": "sandbox_analysis"
            },
            outcome="analysis_started"
        )
        self.log_event(event)
    
    def log_sandbox_analysis_complete(
        self,
        user_id: Optional[str],
        filename: str,
        risk_level: str,
        threats_count: int,
        analysis_duration: float,
        is_safe: bool,
        request: Optional[Request] = None
    ) -> None:
        """Log sandbox analysis completion."""
        event = SecurityEvent(
            event_type=SecurityEventType.SANDBOX_ANALYSIS_COMPLETE,
            risk_level=RiskLevel.LOW if is_safe else RiskLevel.HIGH,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            request_id=self._get_request_id(request),
            details={
                "filename": filename,
                "risk_level": risk_level,
                "threats_count": threats_count,
                "analysis_duration": analysis_duration,
                "is_safe": is_safe,
                "subsystem": "sandbox_analysis"
            },
            outcome="analysis_completed"
        )
        self.log_event(event)
    
    def log_sandbox_analysis_threat(
        self,
        user_id: Optional[str],
        filename: str,
        risk_level: str,
        threats: list,
        request: Optional[Request] = None
    ) -> None:
        """Log sandbox analysis threat detection."""
        event = SecurityEvent(
            event_type=SecurityEventType.SANDBOX_ANALYSIS_THREAT,
            risk_level=RiskLevel.CRITICAL,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            request_id=self._get_request_id(request),
            details={
                "filename": filename,
                "risk_level": risk_level,
                "threats_detected": threats,
                "subsystem": "sandbox_analysis"
            },
            outcome="threats_detected",
            error_code="sandbox_threat_detected"
        )
        self.log_event(event)
    
    def log_sandbox_analysis_error(
        self,
        user_id: Optional[str],
        filename: str,
        error: str,
        request: Optional[Request] = None
    ) -> None:
        """Log sandbox analysis error."""
        event = SecurityEvent(
            event_type=SecurityEventType.SANDBOX_ANALYSIS_ERROR,
            risk_level=RiskLevel.HIGH,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            client_ip=self._get_client_ip(request),
            user_agent=self._get_user_agent(request),
            request_id=self._get_request_id(request),
            details={
                "filename": filename,
                "error": error,
                "subsystem": "sandbox_analysis"
            },
            outcome="analysis_error",
            error_code="sandbox_system_error"
        )
        self.log_event(event)


# Global audit logger instance
security_audit_logger = SecurityAuditLogger()


def log_auth_success(
    user_id: int, 
    user_email: str,
    request: Optional[Request] = None,
    **kwargs
) -> None:
    """Convenience function for logging authentication success."""
    security_audit_logger.log_authentication_success(user_id, user_email, request, **kwargs)


def log_auth_failure(
    attempted_email: str,
    request: Optional[Request] = None,
    reason: str = "invalid_credentials"
) -> None:
    """Convenience function for logging authentication failure."""
    security_audit_logger.log_authentication_failure(attempted_email, request, reason)


def log_suspicious_activity(
    description: str,
    user_id: Optional[int] = None,
    request: Optional[Request] = None,
    **kwargs
) -> None:
    """Convenience function for logging suspicious activity."""
    security_audit_logger.log_suspicious_activity(description, user_id, request, **kwargs)