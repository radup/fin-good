from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import jwt
import uuid
from passlib.context import CryptContext

from app.core.database import get_db
from app.core.config import settings
from app.core.cookie_auth import get_current_user_from_cookie, set_auth_cookie, clear_auth_cookie
from app.core.error_sanitizer import error_sanitizer, create_secure_error_response
from app.schemas.error import ErrorCategory, ErrorSeverity
from app.core.exceptions import AuthenticationException, SystemException
from app.core.csrf import generate_csrf_token, set_csrf_cookie, clear_csrf_cookie, verify_csrf_protection
from app.core.security import jwt_manager
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, AuthResponse, PasswordResetRequest, PasswordResetVerify, PasswordResetConfirm, PasswordResetResponse

router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Note: OAuth2PasswordBearer replaced with secure cookie authentication

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Token creation now handled by JWT manager in security.py

# User authentication now handled by cookie-based authentication

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        company_name=user_data.company_name,
        business_type=user_data.business_type
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.post("/login", response_model=AuthResponse)
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """Secure login with HttpOnly cookies and CSRF protection."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Cookie"},
        )
    
    # Check if user account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive - please contact support"
        )
    
    try:
        # Create JWT token using secure JWT manager
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = jwt_manager.create_access_token(
            data={"sub": user.email}, 
            expires_delta=access_token_expires
        )
        
        # Set secure authentication cookie
        set_auth_cookie(response, access_token, user.id)
        
        # Generate and set CSRF token
        csrf_token = generate_csrf_token(user.id)
        set_csrf_cookie(response, csrf_token)
        
        return {
            "message": "Login successful",
            "user": UserResponse.model_validate(user),
            "csrf_token": csrf_token
        }
        
    except Exception as e:
        # Clear any cookies that might have been set
        if 'user' in locals():
            clear_auth_cookie(response, user.id)
        clear_csrf_cookie(response)
        
        # Create sanitized error response
        error_detail = create_secure_error_response(
            exception=e,
            error_code="LOGIN_SERVER_ERROR",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4()),
            user_message="Login failed due to a server error. Please try again.",
            suggested_action="If the problem persists, please contact support."
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail.user_message
        )


# Password Reset Endpoints

def _get_client_ip(request: Request) -> str:
    """Extract client IP address with proxy support."""
    forwarded_ips = request.headers.get("X-Forwarded-For")
    if forwarded_ips:
        return forwarded_ips.split(",")[0].strip()
    return (
        request.headers.get("X-Real-IP") or
        request.headers.get("X-Client-IP") or
        request.client.host if request.client else "unknown"
    )


@router.post("/forgot-password", response_model=PasswordResetResponse)
async def forgot_password(
    request: Request,
    reset_request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset for a user account.
    
    Security features:
    - Rate limiting (3 attempts per hour, 10 per day)
    - Email enumeration protection
    - Audit logging
    - Secure token generation
    """
    try:
        from app.services.password_reset_service import get_password_reset_service
        
        # Get client information
        client_ip = _get_client_ip(request)
        user_agent = request.headers.get("User-Agent")
        
        # Get password reset service
        reset_service = get_password_reset_service()
        
        # Request password reset
        result = await reset_service.request_password_reset(
            db=db,
            email=reset_request.email,
            client_ip=client_ip,
            user_agent=user_agent
        )
        
        # Always return success message for security (prevent email enumeration)
        return PasswordResetResponse(
            message=result.message,
            success=True  # Always return success to prevent enumeration
        )
        
    except Exception as e:
        # Create sanitized error response
        error_detail = create_secure_error_response(
            exception=e,
            error_code="PASSWORD_RESET_REQUEST_ERROR",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4()),
            user_message="An error occurred while processing your password reset request. Please try again.",
            suggested_action="If the problem persists, please contact support."
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail.user_message
        )


@router.get("/verify-reset-token", response_model=PasswordResetResponse)
async def verify_reset_token(
    request: Request,
    token: str,
    db: Session = Depends(get_db)
):
    """
    Verify that a password reset token is valid.
    
    Security features:
    - Token validation without revealing sensitive information
    - Audit logging of verification attempts
    - Rate limiting protection
    """
    try:
        from app.services.password_reset_service import get_password_reset_service
        
        # Get client information
        client_ip = _get_client_ip(request)
        
        # Get password reset service
        reset_service = get_password_reset_service()
        
        # Verify token
        is_valid, user_id, error_message = reset_service.verify_reset_token(
            db=db,
            token=token,
            client_ip=client_ip
        )
        
        if is_valid:
            return PasswordResetResponse(
                message="Token is valid",
                success=True
            )
        else:
            return PasswordResetResponse(
                message=error_message or "Invalid or expired token",
                success=False
            )
            
    except Exception as e:
        # Create sanitized error response
        error_detail = create_secure_error_response(
            exception=e,
            error_code="TOKEN_VERIFICATION_ERROR",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4()),
            user_message="An error occurred while verifying the token. Please try again.",
            suggested_action="If the problem persists, please request a new password reset."
        )
        
        return PasswordResetResponse(
            message=error_detail.user_message,
            success=False
        )


