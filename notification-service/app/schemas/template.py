from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class TemplateCreate(BaseModel):
    template_key: str
    template_name: str
    description: Optional[str] = None
    channel: str
    subject_template: Optional[str] = None
    body_template: str
    required_variables: Optional[List[str]] = []
    optional_variables: Optional[List[str]] = []
    category: Optional[str] = None
    
    @validator("channel")
    def validate_channel(cls, v):
        allowed_channels = ["email", "sms", "push"]
        if v not in allowed_channels:
            raise ValueError(f"Channel must be one of: {allowed_channels}")
        return v
    
    @validator("template_key")
    def validate_template_key(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Template key can only contain letters, numbers, hyphens and underscores")
        return v

class TemplateUpdate(BaseModel):
    template_name: Optional[str] = None
    description: Optional[str] = None
    subject_template: Optional[str] = None
    body_template: Optional[str] = None
    required_variables: Optional[List[str]] = None
    optional_variables: Optional[List[str]] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None

class TemplateResponse(BaseModel):
    id: int
    template_key: str
    template_name: str
    description: Optional[str]
    channel: str
    subject_template: Optional[str]
    body_template: str
    required_variables: Optional[List[str]]
    optional_variables: Optional[List[str]]
    is_active: bool
    category: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TemplateRender(BaseModel):
    template_key: str
    template_data: Dict[str, Any]

class TemplateRenderResponse(BaseModel):
    template_key: str
    channel: str
    rendered_subject: Optional[str]
    rendered_body: str
    missing_variables: List[str]
