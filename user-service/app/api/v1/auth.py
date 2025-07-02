from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import Token, RefreshToken, UserLogin
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService
from app.utils.response import SuccessResponse
from app.utils.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

router = APIRouter()

@router.post("/register", response_model=SuccessResponse)
def register(
    user_data: UserCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    try:
        auth_service = AuthService(db)
        
        # Get client info
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("User-Agent")
        
        user = auth_service.create_user(user_data, client_ip, user_agent)
        
        # Send verification email in background
        if user.email_verification_token:
            background_tasks.add_task(
                auth_service.send_verification_email,
                user.email,
                user.email_verification_token
            )
        
        return SuccessResponse(
            message="User registered successfully",
            data={
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "is_verified": user.is_verified,
                "created_at": user.created_at.isoformat()
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=SuccessResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Authenticate user and return tokens"""
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    auth_service = AuthService(db)
    
    try:
        login_data = UserLogin(email=form_data.username, password=form_data.password)
        token_data = auth_service.authenticate_user(
            login_data, client_ip, user_agent
        )
        
        return SuccessResponse(
            message="Login successful",
            data=token_data
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )

@router.post("/refresh", response_model=SuccessResponse[Token])
async def refresh_token(
    token_data: RefreshToken,
    request: Request,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    try:
        auth_service = AuthService(db)
        
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("User-Agent")
        
        new_token_data = await auth_service.refresh_access_token(
            token_data.refresh_token, client_ip, user_agent
        )
        
        return SuccessResponse(
            message="Token refreshed successfully",
            data=new_token_data
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.post("/logout", response_model=SuccessResponse)
async def logout(
    request: Request,
    db: Session = Depends(get_db)
):
    """Logout user and invalidate session"""
    try:
        auth_service = AuthService(db)
        
        # Get token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )
            
        token = auth_header.split(" ")[1]
        success = await auth_service.logout_user(token)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid session"
            )
        
        return SuccessResponse(
            message="Logged out successfully",
            data=None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )
