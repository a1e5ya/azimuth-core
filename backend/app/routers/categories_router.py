"""
Categories router - API endpoints for category management - FIXED IMPORTS
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, delete, desc
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date

from ..models.database import get_db, User, Transaction
from ..services.category_service import CategoryService, get_category_service
from ..auth.local_auth import get_current_user

router = APIRouter()


class CategoryCreate(BaseModel):
    name: str
    parent_id: Optional[str] = None
    icon: str
    color: Optional[str] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None


class CategoryResponse(BaseModel):
    id: str
    name: str
    parent_id: Optional[str]
    icon: str
    color: Optional[str]
    category_type: str
    transaction_count: int
    total_amount: float


class DeleteCheckResponse(BaseModel):
    can_delete: bool
    transaction_count: int
    has_children: bool
    warning_message: str


class DeleteCategoryRequest(BaseModel):
    move_to_category_id: Optional[str] = None


@router.get("/tree")
async def get_category_tree(
    category_service: CategoryService = Depends(get_category_service)
):
    """Get full category tree with transaction counts"""
    tree = await category_service.get_category_tree()
    return {"success": True, "tree": tree}


@router.get("/{category_id}")
async def get_category(
    category_id: str,
    category_service: CategoryService = Depends(get_category_service)
):
    """Get single category details"""
    category = await category_service.get_category_by_id(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return {
        "id": category.id,
        "name": category.name,
        "parent_id": category.parent_id,
        "icon": category.icon,
        "color": category.color,
        "category_type": category.category_type,
        "code": category.code,
        "active": category.active
    }


@router.post("/", response_model=CategoryResponse)
async def create_category(
    category_data: CategoryCreate,
    category_service: CategoryService = Depends(get_category_service)
):
    """Create new category or subcategory"""
    category = await category_service.create_category(
        name=category_data.name,
        parent_id=category_data.parent_id,
        icon=category_data.icon,
        color=category_data.color
    )
    
    return CategoryResponse(
        id=category.id,
        name=category.name,
        parent_id=category.parent_id,
        icon=category.icon,
        color=category.color,
        category_type=category.category_type,
        transaction_count=0,
        total_amount=0.0
    )


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: str,
    category_data: CategoryUpdate,
    category_service: CategoryService = Depends(get_category_service)
):
    """Update category details"""
    category = await category_service.update_category(
        category_id=category_id,
        name=category_data.name,
        icon=category_data.icon,
        color=category_data.color
    )
    
    return CategoryResponse(
        id=category.id,
        name=category.name,
        parent_id=category.parent_id,
        icon=category.icon,
        color=category.color,
        category_type=category.category_type,
        transaction_count=0,
        total_amount=0.0
    )


@router.get("/{category_id}/check-delete", response_model=DeleteCheckResponse)
async def check_category_deletion(
    category_id: str,
    category_service: CategoryService = Depends(get_category_service)
):
    """Check if category can be deleted"""
    result = await category_service.check_category_usage(category_id)
    
    return DeleteCheckResponse(
        can_delete=result["can_delete"],
        transaction_count=result["transaction_count"],
        has_children=result["has_children"],
        warning_message=result["warning_message"]
    )


@router.delete("/{category_id}")
async def delete_category(
    category_id: str,
    move_to_category_id: Optional[str] = None,  # Query parameter
    category_service: CategoryService = Depends(get_category_service)
):
    """Delete category and move transactions to specified category"""
    result = await category_service.delete_category(category_id, move_to_category_id)
    return result


@router.post("/initialize")
async def initialize_categories(
    current_user: User = Depends(get_current_user),
    category_service: CategoryService = Depends(get_category_service)
):
    """Initialize default categories for user"""
    created_count = await category_service.initialize_default_categories()
    
    return {
        "success": True,
        "message": f"Created {created_count} default categories",
        "categories_created": created_count
    }


@router.get("/type/{category_type}/summary")
async def get_type_summary(
    category_type: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category_service: CategoryService = Depends(get_category_service)
):
    """Get summary for transaction type (income/expense/transfer)"""
    summary = await category_service.get_type_summary(
        category_type=category_type,
        start_date=start_date,
        end_date=end_date
    )
    return summary


@router.get("/{category_id}/summary")
async def get_category_summary(
    category_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category_service: CategoryService = Depends(get_category_service)
):
    """Get summary for specific category"""
    summary = await category_service.get_category_summary(
        category_id=category_id,
        start_date=start_date,
        end_date=end_date
    )
    return summary


@router.get("/{subcategory_id}/transactions")
async def get_subcategory_transactions(
    subcategory_id: str,
    page: int = 1,
    limit: int = 50,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category_service: CategoryService = Depends(get_category_service)
):
    """Get transaction list for subcategory"""
    result = await category_service.get_subcategory_transactions(
        subcategory_id=subcategory_id,
        page=page,
        limit=limit,
        start_date=start_date,
        end_date=end_date
    )
    return result


@router.get("/debug/transactions")
async def debug_transactions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Debug: Check transaction categorization status"""
    from sqlalchemy import func
    
    total_query = select(func.count(Transaction.id)).where(
        Transaction.user_id == current_user.id
    )
    total_result = await db.execute(total_query)
    total = total_result.scalar()
    
    categorized_query = select(func.count(Transaction.id)).where(
        and_(
            Transaction.user_id == current_user.id,
            Transaction.category_id.isnot(None)
        )
    )
    categorized_result = await db.execute(categorized_query)
    categorized = categorized_result.scalar()
    
    sample_query = select(Transaction).where(
        Transaction.user_id == current_user.id
    ).limit(10)
    sample_result = await db.execute(sample_query)
    samples = sample_result.scalars().all()
    
    return {
        "total_transactions": total,
        "categorized_transactions": categorized,
        "uncategorized_transactions": total - categorized,
        "sample_transactions": [
            {
                "id": str(t.id),
                "merchant": t.merchant,
                "amount": str(t.amount),
                "category": t.category,
                "subcategory": t.subcategory,
                "category_id": str(t.category_id) if t.category_id else None,
                "source_category": t.source_category
            }
            for t in samples
        ]
    }

@router.get("/{category_id}/patterns")
async def get_category_patterns(
    category_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get merchants and keywords from training data for this category"""
    
    # Get transactions with this category from training
    query = select(
        Transaction.merchant,
        Transaction.memo,
        func.count(Transaction.id).label('count')
    ).where(
        and_(
            Transaction.user_id == current_user.id,
            Transaction.category_id == category_id,
            or_(
                Transaction.source_category == 'csv_mapped',
                Transaction.source_category == 'user'
            )
        )
    ).group_by(Transaction.merchant, Transaction.memo)
    
    result = await db.execute(query)
    
    merchants = {}
    all_text = []
    
    for row in result:
        if row.merchant:
            merchants[row.merchant] = merchants.get(row.merchant, 0) + row.count
            all_text.append(row.merchant.lower())
        if row.memo:
            all_text.append(row.memo.lower())
    
    # Extract keywords
    from collections import Counter
    words = ' '.join(all_text).split()
    word_freq = Counter([w for w in words if len(w) > 3])
    keywords = [w for w, _ in word_freq.most_common(20)]
    
    return {
        "merchants": [
            {"name": m, "count": c} 
            for m, c in sorted(merchants.items(), key=lambda x: x[1], reverse=True)[:10]
        ],
        "keywords": keywords
    }