class NotificationServiceError(Exception):
    """Base exception for notification service"""
    pass

class NotificationError(NotificationServiceError):
    """Raised when notification operations fail"""
    pass

class TemplateError(NotificationServiceError):
    """Raised when template operations fail"""
    pass

class ChannelError(NotificationServiceError):
    """Raised when channel-specific operations fail"""
    pass

class ValidationError(NotificationServiceError):
    """Raised when validation fails"""
    pass
