from pydantic import BaseModel, validator, Field
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from ipaddress import IPv4Address, IPv6Address

class AuditEventCreate(BaseModel):
    user_id: Optional[int] = None
    action: str
    table_name: Optional[str] = None
    record_id: Optional[int] = None
    old_data: Optional[Dict[str, Any]] = None
    new_data: Optional[Dict[str, Any]] = None
    ip_address: Optional[Union[IPv4Address, IPv6Address, str]] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    service_name: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None
    severity: str = "INFO"
    category: Optional[str] = None
    compliance_tags: Optional[List[str]] = None
    is_sensitive: bool = False
    is_successful: Optional[bool] = None
    
    @validator("action")
    def validate_action(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Action cannot be empty")
        return v.strip()
    
    @validator("severity")
    def validate_severity(cls, v):
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"Severity must be one of: {allowed_levels}")
        return v.upper()
    
    @validator("method")
    def validate_method(cls, v):
        if v:
            allowed_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]
            if v.upper() not in allowed_methods:
                raise ValueError(f"HTTP method must be one of: {allowed_methods}")
            return v.upper()
        return v

class AuditEventResponse(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    table_name: Optional[str]
    record_id: Optional[int]
    old_data: Optional[Any]  # Can be redacted
    new_data: Optional[Any]  # Can be redacted
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_id: Optional[str]
    session_id: Optional[str]
    service_name: Optional[str]
    endpoint: Optional[str]
    method: Optional[str]
    meta_data: Optional[Any]  # Can be redacted
    severity: str
    category: Optional[str]
    compliance_tags: Optional[List[str]]
    is_sensitive: bool
    is_successful: Optional[bool]
    created_at: datetime
    
    class Config:
        from_attributes = True

class AuditLogQuery(BaseModel):
    user_id: Optional[int] = None
    action: Optional[str] = None
    table_name: Optional[str] = None
    record_id: Optional[int] = None
    service_name: Optional[str] = None
    severity: Optional[str] = None
    category: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    ip_address: Optional[str] = None
    is_successful: Optional[bool] = None
    include_sensitive: bool = False
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=1000)
    
    @validator("severity")
    def validate_severity(cls, v):
        if v:
            allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if v.upper() not in allowed_levels:
                raise ValueError(f"Severity must be one of: {allowed_levels}")
            return v.upper()
        return v

class AuditLogList(BaseModel):
    logs: List[AuditEventResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool

class BulkAuditCreate(BaseModel):
    events: List[AuditEventCreate]
    batch_id: Optional[str] = None
    
    @validator("events")
    def validate_events(cls, v):
        if len(v) > 1000:
            raise ValueError("Maximum 1000 events per batch")
        return v

class AuditStats(BaseModel):
    total_logs: int
    logs_by_severity: Dict[str, int]
    logs_by_category: Dict[str, int]
    logs_by_service: Dict[str, int]
    failed_actions: int
    successful_actions: int
    unique_users: int
    date_range: Dict[str, datetime]

class SecurityAlert(BaseModel):
    alert_type: str
    severity: str
    user_id: Optional[int]
    ip_address: Optional[str]
    description: str
    event_count: int
    first_occurrence: datetime
    last_occurrence: datetime
    related_logs: List[int]  # Log IDs
