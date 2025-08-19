from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import uvicorn
import os
import sys
import asyncio
from dotenv import load_dotenv

from app.core.config import settings
from app.api.v1.api import api_router
from app.core.database import engine, Base, get_db
from app.core.websocket_manager import websocket_manager
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

# Background jobs are imported only when needed (RQ-based)

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
# Temporarily disabled for debugging
# if settings.ENABLE_SECURITY_HEADERS:
#     app.add_middleware(
#         SecurityHeadersMiddleware,
#         enforce_https=settings.ENFORCE_HTTPS,
#         hsts_max_age=settings.HSTS_MAX_AGE,
#         hsts_include_subdomains=settings.HSTS_INCLUDE_SUBDOMAINS,
#         hsts_preload=settings.HSTS_PRELOAD,
#         csp_policy=settings.CUSTOM_CSP_POLICY,
#         allowed_frame_origins=settings.ALLOWED_FRAME_ORIGINS,
#         referrer_policy=settings.REFERRER_POLICY,
#         enable_security_logging=settings.ENABLE_SECURITY_LOGGING
#     )

# Request/Response logging middleware (second to capture all requests after security)
# Temporarily disabled for debugging
# if settings.ENABLE_REQUEST_LOGGING:
#     app.add_middleware(
#         RequestResponseLoggingMiddleware,
#         log_requests=settings.ENABLE_REQUEST_LOGGING,
#         log_responses=settings.ENABLE_RESPONSE_LOGGING,
#         log_request_body=settings.LOG_REQUEST_BODIES,
#         log_response_body=settings.LOG_RESPONSE_BODIES,
#         mask_sensitive_data=settings.MASK_SENSITIVE_DATA,
#         max_body_size=settings.MAX_LOG_BODY_SIZE,
#         excluded_paths=set(settings.EXCLUDED_LOG_PATHS),
#         excluded_user_agents=set(settings.EXCLUDED_USER_AGENTS)
#     )

# Rate limiting middleware (second layer of protection)
# Temporarily disabled for development
# app.add_middleware(
#     RateLimitMiddleware,
#     enable_rate_limiting=settings.ENABLE_RATE_LIMITING
# )

# Validation middleware (second to validate all requests)
# Temporarily disabled for development
# app.add_middleware(
#     ValidationMiddleware,
#     enable_request_validation=True,
#     enable_response_validation=True,
#     enable_sql_injection_check=True,
#     enable_xss_protection=True,
#     log_validation_errors=True
# )

# CSRF protection middleware (must be before CORS for proper security)
# Temporarily disabled for development
# app.add_middleware(CSRFProtectionMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"] if settings.DEBUG else settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-CSRF-Token"],  # Allow CSRF token header
)

# Setup error handlers - TEMPORARILY DISABLED
# setup_error_handlers(app)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# WebSocket endpoint for upload progress tracking
@app.websocket("/ws/upload-progress/{batch_id}")
async def websocket_upload_progress(
    websocket: WebSocket,
    batch_id: str,
    token: str = Query(..., description="JWT authentication token"),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time upload progress tracking.
    
    Clients connect with a batch_id and JWT token for authentication.
    Progress updates are sent as JSON messages with the following format:
    
    {
        "batch_id": "uuid",
        "progress": 45.5,
        "status": "processing|completed|error",
        "stage": "validation|scanning|parsing|database|categorization",
        "message": "Processing transactions...",
        "details": {
            "processed": 150,
            "total": 500,
            "errors": 2
        },
        "timestamp": "2024-01-01T12:00:00Z"
    }
    """
    connection_successful = await websocket_manager.connect(
        websocket=websocket,
        batch_id=batch_id,
        token=token,
        db=db
    )
    
    if not connection_successful:
        return
    
    # Find connection ID for this websocket
    connection_id = None
    for conn_id, conn in websocket_manager.connections.items():
        if conn.websocket == websocket:
            connection_id = conn_id
            break
    
    if not connection_id:
        return
    
    try:
        # Keep connection alive and handle messages
        while True:
            # Wait for client messages (ping/pong for keepalive)
            try:
                data = await websocket.receive_text()
                # Handle client messages if needed (e.g., batch subscription changes)
                # For now, just acknowledge
                if data == "ping":
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                break
            except Exception as e:
                app_logger.warning(f"WebSocket message error: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        app_logger.error(f"WebSocket connection error: {e}")
    finally:
        # Clean up connection
        await websocket_manager.disconnect(connection_id)

# WebSocket status endpoint
@app.get("/api/v1/websocket/status")
async def websocket_status():
    """Get WebSocket manager status and statistics."""
    return {
        "websocket_enabled": True,
        "manager_stats": websocket_manager.get_connection_stats(),
        "endpoints": {
            "upload_progress": "/ws/upload-progress/{batch_id}?token={jwt_token}"
        }
    }

# Application startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize all components on startup."""
    app_logger.info("Starting FinGood application...")
    
    try:
        # Initialize WebSocket manager
        await websocket_manager.start()
        app_logger.info("WebSocket manager initialized successfully")
        
        # Initialize background job manager if enabled
        if settings.ENABLE_BACKGROUND_JOBS:
            try:
                from app.core.background_jobs import job_manager
                app_logger.info("Background job manager initialized successfully")
                app_logger.info(f"Job queue configuration: timeout={settings.JOB_TIMEOUT_MINUTES}min, "
                               f"retries={settings.MAX_JOB_RETRIES}, "
                               f"concurrent_per_user={settings.MAX_CONCURRENT_JOBS_PER_USER}")
            except Exception as e:
                app_logger.error(f"Background job manager initialization failed: {e}")
                print(f"⚠️  Warning: Background job manager failed to initialize: {e}")
                print("   Background job processing will not be available")
        else:
            app_logger.info("Background job processing is disabled by configuration")
        
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
        
        # Background jobs are already initialized via RQ job_manager import above
        app_logger.info("Background job system (RQ) is ready")
        
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
        # Stop WebSocket manager
        await websocket_manager.stop()
        app_logger.info("WebSocket manager stopped")
    except Exception as e:
        app_logger.warning(f"Warning during WebSocket manager shutdown: {e}")
    
    try:
        # Clean up background job manager if enabled
        if settings.ENABLE_BACKGROUND_JOBS:
            # Background job manager doesn't need explicit cleanup
            # Redis connections are handled by connection pooling
            app_logger.info("Background job manager cleanup completed")
    except Exception as e:
        app_logger.warning(f"Warning during background job manager shutdown: {e}")
    
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
        
        # RQ background jobs cleanup is handled automatically via Redis connections
        if settings.ENABLE_BACKGROUND_JOBS:
            app_logger.info("Background job system (RQ) cleanup completed")
        
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
    import sys
    port = 8001 if len(sys.argv) > 1 and sys.argv[1] == "--port" else 8000
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
