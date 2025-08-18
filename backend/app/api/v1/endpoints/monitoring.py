"""
Error Monitoring and Health Check Endpoints

This module provides endpoints for monitoring error rates, system health,
and error analytics for operational and security monitoring.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer

from app.core.error_monitoring import error_monitor
from app.schemas.error import ErrorCategory, ErrorSeverity

router = APIRouter()
security = HTTPBearer()


@router.get("/health", summary="System Health Check")
async def health_check() -> Dict[str, Any]:
    """
    Basic system health check endpoint
    
    Returns:
        System health status and basic metrics
    """
    try:
        # Get recent error metrics
        metrics = error_monitor.get_metrics_summary(hours=1)
        
        # Determine health status based on error rates
        health_status = "healthy"
        if metrics["total_errors"] > 100:  # High error rate
            health_status = "degraded"
        
        critical_errors = metrics["severity_breakdown"].get("critical", 0)
        if critical_errors > 0:
            health_status = "unhealthy"
        
        return {
            "status": health_status,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "environment": "production",  # Should come from config
            "metrics": {
                "total_errors_last_hour": metrics["total_errors"],
                "critical_errors_last_hour": critical_errors,
                "unique_error_codes": metrics["unique_error_codes"],
                "affected_users": metrics["affected_users"],
                "affected_ips": metrics["affected_ips"]
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": "Health check failed",
            "details": str(e)
        }


@router.get("/metrics", summary="Error Metrics Summary")
async def get_error_metrics(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back (1-168)"),
    token: str = Depends(security)  # Require authentication for sensitive metrics
) -> Dict[str, Any]:
    """
    Get comprehensive error metrics for monitoring and analytics
    
    Args:
        hours: Number of hours to look back for metrics
        token: Bearer token for authentication
        
    Returns:
        Detailed error metrics and analytics
    """
    try:
        # TODO: Validate token and check permissions
        # For now, we'll assume the token is valid
        
        metrics = error_monitor.get_metrics_summary(hours=hours)
        
        return {
            "period": {
                "hours": hours,
                "start_time": (datetime.utcnow() - timedelta(hours=hours)).isoformat(),
                "end_time": datetime.utcnow().isoformat()
            },
            "summary": {
                "total_errors": metrics["total_errors"],
                "unique_error_codes": metrics["unique_error_codes"],
                "affected_users": metrics["affected_users"],
                "affected_ips": metrics["affected_ips"]
            },
            "breakdown": {
                "by_severity": metrics["severity_breakdown"],
                "by_category": metrics["category_breakdown"],
                "by_error_code": metrics["error_breakdown"]
            },
            "top_errors": metrics["top_errors"],
            "trends": {
                "error_rate_per_hour": metrics["total_errors"] / hours,
                "critical_error_rate": metrics["severity_breakdown"].get("critical", 0) / hours if hours > 0 else 0
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve metrics: {str(e)}"
        )


@router.get("/errors/critical", summary="Critical Errors Report")
async def get_critical_errors(
    hours: int = Query(24, ge=1, le=48, description="Hours to look back"),
    token: str = Depends(security)
) -> Dict[str, Any]:
    """
    Get details about critical errors requiring immediate attention
    
    Args:
        hours: Number of hours to look back
        token: Bearer token for authentication
        
    Returns:
        Critical error details and recommended actions
    """
    try:
        # TODO: Validate token and ensure user has proper permissions
        
        metrics = error_monitor.get_metrics_summary(hours=hours)
        
        critical_errors = []
        with error_monitor.metrics_lock:
            for error_code, metric in error_monitor.metrics.items():
                if (metric.severity == ErrorSeverity.CRITICAL and 
                    metric.last_occurrence >= datetime.utcnow() - timedelta(hours=hours)):
                    
                    critical_errors.append({
                        "error_code": error_code,
                        "category": metric.category.value,
                        "count": metric.count,
                        "first_occurrence": metric.first_occurrence.isoformat(),
                        "last_occurrence": metric.last_occurrence.isoformat(),
                        "affected_users": len(metric.user_ids),
                        "affected_ips": len(metric.client_ips),
                        "affected_endpoints": list(metric.endpoints)[:10],  # Limit for performance
                        "recommended_actions": _get_recommended_actions(error_code, metric.category)
                    })
        
        return {
            "period": {
                "hours": hours,
                "start_time": (datetime.utcnow() - timedelta(hours=hours)).isoformat(),
                "end_time": datetime.utcnow().isoformat()
            },
            "summary": {
                "total_critical_errors": len(critical_errors),
                "total_occurrences": sum(err["count"] for err in critical_errors),
                "unique_affected_users": len(set().union(*[error_monitor.metrics[err["error_code"]].user_ids for err in critical_errors if err["error_code"] in error_monitor.metrics])),
                "requires_immediate_attention": len(critical_errors) > 0
            },
            "critical_errors": sorted(critical_errors, key=lambda x: x["count"], reverse=True)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve critical errors: {str(e)}"
        )


@router.get("/errors/patterns", summary="Error Pattern Analysis")
async def get_error_patterns(
    hours: int = Query(24, ge=1, le=168, description="Hours to analyze"),
    token: str = Depends(security)
) -> Dict[str, Any]:
    """
    Analyze error patterns for security and operational insights
    
    Args:
        hours: Number of hours to analyze
        token: Bearer token for authentication
        
    Returns:
        Error pattern analysis and insights
    """
    try:
        # TODO: Validate token
        
        metrics = error_monitor.get_metrics_summary(hours=hours)
        
        # Analyze patterns
        patterns = {
            "authentication_issues": _analyze_auth_patterns(hours),
            "system_degradation": _analyze_system_patterns(hours),
            "security_concerns": _analyze_security_patterns(hours),
            "user_experience_impact": _analyze_ux_patterns(hours)
        }
        
        # Generate insights
        insights = []
        
        if metrics["severity_breakdown"].get("critical", 0) > 5:
            insights.append({
                "type": "critical",
                "message": f"High number of critical errors ({metrics['severity_breakdown']['critical']}) detected",
                "recommendation": "Immediate investigation required"
            })
        
        auth_errors = metrics["category_breakdown"].get("authentication", 0)
        if auth_errors > 50:
            insights.append({
                "type": "security",
                "message": f"High authentication failure rate ({auth_errors} failures)",
                "recommendation": "Check for potential brute force attacks"
            })
        
        if metrics["affected_ips"] > 100:
            insights.append({
                "type": "operational",
                "message": f"Errors affecting many IPs ({metrics['affected_ips']})",
                "recommendation": "Possible system-wide issue"
            })
        
        return {
            "period": {
                "hours": hours,
                "start_time": (datetime.utcnow() - timedelta(hours=hours)).isoformat(),
                "end_time": datetime.utcnow().isoformat()
            },
            "patterns": patterns,
            "insights": insights,
            "recommendations": _generate_recommendations(metrics, patterns)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze error patterns: {str(e)}"
        )


def _get_recommended_actions(error_code: str, category: ErrorCategory) -> list:
    """Get recommended actions for specific error types"""
    actions = {
        ErrorCategory.SYSTEM_ERROR: [
            "Check system logs for root cause",
            "Verify infrastructure health",
            "Scale resources if needed",
            "Contact DevOps team"
        ],
        ErrorCategory.AUTHENTICATION: [
            "Review authentication logs",
            "Check for brute force patterns",
            "Verify token service health",
            "Consider rate limiting"
        ],
        ErrorCategory.FINANCIAL_COMPLIANCE: [
            "Review transaction logs",
            "Check compliance rules",
            "Verify user limits",
            "Contact compliance team"
        ],
        ErrorCategory.DATA_INTEGRITY: [
            "Check database health",
            "Verify data consistency",
            "Review recent migrations",
            "Contact database team"
        ]
    }
    
    return actions.get(category, ["Contact support team", "Review error logs"])


def _analyze_auth_patterns(hours: int) -> Dict[str, Any]:
    """Analyze authentication error patterns"""
    # This would analyze authentication-specific patterns
    # For now, return basic analysis
    return {
        "failure_rate": 0,  # Would calculate actual rate
        "suspicious_ips": [],
        "brute_force_attempts": 0,
        "account_lockouts": 0
    }


def _analyze_system_patterns(hours: int) -> Dict[str, Any]:
    """Analyze system error patterns"""
    return {
        "error_clusters": [],
        "performance_degradation": False,
        "service_outages": [],
        "infrastructure_issues": []
    }


def _analyze_security_patterns(hours: int) -> Dict[str, Any]:
    """Analyze security-related error patterns"""
    return {
        "suspicious_activities": [],
        "potential_attacks": [],
        "data_breach_indicators": [],
        "compliance_violations": []
    }


def _analyze_ux_patterns(hours: int) -> Dict[str, Any]:
    """Analyze user experience impact patterns"""
    return {
        "high_error_endpoints": [],
        "user_journey_failures": [],
        "conversion_impact": False,
        "mobile_vs_web_errors": {}
    }


def _generate_recommendations(metrics: Dict[str, Any], patterns: Dict[str, Any]) -> list:
    """Generate actionable recommendations based on error analysis"""
    recommendations = []
    
    if metrics["total_errors"] > 1000:
        recommendations.append({
            "priority": "high",
            "category": "operational",
            "action": "Investigate high error volume",
            "details": f"Total errors ({metrics['total_errors']}) exceed normal thresholds"
        })
    
    critical_errors = metrics["severity_breakdown"].get("critical", 0)
    if critical_errors > 0:
        recommendations.append({
            "priority": "critical",
            "category": "operational",
            "action": "Address critical errors immediately",
            "details": f"{critical_errors} critical errors require immediate attention"
        })
    
    auth_errors = metrics["category_breakdown"].get("authentication", 0)
    if auth_errors > 100:
        recommendations.append({
            "priority": "medium",
            "category": "security",
            "action": "Review authentication security",
            "details": f"High authentication failure rate ({auth_errors}) may indicate attacks"
        })
    
    return recommendations