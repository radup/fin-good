"""
Analytics Caching Service
Provides intelligent caching for expensive analytics calculations.
"""

import json
import logging
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from decimal import Decimal
import hashlib

logger = logging.getLogger(__name__)

class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class AnalyticsCache:
    """
    In-memory cache for analytics results with TTL and intelligent invalidation.
    In production, this would be backed by Redis or similar.
    """
    
    def __init__(self, default_ttl: int = 3600):  # 1 hour default TTL
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.hit_count = 0
        self.miss_count = 0
        
    def _generate_cache_key(self, user_id: int, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate a consistent cache key from parameters"""
        # Sort parameters for consistent key generation
        sorted_params = sorted(params.items()) if params else []
        
        # Create a string representation of parameters
        param_str = json.dumps(sorted_params, cls=DecimalEncoder, sort_keys=True)
        
        # Create hash for the key to keep it manageable
        key_data = f"{user_id}:{endpoint}:{param_str}"
        cache_key = hashlib.md5(key_data.encode()).hexdigest()
        
        return f"analytics:{cache_key}"
    
    def get(self, user_id: int, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """Get cached result if available and not expired"""
        cache_key = self._generate_cache_key(user_id, endpoint, params or {})
        
        if cache_key in self._cache:
            cache_entry = self._cache[cache_key]
            
            # Check if expired
            if datetime.now() > cache_entry['expires_at']:
                del self._cache[cache_key]
                self.miss_count += 1
                return None
            
            self.hit_count += 1
            logger.debug(f"Cache hit for {endpoint} (user {user_id})")
            return cache_entry['data']
        
        self.miss_count += 1
        return None
    
    def set(self, user_id: int, endpoint: str, data: Any, params: Optional[Dict[str, Any]] = None, ttl: Optional[int] = None) -> None:
        """Cache the result with TTL"""
        cache_key = self._generate_cache_key(user_id, endpoint, params or {})
        
        expires_at = datetime.now() + timedelta(seconds=ttl or self.default_ttl)
        
        self._cache[cache_key] = {
            'data': data,
            'created_at': datetime.now(),
            'expires_at': expires_at,
            'user_id': user_id,
            'endpoint': endpoint
        }
        
        logger.debug(f"Cached result for {endpoint} (user {user_id}, TTL: {ttl or self.default_ttl}s)")
    
    def invalidate_user(self, user_id: int) -> int:
        """Invalidate all cache entries for a specific user"""
        keys_to_remove = []
        
        for key, entry in self._cache.items():
            if entry.get('user_id') == user_id:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._cache[key]
        
        logger.info(f"Invalidated {len(keys_to_remove)} cache entries for user {user_id}")
        return len(keys_to_remove)
    
    def invalidate_endpoint(self, endpoint: str) -> int:
        """Invalidate all cache entries for a specific endpoint"""
        keys_to_remove = []
        
        for key, entry in self._cache.items():
            if entry.get('endpoint') == endpoint:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._cache[key]
        
        logger.info(f"Invalidated {len(keys_to_remove)} cache entries for endpoint {endpoint}")
        return len(keys_to_remove)
    
    def cleanup_expired(self) -> int:
        """Remove expired entries from cache"""
        keys_to_remove = []
        now = datetime.now()
        
        for key, entry in self._cache.items():
            if now > entry['expires_at']:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._cache[key]
        
        if keys_to_remove:
            logger.debug(f"Cleaned up {len(keys_to_remove)} expired cache entries")
        
        return len(keys_to_remove)
    
    def clear_all(self) -> int:
        """Clear all cache entries"""
        count = len(self._cache)
        self._cache.clear()
        self.hit_count = 0
        self.miss_count = 0
        
        logger.info(f"Cleared all {count} cache entries")
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'total_entries': len(self._cache),
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': f"{hit_rate:.2f}%",
            'memory_usage_estimate': sum(
                len(json.dumps(entry, cls=DecimalEncoder)) 
                for entry in self._cache.values()
            )
        }

# Global cache instance
analytics_cache = AnalyticsCache()

def cache_analytics_result(endpoint: str, ttl: Optional[int] = None):
    """
    Decorator for caching analytics endpoint results
    
    Usage:
    @cache_analytics_result('cash_flow', ttl=1800)  # 30 minutes
    def get_cash_flow_analysis(...):
        ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract user_id from the analytics service instance
            if args and hasattr(args[0], 'user_id'):
                user_id = args[0].user_id
            else:
                # Fallback - execute without caching
                return func(*args, **kwargs)
            
            # Create cache parameters from function arguments
            cache_params = {}
            if len(args) > 1:  # Skip self parameter
                cache_params.update({f'arg_{i}': arg for i, arg in enumerate(args[1:])})
            cache_params.update(kwargs)
            
            # Try to get from cache first
            cached_result = analytics_cache.get(user_id, endpoint, cache_params)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            analytics_cache.set(user_id, endpoint, result, cache_params, ttl)
            
            return result
        return wrapper
    return decorator

def invalidate_user_cache(user_id: int):
    """Invalidate all cached analytics for a user (call when data changes)"""
    return analytics_cache.invalidate_user(user_id)

def get_cache_stats() -> Dict[str, Any]:
    """Get cache performance statistics"""
    return analytics_cache.get_stats()

def cleanup_cache():
    """Manual cache cleanup - remove expired entries"""
    return analytics_cache.cleanup_expired()