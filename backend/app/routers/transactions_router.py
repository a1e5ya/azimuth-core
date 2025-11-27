"""
Transactions Router - Main Transaction CRUD Operations

This is the primary router for all transaction-related endpoints.

Endpoints:
- GET /list: List transactions with advanced filtering and pagination
- GET /summary: Get transaction summary statistics
- GET /filtered-summary: Get summary for filtered subset
- GET /{transaction_id}: Get single transaction details
- POST /: Create single transaction manually
- PUT /{transaction_id}: Update transaction
- DELETE /{transaction_id}: Delete single transaction
- POST /bulk-delete: Delete multiple transactions
- POST /bulk-categorize: Assign category to multiple transactions
- POST /import: Import CSV/XLSX file
- POST /sync-categories: Sync transaction category strings with Category table

Features:
- Advanced filtering (date, amount, merchant, category, account, owner)
- Pagination and sorting
- Category assignment (manual and automatic)
- Bulk operations (categorize, delete)
- CSV/XLSX import with auto-categorization
- Transfer pair linking
- Confidence scoring
- Review flagging

Database: SQLAlchemy async with Transaction, Category, Account models
Services: TransactionService, TransactionQueries, TransactionImportService
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, distinct
from sqlalchemy.orm import selectinload
from typing import List, Optional, Union
from datetime import date, datetime
from pydantic import BaseModel
import uuid

from ..models.database import get_db, User, Transaction, Category, AuditLog
from ..services.transaction_service import (
    TransactionService, 
    TransactionQueries,
    TransactionImportService,
    get_transaction_service,
    get_transaction_queries,
    get_import_service
)
from .transaction_models import (
    TransactionResponse, TransactionSummary, DeleteResponse,
    BulkCategorizeRequest, BulkOperationResponse
)
from ..auth.local_auth import get_current_user

router = APIRouter()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def ensure_list(param: Optional[Union[str, List[str]]]) -> Optional[List[str]]:
    """
    Convert string params to single-item lists
    
    FastAPI Query params can be sent as either string or list
    Axios with paramsSerializer may send single values as strings
    This normalizes them to always be lists
    
    @param param: String or list of strings (or None)
    @returns {List[str]|None} List of strings or None
    """
    if param is None:
        return None
    if isinstance(param, str):
        return [param]
    return param


# ============================================================================
# REQUEST MODELS
# ============================================================================

class TransactionUpdateRequest(BaseModel):
    """Transaction update request (all fields optional)"""
    merchant: Optional[str] = None
    amount: Optional[float] = None
    memo: Optional[str] = None
    category_id: Optional[str] = None


class BulkDeleteRequest(BaseModel):
    """Bulk delete request"""
    transaction_ids: List[str]


class TransactionCreateRequest(BaseModel):
    """Manual transaction creation request"""
    posted_at: str  # ISO date string
    amount: float
    merchant: Optional[str] = None
    memo: Optional[str] = None
    owner: Optional[str] = None
    bank_account_type: Optional[str] = None
    category_id: Optional[str] = None


# ============================================================================
# LIST TRANSACTIONS ENDPOINT
# ============================================================================

@router.get("/list", response_model=List[TransactionResponse])
async def list_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=1000),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
    merchant: Optional[str] = Query(None),
    category_id: Optional[str] = Query(None),
    account_id: Optional[str] = Query(None),
    main_category: Optional[str] = Query(None),
    review_needed: Optional[bool] = Query(None),
    owners: Optional[List[str]] = Query(None),
    account_types: Optional[List[str]] = Query(None),
    main_categories: Optional[List[str]] = Query(None),
    categories: Optional[List[str]] = Query(None),  # CSV category filter
    subcategories: Optional[List[str]] = Query(None),  # CSV subcategory filter
    sort_by: str = Query("posted_at", regex="^(posted_at|amount|merchant|created_at)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: User = Depends(get_current_user),
    queries: TransactionQueries = Depends(get_transaction_queries)
):
    """
    Get paginated list of transactions with advanced filtering
    
    Supports filtering by:
    - Date range (start_date, end_date)
    - Amount range (min_amount, max_amount)
    - Merchant (partial match, case-insensitive)
    - Category (linked category_id)
    - Account (account_id)
    - Main category (INCOME, EXPENSES, TRANSFERS)
    - Review status (review_needed boolean)
    - Owners (list of owner names: Egor, Alex, Lila)
    - Account types (list: Main, Kopio, Reserv, BSP)
    - CSV categories (list of category strings from CSV)
    - CSV subcategories (list of subcategory strings from CSV)
    
    Supports sorting by: posted_at, amount, merchant, created_at
    Supports pagination with page and limit
    
    Returns transactions with full category details (name, icon, parent)
    
    @param page: Page number (starts at 1)
    @param limit: Items per page (1-1000)
    @param start_date: Filter from date (inclusive)
    @param end_date: Filter to date (inclusive)
    @param min_amount: Minimum amount (inclusive)
    @param max_amount: Maximum amount (inclusive)
    @param merchant: Merchant name (partial match)
    @param category_id: Linked category UUID
    @param account_id: Account UUID
    @param main_category: Main category (INCOME, EXPENSES, TRANSFERS)
    @param review_needed: Filter by review flag
    @param owners: List of owner names
    @param account_types: List of account types
    @param main_categories: List of main categories
    @param categories: List of CSV category strings
    @param subcategories: List of CSV subcategory strings
    @param sort_by: Sort field
    @param sort_order: Sort direction (asc|desc)
    @param current_user: Injected from JWT token
    @param queries: Injected TransactionQueries service
    @returns {List[TransactionResponse]} List of transactions
    """
    # Build filters dict for service
    filters = {
        'page': page, 'limit': limit, 'start_date': start_date, 'end_date': end_date,
        'min_amount': min_amount, 'max_amount': max_amount, 'merchant': merchant,
        'category_id': category_id, 'account_id': account_id, 'main_category': main_category,
        'review_needed': review_needed, 'owners': owners or [], 'account_types': account_types or [],
        'main_categories': main_categories or [], 
        'categories': categories or [],  # CSV category strings
        'subcategories': subcategories or [],  # CSV subcategory strings
        'sort_by': sort_by, 'sort_order': sort_order
    }
    
    # Get filtered transactions from service
    transactions, total_count = await queries.get_transactions_with_filters(filters)
    
    # Build response with full category details
    response_data = []
    for transaction in transactions:
        # Get parent category name if exists
        parent_category_name = None
        if transaction.assigned_category:
            if transaction.assigned_category.parent:
                parent_category_name = transaction.assigned_category.parent.name

        response_data.append(TransactionResponse(
            id=str(transaction.id),
            account_id=str(transaction.account_id) if transaction.account_id else None,
            posted_at=transaction.posted_at.isoformat(),
            amount=str(transaction.amount),
            currency=transaction.currency,
            merchant=transaction.merchant,
            memo=transaction.memo,
            category_id=str(transaction.category_id) if transaction.category_id else None,
            category_name=transaction.assigned_category.name if transaction.assigned_category else None,
            category_icon=transaction.assigned_category.icon if transaction.assigned_category else None,
            parent_category_name=parent_category_name,
            source_category=transaction.source_category,
            import_batch_id=str(transaction.import_batch_id) if transaction.import_batch_id else None,
            main_category=transaction.main_category,
            category=transaction.category,
            subcategory=transaction.subcategory,
            owner=transaction.owner,
            is_expense=transaction.is_expense,
            is_income=transaction.is_income,
            year=transaction.year,
            month=transaction.month,
            year_month=transaction.year_month,
            weekday=transaction.weekday,
            transfer_pair_id=transaction.transfer_pair_id,
            confidence_score=float(transaction.confidence_score) if transaction.confidence_score else None,
            review_needed=transaction.review_needed,
            tags=transaction.tags if transaction.tags else [],
            notes=transaction.notes,
            created_at=transaction.created_at.isoformat(),
            bank_account=transaction.bank_account,
            bank_account_type=transaction.bank_account_type,
        ))
    
    return response_data


# ============================================================================
# TRANSACTION SUMMARY ENDPOINTS
# ============================================================================

@router.get("/summary", response_model=TransactionSummary)
async def get_transaction_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    queries: TransactionQueries = Depends(get_transaction_queries)
):
    """
    Get comprehensive transaction summary with analytics
    
    Aggregates:
    - Total transaction count
    - Total amounts by type (income, expense, transfer)
    - Categorization rate (percentage)
    - Date range
    - Monthly breakdown
    - Recent imports
    - Top merchants
    - Top categories
    
    Optional date range filtering
    
    @param start_date: Filter from date (optional)
    @param end_date: Filter to date (optional)
    @param queries: Injected TransactionQueries service
    @returns {TransactionSummary} Summary statistics
    """
    summary_data = await queries.get_transaction_summary(start_date, end_date)
    return TransactionSummary(**summary_data)


@router.get("/filtered-summary")
async def get_filtered_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
    merchant: Optional[str] = Query(None),
    category_id: Optional[str] = Query(None),
    account_id: Optional[str] = Query(None),
    main_category: Optional[str] = Query(None),
    review_needed: Optional[bool] = Query(None),
    owners: Optional[List[str]] = Query(None),
    account_types: Optional[List[str]] = Query(None),
    main_categories: Optional[List[str]] = Query(None),
    categories: Optional[List[str]] = Query(None),
    subcategories: Optional[List[str]] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get summary statistics for filtered subset of transactions
    
    Calculates totals for currently filtered transactions (all pages)
    Used to show "Filtered X transactions totaling €Y" in UI
    
    Applies same filters as /list endpoint but returns aggregates instead of records
    
    Returns:
    - Total count
    - Total amount (sum of absolute values)
    - Income total
    - Expense total
    - Transfer total
    
    @param start_date through subcategories: Same filters as /list endpoint
    @param current_user: Injected from JWT token
    @param db: Database session
    @returns {dict} {total_count, total_amount, income, expense, transfer}
    """
    # Normalize params (handle single strings from axios)
    main_categories = ensure_list(main_categories)
    categories = ensure_list(categories)
    subcategories = ensure_list(subcategories)
    owners = ensure_list(owners)
    account_types = ensure_list(account_types)
    
    # Build query conditions
    conditions = [Transaction.user_id == current_user.id]
    
    if start_date:
        conditions.append(Transaction.posted_at >= start_date)
    if end_date:
        conditions.append(Transaction.posted_at <= end_date)
    if min_amount is not None:
        conditions.append(Transaction.amount >= min_amount)
    if max_amount is not None:
        conditions.append(Transaction.amount <= max_amount)
    if merchant:
        conditions.append(Transaction.merchant.ilike(f"%{merchant}%"))
    if category_id:
        conditions.append(Transaction.category_id == uuid.UUID(category_id))
    if main_category:
        conditions.append(Transaction.main_category == main_category)
    if review_needed is not None:
        conditions.append(Transaction.review_needed == review_needed)
    if owners and len(owners) > 0:
        conditions.append(Transaction.owner.in_(owners))
    if account_types and len(account_types) > 0:
        conditions.append(Transaction.bank_account_type.in_(account_types))
    if main_categories and len(main_categories) > 0:
        # Case-insensitive comparison
        conditions.append(func.upper(Transaction.main_category).in_([m.upper() for m in main_categories]))
    if categories and len(categories) > 0:
        conditions.append(func.upper(Transaction.category).in_([c.upper() for c in categories]))
    if subcategories and len(subcategories) > 0:
        conditions.append(func.upper(Transaction.subcategory).in_([s.upper() for s in subcategories]))
    
    # Get total count
    count_query = select(func.count(Transaction.id)).where(and_(*conditions))
    count_result = await db.execute(count_query)
    total_count = count_result.scalar()
    
    # Get sum totals by type
    income_query = select(func.sum(Transaction.amount)).where(
        and_(*conditions, Transaction.is_income == True)
    )
    income_result = await db.execute(income_query)
    income_total = float(income_result.scalar() or 0)
    
    expense_query = select(func.sum(func.abs(Transaction.amount))).where(
        and_(*conditions, Transaction.is_expense == True)
    )
    expense_result = await db.execute(expense_query)
    expense_total = float(expense_result.scalar() or 0)
    
    transfer_query = select(func.sum(func.abs(Transaction.amount))).where(
        and_(*conditions, Transaction.main_category == 'TRANSFERS')
    )
    transfer_result = await db.execute(transfer_query)
    transfer_total = float(transfer_result.scalar() or 0)
    
    # Total amount (sum of absolute values)
    total_query = select(func.sum(func.abs(Transaction.amount))).where(and_(*conditions))
    total_result = await db.execute(total_query)
    total_amount = float(total_result.scalar() or 0)
    
    return {
        "total_count": total_count,
        "total_amount": total_amount,
        "income": income_total,
        "expense": expense_total,
        "transfer": transfer_total
    }


# ============================================================================
# SINGLE TRANSACTION ENDPOINTS
# ============================================================================

@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get single transaction by ID
    
    Includes full category details (name, icon, parent)
    
    @param transaction_id: Transaction UUID
    @param current_user: Injected from JWT token
    @param db: Database session
    @returns {TransactionResponse} Transaction details
    @raises HTTPException: 400 if invalid UUID, 404 if not found
    """
    try:
        trans_uuid = uuid.UUID(transaction_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid transaction ID")
    
    # Query transaction with category relationship
    query = select(Transaction).options(
        selectinload(Transaction.assigned_category).selectinload(Category.parent)
    ).where(
        and_(
            Transaction.id == str(trans_uuid),
            Transaction.user_id == current_user.id
        )
    )
    
    result = await db.execute(query)
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Get parent category name
    parent_category_name = None
    if transaction.assigned_category and transaction.assigned_category.parent:
        parent_category_name = transaction.assigned_category.parent.name
    
    return TransactionResponse(
        id=str(transaction.id),
        account_id=str(transaction.account_id) if transaction.account_id else None,
        posted_at=transaction.posted_at.isoformat(),
        amount=str(transaction.amount),
        currency=transaction.currency,
        merchant=transaction.merchant,
        memo=transaction.memo,
        category_id=str(transaction.category_id) if transaction.category_id else None,
        category_name=transaction.assigned_category.name if transaction.assigned_category else None,
        category_icon=transaction.assigned_category.icon if transaction.assigned_category else None,
        parent_category_name=parent_category_name,
        source_category=transaction.source_category,
        import_batch_id=str(transaction.import_batch_id) if transaction.import_batch_id else None,
        main_category=transaction.main_category,
        category=transaction.category,
        subcategory=transaction.subcategory,
        owner=transaction.owner,
        is_expense=transaction.is_expense,
        is_income=transaction.is_income,
        year=transaction.year,
        month=transaction.month,
        year_month=transaction.year_month,
        weekday=transaction.weekday,
        transfer_pair_id=transaction.transfer_pair_id,
        confidence_score=float(transaction.confidence_score) if transaction.confidence_score else None,
        review_needed=transaction.review_needed,
        tags=transaction.tags if transaction.tags else [],
        notes=transaction.notes,
        created_at=transaction.created_at.isoformat(),
        bank_account=transaction.bank_account,
        bank_account_type=transaction.bank_account_type,
    )


# File continues in next message due to length...


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: str,
    data: TransactionUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update transaction fields
    
    All fields optional - only provided fields are updated
    If category_id is updated, automatically syncs category strings
    
    @param transaction_id: Transaction UUID
    @param data: Fields to update
    @param current_user: Injected from JWT token
    @param db: Database session
    @returns {TransactionResponse} Updated transaction
    @raises HTTPException: 400 if invalid UUID, 404 if not found
    """
    try:
        trans_uuid = uuid.UUID(transaction_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid transaction ID")
    
    # Query transaction
    query = select(Transaction).where(
        and_(
            Transaction.id == str(trans_uuid),
            Transaction.user_id == current_user.id
        )
    )
    result = await db.execute(query)
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Update provided fields
    if data.merchant is not None:
        transaction.merchant = data.merchant
    if data.amount is not None:
        transaction.amount = data.amount
        transaction.is_income = data.amount > 0
        transaction.is_expense = data.amount < 0
    if data.memo is not None:
        transaction.memo = data.memo
    
    # Update category if provided (sync category strings)
    if data.category_id is not None:
        transaction.category_id = data.category_id
        
        # Get category hierarchy
        if data.category_id:
            cat_query = select(Category).options(
                selectinload(Category.parent).selectinload(Category.parent)
            ).where(Category.id == data.category_id)
            cat_result = await db.execute(cat_query)
            cat = cat_result.scalar_one_or_none()
            
            if cat:
                # Sync category strings based on hierarchy
                if cat.parent:
                    if cat.parent.parent:
                        # 3-level: grandparent = main, parent = category, self = subcategory
                        transaction.main_category = cat.parent.parent.name
                        transaction.category = cat.parent.name
                        transaction.subcategory = cat.name
                    else:
                        # 2-level: parent = main, self = category
                        transaction.main_category = cat.parent.name
                        transaction.category = cat.name
                        transaction.subcategory = None
                else:
                    # 1-level: self = main
                    transaction.main_category = cat.name
                    transaction.category = None
                    transaction.subcategory = None
    
    await db.commit()
    await db.refresh(transaction)
    
    print(f"✅ Updated transaction: {transaction.id}")
    
    # Return full transaction response (re-query with relationships)
    return await get_transaction(transaction_id, current_user, db)


@router.delete("/{transaction_id}", response_model=DeleteResponse)
async def delete_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete single transaction
    
    @param transaction_id: Transaction UUID
    @param current_user: Injected from JWT token
    @param db: Database session
    @returns {DeleteResponse} {success, message, deleted_count}
    @raises HTTPException: 400 if invalid UUID, 404 if not found
    """
    try:
        trans_uuid = uuid.UUID(transaction_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid transaction ID")
    
    # Query transaction
    query = select(Transaction).where(
        and_(
            Transaction.id == str(trans_uuid),
            Transaction.user_id == current_user.id
        )
    )
    result = await db.execute(query)
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Delete transaction
    await db.delete(transaction)
    await db.commit()
    
    print(f"✅ Deleted transaction: {transaction_id}")
    
    return DeleteResponse(
        success=True,
        message="Transaction deleted successfully",
        deleted_count=1
    )


# ============================================================================
# BULK OPERATIONS ENDPOINTS
# ============================================================================

@router.post("/bulk-categorize", response_model=BulkOperationResponse)
async def bulk_categorize_transactions(
    request: BulkCategorizeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Assign category to multiple transactions
    
    Updates category_id and syncs category strings for all transactions
    Sets source_category to 'user' and confidence to provided value
    
    @param request: {transaction_ids: [UUIDs], category_id: UUID, confidence: float}
    @param current_user: Injected from JWT token
    @param db: Database session
    @returns {BulkOperationResponse} {success, message, updated_count}
    """
    try:
        # Convert to UUIDs
        trans_ids = [str(uuid.UUID(tid)) for tid in request.transaction_ids]
        
        # Get category hierarchy for syncing strings
        cat_query = select(Category).options(
            selectinload(Category.parent).selectinload(Category.parent)
        ).where(Category.id == request.category_id)
        cat_result = await db.execute(cat_query)
        cat = cat_result.scalar_one_or_none()
        
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")
        
        # Determine category strings
        main_category = None
        category = None
        subcategory = None
        
        if cat.parent:
            if cat.parent.parent:
                # 3-level
                main_category = cat.parent.parent.name
                category = cat.parent.name
                subcategory = cat.name
            else:
                # 2-level
                main_category = cat.parent.name
                category = cat.name
        else:
            # 1-level
            main_category = cat.name
        
        # Update all transactions
        query = select(Transaction).where(
            and_(
                Transaction.id.in_(trans_ids),
                Transaction.user_id == current_user.id
            )
        )
        result = await db.execute(query)
        transactions = result.scalars().all()
        
        updated_count = 0
        for trans in transactions:
            trans.category_id = request.category_id
            trans.main_category = main_category
            trans.category = category
            trans.subcategory = subcategory
            trans.source_category = 'user'
            trans.confidence_score = request.confidence
            trans.review_needed = False
            updated_count += 1
        
        await db.commit()
        
        print(f"✅ Bulk categorized {updated_count} transactions")
        
        return BulkOperationResponse(
            success=True,
            message=f"Categorized {updated_count} transactions",
            updated_count=updated_count
        )
    except Exception as e:
        await db.rollback()
        print(f"❌ Bulk categorize failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-delete")
async def bulk_delete_transactions(
    request: BulkDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete multiple transactions
    
    @param request: {transaction_ids: [UUIDs]}
    @param current_user: Injected from JWT token
    @param db: Database session
    @returns {dict} {success, message, deleted_count}
    """
    from sqlalchemy import delete as sql_delete
    
    try:
        # Convert to UUIDs
        trans_ids = [str(uuid.UUID(tid)) for tid in request.transaction_ids]
        
        # Delete all transactions
        delete_query = sql_delete(Transaction).where(
            and_(
                Transaction.id.in_(trans_ids),
                Transaction.user_id == str(current_user.id)
            )
        )
        
        result = await db.execute(delete_query)
        await db.commit()
        
        print(f"✅ Deleted {result.rowcount} transactions")
        
        return {
            "success": True,
            "message": f"Deleted {result.rowcount} transactions",
            "deleted_count": result.rowcount
        }
    except Exception as e:
        await db.rollback()
        print(f"❌ Bulk delete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CSV/XLSX IMPORT ENDPOINT
# ============================================================================

@router.post("/import")
async def import_transactions(
    file: UploadFile = File(...),
    account_id: str = Form(...),
    auto_categorize: bool = Form(True),
    current_user: User = Depends(get_current_user),
    import_service: TransactionImportService = Depends(get_import_service)
):
    """
    Import transactions from CSV/XLSX file
    
    Process:
    1. Validate file format and size
    2. Parse CSV/XLSX
    3. Detect duplicates (hash_dedupe)
    4. Extract transaction data
    5. Auto-categorize if enabled (LLM/rules)
    6. Import to database
    7. Return import summary
    
    Supported formats:
    - Finnish bank CSV (OP, Nordea, etc.)
    - Standard CSV with columns: Date, Amount, Merchant, Memo
    - XLSX with same columns
    
    @param file: Uploaded CSV/XLSX file
    @param account_id: Target account UUID
    @param auto_categorize: Enable AI categorization (default: true)
    @param current_user: Injected from JWT token
    @param import_service: Injected TransactionImportService
    @returns {dict} Import result with statistics
    @raises HTTPException: 400 if invalid file, 500 on import failure
    """
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
    result = await import_service.import_from_csv(
        file_content=file_content,
        filename=file.filename,
        account_id=account_id,
        auto_categorize=auto_categorize
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    
    return result


# ============================================================================
# CATEGORY SYNC ENDPOINT
# ============================================================================

@router.post("/sync-categories")
async def sync_transaction_categories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Sync transaction category strings with Category table
    
    Fixes transactions where category was reassigned but strings not updated
    Useful after bulk category changes or category renames
    
    Process:
    1. Find all transactions with category_id
    2. Get category hierarchy (category → parent → grandparent)
    3. Update main_category, category, subcategory strings
    
    @param current_user: Injected from JWT token
    @param db: Database session
    @returns {dict} {success, updated_count, message}
    """
    # Get all transactions with category_id
    transactions_query = select(Transaction).where(
        and_(
            Transaction.user_id == current_user.id,
            Transaction.category_id.isnot(None)
        )
    )
    
    transactions_result = await db.execute(transactions_query)
    transactions = transactions_result.scalars().all()
    
    updated_count = 0
    
    for transaction in transactions:
        # Get the assigned category with parents
        category_query = select(Category).options(
            selectinload(Category.parent).selectinload(Category.parent)
        ).where(Category.id == transaction.category_id)
        category_result = await db.execute(category_query)
        category = category_result.scalar()
        
        if not category:
            continue
        
        # Update category strings based on hierarchy
        if category.parent:
            if category.parent.parent:
                # 3-level: grandparent = main, parent = category, self = subcategory
                transaction.main_category = category.parent.parent.name
                transaction.category = category.parent.name
                transaction.subcategory = category.name
            else:
                # 2-level: parent = main, self = category
                transaction.main_category = category.parent.name
                transaction.category = category.name
                transaction.subcategory = None
        else:
            # 1-level: self = main
            transaction.main_category = category.name
            transaction.category = None
            transaction.subcategory = None
        
        updated_count += 1
    
    await db.commit()
    
    print(f"✅ Synced {updated_count} transaction categories")
    
    return {
        "success": True,
        "updated_count": updated_count,
        "message": f"Synced {updated_count} transactions with current category names"
    }


# ============================================================================
# CREATE TRANSACTION ENDPOINT
# ============================================================================

@router.post("/create")
async def create_transaction(
    data: TransactionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create new transaction manually
    
    Process:
    1. Parse date from ISO string
    2. Determine is_income/is_expense from amount sign
    3. Extract date components (year, month, weekday)
    4. Get category hierarchy if category_id provided
    5. Create transaction with synced category strings
    
    @param data: Transaction creation data
    @param current_user: Injected from JWT token
    @param db: Database session
    @returns {dict} {success, message, transaction_id}
    @raises HTTPException: 500 on creation failure
    """
    try:
        # Parse date
        posted_at = datetime.fromisoformat(data.posted_at.replace('Z', '+00:00'))
        
        # Determine transaction type from amount sign
        is_income = data.amount > 0
        is_expense = data.amount < 0
        
        # Extract date components for filtering
        year = posted_at.year
        month = posted_at.month
        year_month = posted_at.strftime('%Y-%m')
        weekday = posted_at.strftime('%A')
        
        # Get category hierarchy for syncing strings
        main_category = None
        category = None
        subcategory = None
        
        if data.category_id:
            cat_query = select(Category).options(
                selectinload(Category.parent).selectinload(Category.parent)
            ).where(Category.id == data.category_id)
            cat_result = await db.execute(cat_query)
            cat = cat_result.scalar_one_or_none()
            
            if cat:
                # Determine hierarchy level
                if cat.parent:
                    if cat.parent.parent:
                        # 3-level: grandparent = main, parent = category, self = subcategory
                        main_category = cat.parent.parent.name
                        category = cat.parent.name
                        subcategory = cat.name
                    else:
                        # 2-level: parent = main, self = category
                        main_category = cat.parent.name
                        category = cat.name
                        subcategory = None
                else:
                    # 1-level: self = main
                    main_category = cat.name
                    category = None
                    subcategory = None
        
        # Create transaction
        transaction = Transaction(
            id=str(uuid.uuid4()),
            user_id=str(current_user.id),
            account_id=None,
            posted_at=posted_at,
            amount=data.amount,
            currency='EUR',
            merchant=data.merchant,
            memo=data.memo,
            owner=data.owner,
            bank_account_type=data.bank_account_type,
            main_category=main_category,
            category=category,
            subcategory=subcategory,
            category_id=data.category_id,
            is_income=is_income,
            is_expense=is_expense,
            year=year,
            month=month,
            year_month=year_month,
            weekday=weekday,
            source_category='user',
            review_needed=not data.category_id  # Flag for review if uncategorized
        )
        
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)
        
        print(f"✅ Created transaction: {transaction.id}")
        
        return {
            "success": True,
            "message": "Transaction created successfully",
            "transaction_id": str(transaction.id)
        }
        
    except Exception as e:
        await db.rollback()
        print(f"❌ Create failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))