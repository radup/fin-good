# CRIT-001: Replace hardcoded SECRET_KEY with secure environment variable

## Overview
The application currently uses a hardcoded SECRET_KEY ("your-secret-key-change-in-production") for JWT token signing, which poses a critical security vulnerability. This allows attackers to forge JWT tokens and impersonate any user.

## Priority Level
🔴 CRITICAL - Must be fixed before any production deployment

## Assigned Agent
fintech-compliance-engineer - Specialized in financial security and compliance requirements

## Requirements

### Implementation Requirements
- [ ] Remove hardcoded SECRET_KEY from config.py
- [ ] Add environment variable validation
- [ ] Implement secure key generation for development
- [ ] Add key rotation mechanism
- [ ] Update documentation for deployment
- [ ] Error handling for missing/invalid keys
- [ ] Validate key strength and entropy

### Testing Requirements
- [ ] Unit tests for configuration validation
- [ ] Integration tests for JWT token generation/validation
- [ ] Error scenario testing (missing key, invalid key)
- [ ] Security testing for token forgery prevention
- [ ] Test key rotation functionality

### Code Review Requirements
- [ ] Security review for key management
- [ ] Review environment variable handling
- [ ] Validate error messages don't leak information
- [ ] Check for any remaining hardcoded secrets

## Technical Details

### Files to Modify
- `backend/app/core/config.py` - Update Settings class with proper validation
- `backend/.env.example` - Add SECRET_KEY example
- `docker-compose.yml` - Add environment variable
- `docs/` - Update deployment documentation

### Dependencies
- Must be completed before any other security-related todos
- Required before production deployment

### Implementation Notes
- Use cryptographically secure random key generation
- Key must be at least 256 bits (32 bytes) for HS256
- Consider using HS512 for better security
- Implement proper error handling that doesn't leak system info

## Error Handling Strategy

### Error Scenarios to Handle
1. **Missing SECRET_KEY**: Application should fail to start with clear error
2. **Weak SECRET_KEY**: Validation should reject keys that are too simple
3. **Default SECRET_KEY**: Must detect and reject the default placeholder value
4. **Environment Loading Errors**: Handle .env file issues gracefully

### Error Response Format
```python
# Configuration errors should prevent startup
if not SECRET_KEY or SECRET_KEY == "your-secret-key-change-in-production":
    raise ValueError("SECRET_KEY environment variable must be set to a secure random value")

if len(SECRET_KEY) < 32:
    raise ValueError("SECRET_KEY must be at least 32 characters long")
```

## Testing Strategy

### Unit Tests
```python
def test_config_with_valid_secret_key():
    # Test configuration loads with proper SECRET_KEY
    pass

def test_config_rejects_default_secret_key():
    # Test that default key is rejected
    pass

def test_config_rejects_weak_secret_key():
    # Test that short/weak keys are rejected
    pass

def test_jwt_token_generation_with_new_key():
    # Test JWT generation works with secure key
    pass
```

### Integration Tests
- Test JWT token creation and validation flow
- Test application startup with various key configurations
- Test error responses for authentication failures

## Definition of Done

- [ ] No hardcoded secrets in any configuration files
- [ ] Environment variable validation implemented and tested
- [ ] Secure key generation script/documentation provided
- [ ] All JWT functionality works with new key management
- [ ] Comprehensive error handling for all key-related scenarios
- [ ] Security review passed - no token forgery possible
- [ ] Documentation updated for deployment procedures
- [ ] All tests pass with 100% coverage for new validation code

## Implementation Log

### [Date] - Initial Analysis
- Current SECRET_KEY is hardcoded in config.py line 16
- Used for JWT signing in auth.py line 35
- No validation or environment variable handling

### [Date] - Implementation
- [To be filled during implementation]

### [Date] - Testing
- [To be filled during testing]

### [Date] - Code Review
- [To be filled during review]

## Related Issues
- CRIT-002: JWT token validation (depends on secure key)
- CRIT-003: Database credentials (similar env var pattern)
- HIGH-015: Audit logging (may need to log key rotation events)