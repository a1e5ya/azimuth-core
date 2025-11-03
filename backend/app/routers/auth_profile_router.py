from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..models.database import get_db, User
from ..auth.local_auth import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

class ProfileUpdate(BaseModel):
    display_name: str
    currency: str = "EUR"
    locale: str = "en-US"

@router.put("/profile")
async def update_profile(
    profile: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user profile information"""
    try:
        current_user.display_name = profile.display_name
        current_user.currency = profile.currency
        current_user.locale = profile.locale
        
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
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )