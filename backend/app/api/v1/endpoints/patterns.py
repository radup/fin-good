"""
Pattern Recognition API Endpoints

Advanced pattern recognition endpoints for intelligent categorization rule generation,
user behavior analysis, and automated categorization improvements.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import uuid

from app.core.database import get_db
from app.models.user import User
from app.core.cookie_auth import get_current_user_from_cookie
from app.services.pattern_recognition import (
    PatternRecognitionEngine, PatternAnalysisResult, RecognizedPattern,
    PatternRule, UserBehaviorProfile, RuleGenerationStrategy, PatternType,
    PatternRecognitionLimits
)
from app.core.exceptions import ValidationException, BusinessLogicException
from app.core.error_sanitizer import error_sanitizer, create_secure_error_response
from app.schemas.error import ErrorCategory, ErrorSeverity
from app.core.audit_logger import security_audit_logger

router = APIRouter()


@router.post("/analyze")
async def analyze_user_patterns(
    date_range_days: int = Query(90, ge=30, le=365, description="Days of transaction history to analyze"),
    include_uncategorized: bool = Query(True, description="Include uncategorized transactions in analysis"),
    focus_corrections: bool = Query(True, description="Prioritize user correction patterns"),
    generation_strategy: str = Query("balanced", description="Rule generation strategy: conservative, balanced, aggressive, learning"),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Analyze user's transaction patterns to discover categorization insights and generate rule suggestions.
    
    This endpoint performs comprehensive pattern analysis including:
    - Vendor-based categorization patterns
    - Description keyword patterns  
    - Amount range patterns
    - Frequency and timing patterns
    - User correction patterns for ML improvement
    - Behavioral patterns in categorization habits
    
    Returns detailed analysis results with actionable rule suggestions.
    """
    try:
        # Validate generation strategy
        try:
            strategy = RuleGenerationStrategy(generation_strategy)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid generation strategy. Must be one of: {[s.value for s in RuleGenerationStrategy]}"
            )
        
        # Validate date range
        if date_range_days > PatternRecognitionLimits.MAX_ANALYSIS_TIME_MINUTES * 24:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Analysis period cannot exceed {PatternRecognitionLimits.MAX_ANALYSIS_TIME_MINUTES * 24} days"
            )
        
        # Initialize pattern recognition engine
        pattern_engine = PatternRecognitionEngine(db, current_user)
        
        # Configure analysis strategy
        pattern_engine.analysis_config["generation_strategy"] = strategy
        
        # Perform comprehensive pattern analysis
        analysis_result = await pattern_engine.analyze_user_patterns(
            date_range_days=date_range_days,
            include_uncategorized=include_uncategorized,
            focus_corrections=focus_corrections
        )
        
        # Log analysis activity
        security_audit_logger.info(
            f"Pattern analysis completed for user {current_user.id}",
            extra={
                "user_id": current_user.id,
                "analysis_id": analysis_result.analysis_id,
                "patterns_discovered": analysis_result.patterns_discovered,
                "rules_suggested": analysis_result.rules_suggested,
                "analysis_duration_ms": analysis_result.analysis_duration_ms,
                "date_range_days": date_range_days,
                "generation_strategy": generation_strategy
            }
        )
        
        # Format response
        return {
            "analysis_summary": {
                "analysis_id": analysis_result.analysis_id,
                "total_transactions_analyzed": analysis_result.total_transactions_analyzed,
                "patterns_discovered": analysis_result.patterns_discovered,
                "rules_suggested": analysis_result.rules_suggested,
                "high_confidence_patterns": analysis_result.high_confidence_patterns,
                "analysis_duration_ms": analysis_result.analysis_duration_ms,
                "accuracy_improvements": analysis_result.accuracy_improvements
            },
            "discovered_patterns": [
                {
                    "pattern_id": pattern.pattern_id,
                    "pattern_type": pattern.pattern_type.value,
                    "pattern_value": pattern.pattern_value,
                    "confidence_score": pattern.confidence_score,
                    "frequency": pattern.frequency,
                    "category": pattern.category,
                    "subcategory": pattern.subcategory,
                    "supporting_transactions_count": len(pattern.supporting_transactions),
                    "pattern_metadata": pattern.pattern_metadata,
                    "created_at": pattern.created_at.isoformat(),
                    "pattern_strength": _get_pattern_strength_description(pattern.confidence_score)
                }
                for pattern in analysis_result.discovered_patterns
            ],
            "suggested_rules": [
                {
                    "rule_id": rule.rule_id,
                    "pattern_id": rule.pattern_id,
                    "rule_pattern": rule.rule_pattern,
                    "rule_type": rule.rule_type,
                    "category": rule.category,
                    "subcategory": rule.subcategory,
                    "confidence": rule.confidence,
                    "priority": rule.priority,
                    "estimated_accuracy": rule.estimated_accuracy,
                    "creation_reason": rule.creation_reason,
                    "supporting_evidence": rule.supporting_evidence,
                    "recommendation": _get_rule_recommendation(rule.confidence, rule.estimated_accuracy)
                }
                for rule in analysis_result.suggested_rules
            ],
            "analysis_metadata": {
                "started_at": analysis_result.started_at.isoformat(),
                "completed_at": analysis_result.completed_at.isoformat(),
                "generation_strategy": generation_strategy,
                "analysis_parameters": {
                    "date_range_days": date_range_days,
                    "include_uncategorized": include_uncategorized,
                    "focus_corrections": focus_corrections
                }
            }
        }
        
    except (ValidationException, BusinessLogicException) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        error_detail = create_secure_error_response(
            exception=e,
            error_code="PATTERN_ANALYSIS_FAILED",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4()),
            user_message="Failed to analyze transaction patterns. Please try again with a smaller date range.",
            suggested_action="Try reducing the analysis period or contact support if the problem persists."
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail.user_message
        )


