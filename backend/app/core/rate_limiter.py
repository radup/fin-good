"""
Redis-based rate limiting service with sliding window implementation.
Provides protection against abuse, brute force attacks, and DDoS for financial API.
"""

import asyncio
import json
import time
import functools
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum
import redis.asyncio as redis
from fastapi import HTTPException, status
import logging
from pydantic import BaseModel

from app.core.config import settings
from app.core.audit_logger import security_audit_logger as security_logger

logger = logging.getLogger(__name__)


class RateLimitType(str, Enum):
    """Different types of rate limits for various security scenarios."""
    GENERAL = "general"
    AUTH = "auth"
    UPLOAD = "upload"
    ANALYTICS = "analytics"
    ADMIN = "admin"
    BRUTE_FORCE = "brute_force"
    DDOS = "ddos"


class RateLimitTier(str, Enum):
    """User tiers with different rate limits."""
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"
    ADMIN = "admin"


class RateLimitConfig(BaseModel):
    """Configuration for rate limiting rules."""
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_allowance: int = 0  # Additional requests allowed in burst
    block_duration_minutes: int = 15  # How long to block after limit exceeded
    

class RateLimitResult(BaseModel):
    """Result of rate limit check."""
    allowed: bool
    remaining: int
    reset_time: datetime
    retry_after: Optional[int] = None
    current_usage: int
    limit: int
    

class SecurityBlock(BaseModel):
    """Security block information."""
    blocked_until: datetime
    reason: str
    attempt_count: int
    block_type: RateLimitType


