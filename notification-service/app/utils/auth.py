from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)
security = HTTPBearer()

async def get_current_service(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get current service from JWT token (for inter-service communication)"""
    try:
        payload = jwt.decode(
            credentials.credentials, 
            settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        service_name = payload.get("service")
        if service_name is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid service credentials"
            )
        
        # Create mock service object
        class MockService:
            def __init__(self, name):
                self.name = name
        
        return MockService(service_name)
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service credentials"
        )
