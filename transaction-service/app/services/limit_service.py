from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from app.models.payment_limit import PaymentLimit
from app.schemas.limit import PaymentLimitResponse, PaymentLimitUpdate
from app.core.config import settings
from app.utils.exceptions import ValidationError

logger = logging.getLogger(__name__)

class LimitService:
    def __init__(self, db: Session):
        self.db = db
    
    async def check_payment_limits(
        self,
        user_id: int,
        currency_code: str,
        amount: Decimal
    ) -> PaymentLimitResponse:
        """Check if transaction amount is within payment limits"""
        # Get or create payment limit for user and currency
        limit = await self.get_or_create_user_currency_limit(user_id, currency_code)
        
        # Reset expired limits
        await self._reset_expired_limits_for_user(limit)
        
        # Check limits
        daily_remaining = limit.daily_limit - limit.current_daily_used
        monthly_remaining = limit.monthly_limit - limit.current_monthly_used
        yearly_remaining = limit.yearly_limit - limit.current_yearly_used
        
        can_proceed = (
            amount <= daily_remaining and
            amount <= monthly_remaining and
            amount <= yearly_remaining
        )
        
        # Determine limiting factor
        limiting_factor = None
        if not can_proceed:
            if amount > daily_remaining:
                limiting_factor = "daily"
            elif amount > monthly_remaining:
                limiting_factor = "monthly"
            elif amount > yearly_remaining:
                limiting_factor = "yearly"
        
        message = "Transaction can proceed" if can_proceed else f"Transaction exceeds {limiting_factor} limit"
        
        return PaymentLimitResponse(
            can_proceed=can_proceed,
            currency_code=currency_code,
            requested_amount=amount,
            daily_limit=limit.daily_limit,
            monthly_limit=limit.monthly_limit,
            yearly_limit=limit.yearly_limit,
            daily_remaining=daily_remaining,
            monthly_remaining=monthly_remaining,
            yearly_remaining=yearly_remaining,
            limiting_factor=limiting_factor,
            message=message
        )
    
    async def get_user_limits(self, user_id: int) -> List[PaymentLimit]:
        """Get all payment limits for a user"""
        return self.db.query(PaymentLimit).filter(
            PaymentLimit.user_id == user_id
        ).all()
    
    async def get_user_currency_limit(self, user_id: int, currency_code: str) -> Optional[PaymentLimit]:
        """Get payment limit for specific user and currency"""
        return self.db.query(PaymentLimit).filter(
            and_(
                PaymentLimit.user_id == user_id,
                PaymentLimit.currency_code == currency_code
            )
        ).first()
    
    async def get_or_create_user_currency_limit(self, user_id: int, currency_code: str) -> PaymentLimit:
        """Get or create payment limit for user and currency"""
        limit = await self.get_user_currency_limit(user_id, currency_code)
        
        if not limit:
            limit = await self._create_default_limit(user_id, currency_code)
        
        return limit
    
    async def update_payment_limit(
        self,
        user_id: int,
        currency_code: str,
        limit_update: PaymentLimitUpdate
    ) -> PaymentLimit:
        """Update payment limits for user and currency"""
        limit = await self.get_or_create_user_currency_limit(user_id, currency_code)
        
        update_data = limit_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if value is not None:
                setattr(limit, field, value)
        
        self.db.commit()
        self.db.refresh(limit)
        
        logger.info(f"Updated payment limits for user {user_id}, currency {currency_code}")
        return limit
    
    async def update_limit_usage(
        self,
        user_id: int,
        currency_code: str,
        amount: Decimal,
        operation: str = "add"
    ):
        """Update payment limit usage (add or subtract)"""
        limit = await self.get_or_create_user_currency_limit(user_id, currency_code)
        
        if operation == "add":
            limit.current_daily_used += amount
            limit.current_monthly_used += amount
            limit.current_yearly_used += amount
        elif operation == "subtract":
            limit.current_daily_used = max(Decimal('0'), limit.current_daily_used - amount)
            limit.current_monthly_used = max(Decimal('0'), limit.current_monthly_used - amount)
            limit.current_yearly_used = max(Decimal('0'), limit.current_yearly_used - amount)
        else:
            raise ValidationError("Operation must be 'add' or 'subtract'")
        
        self.db.commit()
        self.db.refresh(limit)
        
        logger.info(f"Updated limit usage for user {user_id}, currency {currency_code}: {operation} {amount}")
    
    async def reset_expired_limits(self) -> int:
        """Reset all expired payment limits"""
        now = datetime.utcnow()
        reset_count = 0
        
        limits = self.db.query(PaymentLimit).all()
        
        for limit in limits:
            reset_needed = limit.is_reset_needed()
            
            if reset_needed["daily"]:
                limit.current_daily_used = Decimal('0')
                limit.daily_reset_at = now + timedelta(days=1)
                reset_count += 1
            
            if reset_needed["monthly"]:
                limit.current_monthly_used = Decimal('0')
                # Reset to first day of next month
                next_month = now.replace(day=1) + timedelta(days=32)
                limit.monthly_reset_at = next_month.replace(day=1)
                reset_count += 1
            
            if reset_needed["yearly"]:
                limit.current_yearly_used = Decimal('0')
                limit.yearly_reset_at = now.replace(year=now.year + 1, month=1, day=1)
                reset_count += 1
        
        self.db.commit()
        
        if reset_count > 0:
            logger.info(f"Reset {reset_count} expired payment limits")
        
        return reset_count
    
    async def _create_default_limit(self, user_id: int, currency_code: str) -> PaymentLimit:
        """Create default payment limit for user and currency"""
        now = datetime.utcnow()
        
        # Set reset times
        daily_reset = now + timedelta(days=1)
        monthly_reset = (now.replace(day=1) + timedelta(days=32)).replace(day=1)
        yearly_reset = now.replace(year=now.year + 1, month=1, day=1)
        
        limit = PaymentLimit(
            user_id=user_id,
            currency_code=currency_code,
            daily_limit=Decimal(str(settings.DEFAULT_DAILY_LIMIT)),
            monthly_limit=Decimal(str(settings.DEFAULT_MONTHLY_LIMIT)),
            yearly_limit=Decimal(str(settings.DEFAULT_YEARLY_LIMIT)),
            current_daily_used=Decimal('0'),
            current_monthly_used=Decimal('0'),
            current_yearly_used=Decimal('0'),
            daily_reset_at=daily_reset,
            monthly_reset_at=monthly_reset,
            yearly_reset_at=yearly_reset
        )
        
        self.db.add(limit)
        self.db.commit()
        self.db.refresh(limit)
        
        logger.info(f"Created default payment limit for user {user_id}, currency {currency_code}")
        return limit
    
    async def _reset_expired_limits_for_user(self, limit: PaymentLimit):
        """Reset expired limits for a specific user limit"""
        reset_needed = limit.is_reset_needed()
        now = datetime.utcnow()
        
        if reset_needed["daily"]:
            limit.current_daily_used = Decimal('0')
            limit.daily_reset_at = now + timedelta(days=1)
        
        if reset_needed["monthly"]:
            limit.current_monthly_used = Decimal('0')
            next_month = now.replace(day=1) + timedelta(days=32)
            limit.monthly_reset_at = next_month.replace(day=1)
        
        if reset_needed["yearly"]:
            limit.current_yearly_used = Decimal('0')
            limit.yearly_reset_at = now.replace(year=now.year + 1, month=1, day=1)
        
        if any(reset_needed.values()):
            self.db.commit()
            self.db.refresh(limit)
