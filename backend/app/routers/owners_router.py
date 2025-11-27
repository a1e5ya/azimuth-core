"""
Owners Router - Account Owner Management

Endpoints:
- GET /: List all owners with their accounts
- GET /{owner_id}: Get single owner with accounts
- POST /: Create new owner
- PUT /{owner_id}: Update owner
- DELETE /{owner_id}: Delete owner (with account protection)
- GET /{owner_id}/stats: Get financial statistics for owner

Features:
- Owner management (family members)
- Account association
- Name uniqueness validation
- Color coding for UI
- Soft delete support (active flag)
- Delete protection (requires account deletion first)
- Financial statistics aggregation

Database: SQLAlchemy async with Owner, Account models
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, delete
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

from ..models.database import Owner, Account, User, get_db
from ..auth.local_auth import get_current_user

router = APIRouter()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class OwnerCreate(BaseModel):
    """Owner creation request"""
    name: str
    color: Optional[str] = None


class OwnerUpdate(BaseModel):
    """Owner update request (all fields optional)"""
    name: Optional[str] = None
    color: Optional[str] = None
    active: Optional[bool] = None


class OwnerResponse(BaseModel):
    """Owner response with account count"""
    id: str
    name: str
    color: Optional[str]
    active: bool
    account_count: int
    created_at: str
    updated_at: str


class OwnerWithAccounts(BaseModel):
    """Owner response with full account details"""
    id: str
    name: str
    color: Optional[str]
    active: bool
    accounts: List[dict]
    created_at: str
    updated_at: str


# ============================================================================
# LIST OWNERS ENDPOINTS
# ============================================================================

@router.get("/", response_model=List[OwnerWithAccounts])
async def list_owners(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all owners with their accounts
    
    Returns owners sorted by name
    Each owner includes list of associated accounts
    
    @param current_user: Injected from JWT token
    @param db: Database session
    @returns {List[OwnerWithAccounts]} List of owners with accounts
    """
    # Get all owners for user
    query = select(Owner).where(
        Owner.user_id == current_user.id
    ).order_by(Owner.name)
    
    result = await db.execute(query)
    owners = result.scalars().all()
    
    # Build response with accounts for each owner
    response = []
    for owner in owners:
        # Get accounts for this owner
        accounts_query = select(Account).where(
            and_(
                Account.owner_id == owner.id,
                Account.user_id == current_user.id
            )
        ).order_by(Account.name)
        
        accounts_result = await db.execute(accounts_query)
        accounts = accounts_result.scalars().all()
        
        response.append({
            "id": str(owner.id),
            "name": owner.name,
            "color": owner.color,
            "active": owner.active,
            "accounts": [
                {
                    "id": str(acc.id),
                    "name": acc.name,
                    "account_type": acc.account_type,
                    "institution": acc.institution,
                    "current_balance": float(acc.current_balance) if acc.current_balance else 0.0,
                    "active": acc.active
                }
                for acc in accounts
            ],
            "created_at": owner.created_at.isoformat(),
            "updated_at": owner.updated_at.isoformat()
        })
    
    return response


# ============================================================================
# SINGLE OWNER ENDPOINTS
# ============================================================================

@router.get("/{owner_id}", response_model=OwnerWithAccounts)
async def get_owner(
    owner_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get single owner with accounts
    
    @param owner_id: Owner UUID
    @param current_user: Injected from JWT token
    @param db: Database session
    @returns {OwnerWithAccounts} Owner with accounts
    @raises HTTPException: 400 if invalid UUID, 404 if not found
    """
    # Validate UUID format
    try:
        owner_uuid = uuid.UUID(owner_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid owner ID")
    
    # Query owner (must belong to current user)
    query = select(Owner).where(
        and_(
            Owner.id == str(owner_uuid),
            Owner.user_id == current_user.id
        )
    )
    result = await db.execute(query)
    owner = result.scalar_one_or_none()
    
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")
    
    # Get accounts for this owner
    accounts_query = select(Account).where(
        and_(
            Account.owner_id == str(owner_uuid),
            Account.user_id == current_user.id
        )
    ).order_by(Account.name)
    
    accounts_result = await db.execute(accounts_query)
    accounts = accounts_result.scalars().all()
    
    return {
        "id": str(owner.id),
        "name": owner.name,
        "color": owner.color,
        "active": owner.active,
        "accounts": [
            {
                "id": str(acc.id),
                "name": acc.name,
                "account_type": acc.account_type,
                "institution": acc.institution,
                "current_balance": float(acc.current_balance) if acc.current_balance else 0.0,
                "active": acc.active
            }
            for acc in accounts
        ],
        "created_at": owner.created_at.isoformat(),
        "updated_at": owner.updated_at.isoformat()
    }


# ============================================================================
# CREATE OWNER ENDPOINT
# ============================================================================

@router.post("/", response_model=OwnerResponse)
async def create_owner(
    owner_data: OwnerCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create new owner
    
    Validates name uniqueness (per user)
    
    @param owner_data: Owner creation data
    @param current_user: Injected from JWT token
    @param db: Database session
    @returns {OwnerResponse} Created owner
    @raises HTTPException: 400 if name already exists
    """
    # Check if name already exists for this user
    existing_query = select(Owner).where(
        and_(
            Owner.user_id == current_user.id,
            Owner.name == owner_data.name
        )
    )
    existing_result = await db.execute(existing_query)
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=400, 
            detail=f"Owner with name '{owner_data.name}' already exists"
        )
    
    # Create owner
    new_owner = Owner(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        name=owner_data.name,
        color=owner_data.color,
        active=True
    )
    
    db.add(new_owner)
    await db.commit()
    await db.refresh(new_owner)
    
    print(f"✅ Created owner: {new_owner.name}")
    
    return {
        "id": str(new_owner.id),
        "name": new_owner.name,
        "color": new_owner.color,
        "active": new_owner.active,
        "account_count": 0,
        "created_at": new_owner.created_at.isoformat(),
        "updated_at": new_owner.updated_at.isoformat()
    }


# ============================================================================
# UPDATE OWNER ENDPOINT
# ============================================================================

