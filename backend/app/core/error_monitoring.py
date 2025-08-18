"""
Error Monitoring and Alerting System for FinGood Financial Platform

This module provides comprehensive error monitoring, alerting, and analytics
for financial application security and operational monitoring.
"""

import logging
import json
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import threading
import time

from app.schemas.error import ErrorCategory, ErrorSeverity
from app.core.audit_logger import security_audit_logger

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels for monitoring systems"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Available alert channels"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"
    PAGERDUTY = "pagerduty"


@dataclass
class ErrorMetric:
    """Error metric for monitoring and alerting"""
    error_code: str
    category: ErrorCategory
    severity: ErrorSeverity
    count: int
    first_occurrence: datetime
    last_occurrence: datetime
    user_ids: set
    client_ips: set
    endpoints: set
    user_agents: set


@dataclass
class Alert:
    """Alert definition for error monitoring"""
    alert_id: str
    severity: AlertSeverity
    title: str
    description: str
    details: Dict[str, Any]
    timestamp: datetime
    channels: List[AlertChannel]
    threshold_exceeded: Optional[str] = None
    recommended_action: Optional[str] = None


class ErrorPatternDetector:
    """
    Detects patterns in errors that may indicate security issues,
    system problems, or other concerns requiring immediate attention.
    """
    
    def __init__(self):
        self.error_history = defaultdict(lambda: deque(maxlen=1000))
        self.pattern_thresholds = {
            # Authentication failures
            "auth_failure_burst": {"count": 5, "window": 60},  # 5 failures in 1 minute
            "auth_failure_sustained": {"count": 20, "window": 600},  # 20 failures in 10 minutes
            
            # System errors
            "system_error_cluster": {"count": 10, "window": 300},  # 10 system errors in 5 minutes
            "critical_error_any": {"count": 1, "window": 1},  # Any critical error immediately
            
            # Financial compliance
            "compliance_violations": {"count": 3, "window": 300},  # 3 violations in 5 minutes
            "rate_limit_abuse": {"count": 10, "window": 60},  # 10 rate limits in 1 minute
            
            # Data integrity
            "data_integrity_issues": {"count": 5, "window": 600},  # 5 issues in 10 minutes
        }
    
    def analyze_error(
        self, 
        error_code: str, 
        category: ErrorCategory, 
        severity: ErrorSeverity,
        context: Dict[str, Any]
    ) -> List[Alert]:
        """
        Analyze an error and detect patterns that require alerts
        
        Returns:
            List of alerts to be sent
        """
        alerts = []
        current_time = datetime.utcnow()
        
        # Record the error
        error_entry = {
            "timestamp": current_time,
            "error_code": error_code,
            "category": category,
            "severity": severity,
            "context": context
        }
        
        # Store in appropriate categories for pattern detection
        self.error_history["all"].append(error_entry)
        self.error_history[category.value].append(error_entry)
        self.error_history[severity.value].append(error_entry)
        self.error_history[error_code].append(error_entry)
        
        # Check for immediate critical alerts
        if severity == ErrorSeverity.CRITICAL:
            alerts.append(self._create_critical_alert(error_code, context))
        
        # Check for authentication failure patterns
        if category == ErrorCategory.AUTHENTICATION:
            auth_alerts = self._check_authentication_patterns(current_time, context)
            alerts.extend(auth_alerts)
        
        # Check for system error patterns
        if category == ErrorCategory.SYSTEM_ERROR:
            system_alerts = self._check_system_error_patterns(current_time, context)
            alerts.extend(system_alerts)
        
        # Check for financial compliance patterns
        if category == ErrorCategory.FINANCIAL_COMPLIANCE:
            compliance_alerts = self._check_compliance_patterns(current_time, context)
            alerts.extend(compliance_alerts)
        
        # Check for rate limiting abuse
        if category == ErrorCategory.RATE_LIMITING:
            rate_alerts = self._check_rate_limiting_patterns(current_time, context)
            alerts.extend(rate_alerts)
        
        return alerts
    
    def _create_critical_alert(self, error_code: str, context: Dict[str, Any]) -> Alert:
        """Create immediate alert for critical errors"""
        return Alert(
            alert_id=f"critical_{error_code}_{int(time.time())}",
            severity=AlertSeverity.CRITICAL,
            title=f"Critical Error: {error_code}",
            description=f"Critical error occurred requiring immediate attention",
            details={
                "error_code": error_code,
                "context": context,
                "user_id": context.get("user_id"),
                "client_ip": context.get("client_ip"),
                "endpoint": context.get("path")
            },
            timestamp=datetime.utcnow(),
            channels=[AlertChannel.PAGERDUTY, AlertChannel.EMAIL, AlertChannel.SLACK],
            recommended_action="Immediate investigation required"
        )
    
    def _check_authentication_patterns(
        self, 
        current_time: datetime, 
        context: Dict[str, Any]
    ) -> List[Alert]:
        """Check for authentication attack patterns"""
        alerts = []
        
        # Check for burst of failures from same IP
        if context.get("client_ip"):
            ip_failures = [
                entry for entry in self.error_history[ErrorCategory.AUTHENTICATION.value]
                if (current_time - entry["timestamp"]).seconds <= 60
                and entry["context"].get("client_ip") == context.get("client_ip")
            ]
            
            if len(ip_failures) >= 5:
                alerts.append(Alert(
                    alert_id=f"auth_burst_{context.get('client_ip')}_{int(time.time())}",
                    severity=AlertSeverity.ERROR,
                    title="Authentication Failure Burst Detected",
                    description=f"Multiple authentication failures from IP {context.get('client_ip')}",
                    details={
                        "client_ip": context.get("client_ip"),
                        "failure_count": len(ip_failures),
                        "time_window": "60 seconds",
                        "pattern": "brute_force_attempt"
                    },
                    timestamp=current_time,
                    channels=[AlertChannel.EMAIL, AlertChannel.SLACK],
                    recommended_action="Consider IP blocking or rate limiting"
                ))
        
        # Check for sustained failures across the system
        recent_auth_failures = [
            entry for entry in self.error_history[ErrorCategory.AUTHENTICATION.value]
            if (current_time - entry["timestamp"]).seconds <= 600
        ]
        
        if len(recent_auth_failures) >= 20:
            alerts.append(Alert(
                alert_id=f"auth_sustained_{int(time.time())}",
                severity=AlertSeverity.WARNING,
                title="Sustained Authentication Failures",
                description="High volume of authentication failures detected",
                details={
                    "failure_count": len(recent_auth_failures),
                    "time_window": "10 minutes",
                    "unique_ips": len(set(e["context"].get("client_ip") for e in recent_auth_failures)),
                    "pattern": "sustained_attack"
                },
                timestamp=current_time,
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK],
                recommended_action="Investigate for coordinated attack"
            ))
        
        return alerts
    
    def _check_system_error_patterns(
        self, 
        current_time: datetime, 
        context: Dict[str, Any]
    ) -> List[Alert]:
        """Check for system error patterns indicating infrastructure issues"""
        alerts = []
        
        recent_system_errors = [
            entry for entry in self.error_history[ErrorCategory.SYSTEM_ERROR.value]
            if (current_time - entry["timestamp"]).seconds <= 300
        ]
        
        if len(recent_system_errors) >= 10:
            alerts.append(Alert(
                alert_id=f"system_cluster_{int(time.time())}",
                severity=AlertSeverity.ERROR,
                title="System Error Cluster Detected",
                description="Multiple system errors in short time period",
                details={
                    "error_count": len(recent_system_errors),
                    "time_window": "5 minutes",
                    "endpoints": list(set(e["context"].get("path", "unknown") for e in recent_system_errors)),
                    "error_types": list(set(e["error_code"] for e in recent_system_errors))
                },
                timestamp=current_time,
                channels=[AlertChannel.PAGERDUTY, AlertChannel.EMAIL],
                recommended_action="Check system health and infrastructure"
            ))
        
        return alerts
    
    def _check_compliance_patterns(
        self, 
        current_time: datetime, 
        context: Dict[str, Any]
    ) -> List[Alert]:
        """Check for financial compliance violation patterns"""
        alerts = []
        
        recent_compliance_errors = [
            entry for entry in self.error_history[ErrorCategory.FINANCIAL_COMPLIANCE.value]
            if (current_time - entry["timestamp"]).seconds <= 300
        ]
        
        if len(recent_compliance_errors) >= 3:
            alerts.append(Alert(
                alert_id=f"compliance_{int(time.time())}",
                severity=AlertSeverity.ERROR,
                title="Financial Compliance Violations",
                description="Multiple compliance violations detected",
                details={
                    "violation_count": len(recent_compliance_errors),
                    "time_window": "5 minutes",
                    "violation_types": list(set(e["error_code"] for e in recent_compliance_errors)),
                    "users_affected": list(set(e["context"].get("user_id") for e in recent_compliance_errors if e["context"].get("user_id")))
                },
                timestamp=current_time,
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK],
                recommended_action="Review compliance violations and user patterns"
            ))
        
        return alerts
    
    def _check_rate_limiting_patterns(
        self, 
        current_time: datetime, 
        context: Dict[str, Any]
    ) -> List[Alert]:
        """Check for rate limiting abuse patterns"""
        alerts = []
        
        recent_rate_limits = [
            entry for entry in self.error_history[ErrorCategory.RATE_LIMITING.value]
            if (current_time - entry["timestamp"]).seconds <= 60
        ]
        
        if len(recent_rate_limits) >= 10:
            alerts.append(Alert(
                alert_id=f"rate_abuse_{int(time.time())}",
                severity=AlertSeverity.WARNING,
                title="Rate Limiting Abuse Detected",
                description="High volume of rate limit violations",
                details={
                    "violation_count": len(recent_rate_limits),
                    "time_window": "1 minute",
                    "unique_ips": len(set(e["context"].get("client_ip") for e in recent_rate_limits if e["context"].get("client_ip"))),
                    "endpoints": list(set(e["context"].get("path") for e in recent_rate_limits if e["context"].get("path")))
                },
                timestamp=current_time,
                channels=[AlertChannel.EMAIL],
                recommended_action="Consider additional rate limiting or IP blocking"
            ))
        
        return alerts


