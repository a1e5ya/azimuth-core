"""
Category analytics queries - FIXED
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, extract, or_
from typing import Dict, Any, Optional, List
from datetime import date
import uuid

from ..models.database import Category, Transaction, User, get_db
from ..auth.local_auth import get_current_user
from fastapi import Depends


class CategoryQueries:
    """Database queries for category analytics"""
    
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
    
    async def get_type_summary(
        self,
        category_type: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get summary for transaction type"""
        
        # Get all categories for this type
        cat_query = select(Category).where(
            and_(
                Category.user_id == self.user.id,
                Category.category_type == category_type,
                Category.active == True
            )
        )
        cat_result = await self.db.execute(cat_query)
        type_categories = cat_result.scalars().all()
        category_ids = [c.id for c in type_categories]
        
        if not category_ids:
            return {
                'type': category_type,
                'stats': {'total_count': 0, 'total_amount': 0, 'avg_amount': 0},
                'categories': [],
                'monthly': []
            }
        
        trans_conditions = [Transaction.user_id == self.user.id]
        if start_date:
            trans_conditions.append(Transaction.posted_at >= start_date)
        if end_date:
            trans_conditions.append(Transaction.posted_at <= end_date)
        trans_conditions.append(Transaction.category_id.in_(category_ids))
        
        # Overall stats
        stats_query = select(
            func.count(Transaction.id).label('total_count'),
            func.coalesce(func.sum(func.abs(Transaction.amount)), 0).label('total_amount'),
            func.coalesce(func.avg(func.abs(Transaction.amount)), 0).label('avg_amount')
        ).where(and_(*trans_conditions))
        
        stats_result = await self.db.execute(stats_query)
        stats = stats_result.first()
        
        # Category breakdown - only parent categories (not subcategories)
        parent_cats = [c for c in type_categories if c.parent_id is not None and self._is_parent_category(c, type_categories)]
        
        category_breakdown = []
        for cat in parent_cats[:15]:
            # Get this category and its children
            child_ids = [c.id for c in type_categories if c.parent_id == cat.id]
            all_cat_ids = [cat.id] + child_ids
            
            cat_query = select(
                func.count(Transaction.id).label('count'),
                func.coalesce(func.sum(func.abs(Transaction.amount)), 0).label('amount')
            ).where(
                and_(
                    Transaction.user_id == self.user.id,
                    Transaction.category_id.in_(all_cat_ids)
                )
            )
            
            cat_result = await self.db.execute(cat_query)
            cat_data = cat_result.first()
            
            if cat_data and cat_data.count > 0:
                category_breakdown.append({
                    'id': str(cat.id),
                    'name': cat.name,
                    'icon': cat.icon,
                    'count': cat_data.count,
                    'amount': float(cat_data.amount)
                })
        
        category_breakdown.sort(key=lambda x: x['amount'], reverse=True)
        
        # Monthly breakdown - ALL months, not just recent
        monthly_query = select(
            func.strftime('%Y-%m', Transaction.posted_at).label('month'),
            func.coalesce(func.sum(func.abs(Transaction.amount)), 0).label('amount')
        ).where(and_(*trans_conditions)).group_by('month').order_by('month')
        
        monthly_result = await self.db.execute(monthly_query)
        monthly_breakdown = [
            {'month': row.month, 'amount': float(row.amount)}
            for row in monthly_result
        ]
        
        return {
            'type': category_type,
            'stats': {
                'total_count': stats.total_count or 0,
                'total_amount': float(stats.total_amount),
                'avg_amount': float(stats.avg_amount)
            },
            'categories': category_breakdown,
            'monthly': monthly_breakdown
        }
    
    def _is_parent_category(self, cat: Category, all_cats: List[Category]) -> bool:
        """Check if category is a parent (has children or is level 2)"""
        # Level 1 = no parent (type level)
        # Level 2 = has parent but parent has no parent (main categories)
        # Level 3 = has parent whose parent exists (subcategories)
        
        if not cat.parent_id:
            return False  # Type level
        
        parent = next((c for c in all_cats if c.id == cat.parent_id), None)
        if parent and not parent.parent_id:
            return True  # This is a main category
        
        return False  # This is a subcategory
    
    async def get_category_summary(
        self,
        category_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get summary for specific category"""
        
        try:
            cat_uuid = uuid.UUID(category_id)
        except ValueError:
            return {}
        
        category_query = select(Category).where(
            and_(
                Category.id == cat_uuid,
                Category.user_id == self.user.id
            )
        )
        category_result = await self.db.execute(category_query)
        category = category_result.scalar_one_or_none()
        
        if not category:
            return {}
        
        # Get child categories
        children_query = select(Category).where(
            and_(
                Category.parent_id == cat_uuid,
                Category.user_id == self.user.id,
                Category.active == True
            )
        )
        children_result = await self.db.execute(children_query)
        children = children_result.scalars().all()
        child_ids = [c.id for c in children]
        all_category_ids = [cat_uuid] + child_ids
        
        conditions = [
            Transaction.user_id == self.user.id,
            Transaction.category_id.in_(all_category_ids)
        ]
        if start_date:
            conditions.append(Transaction.posted_at >= start_date)
        if end_date:
            conditions.append(Transaction.posted_at <= end_date)
        
        # Overall stats
        stats_query = select(
            func.count(Transaction.id).label('total_count'),
            func.coalesce(func.sum(func.abs(Transaction.amount)), 0).label('total_amount'),
            func.coalesce(func.avg(func.abs(Transaction.amount)), 0).label('avg_amount')
        ).where(and_(*conditions))
        
        stats_result = await self.db.execute(stats_query)
        stats = stats_result.first()
        
        # Subcategories breakdown
        subcategories = []
        for child in children:
            sub_query = select(
                func.count(Transaction.id).label('count'),
                func.coalesce(func.sum(func.abs(Transaction.amount)), 0).label('amount')
            ).where(
                and_(
                    Transaction.user_id == self.user.id,
                    Transaction.category_id == child.id
                )
            )
            
            sub_result = await self.db.execute(sub_query)
            sub_data = sub_result.first()
            
            if sub_data and sub_data.count > 0:
                subcategories.append({
                    'id': str(child.id),
                    'name': child.name,
                    'icon': child.icon,
                    'count': sub_data.count,
                    'amount': float(sub_data.amount)
                })
        
        subcategories.sort(key=lambda x: x['amount'], reverse=True)
        
        # Top merchants
        merchants_query = select(
            Transaction.merchant,
            func.count(Transaction.id).label('count'),
            func.coalesce(func.sum(func.abs(Transaction.amount)), 0).label('amount')
        ).where(
            and_(*conditions, Transaction.merchant.isnot(None))
        ).group_by(Transaction.merchant).order_by(desc('amount')).limit(5)
        
        merchants_result = await self.db.execute(merchants_query)
        top_merchants = [
            {
                'name': row.merchant,
                'count': row.count,
                'amount': float(row.amount)
            }
            for row in merchants_result
        ]
        
        # Monthly breakdown
        monthly_query = select(
            func.strftime('%Y-%m', Transaction.posted_at).label('month'),
            func.coalesce(func.sum(func.abs(Transaction.amount)), 0).label('amount')
        ).where(and_(*conditions)).group_by('month').order_by('month')
        
        monthly_result = await self.db.execute(monthly_query)
        monthly_breakdown = [
            {'month': row.month, 'amount': float(row.amount)}
            for row in monthly_result
        ]
        
        return {
            'category': {
                'id': str(category.id),
                'name': category.name,
                'icon': category.icon or 'circle',
                'type': category.category_type
            },
            'stats': {
                'total_count': stats.total_count or 0,
                'total_amount': float(stats.total_amount),
                'avg_amount': float(stats.avg_amount)
            },
            'subcategories': subcategories,
            'top_merchants': top_merchants,
            'monthly': monthly_breakdown
        }
    
    async def get_subcategory_transactions(
        self,
        subcategory_id: str,
        page: int = 1,
        limit: int = 50,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get transactions for subcategory with pagination"""
        
        try:
            subcat_uuid = uuid.UUID(subcategory_id)
        except ValueError:
            return {'transactions': [], 'total': 0}
        
        conditions = [
            Transaction.category_id == subcat_uuid,
            Transaction.user_id == self.user.id
        ]
        
        if start_date:
            conditions.append(Transaction.posted_at >= start_date)
        if end_date:
            conditions.append(Transaction.posted_at <= end_date)
        
        count_query = select(func.count(Transaction.id)).where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        transactions_query = select(Transaction).where(
            and_(*conditions)
        ).order_by(desc(Transaction.posted_at)).offset((page - 1) * limit).limit(limit)
        
        transactions_result = await self.db.execute(transactions_query)
        transactions = transactions_result.scalars().all()
        
        return {
            'transactions': [
                {
                    'id': str(t.id),
                    'posted_at': t.posted_at.isoformat(),
                    'amount': str(t.amount),
                    'merchant': t.merchant,
                    'memo': t.memo,
                    'transaction_type': t.transaction_type
                }
                for t in transactions
            ],
            'total': total,
            'page': page,
            'limit': limit
        }


def get_category_queries(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> CategoryQueries:
    """Get category queries instance"""
    return CategoryQueries(db, current_user)