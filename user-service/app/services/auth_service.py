from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from app.models.user import User
from app.models.session import UserSession
from app.schemas.auth import UserCreate, UserLogin, Token
from app.schemas.user import UserResponse
from app.core.security import SecurityUtils
from app.core.config import settings
from app.core.database import get_db

logger = logging.getLogger(__name__)
security = HTTPBearer()

class AuthService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, user_data: UserCreate, client_ip: str = None, user_agent: str = None) -> User:
        """Create a new user account"""
        # Check if user already exists
        existing_user = self.db.query(User).filter(
            or_(User.email == user_data.email, User.username == user_data.username)
        ).first()
        
        if existing_user:
            if existing_user.email == user_data.email:
                raise ValueError("Email already registered")
            else:
                raise ValueError("Username already taken")
        
        # Validate password strength
        password_validation = SecurityUtils.validate_password(user_data.password)
        if not password_validation["valid"]:
            raise ValueError(password_validation["message"])
        
        # Hash password
        hashed_password = SecurityUtils.hash_password(user_data.password)
        
        # Generate email verification token
        email_verification_token = SecurityUtils.generate_verification_token()
        
        # Create user
        new_user = User(
            username=user_data.username.lower(),
            email=user_data.email.lower(),
            password_hash=hashed_password,
            full_name=user_data.full_name,
            phone_number=user_data.phone_number,
            address=user_data.address,
            role="user",
            is_active=True,
            is_verified=False,
            email_verification_token=email_verification_token,
        )
        
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        
        logger.info(f"User created: {new_user.username}")
        
        return new_user

    def authenticate_user(self, login_data: UserLogin, client_ip: str = None, user_agent: str = None) -> Token:
        """Authenticate user and create session"""
        # Find user
        user = self.db.query(User).filter(User.email == login_data.email.lower()).first()
        
        if not user:
            raise ValueError("Invalid email or password")
        
        # Check if user can login
        if not user.can_login():
            if user.is_locked():
                raise ValueError("Account is temporarily locked")
            else:
                raise ValueError("Account is inactive")
        
        # Verify password
        if not SecurityUtils.verify_password(login_data.password, user.password_hash):
            # Increment failed attempts
            user.failed_login_attempts += 1
            
            # Lock account if too many failed attempts
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(hours=1)
                logger.warning(f"Account locked for user {user.email} due to failed login attempts")
            
            self.db.commit()
            raise ValueError("Invalid email or password")
        
        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.utcnow()
        
        # Create session
        session = self._create_user_session(user, client_ip, user_agent)
        
        # Generate tokens
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_verified": user.is_verified,
            "session_id": session.id
        }
        
        access_token = SecurityUtils.create_access_token(token_data)
        refresh_token = SecurityUtils.create_refresh_token(token_data)
        
        # Update session with refresh token
        session.refresh_token = refresh_token
        
        self.db.commit()
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=settings.JWT_EXPIRE_MINUTES * 60,
            user=UserResponse.from_orm(user)
        )
    
    def _create_user_session(self, user: User, client_ip: str, user_agent: str) -> UserSession:
        """Create a new user session"""
        # Optional: Clean up expired sessions for the user
        self.db.query(UserSession).filter(
            and_(UserSession.user_id == user.id, UserSession.expires_at < datetime.utcnow())
        ).delete(synchronize_session=False)
        
        # Create new session
        session_token = SecurityUtils.generate_session_token()
        expires_at = datetime.utcnow() + timedelta(hours=settings.SESSION_EXPIRE_HOURS)
        
        session = UserSession(
            user_id=user.id,
            session_token=session_token,
            ip_address=client_ip,
            user_agent=user_agent,
            expires_at=expires_at,
            is_active=True
        )
        
        self.db.add(session)
        return session
    
    async def refresh_access_token(self, refresh_token: str, client_ip: str = None, user_agent: str = None) -> Token:
        """Refresh access token using refresh token"""
        # Verify refresh token
        payload = SecurityUtils.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token")
        
        # Get session by refresh token
        session = self.db.query(UserSession).filter(UserSession.refresh_token == refresh_token).first()
        if not session or not session.is_valid():
            raise ValueError("Invalid or expired session")
        
        # Get user
        user_id = int(payload.get("sub"))
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")
        
        # Create new tokens
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_verified": user.is_verified,
            "session_id": session.id
        }
        
        access_token = SecurityUtils.create_access_token(token_data)
        new_refresh_token = SecurityUtils.create_refresh_token(token_data)
        
        # Update session
        session.refresh_token = new_refresh_token
        session.last_accessed = datetime.utcnow()
        session.expires_at = datetime.utcnow() + timedelta(hours=settings.SESSION_EXPIRE_HOURS)
        
        self.db.commit()
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="Bearer",
            expires_in=settings.JWT_EXPIRE_MINUTES * 60,
            user=UserResponse.from_orm(user)
        )
    
    async def logout_user(self, token: str) -> bool:
        """Logout user and invalidate session"""
        try:
            # Verify token to get session id
            payload = SecurityUtils.verify_token(token)
            if not payload:
                return False
                
            session_id = payload.get("session_id")
            if not session_id:
                return False
            
            # Invalidate session
            session = self.db.query(UserSession).filter(UserSession.id == session_id).first()
            if session:
                session.is_active = False
                self.db.commit()
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error during logout: {e}")
            return False
    
    def get_current_user(self, token: HTTPAuthorizationCredentials = Depends(security)):
        """Get current user from token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = SecurityUtils.verify_token(token.credentials)
            if payload is None:
                raise credentials_exception
                
            user_id = payload.get("sub")
            if user_id is None:
                raise credentials_exception
                
        except Exception:
            raise credentials_exception
            
        user = self.db.query(User).filter(User.id == user_id).first()
        if user is None or not user.is_active:
            raise credentials_exception
            
        return user
        
    def get_current_admin_user(self, current_user = Depends(get_current_user)):
        """Check if current user is admin"""
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
            
    async def send_verification_email(self, email: str, token: str):
        """Send verification email (placeholder)"""
        logger.info(f"Sending verification email to {email} with token {token[:10]}...")
        
        # In a real implementation, we would use notification service or an email library
        # For now, we'll just log it
        logger.info(f"Verification link: https://example.com/verify?token={token}")

