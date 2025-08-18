"""
Rate limiting monitoring and alerting system.
Provides comprehensive monitoring, metrics collection, and alerting for rate limiting events.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from app.core.rate_limiter import RateLimiter, RateLimitType, get_rate_limiter
from app.core.error_monitoring import security_logger

logger = logging.getLogger(__name__)


class AlertLevel(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Types of rate limiting alerts."""
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    BRUTE_FORCE_DETECTED = "brute_force_detected"
    DDOS_ATTACK = "ddos_attack"
    SECURITY_BLOCK_CREATED = "security_block_created"
    UNUSUAL_TRAFFIC_PATTERN = "unusual_traffic_pattern"
    SYSTEM_OVERLOAD = "system_overload"


@dataclass
class RateLimitMetric:
    """Rate limiting metric data structure."""
    timestamp: datetime
    metric_type: str
    identifier: str
    limit_type: RateLimitType
    current_usage: int
    limit: int
    remaining: int
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    user_tier: Optional[str] = None


@dataclass
class SecurityAlert:
    """Security alert data structure."""
    alert_id: str
    timestamp: datetime
    alert_type: AlertType
    level: AlertLevel
    identifier: str
    message: str
    details: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class RateLimitMonitor:
    """
    Comprehensive monitoring system for rate limiting events.
    Collects metrics, generates alerts, and provides analytics.
    """
    
    def __init__(self):
        self.rate_limiter: Optional[RateLimiter] = None
        self.metrics_buffer: List[RateLimitMetric] = []
        self.active_alerts: Dict[str, SecurityAlert] = {}
        self.alert_thresholds = self._get_alert_thresholds()
        self.monitoring_enabled = True
    
    def _get_alert_thresholds(self) -> Dict[str, Dict[str, Any]]:
        """Define alert thresholds for different scenarios."""
        return {
            "rate_limit_exceeded": {
                "threshold_multiplier": 1.5,  # Alert when usage exceeds 150% of limit
                "consecutive_violations": 3,   # Alert after 3 consecutive violations
                "time_window_minutes": 5       # Within 5 minutes
            },
            "brute_force_detected": {
                "attempts_threshold": 10,      # 10 failed attempts
                "time_window_minutes": 10,     # Within 10 minutes
                "ip_threshold": 5              # From same IP
            },
            "ddos_attack": {
                "requests_per_second": 100,    # 100 req/sec from single IP
                "concurrent_ips": 50,          # 50+ IPs hitting same endpoint
                "traffic_spike_multiplier": 10 # 10x normal traffic
            },
            "unusual_traffic": {
                "deviation_threshold": 3.0,    # 3 standard deviations
                "minimum_requests": 100,       # Minimum requests for analysis
                "analysis_window_hours": 1     # 1 hour analysis window
            },
            "system_overload": {
                "redis_latency_ms": 1000,      # Redis response > 1 second
                "error_rate_threshold": 0.05,  # 5% error rate
                "memory_usage_threshold": 0.85 # 85% memory usage
            }
        }
    
    async def initialize(self):
        """Initialize the monitoring system."""
        try:
            self.rate_limiter = await get_rate_limiter()
            logger.info("Rate limit monitoring system initialized")
        except Exception as e:
            logger.error(f"Failed to initialize rate limit monitoring: {e}")
            self.monitoring_enabled = False
    
    async def record_metric(self, metric: RateLimitMetric):
        """Record a rate limiting metric."""
        if not self.monitoring_enabled:
            return
        
        try:
            self.metrics_buffer.append(metric)
            
            # Check for alert conditions
            await self._check_alert_conditions(metric)
            
            # Flush metrics buffer if it gets too large
            if len(self.metrics_buffer) > 1000:
                await self._flush_metrics_buffer()
        
        except Exception as e:
            logger.error(f"Error recording rate limit metric: {e}")
    
    async def _check_alert_conditions(self, metric: RateLimitMetric):
        """Check if the metric triggers any alert conditions."""
        try:
            # Check for rate limit violations
            if metric.current_usage > metric.limit:
                await self._check_rate_limit_violation_alert(metric)
            
            # Check for unusual traffic patterns
            await self._check_unusual_traffic_alert(metric)
            
            # Check for potential DDoS
            if metric.limit_type == RateLimitType.DDOS:
                await self._check_ddos_alert(metric)
        
        except Exception as e:
            logger.error(f"Error checking alert conditions: {e}")
    
    async def _check_rate_limit_violation_alert(self, metric: RateLimitMetric):
        """Check for rate limit violation patterns that warrant alerts."""
        alert_key = f"rate_limit_{metric.identifier}_{metric.limit_type.value}"
        threshold = self.alert_thresholds["rate_limit_exceeded"]
        
        # Count recent violations
        recent_violations = [
            m for m in self.metrics_buffer[-100:]  # Last 100 metrics
            if (
                m.identifier == metric.identifier and
                m.limit_type == metric.limit_type and
                m.current_usage > m.limit and
                (datetime.utcnow() - m.timestamp).total_seconds() < threshold["time_window_minutes"] * 60
            )
        ]
        
        if len(recent_violations) >= threshold["consecutive_violations"]:
            await self._create_alert(
                alert_key,
                AlertType.RATE_LIMIT_EXCEEDED,
                AlertLevel.WARNING,
                metric.identifier,
                f"Repeated rate limit violations detected for {metric.limit_type.value}",
                {
                    "limit_type": metric.limit_type.value,
                    "violation_count": len(recent_violations),
                    "current_usage": metric.current_usage,
                    "limit": metric.limit,
                    "endpoint": metric.endpoint,
                    "client_ip": metric.client_ip
                }
            )
    
    async def _check_ddos_alert(self, metric: RateLimitMetric):
        """Check for DDoS attack patterns."""
        if not metric.client_ip:
            return
        
        alert_key = f"ddos_{metric.client_ip}"
        threshold = self.alert_thresholds["ddos_attack"]
        
        # Check if this IP is making too many requests
        if metric.current_usage > threshold["requests_per_second"] * 60:  # Convert to per minute
            await self._create_alert(
                alert_key,
                AlertType.DDOS_ATTACK,
                AlertLevel.CRITICAL,
                metric.client_ip,
                f"Potential DDoS attack detected from IP {metric.client_ip}",
                {
                    "client_ip": metric.client_ip,
                    "requests_per_minute": metric.current_usage,
                    "endpoint": metric.endpoint,
                    "user_agent": metric.user_agent,
                    "threshold": threshold["requests_per_second"] * 60
                }
            )
    
    async def _check_unusual_traffic_alert(self, metric: RateLimitMetric):
        """Check for unusual traffic patterns."""
        try:
            if not self.rate_limiter:
                return
            
            # Get historical data for comparison
            recent_metrics = [
                m for m in self.metrics_buffer[-1000:]  # Last 1000 metrics
                if (
                    m.limit_type == metric.limit_type and
                    (datetime.utcnow() - m.timestamp).total_seconds() < 3600  # Last hour
                )
            ]
            
            if len(recent_metrics) < 10:  # Not enough data
                return
            
            # Calculate average and standard deviation
            usage_values = [m.current_usage for m in recent_metrics]
            avg_usage = sum(usage_values) / len(usage_values)
            variance = sum((x - avg_usage) ** 2 for x in usage_values) / len(usage_values)
            std_dev = variance ** 0.5
            
            threshold = self.alert_thresholds["unusual_traffic"]
            
            # Check if current usage is unusual
            if (
                std_dev > 0 and 
                abs(metric.current_usage - avg_usage) > threshold["deviation_threshold"] * std_dev and
                avg_usage > threshold["minimum_requests"]
            ):
                alert_key = f"unusual_traffic_{metric.limit_type.value}"
                await self._create_alert(
                    alert_key,
                    AlertType.UNUSUAL_TRAFFIC_PATTERN,
                    AlertLevel.WARNING,
                    metric.identifier,
                    f"Unusual traffic pattern detected for {metric.limit_type.value}",
                    {
                        "limit_type": metric.limit_type.value,
                        "current_usage": metric.current_usage,
                        "average_usage": avg_usage,
                        "standard_deviation": std_dev,
                        "deviation_factor": abs(metric.current_usage - avg_usage) / std_dev
                    }
                )
        
        except Exception as e:
            logger.error(f"Error checking unusual traffic patterns: {e}")
    
    async def _create_alert(
        self,
        alert_key: str,
        alert_type: AlertType,
        level: AlertLevel,
        identifier: str,
        message: str,
        details: Dict[str, Any]
    ):
        """Create and store a security alert."""
        # Check if alert already exists and is recent
        if alert_key in self.active_alerts:
            existing_alert = self.active_alerts[alert_key]
            if not existing_alert.resolved and \
               (datetime.utcnow() - existing_alert.timestamp).total_seconds() < 300:  # 5 minutes
                return  # Don't create duplicate alerts
        
        alert = SecurityAlert(
            alert_id=alert_key,
            timestamp=datetime.utcnow(),
            alert_type=alert_type,
            level=level,
            identifier=identifier,
            message=message,
            details=details
        )
        
        self.active_alerts[alert_key] = alert
        
        # Log the alert
        security_logger.log(
            logging.CRITICAL if level == AlertLevel.CRITICAL else 
            logging.WARNING if level == AlertLevel.WARNING else logging.INFO,
            f"Security Alert: {message}",
            extra={
                "alert_type": alert_type.value,
                "alert_level": level.value,
                "identifier": identifier,
                "details": details,
                "timestamp": alert.timestamp.isoformat()
            }
        )
        
        # Trigger additional actions for critical alerts
        if level == AlertLevel.CRITICAL:
            await self._handle_critical_alert(alert)
    
    async def _handle_critical_alert(self, alert: SecurityAlert):
        """Handle critical security alerts."""
        try:
            if alert.alert_type == AlertType.DDOS_ATTACK and self.rate_limiter:
                # Automatically create security block for DDoS attacks
                await self.rate_limiter.create_security_block(
                    f"ip:{alert.identifier}",
                    RateLimitType.DDOS,
                    240,  # 4 hour block
                    "Automatic block due to DDoS detection"
                )
            
            # Additional critical alert handling can be added here:
            # - Send notifications to administrators
            # - Integrate with external alerting systems
            # - Trigger automated responses
            
        except Exception as e:
            logger.error(f"Error handling critical alert: {e}")
    
    async def resolve_alert(self, alert_id: str, resolution_note: str = ""):
        """Resolve an active alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()
            
            security_logger.info(
                f"Security alert resolved: {alert.message}",
                extra={
                    "alert_id": alert_id,
                    "resolution_note": resolution_note,
                    "resolved_at": alert.resolved_at.isoformat()
                }
            )
    
    async def get_active_alerts(self, level: Optional[AlertLevel] = None) -> List[SecurityAlert]:
        """Get list of active alerts, optionally filtered by level."""
        alerts = [
            alert for alert in self.active_alerts.values()
            if not alert.resolved
        ]
        
        if level:
            alerts = [alert for alert in alerts if alert.level == level]
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    async def get_metrics_summary(
        self, 
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """Get summary of rate limiting metrics."""
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
        recent_metrics = [
            m for m in self.metrics_buffer
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return {"message": "No metrics available"}
        
        # Group metrics by type
        metrics_by_type = {}
        for metric in recent_metrics:
            limit_type = metric.limit_type.value
            if limit_type not in metrics_by_type:
                metrics_by_type[limit_type] = []
            metrics_by_type[limit_type].append(metric)
        
        summary = {
            "time_window_hours": time_window_hours,
            "total_requests": len(recent_metrics),
            "by_type": {}
        }
        
        for limit_type, type_metrics in metrics_by_type.items():
            violations = [m for m in type_metrics if m.current_usage > m.limit]
            
            summary["by_type"][limit_type] = {
                "total_requests": len(type_metrics),
                "violations": len(violations),
                "violation_rate": len(violations) / len(type_metrics) if type_metrics else 0,
                "avg_usage": sum(m.current_usage for m in type_metrics) / len(type_metrics),
                "max_usage": max(m.current_usage for m in type_metrics),
                "unique_identifiers": len(set(m.identifier for m in type_metrics))
            }
        
        return summary
    
    async def _flush_metrics_buffer(self):
        """Flush metrics buffer to persistent storage (if configured)."""
        try:
            # In a production environment, you might want to:
            # - Store metrics in a time-series database
            # - Send metrics to monitoring systems
            # - Archive old metrics
            
            # For now, we'll keep only the most recent metrics
            if len(self.metrics_buffer) > 10000:
                self.metrics_buffer = self.metrics_buffer[-5000:]  # Keep last 5000
            
            logger.debug(f"Metrics buffer maintained at {len(self.metrics_buffer)} entries")
        
        except Exception as e:
            logger.error(f"Error flushing metrics buffer: {e}")
    
    async def cleanup_old_data(self):
        """Clean up old metrics and resolved alerts."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            # Remove old metrics
            self.metrics_buffer = [
                m for m in self.metrics_buffer
                if m.timestamp >= cutoff_time
            ]
            
            # Remove old resolved alerts
            old_alert_keys = [
                key for key, alert in self.active_alerts.items()
                if alert.resolved and alert.resolved_at and
                alert.resolved_at < cutoff_time
            ]
            
            for key in old_alert_keys:
                del self.active_alerts[key]
            
            logger.info(
                f"Cleaned up old data: {len(old_alert_keys)} alerts removed, "
                f"{len(self.metrics_buffer)} metrics retained"
            )
        
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    async def start_background_tasks(self):
        """Start background monitoring tasks."""
        if not self.monitoring_enabled:
            return
        
        async def cleanup_task():
            while True:
                try:
                    await asyncio.sleep(3600)  # Run every hour
                    await self.cleanup_old_data()
                except Exception as e:
                    logger.error(f"Error in cleanup task: {e}")
        
        # Start cleanup task
        asyncio.create_task(cleanup_task())
        logger.info("Rate limit monitoring background tasks started")


# Global monitoring instance
rate_limit_monitor = RateLimitMonitor()


async def get_rate_limit_monitor() -> RateLimitMonitor:
    """Dependency to get rate limit monitor instance."""
    if not rate_limit_monitor.monitoring_enabled:
        await rate_limit_monitor.initialize()
    return rate_limit_monitor


# Helper function to record metrics from middleware
async def record_rate_limit_metric(
    identifier: str,
    limit_type: RateLimitType,
    current_usage: int,
    limit: int,
    remaining: int,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    endpoint: Optional[str] = None,
    user_tier: Optional[str] = None
):
    """Helper function to record rate limiting metrics."""
    try:
        monitor = await get_rate_limit_monitor()
        metric = RateLimitMetric(
            timestamp=datetime.utcnow(),
            metric_type="rate_limit_check",
            identifier=identifier,
            limit_type=limit_type,
            current_usage=current_usage,
            limit=limit,
            remaining=remaining,
            client_ip=client_ip,
            user_agent=user_agent,
            endpoint=endpoint,
            user_tier=user_tier
        )
        await monitor.record_metric(metric)
    except Exception as e:
        logger.error(f"Error recording rate limit metric: {e}")