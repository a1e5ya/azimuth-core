import os
import re
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from ..models.database import get_db, User, AuditLog

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 60  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer for token extraction
security = HTTPBearer()

# FIXED: Optional security that doesn't raise exceptions
security_optional = HTTPBearer(auto_error=False)

# Pydantic models
class UserCreate(BaseModel):
    email: str
    password: str
    display_name: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    display_name: Optional[str]
    created_at: str

# Utility functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email"""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password"""
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)"
    
    return True, "Password is valid"

async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """Create a new user with password validation"""
    # Validate password strength
    is_valid, error_message = validate_password(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    
    # Check if user already exists
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        display_name=user_data.display_name
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get current user from JWT token, but allow None for anonymous access"""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        
        user = await get_user_by_email(db, email=email)
        return user
    except JWTError:
        return None

async def log_auth_event(
    db: AsyncSession,
    action: str,
    email: str,
    success: bool,
    user_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
):
    """Log authentication events"""
    audit_entry = AuditLog(
        user_id=user_id,
        entity="auth",
        action=action,
        details={
            "email": email,
            "success": success,
            **(details or {})
        }
    )
    
    db.add(audit_entry)
    await db.commit()

# Authentication service class
class LocalAuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def register(self, user_data: UserCreate) -> Dict[str, Any]:
        """Register a new user"""
        try:
            user = await create_user(self.db, user_data)
            
            # Create access token
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user.email}, expires_delta=access_token_expires
            )
            
            # Log successful registration
            await log_auth_event(
                self.db, "register", user.email, True,
                user_id=user.id,
                details={"user_id": user.id}
            )
            
            return {
                "success": True,
                "access_token": access_token,
                "token_type": "bearer",
                "user": UserResponse(
                    id=user.id,
                    email=user.email,
                    display_name=user.display_name,
                    created_at=user.created_at.isoformat()
                )
            }
        except HTTPException as e:
            # Log failed registration
            print(f"❌ Registration HTTPException: {e.detail}")
            await log_auth_event(
                self.db, "register", user_data.email, False,
                user_id=None,
                details={"error": str(e.detail)}
            )
            raise e
        except Exception as e:
            # Log unexpected error
            print(f"❌ Registration error: {e}")
            import traceback
            traceback.print_exc()
            await log_auth_event(
                self.db, "register", user_data.email, False,
                user_id=None,
                details={"error": str(e)}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed"
            )
    
    async def login(self, user_data: UserLogin) -> Dict[str, Any]:
        """Login user"""
        print(f"🔍 Login attempt for: {user_data.email}")
        try:
            print(f"   Authenticating...")
            user = await authenticate_user(self.db, user_data.email, user_data.password)
            print(f"   User found: {user is not None}")
            
            if user:
                print(f"   User ID: {user.id}, Email: {user.email}")
            
            if not user:
                # Log failed login
                await log_auth_event(
                    self.db, "login", user_data.email, False,
                    user_id=None,
                    details={"error": "Invalid credentials"}
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # Create access token
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user.email}, expires_delta=access_token_expires
            )
            
            # Log successful login
            await log_auth_event(
                self.db, "login", user.email, True,
                user_id=user.id,
                details={"user_id": user.id}
            )
            
            return {
                "success": True,
                "access_token": access_token,
                "token_type": "bearer",
                "user": UserResponse(
                    id=user.id,
                    email=user.email,
                    display_name=user.display_name,
                    created_at=user.created_at.isoformat()
                )
            }
        except HTTPException as e:
            raise e
        except Exception as e:
            # Log unexpected error
            print(f"❌ Login error: {e}")
            import traceback
            traceback.print_exc()
            await log_auth_event(
                self.db, "login", user_data.email, False,
                user_id=None,
                details={"error": str(e)}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Login failed"
            )

def get_auth_service(db: AsyncSession = Depends(get_db)) -> LocalAuthService:
    """Get authentication service instance"""
    return LocalAuthService(db)