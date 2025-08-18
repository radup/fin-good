"""
Secure JWT token handling for FinGood financial application.
Implements comprehensive security measures including token blacklisting,
specific exception handling, and security logging.
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Union
from uuid import uuid4

import jwt
from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import RevokedToken

# Configure security logging
security_logger = logging.getLogger("fingood.security")
security_logger.setLevel(logging.INFO)

# Add handler if not already present
if not security_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    security_logger.addHandler(handler)


class JWTSecurityError(Exception):
    """Base exception for JWT security errors."""
    pass


class TokenExpiredError(JWTSecurityError):
    """Token has expired."""
    pass


class TokenRevokedError(JWTSecurityError):
    """Token has been revoked."""
    pass


class TokenInvalidError(JWTSecurityError):
    """Token is invalid or malformed."""
    pass


class JWTManager:
    """
    Secure JWT token manager for financial applications.
    Implements comprehensive security measures required for fintech systems.
    """
    
    def __init__(self, test_settings=None):
        # Use test settings if provided, otherwise use global settings
        config = test_settings if test_settings else settings
        
        if config is None:
            # Fallback for testing when settings are not initialized
            self.algorithm = "HS256"
            self.secret_key = "test-secret-key-for-testing-only"
            self.access_token_expire_minutes = 30
        else:
            self.algorithm = config.ALGORITHM
            self.secret_key = config.SECRET_KEY
            self.access_token_expire_minutes = config.ACCESS_TOKEN_EXPIRE_MINUTES
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None,
        jti: Optional[str] = None
    ) -> str:
        """
        Create a secure JWT access token with comprehensive claims.
        
        Args:
            data: Token payload data (typically contains 'sub' for user email)
            expires_delta: Custom expiration time
            jti: JWT ID for token tracking (generated if not provided)
            
        Returns:
            Encoded JWT token string
            
        Raises:
            JWTSecurityError: If token creation fails
        """
        try:
            to_encode = data.copy()
            
            # Set expiration
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
            
            # Add required claims
            jti = jti or str(uuid4())
            to_encode.update({
                "exp": expire,
                "iat": datetime.utcnow(),  # Issued at
                "jti": jti,  # JWT ID for tracking
                "type": "access"  # Token type
            })
            
            # Encode token
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            
            # Log token creation (without exposing sensitive data)
            security_logger.info(
                f"JWT token created - JTI: {jti}, Subject: {data.get('sub', 'unknown')}, "
                f"Expires: {expire.isoformat()}"
            )
            
            return encoded_jwt
            
        except Exception as e:
            security_logger.error(f"Failed to create JWT token: {str(e)}")
            raise JWTSecurityError(f"Token creation failed: {str(e)}")
    
    def verify_token(
        self, 
        token: str, 
        db: Session,
        request: Optional[Request] = None
    ) -> Dict[str, Any]:
        """
        Verify and decode JWT token with comprehensive security checks.
        
        Args:
            token: JWT token to verify
            db: Database session for blacklist checks
            request: Optional FastAPI request for audit logging
            
        Returns:
            Decoded token payload
            
        Raises:
            TokenExpiredError: If token has expired
            TokenRevokedError: If token has been revoked
            TokenInvalidError: If token is invalid or malformed
        """
        client_ip = None
        user_agent = None
        
        if request:
            client_ip = self._get_client_ip(request)
            user_agent = request.headers.get("User-Agent", "unknown")
        
        try:
            # First decode without verification to get claims for logging
            unverified_payload = jwt.decode(
                token, 
                options={"verify_signature": False, "verify_exp": False}
            )
            jti = unverified_payload.get("jti")
            subject = unverified_payload.get("sub")
            
        except jwt.DecodeError:
            security_logger.warning(
                f"Malformed JWT token received from IP: {client_ip}, "
                f"User-Agent: {user_agent}"
            )
            raise TokenInvalidError("Malformed token")
        
        try:
            # Verify token signature and expiration
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                options={"verify_exp": True, "verify_iat": True}
            )
            
        except jwt.ExpiredSignatureError:
            security_logger.warning(
                f"Expired JWT token attempted - JTI: {jti}, Subject: {subject}, "
                f"IP: {client_ip}, User-Agent: {user_agent}"
            )
            raise TokenExpiredError("Token has expired")
            
        except jwt.InvalidTokenError as e:
            security_logger.warning(
                f"Invalid JWT token attempted - JTI: {jti}, Subject: {subject}, "
                f"IP: {client_ip}, Error: {str(e)}, User-Agent: {user_agent}"
            )
            raise TokenInvalidError(f"Invalid token: {str(e)}")
        
        # Check if token is blacklisted
        if self._is_token_revoked(token, jti, db):
            security_logger.warning(
                f"Revoked JWT token attempted - JTI: {jti}, Subject: {subject}, "
                f"IP: {client_ip}, User-Agent: {user_agent}"
            )
            raise TokenRevokedError("Token has been revoked")
        
        # Validate token structure
        required_claims = ["sub", "exp", "iat", "jti"]
        missing_claims = [claim for claim in required_claims if claim not in payload]
        if missing_claims:
            security_logger.warning(
                f"JWT token missing required claims: {missing_claims}, "
                f"JTI: {jti}, Subject: {subject}, IP: {client_ip}"
            )
            raise TokenInvalidError(f"Token missing required claims: {missing_claims}")
        
        # Log successful token verification
        security_logger.info(
            f"JWT token verified successfully - JTI: {jti}, Subject: {subject}, "
            f"IP: {client_ip}"
        )
        
        return payload
    
    def revoke_token(
        self, 
        token: str, 
        user_id: int,
        reason: str,
        db: Session,
        request: Optional[Request] = None
    ) -> bool:
        """
        Revoke a JWT token by adding it to the blacklist.
        
        Args:
            token: JWT token to revoke
            user_id: ID of the user who owns the token
            reason: Reason for revocation (logout, compromise, etc.)
            db: Database session
            request: Optional FastAPI request for audit logging
            
        Returns:
            True if revocation successful, False otherwise
        """
        try:
            # Decode token to get claims (without verification since it may be expired)
            payload = jwt.decode(
                token, 
                options={"verify_signature": False, "verify_exp": False}
            )
            
            jti = payload.get("jti")
            expires_at = datetime.fromtimestamp(payload.get("exp", 0))
            
            if not jti:
                security_logger.error(f"Cannot revoke token without JTI - User: {user_id}")
                return False
            
            # Create token hash for storage
            token_hash = self._hash_token(token)
            
            # Get client info for audit trail
            client_ip = None
            user_agent = None
            if request:
                client_ip = self._get_client_ip(request)
                user_agent = request.headers.get("User-Agent", "unknown")
            
            # Add to revoked tokens table
            revoked_token = RevokedToken(
                jti=jti,
                token_hash=token_hash,
                user_id=user_id,
                expires_at=expires_at,
                revocation_reason=reason,
                client_ip=client_ip,
                user_agent=user_agent
            )
            
            db.add(revoked_token)
            db.commit()
            
            security_logger.info(
                f"JWT token revoked - JTI: {jti}, User: {user_id}, "
                f"Reason: {reason}, IP: {client_ip}"
            )
            
            return True
            
        except Exception as e:
            db.rollback()
            security_logger.error(
                f"Failed to revoke token - User: {user_id}, Error: {str(e)}"
            )
            return False
    
    def revoke_all_user_tokens(
        self, 
        user_id: int, 
        reason: str, 
        db: Session,
        request: Optional[Request] = None
    ) -> int:
        """
        Revoke all tokens for a specific user.
        Used for security incidents or when user changes password.
        
        Args:
            user_id: ID of the user whose tokens should be revoked
            reason: Reason for mass revocation
            db: Database session
            request: Optional FastAPI request for audit logging
            
        Returns:
            Number of tokens revoked
        """
        try:
            client_ip = None
            if request:
                client_ip = self._get_client_ip(request)
            
            # This is a placeholder implementation
            # In a real system, you would track active tokens per user
            # For now, we'll just log the mass revocation event
            
            security_logger.warning(
                f"Mass token revocation requested - User: {user_id}, "
                f"Reason: {reason}, IP: {client_ip}"
            )
            
            # TODO: Implement actual mass revocation logic
            # This would require tracking all active tokens per user
            
            return 0
            
        except Exception as e:
            security_logger.error(
                f"Failed to revoke all user tokens - User: {user_id}, Error: {str(e)}"
            )
            return 0
    
    def cleanup_expired_tokens(self, db: Session) -> int:
        """
        Clean up expired tokens from the blacklist.
        Should be run periodically to prevent database bloat.
        
        Args:
            db: Database session
            
        Returns:
            Number of tokens cleaned up
        """
        try:
            cutoff_time = datetime.utcnow()
            
            # Delete expired revoked tokens
            deleted_count = db.query(RevokedToken).filter(
                RevokedToken.expires_at < cutoff_time
            ).delete()
            
            db.commit()
            
            if deleted_count > 0:
                security_logger.info(f"Cleaned up {deleted_count} expired revoked tokens")
            
            return deleted_count
            
        except Exception as e:
            db.rollback()
            security_logger.error(f"Failed to cleanup expired tokens: {str(e)}")
            return 0
    
    def _is_token_revoked(self, token: str, jti: Optional[str], db: Session) -> bool:
        """Check if a token is in the revocation blacklist."""
        if not jti:
            return False
        
        try:
            token_hash = self._hash_token(token)
            
            revoked = db.query(RevokedToken).filter(
                RevokedToken.jti == jti,
                RevokedToken.token_hash == token_hash,
                RevokedToken.expires_at > datetime.utcnow()  # Only check non-expired entries
            ).first()
            
            return revoked is not None
            
        except Exception as e:
            security_logger.error(f"Error checking token revocation status: {str(e)}")
            # Fail secure - assume token is revoked if we can't check
            return True
    
    def _hash_token(self, token: str) -> str:
        """Create a SHA256 hash of the token for secure storage."""
        return hashlib.sha256(token.encode()).hexdigest()
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request headers."""
        # Check for forwarded headers (common in load balancer setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"


# Global JWT manager instance
jwt_manager = JWTManager()


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Convenience function for token creation."""
    return jwt_manager.create_access_token(data, expires_delta)


def verify_token(token: str, db: Session, request: Optional[Request] = None) -> Dict[str, Any]:
    """Convenience function for token verification."""
    return jwt_manager.verify_token(token, db, request)


def revoke_token(
    token: str, 
    user_id: int, 
    reason: str, 
    db: Session, 
    request: Optional[Request] = None
) -> bool:
    """Convenience function for token revocation."""
    return jwt_manager.revoke_token(token, user_id, reason, db, request)