from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Index, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # OAuth fields
    oauth_provider = Column(String(50), nullable=True)  # 'google', 'github', etc.
    oauth_id = Column(String(255), nullable=True)
    
    # Business info
    company_name = Column(String(255), nullable=True)
    business_type = Column(String(100), nullable=True)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="user")
    budgets = relationship("Budget", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"


class RevokedToken(Base):
    """
    Model to track revoked JWT tokens for security.
    Critical for preventing replay attacks in financial applications.
    """
    __tablename__ = "revoked_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(255), unique=True, index=True, nullable=False)  # JWT ID claim
    token_hash = Column(String(255), nullable=False, index=True)  # SHA256 hash of token
    user_id = Column(Integer, nullable=False, index=True)  # User who owned the token
    revoked_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)  # Original token expiry
    revocation_reason = Column(String(100), nullable=True)  # logout, compromise, etc.
    client_ip = Column(String(45), nullable=True)  # IPv4/IPv6 for audit trail
    user_agent = Column(Text, nullable=True)  # Browser/client info for audit
    
    # Composite index for efficient queries
    __table_args__ = (
        Index('idx_revoked_tokens_lookup', 'token_hash', 'expires_at'),
        Index('idx_revoked_tokens_cleanup', 'expires_at'),
        Index('idx_revoked_tokens_audit', 'user_id', 'revoked_at'),
    )
    
    def __repr__(self):
        return f"<RevokedToken(id={self.id}, user_id={self.user_id}, revoked_at='{self.revoked_at}')>"


class PasswordResetToken(Base):
    """
    Model for secure password reset tokens.
    Critical for maintaining security in password reset flows.
    """
    __tablename__ = "password_reset_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), unique=True, index=True, nullable=False)  # SHA256 hash of token
    expires_at = Column(DateTime(timezone=True), nullable=False)  # Token expiry (1 hour)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    used_at = Column(DateTime(timezone=True), nullable=True)  # Track when token was used
    is_used = Column(Boolean, default=False, nullable=False)  # Prevent token reuse
    
    # Security and audit fields
    created_ip = Column(String(45), nullable=True)  # IP that requested reset
    used_ip = Column(String(45), nullable=True)     # IP that used the token
    user_agent = Column(Text, nullable=True)        # Browser info for audit
    
    # Relationship
    user = relationship("User", backref="password_reset_tokens")
    
    # Composite indexes for efficient queries
    __table_args__ = (
        Index('idx_reset_tokens_lookup', 'token_hash', 'expires_at', 'is_used'),
        Index('idx_reset_tokens_cleanup', 'expires_at'),
        Index('idx_reset_tokens_user_active', 'user_id', 'is_used', 'expires_at'),
    )
    
    def __repr__(self):
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id}, is_used={self.is_used})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if the token has expired."""
        return datetime.utcnow() > self.expires_at.replace(tzinfo=None)
    
    @property
    def is_valid(self) -> bool:
        """Check if the token is valid (not used and not expired)."""
        return not self.is_used and not self.is_expired
