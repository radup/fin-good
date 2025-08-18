# CRIT-002: Fix JWT token validation and implement proper expiration checks

## Overview
The current JWT validation in the authentication system has inadequate error handling and lacks proper token expiration validation. The broad exception handling (`except jwt.PyJWTError`) may allow expired or malicious tokens to be accepted, creating authentication bypass vulnerabilities.

## Priority Level
🔴 CRITICAL - Authentication bypass vulnerability in financial application

## Assigned Agent
fintech-compliance-engineer - Specialized in authentication security and financial compliance

## Requirements

### Implementation Requirements
- [ ] Replace broad PyJWTError handling with specific exception types
- [ ] Implement explicit token expiration validation
- [ ] Add token blacklisting/revocation mechanism
- [ ] Improve JWT payload validation (claims verification)
- [ ] Add token refresh mechanism
- [ ] Implement proper error logging for security monitoring
- [ ] Add rate limiting for token validation attempts

### Testing Requirements
- [ ] Unit tests for each JWT exception scenario
- [ ] Integration tests for expired token handling
- [ ] Test token revocation functionality
- [ ] Security testing for token manipulation attempts
- [ ] Performance testing for token validation at scale
- [ ] Test error response consistency

### Code Review Requirements
- [ ] Security review for authentication flow
- [ ] Review error message security (no info leakage)
- [ ] Validate token revocation mechanism
- [ ] Check for timing attack vulnerabilities

## Technical Details

### Files to Modify
- `backend/app/api/v1/endpoints/auth.py` - JWT validation logic (lines 44-55)
- `backend/app/core/database.py` - Add token blacklist table/mechanism
- `backend/app/models/user.py` - Add token tracking if needed
- `backend/app/schemas/user.py` - Update token schemas

### Dependencies
- CRIT-001 (SECRET_KEY security) - ✅ COMPLETED
- Database migration for token blacklist table

### Current Problematic Code
```python
# backend/app/api/v1/endpoints/auth.py:44-55
try:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
except jwt.PyJWTError:  # TOO BROAD - masks specific issues
    raise credentials_exception
```

## Error Handling Strategy

### Specific JWT Error Scenarios
1. **ExpiredSignatureError**: Token has expired
2. **InvalidTokenError**: Token is malformed or invalid
3. **InvalidSignatureError**: Token signature doesn't match
4. **InvalidKeyError**: Wrong signing key used
5. **InvalidIssuerError**: Token issuer validation failed
6. **InvalidAudienceError**: Token audience validation failed
7. **RevokedTokenError**: Token has been blacklisted

### Error Response Format
```python
# Specific error handling without information leakage
{
    "error": "Authentication failed",
    "code": "INVALID_TOKEN",
    "message": "Please log in again",
    "request_id": "uuid"
}
```

### Security Logging
```python
# Log security events without exposing sensitive data
security_logger.warning(
    "Authentication attempt failed",
    extra={
        "reason": "expired_token",
        "user_agent": request.headers.get("user-agent"),
        "ip_address": request.client.host,
        "timestamp": datetime.utcnow()
    }
)
```

## Implementation Plan

### Phase 1: Enhanced JWT Validation
```python
import jwt
from jwt.exceptions import (
    ExpiredSignatureError,
    InvalidTokenError, 
    InvalidSignatureError,
    InvalidKeyError
)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication failed",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode with explicit validation
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM],
            options={
                "verify_exp": True,  # Explicit expiration check
                "verify_iat": True,  # Issued at validation
                "verify_nbf": True,  # Not before validation
            }
        )
        
        # Validate required claims
        email: str = payload.get("sub")
        if email is None:
            security_logger.warning("JWT missing subject claim")
            raise credentials_exception
            
        # Check token blacklist
        if await is_token_blacklisted(token, db):
            security_logger.warning(f"Blacklisted token used for {email}")
            raise credentials_exception
            
    except ExpiredSignatureError:
        security_logger.info("Expired token authentication attempt")
        raise credentials_exception
    except InvalidSignatureError:
        security_logger.warning("Invalid signature authentication attempt")
        raise credentials_exception
    except InvalidTokenError:
        security_logger.warning("Invalid token format authentication attempt")
        raise credentials_exception
    except Exception as e:
        security_logger.error(f"Unexpected JWT validation error: {type(e).__name__}")
        raise credentials_exception
```

### Phase 2: Token Blacklist Implementation
```python
# New model for token revocation
class RevokedToken(Base):
    __tablename__ = "revoked_tokens"
    
    id = Column(Integer, primary_key=True)
    jti = Column(String(255), unique=True, nullable=False)  # JWT ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    revoked_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    reason = Column(String(100), nullable=True)  # logout, security_breach, etc.

async def is_token_blacklisted(token: str, db: Session) -> bool:
    try:
        # Decode without verification to get JTI
        unverified_payload = jwt.decode(token, options={"verify_signature": False})
        jti = unverified_payload.get("jti")
        
        if jti:
            revoked = db.query(RevokedToken).filter(RevokedToken.jti == jti).first()
            return revoked is not None
    except:
        pass
    return False
```

### Phase 3: Token Refresh Mechanism
```python
@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Refresh access token with proper validation"""
    # Validate refresh token
    # Generate new access token
    # Optionally revoke old token
    # Return new token pair
```

## Testing Strategy

### Unit Tests
```python
def test_expired_token_rejection():
    """Test that expired tokens are properly rejected"""
    pass

def test_invalid_signature_rejection():
    """Test that tokens with invalid signatures are rejected"""
    pass

def test_blacklisted_token_rejection():
    """Test that revoked tokens are rejected"""
    pass

def test_malformed_token_rejection():
    """Test that malformed tokens are rejected"""
    pass

def test_missing_claims_rejection():
    """Test that tokens missing required claims are rejected"""
    pass
```

### Integration Tests
```python
def test_complete_authentication_flow():
    """Test login -> token use -> logout -> token revocation"""
    pass

def test_token_refresh_flow():
    """Test token refresh mechanism"""
    pass

def test_concurrent_token_validation():
    """Test token validation under load"""
    pass
```

### Security Tests
```python
def test_timing_attack_resistance():
    """Ensure token validation doesn't leak timing information"""
    pass

def test_token_manipulation_attempts():
    """Test various token manipulation attacks"""
    pass
```

## Definition of Done

- [ ] All JWT validation uses specific exception handling
- [ ] Token expiration is explicitly validated
- [ ] Token blacklist mechanism implemented and tested
- [ ] Security logging implemented without information leakage
- [ ] All authentication endpoints use improved validation
- [ ] Comprehensive test coverage (>95%) for all scenarios
- [ ] Security review passed with no vulnerabilities
- [ ] Performance validated for high-load scenarios
- [ ] Documentation updated for new authentication flow

## Implementation Log

### [Date] - Initial Analysis
- Current JWT validation at backend/app/api/v1/endpoints/auth.py:44-55
- Broad exception handling masks specific security issues
- No token revocation mechanism exists
- Missing explicit expiration validation

### [Date] - Implementation
- [To be filled during implementation]

### [Date] - Testing  
- [To be filled during testing]

### [Date] - Code Review
- [To be filled during review]

## Related Issues
- CRIT-001: SECRET_KEY security (✅ COMPLETED - dependency)
- CRIT-004: Secure token storage (HttpOnly cookies)
- HIGH-012: Rate limiting implementation
- HIGH-015: Audit logging for authentication events