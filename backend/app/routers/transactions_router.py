"""
Main transactions router with CRUD operations - FIXED
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional
from datetime import date, datetime
import uuid

from ..models.database import get_db, User, Transaction, Category, AuditLog
from ..services.transaction_service import TransactionService, get_transaction_service
from ..routers.transaction_queries import TransactionQueries, get_transaction_queries
from ..routers.transaction_models import (
    TransactionResponse, TransactionSummary, DeleteResponse,
    CategoryAssignment, TransactionUpdate, BulkCategorizeRequest,
    TransactionFilters, ReviewTransactionsResponse, BulkOperationResponse
)
from ..routers.auth import get_current_user

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
    db: AsyncSession = Depends(get_db)
):
    """Get paginated list of transactions with enhanced filters"""
    
    print(f"📋 Transaction list request: page={page}, limit={limit}")
    
    filters = TransactionFilters(
        page=page,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        min_amount=min_amount,
        max_amount=max_amount,
        merchant=merchant,
        category_id=category_id,
        account_id=account_id,
        main_category=main_category,
        review_needed=review_needed,
        owners=owners if owners else [],
        account_types=account_types if account_types else [],
        main_categories=main_categories if main_categories else [],
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    queries = get_transaction_queries(db, current_user)
    transactions, total_count = await queries.get_transactions_with_filters(filters)
    
    print(f"✅ Found {len(transactions)} transactions (total: {total_count})")
    
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive transaction summary with analytics"""
    
    print(f"📊 Transaction summary request for user: {current_user.email}")
    
    queries = get_transaction_queries(db, current_user)
    summary_data = await queries.get_transaction_summary(start_date, end_date)
    
    return TransactionSummary(**summary_data)

@router.post("/categorize/{transaction_id}")
async def categorize_transaction(
    transaction_id: str,
    category_id: str = Query(..., description="Category ID to assign"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually categorize a transaction"""
    
    print(f"🏷️ Categorize transaction: {transaction_id} -> {category_id}")
    
    try:
        trans_uuid = uuid.UUID(transaction_id)
        cat_uuid = uuid.UUID(category_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    # Get transaction
    trans_query = select(Transaction).where(
        and_(
            Transaction.id == trans_uuid,
            Transaction.user_id == current_user.id
        )
    )
    trans_result = await db.execute(trans_query)
    transaction = trans_result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Get category
    cat_query = select(Category).where(
        and_(
            Category.id == cat_uuid,
            Category.user_id == current_user.id
        )
    )
    cat_result = await db.execute(cat_query)
    category = cat_result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Update transaction
    transaction.category_id = cat_uuid
    transaction.source_category = "user"
    transaction.confidence_score = 1.0
    transaction.review_needed = False
    transaction.updated_at = datetime.utcnow()
    
    await db.commit()
    
    print(f"✅ Transaction categorized as: {category.name}")
    
    return {
        "success": True,
        "message": f"Transaction categorized as {category.name}",
        "category": {
            "id": str(category.id),
            "name": category.name,
            "icon": category.icon
        }
    }

@router.post("/bulk-categorize", response_model=BulkOperationResponse)
async def bulk_categorize_transactions(
    request: BulkCategorizeRequest,
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    """Bulk categorize multiple transactions"""
    
    print(f"🏷️ Bulk categorize: {len(request.transaction_ids)} transactions -> {request.category_id}")
    
    result = await transaction_service.bulk_categorize_transactions(
        transaction_ids=request.transaction_ids,
        category_id=request.category_id,
        confidence=request.confidence
    )
    
    if not result["success"]:
        if "not found" in result["message"].lower():
            raise HTTPException(status_code=404, detail=result["message"])
        elif "access denied" in result["message"].lower():
            raise HTTPException(status_code=403, detail=result["message"])
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    
    return BulkOperationResponse(
        success=result["success"],
        message=result["message"],
        updated_count=result["updated_count"]
    )

@router.delete("/{transaction_id}", response_model=DeleteResponse)
async def delete_transaction(
    transaction_id: str,
    transaction_service: TransactionService = Depends(get_transaction_service)
):
    """Delete a single transaction"""
    
    print(f"🗑️ Delete transaction request: {transaction_id}")
    
    result = await transaction_service.delete_transaction(transaction_id)
    
    if not result["success"]:
        if "not found" in result["message"].lower():
            raise HTTPException(status_code=404, detail=result["message"])
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    
    return DeleteResponse(**result)

@router.post("/reset")
async def reset_all_transactions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reset all transaction data for the current user"""
    
    try:
        from sqlalchemy import delete
        from ..models.database import Transaction, ImportBatch
        
        count_query = select(func.count(Transaction.id)).where(Transaction.user_id == current_user.id)
        count_result = await db.execute(count_query)
        transaction_count = count_result.scalar()
        
        delete_transactions = delete(Transaction).where(Transaction.user_id == current_user.id)
        await db.execute(delete_transactions)
        
        delete_batches = delete(ImportBatch).where(ImportBatch.user_id == current_user.id)
        await db.execute(delete_batches)
        
        await db.commit()
        
        audit_entry = AuditLog(
            user_id=current_user.id,
            entity="transaction",
            action="reset_all",
            details={
                "transactions_deleted": transaction_count,
                "reason": "user_requested_reset"
            }
        )
        db.add(audit_entry)
        await db.commit()
        
        print(f"✅ Reset complete: {transaction_count} transactions deleted for user {current_user.email}")
        
        return {
            "success": True,
            "message": f"Successfully deleted {transaction_count} transactions",
            "deleted_count": transaction_count
        }
        
    except Exception as e:
        print(f"❌ Reset failed for user {current_user.email}: {e}")
        await db.rollback()
        return {
            "success": False,
            "message": f"Reset failed: {str(e)}",
            "deleted_count": 0
        }

@router.get("/filter-metadata")
async def get_filter_metadata(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get unique values for filter dropdowns - optimized query"""
    
    from sqlalchemy import distinct
    
    print(f"📊 Getting filter metadata for user: {current_user.email}")
    
    try:
        # Get unique owners
        owners_query = select(distinct(Transaction.owner)).where(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.owner.isnot(None),
                Transaction.owner != ''
            )
        ).order_by(Transaction.owner)
        
        owners_result = await db.execute(owners_query)
        unique_owners = [row[0] for row in owners_result]
        
        # Get unique account types  
        account_types_query = select(distinct(Transaction.bank_account_type)).where(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.bank_account_type.isnot(None),
                Transaction.bank_account_type != ''
            )
        ).order_by(Transaction.bank_account_type)
        
        account_types_result = await db.execute(account_types_query)
        unique_account_types = [row[0] for row in account_types_result]
        
        # Get owner -> account type mapping
        owner_account_query = select(
            Transaction.owner,
            Transaction.bank_account_type
        ).where(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.owner.isnot(None),
                Transaction.owner != '',
                Transaction.bank_account_type.isnot(None),
                Transaction.bank_account_type != ''
            )
        ).distinct()
        
        owner_account_result = await db.execute(owner_account_query)
        
        owner_account_map = {}
        for row in owner_account_result:
            owner = row.owner
            account_type = row.bank_account_type
            
            if owner not in owner_account_map:
                owner_account_map[owner] = []
            if account_type not in owner_account_map[owner]:
                owner_account_map[owner].append(account_type)
        
        # Sort account types for each owner
        for owner in owner_account_map:
            owner_account_map[owner].sort()
        
        # Get unique main categories
        main_categories_query = select(distinct(Transaction.main_category)).where(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.main_category.isnot(None),
                Transaction.main_category != ''
            )
        ).order_by(Transaction.main_category)
        
        main_categories_result = await db.execute(main_categories_query)
        unique_main_categories = [row[0] for row in main_categories_result]
        
        # Get unique categories per main category
        categories_query = select(
            Transaction.main_category,
            Transaction.category
        ).where(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.main_category.isnot(None),
                Transaction.main_category != '',
                Transaction.category.isnot(None),
                Transaction.category != ''
            )
        ).distinct()
        
        categories_result = await db.execute(categories_query)
        
        category_map = {}
        for row in categories_result:
            main_cat = row.main_category
            category = row.category
            
            if main_cat not in category_map:
                category_map[main_cat] = []
            if category not in category_map[main_cat]:
                category_map[main_cat].append(category)
        
        # Sort categories
        for main_cat in category_map:
            category_map[main_cat].sort()
        
        # Get unique subcategories per main category + category
        subcategories_query = select(
            Transaction.main_category,
            Transaction.category,
            Transaction.subcategory
        ).where(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.main_category.isnot(None),
                Transaction.main_category != '',
                Transaction.category.isnot(None),
                Transaction.category != '',
                Transaction.subcategory.isnot(None),
                Transaction.subcategory != ''
            )
        ).distinct()
        
        subcategories_result = await db.execute(subcategories_query)
        
        subcategory_map = {}
        for row in subcategories_result:
            key = f"{row.main_category}|{row.category}"
            subcategory = row.subcategory
            
            if key not in subcategory_map:
                subcategory_map[key] = []
            if subcategory not in subcategory_map[key]:
                subcategory_map[key].append(subcategory)
        
        # Sort subcategories
        for key in subcategory_map:
            subcategory_map[key].sort()
        
        result = {
            "owners": unique_owners,
            "account_types": unique_account_types,
            "ownerAccountMap": owner_account_map,
            "mainCategories": unique_main_categories,
            "categoryMap": category_map,
            "subcategoryMap": subcategory_map
        }
        
        print(f"✅ Filter metadata: {len(unique_owners)} owners, {len(unique_account_types)} account types")
        
        return result
        
    except Exception as e:
        print(f"❌ Failed to get filter metadata: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))