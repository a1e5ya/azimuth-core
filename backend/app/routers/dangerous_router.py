from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, func
from pydantic import BaseModel
from typing import Optional

from ..models.database import get_db, User, Transaction, Category, Account, Goal, Budget, CategoryMapping, Owner, ImportBatch, AuditLog
from ..auth.local_auth import get_current_user, verify_password

router = APIRouter(prefix="/dangerous", tags=["dangerous"])

class PasswordConfirmation(BaseModel):
    password: str

@router.delete("/transactions/delete-all")
async def delete_all_transactions(
    confirmation: PasswordConfirmation,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete ALL transactions for the current user.
    Requires password confirmation.
    """
    # Verify password
    if not verify_password(confirmation.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    try:
        # Get count before deletion
        count_query = select(func.count(Transaction.id)).where(Transaction.user_id == current_user.id)
        result = await db.execute(count_query)
        count = result.scalar_one()
        
        # Delete all transactions
        delete_query = delete(Transaction).where(Transaction.user_id == current_user.id)
        await db.execute(delete_query)
        
        # Delete import batches
        delete_batches = delete(ImportBatch).where(ImportBatch.user_id == current_user.id)
        await db.execute(delete_batches)
        
        await db.commit()
        
        # Log the action
        audit = AuditLog(
            user_id=current_user.id,
            entity="transaction",
            action="delete_all",
            details={"count": count}
        )
        db.add(audit)
        await db.commit()
        
        return {
            "message": "All transactions deleted successfully",
            "deleted_count": count
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete transactions: {str(e)}"
        )

@router.delete("/account")
async def delete_account(
    confirmation: PasswordConfirmation,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Permanently delete the user account and ALL associated data.
    Requires password confirmation.
    """
    # Verify password
    if not verify_password(confirmation.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    try:
        # Log the deletion before doing it
        audit = AuditLog(
            user_id=current_user.id,
            entity="user",
            action="delete_account",
            details={"email": current_user.email}
        )
        db.add(audit)
        await db.commit()
        
        # Delete user (cascade will handle related records)
        await db.delete(current_user)
        await db.commit()
        
        return {
            "message": "Account deleted successfully"
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )

@router.post("/categories/reset")
async def reset_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reset categories to default structure.
    Removes all custom categories and restores defaults.
    """
    try:
        # Delete all user categories
        delete_mappings = delete(CategoryMapping).where(CategoryMapping.user_id == current_user.id)
        await db.execute(delete_mappings)
        
        delete_categories = delete(Category).where(Category.user_id == current_user.id)
        await db.execute(delete_categories)
        
        await db.commit()
        
        # Log the action
        audit = AuditLog(
            user_id=current_user.id,
            entity="category",
            action="reset_to_default",
            details={}
        )
        db.add(audit)
        await db.commit()
        
        return {
            "message": "Categories reset to default successfully"
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset categories: {str(e)}"
        )