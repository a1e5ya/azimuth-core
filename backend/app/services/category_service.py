from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, delete, desc
from typing import List, Dict, Any, Optional, Tuple
from datetime import date
import uuid
import random
import hashlib
from difflib import SequenceMatcher
from collections import defaultdict
from fastapi import Depends, HTTPException

from ..models.database import Category, Transaction, User, get_db
from ..auth.local_auth import get_current_user


# ============================================================================
# DEFAULT CATEGORY STRUCTURE
# ============================================================================

DEFAULT_CATEGORIES = {
    'income': {
        'id': 'income',
        'name': 'INCOME',
        'icon': 'apps-add',
        'color': '#00C9A0',
        'categories': [
            {
                'id': 'benefits-support',
                'name': 'Benefits & Support',
                'icon': 'comment-check',
                'color': '#4DB8B8',
                'subcolors': ['#3DA8A8', '#34A0A0', '#2B9898', '#42B0B0', '#4FB8B8', '#5CC0C0'],
                'subcategories': [
                    {'id': 'unemployment-benefits', 'name': 'Unemployment Benefits', 'icon': 'comment-check'},
                    {'id': 'social-benefits', 'name': 'Social Benefits', 'icon': 'comment-heart'}
                ]
            },
            {
                'id': 'employment-income',
                'name': 'Employment Income',
                'icon': 'briefcase',
                'color': '#2EAD8E',
                'subcolors': ['#25A584', '#1F9D7A', '#199570', '#2FAE8F', '#3CB69A', '#49BEA5'],
                'subcategories': [
                    {'id': 'salary', 'name': 'Salary', 'icon': 'briefcase'}
                ]
            },
            {
                'id': 'other-income',
                'name': 'Other Income',
                'icon': 'gift',
                'color': '#5CB8C4',
                'subcolors': ['#4AACB8', '#3FA4B0', '#349CA8', '#51B0BC', '#5EB8C4', '#6BC0CC'],
                'subcategories': [
                    {'id': 'gifts-received', 'name': 'Gifts Received', 'icon': 'gift'}
                ]
            },
            {
                'id': 'investment-income',
                'name': 'Investment Income',
                'icon': 'credit-card',
                'color': '#1E9B7E',
                'subcolors': ['#189373', '#148B68', '#10835D', '#1C977A', '#28A386', '#34AF92'],
                'subcategories': [
                    {'id': 'cashback', 'name': 'Cashback', 'icon': 'credit-card'},
                    {'id': 'dividends-interest', 'name': 'Dividends & Interest', 'icon': 'chat-arrow-grow'}
                ]
            }
        ]
    },
    'expenses': {
        'id': 'expenses',
        'name': 'EXPENSES',
        'icon': 'apps-delete',
        'color': '#9B7EDE',
        'categories': [
            {
                'id': 'food',
                'name': 'Food',
                'icon': 'coffee',
                'color': '#9B7EDE',
                'subcolors': ['#8B6ED4', '#825FCC', '#7950C4', '#9477D8', '#9D80DC', '#A689E0'],
                'subcategories': [
                    {'id': 'cafes-coffee', 'name': 'Cafes & Coffee', 'icon': 'coffee'},
                    {'id': 'groceries', 'name': 'Groceries', 'icon': 'salad'},
                    {'id': 'restaurants', 'name': 'Restaurants', 'icon': 'room-service'},
                    {'id': 'sweets', 'name': 'Sweets', 'icon': 'ice-cream'}
                ]
            },
            {
                'id': 'family',
                'name': 'Family',
                'icon': 'kite',
                'color': '#7B68B8',
                'subcolors': ['#6B58A8', '#6250A0', '#594898', '#7460B0', '#7D68B8', '#8670C0'],
                'subcategories': [
                    {'id': 'sports-activities', 'name': 'Sports Activities', 'icon': 'ice-skate'},
                    {'id': 'child-activities', 'name': "Child's Activities", 'icon': 'ferris-wheel'},
                    {'id': 'toys-games', 'name': 'Toys & Games', 'icon': 'kite'}
                ]
            },
            {
                'id': 'housing-utilities',
                'name': 'Housing & Utilities',
                'icon': 'key',
                'color': '#6A5B9B',
                'subcolors': ['#5A4B8B', '#524383', '#4A3B7B', '#625393', '#6A5B9B', '#7263A3'],
                'subcategories': [
                    {'id': 'monthly-rent', 'name': 'Monthly Rent', 'icon': 'key'},
                    {'id': 'internet-phone', 'name': 'Internet & Phone', 'icon': 'signal-alt-2'},
                    {'id': 'energy-water', 'name': 'Energy & Water', 'icon': 'bulb'}
                ]
            },
            {
                'id': 'shopping',
                'name': 'Shopping',
                'icon': 'shopping-cart',
                'color': '#BA8ED9',
                'subcolors': ['#AA7EC9', '#A270C1', '#9A62B9', '#B284D1', '#BA8CD9', '#C294E1'],
                'subcategories': [
                    {'id': 'household', 'name': 'Household', 'icon': 'soap'},
                    {'id': 'electronics', 'name': 'Electronics', 'icon': 'gamepad'},
                    {'id': 'clothing-shoes', 'name': 'Clothing & Shoes', 'icon': 'label'},
                    {'id': 'accessories', 'name': 'Accessories', 'icon': 'lipstick'},
                    {'id': 'subscriptions', 'name': 'Subscriptions', 'icon': 'interactive'},
                    {'id': 'guilty-pleasure', 'name': 'Guilty Pleasure', 'icon': 'glass-cheers'}
                ]
            },
            {
                'id': 'leisure-culture',
                'name': 'Leisure & Culture',
                'icon': 'ticket',
                'color': '#8B7AC7',
                'subcolors': ['#7B6AB7', '#735FAF', '#6B54A7', '#8372BF', '#8B7AC7', '#9382CF'],
                'subcategories': [
                    {'id': 'music', 'name': 'Music', 'icon': 'guitar'},
                    {'id': 'social-activities', 'name': 'Social Activities', 'icon': 'ticket'},
                    {'id': 'education', 'name': 'Education', 'icon': 'graduation-cap'},
                    {'id': 'books-media', 'name': 'Books & Media', 'icon': 'book-alt'},
                    {'id': 'hobbies-crafts', 'name': 'Hobbies & Crafts', 'icon': 'palette'}
                ]
            },
            {
                'id': 'health',
                'name': 'Health',
                'icon': 'stethoscope',
                'color': '#7A9FD9',
                'subcolors': ['#6A8FC9', '#6087C1', '#567FB9', '#7497D1', '#7E9FD9', '#88A7E1'],
                'subcategories': [
                    {'id': 'pharmacy', 'name': 'Pharmacy', 'icon': 'band-aid'},
                    {'id': 'medical-services', 'name': 'Medical Services', 'icon': 'stethoscope'},
                    {'id': 'dental-care', 'name': 'Dental Care', 'icon': 'tooth'},
                    {'id': 'gym-fitness', 'name': 'Gym & Fitness', 'icon': 'gym'}
                ]
            },
            {
                'id': 'transport',
                'name': 'Transport',
                'icon': 'car',
                'color': '#6B8FCC',
                'subcolors': ['#5B7FBC', '#5377B4', '#4B6FAC', '#6587C4', '#6F8FCC', '#7997D4'],
                'subcategories': [
                    {'id': 'vehicle-registration', 'name': 'Vehicle Registration & Tax', 'icon': 'car'},
                    {'id': 'maintenance-repairs', 'name': 'Maintenance & Repairs', 'icon': 'dashboard'},
                    {'id': 'fuel', 'name': 'Fuel', 'icon': 'gas-pump'},
                    {'id': 'parking-fees', 'name': 'Parking Fees', 'icon': 'road'},
                    {'id': 'public-transport', 'name': 'Public Transport', 'icon': 'train-side'}
                ]
            },
            {
                'id': 'insurance',
                'name': 'Insurance',
                'icon': 'document-signed',
                'color': '#5A7EB8',
                'subcolors': ['#4A6EA8', '#4266A0', '#3A5E98', '#5476B0', '#5E7EB8', '#6886C0'],
                'subcategories': [
                    {'id': 'health-insurance', 'name': 'Health Insurance', 'icon': 'syringe'},
                    {'id': 'home-insurance', 'name': 'Home Insurance', 'icon': 'document-signed'},
                    {'id': 'vehicle-insurance', 'name': 'Vehicle Insurance', 'icon': 'document-signed'}
                ]
            },
            {
                'id': 'financial-management',
                'name': 'Financial Management',
                'icon': 'diploma',
                'color': '#4A6DA3',
                'subcolors': ['#3A5D93', '#32558B', '#2A4D83', '#42659B', '#4A6DA3', '#5275AB'],
                'subcategories': [
                    {'id': 'bureaucracy', 'name': 'Bureaucracy', 'icon': 'diploma'},
                    {'id': 'investment-accounts', 'name': 'Investment Accounts', 'icon': 'earnings'}
                ]
            },
            {
                'id': 'financial-services',
                'name': 'Financial Services',
                'icon': 'bank',
                'color': '#3A5C8F',
                'subcolors': ['#2A4C7F', '#224477', '#1A3C6F', '#325487', '#3A5C8F', '#426497'],
                'subcategories': [
                    {'id': 'withdrawal', 'name': 'Withdrawal', 'icon': 'euro'},
                    {'id': 'payment-provider', 'name': 'Payment Provider', 'icon': 'shopping-cart'},
                    {'id': 'bank-services', 'name': 'Bank Services', 'icon': 'bank'}
                ]
            }
        ]
    },
    'transfers': {
        'id': 'transfers',
        'name': 'TRANSFERS',
        'icon': 'apps-sort',
        'color': "#BD8317",
        'categories': [
            {
                'id': 'account-transfers',
                'name': 'Account Transfers',
                'icon': 'copy-alt',
                'color': '#F0C46C',
                'subcolors': ['#D4A840', '#CCA038', '#C49830', '#DCB048', '#E4B850', '#ECC058'],
                'subcategories': [
                    {'id': 'account-transfers-own', 'name': 'Between Own Accounts', 'icon': 'copy-alt'},
                    {'id': 'account-transfers-family', 'name': 'Family Support', 'icon': 'hand-holding-heart'},
                    {'id': 'account-transfers-reserve', 'name': 'Reserve Transfer', 'icon': 'chart-histogram'}
                ]
            },
            {
                'id': 'savings-transfer',
                'name': 'Savings Transfer',
                'icon': 'calculator',
                'color': '#D4A647',
                'subcolors': ['#BC9030', '#B48828', '#AC8020', '#C49838', '#CCA040', '#D4A848'],
                'subcategories': [
                    {'id': 'savings-transfer-main', 'name': 'Savings Transfer', 'icon': 'calculator'},
                    {'id': 'house-savings', 'name': 'House Savings', 'icon': 'home-location-alt'}
                ]
            }
        ]
    },
    'targets': {
        'id': 'targets',
        'name': 'TARGETS',
        'icon': 'target',
        'color': '#b54a4a',
        'categories': [
            {
                'id': 'savings-targets',
                'name': 'Savings Targets',
                'icon': 'earnings',
                'color': '#AE2C4C',
                'subcolors': ['#9E1C3C', '#961434', '#8E0C2C', '#A62444', '#AE2C4C', '#B63454'],
                'subcategories': []
            },
            {
                'id': 'expense-limits',
                'name': 'Expense Limits',
                'icon': 'euro',
                'color': '#FF6B6B',
                'subcolors': ['#EF5B5B', '#E75353', '#DF4B4B', '#F76363', '#FF6B6B', '#FF7373'],
                'subcategories': []
            },
            {
                'id': 'income-goals',
                'name': 'Income Goals',
                'icon': 'target',
                'color': '#a33333',
                'subcolors': ['#932323', '#8B1B1B', '#831313', '#9B2B2B', '#A33333', '#AB3B3B'],
                'subcategories': []
            }
        ]
    }
}


