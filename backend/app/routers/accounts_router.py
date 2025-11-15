"""
Accounts Router - CRUD operations for accounts
backend/app/routers/accounts_router.py
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, delete
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
import uuid

from ..models.database import Account, Owner, Transaction, User, get_db
from ..auth.local_auth import get_current_user
from ..services.transaction_service import TransactionImportService

router = APIRouter()


# Pydantic Models
class AccountCreate(BaseModel):
    owner_id: str
    name: str
    account_type: str  # Main, Kopio, Reserv, BSP
    institution: Optional[str] = None
    current_balance: Optional[float] = 0.0


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    account_type: Optional[str] = None
    institution: Optional[str] = None
    current_balance: Optional[float] = None
    active: Optional[bool] = None


class AccountResponse(BaseModel):
    id: str
    owner_id: str
    owner_name: str
    name: str
    account_type: str
    institution: Optional[str]
    current_balance: float
    active: bool
    transaction_count: int
    created_at: str
    updated_at: str


# Endpoints

@router.get("/", response_model=List[AccountResponse])
async def list_accounts(
    owner_id: Optional[str] = None,
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all accounts, optionally filtered by owner"""
    
    query = select(Account).where(Account.user_id == current_user.id)
    
    if owner_id:
        try:
            owner_uuid = uuid.UUID(owner_id)
            query = query.where(Account.owner_id == str(owner_uuid))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid owner ID")
    
    if active_only:
        query = query.where(Account.active == True)
    
    query = query.order_by(Account.name)
    
    result = await db.execute(query)
    accounts = result.scalars().all()
    
    # Get owner names and transaction counts
    response = []
    for account in accounts:
        # Get owner
        owner_query = select(Owner).where(Owner.id == account.owner_id)
        owner_result = await db.execute(owner_query)
        owner = owner_result.scalar_one_or_none()
        
        # Get transaction count
        count_query = select(func.count(Transaction.id)).where(
            Transaction.account_id == account.id
        )
        count_result = await db.execute(count_query)
        transaction_count = count_result.scalar()
        
        response.append({
            "id": str(account.id),
            "owner_id": str(account.owner_id),
            "owner_name": owner.name if owner else "Unknown",
            "name": account.name,
            "account_type": account.account_type,
            "institution": account.institution,
            "current_balance": float(account.current_balance or 0),
            "active": account.active,
            "transaction_count": transaction_count,
            "created_at": account.created_at.isoformat(),
            "updated_at": account.updated_at.isoformat()
        })
    
    return response

@router.get("/list")
async def list_accounts_for_import(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all accounts for user with owner information - for import modal"""
    
    query = select(Account, Owner).join(
        Owner, Account.owner_id == Owner.id
    ).where(
        and_(
            Account.user_id == current_user.id,
            Account.active == True
        )
    ).order_by(Owner.name, Account.name)
    
    result = await db.execute(query)
    rows = result.all()
    
    accounts = []
    for account, owner in rows:
        accounts.append({
            "id": str(account.id),
            "name": account.name,
            "account_type": account.account_type,
            "institution": account.institution,
            "current_balance": float(account.current_balance or 0),
            "owner": {
                "id": str(owner.id),
                "name": owner.name,
                "color": owner.color
            }
        })
    
    return {
        "accounts": accounts,
        "total": len(accounts)
    }

@router.get("/list-simple")
async def list_accounts_simple(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all accounts for import modal - simplified"""
    
    query = select(Account, Owner).join(
        Owner, Account.owner_id == Owner.id
    ).where(
        and_(
            Account.user_id == current_user.id,
            Account.active == True
        )
    ).order_by(Owner.name, Account.name)
    
    result = await db.execute(query)
    rows = result.all()
    
    accounts = []
    for account, owner in rows:
        accounts.append({
            "id": str(account.id),
            "name": account.name,
            "account_type": account.account_type,
            "institution": account.institution,
            "current_balance": float(account.current_balance or 0),
            "owner": {
                "id": str(owner.id),
                "name": owner.name,
                "color": owner.color
            }
        })
    
    return {
        "accounts": accounts,
        "total": len(accounts)
    }

@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get single account details"""
    
    try:
        account_uuid = uuid.UUID(account_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid account ID")
    
    query = select(Account).where(
        and_(
            Account.id == str(account_uuid),
            Account.user_id == current_user.id
        )
    )
    result = await db.execute(query)
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Get owner
    owner_query = select(Owner).where(Owner.id == account.owner_id)
    owner_result = await db.execute(owner_query)
    owner = owner_result.scalar_one_or_none()
    
    # Get transaction count
    count_query = select(func.count(Transaction.id)).where(
        Transaction.account_id == str(account_uuid)
    )
    count_result = await db.execute(count_query)
    transaction_count = count_result.scalar()
    
    return {
        "id": str(account.id),
        "owner_id": str(account.owner_id),
        "owner_name": owner.name if owner else "Unknown",
        "name": account.name,
        "account_type": account.account_type,
        "institution": account.institution,
        "current_balance": float(account.current_balance or 0),
        "active": account.active,
        "transaction_count": transaction_count,
        "created_at": account.created_at.isoformat(),
        "updated_at": account.updated_at.isoformat()
    }


@router.post("/", response_model=AccountResponse)
async def create_account(
    account_data: AccountCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new account"""
    
    # Verify owner exists and belongs to user
    try:
        owner_uuid = uuid.UUID(account_data.owner_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid owner ID")
    
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
    
    # Check if account with same name exists for this owner
    existing_query = select(Account).where(
        and_(
            Account.owner_id == str(owner_uuid),
            Account.name == account_data.name,
            Account.account_type == account_data.account_type
        )
    )
    existing_result = await db.execute(existing_query)
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Account '{account_data.name}' ({account_data.account_type}) already exists for {owner.name}"
        )
    
    new_account = Account(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        owner_id=str(owner_uuid),
        name=account_data.name,
        account_type=account_data.account_type,
        institution=account_data.institution,
        current_balance=Decimal(str(account_data.current_balance or 0)),
        active=True
    )
    
    db.add(new_account)
    await db.commit()
    await db.refresh(new_account)
    
    print(f"✅ Created account: {owner.name} - {new_account.name} ({new_account.account_type})")
    
    return {
        "id": str(new_account.id),
        "owner_id": str(new_account.owner_id),
        "owner_name": owner.name,
        "name": new_account.name,
        "account_type": new_account.account_type,
        "institution": new_account.institution,
        "current_balance": float(new_account.current_balance),
        "active": new_account.active,
        "transaction_count": 0,
        "created_at": new_account.created_at.isoformat(),
        "updated_at": new_account.updated_at.isoformat()
    }


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: str,
    account_data: AccountUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update account"""
    
    try:
        account_uuid = uuid.UUID(account_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid account ID")
    
    query = select(Account).where(
        and_(
            Account.id == str(account_uuid),
            Account.user_id == current_user.id
        )
    )
    result = await db.execute(query)
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Update fields
    if account_data.name is not None:
        account.name = account_data.name
    
    if account_data.account_type is not None:
        account.account_type = account_data.account_type
    
    if account_data.institution is not None:
        account.institution = account_data.institution
    
    if account_data.current_balance is not None:
        account.current_balance = Decimal(str(account_data.current_balance))
    
    if account_data.active is not None:
        account.active = account_data.active
    
    account.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(account)
    
    # Get owner and transaction count
    owner_query = select(Owner).where(Owner.id == account.owner_id)
    owner_result = await db.execute(owner_query)
    owner = owner_result.scalar_one_or_none()
    
    count_query = select(func.count(Transaction.id)).where(
        Transaction.account_id == str(account_uuid)
    )
    count_result = await db.execute(count_query)
    transaction_count = count_result.scalar()
    
    print(f"✅ Updated account: {account.name}")
    
    return {
        "id": str(account.id),
        "owner_id": str(account.owner_id),
        "owner_name": owner.name if owner else "Unknown",
        "name": account.name,
        "account_type": account.account_type,
        "institution": account.institution,
        "current_balance": float(account.current_balance),
        "active": account.active,
        "transaction_count": transaction_count,
        "created_at": account.created_at.isoformat(),
        "updated_at": account.updated_at.isoformat()
    }


@router.delete("/{account_id}")
async def delete_account(
    account_id: str,
    force: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete account (only if no transactions or force=true)"""
    
    try:
        account_uuid = uuid.UUID(account_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid account ID")
    
    query = select(Account).where(
        and_(
            Account.id == str(account_uuid),
            Account.user_id == current_user.id
        )
    )
    result = await db.execute(query)
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Check for transactions
    trans_query = select(func.count(Transaction.id)).where(
        Transaction.account_id == str(account_uuid)
    )
    trans_result = await db.execute(trans_query)
    transaction_count = trans_result.scalar()
    
    if transaction_count > 0 and not force:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete account with {transaction_count} transactions. Use force=true to delete anyway"
        )
    
    # Delete account (cascade will delete transactions if force=true)
    delete_query = delete(Account).where(Account.id == str(account_uuid))
    await db.execute(delete_query)
    await db.commit()
    
    print(f"✅ Deleted account: {account.name} (with {transaction_count} transactions)")
    
    return {
        "success": True,
        "message": f"Account '{account.name}' deleted successfully",
        "transactions_deleted": transaction_count
    }


@router.post("/{account_id}/import")
async def import_transactions_to_account(
    account_id: str,
    file: UploadFile = File(...),
    auto_categorize: bool = Form(True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Import transactions directly to specific account"""
    
    try:
        account_uuid = uuid.UUID(account_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid account ID")
    
    # Verify account exists and belongs to user
    query = select(Account).where(
        and_(
            Account.id == str(account_uuid),
            Account.user_id == current_user.id
        )
    )
    result = await db.execute(query)
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Get owner
    owner_query = select(Owner).where(Owner.id == account.owner_id)
    owner_result = await db.execute(owner_query)
    owner = owner_result.scalar_one_or_none()
    
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")
    
    print(f"📤 Import to account: {owner.name} - {account.name} ({account.account_type})")
    
    # Validate file
    if not file.filename.lower().endswith(('.csv', '.xlsx')):
        raise HTTPException(status_code=400, detail="Only CSV and XLSX files are supported")
    
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    # Read file
    try:
        file_content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")
    
    # Import using service
    import_service = TransactionImportService(db, current_user)
    
    result = await import_service.import_from_csv(
        file_content=file_content,
        filename=file.filename,
        account_name=f"{owner.name}_{account.name}",  # Legacy compatibility
        account_type=account.account_type,
        auto_categorize=auto_categorize,
        account_id=str(account_uuid)  # Pass account_id directly
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    
    # Update account balance if needed (calculate from transactions)
    # This could be done asynchronously or here
    
    return result


@router.get("/{account_id}/transactions")
async def get_account_transactions(
    account_id: str,
    page: int = 1,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get transactions for specific account"""
    
    try:
        account_uuid = uuid.UUID(account_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid account ID")
    
    # Verify account exists and belongs to user
    account_query = select(Account).where(
        and_(
            Account.id == str(account_uuid),
            Account.user_id == current_user.id
        )
    )
    account_result = await db.execute(account_query)
    account = account_result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Get transactions
    from sqlalchemy import desc
    
    trans_query = select(Transaction).where(
        Transaction.account_id == str(account_uuid)
    ).order_by(desc(Transaction.posted_at)).offset((page - 1) * limit).limit(limit)
    
    trans_result = await db.execute(trans_query)
    transactions = trans_result.scalars().all()
    
    # Get total count
    count_query = select(func.count(Transaction.id)).where(
        Transaction.account_id == str(account_uuid)
    )
    count_result = await db.execute(count_query)
    total_count = count_result.scalar()
    
    return {
        "account_id": str(account.id),
        "account_name": account.name,
        "transactions": [
            {
                "id": str(t.id),
                "posted_at": t.posted_at.isoformat(),
                "amount": str(t.amount),
                "merchant": t.merchant,
                "memo": t.memo,
                "category_id": str(t.category_id) if t.category_id else None
            }
            for t in transactions
        ],
        "total": total_count,
        "page": page,
        "limit": limit
    }