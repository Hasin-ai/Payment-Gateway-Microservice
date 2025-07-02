from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from typing import Optional

from app.core.config import settings

class ServiceInfo:
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role

def get_current_service() -> ServiceInfo:
    """Mock service authentication - replace with actual JWT validation"""
    # This is a simplified version - implement proper JWT validation
    return ServiceInfo(name="audit-service", role="system")

def require_admin_or_system() -> ServiceInfo:
    """Require admin or system role"""
    service = get_current_service()
    if service.role not in ["admin", "system"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or system role required"
        )
    return service
