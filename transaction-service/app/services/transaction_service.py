from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import logging

from app.models.transaction import Transaction, TransactionStatusHistory
from app.models.payment_limit import PaymentLimit
from app.schemas.transaction import TransactionCreate, TransactionCalculation, TransactionStats
from app.services.limit_service import LimitService
from app.utils.exceptions import ValidationError, TransactionError, LimitExceededError
from app.core.config import settings

logger = logging.getLogger(__name__)

class TransactionService:
    def __init__(self, db: Session):
        self.db = db
        self.limit_service = LimitService(db)
    
    async def create_transaction(
        self,
        user_id: int,
        transaction_data: TransactionCreate,
        calculation: TransactionCalculation
    ) -> Transaction:
        """Create a new transaction"""
        try:
            # Validate currency support
            if transaction_data.requested_foreign_currency not in settings.SUPPORTED_CURRENCIES:
                raise ValidationError(f"Currency {transaction_data.requested_foreign_currency} is not supported")
            
            # Check payment limits
            can_proceed = await self.limit_service.check_payment_limits(
                user_id=user_id,
                currency_code=transaction_data.requested_foreign_currency,
                amount=transaction_data.requested_foreign_amount
            )
            
            if not can_proceed.can_proceed:
                raise LimitExceededError("Transaction amount exceeds payment limits")
            
            # Generate internal transaction ID
            internal_tran_id = f"TXN-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            
            # Create transaction
            transaction = Transaction(
                user_id=user_id,
                internal_tran_id=internal_tran_id,
                requested_foreign_currency=transaction_data.requested_foreign_currency,
                requested_foreign_amount=transaction_data.requested_foreign_amount,
                recipient_paypal_email=transaction_data.recipient_paypal_email,
                payment_purpose=transaction_data.payment_purpose,
                exchange_rate_bdt=calculation.exchange_rate_bdt,
                calculated_bdt_amount=calculation.calculated_bdt_amount,
                service_fee_bdt=calculation.service_fee_bdt,
                total_bdt_amount=calculation.total_bdt_amount,
                status="PENDING"
            )
            
            self.db.add(transaction)
            self.db.commit()
            self.db.refresh(transaction)
            
            # Update payment limits
            await self.limit_service.update_limit_usage(
                user_id=user_id,
                currency_code=transaction_data.requested_foreign_currency,
                amount=transaction_data.requested_foreign_amount,
                operation="add"
            )
            
            # Log status change
            await self._log_status_change(
                transaction.id,
                old_status=None,
                new_status="PENDING",
                changed_by=user_id,
                change_reason="Transaction created"
            )
            
            logger.info(f"Transaction created: {internal_tran_id} for user {user_id}")
            return transaction
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create transaction: {e}")
            raise
    
    async def get_transaction_by_id(self, transaction_id: int, user_id: int) -> Optional[Transaction]:
        """Get transaction by ID (user must own it unless admin)"""
        return self.db.query(Transaction).filter(
            and_(
                Transaction.id == transaction_id,
                Transaction.user_id == user_id
            )
        ).first()
    
    async def get_transaction_by_internal_id(self, internal_tran_id: str) -> Optional[Transaction]:
        """Get transaction by internal transaction ID"""
        return self.db.query(Transaction).filter(
            Transaction.internal_tran_id == internal_tran_id
        ).first()
    
    async def list_user_transactions(
        self,
        user_id: int,
        page: int = 1,
        size: int = 20,
        status_filter: Optional[str] = None,
        currency_filter: Optional[str] = None
    ) -> Tuple[List[Transaction], int]:
        """List user's transactions with pagination and filtering"""
        query = self.db.query(Transaction).filter(Transaction.user_id == user_id)
        
        # Apply filters
        if status_filter:
            query = query.filter(Transaction.status == status_filter)
        
        if currency_filter:
            query = query.filter(Transaction.requested_foreign_currency == currency_filter.upper())
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        transactions = query.order_by(desc(Transaction.created_at)).offset(
            (page - 1) * size
        ).limit(size).all()
        
        return transactions, total
    
    async def update_transaction_status(
        self,
        transaction_id: int,
        new_status: str,
        changed_by: int,
        change_reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Transaction:
        """Update transaction status with history tracking"""
        transaction = self.db.query(Transaction).filter(
            Transaction.id == transaction_id
        ).first()
        
        if not transaction:
            raise ValidationError("Transaction not found")
        
        old_status = transaction.status
        
        # Validate status transition
        if not self._is_valid_status_transition(old_status, new_status):
            raise ValidationError(f"Invalid status transition: {old_status} -> {new_status}")
        
        # Update transaction
        transaction.status = new_status
        
        # Update timestamps based on status
        if new_status == "BDT_RECEIVED":
            transaction.bdt_received_at = datetime.utcnow()
        elif new_status == "PROCESSING":
            transaction.payout_initiated_at = datetime.utcnow()
        elif new_status == "COMPLETED":
            transaction.completed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(transaction)
        
        # Log status change
        await self._log_status_change(
            transaction_id=transaction_id,
            old_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
            change_reason=change_reason,
            metadata=metadata
        )
        
        logger.info(f"Transaction {transaction.internal_tran_id} status updated: {old_status} -> {new_status}")
        return transaction
    
    async def cancel_transaction(
        self,
        transaction_id: int,
        user_id: int,
        cancelled_by: int
    ) -> Transaction:
        """Cancel a transaction and refund limits"""
        transaction = await self.get_transaction_by_id(transaction_id, user_id)
        
        if not transaction:
            raise ValidationError("Transaction not found")
        
        if transaction.status not in ["PENDING"]:
            raise ValidationError(f"Cannot cancel transaction with status: {transaction.status}")
        
        # Update status to cancelled
        updated_transaction = await self.update_transaction_status(
            transaction_id=transaction_id,
            new_status="CANCELLED",
            changed_by=cancelled_by,
            change_reason="Cancelled by user"
        )
        
        # Refund payment limits
        await self.limit_service.update_limit_usage(
            user_id=user_id,
            currency_code=transaction.requested_foreign_currency,
            amount=transaction.requested_foreign_amount,
            operation="subtract"
        )
        
        return updated_transaction
    
    async def get_transaction_history(
        self,
        user_id: int,
        page: int = 1,
        size: int = 20,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status_filter: Optional[str] = None,
        currency_filter: Optional[str] = None
    ) -> Tuple[List[Transaction], int]:
        """Get user's transaction history with advanced filtering"""
        query = self.db.query(Transaction).filter(Transaction.user_id == user_id)
        
        # Apply date range filter
        if start_date:
            query = query.filter(Transaction.created_at >= start_date)
        if end_date:
            query = query.filter(Transaction.created_at <= end_date)
        
        # Apply status filter
        if status_filter:
            query = query.filter(Transaction.status == status_filter)
        
        # Apply currency filter
        if currency_filter:
            query = query.filter(Transaction.requested_foreign_currency == currency_filter.upper())
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        transactions = query.order_by(desc(Transaction.created_at)).offset(
            (page - 1) * size
        ).limit(size).all()
        
        return transactions, total
    
    async def get_recent_transactions(self, user_id: int, limit: int = 10) -> List[Transaction]:
        """Get user's most recent transactions"""
        return self.db.query(Transaction).filter(
            Transaction.user_id == user_id
        ).order_by(desc(Transaction.created_at)).limit(limit).all()
    
    async def get_user_transaction_stats(self, user_id: int) -> TransactionStats:
        """Get user's transaction statistics"""
        transactions = self.db.query(Transaction).filter(Transaction.user_id == user_id).all()
        
        total_transactions = len(transactions)
        completed_transactions = len([t for t in transactions if t.status == "COMPLETED"])
        pending_transactions = len([t for t in transactions if t.status == "PENDING"])
        failed_transactions = len([t for t in transactions if t.status == "FAILED"])
        
        total_volume_bdt = sum(t.total_bdt_amount for t in transactions if t.status == "COMPLETED")
        total_volume_foreign = sum(t.requested_foreign_amount for t in transactions if t.status == "COMPLETED")
        
        average_transaction_size = (
            total_volume_foreign / completed_transactions if completed_transactions > 0 else 0
        )
        
        return TransactionStats(
            total_transactions=total_transactions,
            completed_transactions=completed_transactions,
            pending_transactions=pending_transactions,
            failed_transactions=failed_transactions,
            total_volume_bdt=Decimal(str(total_volume_bdt)),
            total_volume_foreign=Decimal(str(total_volume_foreign)),
            average_transaction_size=Decimal(str(average_transaction_size))
        )
    
    async def get_transaction_stats_by_period(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> TransactionStats:
        """Get transaction statistics for a specific period"""
        transactions = self.db.query(Transaction).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.created_at >= start_date,
                Transaction.created_at <= end_date
            )
        ).all()
        
        total_transactions = len(transactions)
        completed_transactions = len([t for t in transactions if t.status == "COMPLETED"])
        pending_transactions = len([t for t in transactions if t.status == "PENDING"])
        failed_transactions = len([t for t in transactions if t.status == "FAILED"])
        
        total_volume_bdt = sum(t.total_bdt_amount for t in transactions if t.status == "COMPLETED")
        total_volume_foreign = sum(t.requested_foreign_amount for t in transactions if t.status == "COMPLETED")
        
        average_transaction_size = (
            total_volume_foreign / completed_transactions if completed_transactions > 0 else 0
        )
        
        return TransactionStats(
            total_transactions=total_transactions,
            completed_transactions=completed_transactions,
            pending_transactions=pending_transactions,
            failed_transactions=failed_transactions,
            total_volume_bdt=Decimal(str(total_volume_bdt)),
            total_volume_foreign=Decimal(str(total_volume_foreign)),
            average_transaction_size=Decimal(str(average_transaction_size))
        )
    
    async def export_transaction_history(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        format: str = "csv"
    ) -> Dict[str, Any]:
        """Export transaction history in specified format"""
        transactions, _ = await self.get_transaction_history(
            user_id=user_id,
            page=1,
            size=10000,  # Large limit for export
            start_date=start_date,
            end_date=end_date
        )
        
        if format == "json":
            return {
                "format": "json",
                "data": [t.to_dict() for t in transactions],
                "exported_at": datetime.utcnow().isoformat(),
                "total_records": len(transactions)
            }
        
        # For CSV and PDF, return metadata for file generation
        return {
            "format": format,
            "export_id": str(uuid.uuid4()),
            "total_records": len(transactions),
            "exported_at": datetime.utcnow().isoformat(),
            "download_url": f"/api/v1/history/download/{str(uuid.uuid4())}"
        }
    
    async def initiate_payment_process(self, transaction_id: int):
        """Background task to initiate payment process"""
        try:
            # This would typically call the payment service
            # For now, we'll just log it
            logger.info(f"Initiating payment process for transaction {transaction_id}")
            
            # In a real implementation, this would:
            # 1. Call payment service to create SSLCommerz session
            # 2. Send notification to user
            # 3. Set up monitoring for payment completion
            
        except Exception as e:
            logger.error(f"Failed to initiate payment process for transaction {transaction_id}: {e}")
    
    def _is_valid_status_transition(self, old_status: str, new_status: str) -> bool:
        """Validate if status transition is allowed"""
        valid_transitions = {
            "PENDING": ["BDT_RECEIVED", "FAILED", "CANCELLED"],
            "BDT_RECEIVED": ["PROCESSING", "FAILED"],
            "PROCESSING": ["COMPLETED", "FAILED"],
            "COMPLETED": ["REFUNDED"],
            "FAILED": ["PENDING"],  # Allow retry
            "CANCELLED": [],
            "REFUNDED": []
        }
        
        return new_status in valid_transitions.get(old_status, [])
    
    async def _log_status_change(
        self,
        transaction_id: int,
        old_status: Optional[str],
        new_status: str,
        changed_by: int,
        change_reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log transaction status change"""
        try:
            status_history = TransactionStatusHistory(
                transaction_id=transaction_id,
                old_status=old_status,
                new_status=new_status,
                changed_by=changed_by,
                change_reason=change_reason,
                metadata=metadata
            )
            
            self.db.add(status_history)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log status change: {e}")
