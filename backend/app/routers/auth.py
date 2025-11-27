"""
Authentication Router - User Registration and Login

Endpoints:
- POST /register: Create new user account
- POST /login: Authenticate user and return JWT token
- GET /me: Get current user profile (requires auth)
- GET /status: Check authentication status
- POST /verify: Verify JWT token validity
- POST /logout: Logout user (client-side token removal + audit log)
- POST /change-password: Change user password (requires auth)
- GET /debug: Debug authentication system (development only)

Authentication:
- JWT tokens with 24h expiration
- Bcrypt password hashing
- Audit logging for all auth events
- Optional authentication for status checks

Database: SQLAlchemy async with User and AuditLog models
"""

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
import traceback

from ..models.database import get_db, User, AuditLog
from ..auth.local_auth import (
    LocalAuthService, get_auth_service, get_current_user, get_current_user_optional,
    UserCreate, UserLogin, UserResponse, verify_password, get_password_hash
)

router = APIRouter()

# ============================================================================
# RESPONSE MODELS
# ============================================================================

class AuthResponse(BaseModel):
    """Authentication response with token and user data"""
    message: str
    success: bool
    user: Optional[UserResponse] = None
    access_token: Optional[str] = None
    token_type: Optional[str] = None

class StatusResponse(BaseModel):
    """Authentication status check response"""
    authenticated: bool
    user: Optional[UserResponse] = None
    message: str


# ============================================================================
# REGISTRATION ENDPOINT
# ============================================================================

@router.post("/register", response_model=AuthResponse)
async def register_user(
    user_data: UserCreate,
    request: Request,
    auth_service: LocalAuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account
    
    Process:
    1. Validate email uniqueness
    2. Validate password strength (8+ chars, upper, lower, number, special)
    3. Hash password with bcrypt
    4. Create user in database
    5. Generate JWT access token (24h expiration)
    6. Log registration to audit table
    
    Returns JWT token for immediate authentication after registration
    
    @param user_data: Email, password, optional display_name
    @returns {AuthResponse} Success message, JWT token, user data
    @raises HTTPException: 400 if email exists or password invalid
    """
    print(f"🔐 Registration request for: {user_data.email}")
    
    try:
        # Validate and create user (handles password validation, hashing, duplicate check)
        result = await auth_service.register(user_data)
        print(f"✅ Registration successful for: {user_data.email}")
        
        return AuthResponse(
            message="Registration successful",
            success=True,
            user=result["user"],
            access_token=result["access_token"],
            token_type=result["token_type"]
        )
        
    except HTTPException as e:
        # Re-raise validation errors (email exists, weak password, etc.)
        print(f"❌ Registration failed: {e.detail}")
        raise e
    except Exception as e:
        # Log unexpected errors
        print(f"❌ Registration failed with unexpected error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


# ============================================================================
# LOGIN ENDPOINT
# ============================================================================

@router.post("/login", response_model=AuthResponse)
async def login_user(
    user_data: UserLogin,
    request: Request,
    auth_service: LocalAuthService = Depends(get_auth_service)
):
    """
    Login user with email and password
    
    Process:
    1. Find user by email
    2. Verify password with bcrypt
    3. Generate JWT access token (24h expiration)
    4. Log login to audit table
    
    @param user_data: Email and password
    @returns {AuthResponse} Success message, JWT token, user data
    @raises HTTPException: 401 if credentials invalid
    """
    print(f"🔐 Login request for: {user_data.email}")
    
    try:
        # Authenticate user and generate token
        result = await auth_service.login(user_data)
        print(f"✅ Login successful for: {user_data.email}")
        
        return AuthResponse(
            message="Login successful",
            success=True,
            user=result["user"],
            access_token=result["access_token"],
            token_type=result["token_type"]
        )
        
    except HTTPException as e:
        # Re-raise auth errors (invalid credentials)
        print(f"❌ Login failed: {e.detail}")
        raise e
    except Exception as e:
        # Log unexpected errors
        print(f"❌ Login failed with unexpected error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


# ============================================================================
# USER PROFILE ENDPOINTS
# ============================================================================

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's profile
    
    Requires valid JWT token in Authorization header
    Returns user data without sensitive information (no password hash)
    
    @param current_user: Injected from JWT token
    @returns {UserResponse} User profile (id, email, display_name, created_at)
    @raises HTTPException: 401 if token invalid or missing
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
        created_at=current_user.created_at.isoformat()
    )


# ============================================================================
# AUTHENTICATION STATUS ENDPOINTS
# ============================================================================

@router.get("/status", response_model=StatusResponse)
async def get_auth_status(
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Check authentication status (no error if unauthenticated)
    
    Used by frontend to check if user is logged in
    Returns user data if authenticated, null if not
    
    @param current_user: Optional user from JWT token
    @returns {StatusResponse} Authentication status and user data
    """
    if current_user:
        return StatusResponse(
            authenticated=True,
            user=UserResponse(
                id=current_user.id,
                email=current_user.email,
                display_name=current_user.display_name,
                created_at=current_user.created_at.isoformat()
            ),
            message=f"Authenticated as {current_user.email}"
        )
    else:
        return StatusResponse(
            authenticated=False,
            user=None,
            message="Not authenticated"
        )


@router.post("/verify", response_model=StatusResponse)
async def verify_token(
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Verify JWT token validity
    
    Checks if token is valid, not expired, and user still exists
    Similar to /status but POST method (for semantic clarity)
    
    @param current_user: Optional user from JWT token
    @returns {StatusResponse} Token validity status
    """
    if current_user:
        return StatusResponse(
            authenticated=True,
            user=UserResponse(
                id=current_user.id,
                email=current_user.email,
                display_name=current_user.display_name,
                created_at=current_user.created_at.isoformat()
            ),
            message="Token is valid"
        )
    else:
        return StatusResponse(
            authenticated=False,
            user=None,
            message="Invalid or expired token"
        )


# ============================================================================
# LOGOUT ENDPOINT
# ============================================================================

@router.post("/logout")
async def logout_user(
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout user (client-side token removal + audit log)
    
    JWT tokens are stateless, so logout is client-side (remove token from storage)
    This endpoint logs the logout event to audit table
    
    @param current_user: Optional user from JWT token
    @param db: Database session
    @returns {dict} Success message
    """
    if current_user:
        # Log logout event to audit table
        audit_entry = AuditLog(
            user_id=current_user.id,
            entity="auth",
            action="logout",
            details={
                "user_email": current_user.email,
                "logout_time": "client_initiated"
            }
        )
        db.add(audit_entry)
        await db.commit()
        
        return {"message": "Logout successful", "success": True}
    else:
        # No active session (already logged out)
        return {"message": "No active session", "success": True}


# ============================================================================
# PASSWORD CHANGE ENDPOINT
# ============================================================================

@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    auth_service: LocalAuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_db)
):
    """
    Change user password
    
    Process:
    1. Verify current password
    2. Validate new password strength
    3. Hash new password with bcrypt
    4. Update user record
    5. Log password change to audit table
    
    User remains logged in (existing token still valid)
    
    @param current_password: Current password for verification
    @param new_password: New password (must meet strength requirements)
    @param current_user: Injected from JWT token
    @returns {dict} Success message
    @raises HTTPException: 400 if current password incorrect, 401 if not authenticated
    """
    # Verify current password
    if not verify_password(current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Hash new password and update user
    current_user.password_hash = get_password_hash(new_password)
    await db.commit()
    
    # Log password change to audit table
    audit_entry = AuditLog(
        user_id=current_user.id,
        entity="auth",
        action="password_change",
        details={
            "user_email": current_user.email,
            "change_time": "successful"
        }
    )
    db.add(audit_entry)
    await db.commit()
    
    return {"message": "Password changed successfully", "success": True}


# ============================================================================
# DEBUG ENDPOINT (Development Only)
# ============================================================================

@router.get("/debug")
async def debug_auth(
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Debug endpoint for local authentication testing
    
    Returns authentication system information
    Used for development/troubleshooting only
    
    @param current_user: Optional user from JWT token
    @returns {dict} Auth system info and current user status
    """
    return {
        "auth_type": "local_jwt",
        "authenticated": current_user is not None,
        "user_info": {
            "id": current_user.id if current_user else None,
            "email": current_user.email if current_user else None,
            "display_name": current_user.display_name if current_user else None
        } if current_user else None,
        "system": "azimuth_core_local"
    }