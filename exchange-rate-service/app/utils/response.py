from pydantic import BaseModel
from typing import TypeVar, Generic, Optional, Any
from datetime import datetime

T = TypeVar('T')

class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: Optional[T] = None
    timestamp: datetime = datetime.utcnow()

class ErrorResponse(BaseModel):
    success: bool = False
    error: dict
    timestamp: datetime = datetime.utcnow()
