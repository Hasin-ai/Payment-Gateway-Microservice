import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict

from app.core.config import settings

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.failure_threshold = settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD
        self.reset_timeout = settings.CIRCUIT_BREAKER_RESET_TIMEOUT
        
        self.failure_count = 0
        self.last_failure_time: datetime = None
        self.state = CircuitState.CLOSED
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker"""
        if not settings.CIRCUIT_BREAKER_ENABLED:
            return await func(*args, **kwargs)
        
        async with self._lock:
            # Check if circuit should be reset
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info(f"Circuit breaker for {self.service_name} moved to HALF_OPEN")
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker for {self.service_name} is OPEN"
                    )
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise
    
    async def _on_success(self):
        """Handle successful call"""
        async with self._lock:
            self.failure_count = 0
            self.last_failure_time = None
            
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                logger.info(f"Circuit breaker for {self.service_name} moved to CLOSED")
    
    async def _on_failure(self):
        """Handle failed call"""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()
            
            if self.failure_count >= self.failure_threshold:
                if self.state != CircuitState.OPEN:
                    self.state = CircuitState.OPEN
                    logger.warning(
                        f"Circuit breaker for {self.service_name} moved to OPEN "
                        f"after {self.failure_count} failures"
                    )
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if not self.last_failure_time:
            return True
        
        time_since_failure = datetime.utcnow() - self.last_failure_time
        return time_since_failure >= timedelta(seconds=self.reset_timeout)
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        return {
            "service": self.service_name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "reset_timeout": self.reset_timeout
        }

class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open"""
    pass