class CategoryService:
    """Consolidated service for all category operations"""
    
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
    
    async def initialize_default_categories(self) -> int:
        """Create default category tree for user"""
        created_count = 0
        
        for type_key, type_data in DEFAULT_CATEGORIES.items():
            type_category = Category(
                id=str(uuid.uuid4()),
                user_id=self.user.id,
                parent_id=None,
                name=type_data['name'],
                code=type_data['id'],
                icon=type_data['icon'],
                color=type_data['color'],
                category_type=type_key,
                active=True
            )
            self.db.add(type_category)
            created_count += 1
            
            for cat_data in type_data['categories']:
                subcolors = cat_data.get('subcolors', [])
                random.shuffle(subcolors)
                
                category = Category(
                    id=str(uuid.uuid4()),
                    user_id=self.user.id,
                    parent_id=type_category.id,
                    name=cat_data['name'],
                    code=cat_data['id'],
                    icon=cat_data['icon'],
                    color=cat_data['color'],
                    category_type=type_key,
                    active=True
                )
                self.db.add(category)
                created_count += 1
                
                for idx, subcat_data in enumerate(cat_data.get('subcategories', [])):
                    subcolor = subcolors[idx % len(subcolors)] if subcolors else cat_data['color']
                    
                    subcategory = Category(
                        id=str(uuid.uuid4()),
                        user_id=self.user.id,
                        parent_id=category.id,
                        name=subcat_data['name'],
                        code=subcat_data['id'],
                        icon=subcat_data['icon'],
                        color=subcolor,
                        category_type=type_key,
                        active=True
                    )
                    self.db.add(subcategory)
                    created_count += 1
        
        await self.db.commit()
        print(f"✅ Created {created_count} default categories")
        return created_count
    
    async def get_or_create_uncategorized(self) -> Category:
        """Get or create Uncategorized category"""
        query = select(Category).where(
            and_(
                Category.user_id == self.user.id,
                Category.code == 'uncategorized'
            )
        )
        result = await self.db.execute(query)
        uncategorized = result.scalar_one_or_none()
        
        if not uncategorized:
            uncategorized = Category(
                id=str(uuid.uuid4()),
                user_id=self.user.id,
                parent_id=None,
                name='Uncategorized',
                code='uncategorized',
                icon='circle-question',
                color='#999999',
                category_type='expense',
                active=True
            )
            self.db.add(uncategorized)
            await self.db.commit()
            await self.db.refresh(uncategorized)
        
        return uncategorized
    
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
            and_(
                Category.user_id == self.user.id,
                Category.active == True
            )
        ).group_by(
            Category.id, Category.parent_id, Category.name, Category.code,
            Category.icon, Category.color, Category.category_type
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
        """Get single category - FIXED: compare as string"""
        try:
            uuid.UUID(category_id)
        except ValueError:
            return None
        
        query = select(Category).where(
            and_(
                Category.id == category_id,
                Category.user_id == self.user.id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create_category(
        self, name: str, parent_id: Optional[str],
        icon: str, color: Optional[str] = None
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
        self, category_id: str, name: Optional[str] = None,
        icon: Optional[str] = None, color: Optional[str] = None
    ) -> Category:
        """Update category - FIXED"""
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
    
    async def delete_category(self, category_id: str) -> Dict[str, Any]:
        """Delete category - FIXED: string comparisons"""
        category = await self.get_category_by_id(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        usage_check = await self.check_category_usage(category_id)
        if not usage_check["can_delete"]:
            raise HTTPException(status_code=400, detail=usage_check["warning_message"])
        
        uncategorized = await self.get_or_create_uncategorized()
        
        from sqlalchemy import update
        update_query = update(Transaction).where(
            Transaction.category_id == category_id
        ).values(category_id=uncategorized.id)
        await self.db.execute(update_query)
        
        delete_query = delete(Category).where(Category.id == category_id)
        await self.db.execute(delete_query)
        await self.db.commit()
        
        return {
            "success": True,
            "transactions_moved": usage_check["transaction_count"],
            "moved_to": uncategorized.id,
            "message": f"Category deleted. {usage_check['transaction_count']} transactions moved."
        }
    
    async def check_category_usage(self, category_id: str) -> Dict[str, Any]:
        """Check if category can be deleted - FIXED"""
        try:
            uuid.UUID(category_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid category ID")
        
        trans_count_query = select(func.count(Transaction.id)).where(
            Transaction.category_id == category_id
        )
        trans_result = await self.db.execute(trans_count_query)
        transaction_count = trans_result.scalar()
        
        children_query = select(func.count(Category.id)).where(
            Category.parent_id == category_id
        )
        children_result = await self.db.execute(children_query)
        children_count = children_result.scalar()
        
        can_delete = children_count == 0
        
        if children_count > 0:
            warning = f"Cannot delete category with {children_count} subcategories."
        elif transaction_count > 0:
            warning = f"This category has {transaction_count} transactions. They will be moved."
        else:
            warning = "This category can be safely deleted."
        
        return {
            "transaction_count": transaction_count,
            "has_children": children_count > 0,
            "can_delete": can_delete,
            "warning_message": warning
        }
    
    async def ensure_categories_from_csv(
        self, main_category: str, category: str = None, subcategory: str = None
    ) -> Optional[Category]:
        """Ensure categories exist from CSV data"""
        if not main_category:
            return None
        
        type_map = {
            'INCOME': 'income',
            'EXPENSES': 'expenses', 
            'TRANSFERS': 'transfers',
            'TARGETS': 'targets'
        }
        
        category_type = type_map.get(main_category.upper(), 'expenses')
        
        type_query = select(Category).where(
            and_(
                Category.user_id == self.user.id,
                Category.category_type == category_type,
                Category.parent_id.is_(None)
            )
        )
        type_result = await self.db.execute(type_query)
        type_category = type_result.scalar_one_or_none()
        
        if not type_category:
            type_data = DEFAULT_CATEGORIES.get(category_type)
            if type_data:
                color = type_data.get('color', '#94a3b8')
                icon = type_data.get('icon', 'apps-sort')
            else:
                color = '#94a3b8'
                icon = 'apps-sort'
            
            type_category = Category(
                id=str(uuid.uuid4()),
                user_id=self.user.id,
                parent_id=None,
                name=main_category.upper(),
                code=category_type,
                icon=icon,
                color=color,
                category_type=category_type,
                active=True
            )
            self.db.add(type_category)
            await self.db.flush()
        
        if not category:
            return type_category
        
        mid_query = select(Category).where(
            and_(
                Category.user_id == self.user.id,
                Category.parent_id == type_category.id,
                Category.name == category
            )
        )
        mid_result = await self.db.execute(mid_query)
        mid_category = mid_result.scalar_one_or_none()
        
        if not mid_category:
            default_cat = None
            if category_type in DEFAULT_CATEGORIES:
                for cat_data in DEFAULT_CATEGORIES[category_type].get('categories', []):
                    if cat_data['name'].lower() == category.lower():
                        default_cat = cat_data
                        break
            
            if default_cat:
                color = default_cat.get('color', '#94a3b8')
                icon = default_cat.get('icon', 'circle')
            else:
                color_hash = int(hashlib.md5(category.encode()).hexdigest()[:6], 16)
                color = f"#{format(color_hash % 0xFFFFFF, '06x')}"
                icon = 'circle'
            
            mid_category = Category(
                id=str(uuid.uuid4()),
                user_id=self.user.id,
                parent_id=type_category.id,
                name=category,
                icon=icon,
                color=color,
                category_type=category_type,
                active=True
            )
            self.db.add(mid_category)
            await self.db.flush()
        
        if not subcategory:
            return mid_category
        
        sub_query = select(Category).where(
            and_(
                Category.user_id == self.user.id,
                Category.parent_id == mid_category.id,
                Category.name == subcategory
            )
        )
        sub_result = await self.db.execute(sub_query)
        sub_category = sub_result.scalar_one_or_none()
        
        if not sub_category:
            default_subcat = None
            if category_type in DEFAULT_CATEGORIES:
                for cat_data in DEFAULT_CATEGORIES[category_type].get('categories', []):
                    if cat_data['name'].lower() == category.lower():
                        for subcat_data in cat_data.get('subcategories', []):
                            if subcat_data['name'].lower() == subcategory.lower():
                                default_subcat = subcat_data
                                break
                        break
            
            if default_subcat:
                icon = default_subcat.get('icon', 'circle')
                parent_color = mid_category.color or '#94a3b8'
                if parent_color.startswith('#'):
                    r = int(parent_color[1:3], 16)
                    g = int(parent_color[3:5], 16)
                    b = int(parent_color[5:7], 16)
                    r = min(255, r + (255 - r) // 2)
                    g = min(255, g + (255 - g) // 2)
                    b = min(255, b + (255 - b) // 2)
                    color = f"#{r:02x}{g:02x}{b:02x}"
                else:
                    color = parent_color
            else:
                color_hash = int(hashlib.md5(subcategory.encode()).hexdigest()[:6], 16)
                color = f"#{format((color_hash % 0xFFFFFF) | 0x808080, '06x')}"
                icon = 'circle'
            
            sub_category = Category(
                id=str(uuid.uuid4()),
                user_id=self.user.id,
                parent_id=mid_category.id,
                name=subcategory,
                icon=icon,
                color=color,
                category_type=category_type,
                active=True
            )
            self.db.add(sub_category)
            await self.db.flush()
        
        return sub_category
    
    async def get_type_summary(
        self, category_type: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get summary for transaction type"""
        cat_query = select(Category).where(
            and_(
                Category.user_id == self.user.id,
                Category.category_type == category_type,
                Category.active == True
            )
        )
        cat_result = await self.db.execute(cat_query)
        type_categories = cat_result.scalars().all()
        category_ids = [str(c.id) for c in type_categories]
        
        if not category_ids:
            return {
                'type': category_type,
                'stats': {'total_count': 0, 'total_amount': 0, 'avg_amount': 0},
                'categories': []
            }
        
        trans_conditions = [Transaction.user_id == self.user.id]
        if start_date:
            trans_conditions.append(Transaction.posted_at >= start_date)
        if end_date:
            trans_conditions.append(Transaction.posted_at <= end_date)
        trans_conditions.append(Transaction.category_id.in_(category_ids))
        
        stats_query = select(
            func.count(Transaction.id).label('total_count'),
            func.coalesce(func.sum(func.abs(Transaction.amount)), 0).label('total_amount'),
            func.coalesce(func.avg(func.abs(Transaction.amount)), 0).label('avg_amount')
        ).where(and_(*trans_conditions))
        
        stats_result = await self.db.execute(stats_query)
        stats = stats_result.first()
        
        parent_cats = [c for c in type_categories if c.parent_id is not None and self._is_main_category(c, type_categories)]
        
        category_breakdown = []
        for cat in parent_cats:
            child_ids = [str(c.id) for c in type_categories if c.parent_id == cat.id]
            all_cat_ids = [str(cat.id)] + child_ids
            
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
        
        return {
            'type': category_type,
            'stats': {
                'total_count': stats.total_count or 0,
                'total_amount': float(stats.total_amount),
                'avg_amount': float(stats.avg_amount)
            },
            'categories': category_breakdown
        }
    
    def _is_main_category(self, cat: Category, all_cats: List[Category]) -> bool:
        """Check if category is main (level 2)"""
        if not cat.parent_id:
            return False
        
        parent = next((c for c in all_cats if c.id == cat.parent_id), None)
        if parent and not parent.parent_id:
            return True
        
        return False


def get_category_service(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> CategoryService:
    """Get category service instance"""
    return CategoryService(db, current_user)