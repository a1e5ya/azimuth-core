"""
Dangerous Router - Destructive Operations with Password Protection

Endpoints:
- DELETE /dangerous/transactions/delete-all: Delete ALL transactions (requires password)
- DELETE /dangerous/account: Permanently delete user account (requires password)
- POST /dangerous/categories/reset: Reset categories to default (no password)

Security:
- Password confirmation required for destructive operations
- Audit logging for all dangerous operations
- Cascade deletion of related records
- Cannot be undone - data is permanently deleted

WARNING: These operations are IRREVERSIBLE!

Database: SQLAlchemy async with all models
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, func
from pydantic import BaseModel
from typing import Optional

from ..models.database import get_db, User, Transaction, Category, Account, Goal, Budget, CategoryMapping, Owner, ImportBatch, AuditLog
from ..auth.local_auth import get_current_user, verify_password

router = APIRouter(prefix="/dangerous", tags=["dangerous"])


# ============================================================================
# REQUEST MODELS
# ============================================================================

class PasswordConfirmation(BaseModel):
    """Password confirmation for destructive operations"""
    password: str


# ============================================================================
# DELETE ALL TRANSACTIONS ENDPOINT
# ============================================================================

@router.delete("/transactions/delete-all")
async def delete_all_transactions(
    confirmation: PasswordConfirmation,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete ALL transactions for current user
    
    WARNING: This operation cannot be undone!
    
    Process:
    1. Verify password
    2. Count transactions to be deleted
    3. Delete all transactions
    4. Delete all import batches
    5. Log deletion to audit table
    
    Requires password confirmation for safety
    
    @param confirmation: User's password for verification
    @param db: Database session
    @param current_user: Injected from JWT token
    @returns {dict} {message, deleted_count}
    @raises HTTPException: 401 if password incorrect, 500 on deletion failure
    """
    # Verify password before proceeding
    if not verify_password(confirmation.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    try:
        # Get count before deletion (for logging)
        count_query = select(func.count(Transaction.id)).where(Transaction.user_id == current_user.id)
        result = await db.execute(count_query)
        count = result.scalar_one()
        
        # Delete all user's transactions
        delete_query = delete(Transaction).where(Transaction.user_id == current_user.id)
        await db.execute(delete_query)
        
        # Delete all import batches (transaction import metadata)
        delete_batches = delete(ImportBatch).where(ImportBatch.user_id == current_user.id)
        await db.execute(delete_batches)
        
        await db.commit()
        
        # Log the dangerous action
        audit = AuditLog(
            user_id=current_user.id,
            entity="transaction",
            action="delete_all",
            details={"count": count}
        )
        db.add(audit)
        await db.commit()
        
        print(f"⚠️ DANGER: User {current_user.email} deleted {count} transactions")
        
        return {
            "message": "All transactions deleted successfully",
            "deleted_count": count
        }
        
    except Exception as e:
        await db.rollback()
        print(f"❌ Failed to delete all transactions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete transactions: {str(e)}"
        )


# ============================================================================
# DELETE ACCOUNT ENDPOINT
# ============================================================================

@router.delete("/account")
async def delete_account(
    confirmation: PasswordConfirmation,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Permanently delete user account and ALL associated data
    
    WARNING: This operation cannot be undone!
    
    Deletes:
    - User account
    - All transactions (cascade)
    - All categories (cascade)
    - All accounts (cascade)
    - All owners (cascade)
    - All goals and budgets (cascade)
    - All audit logs (cascade)
    
    Process:
    1. Verify password
    2. Log deletion (before deleting user)
    3. Delete user (cascade deletes all related records)
    
    Requires password confirmation for safety
    
    @param confirmation: User's password for verification
    @param db: Database session
    @param current_user: Injected from JWT token
    @returns {dict} {message}
    @raises HTTPException: 401 if password incorrect, 500 on deletion failure
    """
    # Verify password before proceeding
    if not verify_password(confirmation.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    try:
        # Log the deletion BEFORE doing it (won't be visible after user deleted)
        audit = AuditLog(
            user_id=current_user.id,
            entity="user",
            action="delete_account",
            details={"email": current_user.email}
        )
        db.add(audit)
        await db.commit()
        
        print(f"⚠️ DANGER: Deleting user account: {current_user.email}")
        
        # Delete user (cascade will handle all related records)
        await db.delete(current_user)
        await db.commit()
        
        print(f"✅ Account deleted: {current_user.email}")
        
        return {
            "message": "Account deleted successfully"
        }
        
    except Exception as e:
        await db.rollback()
        print(f"❌ Failed to delete account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )


# ============================================================================
# RESET CATEGORIES ENDPOINT
# ============================================================================

@router.post("/categories/reset")
async def reset_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reset categories to default structure
    
    Removes all custom categories and category mappings
    User can then re-initialize default categories
    
    Process:
    1. Delete all category mappings (rules)
    2. Delete all categories
    3. Log reset action
    
    Note: Does NOT delete transactions
    Note: Does NOT require password (can be re-initialized easily)
    
    @param db: Database session
    @param current_user: Injected from JWT token
    @returns {dict} {message}
    @raises HTTPException: 500 on reset failure
    """
    try:
        # Delete all category mappings (auto-categorization rules)
        delete_mappings = delete(CategoryMapping).where(CategoryMapping.user_id == current_user.id)
        await db.execute(delete_mappings)
        
        # Delete all categories
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
        
        print(f"✅ Categories reset for user: {current_user.email}")
        
        return {
            "message": "Categories reset to default successfully"
        }
        
    except Exception as e:
        await db.rollback()
        print(f"❌ Failed to reset categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset categories: {str(e)}"
        )