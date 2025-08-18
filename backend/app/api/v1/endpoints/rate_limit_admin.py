"""
Administrative endpoints for rate limiting management and monitoring.
Provides tools for monitoring, managing, and debugging rate limiting system.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta

from app.core.rate_limiter import (
    RateLimiter, 
    RateLimitType, 
    RateLimitTier, 
    get_rate_limiter,
    RateLimitResult
)
from app.core.rate_limit_monitoring import (
    RateLimitMonitor,
    SecurityAlert,
    AlertLevel,
    get_rate_limit_monitor
)
from app.core.cookie_auth import get_current_user_from_cookie
from app.models.user import User

router = APIRouter()


# Dependency for admin access
async def require_admin_access(
    current_user: User = Depends(get_current_user_from_cookie)
) -> User:
    """Require admin role for rate limiting administration."""
    return current_user


@router.get("/status", summary="Get rate limiting system status")
async def get_rate_limit_status(
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
    monitor: RateLimitMonitor = Depends(get_rate_limit_monitor),
    admin_user: User = Depends(require_admin_access)
):
    """Get overall status of the rate limiting system."""
    try:
        # Test Redis connectivity
        redis_status = "connected"
        try:
            if rate_limiter.redis_client:
                await rate_limiter.redis_client.ping()
            else:
                redis_status = "not_initialized"
        except Exception:
            redis_status = "disconnected"
        
        # Get monitoring status
        monitoring_status = "enabled" if monitor.monitoring_enabled else "disabled"
        
        # Get active alerts count
        active_alerts = await monitor.get_active_alerts()
        critical_alerts = [a for a in active_alerts if a.level == AlertLevel.CRITICAL]
        
        return {
            "system_status": "operational" if redis_status == "connected" else "degraded",
            "redis_status": redis_status,
            "monitoring_status": monitoring_status,
            "active_alerts": len(active_alerts),
            "critical_alerts": len(critical_alerts),
            "metrics_buffer_size": len(monitor.metrics_buffer),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting rate limit status: {str(e)}"
        )


@router.get("/alerts", summary="Get active security alerts")
async def get_active_alerts(
    level: Optional[AlertLevel] = Query(None, description="Filter by alert level"),
    monitor: RateLimitMonitor = Depends(get_rate_limit_monitor),
    admin_user: User = Depends(require_admin_access)
) -> List[Dict[str, Any]]:
    """Get list of active security alerts from rate limiting system."""
    try:
        alerts = await monitor.get_active_alerts(level)
        return [
            {
                "alert_id": alert.alert_id,
                "timestamp": alert.timestamp.isoformat(),
                "alert_type": alert.alert_type.value,
                "level": alert.level.value,
                "identifier": alert.identifier,
                "message": alert.message,
                "details": alert.details,
                "resolved": alert.resolved,
                "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
            }
            for alert in alerts
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting alerts: {str(e)}"
        )


@router.post("/alerts/{alert_id}/resolve", summary="Resolve a security alert")
async def resolve_alert(
    alert_id: str,
    resolution_note: str = "",
    monitor: RateLimitMonitor = Depends(get_rate_limit_monitor),
    admin_user: User = Depends(require_admin_access)
):
    """Resolve an active security alert."""
    try:
        await monitor.resolve_alert(alert_id, resolution_note)
        return {"message": "Alert resolved successfully", "alert_id": alert_id}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resolving alert: {str(e)}"
        )


@router.get("/metrics/summary", summary="Get rate limiting metrics summary")
async def get_metrics_summary(
    hours: int = Query(24, ge=1, le=168, description="Time window in hours (1-168)"),
    monitor: RateLimitMonitor = Depends(get_rate_limit_monitor),
    admin_user: User = Depends(require_admin_access)
) -> Dict[str, Any]:
    """Get summary of rate limiting metrics for specified time window."""
    try:
        summary = await monitor.get_metrics_summary(hours)
        return summary
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting metrics summary: {str(e)}"
        )


@router.get("/limits/{identifier}", summary="Get rate limit status for identifier")
async def get_identifier_limits(
    identifier: str,
    limit_type: RateLimitType = Query(..., description="Type of rate limit to check"),
    user_tier: RateLimitTier = Query(RateLimitTier.FREE, description="User tier"),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
    admin_user: User = Depends(require_admin_access)
) -> Dict[str, RateLimitResult]:
    """Get current rate limit status for a specific identifier."""
    try:
        status_data = await rate_limiter.get_rate_limit_status(
            identifier, limit_type, user_tier
        )
        
        # Convert RateLimitResult objects to dictionaries
        return {
            window: {
                "allowed": result.allowed,
                "remaining": result.remaining,
                "reset_time": result.reset_time.isoformat(),
                "retry_after": result.retry_after,
                "current_usage": result.current_usage,
                "limit": result.limit
            }
            for window, result in status_data.items()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting rate limit status: {str(e)}"
        )


@router.delete("/limits/{identifier}", summary="Reset rate limits for identifier")
async def reset_identifier_limits(
    identifier: str,
    limit_type: RateLimitType = Query(..., description="Type of rate limit to reset"),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
    admin_user: User = Depends(require_admin_access)
):
    """Reset rate limits for a specific identifier (admin function)."""
    try:
        await rate_limiter.reset_rate_limits(identifier, limit_type)
        return {
            "message": "Rate limits reset successfully",
            "identifier": identifier,
            "limit_type": limit_type.value
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resetting rate limits: {str(e)}"
        )


@router.get("/blocks/{identifier}", summary="Check security blocks for identifier")
async def check_security_blocks(
    identifier: str,
    block_type: RateLimitType = Query(..., description="Type of security block to check"),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
    admin_user: User = Depends(require_admin_access)
):
    """Check if identifier has any active security blocks."""
    try:
        block_info = await rate_limiter.check_security_block(identifier, block_type)
        
        if block_info:
            return {
                "blocked": True,
                "blocked_until": block_info.blocked_until.isoformat(),
                "reason": block_info.reason,
                "attempt_count": block_info.attempt_count,
                "block_type": block_info.block_type.value
            }
        else:
            return {"blocked": False}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking security blocks: {str(e)}"
        )


@router.delete("/blocks/{identifier}", summary="Remove security block for identifier")
async def remove_security_block(
    identifier: str,
    block_type: RateLimitType = Query(..., description="Type of security block to remove"),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
    admin_user: User = Depends(require_admin_access)
):
    """Remove security block for a specific identifier (admin function)."""
    try:
        await rate_limiter.remove_security_block(identifier, block_type)
        return {
            "message": "Security block removed successfully",
            "identifier": identifier,
            "block_type": block_type.value
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing security block: {str(e)}"
        )


@router.post("/blocks/{identifier}", summary="Create security block for identifier")
async def create_security_block(
    identifier: str,
    block_type: RateLimitType = Query(..., description="Type of security block to create"),
    duration_minutes: int = Query(..., ge=1, le=1440, description="Block duration in minutes"),
    reason: str = Query(..., min_length=1, description="Reason for the block"),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
    admin_user: User = Depends(require_admin_access)
):
    """Create a security block for a specific identifier (admin function)."""
    try:
        await rate_limiter.create_security_block(
            identifier, block_type, duration_minutes, f"Admin block: {reason}"
        )
        return {
            "message": "Security block created successfully",
            "identifier": identifier,
            "block_type": block_type.value,
            "duration_minutes": duration_minutes,
            "reason": reason
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating security block: {str(e)}"
        )


@router.post("/maintenance/cleanup", summary="Run maintenance cleanup")
async def run_maintenance_cleanup(
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
    monitor: RateLimitMonitor = Depends(get_rate_limit_monitor),
    admin_user: User = Depends(require_admin_access)
):
    """Run maintenance cleanup for rate limiting data."""
    try:
        # Clean up expired rate limiting data
        await rate_limiter.cleanup_expired_data()
        
        # Clean up old monitoring data
        await monitor.cleanup_old_data()
        
        return {
            "message": "Maintenance cleanup completed successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during maintenance cleanup: {str(e)}"
        )


@router.get("/config", summary="Get current rate limiting configuration")
async def get_rate_limit_config(
    admin_user: User = Depends(require_admin_access)
):
    """Get current rate limiting configuration settings."""
    from app.core.config import settings
    
    return {
        "rate_limiting_enabled": settings.ENABLE_RATE_LIMITING,
        "monitoring_enabled": settings.ENABLE_RATE_LIMIT_MONITORING,
        "automatic_blocks_enabled": settings.ENABLE_AUTOMATIC_SECURITY_BLOCKS,
        "default_limits": {
            "requests_per_minute": settings.DEFAULT_REQUESTS_PER_MINUTE,
            "requests_per_hour": settings.DEFAULT_REQUESTS_PER_HOUR,
            "requests_per_day": settings.DEFAULT_REQUESTS_PER_DAY
        },
        "auth_limits": {
            "requests_per_minute": settings.AUTH_REQUESTS_PER_MINUTE,
            "requests_per_hour": settings.AUTH_REQUESTS_PER_HOUR,
            "block_duration_minutes": settings.AUTH_BLOCK_DURATION_MINUTES
        },
        "brute_force_limits": {
            "attempts_per_minute": settings.BRUTE_FORCE_ATTEMPTS_PER_MINUTE,
            "attempts_per_hour": settings.BRUTE_FORCE_ATTEMPTS_PER_HOUR,
            "block_duration_minutes": settings.BRUTE_FORCE_BLOCK_DURATION_MINUTES
        },
        "ddos_limits": {
            "requests_per_minute": settings.DDOS_REQUESTS_PER_MINUTE,
            "requests_per_hour": settings.DDOS_REQUESTS_PER_HOUR,
            "block_duration_minutes": settings.DDOS_BLOCK_DURATION_MINUTES
        },
        "trusted_ip_ranges": settings.TRUSTED_IP_RANGES
    }