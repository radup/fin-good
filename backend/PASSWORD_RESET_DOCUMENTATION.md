# Password Reset System Documentation

## Overview

The FinGood password reset system provides a secure, enterprise-grade solution for password recovery with comprehensive security features tailored for financial applications.

## Security Features

### 🔐 Core Security
- **Cryptographically Secure Tokens**: 256-bit URL-safe tokens using `secrets.token_urlsafe()`
- **Token Hashing**: SHA-256 hashed tokens stored in database (never store plain tokens)
- **Time-Limited Tokens**: 1-hour expiration with configurable timeout
- **Single-Use Tokens**: Tokens invalidated after successful password reset
- **Rate Limiting**: 3 attempts per hour, 10 per day per email address

### 🛡️ Anti-Enumeration Protection
- **Generic Response Messages**: Same success message for valid and invalid emails
- **Security Logging**: Comprehensive audit trail for all reset attempts
- **IP Tracking**: Track and log IP addresses for security monitoring

### ⚡ Performance & Scalability
- **Database Indexes**: Optimized queries for token lookup and cleanup
- **Automatic Cleanup**: Expired tokens automatically removed
- **Redis Integration**: Leverages existing Redis infrastructure for rate limiting

## API Endpoints

### 1. Request Password Reset
```http
POST /api/v1/auth/forgot-password
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Response**:
```json
{
  "message": "If an account with this email exists, you will receive a password reset link shortly.",
  "success": true
}
```

**Security Features**:
- Rate limiting (3/hour, 10/day)
- Email enumeration protection
- Audit logging
- Token generation and email dispatch

### 2. Verify Reset Token
```http
GET /api/v1/auth/verify-reset-token?token=<reset_token>
```

**Response (Valid)**:
```json
{
  "message": "Token is valid",
  "success": true
}
```

**Response (Invalid/Expired)**:
```json
{
  "message": "Invalid or expired token",
  "success": false
}
```

### 3. Reset Password
```http
POST /api/v1/auth/reset-password
Content-Type: application/json

{
  "token": "<reset_token>",
  "new_password": "newSecurePassword123"
}
```

**Response (Success)**:
```json
{
  "message": "Password reset successfully",
  "success": true
}
```

**Response (Error)**:
```json
{
  "message": "Invalid token",
  "success": false
}
```

## Database Schema

### password_reset_tokens Table
```sql
CREATE TABLE password_reset_tokens (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    used_at TIMESTAMP WITH TIME ZONE,
    is_used BOOLEAN DEFAULT FALSE NOT NULL,
    created_ip VARCHAR(45),
    used_ip VARCHAR(45),
    user_agent TEXT
);

-- Optimized indexes
CREATE INDEX idx_reset_tokens_lookup ON password_reset_tokens (token_hash, expires_at, is_used);
CREATE INDEX idx_reset_tokens_cleanup ON password_reset_tokens (expires_at);
CREATE INDEX idx_reset_tokens_user_active ON password_reset_tokens (user_id, is_used, expires_at);
```

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Password Reset Settings
PASSWORD_RESET_TOKEN_EXPIRE_HOURS=1
MAX_PASSWORD_RESET_ATTEMPTS_PER_HOUR=3
MAX_PASSWORD_RESET_ATTEMPTS_PER_DAY=10
FRONTEND_URL=http://localhost:3000

# Email Configuration (required for password reset)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@domain.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
FROM_EMAIL=noreply@fingood.com
FROM_NAME=FinGood Security
```

### Application Settings

The system uses the existing `app.core.config.Settings` class with these additions:

```python
# Password Reset Security Settings
PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1
MAX_PASSWORD_RESET_ATTEMPTS_PER_HOUR: int = 3
MAX_PASSWORD_RESET_ATTEMPTS_PER_DAY: int = 10

# Email Configuration
FRONTEND_URL: str = "http://localhost:3000"
```

## Email Templates

The system includes responsive HTML and text email templates:

- **HTML Template**: `app/templates/emails/password_reset.html`
- **Text Template**: `app/templates/emails/password_reset.txt`

Templates support Jinja2 templating with variables:
- `user_name`: User's full name
- `user_email`: User's email address
- `reset_link`: Full password reset URL
- `expires_at`: Token expiration date/time
- `company_name`: Application name
- `support_email`: Support contact email

## Rate Limiting Integration

The password reset endpoints are integrated with the existing rate limiting middleware:

```python
# Sensitive endpoints with stricter protection
self.sensitive_endpoints = {
    r"/api/v1/auth/forgot-password",
    r"/api/v1/auth/reset-password",
    r"/api/v1/auth/verify-reset-token",
    # ... other auth endpoints
}
```

## Maintenance & Operations

### Token Cleanup

