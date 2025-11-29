"""
Transactions Router - Main API endpoints for transaction CRUD operations

This module provides comprehensive REST API endpoints for managing financial transactions,
including listing, filtering, importing, categorizing, and bulk operations.

Features:
- Transaction listing with advanced filtering and pagination
- CSV/XLSX file import with training and account modes
- Single and bulk categorization
- Transaction CRUD operations (create, read, update, delete)
- Category metadata and filter options
- Transaction summary and statistics
- Async import job status tracking

Endpoints:
- GET /list: Paginated transaction listing with filters
- GET /summary: Overall transaction statistics
- GET /filtered-summary: Statistics for filtered results
- POST /import: Import transactions from CSV/XLSX
- GET /import/status/{job_id}: Check import job progress
- POST /categorize/{transaction_id}: Categorize single transaction
- POST /bulk-categorize: Categorize multiple transactions
- POST /create: Create new transaction
- PUT /{transaction_id}: Update transaction
- DELETE /{transaction_id}: Delete single transaction
- POST /bulk-delete: Delete multiple transactions
- GET /filter-metadata: Get available filter options
- POST /sync-category-strings: Sync transaction category names

Dependencies:
- FastAPI for routing and validation
- SQLAlchemy for database operations
- Transaction services for business logic
- Authentication for user context
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

# ========================================
# HELPER FUNCTIONS
# ========================================

def ensure_list(param: Optional[Union[str, List[str]]]) -> Optional[List[str]]:
    """
    Convert string parameters to single-item lists for FastAPI Query compatibility
    
    FastAPI Query parameters can be received as strings (single value) or lists (multiple values).
    This helper ensures consistent list format for filter processing.
    
    Args:
        param: Query parameter value (string, list, or None)
        
    Returns:
        List of strings, or None if input was None
        
    Example:
        ensure_list("Alexa") -> ["Alexa"]
        ensure_list(["Alexa", "John"]) -> ["Alexa", "John"]
        ensure_list(None) -> None
    """
    if param is None:
        return None
    if isinstance(param, str):
        return [param]
    return param

# ========================================
# REQUEST MODELS
# ========================================

class TransactionUpdateRequest(BaseModel):
    """Request model for updating transaction fields"""
    merchant: Optional[str] = None
    amount: Optional[float] = None
    memo: Optional[str] = None
    category_id: Optional[str] = None

class BulkDeleteRequest(BaseModel):
    """Request model for bulk delete operations"""
    transaction_ids: List[str]

class TransactionCreateRequest(BaseModel):
    """
    Request model for creating new transactions
    
    All date-related fields (year, month, year_month, weekday) are automatically
    calculated from posted_at during creation.
    """
    posted_at: str  # ISO date string
    amount: float
    merchant: Optional[str] = None
    memo: Optional[str] = None
    owner: Optional[str] = None
    bank_account_type: Optional[str] = None
    category_id: Optional[str] = None


# ========================================
# TRANSACTION LISTING & FILTERING
# ========================================

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
    categories: Optional[List[str]] = Query(None),  
    subcategories: Optional[List[str]] = Query(None),  
    sort_by: str = Query("posted_at", regex="^(posted_at|amount|merchant|created_at)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: User = Depends(get_current_user),
    queries: TransactionQueries = Depends(get_transaction_queries)
):
    """
    Get paginated list of transactions with comprehensive filtering
    
    This endpoint supports multi-level category filtering (type -> category -> subcategory),
    owner/account filtering, date ranges, and amount ranges. Results are paginated and sortable.
    
    Query Parameters:
        page: Page number (1-indexed)
        limit: Items per page (1-1000)
        start_date: Filter transactions on or after this date
        end_date: Filter transactions on or before this date
        min_amount: Minimum transaction amount (negative for expenses)
        max_amount: Maximum transaction amount (negative for expenses)
        merchant: Search by merchant name (case-insensitive partial match)
        category_id: Filter by specific category UUID
        account_id: Filter by specific account UUID
        main_category: Filter by main category name
        review_needed: Filter by review status (True/False)
        owners: Filter by owner names (multiple allowed)
        account_types: Filter by account types (multiple allowed)
        main_categories: Filter by main category names (multiple allowed)
        categories: Filter by category names (multiple allowed)
        subcategories: Filter by subcategory names (multiple allowed)
        sort_by: Sort field (posted_at, amount, merchant, created_at)
        sort_order: Sort direction (asc, desc)
        
    Returns:
        List of TransactionResponse objects with full category hierarchy
        
    Note:
        Category hierarchy is automatically populated from assigned_category relationship.
        If transaction has no assigned category, falls back to CSV-imported category strings.
    """
    # Build comprehensive filter dictionary
    filters = {
        'page': page, 'limit': limit, 'start_date': start_date, 'end_date': end_date,
        'min_amount': min_amount, 'max_amount': max_amount, 'merchant': merchant,
        'category_id': category_id, 'account_id': account_id, 'main_category': main_category,
        'review_needed': review_needed, 'owners': owners or [], 'account_types': account_types or [],
        'main_categories': main_categories or [], 
        'categories': categories or [],  
        'subcategories': subcategories or [],  
        'sort_by': sort_by, 'sort_order': sort_order
    }
    
    # Execute filtered query with pagination
    transactions, total_count = await queries.get_transactions_with_filters(filters)    
    
    # Build response with category hierarchy
    response_data = []
    for transaction in transactions:
        # Extract parent category name if exists
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

# ========================================
# TRANSACTION STATISTICS
# ========================================

@router.get("/summary", response_model=TransactionSummary)
async def get_transaction_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    queries: TransactionQueries = Depends(get_transaction_queries)
):
    """
    Get comprehensive transaction summary with analytics
    
    Provides aggregate statistics including total transactions, income, expenses,
    categorization rates, and date ranges. Optional date filtering.
    
    Query Parameters:
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        
    Returns:
        TransactionSummary with counts, amounts, and categorization statistics
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
    Get summary statistics for filtered transactions (all pages)
    
    Unlike /list which is paginated, this endpoint returns aggregate stats for ALL
    transactions matching the filters. Useful for displaying total counts and amounts
    while user navigates through paginated results.
    
    Query Parameters:
        Same as /list endpoint filters
        
    Returns:
        Dict with filtered_count, categorized_count, uncategorized_count, total_amount
        
    Note:
        Axios sends single values as strings, so we normalize to lists for consistency
    """
    # Convert single string params to lists (axios paramsSerializer compatibility)
    main_categories = ensure_list(main_categories)
    categories = ensure_list(categories)
    subcategories = ensure_list(subcategories)
    owners = ensure_list(owners)
    account_types = ensure_list(account_types)
    
    # Build filter conditions
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
        # Case-insensitive comparison for category names
        conditions.append(func.upper(Transaction.main_category).in_([m.upper() for m in main_categories]))
    if categories and len(categories) > 0:
        conditions.append(func.upper(Transaction.category).in_([c.upper() for c in categories]))
    if subcategories and len(subcategories) > 0:
        conditions.append(func.upper(Transaction.subcategory).in_([s.upper() for s in subcategories]))
    
    base_condition = and_(*conditions)
    
    # Get total count, categorized count, and total amount
    stats_query = select(
        func.count(Transaction.id).label('total'),
        func.count(Transaction.category_id).label('categorized'),
        func.coalesce(func.sum(func.abs(Transaction.amount)), 0).label('total_amount')
    ).where(base_condition)
    
    stats_result = await db.execute(stats_query)
    stats = stats_result.first()
    
    # Count transactions with category = "Uncategorized" (from CSV import)
    uncategorized_query = select(func.count(Transaction.id)).where(
        and_(base_condition, Transaction.category == "Uncategorized")
    )
    uncategorized_result = await db.execute(uncategorized_query)
    uncategorized_count = uncategorized_result.scalar() or 0
    
    return {
        "filtered_count": stats.total or 0,
        "categorized_count": stats.categorized or 0,
        "uncategorized_count": uncategorized_count,
        "total_amount": float(stats.total_amount or 0)
    }

# ========================================
# TRANSACTION IMPORT
# ========================================

@router.get("/import/status/{job_id}")
async def get_import_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get import job status for polling
    
    Used by frontend to track progress of async import operations.
    Returns job status, progress, and results when complete.
    
    Path Parameters:
        job_id: Unique identifier for the import job
        
    Returns:
        Job status object with progress information
        
    Raises:
        404: Job not found
        403: Job belongs to different user
    """
    from ..services.import_jobs import get_job
    
    job = get_job(job_id)
    
    if not job:
        raise HTTPException(404, "Job not found")
    
    # Verify job belongs to current user
    if job["user_id"] != str(current_user.id):
        raise HTTPException(403, "Access denied")
    
    return job

