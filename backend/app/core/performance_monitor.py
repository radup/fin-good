"""
Performance Monitoring Logger for FinGood Financial Application

This module provides comprehensive performance monitoring and metrics collection
for API endpoints, database operations, system resources, and business processes.
Includes alerting for performance degradation and capacity planning data.
"""

import asyncio
import time
import psutil
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Callable, AsyncContextManager
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import threading
from functools import wraps
import inspect

from app.core.logging_config import get_logger, LogCategory


class MetricType(Enum):
    """Types of performance metrics"""
    API_REQUEST = "api_request"
    DATABASE_QUERY = "database_query"
    FILE_OPERATION = "file_operation"
    BUSINESS_PROCESS = "business_process"
    SYSTEM_RESOURCE = "system_resource"
    EXTERNAL_API = "external_api"
    CACHE_OPERATION = "cache_operation"
    AUTHENTICATION = "authentication"
    DATA_PROCESSING = "data_processing"
    VALIDATION = "validation"


class PerformanceLevel(Enum):
    """Performance levels for alerting"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    metric_id: str
    timestamp: str
    metric_type: MetricType
    operation_name: str
    duration_ms: float
    success: bool
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    response_size_bytes: Optional[int] = None
    db_queries: Optional[int] = None
    db_duration_ms: Optional[float] = None
    cache_hits: Optional[int] = None
    cache_misses: Optional[int] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    client_ip: Optional[str] = None
    error_message: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['metric_type'] = self.metric_type.value
        return data


@dataclass
class SystemMetrics:
    """System resource metrics"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    active_connections: int
    load_average: Optional[List[float]] = None


class PerformanceThresholds:
    """Performance thresholds for alerting"""
    
    # API endpoint thresholds (milliseconds)
    API_THRESHOLDS = {
        'excellent': 100,
        'good': 250,
        'acceptable': 500,
        'poor': 1000,
        'critical': 2000
    }
    
    # Database query thresholds (milliseconds)
    DB_THRESHOLDS = {
        'excellent': 50,
        'good': 100,
        'acceptable': 250,
        'poor': 500,
        'critical': 1000
    }
    
    # System resource thresholds (percentage)
    SYSTEM_THRESHOLDS = {
        'cpu_excellent': 20,
        'cpu_good': 40,
        'cpu_acceptable': 60,
        'cpu_poor': 80,
        'cpu_critical': 95,
        'memory_excellent': 30,
        'memory_good': 50,
        'memory_acceptable': 70,
        'memory_poor': 85,
        'memory_critical': 95,
        'disk_excellent': 20,
        'disk_good': 40,
        'disk_acceptable': 60,
        'disk_poor': 80,
        'disk_critical': 90
    }
    
    @classmethod
    def get_performance_level(cls, metric_type: MetricType, value: float) -> PerformanceLevel:
        """Determine performance level based on metric type and value"""
        
        if metric_type == MetricType.API_REQUEST:
            thresholds = cls.API_THRESHOLDS
        elif metric_type == MetricType.DATABASE_QUERY:
            thresholds = cls.DB_THRESHOLDS
        else:
            # Use API thresholds as default
            thresholds = cls.API_THRESHOLDS
        
        if value <= thresholds['excellent']:
            return PerformanceLevel.EXCELLENT
        elif value <= thresholds['good']:
            return PerformanceLevel.GOOD
        elif value <= thresholds['acceptable']:
            return PerformanceLevel.ACCEPTABLE
        elif value <= thresholds['poor']:
            return PerformanceLevel.POOR
        else:
            return PerformanceLevel.CRITICAL


