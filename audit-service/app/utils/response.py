from typing import TypeVar, Generic, Optional, Any
from pydantic import BaseModel

T = TypeVar('T')

class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: Optional[T] = None
    
class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Any] = None