class RateLimiter:
    """
    Redis-based rate limiter with sliding window algorithm.
    Provides comprehensive protection for financial API endpoints.
    """
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.rate_limit_configs = self._get_rate_limit_configs()
        
    async def initialize(self):
        """Initialize Redis connection."""
        try:
            if not settings.REDIS_URL:
                raise ValueError("REDIS_URL not configured for rate limiting")
                
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Rate limiter Redis connection established")
            
        except Exception as e:
            logger.error(f"Failed to initialize rate limiter Redis: {e}")
            raise
    
    def _get_rate_limit_configs(self) -> Dict[RateLimitType, Dict[RateLimitTier, RateLimitConfig]]:
        """Get rate limiting configurations for different endpoint types and user tiers."""
        return {
            RateLimitType.GENERAL: {
                RateLimitTier.FREE: RateLimitConfig(
                    requests_per_minute=60,
                    requests_per_hour=1000,
                    requests_per_day=10000,
                    burst_allowance=10
                ),
                RateLimitTier.PREMIUM: RateLimitConfig(
                    requests_per_minute=120,
                    requests_per_hour=5000,
                    requests_per_day=50000,
                    burst_allowance=20
                ),
                RateLimitTier.ENTERPRISE: RateLimitConfig(
                    requests_per_minute=300,
                    requests_per_hour=15000,
                    requests_per_day=200000,
                    burst_allowance=50
                ),
                RateLimitTier.ADMIN: RateLimitConfig(
                    requests_per_minute=1000,
                    requests_per_hour=50000,
                    requests_per_day=1000000,
                    burst_allowance=100
                )
            },
            RateLimitType.AUTH: {
                RateLimitTier.FREE: RateLimitConfig(
                    requests_per_minute=5,
                    requests_per_hour=20,
                    requests_per_day=100,
                    block_duration_minutes=30
                ),
                RateLimitTier.PREMIUM: RateLimitConfig(
                    requests_per_minute=10,
                    requests_per_hour=50,
                    requests_per_day=200,
                    block_duration_minutes=15
                ),
                RateLimitTier.ENTERPRISE: RateLimitConfig(
                    requests_per_minute=20,
                    requests_per_hour=100,
                    requests_per_day=500,
                    block_duration_minutes=10
                ),
                RateLimitTier.ADMIN: RateLimitConfig(
                    requests_per_minute=50,
                    requests_per_hour=200,
                    requests_per_day=1000,
                    block_duration_minutes=5
                )
            },
            RateLimitType.UPLOAD: {
                RateLimitTier.FREE: RateLimitConfig(
                    requests_per_minute=2,
                    requests_per_hour=10,
                    requests_per_day=50,
                    block_duration_minutes=60
                ),
                RateLimitTier.PREMIUM: RateLimitConfig(
                    requests_per_minute=5,
                    requests_per_hour=25,
                    requests_per_day=200,
                    block_duration_minutes=30
                ),
                RateLimitTier.ENTERPRISE: RateLimitConfig(
                    requests_per_minute=15,
                    requests_per_hour=100,
                    requests_per_day=1000,
                    block_duration_minutes=15
                ),
                RateLimitTier.ADMIN: RateLimitConfig(
                    requests_per_minute=30,
                    requests_per_hour=200,
                    requests_per_day=2000,
                    block_duration_minutes=10
                )
            },
            RateLimitType.ANALYTICS: {
                RateLimitTier.FREE: RateLimitConfig(
                    requests_per_minute=10,
                    requests_per_hour=100,
                    requests_per_day=500
                ),
                RateLimitTier.PREMIUM: RateLimitConfig(
                    requests_per_minute=30,
                    requests_per_hour=500,
                    requests_per_day=2000
                ),
                RateLimitTier.ENTERPRISE: RateLimitConfig(
                    requests_per_minute=100,
                    requests_per_hour=2000,
                    requests_per_day=10000
                ),
                RateLimitTier.ADMIN: RateLimitConfig(
                    requests_per_minute=200,
                    requests_per_hour=5000,
                    requests_per_day=50000
                )
            },
            RateLimitType.BRUTE_FORCE: {
                RateLimitTier.FREE: RateLimitConfig(
                    requests_per_minute=3,
                    requests_per_hour=10,
                    requests_per_day=20,
                    block_duration_minutes=60
                ),
                RateLimitTier.PREMIUM: RateLimitConfig(
                    requests_per_minute=3,
                    requests_per_hour=10,
                    requests_per_day=20,
                    block_duration_minutes=45
                ),
                RateLimitTier.ENTERPRISE: RateLimitConfig(
                    requests_per_minute=5,
                    requests_per_hour=15,
                    requests_per_day=30,
                    block_duration_minutes=30
                ),
                RateLimitTier.ADMIN: RateLimitConfig(
                    requests_per_minute=10,
                    requests_per_hour=30,
                    requests_per_day=100,
                    block_duration_minutes=15
                )
            },
            RateLimitType.DDOS: {
                # DDoS protection is IP-based, not user-based
                RateLimitTier.FREE: RateLimitConfig(
                    requests_per_minute=100,
                    requests_per_hour=1000,
                    requests_per_day=5000,
                    block_duration_minutes=120
                )
            }
        }
    
    def _get_redis_keys(self, identifier: str, limit_type: RateLimitType) -> Dict[str, str]:
        """Generate Redis keys for different time windows."""
        base_key = f"rate_limit:{limit_type.value}:{identifier}"
        return {
            "minute": f"{base_key}:minute",
            "hour": f"{base_key}:hour", 
            "day": f"{base_key}:day",
            "block": f"{base_key}:block",
            "attempts": f"{base_key}:attempts"
        }
    
    async def _sliding_window_check(
        self, 
        key: str, 
        limit: int, 
        window_seconds: int,
        burst_allowance: int = 0
    ) -> Tuple[bool, int, int]:
        """
        Implement sliding window rate limiting.
        Returns: (allowed, current_count, remaining)
        """
        if not self.redis_client:
            raise RuntimeError("Rate limiter not initialized")
        
        now = int(time.time())
        window_start = now - window_seconds
        
        # Use Redis pipeline for atomic operations
        pipe = self.redis_client.pipeline()
        
        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Count current requests in window
        pipe.zcard(key)
        
        # Add current request
        pipe.zadd(key, {str(now): now})
        
        # Set expiration
        pipe.expire(key, window_seconds + 60)
        
        results = await pipe.execute()
        current_count = results[1] + 1  # +1 for current request
        
        effective_limit = limit + burst_allowance
        allowed = current_count <= effective_limit
        remaining = max(0, effective_limit - current_count)
        
        if not allowed:
            # Remove the request we just added since it's not allowed
            await self.redis_client.zrem(key, str(now))
            current_count -= 1
            remaining = 0
        
        return allowed, current_count, remaining
    
    async def check_rate_limit(
        self,
        identifier: str,
        limit_type: RateLimitType,
        user_tier: RateLimitTier = RateLimitTier.FREE,
        check_only: bool = False
    ) -> RateLimitResult:
        """
        Check if request is within rate limits.
        
        Args:
            identifier: User ID, IP address, or other identifier
            limit_type: Type of rate limit to apply
            user_tier: User's subscription tier
            check_only: If True, don't increment counters (for checking status)
        """
        if not self.redis_client:
            raise RuntimeError("Rate limiter not initialized")
        
        # Check if already blocked
        block_info = await self.check_security_block(identifier, limit_type)
        if block_info:
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=block_info.blocked_until,
                retry_after=int((block_info.blocked_until - datetime.utcnow()).total_seconds()),
                current_usage=0,
                limit=0
            )
        
        config = self.rate_limit_configs[limit_type][user_tier]
        keys = self._get_redis_keys(identifier, limit_type)
        
        # Check different time windows
        checks = [
            ("minute", config.requests_per_minute, 60),
            ("hour", config.requests_per_hour, 3600),
            ("day", config.requests_per_day, 86400)
        ]
        
        results = []
        for window_name, limit, seconds in checks:
            if check_only:
                # For check-only, just count without incrementing
                current_count = await self.redis_client.zcard(keys[window_name])
                allowed = current_count < limit + config.burst_allowance
                remaining = max(0, limit + config.burst_allowance - current_count)
            else:
                allowed, current_count, remaining = await self._sliding_window_check(
                    keys[window_name], limit, seconds, config.burst_allowance
                )
            
            results.append((allowed, current_count, remaining, limit + config.burst_allowance))
            
            if not allowed:
                # Log rate limit violation
                await self._log_rate_limit_violation(
                    identifier, limit_type, window_name, current_count, limit
                )
                
                # Check if this should trigger a security block
                await self._check_security_block_trigger(identifier, limit_type, config)
                
                reset_time = datetime.utcnow() + timedelta(seconds=seconds)
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=reset_time,
                    retry_after=seconds,
                    current_usage=current_count,
                    limit=limit + config.burst_allowance
                )
        
        # If all checks pass, use the most restrictive remaining count
        min_remaining = min(result[2] for result in results)
        max_usage = max(result[1] for result in results)
        max_limit = max(result[3] for result in results)
        
        return RateLimitResult(
            allowed=True,
            remaining=min_remaining,
            reset_time=datetime.utcnow() + timedelta(minutes=1),
            current_usage=max_usage,
            limit=max_limit
        )
    
    async def _check_security_block_trigger(
        self, 
        identifier: str, 
        limit_type: RateLimitType, 
        config: RateLimitConfig
    ):
        """Check if repeated violations should trigger a security block."""
        violation_key = f"violations:{limit_type.value}:{identifier}"
        
        # Increment violation count
        violation_count = await self.redis_client.incr(violation_key)
        await self.redis_client.expire(violation_key, 3600)  # Reset violations after 1 hour
        
        # Trigger security block after multiple violations
        if violation_count >= 3:  # 3 violations in an hour = block
            await self.create_security_block(
                identifier,
                limit_type,
                config.block_duration_minutes,
                f"Multiple rate limit violations ({violation_count})"
            )
    
    async def create_security_block(
        self,
        identifier: str,
        block_type: RateLimitType,
        duration_minutes: int,
        reason: str
    ):
        """Create a security block for an identifier."""
        blocked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        
        block_info = SecurityBlock(
            blocked_until=blocked_until,
            reason=reason,
            attempt_count=1,
            block_type=block_type
        )
        
        keys = self._get_redis_keys(identifier, block_type)
        await self.redis_client.setex(
            keys["block"],
            int(duration_minutes * 60),
            block_info.model_dump_json()
        )
        
        # Log security block
        security_logger.warning(
            "Security block created",
            extra={
                "identifier": identifier,
                "block_type": block_type.value,
                "duration_minutes": duration_minutes,
                "reason": reason,
                "blocked_until": blocked_until.isoformat()
            }
        )
    
    async def check_security_block(
        self, 
        identifier: str, 
        block_type: RateLimitType
    ) -> Optional[SecurityBlock]:
        """Check if identifier is currently blocked."""
        keys = self._get_redis_keys(identifier, block_type)
        block_data = await self.redis_client.get(keys["block"])
        
        if block_data:
            block_info = SecurityBlock.model_validate_json(block_data)
            if block_info.blocked_until > datetime.utcnow():
                return block_info
            else:
                # Block expired, clean up
                await self.redis_client.delete(keys["block"])
        
        return None
    
    async def remove_security_block(self, identifier: str, block_type: RateLimitType):
        """Remove a security block (admin function)."""
        keys = self._get_redis_keys(identifier, block_type)
        await self.redis_client.delete(keys["block"])
        
        security_logger.info(
            "Security block removed",
            extra={
                "identifier": identifier,
                "block_type": block_type.value
            }
        )
    
    async def _log_rate_limit_violation(
        self,
        identifier: str,
        limit_type: RateLimitType,
        window: str,
        current_count: int,
        limit: int
    ):
        """Log rate limit violations for monitoring."""
        security_logger.warning(
            "Rate limit exceeded",
            extra={
                "identifier": identifier,
                "limit_type": limit_type.value,
                "window": window,
                "current_count": current_count,
                "limit": limit,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def get_rate_limit_status(
        self, 
        identifier: str, 
        limit_type: RateLimitType,
        user_tier: RateLimitTier = RateLimitTier.FREE
    ) -> Dict[str, RateLimitResult]:
        """Get current rate limit status for all time windows."""
        status = {}
        
        for window in ["minute", "hour", "day"]:
            result = await self.check_rate_limit(
                identifier, limit_type, user_tier, check_only=True
            )
            status[window] = result
        
        return status
    
    async def reset_rate_limits(self, identifier: str, limit_type: RateLimitType):
        """Reset rate limits for an identifier (admin function)."""
        keys = self._get_redis_keys(identifier, limit_type)
        
        await self.redis_client.delete(
            keys["minute"],
            keys["hour"], 
            keys["day"],
            keys["attempts"]
        )
        
        security_logger.info(
            "Rate limits reset",
            extra={
                "identifier": identifier,
                "limit_type": limit_type.value
            }
        )
    
    async def cleanup_expired_data(self):
        """Clean up expired rate limiting data (maintenance function)."""
        try:
            # This would typically be run as a background task
            pattern = "rate_limit:*"
            cursor = 0
            deleted_count = 0
            
            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor=cursor, match=pattern, count=1000
                )
                
                if keys:
                    # Check TTL and remove expired keys
                    for key in keys:
                        ttl = await self.redis_client.ttl(key)
                        if ttl == -1:  # No expiration set
                            await self.redis_client.expire(key, 86400)  # Set 24h expiration
                        elif ttl == -2:  # Key doesn't exist
                            deleted_count += 1
                
                if cursor == 0:
                    break
            
            logger.info(f"Rate limit cleanup completed. Processed expired keys: {deleted_count}")
            
        except Exception as e:
            logger.error(f"Error during rate limit cleanup: {e}")
    
    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()


# Global rate limiter instance
rate_limiter = RateLimiter()


async def get_rate_limiter() -> RateLimiter:
    """Dependency to get rate limiter instance."""
    if not rate_limiter.redis_client:
        await rate_limiter.initialize()
    return rate_limiter


def rate_limit(requests_per_hour: int = 1000, requests_per_minute: int = 100):
    """
    Decorator for rate limiting API endpoints.
    
    Args:
        requests_per_hour: Maximum requests per hour (default: 1000)
        requests_per_minute: Maximum requests per minute (default: 100)
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user and request from function arguments
            current_user = None
            request = None
            
            # Find current_user in kwargs
            if 'current_user' in kwargs:
                current_user = kwargs['current_user']
            elif 'request' in kwargs:
                request = kwargs['request']
            
            # Create identifier for rate limiting
            if current_user:
                identifier = f"user:{current_user.id}"
            elif request:
                identifier = f"ip:{request.client.host}"
            else:
                # Fallback to function name
                identifier = f"func:{func.__name__}"
            
            # Get rate limiter instance
            limiter = await get_rate_limiter()
            
            # Check rate limits
            result = await limiter.check_rate_limit(
                identifier=identifier,
                limit_type=RateLimitType.GENERAL,
                user_tier=RateLimitTier.FREE  # Default tier
            )
            
            if not result.allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Rate limit exceeded",
                        "retry_after": result.retry_after,
                        "limit": result.limit,
                        "current_usage": result.current_usage
                    }
                )
            
            # Call the original function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator