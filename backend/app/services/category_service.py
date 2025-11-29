"""
Category Service - Comprehensive Category Management

Handles all category operations including:
- Default category tree initialization (4-level hierarchy)
- Category CRUD operations (create, read, update, delete)
- Category tree building with transaction counts
- CSV category auto-creation and mapping
- Category usage validation before deletion
- Type-based summaries (income, expenses, transfers)

Database: SQLAlchemy async with Category, Transaction models
Hierarchy: Type (L1) → Category (L2) → Subcategory (L3) → Sub-subcategory (L4)

Default Categories:
- Income: Employment, Benefits, Investment, Other
- Expenses: Food, Family, Housing, Shopping, Health, Transport, etc.
- Transfers: Account transfers, Savings transfers
- Targets: Savings targets, Expense limits, Income goals
"""

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
        'name': 'Income',
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
        'name': 'Expenses',
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
        'name': 'Transfers',
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
        'name': 'Targets',
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


# ============================================================================
# CATEGORY SERVICE CLASS
# ============================================================================

class CategoryService:
    """
    Consolidated service for all category operations
    
    Provides methods for:
    - Initializing default category structure
    - CRUD operations on categories
    - Building hierarchical category trees
    - Auto-creating categories from CSV imports
    - Validating category usage before deletion
    - Generating category summaries by type
    """
    
    def __init__(self, db: AsyncSession, user: User):
        """
        Initialize category service
        
        @param db: Database session for async operations
        @param user: Current user (for filtering categories)
        """
        self.db = db
        self.user = user
    
    async def initialize_default_categories(self) -> int:
        """
        Create default category tree for user
        
        Creates 4-level hierarchy:
        - Level 1: Type (income, expenses, transfers, targets)
        - Level 2: Category (Food, Transport, etc.)
        - Level 3: Subcategory (Groceries, Fuel, etc.)
        - Level 4: Sub-subcategory (future use)
        
        Process:
        1. Iterate through DEFAULT_CATEGORIES structure
        2. Create type categories (L1) with no parent
        3. Create categories (L2) under each type
        4. Create subcategories (L3) under each category
        5. Assign colors from subcolors array with rotation
        
        @returns {int} Number of categories created
        """
        created_count = 0
        
        # Iterate through each type (income, expenses, transfers, targets)
        for type_key, type_data in DEFAULT_CATEGORIES.items():
            # Create type category (L1)
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
            
            # Create categories (L2) under type
            for cat_data in type_data['categories']:
                # Shuffle subcolors for variety
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
                
                # Create subcategories (L3) under category
                for idx, subcat_data in enumerate(cat_data.get('subcategories', [])):
                    # Rotate through subcolors
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
    
    async def get_or_create_uncategorized(self, category_type: str = 'expenses') -> Category:
        """
        Get or create Uncategorized category (3-level hierarchy)
        
        Structure:
        - Level 1: Type (EXPENSES, INCOME, etc.)
        - Level 2: Uncategorized category
        - Level 3: Uncategorized subcategory (returned)
        
        This ensures compatibility with the 3-level categorization system
        used throughout the app.
        
        Process:
        1. Find or create type category (L1)
        2. Find or create "Uncategorized" category (L2) under type
        3. Find or create "Uncategorized" subcategory (L3) under category
        4. Return the subcategory (L3) for transaction assignment
        
        @param category_type: Type of category (income, expenses, transfers, targets)
        @returns {Category} Uncategorized subcategory (Level 3)
        """
        # STEP 1: Get or create type category (L1)
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
            # Create type if it doesn't exist
            type_data = DEFAULT_CATEGORIES.get(category_type, {})
            type_category = Category(
                id=str(uuid.uuid4()),
                user_id=self.user.id,
                parent_id=None,
                name=type_data.get('name', category_type.upper()),
                code=category_type,
                icon=type_data.get('icon', 'apps-sort'),
                color=type_data.get('color', '#94a3b8'),
                category_type=category_type,
                active=True
            )
            self.db.add(type_category)
            await self.db.flush()
        
        # STEP 2: Find or create "Uncategorized" category (L2)
        query = select(Category).where(
            and_(
                Category.user_id == self.user.id,
                Category.parent_id == type_category.id,
                Category.code == 'uncategorized'
            )
        )
        result = await self.db.execute(query)
        uncategorized_category = result.scalar_one_or_none()
        
        if not uncategorized_category:
            uncategorized_category = Category(
                id=str(uuid.uuid4()),
                user_id=self.user.id,
                parent_id=type_category.id,  # Child of type (L2)
                name='Uncategorized',
                code='uncategorized',
                icon='circle',
                color='#999999',
                category_type=category_type,
                active=True
            )
            self.db.add(uncategorized_category)
            await self.db.flush()
        
        # STEP 3: Find or create "Uncategorized" subcategory (L3)
        subcat_query = select(Category).where(
            and_(
                Category.user_id == self.user.id,
                Category.parent_id == uncategorized_category.id,
                Category.name == 'Uncategorized'
            )
        )
        subcat_result = await self.db.execute(subcat_query)
        uncategorized_subcat = subcat_result.scalar_one_or_none()
        
        if not uncategorized_subcat:
            uncategorized_subcat = Category(
                id=str(uuid.uuid4()),
                user_id=self.user.id,
                parent_id=uncategorized_category.id,  # Child of category (L3)
                name='Uncategorized',
                code='uncategorized-sub',
                icon='circle',
                color='#999999',
                category_type=category_type,
                active=True
            )
            self.db.add(uncategorized_subcat)
            await self.db.commit()
            await self.db.refresh(uncategorized_subcat)
        
        return uncategorized_subcat  # Return L3 subcategory for transaction assignment
    
    async def get_category_tree(self) -> List[Dict[str, Any]]:
        """
        Get hierarchical category tree with transaction counts
        
        Builds complete tree structure:
        - Root categories (types) at top level
        - Children nested recursively
        - Transaction count for each category
        - Total amount for each category (absolute values)
        
        Query optimization:
        - Single query with LEFT JOIN on transactions
        - Grouped by category attributes
        - Ordered by name
        
        @returns {List[Dict]} Tree structure with nested children
        """
        # Query categories with transaction counts
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
        
        # Build flat map first
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
        
        # Build tree by linking children to parents
        tree = []
        for cat in category_map.values():
            if cat['parent_id'] is None:
                # Root category (type)
                tree.append(cat)
            else:
                # Child category - link to parent
                parent = category_map.get(cat['parent_id'])
                if parent:
                    parent['children'].append(cat)
        
        return tree
    
    async def get_category_by_id(self, category_id: str) -> Optional[Category]:
        """
        Get single category by ID
        
        Validates UUID format before querying.
        Ensures category belongs to current user.
        
        @param category_id: Category UUID as string
        @returns {Category|None} Category object or None if not found
        """
        # Validate UUID format
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
        """
        Create new category or subcategory
        
        Process:
        1. Validate parent category exists (if parent_id provided)
        2. Inherit category_type from parent
        3. Generate UUID for new category
        4. Create and save category
        5. Return refreshed category object
        
        @param name: Category name
        @param parent_id: Parent category UUID (None for root categories)
        @param icon: Icon identifier
        @param color: Hex color code (optional)
        @returns {Category} Newly created category
        @raises HTTPException: If parent not found (404)
        """
        category_type = 'expense'  # Default type
        parent = None
        
        # Validate parent if provided
        if parent_id:
            parent = await self.get_category_by_id(parent_id)
            if not parent:
                raise HTTPException(status_code=404, detail="Parent category not found")
            category_type = parent.category_type
        
        # Create new category
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
        
        print(f"✅ Created category: {name}")
        return new_category
    
    async def update_category(
        self, category_id: str, name: Optional[str] = None,
        icon: Optional[str] = None, color: Optional[str] = None
    ) -> Category:
        """
        Update category properties
        
        Allows partial updates - only provided fields are updated.
        
        @param category_id: Category UUID
        @param name: New name (optional)
        @param icon: New icon (optional)
        @param color: New color (optional)
        @returns {Category} Updated category
        @raises HTTPException: If category not found (404)
        """
        category = await self.get_category_by_id(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        # Apply updates
        if name is not None:
            category.name = name
        if icon is not None:
            category.icon = icon
        if color is not None:
            category.color = color
        
        await self.db.commit()
        await self.db.refresh(category)
        
        print(f"✅ Updated category: {category.name}")
        return category
    
    async def delete_category(self, category_id: str, move_to_category_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Delete category and move transactions to specified category
        
        Safety checks:
        1. Check if category has children (cannot delete if it has subcategories)
        2. Check transaction count
        3. Move transactions to target category or "Uncategorized"
        4. Update transaction CSV fields (main_category, category, subcategory)
        5. Delete category
        
        Transaction moving process:
        - Determine target category hierarchy (L1, L2, or L3)
        - Set main_category, category, subcategory strings appropriately
        - Update all transactions with new category_id and CSV fields
        
        @param category_id: Category UUID to delete
        @param move_to_category_id: Target category UUID or "uncategorized"
        @returns {Dict} Success status with statistics
        @raises HTTPException: If category not found (404) or has children (400)
        """
        # Get category to delete
        category = await self.get_category_by_id(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        # Check if category can be deleted (no children)
        usage_check = await self.check_category_usage(category_id)
        if not usage_check["can_delete"]:
            raise HTTPException(status_code=400, detail=usage_check["warning_message"])
        
        transactions_moved = 0
        moved_to = None
        
        # Move transactions if any exist
        if usage_check["transaction_count"] > 0:
            # Determine target category
            if move_to_category_id == "uncategorized" or not move_to_category_id:
                target_category = await self.get_or_create_uncategorized(category.category_type)
            else:
                target_category = await self.get_category_by_id(move_to_category_id)
                if not target_category:
                    raise HTTPException(status_code=404, detail="Target category not found")
            
            # Get parent hierarchy for string columns
            target_parent = None
            target_grandparent = None
            
            if target_category.parent_id:
                target_parent = await self.get_category_by_id(target_category.parent_id)
                if target_parent and target_parent.parent_id:
                    target_grandparent = await self.get_category_by_id(target_parent.parent_id)
            
            # Determine string values based on hierarchy level
            main_cat_str = None
            cat_str = None
            subcat_str = None
            
            if target_grandparent and not target_grandparent.parent_id:
                # Target is level 3 (subcategory): grandparent > parent > target
                main_cat_str = target_grandparent.name
                cat_str = target_parent.name
                subcat_str = target_category.name
            elif target_parent and not target_parent.parent_id:
                # Target is level 2 (category): parent > target
                main_cat_str = target_parent.name
                cat_str = target_category.name
                subcat_str = None
            elif not target_category.parent_id:
                # Target is level 1 (type): target only
                main_cat_str = target_category.name
                cat_str = None
                subcat_str = None
            
            # Update all transactions with new category and CSV fields
            from sqlalchemy import update
            update_query = update(Transaction).where(
                Transaction.category_id == category_id
            ).values(
                category_id=target_category.id,
                main_category=main_cat_str,
                category=cat_str,
                subcategory=subcat_str
            )
            await self.db.execute(update_query)
            transactions_moved = usage_check["transaction_count"]
            moved_to = target_category.id
        
        # Delete category
        delete_query = delete(Category).where(Category.id == category_id)
        await self.db.execute(delete_query)
        await self.db.commit()
        
        print(f"✅ Deleted category: {category.name} ({transactions_moved} transactions moved)")
        
        return {
            "success": True,
            "transactions_moved": transactions_moved,
            "moved_to": moved_to,
            "message": f"Category deleted. {transactions_moved} transactions moved." if transactions_moved > 0 else "Category deleted."
        }
    
    async def check_category_usage(self, category_id: str) -> Dict[str, Any]:
        """
        Check if category can be safely deleted
        
        Validates:
        1. Category has no children (subcategories)
        2. Transaction count (warning if > 0)
        
        Returns:
        - transaction_count: Number of transactions using this category
        - has_children: Boolean indicating if category has subcategories
        - can_delete: Boolean indicating if deletion is allowed
        - warning_message: User-friendly message about deletion impact
        
        @param category_id: Category UUID
        @returns {Dict} Usage statistics and deletion eligibility
        @raises HTTPException: If category_id is invalid UUID (400)
        """
        # Validate UUID format
        try:
            uuid.UUID(category_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid category ID")
        
        # Count transactions using this category
        trans_count_query = select(func.count(Transaction.id)).where(
            Transaction.category_id == category_id
        )
        trans_result = await self.db.execute(trans_count_query)
        transaction_count = trans_result.scalar()
        
        # Count child categories
        children_query = select(func.count(Category.id)).where(
            Category.parent_id == category_id
        )
        children_result = await self.db.execute(children_query)
        children_count = children_result.scalar()
        
        # Determine if deletion is allowed (no children)
        can_delete = children_count == 0
        
        # Generate warning message
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
        """
        Ensure categories exist from CSV data, creating if necessary
        
        Process:
        1. Map CSV main_category to category_type (INCOME → income, etc.)
        2. Find or create type category (L1)
        3. Find or create category (L2) under type
        4. Find or create subcategory (L3) under category
        5. Auto-generate colors for new categories
        
        Color generation:
        - Check DEFAULT_CATEGORIES for predefined colors
        - If not found, generate hash-based color from name
        - Subcategories get lighter shade of parent color
        
        @param main_category: CSV main category (INCOME, EXPENSES, etc.)
        @param category: CSV category (Food, Transport, etc.)
        @param subcategory: CSV subcategory (Groceries, Fuel, etc.)
        @returns {Category|None} Deepest category found/created, or None if invalid
        """
        if not main_category:
            return None
        
        # Map CSV main category to category type
        type_map = {
            'INCOME': 'income',
            'EXPENSES': 'expenses', 
            'TRANSFERS': 'transfers',
            'TARGETS': 'targets'
        }
        
        category_type = type_map.get(main_category.upper(), 'expenses')
        
        # STEP 1: Find or create type category (L1)
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
            # Create type if it doesn't exist
            type_data = DEFAULT_CATEGORIES.get(category_type)
            if type_data:
                color = type_data.get('color', '#94a3b8')
                icon = type_data.get('icon', 'apps-sort')
                name = type_data.get('name', category_type.upper())
            else:
                color = '#94a3b8'
                icon = 'apps-sort'
                name = category_type.upper()
            
            type_category = Category(
                id=str(uuid.uuid4()),
                user_id=self.user.id,
                parent_id=None,
                name=name,
                code=category_type,
                icon=icon,
                color=color,
                category_type=category_type,
                active=True
            )
            self.db.add(type_category)
            await self.db.flush()
        
        # If no category specified, return type
        if not category:
            return type_category
        
        # STEP 2: Find or create category (L2)
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
            # Try to find in DEFAULT_CATEGORIES
            default_cat = None
            if category_type in DEFAULT_CATEGORIES:
                for cat_data in DEFAULT_CATEGORIES[category_type].get('categories', []):
                    if cat_data['name'].lower() == category.lower():
                        default_cat = cat_data
                        break
            
            # Use default colors/icons or generate new ones
            if default_cat:
                color = default_cat.get('color', '#94a3b8')
                icon = default_cat.get('icon', 'circle')
            else:
                # Generate color from name hash
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
        
        # If no subcategory specified, return category
        if not subcategory:
            return mid_category
        
        # STEP 3: Find or create subcategory (L3)
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
            # Try to find in DEFAULT_CATEGORIES
            default_subcat = None
            if category_type in DEFAULT_CATEGORIES:
                for cat_data in DEFAULT_CATEGORIES[category_type].get('categories', []):
                    if cat_data['name'].lower() == category.lower():
                        for subcat_data in cat_data.get('subcategories', []):
                            if subcat_data['name'].lower() == subcategory.lower():
                                default_subcat = subcat_data
                                break
                        break
            
            # Use default colors/icons or generate lighter shade
            if default_subcat:
                icon = default_subcat.get('icon', 'circle')
                parent_color = mid_category.color or '#94a3b8'
                if parent_color.startswith('#'):
                    # Lighten parent color for subcategory
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
                # Generate color from name hash (mid-tone)
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
        """
        Get summary statistics for a category type
        
        Calculates:
        - Total transaction count
        - Total amount (sum of absolute values)
        - Average amount per transaction
        - Breakdown by category (top-level categories under type)
        
        Optional date filtering:
        - start_date: Include only transactions after this date
        - end_date: Include only transactions before this date
        
        @param category_type: Type to summarize (income, expenses, transfers, targets)
        @param start_date: Optional start date filter
        @param end_date: Optional end date filter
        @returns {Dict} Summary statistics with category breakdown
        """
        # Get all categories of this type
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
        
        # Build transaction filter conditions
        trans_conditions = [Transaction.user_id == self.user.id]
        if start_date:
            trans_conditions.append(Transaction.posted_at >= start_date)
        if end_date:
            trans_conditions.append(Transaction.posted_at <= end_date)
        trans_conditions.append(Transaction.category_id.in_(category_ids))
        
        # Get overall statistics
        stats_query = select(
            func.count(Transaction.id).label('total_count'),
            func.coalesce(func.sum(func.abs(Transaction.amount)), 0).label('total_amount'),
            func.coalesce(func.avg(func.abs(Transaction.amount)), 0).label('avg_amount')
        ).where(and_(*trans_conditions))
        
        stats_result = await self.db.execute(stats_query)
        stats = stats_result.first()
        
        # Get main categories (L2) - categories with parent but parent has no parent
        parent_cats = [c for c in type_categories if c.parent_id is not None and self._is_main_category(c, type_categories)]
        
        # Get breakdown by main category
        category_breakdown = []
        for cat in parent_cats:
            # Get all child IDs
            child_ids = [str(c.id) for c in type_categories if c.parent_id == cat.id]
            all_cat_ids = [str(cat.id)] + child_ids
            
            # Query transactions for this category tree
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
            
            # Only include categories with transactions
            if cat_data and cat_data.count > 0:
                category_breakdown.append({
                    'id': str(cat.id),
                    'name': cat.name,
                    'icon': cat.icon,
                    'count': cat_data.count,
                    'amount': float(cat_data.amount)
                })
        
        # Sort by amount descending
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
        """
        Check if category is a main category (level 2)
        
        Main category = has parent, but parent has no parent (parent is type)
        
        @param cat: Category to check
        @param all_cats: All categories (for finding parent)
        @returns {bool} True if main category (L2)
        """
        if not cat.parent_id:
            return False
        
        parent = next((c for c in all_cats if c.id == cat.parent_id), None)
        if parent and not parent.parent_id:
            return True
        
        return False


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_category_service(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> CategoryService:
    """
    Dependency injection for CategoryService
    
    Used in FastAPI route handlers to inject service with:
    - Database session
    - Current authenticated user
    
    Example:
    ```python
    @router.get("/categories")
    async def get_categories(
        service: CategoryService = Depends(get_category_service)
    ):
        return await service.get_category_tree()
    ```
    
    @param current_user: Injected from JWT token
    @param db: Injected database session
    @returns {CategoryService} Initialized service instance
    """
    return CategoryService(db, current_user)