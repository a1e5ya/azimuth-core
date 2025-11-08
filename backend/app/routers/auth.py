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
from ..services.category_service import CategoryService

router = APIRouter()

# Response Models
class AuthResponse(BaseModel):
    message: str
    success: bool
    user: Optional[UserResponse] = None
    access_token: Optional[str] = None
    token_type: Optional[str] = None

class StatusResponse(BaseModel):
    authenticated: bool
    user: Optional[UserResponse] = None
    message: str

@router.post("/register", response_model=AuthResponse)
async def register_user(
    user_data: UserCreate,
    request: Request,
    auth_service: LocalAuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_db)
):
    """Register a new user with email and password"""
    
    print(f"📝 Registration request for: {user_data.email}")
    
    try:
        result = await auth_service.register(user_data)
        print(f"✅ Registration successful for: {user_data.email}")
        
        # Initialize categories using CategoryService
        try:
            category_service = CategoryService(db, result["user"])
            await category_service.initialize_default_categories()
            print(f"✅ Categories initialized for: {user_data.email}")
        except Exception as cat_error:
            print(f"⚠️ Category initialization failed (non-fatal): {cat_error}")
            traceback.print_exc()
        
        return AuthResponse(
            message="Registration successful",
            success=True,
            user=result["user"],
            access_token=result["access_token"],
            token_type=result["token_type"]
        )
        
    except HTTPException as e:
        print(f"❌ Registration failed with HTTPException: {e.detail}")
        raise e
    except Exception as e:
        print(f"❌ Registration failed with unexpected error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/login", response_model=AuthResponse)
async def login_user(
    user_data: UserLogin,
    request: Request,
    auth_service: LocalAuthService = Depends(get_auth_service)
):
    """Login user with email and password"""
    
    print(f"🔐 Login request for: {user_data.email}")
    
    try:
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
        print(f"❌ Login failed with HTTPException: {e.detail}")
        raise e
    except Exception as e:
        print(f"❌ Login failed with unexpected error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user profile"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
        created_at=current_user.created_at.isoformat()
    )

@router.get("/status", response_model=StatusResponse)
async def get_auth_status(
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Check authentication status"""
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
    """Verify JWT token validity"""
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

@router.post("/logout")
async def logout_user(
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Logout user (client-side token removal)"""
    if current_user:
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
        return {"message": "No active session", "success": True}

@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    auth_service: LocalAuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_db)
):
    """Change user password"""
    if not verify_password(current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    current_user.password_hash = get_password_hash(new_password)
    await db.commit()
    
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

@router.get("/debug")
async def debug_auth(
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Debug endpoint for local authentication testing"""
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