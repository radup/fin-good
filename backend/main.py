from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import sys
import asyncio
from dotenv import load_dotenv

from app.core.config import settings
from app.api.v1.api import api_router
from app.core.database import engine, Base
from app.core.csrf_middleware import CSRFProtectionMiddleware
from app.core.validation_middleware import ValidationMiddleware
from app.core.rate_limit_middleware import RateLimitMiddleware
from app.core.security_headers_middleware import SecurityHeadersMiddleware
from app.core.error_handlers import setup_error_handlers

# Import comprehensive logging modules
from app.core.logging_config import initialize_logging, get_logger, LogCategory
from app.core.transaction_audit import initialize_transaction_audit
from app.core.performance_monitor import initialize_performance_monitor
from app.core.compliance_logger import initialize_compliance_logger
from app.core.request_logging_middleware import RequestResponseLoggingMiddleware
from app.core.security_validator import validate_security_configuration, SecurityLevel

# Load environment variables
load_dotenv()

# Validate security configuration before startup
try:
    # Determine security level based on DEBUG setting
    security_level = SecurityLevel.DEVELOPMENT if settings.DEBUG else SecurityLevel.PRODUCTION
    
    is_valid, security_report = validate_security_configuration(settings, security_level)
    
    if not is_valid:
        print("\n🚨 CRITICAL SECURITY CONFIGURATION ISSUES DETECTED:\n")
        print(security_report)
        print("\n❌ Application startup blocked due to security issues.")
        print("   Please fix the critical security issues before starting the application.\n")
        sys.exit(1)
    else:
        print("✅ Security configuration validation passed")
        if security_report.strip() != "✅ Security configuration validation passed - no issues found.":
            print("\n⚠️  Security validation warnings:")
            print(security_report)
            print()
            
except Exception as e:
    print(f"❌ Security validation failed: {str(e)}")
    print("   Application startup will continue, but security may be compromised.")
    print("   Please review security configuration manually.\n")

# Initialize comprehensive logging system
try:
    # Initialize core logging
    logging_config = initialize_logging(
        log_level=settings.LOG_LEVEL,
        log_dir=settings.LOG_DIR,
        enable_console=settings.ENABLE_CONSOLE_LOGGING,
        enable_file=settings.ENABLE_FILE_LOGGING,
        enable_rotation=settings.ENABLE_LOG_ROTATION,
        max_file_size=settings.MAX_LOG_FILE_SIZE,
        backup_count=settings.LOG_BACKUP_COUNT,
        enable_syslog=settings.ENABLE_SYSLOG,
        syslog_address=settings.SYSLOG_ADDRESS,
        enable_remote_logging=settings.ENABLE_REMOTE_LOGGING,
        remote_log_url=settings.REMOTE_LOG_URL
    )
    
    # Initialize transaction audit logging
    if settings.ENABLE_TRANSACTION_AUDIT and settings.COMPLIANCE_SECRET_KEY:
        transaction_audit = initialize_transaction_audit(
            secret_key=settings.COMPLIANCE_SECRET_KEY,
            retention_years=settings.AUDIT_RETENTION_YEARS
        )
    
    # Initialize performance monitoring
    if settings.ENABLE_PERFORMANCE_MONITORING:
        performance_monitor = initialize_performance_monitor(
            enable_system_monitoring=settings.ENABLE_SYSTEM_MONITORING
        )
    
    # Initialize compliance logging
    if settings.ENABLE_COMPLIANCE_LOGGING and settings.COMPLIANCE_SECRET_KEY:
        compliance_logger = initialize_compliance_logger(
            secret_key=settings.COMPLIANCE_SECRET_KEY,
            enable_digital_signatures=settings.ENABLE_DIGITAL_SIGNATURES
        )
    
    # Get application logger
    app_logger = get_logger('fingood.main', LogCategory.APPLICATION)
    app_logger.info("Logging system initialized successfully")
    
except Exception as e:
    print(f"❌ Failed to initialize logging system: {str(e)}")
    print("🔄 Falling back to basic logging...")
    import logging
    logging.basicConfig(level=logging.INFO)
    app_logger = logging.getLogger('fingood.main')

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FinGood API",
    description="AI-Powered Financial Intelligence Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Security middlewares (order matters!)

