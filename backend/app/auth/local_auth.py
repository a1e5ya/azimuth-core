"""
Local Authentication System - JWT-based User Authentication

Handles:
- User registration with password validation
- Login with email/password
- JWT token generation and verification
- Password hashing with bcrypt
- Audit logging for auth events

Security:
- Bcrypt password hashing (cost factor 12)
- JWT tokens with 24h expiration
- Password requirements: 8+ chars, uppercase, lowercase, number, special char
- HTTP Bearer token authentication

Database: SQLAlchemy async (User model)
Token: JWT with HS256 algorithm
"""

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

# ============================================================================
# JWT CONFIGURATION
# ============================================================================
# Secret key for signing tokens (generated if not in env)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 60  # 24 hours

# ============================================================================
# PASSWORD HASHING CONFIGURATION
# ============================================================================
# Using bcrypt with default cost factor (12 rounds)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ============================================================================
# HTTP BEARER TOKEN EXTRACTORS
# ============================================================================
# Required authentication - raises 401 if missing
security = HTTPBearer()

# Optional authentication - returns None if missing (no error)
security_optional = HTTPBearer(auto_error=False)

# ============================================================================
# PYDANTIC MODELS FOR API REQUESTS/RESPONSES
# ============================================================================

class UserCreate(BaseModel):
    """User registration request"""
    email: str
    password: str
    display_name: Optional[str] = None

class UserLogin(BaseModel):
    """User login request"""
    email: str
    password: str

class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Decoded JWT token data"""
    email: Optional[str] = None

class UserResponse(BaseModel):
    """User profile response (no sensitive data)"""
    id: str
    email: str
    display_name: Optional[str]
    created_at: str


# ============================================================================
# PASSWORD UTILITIES
# ============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its bcrypt hash
    
    Uses constant-time comparison to prevent timing attacks
    
    @param plain_password: User-provided password
    @param hashed_password: Stored bcrypt hash from database
    @returns {bool} True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Generate bcrypt hash for password
    
    Uses bcrypt with cost factor 12 (secure but fast enough for UX)
    
    @param password: Plain text password
    @returns {str} Bcrypt hash string
    """
    return pwd_context.hash(password)


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength requirements
    
    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character (!@#$%^&*(),.?":{}|<>)
    
    @param password: Password to validate
    @returns {tuple} (is_valid: bool, error_message: str)
    """
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


# ============================================================================
# JWT TOKEN MANAGEMENT
# ============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create a JWT access token
    
    Encodes user data (typically email) into a signed JWT token
    Token includes expiration timestamp (24h default)
    
    @param data: Payload to encode (e.g., {"sub": user_email})
    @param expires_delta: Custom expiration time (optional)
    @returns {str} Signed JWT token string
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Sign and encode token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# ============================================================================
# DATABASE USER OPERATIONS
# ============================================================================

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Retrieve user from database by email
    
    @param db: Database session
    @param email: User email address
    @returns {User|None} User object or None if not found
    """
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """
    Authenticate user credentials
    
    Process:
    1. Find user by email
    2. Verify password hash
    3. Return user if valid, None otherwise
    
    @param db: Database session
    @param email: User email
    @param password: Plain text password
    @returns {User|None} Authenticated user or None
    """
    user = await get_user_by_email(db, email)
    if not user:
        return None
    
    if not verify_password(password, user.password_hash):
        return None
    
    return user


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """
    Create new user in database
    
    Process:
    1. Validate password strength
    2. Check for existing email
    3. Hash password
    4. Create user record
    
    Raises HTTPException on validation failure
    
    @param db: Database session
    @param user_data: User registration data
    @returns {User} Created user object
    """
    # Validate password strength
    is_valid, error_message = validate_password(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    
    # Check if email already exists
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user with hashed password
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


# ============================================================================
# TOKEN VERIFICATION & USER EXTRACTION
# ============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Extract and verify current user from JWT token (REQUIRED)
    
    Used for protected endpoints that require authentication
    Raises 401 Unauthorized if token is invalid or missing
    
    Process:
    1. Extract token from Authorization header
    2. Decode and verify JWT signature
    3. Extract email from token payload
    4. Load user from database
    
    @param credentials: HTTP Bearer token from header
    @param db: Database session
    @returns {User} Authenticated user
    @raises HTTPException: 401 if authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        
        # Decode JWT token (verifies signature and expiration)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        
        if email is None:
            raise credentials_exception
            
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    # Load user from database
    user = await get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Extract current user from JWT token (OPTIONAL)
    
    Used for endpoints that work both authenticated and anonymous
    Returns None if no token provided (no error raised)
    
    @param credentials: HTTP Bearer token (optional)
    @param db: Database session
    @returns {User|None} Authenticated user or None
    """
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


# ============================================================================
# AUDIT LOGGING
# ============================================================================

async def log_auth_event(
    db: AsyncSession,
    action: str,
    email: str,
    success: bool,
    user_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
):
    """
    Log authentication events to audit table
    
    Logged events: register, login, logout, password_change
    Includes success/failure status and additional details
    
    @param db: Database session
    @param action: Event type (register/login/logout)
    @param email: User email
    @param success: Whether action succeeded
    @param user_id: User ID (if known)
    @param details: Additional event metadata
    """
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


# ============================================================================
# AUTHENTICATION SERVICE CLASS
# ============================================================================

class LocalAuthService:
    """
    High-level authentication service
    
    Handles complete auth workflows:
    - User registration with token generation
    - User login with token generation
    - Audit logging for all auth events
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize auth service
        
        @param db: Database session for user operations
        """
        self.db = db
    
    async def register(self, user_data: UserCreate) -> Dict[str, Any]:
        """
        Register new user and return access token
        
        Process:
        1. Validate and create user (raises HTTPException on error)
        2. Generate JWT access token
        3. Log successful registration
        4. Return token and user data
        
        @param user_data: Registration data (email, password, display_name)
        @returns {dict} {success, access_token, token_type, user}
        @raises HTTPException: On validation errors or duplicate email
        """
        try:
            # Create user in database (validates password and email uniqueness)
            user = await create_user(self.db, user_data)
            
            # Generate JWT access token (24h expiration)
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user.email}, 
                expires_delta=access_token_expires
            )
            
            # Log successful registration to audit table
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
            # Log failed registration (validation error or duplicate email)
            await log_auth_event(
                self.db, "register", user_data.email, False,
                user_id=None,
                details={"error": str(e.detail)}
            )
            raise e
            
        except Exception as e:
            # Log unexpected error
            console.error(f"❌ Registration error: {e}")
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
        """
        Login user and return access token
        
        Process:
        1. Authenticate credentials
        2. Generate JWT token
        3. Log login event
        4. Return token and user data
        
        @param user_data: Login credentials (email, password)
        @returns {dict} {success, access_token, token_type, user}
        @raises HTTPException: 401 if credentials invalid
        """
        try:
            # Verify email and password
            user = await authenticate_user(self.db, user_data.email, user_data.password)
            
            if not user:
                # Log failed login attempt
                await log_auth_event(
                    self.db, "login", user_data.email, False,
                    user_id=None,
                    details={"error": "Invalid credentials"}
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # Generate JWT access token
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user.email}, 
                expires_delta=access_token_expires
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
            console.error(f"❌ Login error: {e}")
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
    """
    Dependency injection for LocalAuthService
    
    Used in FastAPI endpoints:
    @router.post("/register")
    async def register(auth_service: LocalAuthService = Depends(get_auth_service)):
        ...
    
    @param db: Database session (injected by FastAPI)
    @returns {LocalAuthService} Initialized auth service
    """
    return LocalAuthService(db)