@router.post("/reset-password", response_model=PasswordResetResponse)
async def reset_password(
    request: Request,
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Reset user password using a valid reset token.
    
    Security features:
    - Secure token validation
    - Password strength validation
    - Token invalidation after use
    - Audit logging
    - Rate limiting protection
    """
    try:
        from app.services.password_reset_service import get_password_reset_service
        
        # Get client information
        client_ip = _get_client_ip(request)
        user_agent = request.headers.get("User-Agent")
        
        # Get password reset service
        reset_service = get_password_reset_service()
        
        # Reset password
        result = reset_service.reset_password(
            db=db,
            token=reset_data.token,
            new_password=reset_data.new_password,
            client_ip=client_ip,
            user_agent=user_agent
        )
        
        return PasswordResetResponse(
            message=result.message,
            success=result.success
        )
        
    except Exception as e:
        # Create sanitized error response
        error_detail = create_secure_error_response(
            exception=e,
            error_code="PASSWORD_RESET_ERROR",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4()),
            user_message="An error occurred while resetting your password. Please try again.",
            suggested_action="If the problem persists, please request a new password reset."
        )
        
        return PasswordResetResponse(
            message=error_detail.user_message,
            success=False
        )

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie)
):
    """Get current authenticated user information."""
    return UserResponse.model_validate(current_user)

@router.get("/test-auth")
async def test_auth():
    """Test endpoint that doesn't require authentication."""
    return {"message": "Test endpoint working"}

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Secure logout with token revocation and cookie clearing."""
    try:
        # Extract token from request for revocation
        from app.core.cookie_auth import extract_token_from_request
        token = extract_token_from_request(request)
        
        if token:
            # Revoke the token
            jwt_manager.revoke_token(
                token=token,
                user_id=current_user.id,
                reason="user_logout",
                db=db,
                request=request
            )
        
        # Clear authentication and CSRF cookies
        clear_auth_cookie(response, current_user.id)
        clear_csrf_cookie(response)
        
        return {"message": "Logout successful"}
        
    except Exception as e:
        # Always clear cookies even if token revocation fails
        clear_auth_cookie(response, current_user.id)
        clear_csrf_cookie(response)
        
        return {"message": "Logout completed"}

@router.post("/refresh-csrf")
async def refresh_csrf_token(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user_from_cookie)
):
    """Refresh CSRF token for authenticated user."""
    try:
        # Generate new CSRF token
        csrf_token = generate_csrf_token(current_user.id)
        
        # Set new CSRF cookie
        set_csrf_cookie(response, csrf_token)
        
        return {"csrf_token": csrf_token}
        
    except Exception as e:
        # Create sanitized error response
        error_detail = create_secure_error_response(
            exception=e,
            error_code="CSRF_REFRESH_ERROR",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4()),
            user_message="Failed to refresh security token. Please try again.",
            suggested_action="If the problem persists, please refresh the page."
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail.user_message
        )


# Password Reset Endpoints

def _get_client_ip(request: Request) -> str:
    """Extract client IP address with proxy support."""
    forwarded_ips = request.headers.get("X-Forwarded-For")
    if forwarded_ips:
        return forwarded_ips.split(",")[0].strip()
    return (
        request.headers.get("X-Real-IP") or
        request.headers.get("X-Client-IP") or
        request.client.host if request.client else "unknown"
    )


@router.post("/forgot-password", response_model=PasswordResetResponse)
async def forgot_password(
    request: Request,
    reset_request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset for a user account.
    
    Security features:
    - Rate limiting (3 attempts per hour, 10 per day)
    - Email enumeration protection
    - Audit logging
    - Secure token generation
    """
    try:
        from app.services.password_reset_service import get_password_reset_service
        
        # Get client information
        client_ip = _get_client_ip(request)
        user_agent = request.headers.get("User-Agent")
        
        # Get password reset service
        reset_service = get_password_reset_service()
        
        # Request password reset
        result = await reset_service.request_password_reset(
            db=db,
            email=reset_request.email,
            client_ip=client_ip,
            user_agent=user_agent
        )
        
        # Always return success message for security (prevent email enumeration)
        return PasswordResetResponse(
            message=result.message,
            success=True  # Always return success to prevent enumeration
        )
        
    except Exception as e:
        # Create sanitized error response
        error_detail = create_secure_error_response(
            exception=e,
            error_code="PASSWORD_RESET_REQUEST_ERROR",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4()),
            user_message="An error occurred while processing your password reset request. Please try again.",
            suggested_action="If the problem persists, please contact support."
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail.user_message
        )


