from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    business_type: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    business_type: Optional[str] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class AuthResponse(BaseModel):
    message: str
    user: UserResponse
    csrf_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address to send password reset link to")


class PasswordResetVerify(BaseModel):
    token: str = Field(..., min_length=1, description="Password reset token to verify")


class PasswordResetConfirm(BaseModel):
    token: str = Field(..., min_length=1, description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password (minimum 8 characters)")


class PasswordResetResponse(BaseModel):
    message: str
    success: bool = True