@router.post("/import")
async def import_transactions(
    file: UploadFile = File(...),
    import_mode: str = Form("training"),
    account_id: Optional[str] = Form(None),
    auto_categorize: bool = Form(True),
    current_user: User = Depends(get_current_user),
    import_service: TransactionImportService = Depends(get_import_service)
):
    """
    Import transactions from CSV/XLSX file
    
    Supports two import modes:
    1. Training Mode: Pre-categorized data with automatic category creation
       - Expects columns: Date, Amount, Merchant, Category, etc.
       - Auto-creates categories if they don't exist
       - Extracts training patterns for LLM categorization
       
    2. Account Mode: Uncategorized bank data to specific account
       - Requires account_id parameter
       - Raw bank export data
       - Can trigger automatic categorization via LLM
    
    Form Parameters:
        file: CSV or XLSX file (max 10MB)
        import_mode: 'training' or 'account'
        account_id: Required for account mode - target account UUID
        auto_categorize: Enable LLM categorization (default True)
        
    Returns:
        Import result with job_id for status tracking
        
    Raises:
        400: Invalid file format, file too large, or missing account_id
        500: Import processing failed
        
    Note:
        Import is async - use job_id with /import/status endpoint to track progress
    """
    # Validate file format
    if not file.filename.lower().endswith(('.csv', '.xlsx')):
        raise HTTPException(status_code=400, detail="Only CSV and XLSX files supported")
    
    # Validate file size (10MB limit)
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    # Validate import mode
    if import_mode not in ['training', 'account']:
        raise HTTPException(status_code=400, detail="Invalid import_mode. Use 'training' or 'account'")
    
    # For account mode, account_id is required
    if import_mode == 'account' and not account_id:
        raise HTTPException(status_code=400, detail="account_id required for account mode")
    
    # Read file content
    try:
        file_content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")
    
    # Start async import
    result = await import_service.import_from_csv(
        file_content=file_content,
        filename=file.filename,
        import_mode=import_mode,
        account_id=account_id,
        auto_categorize=auto_categorize
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    
    return result

# ========================================
# TRANSACTION CATEGORIZATION
# ========================================

@router.post("/categorize/{transaction_id}")
async def categorize_transaction(
    transaction_id: str,
    category_id: str = Query(...),
    service: TransactionService = Depends(get_transaction_service)
):
    """
    Manually categorize a single transaction
    
    Assigns a category to a transaction and updates related fields:
    - Sets category_id
    - Derives main_category, category, subcategory from hierarchy
    - Sets source_category to 'user'
    - Marks review_needed as False
    
    Path Parameters:
        transaction_id: UUID of transaction to categorize
        
    Query Parameters:
        category_id: UUID of category to assign
        
    Returns:
        Success response with message
        
    Raises:
        404: Transaction or category not found
    """
    result = await service.categorize_transaction(transaction_id, category_id)
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    
    return result

@router.post("/bulk-categorize", response_model=BulkOperationResponse)
async def bulk_categorize_transactions(
    request: BulkCategorizeRequest,
    service: TransactionService = Depends(get_transaction_service)
):
    """
    Bulk categorize multiple transactions
    
    Assigns the same category to multiple transactions simultaneously.
    Useful for correcting LLM categorization or batch organizing.
    
    Request Body:
        transaction_ids: List of transaction UUIDs
        category_id: Category UUID to assign to all
        confidence: Optional confidence score (0-1)
        
    Returns:
        BulkOperationResponse with updated_count and details
    """
    result = await service.bulk_categorize(
        transaction_ids=request.transaction_ids,
        category_id=request.category_id,
        confidence=request.confidence
    )
    
    return BulkOperationResponse(**result)

# ========================================
# TRANSACTION CRUD OPERATIONS
# ========================================

@router.delete("/{transaction_id}", response_model=DeleteResponse)
async def delete_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a single transaction
    
    Permanently removes a transaction from the database. Only the owner
    can delete their transactions.
    
    Path Parameters:
        transaction_id: UUID of transaction to delete
        
    Returns:
        DeleteResponse with success status and deleted_count
        
    Raises:
        404: Transaction not found or doesn't belong to user
        500: Database error during deletion
    """
    from sqlalchemy import delete as sql_delete
    
    try:
        # Convert to UUID and validate format
        trans_uuid = str(uuid.UUID(transaction_id))
        
        print(f"🗑️ Deleting transaction: {trans_uuid}")
        
        # Execute DELETE with user ownership check
        delete_query = sql_delete(Transaction).where(
            and_(
                Transaction.id == trans_uuid,
                Transaction.user_id == str(current_user.id)
            )
        )
        
        result = await db.execute(delete_query)
        deleted_count = result.rowcount
        
        print(f"✅ Rows affected: {deleted_count}")
        
        await db.commit()
        
        if deleted_count == 0:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        return DeleteResponse(
            success=True,
            message="Transaction deleted",
            deleted_count=deleted_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        print(f"❌ Delete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{transaction_id}")
async def update_transaction(
    transaction_id: str,
    data: TransactionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update transaction details
    
    Allows editing all transaction fields including date, amount, merchant, memo,
    owner, account type, and category. Category assignment automatically derives
    the 3-level hierarchy (main_category, category, subcategory).
    
    Path Parameters:
        transaction_id: UUID of transaction to update
        
    Request Body:
        TransactionCreateRequest with updated fields
        
    Returns:
        Success response with message
        
    Raises:
        404: Transaction not found or doesn't belong to user
        500: Database error during update
        
    Note:
        - Date changes automatically recalculate year, month, year_month, weekday
        - Amount changes automatically update is_income and is_expense flags
        - Category changes derive full hierarchy from Category tree
    """
    from datetime import datetime
    
    try:
        trans_uuid = str(uuid.UUID(transaction_id))
        
        # Fetch transaction with ownership check
        transaction_query = select(Transaction).where(
            and_(
                Transaction.id == trans_uuid,
                Transaction.user_id == str(current_user.id)
            )
        )
        result = await db.execute(transaction_query)
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Update date and derived date fields
        if data.posted_at:
            posted_at = datetime.fromisoformat(data.posted_at.replace('Z', '+00:00'))
            transaction.posted_at = posted_at
            transaction.year = posted_at.year
            transaction.month = posted_at.month
            transaction.year_month = posted_at.strftime('%Y-%m')
            transaction.weekday = posted_at.strftime('%A')
        
        # Update amount and derived income/expense flags
        if data.amount is not None:
            transaction.amount = data.amount
            transaction.is_income = data.amount > 0
            transaction.is_expense = data.amount < 0
        
        # Update basic fields
        if data.merchant is not None:
            transaction.merchant = data.merchant
        if data.memo is not None:
            transaction.memo = data.memo
        if data.owner is not None:
            transaction.owner = data.owner
        if data.bank_account_type is not None:
            transaction.bank_account_type = data.bank_account_type
        
        # Update category and derive hierarchy
        if data.category_id:
            transaction.category_id = data.category_id
            transaction.source_category = "user"
            transaction.review_needed = False
            
            # Fetch category with parent relationships
            cat_query = select(Category).options(
                selectinload(Category.parent).selectinload(Category.parent)
            ).where(Category.id == data.category_id)
            cat_result = await db.execute(cat_query)
            cat = cat_result.scalar_one_or_none()
            
            if cat:
                # Determine hierarchy level and set appropriate fields
                if cat.parent:
                    if cat.parent.parent:
                        # 3-level: grandparent -> parent -> self
                        transaction.main_category = cat.parent.parent.name
                        transaction.category = cat.parent.name
                        transaction.subcategory = cat.name
                    else:
                        # 2-level: parent -> self
                        transaction.main_category = cat.parent.name
                        transaction.category = cat.name
                        transaction.subcategory = None
                else:
                    # 1-level: self only
                    transaction.main_category = cat.name
                    transaction.category = None
                    transaction.subcategory = None
        
        transaction.updated_at = datetime.utcnow()
        
        await db.commit()
        
        print(f"✅ Updated transaction {transaction_id}")
        
        return {
            "success": True,
            "message": "Transaction updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        print(f"❌ Update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create")
async def create_transaction(
    data: TransactionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create new transaction
    
    Creates a transaction from scratch with all required fields. Automatically
    calculates date-related fields and category hierarchy.
    
    Request Body:
        TransactionCreateRequest with transaction details
        
    Returns:
        Success response with new transaction_id
        
    Raises:
        500: Database error during creation
        
    Note:
        - Automatically generates UUID for new transaction
        - Derives year, month, year_month, weekday from posted_at
        - Derives is_income/is_expense from amount sign
        - Derives category hierarchy if category_id provided
        - Sets review_needed=True if no category assigned
    """
    from datetime import datetime
    
    try:
        # Parse date
        posted_at = datetime.fromisoformat(data.posted_at.replace('Z', '+00:00'))
        
        # Determine transaction type from amount
        is_income = data.amount > 0
        is_expense = data.amount < 0
        
        # Extract date components
        year = posted_at.year
        month = posted_at.month
        year_month = posted_at.strftime('%Y-%m')
        weekday = posted_at.strftime('%A')
        
        # Get category hierarchy if category provided
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
                        # 3-level: grandparent -> parent -> self
                        main_category = cat.parent.parent.name
                        category = cat.parent.name
                        subcategory = cat.name
                    else:
                        # 2-level: parent -> self
                        main_category = cat.parent.name
                        category = cat.name
                        subcategory = None
                else:
                    # 1-level: self only
                    main_category = cat.name
                    category = None
                    subcategory = None
        
        # Create transaction with all fields
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
            review_needed=not data.category_id
        )
        
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)
        
        return {
            "success": True,
            "message": "Transaction created successfully",
            "transaction_id": str(transaction.id)
        }
        
    except Exception as e:
        await db.rollback()
        print(f"❌ Create failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk-delete")
async def bulk_delete_transactions(
    request: BulkDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete multiple transactions
    
    Permanently removes multiple transactions in a single operation.
    Only deletes transactions belonging to the current user.
    
    Request Body:
        transaction_ids: List of transaction UUIDs to delete
        
    Returns:
        Success response with deleted_count
        
    Raises:
        500: Database error during deletion
    """
    from sqlalchemy import delete as sql_delete
    
    try:
        # Convert all IDs to UUIDs (validates format)
        trans_ids = [str(uuid.UUID(tid)) for tid in request.transaction_ids]
        
        # Execute bulk DELETE with ownership check
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

# ========================================
# FILTER METADATA & UTILITIES
# ========================================

@router.get("/filter-metadata")
async def get_filter_metadata(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get unique values for filter dropdowns - FROM ACTUAL TRANSACTION DATA
    
    Provides all available filter options based on existing transaction data:
    - Owner/Account combinations
    - Main categories (top-level types)
    - Categories (mid-level)
    - Subcategories (bottom-level)
    
    Returns a structured hierarchy that matches the 3-level category system.
    
    Returns:
        Dict with ownerAccountMap, mainCategories, categoryMap, subcategoryMap
        
    Note:
        All values are extracted from actual transactions, not from Category table.
        This ensures filters only show options that have data.
    """
    # Get unique owner and account type combinations
    owner_account_query = select(
        Transaction.owner,
        Transaction.bank_account_type
    ).where(
        and_(
            Transaction.user_id == current_user.id,
            Transaction.owner.isnot(None),
            Transaction.bank_account_type.isnot(None)
        )
    ).distinct()
    
    owner_account_result = await db.execute(owner_account_query)
    
    # Build owner -> [account_types] map
    owner_account_map = {}
    for owner, account_type in owner_account_result:
        if owner not in owner_account_map:
            owner_account_map[owner] = []
        if account_type not in owner_account_map[owner]:
            owner_account_map[owner].append(account_type)
    
    # Sort account types for each owner
    for owner in owner_account_map:
        owner_account_map[owner].sort()
    
    # Get category hierarchy from transactions
    categories_query = select(
        Transaction.main_category,
        Transaction.category,
        Transaction.subcategory
    ).where(
        and_(
            Transaction.user_id == current_user.id,
            Transaction.main_category.isnot(None)
        )
    ).distinct()
    
    categories_result = await db.execute(categories_query)
    
    # Build hierarchical category structure
    main_categories_set = set()
    category_map = {}  # main_category -> [categories]
    subcategory_map = {}  # "main_category|category" -> [subcategories]
    
    for main_cat, cat, subcat in categories_result:
        if main_cat:
            main_categories_set.add(main_cat)
            
            if cat:
                # Add to category map
                if main_cat not in category_map:
                    category_map[main_cat] = set()
                category_map[main_cat].add(cat)
                
                if subcat:
                    # Add to subcategory map with compound key
                    key = f"{main_cat}|{cat}"
                    if key not in subcategory_map:
                        subcategory_map[key] = set()
                    subcategory_map[key].add(subcat)
    
    # Convert sets to sorted lists
    main_categories = sorted(list(main_categories_set))
    
    category_map_final = {}
    for main_cat in category_map:
        category_map_final[main_cat] = sorted(list(category_map[main_cat]))
    
    subcategory_map_final = {}
    for key in subcategory_map:
        subcategory_map_final[key] = sorted(list(subcategory_map[key]))
    
    return {
        "ownerAccountMap": owner_account_map,
        "mainCategories": main_categories,
        "categoryMap": category_map_final,
        "subcategoryMap": subcategory_map_final
    }

@router.get("/debug/main-categories")
async def debug_main_categories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Debug endpoint: Check actual main_category values in database
    
    Returns all unique main_category values with transaction counts.
    Useful for debugging category hierarchy issues or data inconsistencies.
    
    Returns:
        Dict with main_categories list and total_transactions count
    """
    from sqlalchemy import func, distinct
    
    # Get all unique main_category values with counts
    query = select(
        Transaction.main_category,
        func.count(Transaction.id).label('count')
    ).where(
        Transaction.user_id == current_user.id
    ).group_by(
        Transaction.main_category
    ).order_by(
        desc(func.count(Transaction.id))
    )
    
    result = await db.execute(query)
    categories = result.all()
    
    return {
        "main_categories": [
            {"value": cat.main_category, "count": cat.count}
            for cat in categories
        ],
        "total_transactions": sum(cat.count for cat in categories)
    }

@router.post("/sync-category-strings")
async def sync_category_strings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Sync transaction category strings with Category table
    
    Updates main_category, category, and subcategory strings on transactions
    to match current category names from the Category tree. Useful after:
    - Renaming categories
    - Reassigning transactions to different categories
    - Fixing category hierarchy inconsistencies
    
    Process:
    1. Find all transactions with category_id
    2. Fetch assigned category with parent hierarchy
    3. Update string fields based on hierarchy level
    
    Returns:
        Success response with updated_count
        
    Note:
        This operation can be slow for large transaction sets.
        It's a maintenance operation, not for regular use.
    """
    # Get all transactions with assigned categories
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
        # Get the assigned category with hierarchy
        category_query = select(Category).where(Category.id == transaction.category_id)
        category_result = await db.execute(category_query)
        category = category_result.scalar()
        
        if not category:
            continue
        
        # Get parent and grandparent
        parent = None
        grandparent = None
        
        if category.parent_id:
            parent_query = select(Category).where(Category.id == category.parent_id)
            parent_result = await db.execute(parent_query)
            parent = parent_result.scalar()
            
            if parent and parent.parent_id:
                grandparent_query = select(Category).where(Category.id == parent.parent_id)
                grandparent_result = await db.execute(grandparent_query)
                grandparent = grandparent_result.scalar()
        
        # Update transaction strings based on category hierarchy
        if grandparent and parent:
            # 3-level: grandparent = main, parent = category, self = subcategory
            transaction.main_category = grandparent.name
            transaction.category = parent.name
            transaction.subcategory = category.name
        elif parent:
            # 2-level: parent = main, self = category
            transaction.main_category = parent.name
            transaction.category = category.name
            transaction.subcategory = None
        else:
            # 1-level: self = main
            transaction.main_category = category.name
            transaction.category = None
            transaction.subcategory = None
        
        updated_count += 1
    
    await db.commit()
    
    return {
        "success": True,
        "updated_count": updated_count,
        "message": f"Synced {updated_count} transactions with current category names"
    }