# Security Headers middleware (first to ensure all responses have security headers)
if settings.ENABLE_SECURITY_HEADERS:
    app.add_middleware(
        SecurityHeadersMiddleware,
        enforce_https=settings.ENFORCE_HTTPS,
        hsts_max_age=settings.HSTS_MAX_AGE,
        hsts_include_subdomains=settings.HSTS_INCLUDE_SUBDOMAINS,
        hsts_preload=settings.HSTS_PRELOAD,
        csp_policy=settings.CUSTOM_CSP_POLICY,
        allowed_frame_origins=settings.ALLOWED_FRAME_ORIGINS,
        referrer_policy=settings.REFERRER_POLICY,
        enable_security_logging=settings.ENABLE_SECURITY_LOGGING
    )

# Request/Response logging middleware (second to capture all requests after security)
if settings.ENABLE_REQUEST_LOGGING:
    app.add_middleware(
        RequestResponseLoggingMiddleware,
        log_requests=settings.ENABLE_REQUEST_LOGGING,
        log_responses=settings.ENABLE_RESPONSE_LOGGING,
        log_request_body=settings.LOG_REQUEST_BODIES,
        log_response_body=settings.LOG_RESPONSE_BODIES,
        mask_sensitive_data=settings.MASK_SENSITIVE_DATA,
        max_body_size=settings.MAX_LOG_BODY_SIZE,
        excluded_paths=set(settings.EXCLUDED_LOG_PATHS),
        excluded_user_agents=set(settings.EXCLUDED_USER_AGENTS)
    )

# Rate limiting middleware (second layer of protection)
app.add_middleware(
    RateLimitMiddleware,
    enable_rate_limiting=settings.ENABLE_RATE_LIMITING
)

# Validation middleware (second to validate all requests)
app.add_middleware(
    ValidationMiddleware,
    enable_request_validation=True,
    enable_response_validation=True,
    enable_sql_injection_check=True,
    enable_xss_protection=True,
    log_validation_errors=True
)

# CSRF protection middleware (must be before CORS for proper security)
app.add_middleware(CSRFProtectionMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-CSRF-Token"],  # Allow CSRF token header
)

# Setup error handlers
setup_error_handlers(app)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Application startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize all components on startup."""
    app_logger.info("Starting FinGood application...")
    
    try:
        # Initialize rate limiter
        from app.core.rate_limiter import get_rate_limiter
        from app.core.rate_limit_monitoring import get_rate_limit_monitor
        
        rate_limiter = await get_rate_limiter()
        app_logger.info("Rate limiter initialized successfully")
        
        # Initialize rate limit monitoring
        if settings.ENABLE_RATE_LIMIT_MONITORING:
            monitor = await get_rate_limit_monitor()
            await monitor.start_background_tasks()
            app_logger.info("Rate limit monitoring initialized successfully")
        
    except Exception as e:
        app_logger.error(f"Rate limiting initialization failed: {e}")
        print(f"⚠️  Warning: Rate limiting initialization failed: {e}")
        print("   Application will continue without rate limiting")
    
    try:
        # Start performance monitoring if enabled
        if settings.ENABLE_PERFORMANCE_MONITORING:
            from app.core.performance_monitor import get_performance_monitor
            monitor = get_performance_monitor()
            if monitor:
                await monitor.start_monitoring()
                app_logger.info("Performance monitoring started successfully")
        
        # Log successful startup
        app_logger.info("FinGood application startup completed successfully", extra={
            'startup_complete': True,
            'logging_enabled': True,
            'performance_monitoring': settings.ENABLE_PERFORMANCE_MONITORING,
            'compliance_logging': settings.ENABLE_COMPLIANCE_LOGGING,
            'transaction_audit': settings.ENABLE_TRANSACTION_AUDIT
        })
        
    except Exception as e:
        app_logger.error(f"Error during application startup: {e}")
        print(f"⚠️  Warning: Some components failed to initialize: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up all components on shutdown."""
    app_logger.info("Shutting down FinGood application...")
    
    try:
        # Clean up rate limiter
        from app.core.rate_limiter import rate_limiter
        await rate_limiter.close()
        app_logger.info("Rate limiter connections closed")
    except Exception as e:
        app_logger.warning(f"Warning during rate limiter shutdown: {e}")
    
    try:
        # Stop performance monitoring
        if settings.ENABLE_PERFORMANCE_MONITORING:
            from app.core.performance_monitor import get_performance_monitor
            monitor = get_performance_monitor()
            if monitor:
                await monitor.stop_monitoring()
                app_logger.info("Performance monitoring stopped")
        
        # Log successful shutdown
        app_logger.info("FinGood application shutdown completed successfully")
        
    except Exception as e:
        app_logger.error(f"Error during application shutdown: {e}")
        print(f"Warning during shutdown: {e}")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "FinGood API is running"}

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to FinGood API",
        "docs": "/docs",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