class PerformanceCollector:
    """
    Collects and aggregates performance metrics for analysis and alerting
    """
    
    def __init__(self, window_size: int = 1000):
        """
        Initialize performance collector
        
        Args:
            window_size: Number of metrics to keep in memory for analysis
        """
        self.window_size = window_size
        self.metrics_history = defaultdict(lambda: deque(maxlen=window_size))
        self.aggregated_stats = defaultdict(dict)
        self.lock = threading.Lock()
        
        # Performance counters
        self.counters = defaultdict(int)
        
        # System monitoring
        self.system_monitor_enabled = True
        self.system_metrics_interval = 60  # seconds
    
    def add_metric(self, metric: PerformanceMetric):
        """Add a performance metric to the collector"""
        with self.lock:
            # Store in history
            key = f"{metric.metric_type.value}_{metric.operation_name}"
            self.metrics_history[key].append(metric)
            
            # Update counters
            self.counters[f"{metric.metric_type.value}_total"] += 1
            if not metric.success:
                self.counters[f"{metric.metric_type.value}_errors"] += 1
            
            # Update aggregated statistics
            self._update_aggregated_stats(key, metric)
    
    def _update_aggregated_stats(self, key: str, metric: PerformanceMetric):
        """Update aggregated statistics for a metric type"""
        if key not in self.aggregated_stats:
            self.aggregated_stats[key] = {
                'count': 0,
                'total_duration': 0,
                'min_duration': float('inf'),
                'max_duration': 0,
                'error_count': 0,
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
        
        stats = self.aggregated_stats[key]
        stats['count'] += 1
        stats['total_duration'] += metric.duration_ms
        stats['min_duration'] = min(stats['min_duration'], metric.duration_ms)
        stats['max_duration'] = max(stats['max_duration'], metric.duration_ms)
        stats['avg_duration'] = stats['total_duration'] / stats['count']
        stats['last_updated'] = datetime.now(timezone.utc).isoformat()
        
        if not metric.success:
            stats['error_count'] += 1
            stats['error_rate'] = stats['error_count'] / stats['count']
    
    def get_stats(self, metric_type: Optional[MetricType] = None) -> Dict[str, Any]:
        """Get aggregated statistics"""
        with self.lock:
            if metric_type:
                prefix = metric_type.value
                return {
                    key: stats for key, stats in self.aggregated_stats.items()
                    if key.startswith(prefix)
                }
            return dict(self.aggregated_stats)
    
    def get_recent_metrics(
        self, 
        metric_type: MetricType, 
        operation_name: str,
        limit: int = 100
    ) -> List[PerformanceMetric]:
        """Get recent metrics for a specific operation"""
        key = f"{metric_type.value}_{operation_name}"
        with self.lock:
            metrics = list(self.metrics_history[key])
            return metrics[-limit:] if limit else metrics
    
    def check_performance_alerts(self, metric: PerformanceMetric) -> List[Dict[str, Any]]:
        """Check if metric triggers any performance alerts"""
        alerts = []
        
        # Check duration thresholds
        performance_level = PerformanceThresholds.get_performance_level(
            metric.metric_type, metric.duration_ms
        )
        
        if performance_level in [PerformanceLevel.POOR, PerformanceLevel.CRITICAL]:
            alerts.append({
                'type': 'performance_degradation',
                'severity': 'critical' if performance_level == PerformanceLevel.CRITICAL else 'warning',
                'message': f"Performance degradation detected for {metric.operation_name}",
                'metric': metric.to_dict(),
                'performance_level': performance_level.value,
                'threshold_exceeded': True
            })
        
        # Check error rate
        key = f"{metric.metric_type.value}_{metric.operation_name}"
        stats = self.aggregated_stats.get(key, {})
        error_rate = stats.get('error_rate', 0)
        
        if error_rate > 0.1:  # 10% error rate threshold
            alerts.append({
                'type': 'high_error_rate',
                'severity': 'critical' if error_rate > 0.25 else 'warning',
                'message': f"High error rate detected for {metric.operation_name}",
                'error_rate': error_rate,
                'operation': metric.operation_name,
                'metric_type': metric.metric_type.value
            })
        
        return alerts


class PerformanceMonitor:
    """
    Main performance monitoring system with logging and alerting
    """
    
    def __init__(self, enable_system_monitoring: bool = True):
        """
        Initialize performance monitor
        
        Args:
            enable_system_monitoring: Whether to enable system resource monitoring
        """
        self.logger = get_logger('fingood.performance', LogCategory.PERFORMANCE)
        self.collector = PerformanceCollector()
        self.enable_system_monitoring = enable_system_monitoring
        
        # System monitoring task
        self._system_monitor_task = None
        
        # Performance alert handlers
        self.alert_handlers = []
    
    async def start_monitoring(self):
        """Start performance monitoring"""
        if self.enable_system_monitoring:
            self._system_monitor_task = asyncio.create_task(self._system_monitor_loop())
        
        self.logger.info(
            "Performance monitoring started",
            extra={
                'metric_type': 'system',
                'system_monitoring_enabled': self.enable_system_monitoring
            }
        )
    
    async def stop_monitoring(self):
        """Stop performance monitoring"""
        if self._system_monitor_task:
            self._system_monitor_task.cancel()
            try:
                await self._system_monitor_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info(
            "Performance monitoring stopped",
            extra={'metric_type': 'system'}
        )
    
    async def _system_monitor_loop(self):
        """System resource monitoring loop"""
        while True:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(self.collector.system_metrics_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(
                    f"System monitoring error: {str(e)}",
                    extra={'metric_type': 'system', 'error': str(e)}
                )
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _collect_system_metrics(self):
        """Collect system resource metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            # Network metrics
            network = psutil.net_io_counters()
            
            # System load (Unix only)
            load_avg = None
            try:
                load_avg = list(psutil.getloadavg())
            except AttributeError:
                pass  # Windows doesn't have load average
            
            # Active connections
            connections = len(psutil.net_connections())
            
            system_metrics = SystemMetrics(
                timestamp=datetime.now(timezone.utc).isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_available_mb=memory.available / 1024 / 1024,
                disk_usage_percent=disk.percent,
                disk_free_gb=disk.free / 1024 / 1024 / 1024,
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                active_connections=connections,
                load_average=load_avg
            )
            
            # Log system metrics
            self.logger.info(
                "System metrics collected",
                extra={
                    'metric_type': 'system_resource',
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'disk_percent': disk.percent,
                    'active_connections': connections,
                    **asdict(system_metrics)
                }
            )
            
            # Check for system resource alerts
            await self._check_system_alerts(system_metrics)
            
        except Exception as e:
            self.logger.error(
                f"Failed to collect system metrics: {str(e)}",
                extra={'metric_type': 'system', 'error': str(e)}
            )
    
    async def _check_system_alerts(self, metrics: SystemMetrics):
        """Check system metrics for alert conditions"""
        alerts = []
        
        # CPU usage alerts
        if metrics.cpu_percent > PerformanceThresholds.SYSTEM_THRESHOLDS['cpu_critical']:
            alerts.append({
                'type': 'high_cpu_usage',
                'severity': 'critical',
                'message': f"Critical CPU usage: {metrics.cpu_percent}%",
                'value': metrics.cpu_percent,
                'threshold': PerformanceThresholds.SYSTEM_THRESHOLDS['cpu_critical']
            })
        elif metrics.cpu_percent > PerformanceThresholds.SYSTEM_THRESHOLDS['cpu_poor']:
            alerts.append({
                'type': 'high_cpu_usage',
                'severity': 'warning',
                'message': f"High CPU usage: {metrics.cpu_percent}%",
                'value': metrics.cpu_percent,
                'threshold': PerformanceThresholds.SYSTEM_THRESHOLDS['cpu_poor']
            })
        
        # Memory usage alerts
        if metrics.memory_percent > PerformanceThresholds.SYSTEM_THRESHOLDS['memory_critical']:
            alerts.append({
                'type': 'high_memory_usage',
                'severity': 'critical',
                'message': f"Critical memory usage: {metrics.memory_percent}%",
                'value': metrics.memory_percent,
                'threshold': PerformanceThresholds.SYSTEM_THRESHOLDS['memory_critical']
            })
        elif metrics.memory_percent > PerformanceThresholds.SYSTEM_THRESHOLDS['memory_poor']:
            alerts.append({
                'type': 'high_memory_usage',
                'severity': 'warning',
                'message': f"High memory usage: {metrics.memory_percent}%",
                'value': metrics.memory_percent,
                'threshold': PerformanceThresholds.SYSTEM_THRESHOLDS['memory_poor']
            })
        
        # Disk usage alerts
        if metrics.disk_usage_percent > PerformanceThresholds.SYSTEM_THRESHOLDS['disk_critical']:
            alerts.append({
                'type': 'high_disk_usage',
                'severity': 'critical',
                'message': f"Critical disk usage: {metrics.disk_usage_percent}%",
                'value': metrics.disk_usage_percent,
                'threshold': PerformanceThresholds.SYSTEM_THRESHOLDS['disk_critical']
            })
        
        # Send alerts
        for alert in alerts:
            await self._send_performance_alert(alert)
    
    async def _send_performance_alert(self, alert: Dict[str, Any]):
        """Send performance alert"""
        self.logger.warning(
            f"Performance alert: {alert['message']}",
            extra={
                'alert_type': alert['type'],
                'severity': alert['severity'],
                'alert_data': alert,
                'metric_type': 'alert'
            }
        )
        
        # Call alert handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                self.logger.error(f"Alert handler failed: {str(e)}")
    
    def add_alert_handler(self, handler: Callable[[Dict[str, Any]], None]):
        """Add a performance alert handler"""
        self.alert_handlers.append(handler)
    
    async def record_metric(
        self,
        metric_type: MetricType,
        operation_name: str,
        duration_ms: float,
        success: bool = True,
        **kwargs
    ) -> str:
        """
        Record a performance metric
        
        Args:
            metric_type: Type of metric
            operation_name: Name of the operation
            duration_ms: Duration in milliseconds
            success: Whether the operation was successful
            **kwargs: Additional metric data
            
        Returns:
            Metric ID
        """
        import uuid
        
        metric = PerformanceMetric(
            metric_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            metric_type=metric_type,
            operation_name=operation_name,
            duration_ms=duration_ms,
            success=success,
            **kwargs
        )
        
        # Add to collector
        self.collector.add_metric(metric)
        
        # Log the metric
        self.logger.info(
            f"Performance metric: {operation_name} completed in {duration_ms:.2f}ms",
            extra=metric.to_dict()
        )
        
        # Check for alerts
        alerts = self.collector.check_performance_alerts(metric)
        for alert in alerts:
            await self._send_performance_alert(alert)
        
        return metric.metric_id
    
    @asynccontextmanager
    async def measure_operation(
        self,
        metric_type: MetricType,
        operation_name: str,
        **kwargs
    ) -> AsyncContextManager[Dict[str, Any]]:
        """
        Context manager for measuring operation performance
        
        Args:
            metric_type: Type of metric
            operation_name: Name of the operation
            **kwargs: Additional metric data
            
        Yields:
            Dictionary for storing operation context
        """
        start_time = time.time()
        context = {'start_time': start_time}
        success = True
        error_message = None
        
        try:
            yield context
        except Exception as e:
            success = False
            error_message = str(e)
            raise
        finally:
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            # Record the metric
            await self.record_metric(
                metric_type=metric_type,
                operation_name=operation_name,
                duration_ms=duration_ms,
                success=success,
                error_message=error_message,
                **kwargs
            )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            'aggregated_stats': self.collector.get_stats(),
            'counters': dict(self.collector.counters),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def initialize_performance_monitor(enable_system_monitoring: bool = True) -> PerformanceMonitor:
    """
    Initialize global performance monitor
    
    Args:
        enable_system_monitoring: Whether to enable system monitoring
        
    Returns:
        PerformanceMonitor instance
    """
    global _performance_monitor
    _performance_monitor = PerformanceMonitor(enable_system_monitoring)
    return _performance_monitor


def get_performance_monitor() -> Optional[PerformanceMonitor]:
    """Get the global performance monitor"""
    return _performance_monitor


# Performance measurement decorators
def measure_performance(
    metric_type: MetricType,
    operation_name: Optional[str] = None
):
    """
    Decorator for measuring function performance
    
    Args:
        metric_type: Type of metric
        operation_name: Name of operation (defaults to function name)
    """
    def decorator(func):
        name = operation_name or func.__name__
        
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                if _performance_monitor:
                    async with _performance_monitor.measure_operation(
                        metric_type=metric_type,
                        operation_name=name
                    ):
                        return await func(*args, **kwargs)
                else:
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                if _performance_monitor:
                    start_time = time.time()
                    success = True
                    error_message = None
                    
                    try:
                        result = func(*args, **kwargs)
                        return result
                    except Exception as e:
                        success = False
                        error_message = str(e)
                        raise
                    finally:
                        duration_ms = (time.time() - start_time) * 1000
                        asyncio.create_task(_performance_monitor.record_metric(
                            metric_type=metric_type,
                            operation_name=name,
                            duration_ms=duration_ms,
                            success=success,
                            error_message=error_message
                        ))
                else:
                    return func(*args, **kwargs)
            return sync_wrapper
    return decorator


# Convenience functions for common measurements
async def measure_api_request(
    endpoint: str,
    method: str,
    duration_ms: float,
    status_code: int,
    response_size: Optional[int] = None,
    **kwargs
) -> str:
    """Measure API request performance"""
    if _performance_monitor:
        return await _performance_monitor.record_metric(
            metric_type=MetricType.API_REQUEST,
            operation_name=f"{method} {endpoint}",
            duration_ms=duration_ms,
            success=200 <= status_code < 400,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_size_bytes=response_size,
            **kwargs
        )
    return ""


async def measure_database_query(
    query_type: str,
    duration_ms: float,
    success: bool = True,
    **kwargs
) -> str:
    """Measure database query performance"""
    if _performance_monitor:
        return await _performance_monitor.record_metric(
            metric_type=MetricType.DATABASE_QUERY,
            operation_name=query_type,
            duration_ms=duration_ms,
            success=success,
            **kwargs
        )
    return ""


async def measure_file_operation(
    operation: str,
    file_size: Optional[int] = None,
    duration_ms: float = 0,
    success: bool = True,
    **kwargs
) -> str:
    """Measure file operation performance"""
    if _performance_monitor:
        return await _performance_monitor.record_metric(
            metric_type=MetricType.FILE_OPERATION,
            operation_name=operation,
            duration_ms=duration_ms,
            success=success,
            additional_data={'file_size_bytes': file_size} if file_size else None,
            **kwargs
        )
    return ""