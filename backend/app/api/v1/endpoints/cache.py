"""
Cache Management Endpoints
Provides cache control and monitoring capabilities for analytics.
"""

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from app.core.database import get_db
from app.models.user import User
from app.core.cookie_auth import get_current_user_from_cookie
from app.services.analytics_cache import get_cache_stats, cleanup_cache, invalidate_user_cache

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/stats")
async def get_cache_statistics(
    current_user: User = Depends(get_current_user_from_cookie)
) -> Dict[str, Any]:
    """
    Get cache performance statistics.
    
    Returns cache hit rates, memory usage, and other performance metrics.
    """
    try:
        stats = get_cache_stats()
        logger.info(f"Cache statistics requested by user {current_user.id}")
        return stats
        
    except Exception as e:
        logger.error(f"Error retrieving cache statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cache statistics."
        ) from e

@router.post("/cleanup")
async def cleanup_expired_cache(
    current_user: User = Depends(get_current_user_from_cookie)
) -> Dict[str, Any]:
    """
    Manually trigger cleanup of expired cache entries.
    
    Returns the number of entries cleaned up.
    """
    try:
        cleaned_count = cleanup_cache()
        logger.info(f"Cache cleanup triggered by user {current_user.id}: {cleaned_count} entries removed")
        
        return {
            "cleaned_entries": cleaned_count,
            "message": f"Successfully cleaned up {cleaned_count} expired cache entries"
        }
        
    except Exception as e:
        logger.error(f"Error during cache cleanup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup cache."
        ) from e

@router.post("/invalidate")
async def invalidate_user_analytics_cache(
    current_user: User = Depends(get_current_user_from_cookie)
) -> Dict[str, Any]:
    """
    Invalidate all cached analytics for the current user.
    
    Useful when user data has been updated and fresh analytics are needed.
    """
    try:
        invalidated_count = invalidate_user_cache(current_user.id)
        logger.info(f"User {current_user.id} invalidated their analytics cache: {invalidated_count} entries")
        
        return {
            "invalidated_entries": invalidated_count,
            "message": f"Successfully invalidated {invalidated_count} cache entries"
        }
        
    except Exception as e:
        logger.error(f"Error invalidating user cache for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to invalidate user cache."
        ) from e