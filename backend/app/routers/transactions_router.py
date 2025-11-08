"""
Main transactions router with CRUD operations - FIXED IMPORTS
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional
from datetime import date, datetime
import uuid

from ..models.database import get_db, User, Transaction, Category, AuditLog
from ..services.transaction_service import (
    TransactionService, 
    TransactionQueries,
    get_transaction_service,
    get_transaction_queries
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
        'main_categories': main_categories or [], 'sort_by': sort_by, 'sort_order': sort_order
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
    # Note: bulk_categorize not in merged service - needs adding if used
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
    """Get unique values for filter dropdowns"""
    from sqlalchemy import distinct
    
    owners_query = select(distinct(Transaction.owner)).where(
        and_(Transaction.user_id == current_user.id, Transaction.owner.isnot(None))
    )
    owners_result = await db.execute(owners_query)
    unique_owners = [row[0] for row in owners_result]
    
    account_types_query = select(distinct(Transaction.bank_account_type)).where(
        and_(Transaction.user_id == current_user.id, Transaction.bank_account_type.isnot(None))
    )
    account_types_result = await db.execute(account_types_query)
    unique_account_types = [row[0] for row in account_types_result]
    
    return {
        "owners": unique_owners,
        "account_types": unique_account_types
    }