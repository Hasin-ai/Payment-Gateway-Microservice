import logging
import sys
from app.core.config import settings

def setup_logger(name: str) -> logging.Logger:
    """Setup logger with consistent formatting"""
    logger = logging.getLogger(name)
    
    # Set log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        # Console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        
        # Formatter
        if settings.DEBUG:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Prevent propagation to avoid duplicate logs
        logger.propagate = False
    
    return logger
