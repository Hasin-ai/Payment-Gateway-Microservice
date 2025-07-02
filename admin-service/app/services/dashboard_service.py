import httpx
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Any, List
from decimal import Decimal

from app.core.config import settings
from app.schemas.dashboard import (
    DashboardStats, 
    DateRange, 
    TransactionStats, 
    RevenueStats, 
    UserStats, 
    SystemHealthStats,
    PlatformMetrics,
    CurrencyStats,
    TopRecipients
)

class DashboardService:
    def __init__(self, db: Session):
        self.db = db
        self.http_client = httpx.AsyncClient()
    
    async def get_dashboard_stats(self, period: str = "today") -> DashboardStats:
        """Get comprehensive dashboard statistics"""
        date_range = self._get_date_range(period)
        
        # Get data from various services
        transactions = await self._get_transaction_stats(date_range)
        revenue = await self._get_revenue_stats(date_range)
        users = await self._get_user_stats(date_range)
        system_health = await self._get_system_health_stats()
        
        return DashboardStats(
            period=period,
            date_range=date_range,
            transactions=transactions,
            revenue=revenue,
            users=users,
            system_health=system_health
        )
    
    async def get_platform_metrics(self) -> PlatformMetrics:
        """Get platform-wide metrics"""
        try:
            # Get transaction metrics
            transaction_response = await self.http_client.get(
                f"{settings.TRANSACTION_SERVICE_URL}/api/v1/metrics/platform"
            )
            transaction_data = transaction_response.json() if transaction_response.status_code == 200 else {}
            
            # Get currency stats
            currency_stats = await self._get_currency_stats()
            
            # Get top recipients
            top_recipients = await self._get_top_recipients()
            
            return PlatformMetrics(
                total_processed_volume_bdt=Decimal(str(transaction_data.get("total_volume_bdt", 0))),
                total_processed_volume_usd=Decimal(str(transaction_data.get("total_volume_usd", 0))),
                success_rate_percentage=float(transaction_data.get("success_rate", 0)),
                average_processing_time_minutes=float(transaction_data.get("avg_processing_time", 0)),
                most_popular_currencies=currency_stats,
                top_recipients=top_recipients
            )
        except Exception as e:
            # Return default values if external services are unavailable
            return PlatformMetrics(
                total_processed_volume_bdt=Decimal("0"),
                total_processed_volume_usd=Decimal("0"),
                success_rate_percentage=0.0,
                average_processing_time_minutes=0.0,
                most_popular_currencies=[],
                top_recipients=[]
            )
    
    def _get_date_range(self, period: str) -> DateRange:
        """Get date range based on period"""
        now = datetime.utcnow()
        
        if period == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif period == "week":
            start = now - timedelta(days=7)
            end = now
        elif period == "month":
            start = now - timedelta(days=30)
            end = now
        elif period == "year":
            start = now - timedelta(days=365)
            end = now
        else:
            # Default to today
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
        
        return DateRange(start=start, end=end)
    
    async def _get_transaction_stats(self, date_range: DateRange) -> TransactionStats:
        """Get transaction statistics from transaction service"""
        try:
            response = await self.http_client.get(
                f"{settings.TRANSACTION_SERVICE_URL}/api/v1/stats/transactions",
                params={
                    "start_date": date_range.start.isoformat(),
                    "end_date": date_range.end.isoformat()
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return TransactionStats(
                    total_count=data.get("total_count", 0),
                    completed_count=data.get("completed_count", 0),
                    pending_count=data.get("pending_count", 0),
                    failed_count=data.get("failed_count", 0),
                    total_volume_bdt=Decimal(str(data.get("total_volume_bdt", 0))),
                    total_volume_usd=Decimal(str(data.get("total_volume_usd", 0))),
                    average_transaction_size_usd=Decimal(str(data.get("average_transaction_size_usd", 0)))
                )
            else:
                return self._default_transaction_stats()
        except Exception:
            return self._default_transaction_stats()
    
    async def _get_revenue_stats(self, date_range: DateRange) -> RevenueStats:
        """Get revenue statistics from payment service"""
        try:
            response = await self.http_client.get(
                f"{settings.PAYMENT_SERVICE_URL}/api/v1/stats/revenue",
                params={
                    "start_date": date_range.start.isoformat(),
                    "end_date": date_range.end.isoformat()
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return RevenueStats(
                    service_fees_bdt=Decimal(str(data.get("service_fees_bdt", 0))),
                    service_fees_usd=Decimal(str(data.get("service_fees_usd", 0)))
                )
            else:
                return RevenueStats(
                    service_fees_bdt=Decimal("0"),
                    service_fees_usd=Decimal("0")
                )
        except Exception:
            return RevenueStats(
                service_fees_bdt=Decimal("0"),
                service_fees_usd=Decimal("0")
            )
    
    async def _get_user_stats(self, date_range: DateRange) -> UserStats:
        """Get user statistics from user service"""
        try:
            response = await self.http_client.get(
                f"{settings.USER_SERVICE_URL}/api/v1/stats/users",
                params={
                    "start_date": date_range.start.isoformat(),
                    "end_date": date_range.end.isoformat()
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return UserStats(
                    new_registrations=data.get("new_registrations", 0),
                    active_users=data.get("active_users", 0),
                    verified_users=data.get("verified_users", 0),
                    total_users=data.get("total_users", 0)
                )
            else:
                return UserStats(
                    new_registrations=0,
                    active_users=0,
                    verified_users=0,
                    total_users=0
                )
        except Exception:
            return UserStats(
                new_registrations=0,
                active_users=0,
                verified_users=0,
                total_users=0
            )
    
    async def _get_system_health_stats(self) -> SystemHealthStats:
        """Get system health statistics"""
        # This would typically check the health of various services
        # For now, return mock data
        return SystemHealthStats(
            uptime_percentage=99.9,
            average_response_time_ms=150,
            error_rate_percentage=0.1
        )
    
    async def _get_currency_stats(self) -> List[CurrencyStats]:
        """Get currency statistics"""
        try:
            response = await self.http_client.get(
                f"{settings.TRANSACTION_SERVICE_URL}/api/v1/stats/currencies"
            )
            
            if response.status_code == 200:
                data = response.json()
                return [
                    CurrencyStats(
                        currency_code=item["currency_code"],
                        transaction_count=item["transaction_count"],
                        total_volume=Decimal(str(item["total_volume"])),
                        percentage_of_total=float(item["percentage_of_total"])
                    )
                    for item in data.get("currencies", [])
                ]
            else:
                return []
        except Exception:
            return []
    
    async def _get_top_recipients(self) -> List[TopRecipients]:
        """Get top recipients statistics"""
        try:
            response = await self.http_client.get(
                f"{settings.TRANSACTION_SERVICE_URL}/api/v1/stats/top-recipients"
            )
            
            if response.status_code == 200:
                data = response.json()
                return [
                    TopRecipients(
                        recipient_email=item["recipient_email"],
                        transaction_count=item["transaction_count"],
                        total_amount_usd=Decimal(str(item["total_amount_usd"]))
                    )
                    for item in data.get("recipients", [])
                ]
            else:
                return []
        except Exception:
            return []
    
    def _default_transaction_stats(self) -> TransactionStats:
        """Return default transaction stats when service is unavailable"""
        return TransactionStats(
            total_count=0,
            completed_count=0,
            pending_count=0,
            failed_count=0,
            total_volume_bdt=Decimal("0"),
            total_volume_usd=Decimal("0"),
            average_transaction_size_usd=Decimal("0")
        )
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
