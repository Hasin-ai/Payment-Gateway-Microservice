class PaymentServiceError(Exception):
    """Base exception for payment service"""
    pass

class PaymentError(PaymentServiceError):
    """Raised when payment operations fail"""
    pass

class ValidationError(PaymentServiceError):
    """Raised when validation fails"""
    pass

class WebhookError(PaymentServiceError):
    """Raised when webhook processing fails"""
    pass

class GatewayError(PaymentServiceError):
    """Raised when external gateway calls fail"""
    pass

class AuthenticationError(PaymentServiceError):
    """Raised when gateway authentication fails"""
    pass