Run the cleanup script regularly to remove expired tokens:

```bash
# Dry run to see what would be cleaned
python scripts/cleanup_expired_tokens.py --dry-run --verbose

# Actual cleanup
python scripts/cleanup_expired_tokens.py --verbose

# Show statistics
python scripts/cleanup_expired_tokens.py --stats
```

**Recommended**: Set up a daily cron job:
```bash
# Add to crontab: daily cleanup at 2 AM
0 2 * * * cd /path/to/fingood/backend && python scripts/cleanup_expired_tokens.py >> logs/token_cleanup.log 2>&1
```

### Monitoring & Alerts

Monitor these metrics:

1. **Reset Request Rate**: Unusual spikes may indicate attacks
2. **Token Usage Rate**: Low usage rates may indicate email delivery issues
3. **Expired Token Count**: High counts may indicate cleanup issues
4. **Failed Verification Attempts**: May indicate brute force attempts

### Security Logging

All password reset operations are logged with:
- Request/response details
- IP addresses and user agents
- Rate limiting violations
- Token verification attempts
- Password reset completions

Check logs in:
- `logs/audit/security_audit.jsonl` - Security events
- Application logs - General operations

## Integration with Frontend

### Reset Flow

1. **Request Reset**: POST to `/api/v1/auth/forgot-password`
2. **User Clicks Link**: Email contains link to your frontend reset page
3. **Verify Token**: GET `/api/v1/auth/verify-reset-token?token=...`
4. **Show Reset Form**: If token valid, show password reset form
5. **Submit Reset**: POST to `/api/v1/auth/reset-password`

### Frontend Reset Page

Your frontend should handle the reset page (e.g., `/reset-password?token=...`):

```javascript
// Example React component
const ResetPasswordPage = () => {
  const [token] = useSearchParams();
  const [isValidToken, setIsValidToken] = useState(false);
  
  useEffect(() => {
    // Verify token on page load
    fetch(`/api/v1/auth/verify-reset-token?token=${token}`)
      .then(res => res.json())
      .then(data => setIsValidToken(data.success));
  }, [token]);
  
  if (!isValidToken) {
    return <div>Invalid or expired reset link</div>;
  }
  
  return <PasswordResetForm token={token} />;
};
```

## Testing

Run the password reset tests:

```bash
# Run password reset specific tests
pytest tests/unit/api/test_password_reset_endpoints.py -v

# Run all authentication tests
pytest tests/unit/api/test_auth_endpoints.py -v

# Run security tests
pytest tests/security/ -v
```

## Security Best Practices

### For Production

1. **HTTPS Only**: Always use HTTPS in production
2. **Strong SMTP Security**: Use TLS-encrypted SMTP connections
3. **Monitor Reset Patterns**: Watch for unusual reset request patterns
4. **Rate Limit Monitoring**: Alert on rate limit violations
5. **Token Entropy**: Regularly verify token randomness
6. **Database Security**: Encrypt database at rest
7. **Email Security**: Use SPF, DKIM, and DMARC for email authentication

### Compliance Considerations

For financial applications:
- All reset attempts are audited and logged
- Token generation uses cryptographically secure random numbers
- Tokens are properly invalidated after use
- System maintains detailed audit trails
- Rate limiting prevents abuse

## Troubleshooting

### Common Issues

1. **Email Not Received**:
   - Check SMTP configuration
   - Verify email service is running
   - Check spam/junk folders
   - Review email service logs

2. **Invalid Token Errors**:
   - Check token expiration (1 hour default)
   - Verify token wasn't already used
   - Check for URL encoding issues

3. **Rate Limiting**:
   - Tokens may be rate limited (3/hour, 10/day)
   - Check audit logs for rate limit violations
   - Consider temporary IP whitelisting for testing

4. **Database Issues**:
   - Run database migration: `alembic upgrade head`
   - Check password_reset_tokens table exists
   - Verify foreign key constraints

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('app.services.password_reset_service').setLevel(logging.DEBUG)
logging.getLogger('app.services.email_service').setLevel(logging.DEBUG)
```

## Migration Instructions

To add password reset to an existing FinGood installation:

1. **Run Migration**:
   ```bash
   cd backend
   alembic upgrade head
   ```

2. **Update Environment**:
   Add email configuration to `.env` file

3. **Test Configuration**:
   ```bash
   python -c "from app.core.config import settings; print('✅ Config OK')"
   ```

4. **Test Email Service**:
   ```bash
   python scripts/cleanup_expired_tokens.py --stats
   ```

5. **Update Frontend**:
   Add password reset pages and integrate with new endpoints

## Support

For questions or issues:
- Check logs in `logs/` directory
- Review security audit logs
- Contact: security@fingood.com
- Documentation: See API docs at `/docs`