@router.get("/verify-reset-token", response_model=PasswordResetResponse)
async def verify_reset_token(
    request: Request,
    token: str,
    db: Session = Depends(get_db)
):
    """
    Verify that a password reset token is valid.
    
    Security features:
    - Token validation without revealing sensitive information
    - Audit logging of verification attempts
    - Rate limiting protection
    """
    try:
        from app.services.password_reset_service import get_password_reset_service
        
        # Get client information
        client_ip = _get_client_ip(request)
        
        # Get password reset service
        reset_service = get_password_reset_service()
        
        # Verify token
        is_valid, user_id, error_message = reset_service.verify_reset_token(
            db=db,
            token=token,
            client_ip=client_ip
        )
        
        if is_valid:
            return PasswordResetResponse(
                message="Token is valid",
                success=True
            )
        else:
            return PasswordResetResponse(
                message=error_message or "Invalid or expired token",
                success=False
            )
            
    except Exception as e:
        # Create sanitized error response
        error_detail = create_secure_error_response(
            exception=e,
            error_code="TOKEN_VERIFICATION_ERROR",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4()),
            user_message="An error occurred while verifying the token. Please try again.",
            suggested_action="If the problem persists, please request a new password reset."
        )
        
        return PasswordResetResponse(
            message=error_detail.user_message,
            success=False
        )


@router.post("/reset-password", response_model=PasswordResetResponse)
async def reset_password(
    request: Request,
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Reset user password using a valid reset token.
    
    Security features:
    - Secure token validation
    - Password strength validation
    - Token invalidation after use
    - Audit logging
    - Rate limiting protection
    """
    try:
        from app.services.password_reset_service import get_password_reset_service
        
        # Get client information
        client_ip = _get_client_ip(request)
        user_agent = request.headers.get("User-Agent")
        
        # Get password reset service
        reset_service = get_password_reset_service()
        
        # Reset password
        result = reset_service.reset_password(
            db=db,
            token=reset_data.token,
            new_password=reset_data.new_password,
            client_ip=client_ip,
            user_agent=user_agent
        )
        
        return PasswordResetResponse(
            message=result.message,
            success=result.success
        )
        
    except Exception as e:
        # Create sanitized error response
        error_detail = create_secure_error_response(
            exception=e,
            error_code="PASSWORD_RESET_ERROR",
            error_category=ErrorCategory.SYSTEM_ERROR,
            correlation_id=str(uuid.uuid4()),
            user_message="An error occurred while resetting your password. Please try again.",
            suggested_action="If the problem persists, please request a new password reset."
        )
        
        return PasswordResetResponse(
            message=error_detail.user_message,
            success=False
        )

@router.post("/websocket-token")
async def get_websocket_token(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Generate a temporary WebSocket authentication token.
    This token is needed because WebSocket connections cannot access HttpOnly cookies.
    The token is valid for 5 minutes and is single-use for WebSocket connections.
    """
    try:
        # Create a temporary token with limited lifetime
        token_data = {
            "sub": str(current_user.id),
            "type": "websocket",
            "iat": datetime.utcnow().timestamp(),
            "exp": (datetime.utcnow() + timedelta(minutes=5)).timestamp(),
            "jti": str(uuid.uuid4())  # Unique token ID
        }
        
        # Use the same JWT encoding as regular auth
        websocket_token = jwt.encode(
            token_data,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        return {
            "websocket_token": websocket_token,
            "expires_in": 300,  # 5 minutes in seconds
            "token_type": "websocket"
        }
        
    except Exception as e:
        # Create sanitized error response
        error_detail = create_secure_error_response(
            exception=e,
            error_code="WEBSOCKET_TOKEN_ERROR",
            error_category=ErrorCategory.AUTHENTICATION,
            correlation_id=str(uuid.uuid4()),
            user_message="Failed to generate WebSocket token",
            suggested_action="Please try again or refresh the page"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail.user_message
        )
