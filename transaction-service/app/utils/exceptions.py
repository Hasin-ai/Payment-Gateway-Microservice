class TransactionServiceError(Exception):
    """Base exception for transaction service"""
    pass

class ValidationError(TransactionServiceError):
    """Raised when validation fails"""
    pass

class TransactionError(TransactionServiceError):
    """Raised when transaction operations fail"""
    pass

class LimitExceededError(TransactionServiceError):
    """Raised when payment limits are exceeded"""
    pass

class ExternalServiceError(TransactionServiceError):
    """Raised when external service calls fail"""
    pass

class InsufficientFundsError(TransactionServiceError):
    """Raised when user has insufficient funds"""
    pass

class InvalidStatusTransitionError(TransactionServiceError):
    """Raised when invalid status transition is attempted"""
    pass
