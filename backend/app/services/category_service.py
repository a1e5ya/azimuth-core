"""
Category service - Business logic for category operations
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, delete
from typing import List, Dict, Any, Optional
import uuid
from difflib import SequenceMatcher

from ..models.database import Category, Transaction, User, get_db
from ..auth.local_auth import get_current_user
from .category_initialization import get_or_create_uncategorized
from fastapi import Depends, HTTPException


class CategoryService:
    """Service for category operations"""
    
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
    
    async def get_category_tree(self) -> List[Dict[str, Any]]:
        """Get hierarchical category tree with transaction counts"""
        
        query = select(
            Category.id,
            Category.parent_id,
            Category.name,
            Category.code,
            Category.icon,
            Category.color,
            Category.category_type,
            func.count(Transaction.id).label('transaction_count'),
            func.coalesce(func.sum(func.abs(Transaction.amount)), 0).label('total_amount')
        ).outerjoin(
            Transaction, Transaction.category_id == Category.id
        ).where(
            Category.user_id == self.user.id,
            Category.active == True
        ).group_by(
            Category.id,
            Category.parent_id,
            Category.name,
            Category.code,
            Category.icon,
            Category.color,
            Category.category_type
        ).order_by(Category.name)
        
        result = await self.db.execute(query)
        all_categories = result.all()
        
        category_map = {}
        for cat in all_categories:
            category_map[cat.id] = {
                'id': cat.id,
                'parent_id': cat.parent_id,
                'name': cat.name,
                'code': cat.code,
                'icon': cat.icon,
                'color': cat.color,
                'category_type': cat.category_type,
                'transaction_count': cat.transaction_count,
                'total_amount': float(cat.total_amount),
                'children': []
            }
        
        tree = []
        for cat in category_map.values():
            if cat['parent_id'] is None:
                tree.append(cat)
            else:
                parent = category_map.get(cat['parent_id'])
                if parent:
                    parent['children'].append(cat)
        
        return tree
    
    async def get_category_by_id(self, category_id: str) -> Optional[Category]:
        """Get single category with user verification"""
        
        try:
            cat_uuid = uuid.UUID(category_id)
        except ValueError:
            return None
        
        query = select(Category).where(
            and_(
                Category.id == cat_uuid,
                Category.user_id == self.user.id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create_category(
        self,
        name: str,
        parent_id: Optional[str],
        icon: str,
        color: Optional[str] = None
    ) -> Category:
        """Create new category or subcategory"""
        
        category_type = 'expense'
        parent = None
        
        if parent_id:
            parent = await self.get_category_by_id(parent_id)
            if not parent:
                raise HTTPException(status_code=404, detail="Parent category not found")
            category_type = parent.category_type
        
        new_category = Category(
            id=str(uuid.uuid4()),
            user_id=self.user.id,
            parent_id=parent_id,
            name=name,
            icon=icon,
            color=color,
            category_type=category_type,
            active=True
        )
        
        self.db.add(new_category)
        await self.db.commit()
        await self.db.refresh(new_category)
        
        return new_category
    
    async def update_category(
        self,
        category_id: str,
        name: Optional[str] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None
    ) -> Category:
        """Update category details"""
        
        category = await self.get_category_by_id(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        if name:
            category.name = name
        if icon:
            category.icon = icon
        if color is not None:
            category.color = color
        
        await self.db.commit()
        await self.db.refresh(category)
        
        return category
    
    async def check_category_usage(self, category_id: str) -> Dict[str, Any]:
        """Check if category can be deleted"""
        
        try:
            cat_uuid = uuid.UUID(category_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid category ID")
        
        trans_count_query = select(func.count(Transaction.id)).where(
            Transaction.category_id == cat_uuid
        )
        trans_result = await self.db.execute(trans_count_query)
        transaction_count = trans_result.scalar()
        
        children_query = select(func.count(Category.id)).where(
            Category.parent_id == cat_uuid
        )
        children_result = await self.db.execute(children_query)
        children_count = children_result.scalar()
        
        can_delete = children_count == 0
        
        warning_message = ""
        if children_count > 0:
            warning_message = f"Cannot delete category with {children_count} subcategories. Delete subcategories first."
        elif transaction_count > 0:
            warning_message = f"This category has {transaction_count} transactions. They will be moved to 'Uncategorized'."
        else:
            warning_message = "This category can be safely deleted."
        
        return {
            "transaction_count": transaction_count,
            "has_children": children_count > 0,
            "can_delete": can_delete,
            "warning_message": warning_message
        }
    
    async def delete_category(self, category_id: str) -> Dict[str, Any]:
        """Delete category and move transactions to Uncategorized"""
        
        category = await self.get_category_by_id(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        usage_check = await self.check_category_usage(category_id)
        if not usage_check["can_delete"]:
            raise HTTPException(status_code=400, detail=usage_check["warning_message"])
        
        uncategorized = await get_or_create_uncategorized(self.user.id, self.db)
        
        cat_uuid = uuid.UUID(category_id)
        
        from sqlalchemy import update
        update_query = update(Transaction).where(
            Transaction.category_id == cat_uuid
        ).values(
            category_id=uuid.UUID(uncategorized.id)
        )
        await self.db.execute(update_query)
        
        delete_query = delete(Category).where(Category.id == cat_uuid)
        await self.db.execute(delete_query)
        
        await self.db.commit()
        
        return {
            "success": True,
            "transactions_moved": usage_check["transaction_count"],
            "moved_to": uncategorized.id,
            "message": f"Category deleted. {usage_check['transaction_count']} transactions moved to Uncategorized."
        }
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings (0.0 to 1.0)"""
        if not str1 or not str2:
            return 0.0
        
        s1 = str1.lower().strip()
        s2 = str2.lower().strip()
        
        if s1 == s2:
            return 1.0
        
        return SequenceMatcher(None, s1, s2).ratio()
    
    async def match_category(
        self,
        csv_main: str,
        category: str,
        subcategory: Optional[str] = None
    ) -> Dict[str, Any]:
        """Match CSV categories to user categories"""
        
        query = select(Category).where(
            and_(
                Category.user_id == self.user.id,
                Category.active == True
            )
        )
        result = await self.db.execute(query)
        user_categories = result.scalars().all()
        
        csv_full = f"{csv_main} {category}"
        if subcategory:
            csv_full = f"{csv_full} {subcategory}"
        csv_full = csv_full.lower().strip()
        
        best_match = None
        best_score = 0.0
        suggestions = []
        
        for category in user_categories:
            cat_full = category.name.lower().strip()
            score = self._calculate_similarity(csv_full, cat_full)
            
            if score > best_score:
                best_score = score
                best_match = category
            
            if score >= 0.5:
                suggestions.append({
                    "id": category.id,
                    "name": category.name,
                    "score": round(score, 2)
                })
        
        suggestions.sort(key=lambda x: x["score"], reverse=True)
        suggestions = suggestions[:5]
        
        match_type = "none"
        category_id = None
        
        if best_score >= 0.95:
            match_type = "exact"
            category_id = best_match.id
        elif best_score >= 0.8:
            match_type = "similar"
            category_id = best_match.id
        
        return {
            "match_type": match_type,
            "category_id": category_id,
            "confidence": round(best_score, 2),
            "suggestions": suggestions
        }


def get_category_service(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> CategoryService:
    """Get category service instance"""
    return CategoryService(db, current_user)