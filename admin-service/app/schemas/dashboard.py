from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal

class DateRange(BaseModel):
    start: datetime
    end: datetime

class TransactionStats(BaseModel):
    total_count: int
    completed_count: int
    pending_count: int
    failed_count: int
    total_volume_bdt: Decimal
    total_volume_usd: Decimal
    average_transaction_size_usd: Decimal

class RevenueStats(BaseModel):
    service_fees_bdt: Decimal
    service_fees_usd: Decimal

class UserStats(BaseModel):
    new_registrations: int
    active_users: int
    verified_users: int
    total_users: int

class SystemHealthStats(BaseModel):
    uptime_percentage: float
    average_response_time_ms: int
    error_rate_percentage: float

class DashboardStats(BaseModel):
    period: str
    date_range: DateRange
    transactions: TransactionStats
    revenue: RevenueStats
    users: UserStats
    system_health: SystemHealthStats

class CurrencyStats(BaseModel):
    currency_code: str
    transaction_count: int
    total_volume: Decimal
    percentage_of_total: float

class TopRecipients(BaseModel):
    recipient_email: str
    transaction_count: int
    total_amount_usd: Decimal

class PlatformMetrics(BaseModel):
    total_processed_volume_bdt: Decimal
    total_processed_volume_usd: Decimal
    success_rate_percentage: float
    average_processing_time_minutes: float
    most_popular_currencies: List[CurrencyStats]
    top_recipients: List[TopRecipients]