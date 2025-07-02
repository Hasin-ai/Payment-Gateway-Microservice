from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    phone_number: Optional[str] = None
    address: Optional[str] = None
    
    @validator("username")
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if len(v) > 50:
            raise ValueError("Username cannot be longer than 50 characters")
        return v.lower()
    
    @validator("phone_number")
    def validate_phone_number(cls, v):
        if v and not v.startswith("+880"):
            raise ValueError("Phone number must start with +880 for Bangladesh")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: dict

class RefreshToken(BaseModel):
    refresh_token: str

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class EmailVerification(BaseModel):
    token: str

class UserResponse(BaseModel):
    success: bool = True
    message: str
    data: dict
    
    class Config:
        from_attributes = True
