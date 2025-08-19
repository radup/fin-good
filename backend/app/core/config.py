from pydantic_settings import BaseSettings
from typing import List, Optional
import os
import re
import secrets
import sys
import urllib.parse
from pydantic import field_validator, ConfigDict

class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "FinGood"
    DEBUG: bool = True
    VERSION: str = "1.0.0"
    
    # Database - Environment variables are required for production security
    DATABASE_URL: Optional[str] = None
    REDIS_URL: Optional[str] = None
    
    # Security - Environment variables are required for production security
    SECRET_KEY: Optional[str] = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Cookie Security Settings
    COOKIE_NAME: str = "fingood_auth"
    COOKIE_SECURE: bool = True  # Set to False for localhost development
    COOKIE_HTTPONLY: bool = True
    COOKIE_SAMESITE: str = "strict"
    COOKIE_DOMAIN: Optional[str] = None  # Set to your domain in production
    
    # CSRF Protection
    CSRF_SECRET_KEY: Optional[str] = None
    CSRF_TOKEN_EXPIRE_MINUTES: int = 60
    
    # CORS
    ALLOWED_HOSTS: List[str] = [
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:3001", 
        "http://127.0.0.1:3001"
    ]
    
    # Security Headers and HTTPS Enforcement
    ENFORCE_HTTPS: bool = True  # Set to False for localhost development
    HSTS_MAX_AGE: int = 31536000  # 1 year in seconds
    HSTS_INCLUDE_SUBDOMAINS: bool = True
    HSTS_PRELOAD: bool = True
    ENABLE_SECURITY_HEADERS: bool = True
    
    # Content Security Policy
    CUSTOM_CSP_POLICY: Optional[str] = None  # Use default financial CSP if None
    
    # Frame Options
    ALLOWED_FRAME_ORIGINS: List[str] = []  # Empty list means DENY all framing
    
    # Referrer Policy
    REFERRER_POLICY: str = "strict-origin-when-cross-origin"
    
    # Security Logging
    ENABLE_SECURITY_LOGGING: bool = True
    
    # File upload with enhanced security controls
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB global limit
    ALLOWED_EXTENSIONS: List[str] = [".csv", ".xlsx", ".xls"]
    
    # File size limits by type (bytes)
    MAX_CSV_SIZE: int = 50 * 1024 * 1024   # 50MB for CSV files
    MAX_EXCEL_SIZE: int = 25 * 1024 * 1024  # 25MB for Excel files
    
    # File validation settings
    MAX_COLUMNS_PER_CSV: int = 100
    MAX_ROWS_PER_CSV: int = 1000000  # 1 million rows
    
    # Security scanning settings
    ENABLE_MALWARE_SCANNING: bool = True
    QUARANTINE_SUSPICIOUS_FILES: bool = True
    VIRUSTOTAL_API_KEY: Optional[str] = None
    
    # Rate limiting for file uploads
    MAX_UPLOADS_PER_HOUR: int = 50
    MAX_UPLOADS_PER_DAY: int = 200
    
    # Comprehensive Rate Limiting Settings
    ENABLE_RATE_LIMITING: bool = True
    
    # Redis-based rate limiting
    RATE_LIMIT_REDIS_KEY_PREFIX: str = "fingood:rate_limit"
    
    # Global rate limiting defaults (can be overridden per user tier)
    DEFAULT_REQUESTS_PER_MINUTE: int = 60
    DEFAULT_REQUESTS_PER_HOUR: int = 1000
    DEFAULT_REQUESTS_PER_DAY: int = 10000
    
    # Authentication rate limiting (stricter limits for security)
    AUTH_REQUESTS_PER_MINUTE: int = 5
    AUTH_REQUESTS_PER_HOUR: int = 20
    AUTH_REQUESTS_PER_DAY: int = 100
    AUTH_BLOCK_DURATION_MINUTES: int = 30
    
    # Brute force protection
    BRUTE_FORCE_ATTEMPTS_PER_MINUTE: int = 3
    BRUTE_FORCE_ATTEMPTS_PER_HOUR: int = 10
    BRUTE_FORCE_BLOCK_DURATION_MINUTES: int = 60
    
    # DDoS protection
    DDOS_REQUESTS_PER_MINUTE: int = 100
    DDOS_REQUESTS_PER_HOUR: int = 1000
    DDOS_BLOCK_DURATION_MINUTES: int = 120
    
    # Upload rate limiting (file operations)
    UPLOAD_REQUESTS_PER_MINUTE: int = 2
    UPLOAD_REQUESTS_PER_HOUR: int = 10
    UPLOAD_REQUESTS_PER_DAY: int = 50
    
    # Analytics rate limiting
    ANALYTICS_REQUESTS_PER_MINUTE: int = 10
    ANALYTICS_REQUESTS_PER_HOUR: int = 100
    ANALYTICS_REQUESTS_PER_DAY: int = 500
    
    # Trusted IP ranges (no rate limiting applied)
    TRUSTED_IP_RANGES: List[str] = [
        "127.0.0.0/8",    # Localhost
        "10.0.0.0/8",     # Private network
        "172.16.0.0/12",  # Private network
        "192.168.0.0/16"  # Private network
    ]
    
    # Rate limit monitoring and alerting
    ENABLE_RATE_LIMIT_MONITORING: bool = True
    RATE_LIMIT_ALERT_THRESHOLD_MULTIPLIER: float = 1.5
    RATE_LIMIT_VIOLATION_ALERT_COUNT: int = 3
    
    # Security block settings
    ENABLE_AUTOMATIC_SECURITY_BLOCKS: bool = True
    MAX_SECURITY_BLOCK_DURATION_HOURS: int = 24
    
    # WebSocket Configuration
    ENABLE_WEBSOCKETS: bool = True
    MAX_WEBSOCKET_CONNECTIONS_PER_USER: int = 5
    WEBSOCKET_HEARTBEAT_INTERVAL: int = 30  # seconds
    WEBSOCKET_CONNECTION_TIMEOUT: int = 300  # seconds (5 minutes)
    WEBSOCKET_MESSAGE_RATE_LIMIT: int = 10  # messages per second
    WEBSOCKET_MAX_MESSAGE_SIZE: int = 1024  # bytes
    
    # Background Jobs Configuration
    ENABLE_BACKGROUND_JOBS: bool = True
    CELERY_WORKER_CONCURRENCY: int = 2
    CELERY_TASK_TIME_LIMIT: int = 1800  # 30 minutes
    CELERY_TASK_SOFT_TIME_LIMIT: int = 1500  # 25 minutes
    CELERY_MAX_TASKS_PER_CHILD: int = 1000
    CELERY_RESULT_EXPIRES: int = 3600  # 1 hour
    
    # AI/ML settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"
    
    # Password Reset Security Settings
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1
    MAX_PASSWORD_RESET_ATTEMPTS_PER_HOUR: int = 3
    MAX_PASSWORD_RESET_ATTEMPTS_PER_DAY: int = 10
    
    # Email Configuration
    FRONTEND_URL: str = "http://localhost:3000"  # Frontend URL for reset links
    
    # External APIs
    QUICKBOOKS_CLIENT_ID: Optional[str] = None
    QUICKBOOKS_CLIENT_SECRET: Optional[str] = None
    XERO_CLIENT_ID: Optional[str] = None
    XERO_CLIENT_SECRET: Optional[str] = None
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    ENABLE_CONSOLE_LOGGING: bool = True
    ENABLE_FILE_LOGGING: bool = True
    ENABLE_JSON_LOGGING: bool = True
    ENABLE_LOG_ROTATION: bool = True
    MAX_LOG_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    LOG_BACKUP_COUNT: int = 10
    
    # Advanced logging features
    ENABLE_SYSTEM_MONITORING: bool = True
    SYSTEM_METRICS_INTERVAL: int = 60  # seconds
    ENABLE_PERFORMANCE_MONITORING: bool = True
    ENABLE_REQUEST_LOGGING: bool = True
    ENABLE_RESPONSE_LOGGING: bool = True
    LOG_REQUEST_BODIES: bool = False  # Security risk if enabled
    LOG_RESPONSE_BODIES: bool = False  # Security risk if enabled
    MASK_SENSITIVE_DATA: bool = True
    MAX_LOG_BODY_SIZE: int = 1024 * 1024  # 1MB
    
    # Compliance and audit logging
    ENABLE_COMPLIANCE_LOGGING: bool = True
    ENABLE_TRANSACTION_AUDIT: bool = True
    COMPLIANCE_SECRET_KEY: Optional[str] = None
    ENABLE_DIGITAL_SIGNATURES: bool = False
    AUDIT_RETENTION_YEARS: int = 7
    
    # Remote logging and SIEM integration
    ENABLE_SYSLOG: bool = False
    SYSLOG_ADDRESS: Optional[str] = None
    ENABLE_REMOTE_LOGGING: bool = False
    REMOTE_LOG_URL: Optional[str] = None
    
    # Log filtering and exclusions
    EXCLUDED_LOG_PATHS: List[str] = [
        "/health", "/metrics", "/favicon.ico", "/robots.txt", "/ping", "/status"
    ]
    EXCLUDED_USER_AGENTS: List[str] = [
        "HealthCheck", "Monitoring", "Pingdom", "StatusCake", "UptimeRobot"
    ]
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True
    )
    
    @field_validator('SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, v):
        """Validate SECRET_KEY meets security requirements for financial applications."""
        if not v:
            raise ValueError(
                "SECRET_KEY environment variable is required. "
                "Generate a secure key using: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        
        # Reject dangerous default values
        dangerous_defaults = [
            "your-secret-key-change-in-production",
            "secret",
            "secretkey",
            "password",
            "123456",
            "changeme",
            "default",
            "test",
            "dev",
            "development"
        ]
        
        if v.lower() in [d.lower() for d in dangerous_defaults]:
            raise ValueError(
                "SECRET_KEY cannot use default or common values. "
                "Generate a secure key using: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        
        # Validate minimum length for cryptographic security
        if len(v) < 32:
            raise ValueError(
                f"SECRET_KEY must be at least 32 characters long for security. "
                f"Current length: {len(v)}. "
                "Generate a secure key using: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        
        # Check for sufficient entropy (basic heuristic)
        unique_chars = len(set(v))
        if unique_chars < 8:
            raise ValueError(
                "SECRET_KEY appears to have insufficient entropy. "
                "Generate a secure key using: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        
        return v
    
    @field_validator('CSRF_SECRET_KEY')
    @classmethod
    def validate_csrf_secret_key(cls, v):
        """Validate CSRF_SECRET_KEY meets security requirements."""
        if not v:
            raise ValueError(
                "CSRF_SECRET_KEY environment variable is required. "
                "Generate a secure key using: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        
        if len(v) < 32:
            raise ValueError(
                f"CSRF_SECRET_KEY must be at least 32 characters long for security. "
                f"Current length: {len(v)}. "
                "Generate a secure key using: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        
        return v
    
    @field_validator('COMPLIANCE_SECRET_KEY')
    @classmethod
    def validate_compliance_secret_key(cls, v):
        """Validate COMPLIANCE_SECRET_KEY meets security requirements for audit integrity."""
        if not v:
            raise ValueError(
                "COMPLIANCE_SECRET_KEY environment variable is required for audit log integrity. "
                "Generate a secure key using: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        
        if len(v) < 32:
            raise ValueError(
                f"COMPLIANCE_SECRET_KEY must be at least 32 characters long for audit integrity. "
                f"Current length: {len(v)}. "
                "Generate a secure key using: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        
        # Ensure it's different from other keys for security isolation
        if hasattr(cls, 'SECRET_KEY') and v == cls.SECRET_KEY:
            raise ValueError(
                "COMPLIANCE_SECRET_KEY must be different from SECRET_KEY for security isolation"
            )
        
        return v
    
    # Database and Redis validators are defined below with comprehensive security checks
    
    @field_validator('DATABASE_URL')
    @classmethod
    def validate_database_url(cls, v):
        """Validate DATABASE_URL meets security requirements for financial applications."""
        if not v:
            raise ValueError(
                "DATABASE_URL environment variable is required. "
                "Example: postgresql://username:password@hostname:port/database_name"
            )
        
        # Reject dangerous default values
        dangerous_defaults = [
            "postgresql://postgres:password@localhost:5432/fingood",
            "postgresql://user:password@localhost:5432/db",
            "postgresql://postgres:123456@localhost:5432/fingood",
            "postgresql://postgres:admin@localhost:5432/fingood",
            "postgresql://admin:admin@localhost:5432/fingood",
            "postgresql://root:root@localhost:5432/fingood",
            "postgresql://test:test@localhost:5432/test",
            "sqlite:///./test.db",
            "postgresql://postgres@localhost:5432/fingood"
        ]
        
        if v.lower() in [d.lower() for d in dangerous_defaults]:
            raise ValueError(
                "DATABASE_URL cannot use default or common values. "
                "Use secure credentials with strong passwords."
            )
        
        # Validate URL format
        try:
            parsed = urllib.parse.urlparse(v)
        except Exception:
            raise ValueError("DATABASE_URL must be a valid URL format")
        
        # Validate supported database schemes
        if parsed.scheme not in ['postgresql', 'postgresql+psycopg2', 'sqlite']:
            raise ValueError(
                f"Unsupported database scheme: {parsed.scheme}. "
                "Supported schemes: postgresql, postgresql+psycopg2, sqlite"
            )
        
        # Security checks for production databases
        if parsed.scheme.startswith('postgresql'):
            # Validate hostname/host
            if not parsed.hostname:
                raise ValueError("DATABASE_URL must include a hostname")
            
            # Check for secure authentication
            if not parsed.username:
                raise ValueError("DATABASE_URL must include username for authentication")
            
            # Password strength validation (skip for development localhost)
            if parsed.hostname not in ['localhost', '127.0.0.1'] and parsed.password:
                if len(parsed.password) < 12:
                    raise ValueError(
                        "Database password must be at least 12 characters for production use"
                    )
                
                # Check for weak passwords
                weak_passwords = [
                    'password', 'admin', 'root', '123456', 'postgres', 
                    'fingood', 'test', 'dev', 'development', 'production'
                ]
                if parsed.password.lower() in weak_passwords:
                    raise ValueError(
                        "Database password cannot use common/weak values. "
                        "Use a strong, unique password."
                    )
            
            # Validate database name
            if not parsed.path or parsed.path == '/':
                raise ValueError("DATABASE_URL must include a database name")
            
            # Remove leading slash from path to get database name
            db_name = parsed.path.lstrip('/')
            if not db_name:
                raise ValueError("DATABASE_URL must include a valid database name")
            
            # Check for SQL injection patterns in database name
            if re.search(r'[;\'\"\\]', db_name):
                raise ValueError("Database name contains potentially dangerous characters")
        
        return v

    @field_validator('REDIS_URL')
    @classmethod
    def validate_redis_url(cls, v):
        """Validate REDIS_URL meets security requirements for financial applications."""
        if not v:
            raise ValueError(
                "REDIS_URL environment variable is required. "
                "Example: redis://username:password@hostname:port/db_number"
            )
        
        # Reject dangerous default values
        dangerous_defaults = [
            "redis://localhost:6379",
            "redis://127.0.0.1:6379",
            "redis://:password@localhost:6379",
            "redis://admin:admin@localhost:6379",
            "redis://root:root@localhost:6379",
            "redis://test:test@localhost:6379",
            "redis://:admin@localhost:6379",
            "redis://:root@localhost:6379",
            "redis://:test@localhost:6379"
        ]
        
        if v.lower() in [d.lower() for d in dangerous_defaults]:
            raise ValueError(
                "REDIS_URL cannot use default or common values. "
                "Use secure credentials and configuration."
            )
        
        # Validate URL format
        try:
            parsed = urllib.parse.urlparse(v)
        except Exception:
            raise ValueError("REDIS_URL must be a valid URL format")
        
        # Validate Redis scheme
        if parsed.scheme not in ['redis', 'rediss']:
            raise ValueError(
                f"Unsupported Redis scheme: {parsed.scheme}. "
                "Supported schemes: redis (unencrypted), rediss (TLS encrypted)"
            )
        
        # Validate hostname
        if not parsed.hostname:
            raise ValueError("REDIS_URL must include a hostname")
        
        # Security checks for production Redis
        if parsed.hostname not in ['localhost', '127.0.0.1']:
            # Recommend TLS for production
            if parsed.scheme != 'rediss':
                # Warning for unencrypted Redis in production
                pass  # Allow but log warning
            
            # Validate authentication for production
            if parsed.password:
                if len(parsed.password) < 12:
                    raise ValueError(
                        "Redis password must be at least 12 characters for production use"
                    )
                
                # Check for weak passwords
                weak_passwords = [
                    'password', 'admin', 'root', '123456', 'redis', 
                    'fingood', 'test', 'dev', 'development', 'production'
                ]
                if parsed.password.lower() in weak_passwords:
                    raise ValueError(
                        "Redis password cannot use common/weak values. "
                        "Use a strong, unique password."
                    )
        
        return v

# Initialize settings with comprehensive error handling
# Skip initialization during testing
if "pytest" not in sys.modules:
    try:
        settings = Settings()
    except Exception as e:
        print(f"\n❌ CRITICAL CONFIGURATION ERROR: {str(e)}\n", file=sys.stderr)
        print("🔐 For development, create a .env file with:", file=sys.stderr)
        print(f"SECRET_KEY={secrets.token_urlsafe(32)}", file=sys.stderr)
        print("DATABASE_URL=postgresql://username:password@localhost:5432/fingood", file=sys.stderr)
        print("REDIS_URL=redis://:secure_dev_password_2024@localhost:6379/0", file=sys.stderr)
        print("", file=sys.stderr)
        print("🚀 For production, use securely generated environment variables.", file=sys.stderr)
        print("📖 See .env.example for complete configuration examples.\n", file=sys.stderr)
        sys.exit(1)
else:
    # For testing, create a placeholder that will be overridden
    settings = None

# Create upload directory if it doesn't exist (skip during testing)
if settings is not None:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Security validation on startup
if settings is not None and ("pytest" not in sys.modules):
    # Log successful security configuration (without exposing sensitive data)
    print(f"✅ Security configuration validated: SECRET_KEY length={len(settings.SECRET_KEY)} characters")
    print(f"🔒 JWT Algorithm: {settings.ALGORITHM}")
    print(f"⏰ Token Expiry: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
    
    # Log database configuration status (without exposing credentials)
    db_parsed = urllib.parse.urlparse(settings.DATABASE_URL)
    redis_parsed = urllib.parse.urlparse(settings.REDIS_URL)
    print(f"🗄️  Database: {db_parsed.scheme}://{db_parsed.hostname}:{db_parsed.port}/{db_parsed.path.lstrip('/')}")
    print(f"📊 Redis: {redis_parsed.scheme}://{redis_parsed.hostname}:{redis_parsed.port}")
    
    # Security warnings for production
    if not settings.DEBUG:
        if db_parsed.hostname in ['localhost', '127.0.0.1']:
            print("⚠️  WARNING: Using localhost database in production mode")
        if redis_parsed.hostname in ['localhost', '127.0.0.1']:
            print("⚠️  WARNING: Using localhost Redis in production mode")
        if redis_parsed.scheme == 'redis' and redis_parsed.hostname not in ['localhost', '127.0.0.1']:
            print("⚠️  WARNING: Using unencrypted Redis connection for production")