@router.post("/apply-rules")
async def apply_suggested_rules(
    rule_ids: List[str] = Query(..., description="List of rule IDs to apply"),
    dry_run: bool = Query(True, description="Perform dry run without creating actual rules"),
    auto_activate: bool = Query(False, description="Automatically activate created rules"),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Apply suggested pattern-based categorization rules to the user's account.
    
    WARNING: This will create new categorization rules that affect future transaction processing!
    Use dry_run=true first to preview the impact before applying rules.
    """
    try:
        if not rule_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one rule ID must be provided"
            )
        
        if len(rule_ids) > PatternRecognitionLimits.MAX_RULES_GENERATE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot apply more than {PatternRecognitionLimits.MAX_RULES_GENERATE} rules at once"
            )
        
        if not dry_run and auto_activate and len(rule_ids) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Auto-activation is limited to 10 rules at a time for safety"
            )
        
        # Initialize pattern recognition engine
        pattern_engine = PatternRecognitionEngine(db, current_user)
        
        # Apply the suggested rules
        application_result = await pattern_engine.apply_suggested_rules(
            rule_ids=rule_ids,
            dry_run=dry_run,
            auto_activate=auto_activate
        )
        
        # Log rule application
        security_audit_logger.info(
            f"Pattern rules {'simulated' if dry_run else 'applied'} for user {current_user.id}",
            extra={
                "user_id": current_user.id,
                "rule_ids": rule_ids,
                "rules_processed": len(rule_ids),
                "dry_run": dry_run,
                "auto_activate": auto_activate,
                "success": application_result.get("success", True)
            }
        )
        
        return {
            "operation_type": "simulation" if dry_run else "rule_creation",
            "rules_processed": len(rule_ids),
            "results": application_result,
            "recommendations": [
                {
                    "priority": "high",
                    "message": "Review dry run results carefully before applying rules" if dry_run else "Monitor categorization accuracy after rule activation",
                    "action": "Run with dry_run=false to create actual rules" if dry_run else "Check categorization statistics in a few days"
                }
            ] if not application_result.get("errors") else [
                {
                    "priority": "urgent",
                    "message": "Some rules failed to apply",
                    "action": "Review errors and try again with valid rule IDs"
                }
            ]
        }
        
    except (ValidationException, BusinessLogicException) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        error_detail = create_secure_error_response(
            exception=e,
            error_code="RULE_APPLICATION_FAILED",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4()),
            user_message="Failed to apply pattern-based rules. Please try again.",
            suggested_action="Try with fewer rules or contact support if the problem persists."
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail.user_message
        )


@router.get("/behavior-profile")
async def get_user_behavior_profile(
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Get detailed user behavior profile showing categorization patterns and preferences.
    
    Provides insights into user's categorization habits, consistency, and learning patterns
    to help optimize the pattern recognition and rule generation process.
    """
    try:
        pattern_engine = PatternRecognitionEngine(db, current_user)
        
        # Get recent transactions for profile building
        cutoff_date = datetime.utcnow() - timedelta(days=180)  # 6 months
        transactions = await pattern_engine._get_transactions_for_pattern_analysis(180, True)
        
        if not transactions:
            return {
                "profile_available": False,
                "message": "Insufficient transaction history for behavior analysis",
                "minimum_transactions_needed": 20
            }
        
        # Build behavior profile
        user_profile = await pattern_engine._build_user_behavior_profile(transactions)
        
        # Get analytics
        analytics = await pattern_engine.get_pattern_analytics()
        
        return {
            "profile_available": True,
            "user_behavior": {
                "user_id": user_profile.user_id,
                "total_manual_corrections": user_profile.total_manual_corrections,
                "categorization_style": user_profile.categorization_style,
                "consistency_score": user_profile.consistency_score,
                "learning_rate": user_profile.learning_rate,
                "last_updated": user_profile.last_updated.isoformat(),
                "style_description": _get_style_description(user_profile.categorization_style)
            },
            "correction_patterns": {
                "total_corrections": len(user_profile.correction_patterns),
                "common_corrections": list(user_profile.correction_patterns.items())[:5],
                "correction_frequency": user_profile.total_manual_corrections / max(len(transactions), 1)
            },
            "preferred_categories": {
                "total_categories": len(user_profile.preferred_categories),
                "top_categories": sorted(
                    user_profile.preferred_categories.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:10],
                "category_distribution": _calculate_category_distribution(user_profile.preferred_categories)
            },
            "pattern_analytics": analytics,
            "recommendations": _generate_behavior_recommendations(user_profile, len(transactions))
        }
        
    except Exception as e:
        error_detail = create_secure_error_response(
            exception=e,
            error_code="BEHAVIOR_PROFILE_FAILED",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4()),
            user_message="Failed to retrieve behavior profile. Please try again.",
            suggested_action="Try again later or contact support if the problem persists."
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail.user_message
        )


