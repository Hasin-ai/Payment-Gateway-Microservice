import bcrypt
from jose import jwt  # Change import to use jwt from jose package
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import re

from app.core.config import settings

class SecurityUtils:
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    @staticmethod
    def validate_password(password: str) -> Dict[str, Any]:
        """Validate password strength"""
        errors = []
        
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            errors.append(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long")
        
        if settings.PASSWORD_REQUIRE_UPPER and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if settings.PASSWORD_REQUIRE_NUMBER and not re.search(r'[0-9]', password):
            errors.append("Password must contain at least one number")
        
        if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    @staticmethod
    def create_access_token(data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        to_encode.update({"exp": expire, "type": "access"})
        
        return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None
    
    @staticmethod
    def generate_session_token() -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_verification_token() -> str:
        """Generate email verification token"""
        return secrets.token_urlsafe(32)
