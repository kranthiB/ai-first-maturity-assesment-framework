"""
Logging configuration and utilities for the AFS Assessment Framework.
"""

import logging
import sys
from typing import Optional


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Set level
    if level:
        logger.setLevel(getattr(logging, level.upper()))
    elif not logger.handlers:
        logger.setLevel(logging.INFO)
    
    # Add handler if none exists
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(name)s: %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


def setup_application_logging(app):
    """
    Setup application-wide logging configuration.
    
    Args:
        app: Flask application instance
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Configure application logger
    app_logger = get_logger('app')
    app.logger.handlers = app_logger.handlers
    app.logger.setLevel(app_logger.level)