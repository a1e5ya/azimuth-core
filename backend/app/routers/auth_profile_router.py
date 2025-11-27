"""
Authentication Profile Router - User Profile Management

Endpoints:
- PUT /auth/profile: Update user profile (display_name, email, currency, locale)

Features:
- Update user profile information
- Email uniqueness validation
- Requires authentication (JWT token)

Database: SQLAlchemy async with User model
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from ..models.database import get_db, User
from ..auth.local_auth import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

# ============================================================================
# REQUEST MODELS
# ============================================================================

class ProfileUpdate(BaseModel):
    """User profile update request"""
    display_name: str
    email: str
    currency: str = "EUR"
    locale: str = "en-US"


# ============================================================================
# PROFILE UPDATE ENDPOINT
# ============================================================================

@router.put("/profile")
async def update_profile(
    profile: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update user profile information
    
    Allows updating:
    - display_name: User's display name
    - email: User's email (must be unique)
    - currency: Preferred currency (default: EUR)
    - locale: Preferred locale (default: en-US)
    
    Process:
    1. Validate email uniqueness (if changed)
    2. Update user fields
    3. Commit to database
    4. Return updated user data
    
    @param profile: Updated profile data
    @param db: Database session
    @param current_user: Injected from JWT token
    @returns {dict} Success message and updated user data
    @raises HTTPException: 400 if email already in use, 401 if not authenticated
    """
    try:
        # Check if email is being changed to one that already exists
        if profile.email != current_user.email:
            # Query database for existing email
            existing_user = await db.execute(
                select(User).where(User.email == profile.email)
            )
            if existing_user.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
            # Email is unique - update it
            current_user.email = profile.email
        
        # Update profile fields
        current_user.display_name = profile.display_name
        current_user.currency = profile.currency
        current_user.locale = profile.locale
        
        # Commit changes to database
        await db.commit()
        await db.refresh(current_user)
        
        return {
            "message": "Profile updated successfully",
            "user": {
                "email": current_user.email,
                "display_name": current_user.display_name,
                "currency": current_user.currency,
                "locale": current_user.locale
            }
        }
        
    except HTTPException as e:
        # Re-raise HTTP exceptions (email conflict, etc.)
        raise e
    except Exception as e:
        # Rollback on unexpected error
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )