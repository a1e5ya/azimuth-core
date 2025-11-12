"""
Main transactions router with CRUD operations - FIXED
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, distinct
from typing import List, Optional
from datetime import date, datetime
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
    """Get paginated list of transactions with enhanced filters"""
    
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
    
    transactions, total_count = await queries.get_transactions_with_filters(filters)    
    response_data = []
    for transaction in transactions:
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

@router.get("/summary", response_model=TransactionSummary)
async def get_transaction_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    queries: TransactionQueries = Depends(get_transaction_queries)
):
    """Get comprehensive transaction summary with analytics"""
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
    """Get summary stats for filtered transactions (all pages)"""
    
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
        conditions.append(Transaction.main_category.in_(main_categories))
    if categories and len(categories) > 0:
        conditions.append(Transaction.category.in_(categories))
    if subcategories and len(subcategories) > 0:
        conditions.append(Transaction.subcategory.in_(subcategories))
    
    base_condition = and_(*conditions)
    
    # Total count and categorized
    stats_query = select(
        func.count(Transaction.id).label('total'),
        func.count(Transaction.category_id).label('categorized'),
        func.coalesce(func.sum(func.abs(Transaction.amount)), 0).label('total_amount')
    ).where(base_condition)
    
    stats_result = await db.execute(stats_query)
    stats = stats_result.first()
    
    # Count transactions with category = "-" (uncategorized in CSV)
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
    
    Modes:
    - training: Pre-categorized data with auto-category creation
    - account: Uncategorized bank data to specific account
    """
    
    # Validate file
    if not file.filename.lower().endswith(('.csv', '.xlsx')):
        raise HTTPException(status_code=400, detail="Only CSV and XLSX files supported")
    
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    # Validate mode
    if import_mode not in ['training', 'account']:
        raise HTTPException(status_code=400, detail="Invalid import_mode. Use 'training' or 'account'")
    
    # For account mode, account_id is required
    if import_mode == 'account' and not account_id:
        raise HTTPException(status_code=400, detail="account_id required for account mode")
    
    # Read file
    try:
        file_content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")
    
    # Import
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

@router.post("/categorize/{transaction_id}")
async def categorize_transaction(
    transaction_id: str,
    category_id: str = Query(...),
    service: TransactionService = Depends(get_transaction_service)
):
    """Manually categorize a transaction"""
    result = await service.categorize_transaction(transaction_id, category_id)
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    
    return result

@router.post("/bulk-categorize", response_model=BulkOperationResponse)
async def bulk_categorize_transactions(
    request: BulkCategorizeRequest,
    service: TransactionService = Depends(get_transaction_service)
):
    """Bulk categorize multiple transactions"""
    return BulkOperationResponse(success=False, message="Not implemented yet", updated_count=0)

@router.delete("/{transaction_id}", response_model=DeleteResponse)
async def delete_transaction(
    transaction_id: str,
    service: TransactionService = Depends(get_transaction_service)
):
    """Delete a single transaction"""
    result = await service.delete_transaction(transaction_id)
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    
    return DeleteResponse(**result)

@router.post("/reset")
async def reset_all_transactions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reset all transaction data for the current user"""
    from sqlalchemy import delete
    from ..models.database import Transaction, ImportBatch
    
    count_query = select(func.count(Transaction.id)).where(Transaction.user_id == current_user.id)
    count_result = await db.execute(count_query)
    transaction_count = count_result.scalar()
    
    await db.execute(delete(Transaction).where(Transaction.user_id == current_user.id))
    await db.execute(delete(ImportBatch).where(ImportBatch.user_id == current_user.id))
    await db.commit()
    
    return {
        "success": True,
        "message": f"Successfully deleted {transaction_count} transactions",
        "deleted_count": transaction_count
    }

@router.get("/filter-metadata")
async def get_filter_metadata(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get unique values for filter dropdowns - FIXED"""
    
    # Get unique owners and account types
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
    
    owner_account_map = {}
    for owner, account_type in owner_account_result:
        if owner not in owner_account_map:
            owner_account_map[owner] = []
        if account_type not in owner_account_map[owner]:
            owner_account_map[owner].append(account_type)
    
    # Sort account types for each owner
    for owner in owner_account_map:
        owner_account_map[owner].sort()
    
    # Get unique main categories
    main_cat_query = select(Transaction.main_category).where(
        and_(
            Transaction.user_id == current_user.id,
            Transaction.main_category.isnot(None)
        )
    ).distinct()
    
    main_cat_result = await db.execute(main_cat_query)
    main_categories = sorted([row[0] for row in main_cat_result])
    
    # Build category/subcategory maps
    category_query = select(
        Transaction.main_category,
        Transaction.category,
        Transaction.subcategory
    ).where(
        and_(
            Transaction.user_id == current_user.id,
            Transaction.main_category.isnot(None)
        )
    ).distinct()
    
    category_result = await db.execute(category_query)
    
    category_map = {}
    subcategory_map = {}
    
    for main_cat, cat, subcat in category_result:
        if main_cat:
            if cat:
                if main_cat not in category_map:
                    category_map[main_cat] = set()
                category_map[main_cat].add(cat)
                
                if subcat:
                    key = f"{main_cat}|{cat}"
                    if key not in subcategory_map:
                        subcategory_map[key] = set()
                    subcategory_map[key].add(subcat)
    
    # Convert sets to sorted lists
    category_map_list = {}
    for main_cat, cats in category_map.items():
        category_map_list[main_cat] = sorted(list(cats))
    
    subcategory_map_list = {}
    for key, subcats in subcategory_map.items():
        subcategory_map_list[key] = sorted(list(subcats))
    
    return {
        "ownerAccountMap": owner_account_map,
        "mainCategories": main_categories,
        "categoryMap": category_map_list,
        "subcategoryMap": subcategory_map_list
    }