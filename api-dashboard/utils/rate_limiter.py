"""
Rate Limiting Utilities
Provides rate limiting for API endpoints to prevent DDoS attacks
"""

from typing import Optional
from fastapi import HTTPException, Request, status
from functools import wraps
import time
import logging
import os

logger = logging.getLogger(__name__)

# Rate limit configuration
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))

# In-memory rate limit store (use Redis in production for distributed systems)
_rate_limit_store = {}
_rate_limit_lock = {}

def get_client_identifier(request: Request) -> str:
    """Get client identifier for rate limiting"""
    # Try to get IP from various headers
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Get first IP if there's a chain
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # Fallback to direct client IP
    if request.client:
        return request.client.host
    
    return "unknown"

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, per_minute: int = RATE_LIMIT_PER_MINUTE, per_hour: int = RATE_LIMIT_PER_HOUR):
        self.per_minute = per_minute
        self.per_hour = per_hour
    
    def check_rate_limit(self, client_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if client has exceeded rate limit
        
        Returns:
            (allowed, error_message)
        """
        current_time = time.time()
        
        if client_id not in _rate_limit_store:
            _rate_limit_store[client_id] = {
                "minute": [],
                "hour": []
            }
        
        client_data = _rate_limit_store[client_id]
        
        # Clean old entries (older than 1 hour)
        client_data["hour"] = [
            timestamp for timestamp in client_data["hour"]
            if current_time - timestamp < 3600
        ]
        
        # Clean old entries (older than 1 minute)
        client_data["minute"] = [
            timestamp for timestamp in client_data["minute"]
            if current_time - timestamp < 60
        ]
        
        # Check hourly limit
        if len(client_data["hour"]) >= self.per_hour:
            return False, f"Rate limit exceeded: {self.per_hour} requests per hour"
        
        # Check minute limit
        if len(client_data["minute"]) >= self.per_minute:
            return False, f"Rate limit exceeded: {self.per_minute} requests per minute"
        
        # Add current request
        client_data["hour"].append(current_time)
        client_data["minute"].append(current_time)
        
        return True, None

# Global rate limiter instance
_rate_limiter = RateLimiter()

def rate_limit(
    per_minute: Optional[int] = None,
    per_hour: Optional[int] = None
):
    """
    Decorator for rate limiting endpoints
    
    Usage:
        @router.get("/endpoint")
        @rate_limit(per_minute=30, per_hour=500)
        async def my_endpoint(request: Request):
            ...
    """
    def decorator(func):
        limiter = RateLimiter(
            per_minute=per_minute or RATE_LIMIT_PER_MINUTE,
            per_hour=per_hour or RATE_LIMIT_PER_HOUR
        )
        
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            client_id = get_client_identifier(request)
            allowed, error_msg = limiter.check_rate_limit(client_id)
            
            if not allowed:
                logger.warning(f"Rate limit exceeded for client {client_id}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=error_msg,
                    headers={"Retry-After": "60"}
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator

# Simplified rate limit dependency for FastAPI
from fastapi import Depends

def get_rate_limiter():
    """Dependency to get rate limiter"""
    return _rate_limiter

async def check_rate_limit(
    request: Request,
    limiter: RateLimiter = Depends(get_rate_limiter)
):
    """Dependency to check rate limit"""
    client_id = get_client_identifier(request)
    allowed, error_msg = limiter.check_rate_limit(client_id)
    
    if not allowed:
        logger.warning(f"Rate limit exceeded for client {client_id}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_msg,
            headers={"Retry-After": "60"}
        )
    
    return True

