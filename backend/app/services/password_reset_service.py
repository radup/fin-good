"""
Password reset service with comprehensive security features.
Implements secure token generation, validation, and rate limiting for financial applications.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models.user import User, PasswordResetToken
from app.services.email_service import get_email_service, EmailServiceException
from app.core.config import settings
from app.core.audit_logger import get_audit_logger
from app.core.audit_logger import security_audit_logger as security_logger

logger = logging.getLogger(__name__)
audit_logger = get_audit_logger()


class PasswordResetResult:
    """Result object for password reset operations."""
    
    def __init__(self, success: bool, message: str, error_code: Optional[str] = None):
        self.success = success
        self.message = message
        self.error_code = error_code


class PasswordResetRateLimitExceeded(Exception):
    """Exception raised when reset rate limit is exceeded."""
    pass


class PasswordResetService:
    """
    Secure password reset service with comprehensive security features.
    """
    
    def __init__(self):
        self.email_service = get_email_service()
        
        # Security configuration
        self.token_expiry_hours = getattr(settings, 'PASSWORD_RESET_TOKEN_EXPIRE_HOURS', 1)
        self.max_reset_attempts_per_hour = getattr(settings, 'MAX_PASSWORD_RESET_ATTEMPTS_PER_HOUR', 3)
        self.max_reset_attempts_per_day = getattr(settings, 'MAX_PASSWORD_RESET_ATTEMPTS_PER_DAY', 10)
        self.token_length = 32  # 256-bit token
        
        # Cleanup configuration
        self.cleanup_expired_tokens_enabled = True
    
    def _generate_secure_token(self) -> str:
        """Generate cryptographically secure reset token."""
        return secrets.token_urlsafe(self.token_length)
    
    def _hash_token(self, token: str) -> str:
        """Hash token for secure storage."""
        return hashlib.sha256(token.encode('utf-8')).hexdigest()
    
    def _check_rate_limits(self, db: Session, user_id: int, client_ip: str) -> None:
        """
        Check rate limits for password reset requests.
        
        Raises:
            PasswordResetRateLimitExceeded: If rate limits are exceeded
        """
        now = datetime.utcnow()
        
        # Check hourly limit
        one_hour_ago = now - timedelta(hours=1)
        hourly_count = db.query(PasswordResetToken).filter(
            and_(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.created_at >= one_hour_ago
            )
        ).count()
        
        if hourly_count >= self.max_reset_attempts_per_hour:
            # Log security event
            security_logger.warning(
                "Password reset rate limit exceeded (hourly)",
                extra={
                    "user_id": user_id,
                    "client_ip": client_ip,
                    "attempts_in_hour": hourly_count,
                    "limit": self.max_reset_attempts_per_hour,
                    "timestamp": now.isoformat()
                }
            )
            raise PasswordResetRateLimitExceeded(
                f"Too many password reset attempts. Please wait before trying again."
            )
        
        # Check daily limit
        one_day_ago = now - timedelta(days=1)
        daily_count = db.query(PasswordResetToken).filter(
            and_(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.created_at >= one_day_ago
            )
        ).count()
        
        if daily_count >= self.max_reset_attempts_per_day:
            # Log security event
            security_logger.warning(
                "Password reset rate limit exceeded (daily)",
                extra={
                    "user_id": user_id,
                    "client_ip": client_ip,
                    "attempts_in_day": daily_count,
                    "limit": self.max_reset_attempts_per_day,
                    "timestamp": now.isoformat()
                }
            )
            raise PasswordResetRateLimitExceeded(
                f"Daily password reset limit exceeded. Please contact support if you need assistance."
            )
    
    def _cleanup_expired_tokens(self, db: Session, user_id: Optional[int] = None) -> int:
        """Clean up expired password reset tokens."""
        if not self.cleanup_expired_tokens_enabled:
            return 0
        
        try:
            now = datetime.utcnow()
            query = db.query(PasswordResetToken).filter(
                PasswordResetToken.expires_at <= now
            )
            
            if user_id:
                query = query.filter(PasswordResetToken.user_id == user_id)
            
            expired_tokens = query.all()
            count = len(expired_tokens)
            
            if count > 0:
                # Delete expired tokens
                query.delete()
                db.commit()
                
                logger.info(f"Cleaned up {count} expired password reset tokens")
            
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {e}")
            db.rollback()
            return 0
    
    def _invalidate_existing_tokens(self, db: Session, user_id: int) -> int:
        """Invalidate all existing password reset tokens for a user."""
        try:
            # Mark existing tokens as used
            updated_count = db.query(PasswordResetToken).filter(
                and_(
                    PasswordResetToken.user_id == user_id,
                    PasswordResetToken.is_used == False,
                    PasswordResetToken.expires_at > datetime.utcnow()
                )
            ).update({"is_used": True})
            
            db.commit()
            
            if updated_count > 0:
                logger.info(f"Invalidated {updated_count} existing tokens for user {user_id}")
            
            return updated_count
            
        except Exception as e:
            logger.error(f"Error invalidating existing tokens: {e}")
            db.rollback()
            return 0
    
    async def request_password_reset(
        self,
        db: Session,
        email: str,
        client_ip: str,
        user_agent: Optional[str] = None
    ) -> PasswordResetResult:
        """
        Request a password reset for a user.
        
        Args:
            db: Database session
            email: User's email address
            client_ip: Client IP address
            user_agent: Client user agent
            
        Returns:
            PasswordResetResult: Result of the operation
        """
        try:
            # Find user by email
            user = db.query(User).filter(
                and_(
                    User.email == email.lower().strip(),
                    User.is_active == True
                )
            ).first()
            
            # Always return success message for security (prevent email enumeration)
            success_message = (
                "If an account with this email exists, you will receive a password reset link shortly."
            )
            
            if not user:
                # Log potential reconnaissance attempt
                security_logger.info(
                    "Password reset requested for non-existent email",
                    extra={
                        "email": email,
                        "client_ip": client_ip,
                        "user_agent": user_agent,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                return PasswordResetResult(True, success_message)
            
            # Check rate limits
            try:
                self._check_rate_limits(db, user.id, client_ip)
            except PasswordResetRateLimitExceeded as e:
                # Log rate limit violation
                audit_logger.log_security_event(
                    event_type="password_reset_rate_limit_exceeded",
                    user_id=user.id,
                    details={
                        "email": email,
                        "client_ip": client_ip,
                        "user_agent": user_agent,
                        "error": str(e)
                    }
                )
                
                # Return generic message for security
                return PasswordResetResult(
                    False, 
                    "Too many password reset attempts. Please try again later.",
                    "RATE_LIMIT_EXCEEDED"
                )
            
            # Clean up expired tokens
            self._cleanup_expired_tokens(db, user.id)
            
            # Invalidate existing active tokens (security best practice)
            self._invalidate_existing_tokens(db, user.id)
            
            # Generate secure token
            reset_token = self._generate_secure_token()
            token_hash = self._hash_token(reset_token)
            expires_at = datetime.utcnow() + timedelta(hours=self.token_expiry_hours)
            
            # Create reset token record
            reset_token_record = PasswordResetToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
                created_ip=client_ip,
                user_agent=user_agent
            )
            
            db.add(reset_token_record)
            db.commit()
            
            # Send reset email
            email_sent = await self.email_service.send_password_reset_email(
                user_email=user.email,
                user_name=user.full_name or user.email,
                reset_token=reset_token,
                expires_at=expires_at
            )
            
            if not email_sent:
                # Rollback token creation if email failed
                db.delete(reset_token_record)
                db.commit()
                
                logger.error(f"Failed to send password reset email to {email}")
                
                return PasswordResetResult(
                    False,
                    "Failed to send password reset email. Please try again later.",
                    "EMAIL_SEND_FAILED"
                )
            
            # Log successful reset request
            audit_logger.log_security_event(
                event_type="password_reset_requested",
                user_id=user.id,
                details={
                    "email": email,
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "token_expires_at": expires_at.isoformat()
                }
            )
            
            logger.info(f"Password reset token generated for user {user.id}")
            
            return PasswordResetResult(True, success_message)
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error in password reset request: {e}")
            
            # Log system error
            audit_logger.log_security_event(
                event_type="password_reset_system_error",
                user_id=user.id if 'user' in locals() else None,
                details={
                    "email": email,
                    "client_ip": client_ip,
                    "error": str(e)
                }
            )
            
            return PasswordResetResult(
                False,
                "An error occurred while processing your request. Please try again later.",
                "SYSTEM_ERROR"
            )
    
    def verify_reset_token(
        self,
        db: Session,
        token: str,
        client_ip: str
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Verify a password reset token.
        
        Args:
            db: Database session
            token: Reset token to verify
            client_ip: Client IP address
            
        Returns:
            Tuple[bool, Optional[int], Optional[str]]: (is_valid, user_id, error_message)
        """
        try:
            if not token or len(token.strip()) == 0:
                return False, None, "Invalid token"
            
            # Hash the provided token
            token_hash = self._hash_token(token)
            
            # Find token record
            reset_token_record = db.query(PasswordResetToken).filter(
                PasswordResetToken.token_hash == token_hash
            ).first()
            
            if not reset_token_record:
                # Log invalid token attempt
                security_logger.warning(
                    "Invalid password reset token attempted",
                    extra={
                        "client_ip": client_ip,
                        "token_hash": token_hash[:16] + "...",  # Log partial hash for debugging
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                return False, None, "Invalid or expired token"
            
            # Check if token is valid
            if not reset_token_record.is_valid:
                error_message = "Token has expired" if reset_token_record.is_expired else "Token has already been used"
                
                # Log expired/used token attempt
                security_logger.info(
                    "Expired or used password reset token attempted",
                    extra={
                        "user_id": reset_token_record.user_id,
                        "client_ip": client_ip,
                        "is_expired": reset_token_record.is_expired,
                        "is_used": reset_token_record.is_used,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                return False, None, error_message
            
            # Verify user still exists and is active
            user = db.query(User).filter(
                and_(
                    User.id == reset_token_record.user_id,
                    User.is_active == True
                )
            ).first()
            
            if not user:
                # Log attempt for inactive/deleted user
                security_logger.warning(
                    "Password reset attempted for inactive/deleted user",
                    extra={
                        "user_id": reset_token_record.user_id,
                        "client_ip": client_ip,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                return False, None, "User account not found or inactive"
            
            return True, user.id, None
            
        except Exception as e:
            logger.error(f"Error verifying reset token: {e}")
            return False, None, "Error verifying token"
    
    def reset_password(
        self,
        db: Session,
        token: str,
        new_password: str,
        client_ip: str,
        user_agent: Optional[str] = None
    ) -> PasswordResetResult:
        """
        Reset user password with token validation.
        
        Args:
            db: Database session
            token: Reset token
            new_password: New password
            client_ip: Client IP address
            user_agent: Client user agent
            
        Returns:
            PasswordResetResult: Result of the operation
        """
        try:
            # Verify token
            is_valid, user_id, error_message = self.verify_reset_token(db, token, client_ip)
            
            if not is_valid:
                return PasswordResetResult(False, error_message or "Invalid token", "INVALID_TOKEN")
            
            # Get user and token record
            token_hash = self._hash_token(token)
            reset_token_record = db.query(PasswordResetToken).filter(
                PasswordResetToken.token_hash == token_hash
            ).first()
            
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user or not reset_token_record:
                return PasswordResetResult(False, "Invalid token", "INVALID_TOKEN")
            
            # Validate new password (basic validation)
            if len(new_password) < 8:
                return PasswordResetResult(
                    False, 
                    "Password must be at least 8 characters long", 
                    "WEAK_PASSWORD"
                )
            
            # Import password hashing function
            from app.api.v1.endpoints.auth import get_password_hash
            
            # Update user password
            user.hashed_password = get_password_hash(new_password)
            
            # Mark token as used
            reset_token_record.is_used = True
            reset_token_record.used_at = datetime.utcnow()
            reset_token_record.used_ip = client_ip
            
            # Invalidate any other active tokens for this user
            self._invalidate_existing_tokens(db, user.id)
            
            db.commit()
            
            # Log successful password reset
            audit_logger.log_security_event(
                event_type="password_reset_completed",
                user_id=user.id,
                details={
                    "email": user.email,
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "token_id": reset_token_record.id
                }
            )
            
            logger.info(f"Password reset completed for user {user.id}")
            
            # Clean up expired tokens
            self._cleanup_expired_tokens(db)
            
            return PasswordResetResult(True, "Password reset successfully")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error resetting password: {e}")
            
            # Log system error
            audit_logger.log_security_event(
                event_type="password_reset_system_error",
                user_id=user_id if 'user_id' in locals() else None,
                details={
                    "client_ip": client_ip,
                    "error": str(e)
                }
            )
            
            return PasswordResetResult(
                False,
                "An error occurred while resetting your password. Please try again.",
                "SYSTEM_ERROR"
            )
    
    def cleanup_expired_tokens_batch(self, db: Session) -> int:
        """Batch cleanup of expired tokens (for scheduled jobs)."""
        return self._cleanup_expired_tokens(db)


# Global service instance
_password_reset_service_instance = None


def get_password_reset_service() -> PasswordResetService:
    """Get global password reset service instance."""
    global _password_reset_service_instance
    
    if _password_reset_service_instance is None:
        _password_reset_service_instance = PasswordResetService()
    
    return _password_reset_service_instance