@router.get("/analytics")
async def get_pattern_analytics(
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive pattern recognition analytics and performance metrics.
    
    Provides insights into pattern discovery effectiveness, rule generation performance,
    and overall categorization improvements from pattern-based automation.
    """
    try:
        pattern_engine = PatternRecognitionEngine(db, current_user)
        analytics = await pattern_engine.get_pattern_analytics()
        
        # Add system-wide pattern recognition statistics
        system_stats = {
            "pattern_recognition_limits": {
                "max_transactions_analyze": PatternRecognitionLimits.MAX_TRANSACTIONS_ANALYZE,
                "max_patterns_per_analysis": PatternRecognitionLimits.MAX_PATTERNS_PER_ANALYSIS,
                "max_rules_generate": PatternRecognitionLimits.MAX_RULES_GENERATE,
                "min_pattern_confidence": PatternRecognitionLimits.MIN_PATTERN_CONFIDENCE
            },
            "supported_pattern_types": [ptype.value for ptype in PatternType],
            "generation_strategies": [strategy.value for strategy in RuleGenerationStrategy]
        }
        
        return {
            "user_analytics": analytics,
            "system_configuration": system_stats,
            "performance_insights": {
                "cache_status": "active" if analytics.get("pattern_discovery", {}).get("patterns_in_cache", 0) > 0 else "empty",
                "analysis_freshness": f"{analytics.get('pattern_discovery', {}).get('cache_age_minutes', 0):.1f} minutes ago",
                "recommendation": _get_analytics_recommendation(analytics)
            }
        }
        
    except Exception as e:
        error_detail = create_secure_error_response(
            exception=e,
            error_code="PATTERN_ANALYTICS_FAILED",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4()),
            user_message="Failed to retrieve pattern analytics. Please try again.",
            suggested_action="Try again later or contact support if the problem persists."
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail.user_message
        )


@router.get("/config")
async def get_pattern_recognition_config():
    """
    Get current pattern recognition configuration, limits, and available options.
    
    Returns system configuration for pattern recognition algorithms,
    analysis parameters, and operational limits.
    """
    return {
        "analysis_config": {
            "max_transactions_analyze": PatternRecognitionLimits.MAX_TRANSACTIONS_ANALYZE,
            "max_patterns_per_analysis": PatternRecognitionLimits.MAX_PATTERNS_PER_ANALYSIS,
            "max_rules_generate": PatternRecognitionLimits.MAX_RULES_GENERATE,
            "min_pattern_frequency": PatternRecognitionLimits.MIN_PATTERN_FREQUENCY,
            "min_pattern_confidence": PatternRecognitionLimits.MIN_PATTERN_CONFIDENCE,
            "max_analysis_time_minutes": PatternRecognitionLimits.MAX_ANALYSIS_TIME_MINUTES,
            "cache_ttl_hours": PatternRecognitionLimits.CACHE_TTL_HOURS
        },
        "pattern_types": {
            pattern_type.name.lower(): {
                "value": pattern_type.value,
                "description": _get_pattern_type_description(pattern_type)
            }
            for pattern_type in PatternType
        },
        "generation_strategies": {
            strategy.name.lower(): {
                "value": strategy.value,
                "description": _get_strategy_description(strategy)
            }
            for strategy in RuleGenerationStrategy
        },
        "confidence_levels": {
            "very_high": "95%+ - Extremely reliable patterns",
            "high": "85%+ - Highly reliable patterns",
            "medium": "70%+ - Moderately reliable patterns", 
            "low": "55%+ - Lower confidence patterns",
            "minimum": f"{PatternRecognitionLimits.MIN_PATTERN_CONFIDENCE:.1%} - Minimum threshold for consideration"
        },
        "algorithm_info": {
            "pattern_discovery": "Multi-algorithm analysis of vendor, description, amount, frequency, and behavioral patterns",
            "confidence_scoring": "Weighted scoring based on frequency, consistency, and historical accuracy",
            "rule_generation": "Automatic conversion of patterns to categorization rules with priority assignment",
            "user_learning": "Adaptive learning from user corrections and categorization behavior"
        }
    }


# Helper functions

def _get_pattern_strength_description(confidence: float) -> str:
    """Get human-readable pattern strength description"""
    if confidence >= 0.95:
        return "Extremely strong - virtually certain pattern"
    elif confidence >= 0.85:
        return "Very strong - highly reliable pattern"
    elif confidence >= 0.75:
        return "Strong - reliable pattern with good evidence"
    elif confidence >= 0.65:
        return "Moderate - decent pattern with some uncertainty"
    else:
        return "Weak - low confidence pattern, use with caution"


def _get_rule_recommendation(confidence: float, accuracy: float) -> str:
    """Get recommendation for rule application"""
    if confidence >= 0.9 and accuracy >= 0.9:
        return "Highly recommended - apply immediately"
    elif confidence >= 0.8 and accuracy >= 0.8:
        return "Recommended - good candidate for application"
    elif confidence >= 0.7:
        return "Consider carefully - may be useful in specific contexts"
    else:
        return "Not recommended - low confidence, consider manual review"


def _get_style_description(style: str) -> str:
    """Get description of categorization style"""
    descriptions = {
        "simple": "Prefers few, broad categories for easy management",
        "detailed": "Uses many specific categories for detailed tracking",
        "balanced": "Uses moderate number of categories with good organization",
        "unknown": "Insufficient data to determine style"
    }
    return descriptions.get(style, "Unknown categorization style")


def _calculate_category_distribution(preferred_categories: Dict[str, int]) -> Dict[str, float]:
    """Calculate distribution percentages for categories"""
    total = sum(preferred_categories.values())
    if total == 0:
        return {}
    
    return {
        "concentration": max(preferred_categories.values()) / total,
        "diversity_score": len(preferred_categories) / max(total, 1),
        "top_category_dominance": max(preferred_categories.values()) / total
    }


def _generate_behavior_recommendations(profile: UserBehaviorProfile, total_transactions: int) -> List[Dict[str, str]]:
    """Generate recommendations based on user behavior profile"""
    recommendations = []
    
    if profile.learning_rate < 0.1:
        recommendations.append({
            "priority": "medium",
            "type": "engagement",
            "message": "Consider reviewing and correcting more categorizations to improve accuracy",
            "action": "Review uncategorized transactions and provide corrections"
        })
    
    if profile.consistency_score < 0.7:
        recommendations.append({
            "priority": "high",
            "type": "consistency",
            "message": "Categorization consistency could be improved",
            "action": "Focus on developing consistent categorization patterns"
        })
    
    if len(profile.preferred_categories) < 5:
        recommendations.append({
            "priority": "low",
            "type": "categories",
            "message": "Consider using more specific categories for better insights",
            "action": "Create additional subcategories for detailed tracking"
        })
    
    if profile.total_manual_corrections > total_transactions * 0.5:
        recommendations.append({
            "priority": "high",
            "type": "automation",
            "message": "High correction rate suggests automation opportunities",
            "action": "Run pattern analysis to generate helpful rules"
        })
    
    return recommendations


def _get_analytics_recommendation(analytics: Dict[str, Any]) -> str:
    """Get recommendation based on analytics data"""
    user_behavior = analytics.get("user_behavior", {})
    
    corrections = user_behavior.get("total_manual_corrections", 0)
    consistency = user_behavior.get("consistency_score", 0)
    
    if corrections > 20 and consistency > 0.8:
        return "Excellent candidate for pattern analysis - high activity with good consistency"
    elif corrections > 10:
        return "Good candidate for pattern analysis - sufficient correction history available"
    elif corrections < 5:
        return "Consider using the system more to build correction history for better patterns"
    else:
        return "Standard usage - pattern analysis available when needed"


def _get_pattern_type_description(pattern_type: PatternType) -> str:
    """Get description for pattern type"""
    descriptions = {
        PatternType.VENDOR_PATTERN: "Patterns based on merchant/vendor names",
        PatternType.DESCRIPTION_PATTERN: "Patterns based on transaction description keywords",
        PatternType.AMOUNT_PATTERN: "Patterns based on transaction amount ranges",
        PatternType.DATE_PATTERN: "Patterns based on dates and timing",
        PatternType.FREQUENCY_PATTERN: "Patterns based on transaction frequency",
        PatternType.BEHAVIORAL_PATTERN: "Patterns based on user behavior analysis",
        PatternType.CORRECTION_PATTERN: "Patterns learned from user corrections"
    }
    return descriptions.get(pattern_type, "Unknown pattern type")


def _get_strategy_description(strategy: RuleGenerationStrategy) -> str:
    """Get description for generation strategy"""
    descriptions = {
        RuleGenerationStrategy.CONSERVATIVE: "High confidence only - fewer but very reliable rules",
        RuleGenerationStrategy.BALANCED: "Moderate confidence - balanced approach with good reliability",
        RuleGenerationStrategy.AGGRESSIVE: "Lower confidence threshold - more rules with higher risk",
        RuleGenerationStrategy.LEARNING: "Adaptive approach based on user feedback and behavior"
    }
    return descriptions.get(strategy, "Unknown strategy")


# Import timedelta for behavior profile endpoint
from datetime import timedelta