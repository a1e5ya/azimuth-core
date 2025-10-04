"""
Categories router - API endpoints for category management
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from ..models.database import get_db, User
from ..services.category_service import CategoryService, get_category_service
from ..services.category_initialization import initialize_user_categories
from ..routers.category_queries import CategoryQueries, get_category_queries
from ..auth.local_auth import get_current_user
from datetime import date

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


class CSVMatchRequest(BaseModel):
    csv_main: str
    csv_category: str
    csv_subcategory: Optional[str] = None


class CSVMatchResponse(BaseModel):
    match_type: str
    category_id: Optional[str]
    confidence: float
    suggestions: List[Dict[str, Any]]


@router.get("/tree")
async def get_category_tree(
    category_service: CategoryService = Depends(get_category_service)
):
    """Get full category tree with transaction counts"""
    
    tree = await category_service.get_category_tree()
    return {
        "success": True,
        "tree": tree
    }


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
    category_service: CategoryService = Depends(get_category_service)
):
    """Delete category and move transactions to Uncategorized"""
    
    result = await category_service.delete_category(category_id)
    return result


@router.post("/initialize")
async def initialize_categories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Initialize default categories for user"""
    
    created_count = await initialize_user_categories(current_user.id, db)
    
    return {
        "success": True,
        "message": f"Created {created_count} default categories",
        "categories_created": created_count
    }


@router.post("/match-csv", response_model=CSVMatchResponse)
async def match_csv_category(
    match_request: CSVMatchRequest,
    category_service: CategoryService = Depends(get_category_service)
):
    """Match CSV category to user categories"""
    
    result = await category_service.match_csv_category(
        csv_main=match_request.csv_main,
        csv_category=match_request.csv_category,
        csv_subcategory=match_request.csv_subcategory
    )
    
    return CSVMatchResponse(
        match_type=result["match_type"],
        category_id=result["category_id"],
        confidence=result["confidence"],
        suggestions=result["suggestions"]
    )


@router.get("/type/{category_type}/summary")
async def get_type_summary(
    category_type: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category_queries: CategoryQueries = Depends(get_category_queries)
):
    """Get summary for transaction type (income/expense/transfer)"""
    
    summary = await category_queries.get_type_summary(
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
    category_queries: CategoryQueries = Depends(get_category_queries)
):
    """Get summary for specific category"""
    
    summary = await category_queries.get_category_summary(
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
    category_queries: CategoryQueries = Depends(get_category_queries)
):
    """Get transaction list for subcategory"""
    
    result = await category_queries.get_subcategory_transactions(
        subcategory_id=subcategory_id,
        page=page,
        limit=limit,
        start_date=start_date,
        end_date=end_date
    )
    
    return result