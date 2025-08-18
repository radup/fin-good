"""
Token blacklisting service for FinGood financial application.
Provides secure token revocation and blacklist management for JWT tokens.
Critical for financial application security and compliance.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.user import RevokedToken
from app.core.security import jwt_manager

# Configure service logging
blacklist_logger = logging.getLogger("fingood.token_blacklist")
blacklist_logger.setLevel(logging.INFO)


@dataclass
class TokenRevocationInfo:
    """Information about a revoked token."""
    jti: str
    user_id: int
    revoked_at: datetime
    expires_at: datetime
    reason: str
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class BlacklistStats:
    """Statistics about the token blacklist."""
    total_revoked: int
    expired_count: int
    active_count: int
    oldest_active: Optional[datetime]
    newest_revoked: Optional[datetime]


class TokenBlacklistService:
    """
    Service for managing JWT token blacklisting operations.
    Provides secure token revocation, cleanup, and audit functionality.
    """
    
    def __init__(self):
        self.logger = blacklist_logger
    
    def revoke_token_by_jti(
        self, 
        jti: str, 
        user_id: int, 
        reason: str, 
        expires_at: datetime,
        db: Session,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Revoke a token by its JTI (JWT ID).
        
        Args:
            jti: JWT ID of the token to revoke
            user_id: ID of the user who owns the token
            reason: Reason for revocation
            expires_at: Original expiration time of the token
            db: Database session
            client_ip: Client IP for audit trail
            user_agent: User agent for audit trail
            
        Returns:
            True if revocation successful, False otherwise
        """
        try:
            # Check if token is already revoked
            existing = db.query(RevokedToken).filter(
                RevokedToken.jti == jti
            ).first()
            
            if existing:
                self.logger.info(f"Token already revoked - JTI: {jti}, User: {user_id}")
                return True
            
            # Create revocation record
            revoked_token = RevokedToken(
                jti=jti,
                token_hash="",  # Will be set when full token is available
                user_id=user_id,
                expires_at=expires_at,
                revocation_reason=reason,
                client_ip=client_ip,
                user_agent=user_agent
            )
            
            db.add(revoked_token)
            db.commit()
            
            self.logger.info(
                f"Token revoked by JTI - JTI: {jti}, User: {user_id}, "
                f"Reason: {reason}, IP: {client_ip}"
            )
            
            return True
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Failed to revoke token by JTI: {str(e)}")
            return False
    
    def is_token_revoked(self, jti: str, db: Session) -> bool:
        """
        Check if a token is revoked by its JTI.
        
        Args:
            jti: JWT ID to check
            db: Database session
            
        Returns:
            True if token is revoked, False otherwise
        """
        try:
            revoked = db.query(RevokedToken).filter(
                and_(
                    RevokedToken.jti == jti,
                    RevokedToken.expires_at > datetime.utcnow()
                )
            ).first()
            
            return revoked is not None
            
        except Exception as e:
            self.logger.error(f"Error checking token revocation: {str(e)}")
            # Fail secure - assume revoked if we can't check
            return True
    
    def revoke_all_user_tokens(
        self, 
        user_id: int, 
        reason: str, 
        db: Session,
        client_ip: Optional[str] = None
    ) -> int:
        """
        Mark all active tokens for a user as revoked.
        Note: This is a logical revocation - we add a special marker.
        
        Args:
            user_id: ID of the user whose tokens should be revoked
            reason: Reason for mass revocation
            db: Database session
            client_ip: Client IP for audit trail
            
        Returns:
            Number of revocation records created
        """
        try:
            # Create a mass revocation marker
            # This uses a special JTI pattern to mark all tokens for the user as invalid
            mass_revocation_jti = f"MASS_REVOKE_{user_id}_{datetime.utcnow().isoformat()}"
            
            revoked_token = RevokedToken(
                jti=mass_revocation_jti,
                token_hash="MASS_REVOCATION",
                user_id=user_id,
                expires_at=datetime.utcnow() + timedelta(days=365),  # Long expiry for audit
                revocation_reason=f"MASS_REVOCATION: {reason}",
                client_ip=client_ip,
                user_agent="system"
            )
            
            db.add(revoked_token)
            db.commit()
            
            self.logger.warning(
                f"Mass token revocation - User: {user_id}, Reason: {reason}, "
                f"IP: {client_ip}, Marker: {mass_revocation_jti}"
            )
            
            return 1
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Failed mass token revocation: {str(e)}")
            return 0
    
    def has_mass_revocation(self, user_id: int, issued_at: datetime, db: Session) -> bool:
        """
        Check if there's a mass revocation that affects a token.
        
        Args:
            user_id: User ID to check
            issued_at: When the token was issued
            db: Database session
            
        Returns:
            True if token is affected by mass revocation
        """
        try:
            mass_revocation = db.query(RevokedToken).filter(
                and_(
                    RevokedToken.user_id == user_id,
                    RevokedToken.jti.like(f"MASS_REVOKE_{user_id}_%"),
                    RevokedToken.revoked_at > issued_at,
                    RevokedToken.expires_at > datetime.utcnow()
                )
            ).first()
            
            return mass_revocation is not None
            
        except Exception as e:
            self.logger.error(f"Error checking mass revocation: {str(e)}")
            # Fail secure
            return True
    
    def get_user_revoked_tokens(
        self, 
        user_id: int, 
        limit: int = 50, 
        db: Session
    ) -> List[TokenRevocationInfo]:
        """
        Get revoked tokens for a specific user.
        
        Args:
            user_id: User ID to get revoked tokens for
            limit: Maximum number of records to return
            db: Database session
            
        Returns:
            List of token revocation information
        """
        try:
            revoked_tokens = db.query(RevokedToken).filter(
                RevokedToken.user_id == user_id
            ).order_by(
                RevokedToken.revoked_at.desc()
            ).limit(limit).all()
            
            return [
                TokenRevocationInfo(
                    jti=token.jti,
                    user_id=token.user_id,
                    revoked_at=token.revoked_at,
                    expires_at=token.expires_at,
                    reason=token.revocation_reason or "unknown",
                    client_ip=token.client_ip,
                    user_agent=token.user_agent
                )
                for token in revoked_tokens
            ]
            
        except Exception as e:
            self.logger.error(f"Error getting user revoked tokens: {str(e)}")
            return []
    
    def cleanup_expired_tokens(self, db: Session, batch_size: int = 1000) -> int:
        """
        Clean up expired tokens from the blacklist.
        
        Args:
            db: Database session
            batch_size: Number of records to process at once
            
        Returns:
            Total number of tokens cleaned up
        """
        total_cleaned = 0
        cutoff_time = datetime.utcnow()
        
        try:
            while True:
                # Process in batches to avoid large transactions
                expired_tokens = db.query(RevokedToken).filter(
                    RevokedToken.expires_at < cutoff_time
                ).limit(batch_size).all()
                
                if not expired_tokens:
                    break
                
                batch_count = len(expired_tokens)
                
                # Delete the batch
                for token in expired_tokens:
                    db.delete(token)
                
                db.commit()
                total_cleaned += batch_count
                
                self.logger.info(f"Cleaned up batch of {batch_count} expired tokens")
                
                # If we got less than batch_size, we're done
                if batch_count < batch_size:
                    break
            
            if total_cleaned > 0:
                self.logger.info(f"Cleanup completed: {total_cleaned} expired tokens removed")
            
            return total_cleaned
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error during token cleanup: {str(e)}")
            return total_cleaned
    
    def get_blacklist_stats(self, db: Session) -> BlacklistStats:
        """
        Get statistics about the token blacklist.
        
        Args:
            db: Database session
            
        Returns:
            Blacklist statistics
        """
        try:
            now = datetime.utcnow()
            
            # Total revoked tokens
            total_revoked = db.query(func.count(RevokedToken.id)).scalar() or 0
            
            # Expired tokens
            expired_count = db.query(func.count(RevokedToken.id)).filter(
                RevokedToken.expires_at < now
            ).scalar() or 0
            
            # Active (non-expired) tokens
            active_count = total_revoked - expired_count
            
            # Oldest active token
            oldest_active = db.query(func.min(RevokedToken.revoked_at)).filter(
                RevokedToken.expires_at > now
            ).scalar()
            
            # Newest revoked token
            newest_revoked = db.query(func.max(RevokedToken.revoked_at)).scalar()
            
            return BlacklistStats(
                total_revoked=total_revoked,
                expired_count=expired_count,
                active_count=active_count,
                oldest_active=oldest_active,
                newest_revoked=newest_revoked
            )
            
        except Exception as e:
            self.logger.error(f"Error getting blacklist stats: {str(e)}")
            return BlacklistStats(
                total_revoked=0,
                expired_count=0,
                active_count=0,
                oldest_active=None,
                newest_revoked=None
            )
    
    def audit_revocation_activity(
        self, 
        start_date: datetime, 
        end_date: datetime, 
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Get audit information about revocation activity in a date range.
        
        Args:
            start_date: Start of audit period
            end_date: End of audit period
            db: Database session
            
        Returns:
            List of audit records
        """
        try:
            revocations = db.query(RevokedToken).filter(
                and_(
                    RevokedToken.revoked_at >= start_date,
                    RevokedToken.revoked_at <= end_date
                )
            ).order_by(RevokedToken.revoked_at.desc()).all()
            
            audit_records = []
            for token in revocations:
                audit_records.append({
                    "jti": token.jti,
                    "user_id": token.user_id,
                    "revoked_at": token.revoked_at.isoformat(),
                    "expires_at": token.expires_at.isoformat(),
                    "reason": token.revocation_reason,
                    "client_ip": token.client_ip,
                    "user_agent": token.user_agent
                })
            
            return audit_records
            
        except Exception as e:
            self.logger.error(f"Error generating audit report: {str(e)}")
            return []


# Global service instance
token_blacklist_service = TokenBlacklistService()