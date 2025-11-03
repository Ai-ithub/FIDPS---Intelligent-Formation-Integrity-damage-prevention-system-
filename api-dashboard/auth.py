"""
JWT Authentication Module for FIDPS API
Provides authentication and authorization for API endpoints
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import os
import logging

logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE_THIS_TO_A_RANDOM_SECRET_KEY_MIN_32_CHARS")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token
security = HTTPBearer()

# User roles
class UserRole(str):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"
    ENGINEER = "engineer"

# Pydantic models
class User(BaseModel):
    username: str
    email: Optional[str] = None
    role: str = UserRole.VIEWER
    disabled: bool = False

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

# In-memory user store (replace with database in production)
# Default users for development
fake_users_db = {
    "admin": {
        "username": "admin",
        "email": "admin@fidps.com",
        "hashed_password": pwd_context.hash("admin123"),  # Change in production!
        "role": UserRole.ADMIN,
        "disabled": False
    },
    "operator": {
        "username": "operator",
        "email": "operator@fidps.com",
        "hashed_password": pwd_context.hash("operator123"),  # Change in production!
        "role": UserRole.OPERATOR,
        "disabled": False
    },
    "viewer": {
        "username": "viewer",
        "email": "viewer@fidps.com",
        "hashed_password": pwd_context.hash("viewer123"),  # Change in production!
        "role": UserRole.VIEWER,
        "disabled": False
    }
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def get_user(username: str) -> Optional[dict]:
    """Get user from database (in-memory for now)"""
    return fake_users_db.get(username)

def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate a user"""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    if user.get("disabled", False):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, role=payload.get("role"))
    except JWTError:
        raise credentials_exception
    
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    
    return User(
        username=user["username"],
        email=user.get("email"),
        role=user["role"],
        disabled=user.get("disabled", False)
    )

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user (not disabled)"""
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

def require_role(allowed_roles: list[str]):
    """Dependency to check if user has required role"""
    async def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker

# Role-based dependencies
RequireAdmin = Depends(require_role([UserRole.ADMIN]))
RequireOperator = Depends(require_role([UserRole.ADMIN, UserRole.OPERATOR, UserRole.ENGINEER]))
RequireEngineer = Depends(require_role([UserRole.ADMIN, UserRole.ENGINEER]))
RequireAny = Depends(get_current_active_user)  # Any authenticated user