@router.put("/{owner_id}", response_model=OwnerResponse)
async def update_owner(
    owner_id: str,
    owner_data: OwnerUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update owner details
    
    All fields optional - only provided fields are updated
    Validates name uniqueness if name is changed
    Updates updated_at timestamp automatically
    
    @param owner_id: Owner UUID
    @param owner_data: Fields to update
    @param current_user: Injected from JWT token
    @param db: Database session
    @returns {OwnerResponse} Updated owner
    @raises HTTPException: 400 if invalid UUID or name conflict, 404 if not found
    """
    # Validate UUID format
    try:
        owner_uuid = uuid.UUID(owner_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid owner ID")
    
    # Query owner (must belong to current user)
    query = select(Owner).where(
        and_(
            Owner.id == str(owner_uuid),
            Owner.user_id == current_user.id
        )
    )
    result = await db.execute(query)
    owner = result.scalar_one_or_none()
    
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")
    
    # Update name if provided (with uniqueness check)
    if owner_data.name is not None:
        # Check if new name already exists (only if name changed)
        if owner_data.name != owner.name:
            existing_query = select(Owner).where(
                and_(
                    Owner.user_id == current_user.id,
                    Owner.name == owner_data.name
                )
            )
            existing_result = await db.execute(existing_query)
            if existing_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=400,
                    detail=f"Owner with name '{owner_data.name}' already exists"
                )
        owner.name = owner_data.name
    
    # Update color if provided
    if owner_data.color is not None:
        owner.color = owner_data.color
    
    # Update active status if provided
    if owner_data.active is not None:
        owner.active = owner_data.active
    
    # Update timestamp
    owner.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(owner)
    
    # Get account count for response
    count_query = select(func.count(Account.id)).where(Account.owner_id == str(owner_uuid))
    count_result = await db.execute(count_query)
    account_count = count_result.scalar()
    
    print(f"✅ Updated owner: {owner.name}")
    
    return {
        "id": str(owner.id),
        "name": owner.name,
        "color": owner.color,
        "active": owner.active,
        "account_count": account_count,
        "created_at": owner.created_at.isoformat(),
        "updated_at": owner.updated_at.isoformat()
    }


# ============================================================================
# DELETE OWNER ENDPOINT
# ============================================================================

@router.delete("/{owner_id}")
async def delete_owner(
    owner_id: str,
    force: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete owner (with account protection)
    
    By default, prevents deletion if owner has accounts
    Use force=true to delete owner with all its accounts
    
    CASCADE DELETE: If force=true, all accounts are deleted too
    
    @param owner_id: Owner UUID
    @param force: Allow deletion with accounts (default: false)
    @param current_user: Injected from JWT token
    @param db: Database session
    @returns {dict} {success, message, accounts_deleted}
    @raises HTTPException: 400 if has accounts and force=false, 404 if not found
    """
    # Validate UUID format
    try:
        owner_uuid = uuid.UUID(owner_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid owner ID")
    
    # Query owner (must belong to current user)
    query = select(Owner).where(
        and_(
            Owner.id == str(owner_uuid),
            Owner.user_id == current_user.id
        )
    )
    result = await db.execute(query)
    owner = result.scalar_one_or_none()
    
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")
    
    # Check for accounts
    accounts_query = select(func.count(Account.id)).where(Account.owner_id == str(owner_uuid))
    accounts_result = await db.execute(accounts_query)
    account_count = accounts_result.scalar()
    
    # Prevent deletion if has accounts (unless force=true)
    if account_count > 0 and not force:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete owner with {account_count} accounts. Delete accounts first or use force=true"
        )
    
    # Delete owner (cascade deletes accounts if force=true)
    delete_query = delete(Owner).where(Owner.id == str(owner_uuid))
    await db.execute(delete_query)
    await db.commit()
    
    print(f"✅ Deleted owner: {owner.name} (with {account_count} accounts)")
    
    return {
        "success": True,
        "message": f"Owner '{owner.name}' deleted successfully",
        "accounts_deleted": account_count
    }


# ============================================================================
# OWNER STATISTICS ENDPOINT
# ============================================================================

@router.get("/{owner_id}/stats")
async def get_owner_stats(
    owner_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get financial statistics for owner
    
    Aggregates:
    - Total number of accounts
    - Total balance across all accounts
    - Individual account balances
    
    @param owner_id: Owner UUID
    @param current_user: Injected from JWT token
    @param db: Database session
    @returns {dict} {owner_id, owner_name, total_accounts, total_balance, accounts}
    @raises HTTPException: 400 if invalid UUID, 404 if not found
    """
    # Validate UUID format
    try:
        owner_uuid = uuid.UUID(owner_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid owner ID")
    
    # Verify owner exists and belongs to user
    owner_query = select(Owner).where(
        and_(
            Owner.id == str(owner_uuid),
            Owner.user_id == current_user.id
        )
    )
    owner_result = await db.execute(owner_query)
    owner = owner_result.scalar_one_or_none()
    
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")
    
    # Get all accounts for this owner
    accounts_query = select(Account).where(Account.owner_id == str(owner_uuid))
    accounts_result = await db.execute(accounts_query)
    accounts = accounts_result.scalars().all()
    
    # Calculate total balance
    total_balance = sum(float(acc.current_balance or 0) for acc in accounts)
    
    return {
        "owner_id": str(owner.id),
        "owner_name": owner.name,
        "total_accounts": len(accounts),
        "total_balance": total_balance,
        "accounts": [
            {
                "id": str(acc.id),
                "name": acc.name,
                "account_type": acc.account_type,
                "balance": float(acc.current_balance or 0)
            }
            for acc in accounts
        ]
    }