class ErrorMonitor:
    """
    Main error monitoring system that tracks errors, generates metrics,
    and sends alerts based on patterns and thresholds.
    """
    
    def __init__(self):
        self.pattern_detector = ErrorPatternDetector()
        self.metrics = defaultdict(lambda: ErrorMetric(
            error_code="",
            category=ErrorCategory.SYSTEM_ERROR,
            severity=ErrorSeverity.MEDIUM,
            count=0,
            first_occurrence=datetime.utcnow(),
            last_occurrence=datetime.utcnow(),
            user_ids=set(),
            client_ips=set(),
            endpoints=set(),
            user_agents=set()
        ))
        self.alert_handlers = {}
        self.metrics_lock = threading.Lock()
        
        # Setup default alert handlers
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        """Setup default alert handlers"""
        self.alert_handlers[AlertChannel.EMAIL] = self._handle_email_alert
        self.alert_handlers[AlertChannel.SLACK] = self._handle_slack_alert
        self.alert_handlers[AlertChannel.WEBHOOK] = self._handle_webhook_alert
        self.alert_handlers[AlertChannel.PAGERDUTY] = self._handle_pagerduty_alert
    
    def _serialize_datetime_objects(self, obj: Any) -> Any:
        """Recursively convert datetime objects to ISO format strings for JSON serialization"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: self._serialize_datetime_objects(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetime_objects(item) for item in obj]
        elif isinstance(obj, set):
            return [self._serialize_datetime_objects(item) for item in obj]
        else:
            return obj
    
    def record_error(
        self,
        error_code: str,
        category: ErrorCategory,
        severity: ErrorSeverity,
        context: Dict[str, Any]
    ) -> None:
        """
        Record an error and check for alert conditions
        
        Args:
            error_code: The specific error code
            category: Error category
            severity: Error severity
            context: Additional context information
        """
        current_time = datetime.utcnow()
        
        # Update metrics
        with self.metrics_lock:
            metric = self.metrics[error_code]
            if metric.count == 0:
                metric.error_code = error_code
                metric.category = category
                metric.severity = severity
                metric.first_occurrence = current_time
            
            metric.count += 1
            metric.last_occurrence = current_time
            
            # Add context information
            if context.get("user_id"):
                metric.user_ids.add(context["user_id"])
            if context.get("client_ip"):
                metric.client_ips.add(context["client_ip"])
            if context.get("path"):
                metric.endpoints.add(context["path"])
            if context.get("user_agent"):
                metric.user_agents.add(context["user_agent"][:100])  # Limit length
        
        # Check for alert patterns
        alerts = self.pattern_detector.analyze_error(error_code, category, severity, context)
        
        # Send alerts
        for alert in alerts:
            self._send_alert(alert)
            
            # Log the alert to security audit
            security_audit_logger.log_suspicious_activity(
                description=f"Alert triggered: {alert.title}",
                details=alert.details
            )
    
    def _send_alert(self, alert: Alert) -> None:
        """Send alert through configured channels"""
        logger.info(f"Sending alert: {alert.title}", extra={
            "alert_id": alert.alert_id,
            "severity": alert.severity.value,
            "channels": [ch.value for ch in alert.channels]
        })
        
        for channel in alert.channels:
            try:
                handler = self.alert_handlers.get(channel)
                if handler:
                    handler(alert)
                else:
                    logger.warning(f"No handler configured for alert channel: {channel.value}")
            except Exception as e:
                logger.error(f"Failed to send alert via {channel.value}: {str(e)}")
    
    def _handle_email_alert(self, alert: Alert) -> None:
        """Handle email alerts (placeholder implementation)"""
        # In production, this would integrate with email service
        alert_dict = asdict(alert)
        # Convert datetime objects to ISO strings for JSON serialization
        if 'timestamp' in alert_dict and hasattr(alert_dict['timestamp'], 'isoformat'):
            alert_dict['timestamp'] = alert_dict['timestamp'].isoformat()
        # Ensure all datetime objects are converted to strings
        alert_dict = self._serialize_datetime_objects(alert_dict)
        logger.info(f"EMAIL ALERT: {alert.title}", extra={
            "alert_details": alert_dict
        })
    
    def _handle_slack_alert(self, alert: Alert) -> None:
        """Handle Slack alerts (placeholder implementation)"""
        # In production, this would integrate with Slack API
        alert_dict = asdict(alert)
        # Convert datetime objects to ISO strings for JSON serialization
        if 'timestamp' in alert_dict and hasattr(alert_dict['timestamp'], 'isoformat'):
            alert_dict['timestamp'] = alert_dict['timestamp'].isoformat()
        # Ensure all datetime objects are converted to strings
        alert_dict = self._serialize_datetime_objects(alert_dict)
        logger.info(f"SLACK ALERT: {alert.title}", extra={
            "alert_details": alert_dict
        })
    
    def _handle_webhook_alert(self, alert: Alert) -> None:
        """Handle webhook alerts (placeholder implementation)"""
        # In production, this would send HTTP POST to webhook URL
        alert_dict = asdict(alert)
        # Convert datetime objects to ISO strings for JSON serialization
        if 'timestamp' in alert_dict and hasattr(alert_dict['timestamp'], 'isoformat'):
            alert_dict['timestamp'] = alert_dict['timestamp'].isoformat()
        # Ensure all datetime objects are converted to strings
        alert_dict = self._serialize_datetime_objects(alert_dict)
        logger.info(f"WEBHOOK ALERT: {alert.title}", extra={
            "alert_details": alert_dict
        })
    
    def _handle_pagerduty_alert(self, alert: Alert) -> None:
        """Handle PagerDuty alerts (placeholder implementation)"""
        # In production, this would integrate with PagerDuty API
        alert_dict = asdict(alert)
        # Convert datetime objects to ISO strings for JSON serialization
        if 'timestamp' in alert_dict and hasattr(alert_dict['timestamp'], 'isoformat'):
            alert_dict['timestamp'] = alert_dict['timestamp'].isoformat()
        # Ensure all datetime objects are converted to strings
        alert_dict = self._serialize_datetime_objects(alert_dict)
        logger.critical(f"PAGERDUTY ALERT: {alert.title}", extra={
            "alert_details": alert_dict
        })
    
    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error metrics summary for the specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        with self.metrics_lock:
            recent_metrics = {
                code: metric for code, metric in self.metrics.items()
                if metric.last_occurrence >= cutoff_time
            }
        
        summary = {
            "total_errors": sum(metric.count for metric in recent_metrics.values()),
            "unique_error_codes": len(recent_metrics),
            "error_breakdown": {},
            "severity_breakdown": defaultdict(int),
            "category_breakdown": defaultdict(int),
            "top_errors": [],
            "affected_users": set(),
            "affected_ips": set()
        }
        
        for code, metric in recent_metrics.items():
            summary["error_breakdown"][code] = metric.count
            summary["severity_breakdown"][metric.severity.value] += metric.count
            summary["category_breakdown"][metric.category.value] += metric.count
            summary["affected_users"].update(metric.user_ids)
            summary["affected_ips"].update(metric.client_ips)
        
        # Convert sets to counts for JSON serialization
        summary["affected_users"] = len(summary["affected_users"])
        summary["affected_ips"] = len(summary["affected_ips"])
        
        # Get top 10 errors
        summary["top_errors"] = sorted(
            [(code, metric.count) for code, metric in recent_metrics.items()],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return summary


# Global error monitor instance
error_monitor = ErrorMonitor()


def record_error(
    error_code: str,
    category: ErrorCategory,
    severity: ErrorSeverity,
    **context
) -> None:
    """Convenience function to record errors"""
    error_monitor.record_error(error_code, category, severity, context)