"""
Structured Logging Configuration
Provides structured logging with JSON format for better observability
"""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict
import os

class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data: Dict[str, Any] = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)

def setup_logging(
    log_level: str = None,
    log_format: str = None,
    json_format: bool = None
):
    """
    Setup logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format ('json' or 'text')
        json_format: Enable JSON format (overrides log_format)
    """
    # Get configuration from environment or arguments
    log_level = log_level or os.getenv('LOG_LEVEL', 'INFO').upper()
    log_format = log_format or os.getenv('LOG_FORMAT', 'json').lower()
    json_format = json_format if json_format is not None else (log_format == 'json')
    
    # Set logging level
    numeric_level = getattr(logging, log_level, logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    
    # Set formatter
    if json_format:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Set logging level for third-party libraries
    logging.getLogger('kafka').setLevel(logging.WARNING)
    logging.getLogger('aiokafka').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger with structured logging support"""
    logger = logging.getLogger(name)
    
    # Add method for structured logging
    def log_with_fields(level: int, message: str, **fields):
        """Log with additional structured fields"""
        extra = {'extra_fields': fields}
        logger.log(level, message, extra=extra)
    
    logger.info_fields = lambda msg, **fields: log_with_fields(logging.INFO, msg, **fields)
    logger.warning_fields = lambda msg, **fields: log_with_fields(logging.WARNING, msg, **fields)
    logger.error_fields = lambda msg, **fields: log_with_fields(logging.ERROR, msg, **fields)
    logger.debug_fields = lambda msg, **fields: log_with_fields(logging.DEBUG, msg, **fields)
    
    return logger

