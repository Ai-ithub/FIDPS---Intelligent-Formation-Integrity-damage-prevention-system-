"""
Database Connection Retry Utilities
Provides retry logic with exponential backoff for database connections
"""

import asyncio
import logging
from typing import Callable, Any, Optional
from functools import wraps
import time

logger = logging.getLogger(__name__)

class RetryConfig:
    """Configuration for retry logic"""
    def __init__(
        self,
        max_attempts: int = 5,
        initial_wait: float = 1.0,
        max_wait: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.initial_wait = initial_wait
        self.max_wait = max_wait
        self.exponential_base = exponential_base
        self.jitter = jitter

def get_retry_config() -> RetryConfig:
    """Get retry configuration from environment variables"""
    import os
    return RetryConfig(
        max_attempts=int(os.getenv("DB_CONNECTION_RETRY_ATTEMPTS", "5")),
        initial_wait=float(os.getenv("DB_CONNECTION_RETRY_WAIT_SECONDS", "5")),
        max_wait=60.0,
        exponential_base=2.0,
        jitter=True
    )

async def retry_async(
    func: Callable,
    *args,
    config: Optional[RetryConfig] = None,
    exception_types: tuple = (Exception,),
    **kwargs
) -> Any:
    """
    Retry an async function with exponential backoff
    
    Args:
        func: Async function to retry
        *args: Positional arguments for func
        config: Retry configuration (uses default if None)
        exception_types: Tuple of exception types to catch and retry
        **kwargs: Keyword arguments for func
    
    Returns:
        Result of func if successful
    
    Raises:
        Last exception if all retries fail
    """
    if config is None:
        config = get_retry_config()
    
    last_exception = None
    wait_time = config.initial_wait
    
    for attempt in range(config.max_attempts):
        try:
            return await func(*args, **kwargs)
        except exception_types as e:
            last_exception = e
            if attempt < config.max_attempts - 1:  # Don't wait after last attempt
                if config.jitter:
                    # Add random jitter to prevent thundering herd
                    import random
                    jitter = random.uniform(0, wait_time * 0.1)
                    actual_wait = wait_time + jitter
                else:
                    actual_wait = wait_time
                
                logger.warning(
                    f"Attempt {attempt + 1}/{config.max_attempts} failed: {str(e)}. "
                    f"Retrying in {actual_wait:.2f} seconds..."
                )
                await asyncio.sleep(actual_wait)
                
                # Exponential backoff
                wait_time = min(
                    wait_time * config.exponential_base,
                    config.max_wait
                )
            else:
                logger.error(
                    f"All {config.max_attempts} attempts failed. Last error: {str(e)}"
                )
    
    # All retries failed
    raise last_exception

def retry_sync(
    func: Callable,
    *args,
    config: Optional[RetryConfig] = None,
    exception_types: tuple = (Exception,),
    **kwargs
) -> Any:
    """
    Retry a synchronous function with exponential backoff
    
    Args:
        func: Synchronous function to retry
        *args: Positional arguments for func
        config: Retry configuration (uses default if None)
        exception_types: Tuple of exception types to catch and retry
        **kwargs: Keyword arguments for func
    
    Returns:
        Result of func if successful
    
    Raises:
        Last exception if all retries fail
    """
    if config is None:
        config = get_retry_config()
    
    last_exception = None
    wait_time = config.initial_wait
    
    for attempt in range(config.max_attempts):
        try:
            return func(*args, **kwargs)
        except exception_types as e:
            last_exception = e
            if attempt < config.max_attempts - 1:  # Don't wait after last attempt
                if config.jitter:
                    # Add random jitter to prevent thundering herd
                    import random
                    jitter = random.uniform(0, wait_time * 0.1)
                    actual_wait = wait_time + jitter
                else:
                    actual_wait = wait_time
                
                logger.warning(
                    f"Attempt {attempt + 1}/{config.max_attempts} failed: {str(e)}. "
                    f"Retrying in {actual_wait:.2f} seconds..."
                )
                time.sleep(actual_wait)
                
                # Exponential backoff
                wait_time = min(
                    wait_time * config.exponential_base,
                    config.max_wait
                )
            else:
                logger.error(
                    f"All {config.max_attempts} attempts failed. Last error: {str(e)}"
                )
    
    # All retries failed
    raise last_exception

def retry_decorator(
    config: Optional[RetryConfig] = None,
    exception_types: tuple = (Exception,)
):
    """
    Decorator for retrying async functions
    
    Usage:
        @retry_decorator()
        async def my_function():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_async(
                func,
                *args,
                config=config,
                exception_types=exception_types,
                **kwargs
            )
        return wrapper
    return decorator

