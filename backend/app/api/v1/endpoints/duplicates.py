"""
Duplicate Detection API Endpoints

Provides comprehensive duplicate transaction detection and management
with fuzzy matching, confidence scoring, and automated merge capabilities.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from app.core.database import get_db
from app.models.user import User
from app.core.cookie_auth import get_current_user_from_cookie
from app.services.duplicate_detection import (
    DuplicateDetectionService, DuplicateDetectionResult, DuplicateGroup,
    DuplicateConfidenceLevel, DuplicateMatchType, DuplicateReviewStatus,
    DuplicateDetectionLimits
)
from app.core.exceptions import ValidationException, BusinessLogicException
from app.core.error_sanitizer import error_sanitizer, create_secure_error_response
from app.schemas.error import ErrorCategory, ErrorSeverity
from app.core.rate_limiter import get_rate_limiter, RateLimitType, RateLimitTier
from app.core.audit_logger import security_audit_logger
from fastapi import Request
import uuid

router = APIRouter()


@router.post("/scan")
async def scan_for_duplicates(
    date_range_days: int = Query(30, ge=1, le=90, description="Number of days to scan for duplicates"),
    min_confidence: float = Query(0.5, ge=0.1, le=1.0, description="Minimum confidence score (0.1-1.0)"),
    include_reviewed: bool = Query(False, description="Include previously reviewed duplicates"),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Scan for potential duplicate transactions using advanced fuzzy matching algorithms.
    
    This endpoint performs comprehensive duplicate detection using:
    - Exact matching on amount, date, description, and vendor
    - Fuzzy string matching for similar descriptions and vendors
    - Date proximity analysis for near-duplicate detection
    - Confidence scoring with multiple matching algorithms
    
    Returns detailed results with suggested actions for each potential duplicate.
    """
    try:
        # Validate date range
        if date_range_days > DuplicateDetectionLimits.MAX_COMPARISON_DAYS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Date range cannot exceed {DuplicateDetectionLimits.MAX_COMPARISON_DAYS} days"
            )
        
        # Validate confidence threshold
        if min_confidence < DuplicateDetectionLimits.MIN_CONFIDENCE_THRESHOLD:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Minimum confidence cannot be below {DuplicateDetectionLimits.MIN_CONFIDENCE_THRESHOLD}"
            )
        
        # Initialize duplicate detection service
        duplicate_service = DuplicateDetectionService(db, current_user)
        
        # Perform duplicate scan
        result = await duplicate_service.scan_for_duplicates(
            date_range_days=date_range_days,
            min_confidence=min_confidence,
            include_reviewed=include_reviewed
        )
        
        # Log scan activity
        security_audit_logger.info(
            f"Duplicate scan completed for user {current_user.id}",
            extra={
                "user_id": current_user.id,
                "scan_id": result.scan_id,
                "duplicates_found": result.potential_duplicates_found,
                "high_confidence_matches": result.high_confidence_matches,
                "date_range_days": date_range_days,
                "min_confidence": min_confidence
            }
        )
        
        # Return serialized result
        return {
            "scan_id": result.scan_id,
            "scan_summary": {
                "total_transactions_scanned": result.total_transactions_scanned,
                "potential_duplicates_found": result.potential_duplicates_found,
                "high_confidence_matches": result.high_confidence_matches,
                "auto_merge_candidates": result.auto_merge_candidates,
                "total_amount_affected": str(result.total_amount_affected),
                "scan_duration_ms": result.scan_duration_ms
            },
            "duplicate_groups": [
                {
                    "group_id": group.group_id,
                    "confidence_score": group.confidence_score,
                    "primary_transaction_id": group.primary_transaction_id,
                    "duplicate_count": group.duplicate_count,
                    "total_amount": str(group.total_amount),
                    "date_range": group.date_range,
                    "review_status": group.review_status.value,
                    "transactions": group.transactions,
                    "suggested_action": _get_suggested_action_description(group.confidence_score)
                }
                for group in result.duplicate_groups
            ],
            "scan_metadata": {
                "started_at": result.started_at.isoformat(),
                "completed_at": result.completed_at.isoformat(),
                "parameters": {
                    "date_range_days": date_range_days,
                    "min_confidence": min_confidence,
                    "include_reviewed": include_reviewed
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
            error_code="DUPLICATE_SCAN_FAILED",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4()),
            user_message="Failed to scan for duplicate transactions. Please try again.",
            suggested_action="Reduce the date range or contact support if the problem persists."
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail.user_message
        )


@router.post("/auto-merge")
async def auto_merge_high_confidence_duplicates(
    scan_id: str = Query(..., description="Scan ID from duplicate detection scan"),
    min_confidence: float = Query(0.95, ge=0.8, le=1.0, description="Minimum confidence for auto-merge"),
    dry_run: bool = Query(True, description="Perform dry run without actual merging"),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Automatically merge high-confidence duplicate transactions.
    
    WARNING: This operation will permanently delete duplicate transactions!
    Use dry_run=true first to preview what will be merged.
    
    Only transactions with very high confidence scores (>= 0.95 by default) 
    will be auto-merged to prevent accidental data loss.
    """
    try:
        if not dry_run and min_confidence < 0.9:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Auto-merge requires minimum confidence of 0.9 for safety"
            )
        
        # For this implementation, we need to re-scan to get the duplicate groups
        # In production, scan results would be cached in Redis
        duplicate_service = DuplicateDetectionService(db, current_user)
        
        # Perform a fresh scan with the specified confidence
        result = await duplicate_service.scan_for_duplicates(
            date_range_days=30,  # Standard range for auto-merge
            min_confidence=min_confidence
        )
        
        if dry_run:
            # Return preview of what would be merged
            auto_merge_candidates = [
                group for group in result.duplicate_groups
                if group.confidence_score >= min_confidence
            ]
            
            return {
                "dry_run": True,
                "scan_id": result.scan_id,
                "auto_merge_preview": {
                    "total_groups": len(auto_merge_candidates),
                    "total_transactions_to_merge": sum(len(group.transactions) for group in auto_merge_candidates),
                    "total_transactions_to_delete": sum(len(group.transactions) - 1 for group in auto_merge_candidates),
                    "total_amount_affected": str(sum(group.total_amount for group in auto_merge_candidates))
                },
                "groups_preview": [
                    {
                        "group_id": group.group_id,
                        "confidence_score": group.confidence_score,
                        "transaction_count": len(group.transactions),
                        "transactions_to_delete": len(group.transactions) - 1,
                        "primary_transaction_id": group.primary_transaction_id,
                        "duplicate_transaction_ids": [
                            txn['id'] for txn in group.transactions 
                            if txn['id'] != group.primary_transaction_id
                        ],
                        "total_amount": str(group.total_amount)
                    }
                    for group in auto_merge_candidates
                ],
                "warning": "This is a preview. Set dry_run=false to execute the actual merge."
            }
        else:
            # Perform actual auto-merge
            merge_result = await duplicate_service.auto_merge_high_confidence_duplicates(
                duplicate_groups=result.duplicate_groups,
                min_auto_merge_confidence=min_confidence
            )
            
            # Log merge activity
            security_audit_logger.info(
                f"Auto-merge completed for user {current_user.id}",
                extra={
                    "user_id": current_user.id,
                    "scan_id": result.scan_id,
                    "groups_merged": merge_result['total_merged'],
                    "merge_errors": merge_result['total_errors'],
                    "min_confidence": min_confidence
                }
            )
            
            return {
                "dry_run": False,
                "scan_id": result.scan_id,
                "merge_results": {
                    "total_groups_processed": len(result.duplicate_groups),
                    "total_groups_merged": merge_result['total_merged'],
                    "total_merge_errors": merge_result['total_errors'],
                    "total_transactions_deleted": sum(
                        len(group['deleted_transaction_ids']) for group in merge_result['merged_groups']
                    )
                },
                "merged_groups": merge_result['merged_groups'],
                "merge_errors": merge_result['merge_errors'],
                "success": merge_result['total_errors'] == 0
            }
        
    except (ValidationException, BusinessLogicException) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        error_detail = create_secure_error_response(
            exception=e,
            error_code="AUTO_MERGE_FAILED",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4()),
            user_message="Failed to auto-merge duplicate transactions. Please try again.",
            suggested_action="Try with a higher confidence threshold or contact support."
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail.user_message
        )


@router.get("/stats")
async def get_duplicate_detection_stats(
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Get statistics about potential duplicates in user's transaction data.
    
    Provides overview of duplicate patterns, confidence distribution,
    and recommendations for duplicate management.
    """
    try:
        duplicate_service = DuplicateDetectionService(db, current_user)
        stats = await duplicate_service.get_duplicate_statistics()
        
        # Add recommendations based on stats
        recommendations = _generate_duplicate_recommendations(stats)
        
        return {
            "duplicate_statistics": stats,
            "recommendations": recommendations,
            "thresholds": {
                "min_confidence_threshold": DuplicateDetectionLimits.MIN_CONFIDENCE_THRESHOLD,
                "auto_merge_threshold": DuplicateDetectionLimits.AUTO_MERGE_THRESHOLD,
                "max_comparison_days": DuplicateDetectionLimits.MAX_COMPARISON_DAYS
            }
        }
        
    except Exception as e:
        error_detail = create_secure_error_response(
            exception=e,
            error_code="DUPLICATE_STATS_FAILED",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4()),
            user_message="Failed to retrieve duplicate detection statistics.",
            suggested_action="Please try again later."
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail.user_message
        )


@router.get("/config")
async def get_duplicate_detection_config():
    """
    Get current duplicate detection configuration and limits.
    
    Returns system configuration for duplicate detection algorithms,
    thresholds, and operational limits.
    """
    return {
        "detection_config": {
            "min_confidence_threshold": DuplicateDetectionLimits.MIN_CONFIDENCE_THRESHOLD,
            "auto_merge_threshold": DuplicateDetectionLimits.AUTO_MERGE_THRESHOLD,
            "max_duplicates_per_scan": DuplicateDetectionLimits.MAX_DUPLICATES_PER_SCAN,
            "max_comparison_days": DuplicateDetectionLimits.MAX_COMPARISON_DAYS,
            "min_amount_threshold": str(DuplicateDetectionLimits.MIN_AMOUNT_THRESHOLD),
            "max_description_distance": DuplicateDetectionLimits.MAX_DESCRIPTION_DISTANCE
        },
        "confidence_levels": {
            level.name.lower(): level.value for level in DuplicateConfidenceLevel
        },
        "match_types": {
            match_type.name.lower(): match_type.value for match_type in DuplicateMatchType
        },
        "review_statuses": {
            status.name.lower(): status.value for status in DuplicateReviewStatus
        },
        "algorithm_info": {
            "fuzzy_matching": "Levenshtein distance + sequence matching + token similarity",
            "string_normalization": "Lowercase, special character removal, stop word filtering",
            "confidence_weighting": "Amount (30%), Date (20%), Vendor (25%), Description (25%)",
            "date_tolerance": "7 days maximum for comparison window"
        }
    }


def _get_suggested_action_description(confidence_score: float) -> str:
    """Get human-readable suggested action description"""
    if confidence_score >= DuplicateDetectionLimits.AUTO_MERGE_THRESHOLD:
        return "Highly confident duplicate - safe for auto-merge"
    elif confidence_score >= 0.8:
        return "Very likely duplicate - recommend manual review before merging"
    elif confidence_score >= 0.7:
        return "Probable duplicate - manual review required"
    elif confidence_score >= 0.6:
        return "Possible duplicate - careful manual review needed"
    else:
        return "Low confidence match - flag for attention only"


def _generate_duplicate_recommendations(stats: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate recommendations based on duplicate statistics"""
    recommendations = []
    
    total_duplicates = stats.get('potential_duplicates_found', 0)
    auto_merge_candidates = stats.get('auto_merge_candidates', 0)
    high_confidence = stats.get('high_confidence_duplicates', 0)
    
    if auto_merge_candidates > 0:
        recommendations.append({
            "priority": "high",
            "action": "auto_merge",
            "description": f"You have {auto_merge_candidates} high-confidence duplicates that can be safely auto-merged.",
            "suggestion": "Run auto-merge with dry_run=true first to preview changes."
        })
    
    if high_confidence > auto_merge_candidates:
        manual_review_count = high_confidence - auto_merge_candidates
        recommendations.append({
            "priority": "medium", 
            "action": "manual_review",
            "description": f"You have {manual_review_count} likely duplicates that need manual review.",
            "suggestion": "Review these transactions carefully before merging to avoid data loss."
        })
    
    if total_duplicates > high_confidence:
        low_confidence_count = total_duplicates - high_confidence
        recommendations.append({
            "priority": "low",
            "action": "investigate",
            "description": f"You have {low_confidence_count} possible duplicates with lower confidence scores.",
            "suggestion": "These may be false positives - investigate before taking action."
        })
    
    if total_duplicates == 0:
        recommendations.append({
            "priority": "info",
            "action": "no_action",
            "description": "No potential duplicates found in your recent transactions.",
            "suggestion": "Your transaction data appears to be clean. Run periodic scans to maintain data quality."
        })
    
    return recommendations