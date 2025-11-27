"""
Categories Router - Category Management and Training

Endpoints:
- GET /tree: Get full category tree with transaction counts
- GET /{category_id}: Get single category details
- POST /: Create new category or subcategory
- PUT /{category_id}: Update category details
- GET /{category_id}/check-delete: Check if category can be deleted
- DELETE /{category_id}: Delete category and move transactions
- POST /initialize: Initialize default categories for user
- GET /type/{category_type}/summary: Get summary for type (income/expense/transfer)
- GET /{category_id}/summary: Get summary for specific category
- GET /{subcategory_id}/transactions: Get transaction list for subcategory
- GET /debug/transactions: Debug categorization status
- GET /{category_id}/patterns: Get cached merchants and keywords
- POST /train: Train all categories (extract merchants and keywords)
- PUT /{category_id}/keywords: Update category keywords

Features:
- Hierarchical category tree (Type > Category > Subcategory)
- Transaction count and amount tracking
- Safe deletion with transaction migration
- Category training (merchant/keyword extraction)
- Pattern-based auto-categorization
- Debug endpoints for troubleshooting

Database: SQLAlchemy async with Category, Transaction models
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, delete, desc, or_
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date, datetime

from ..models.database import get_db, User, Transaction, Category
from ..services.category_service import CategoryService, get_category_service
from ..auth.local_auth import get_current_user

router = APIRouter()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CategoryCreate(BaseModel):
    """Category creation request"""
    name: str
    parent_id: Optional[str] = None
    icon: str
    color: Optional[str] = None


class CategoryUpdate(BaseModel):
    """Category update request (all fields optional)"""
    name: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None


class CategoryResponse(BaseModel):
    """Category response with metadata"""
    id: str
    name: str
    parent_id: Optional[str]
    icon: str
    color: Optional[str]
    category_type: str
    transaction_count: int
    total_amount: float


class DeleteCheckResponse(BaseModel):
    """Category deletion check response"""
    can_delete: bool
    transaction_count: int
    has_children: bool
    warning_message: str


class DeleteCategoryRequest(BaseModel):
    """Category deletion request"""
    move_to_category_id: Optional[str] = None


# ============================================================================
# CATEGORY TREE ENDPOINT
# ============================================================================

@router.get("/tree")
async def get_category_tree(
    category_service: CategoryService = Depends(get_category_service)
):
    """
    Get full category tree with transaction counts
    
    Returns hierarchical structure:
    Type (INCOME, EXPENSES, TRANSFERS)
      → Category (Food, Transport, Salary)
        → Subcategory (Groceries, Fuel, Monthly Salary)
    
    Each node includes:
    - Transaction count
    - Total amount
    - Icon and color
    
    @param category_service: Injected category service
    @returns {dict} {success: true, tree: [...]}
    """
    tree = await category_service.get_category_tree()
    return {"success": True, "tree": tree}


# ============================================================================
# SINGLE CATEGORY ENDPOINTS
# ============================================================================

@router.get("/{category_id}")
async def get_category(
    category_id: str,
    category_service: CategoryService = Depends(get_category_service)
):
    """
    Get single category details by ID
    
    @param category_id: Category UUID
    @param category_service: Injected category service
    @returns {dict} Category details
    @raises HTTPException: 404 if category not found
    """
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


# ============================================================================
# CREATE/UPDATE CATEGORY ENDPOINTS
# ============================================================================

@router.post("/", response_model=CategoryResponse)
async def create_category(
    category_data: CategoryCreate,
    category_service: CategoryService = Depends(get_category_service)
):
    """
    Create new category or subcategory
    
    If parent_id is None: Creates top-level category
    If parent_id is provided: Creates subcategory under parent
    
    @param category_data: Category creation data
    @param category_service: Injected category service
    @returns {CategoryResponse} Created category
    """
    category = await category_service.create_category(
        name=category_data.name,
        parent_id=category_data.parent_id,
        icon=category_data.icon,
        color=category_data.color
    )
    
    print(f"✅ Created category: {category.name}")
    
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
    """
    Update category details
    
    All fields optional - only provided fields are updated
    
    @param category_id: Category UUID
    @param category_data: Fields to update
    @param category_service: Injected category service
    @returns {CategoryResponse} Updated category
    """
    category = await category_service.update_category(
        category_id=category_id,
        name=category_data.name,
        icon=category_data.icon,
        color=category_data.color
    )
    
    print(f"✅ Updated category: {category.name}")
    
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


# ============================================================================
# DELETE CATEGORY ENDPOINTS
# ============================================================================

@router.get("/{category_id}/check-delete", response_model=DeleteCheckResponse)
async def check_category_deletion(
    category_id: str,
    category_service: CategoryService = Depends(get_category_service)
):
    """
    Check if category can be safely deleted
    
    Checks:
    - Does category have transactions?
    - Does category have children (subcategories)?
    
    Returns warning message if issues found
    
    @param category_id: Category UUID
    @param category_service: Injected category service
    @returns {DeleteCheckResponse} Deletion safety check
    """
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
    move_to_category_id: Optional[str] = None,
    category_service: CategoryService = Depends(get_category_service)
):
    """
    Delete category and move transactions to specified category
    
    Process:
    1. Check category usage (transactions, children)
    2. Move transactions to target category (if specified)
    3. Delete category
    
    If move_to_category_id not provided, transactions become uncategorized
    
    @param category_id: Category UUID to delete
    @param move_to_category_id: Target category for transactions (optional)
    @param category_service: Injected category service
    @returns {dict} Deletion result
    """
    result = await category_service.delete_category(category_id, move_to_category_id)
    
    print(f"✅ Deleted category: {category_id}")
    
    return result


# ============================================================================
# CATEGORY INITIALIZATION ENDPOINT
# ============================================================================

@router.post("/initialize")
async def initialize_categories(
    current_user: User = Depends(get_current_user),
    category_service: CategoryService = Depends(get_category_service)
):
    """
    Initialize default categories for user
    
    Creates standard category tree:
    - INCOME (Salary, Business, Other)
    - EXPENSES (Food, Transport, Housing, etc.)
    - TRANSFERS (Between Accounts)
    
    @param current_user: Injected from JWT token
    @param category_service: Injected category service
    @returns {dict} {success, message, categories_created}
    """
    created_count = await category_service.initialize_default_categories()
    
    print(f"✅ Initialized {created_count} default categories")
    
    return {
        "success": True,
        "message": f"Created {created_count} default categories",
        "categories_created": created_count
    }


# ============================================================================
# CATEGORY SUMMARY ENDPOINTS
# ============================================================================

@router.get("/type/{category_type}/summary")
async def get_type_summary(
    category_type: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category_service: CategoryService = Depends(get_category_service)
):
    """
    Get summary for transaction type (income/expense/transfer)
    
    Aggregates:
    - Total amount
    - Transaction count
    - Category breakdown
    
    Optional date range filtering
    
    @param category_type: income|expense|transfer
    @param start_date: Optional start date filter
    @param end_date: Optional end date filter
    @param category_service: Injected category service
    @returns {dict} Type summary with breakdown
    """
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
    """
    Get summary for specific category
    
    Aggregates:
    - Total amount
    - Transaction count
    - Subcategory breakdown (if has children)
    
    Optional date range filtering
    
    @param category_id: Category UUID
    @param start_date: Optional start date filter
    @param end_date: Optional end date filter
    @param category_service: Injected category service
    @returns {dict} Category summary with breakdown
    """
    summary = await category_service.get_category_summary(
        category_id=category_id,
        start_date=start_date,
        end_date=end_date
    )
    return summary


# ============================================================================
# CATEGORY TRANSACTIONS ENDPOINT
# ============================================================================

@router.get("/{subcategory_id}/transactions")
async def get_subcategory_transactions(
    subcategory_id: str,
    page: int = 1,
    limit: int = 50,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category_service: CategoryService = Depends(get_category_service)
):
    """
    Get paginated transaction list for subcategory
    
    Returns transactions sorted by date (newest first)
    Optional date range filtering
    
    @param subcategory_id: Subcategory UUID
    @param page: Page number (default: 1)
    @param limit: Items per page (default: 50)
    @param start_date: Optional start date filter
    @param end_date: Optional end date filter
    @param category_service: Injected category service
    @returns {dict} {transactions: [...], total, page, limit}
    """
    result = await category_service.get_subcategory_transactions(
        subcategory_id=subcategory_id,
        page=page,
        limit=limit,
        start_date=start_date,
        end_date=end_date
    )
    return result


# ============================================================================
# DEBUG ENDPOINTS
# ============================================================================

@router.get("/debug/transactions")
async def debug_transactions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Debug endpoint: Check transaction categorization status
    
    Returns:
    - Total transaction count
    - Categorized transaction count
    - Uncategorized transaction count
    - Sample of 10 transactions with category info
    
    @param current_user: Injected from JWT token
    @param db: Database session
    @returns {dict} Categorization statistics and samples
    """
    # Total transactions
    total_query = select(func.count(Transaction.id)).where(
        Transaction.user_id == current_user.id
    )
    total_result = await db.execute(total_query)
    total = total_result.scalar()
    
    # Categorized transactions (have category_id)
    categorized_query = select(func.count(Transaction.id)).where(
        and_(
            Transaction.user_id == current_user.id,
            Transaction.category_id.isnot(None)
        )
    )
    categorized_result = await db.execute(categorized_query)
    categorized = categorized_result.scalar()
    
    # Sample transactions
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


# ============================================================================
# CATEGORY TRAINING ENDPOINTS
# ============================================================================

@router.get("/{category_id}/patterns")
async def get_category_patterns(
    category_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get cached merchants and keywords for category
    
    Returns learned patterns from training:
    - Merchants: List of merchant names
    - Keywords: List of extracted keywords
    - Last updated timestamp
    
    @param category_id: Category UUID
    @param db: Database session
    @param current_user: Injected from JWT token
    @returns {dict} {merchants: [...], keywords: [...], last_updated: str}
    @raises HTTPException: 404 if category not found
    """
    query = select(Category).where(
        and_(
            Category.id == category_id,
            Category.user_id == current_user.id
        )
    )
    result = await db.execute(query)
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return {
        "merchants": category.training_merchants or [],
        "keywords": category.training_keywords or [],
        "last_updated": category.last_training_update.isoformat() if category.last_training_update else None
    }


@router.post("/train")
async def train_categories(
    category_service: CategoryService = Depends(get_category_service),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Train all categories - extract merchants and keywords
    
    Process:
    1. Find all categorized transactions
    2. Group by category
    3. Extract unique merchants
    4. Extract keywords from merchant names
    5. Update category training_merchants and training_keywords
    
    Used for auto-categorization of new transactions
    
    @param category_service: Injected category service
    @param db: Database session
    @param current_user: Injected from JWT token
    @returns {dict} {success, trained_count, message}
    """
    from ..services.category_training import CategoryTrainingService
    
    trainer = CategoryTrainingService(db, current_user)
    trained_count = await trainer.train_all_categories()
    
    print(f"✅ Trained {trained_count} categories")
    
    return {
        "success": True,
        "trained_count": trained_count,
        "message": f"Trained {trained_count} categories"
    }


@router.put("/{category_id}/keywords")
async def update_category_keywords(
    category_id: str,
    keywords: List[str],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update category keywords manually
    
    Allows manual override of auto-learned keywords
    Updates last_training_update timestamp
    
    @param category_id: Category UUID
    @param keywords: List of keywords
    @param db: Database session
    @param current_user: Injected from JWT token
    @returns {dict} {success, keywords}
    @raises HTTPException: 404 if category not found
    """
    query = select(Category).where(
        and_(
            Category.id == category_id,
            Category.user_id == current_user.id
        )
    )
    result = await db.execute(query)
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Update keywords and timestamp
    category.training_keywords = keywords
    category.last_training_update = datetime.utcnow()
    
    await db.commit()
    
    print(f"✅ Updated keywords for category: {category.name}")
    
    return {"success": True, "keywords": keywords}