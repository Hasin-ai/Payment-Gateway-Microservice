from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Annotated
from datetime import datetime

# Base schema for user attributes
class UserBase(BaseModel):
    username: Annotated[str, Field(min_length=3, max_length=50)]
    email: EmailStr
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None

# Schema for creating a new user
class UserCreate(UserBase):
    password: str

# Schema for updating a user's profile
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    address: Optional[str] = None

# Response schema for user data
class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserProfile(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    phone_number: Optional[str]
    address: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class UserList(BaseModel):
    users: list[UserProfile]
    total: int
    page: int
    size: int

class UserStats(BaseModel):
    total_users: int
    verified_users: int
    active_users: int
    new_registrations_today: int
    new_registrations_this_week: int
    new_registrations_this_month: int
