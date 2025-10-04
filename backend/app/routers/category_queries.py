"""
Category analytics queries
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, extract
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
        """Get summary for transaction type (income/expense/transfer)"""
        
        trans_conditions = [Transaction.user_id == self.user.id]
        
        if start_date:
            trans_conditions.append(Transaction.posted_at >= start_date)
        if end_date:
            trans_conditions.append(Transaction.posted_at <= end_date)
        
        stats_query = select(
            func.count(Transaction.id).label('total_count'),
            func.coalesce(func.sum(func.abs(Transaction.amount)), 0).label('total_amount'),
            func.coalesce(func.avg(func.abs(Transaction.amount)), 0).label('avg_amount')
        ).select_from(Transaction).outerjoin(
            Category, Transaction.category_id == Category.id
        ).where(
            and_(
                *trans_conditions,
                Category.category_type == category_type
            )
        )
        
        stats_result = await self.db.execute(stats_query)
        stats = stats_result.first()
        
        category_breakdown_query = select(
            Category.id,
            Category.name,
            Category.icon,
            func.count(Transaction.id).label('count'),
            func.coalesce(func.sum(func.abs(Transaction.amount)), 0).label('amount')
        ).select_from(Category).outerjoin(
            Transaction, Transaction.category_id == Category.id
        ).where(
            and_(
                Category.user_id == self.user.id,
                Category.category_type == category_type,
                Category.parent_id.isnot(None),
                Category.active == True
            )
        ).group_by(Category.id, Category.name, Category.icon).order_by(desc('amount'))
        
        breakdown_result = await self.db.execute(category_breakdown_query)
        breakdown = []
        
        for row in breakdown_result:
            breakdown.append({
                'id': str(row.id),
                'name': row.name,
                'icon': row.icon,
                'count': row.count,
                'amount': float(row.amount)
            })
        
        monthly_query = select(
            func.strftime('%Y-%m', Transaction.posted_at).label('month'),
            func.coalesce(func.sum(func.abs(Transaction.amount)), 0).label('amount')
        ).select_from(Transaction).outerjoin(
            Category, Transaction.category_id == Category.id
        ).where(
            and_(
                *trans_conditions,
                Category.category_type == category_type
            )
        ).group_by('month').order_by('month')
        
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
            'categories': breakdown[:10],
            'monthly': monthly_breakdown
        }
    
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
        
        conditions = [Transaction.category_id == cat_uuid]
        if start_date:
            conditions.append(Transaction.posted_at >= start_date)
        if end_date:
            conditions.append(Transaction.posted_at <= end_date)
        
        stats_query = select(
            func.count(Transaction.id).label('total_count'),
            func.coalesce(func.sum(func.abs(Transaction.amount)), 0).label('total_amount'),
            func.coalesce(func.avg(func.abs(Transaction.amount)), 0).label('avg_amount')
        ).where(and_(*conditions))
        
        stats_result = await self.db.execute(stats_query)
        stats = stats_result.first()
        
        subcategories_query = select(
            Category.id,
            Category.name,
            Category.icon,
            func.count(Transaction.id).label('count'),
            func.coalesce(func.sum(func.abs(Transaction.amount)), 0).label('amount')
        ).select_from(Category).outerjoin(
            Transaction, Transaction.category_id == Category.id
        ).where(
            Category.parent_id == cat_uuid
        ).group_by(Category.id, Category.name, Category.icon).order_by(desc('amount'))
        
        subcategories_result = await self.db.execute(subcategories_query)
        subcategories = [
            {
                'id': row.id,
                'name': row.name,
                'icon': row.icon,
                'count': row.count,
                'amount': float(row.amount)
            }
            for row in subcategories_result
        ]
        
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
                    'id': t.id,
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