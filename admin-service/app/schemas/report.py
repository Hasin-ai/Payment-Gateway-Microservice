from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal

class ReportRequest(BaseModel):
    report_type: str
    start_date: date
    end_date: date
    filters: Optional[Dict[str, Any]] = {}
    format: str = "json"  # json, csv, pdf
    
    @validator("report_type")
    def validate_report_type(cls, v):
        allowed_types = [
            "transaction_summary",
            "revenue_report",
            "user_activity",
            "payment_method_analysis",
            "currency_breakdown",
            "failure_analysis",
            "settlement_report"
        ]
        if v not in allowed_types:
            raise ValueError(f"Report type must be one of: {allowed_types}")
        return v
    
    @validator("format")
    def validate_format(cls, v):
        allowed_formats = ["json", "csv", "pdf"]
        if v not in allowed_formats:
            raise ValueError(f"Format must be one of: {allowed_formats}")
        return v
    
    @validator("end_date")
    def validate_date_range(cls, v, values):
        if "start_date" in values and v < values["start_date"]:
            raise ValueError("End date must be after start date")
        return v