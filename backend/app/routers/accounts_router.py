"""
Accounts Router - Bank Account CRUD Operations

Endpoints:
- GET /: List all accounts (with owner info and transaction counts)
- GET /list: List accounts for import modal (with owner details)
- GET /list-simple: Simplified account list for dropdowns
- GET /{account_id}: Get single account details
- POST /: Create new account
- PUT /{account_id}: Update account
- DELETE /{account_id}: Delete account (with transaction protection)
- POST /{account_id}/import: Import CSV/XLSX transactions to account
- GET /{account_id}/transactions: Get paginated transactions for account

Features:
- Account types: Main, Kopio, Reserv, BSP
- Owner linking (family members)
- Transaction count tracking
- Balance tracking
- Soft delete support (active flag)
- Direct CSV import to specific account
- Transaction protection on delete

Database: SQLAlchemy async with Account, Owner, Transaction models
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, delete, desc
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
import uuid

from ..models.database import Account, Owner, Transaction, User, get_db
from ..auth.local_auth import get_current_user
from ..services.transaction_service import TransactionImportService

router = APIRouter()


# ============================================================================
# PYDANTIC REQUEST/RESPONSE MODELS
# ============================================================================

class AccountCreate(BaseModel):
    """Account creation request"""
    owner_id: str
    name: str
    account_type: str  # Main, Kopio, Reserv, BSP
    institution: Optional[str] = None
    current_balance: Optional[float] = 0.0


class AccountUpdate(BaseModel):
    """Account update request (all fields optional)"""
    name: Optional[str] = None
    account_type: Optional[str] = None
    institution: Optional[str] = None
    current_balance: Optional[float] = None
    active: Optional[bool] = None


class AccountResponse(BaseModel):
    """Account response with owner and transaction count"""
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


# ============================================================================
# LIST ACCOUNTS ENDPOINTS
# ============================================================================

@router.get("/", response_model=List[AccountResponse])
async def list_accounts(
    owner_id: Optional[str] = None,
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all accounts for current user
    
    Features:
    - Optional filter by owner_id
    - Optional filter for active accounts only
    - Includes owner name and transaction count
    - Sorted by account name
    
    @param owner_id: Optional UUID to filter by owner
    @param active_only: Filter for active accounts (default: true)
    @param current_user: Injected from JWT token
    @param db: Database session
    @returns {List[AccountResponse]} List of accounts with metadata
    """
    # Build query: user's accounts
    query = select(Account).where(Account.user_id == current_user.id)
    
    # Filter by owner if specified
    if owner_id:
        try:
            owner_uuid = uuid.UUID(owner_id)
            query = query.where(Account.owner_id == str(owner_uuid))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid owner ID")
    
    # Filter active accounts only
    if active_only:
        query = query.where(Account.active == True)
    
    # Sort by name
    query = query.order_by(Account.name)
    
    # Execute query
    result = await db.execute(query)
    accounts = result.scalars().all()
    
    # Build response with owner names and transaction counts
    response = []
    for account in accounts:
        # Get owner name
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
    """
    Get all accounts for import modal
    
    Returns accounts with full owner details (name, color)
    Used in frontend import modal dropdowns
    Sorted by owner name, then account name
    
    @param current_user: Injected from JWT token
    @param db: Database session
    @returns {dict} {accounts: [...], total: int}
    """
    # Join accounts with owners, filter active only
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
    
    # Build response with nested owner data
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
    """
    Get simplified account list
    
    Same as /list but with cleaner endpoint name
    Used for dropdown selects in UI
    
    @param current_user: Injected from JWT token
    @param db: Database session
    @returns {dict} {accounts: [...], total: int}
    """
    # Join accounts with owners, filter active only
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


# ============================================================================
# SINGLE ACCOUNT ENDPOINTS
# ============================================================================

@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get single account details by ID
    
    Includes owner name and transaction count
    
    @param account_id: Account UUID
    @param current_user: Injected from JWT token
    @param db: Database session
    @returns {AccountResponse} Account with metadata
    @raises HTTPException: 400 if invalid UUID, 404 if not found
    """
    # Validate UUID format
    try:
        account_uuid = uuid.UUID(account_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid account ID")
    
    # Query account (must belong to current user)
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
    
    # Get owner name
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


# ============================================================================
# CREATE ACCOUNT ENDPOINT
# ============================================================================

@router.post("/", response_model=AccountResponse)
async def create_account(
    account_data: AccountCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create new bank account
    
    Process:
    1. Validate owner_id exists and belongs to user
    2. Create account with initial balance
    3. Return created account with metadata
    
    @param account_data: Account creation data
    @param current_user: Injected from JWT token
    @param db: Database session
    @returns {AccountResponse} Created account
    @raises HTTPException: 400 if invalid owner_id, 404 if owner not found
    """
    # Validate owner UUID
    try:
        owner_uuid = uuid.UUID(account_data.owner_id)
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
    
    # Create account
    new_account = Account(
        user_id=current_user.id,
        owner_id=str(owner_uuid),
        name=account_data.name,
        account_type=account_data.account_type,
        institution=account_data.institution,
        current_balance=Decimal(str(account_data.current_balance or 0))
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


# ============================================================================
# UPDATE ACCOUNT ENDPOINT
# ============================================================================

@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: str,
    account_data: AccountUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update existing account
    
    All fields are optional - only provided fields are updated
    Updates updated_at timestamp automatically
    
    @param account_id: Account UUID
    @param account_data: Fields to update
    @param current_user: Injected from JWT token
    @param db: Database session
    @returns {AccountResponse} Updated account
    @raises HTTPException: 400 if invalid UUID, 404 if not found
    """
    # Validate UUID format
    try:
        account_uuid = uuid.UUID(account_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid account ID")
    
    # Query account (must belong to current user)
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
    
    # Update only provided fields
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
    
    # Update timestamp
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


# ============================================================================
# DELETE ACCOUNT ENDPOINT
# ============================================================================

@router.delete("/{account_id}")
async def delete_account(
    account_id: str,
    force: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete account (with transaction protection)
    
    By default, prevents deletion if account has transactions
    Use force=true to delete account with all its transactions
    
    CASCADE DELETE: If force=true, all transactions are deleted too
    
    @param account_id: Account UUID
    @param force: Allow deletion with transactions (default: false)
    @param current_user: Injected from JWT token
    @param db: Database session
    @returns {dict} Success message with transaction count
    @raises HTTPException: 400 if has transactions and force=false, 404 if not found
    """
    # Validate UUID format
    try:
        account_uuid = uuid.UUID(account_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid account ID")
    
    # Query account (must belong to current user)
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
    
    # Prevent deletion if has transactions (unless force=true)
    if transaction_count > 0 and not force:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete account with {transaction_count} transactions. Use force=true to delete anyway"
        )
    
    # Delete account (cascade deletes transactions if force=true)
    delete_query = delete(Account).where(Account.id == str(account_uuid))
    await db.execute(delete_query)
    await db.commit()
    
    print(f"✅ Deleted account: {account.name} (with {transaction_count} transactions)")
    
    return {
        "success": True,
        "message": f"Account '{account.name}' deleted successfully",
        "transactions_deleted": transaction_count
    }


# ============================================================================
# ACCOUNT TRANSACTION IMPORT ENDPOINT
# ============================================================================

@router.post("/{account_id}/import")
async def import_transactions_to_account(
    account_id: str,
    file: UploadFile = File(...),
    auto_categorize: bool = Form(True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Import CSV/XLSX transactions directly to specific account
    
    Process:
    1. Validate account exists and belongs to user
    2. Validate file format (CSV/XLSX) and size (<10MB)
    3. Parse transactions from file
    4. Auto-categorize if enabled (using LLM or rules)
    5. Import to database with duplicate detection
    
    @param account_id: Target account UUID
    @param file: CSV or XLSX file upload
    @param auto_categorize: Enable LLM categorization (default: true)
    @param current_user: Injected from JWT token
    @param db: Database session
    @returns {dict} Import result with statistics
    @raises HTTPException: 400 if invalid file, 404 if account not found
    """
    # Validate UUID format
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
    
    # Get owner for logging
    owner_query = select(Owner).where(Owner.id == account.owner_id)
    owner_result = await db.execute(owner_query)
    owner = owner_result.scalar_one_or_none()
    
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")
    
    print(f"📤 Import to account: {owner.name} - {account.name} ({account.account_type})")
    
    # Validate file type
    if not file.filename.lower().endswith(('.csv', '.xlsx')):
        raise HTTPException(status_code=400, detail="Only CSV and XLSX files are supported")
    
    # Validate file size
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    # Read file content
    try:
        file_content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")
    
    # Import using TransactionImportService
    import_service = TransactionImportService(db, current_user)
    
    result = await import_service.import_from_csv(
        file_content=file_content,
        filename=file.filename,
        account_name=f"{owner.name}_{account.name}",  # Legacy format for compatibility
        account_type=account.account_type,
        auto_categorize=auto_categorize,
        account_id=str(account_uuid)  # Link transactions to account
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    
    return result


# ============================================================================
# ACCOUNT TRANSACTIONS ENDPOINT
# ============================================================================

@router.get("/{account_id}/transactions")
async def get_account_transactions(
    account_id: str,
    page: int = 1,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get paginated transactions for specific account
    
    Returns transactions sorted by posted_at descending (newest first)
    Includes pagination with page and limit parameters
    
    @param account_id: Account UUID
    @param page: Page number (default: 1)
    @param limit: Items per page (default: 50)
    @param current_user: Injected from JWT token
    @param db: Database session
    @returns {dict} {account_id, account_name, transactions: [...], total, page, limit}
    @raises HTTPException: 400 if invalid UUID, 404 if account not found
    """
    # Validate UUID format
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
    
    # Get paginated transactions (newest first)
    trans_query = select(Transaction).where(
        Transaction.account_id == str(account_uuid)
    ).order_by(desc(Transaction.posted_at)).offset((page - 1) * limit).limit(limit)
    
    trans_result = await db.execute(trans_query)
    transactions = trans_result.scalars().all()
    
    # Get total count for pagination
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