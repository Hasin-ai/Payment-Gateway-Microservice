class ExchangeRateError(Exception):
    """Base exception for exchange rate service"""
    pass

class RateNotFoundError(ExchangeRateError):
    """Raised when exchange rate is not found"""
    pass

class ValidationError(ExchangeRateError):
    """Raised when validation fails"""
    pass

class APIError(ExchangeRateError):
    """Raised when external API calls fail"""
    pass

class CacheError(ExchangeRateError):
    """Raised when cache operations fail"""
    pass
