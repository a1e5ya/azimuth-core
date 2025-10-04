"""
Category initialization service for Azimuth Core
Creates default categories for new users
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, List
import uuid

from ..models.database import Category

DEFAULT_CATEGORIES = {
    'income': {
        'id': 'income',
        'name': 'INCOME',
        'icon': 'apps-add',
        'categories': [
            {
                'id': 'benefits-support',
                'name': 'Benefits & Support',
                'icon': 'comment-check',
                'subcategories': [
                    {'id': 'unemployment-benefits', 'name': 'Unemployment Benefits', 'icon': 'comment-check'},
                    {'id': 'social-benefits', 'name': 'Social Benefits', 'icon': 'comment-heart'}
                ]
            },
            {
                'id': 'employment-income',
                'name': 'Employment Income',
                'icon': 'briefcase',
                'subcategories': [
                    {'id': 'salary', 'name': 'Salary', 'icon': 'briefcase'}
                ]
            },
            {
                'id': 'other-income',
                'name': 'Other Income',
                'icon': 'gift',
                'subcategories': [
                    {'id': 'gifts-received', 'name': 'Gifts Received', 'icon': 'gift'}
                ]
            },
            {
                'id': 'investment-income',
                'name': 'Investment Income',
                'icon': 'credit-card',
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
        'categories': [
            {
                'id': 'food',
                'name': 'Food',
                'icon': 'coffee',
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
                'subcategories': [
                    {'id': 'bureaucracy', 'name': 'Bureaucracy', 'icon': 'diploma'},
                    {'id': 'investment-accounts', 'name': 'Investment Accounts', 'icon': 'earnings'}
                ]
            },
            {
                'id': 'financial-services',
                'name': 'Financial Services',
                'icon': 'bank',
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
        'categories': [
            {
                'id': 'account-transfers',
                'name': 'Account Transfers',
                'icon': 'copy-alt',
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
                'subcategories': [
                    {'id': 'savings-transfer-main', 'name': 'Savings Transfer', 'icon': 'calculator'},
                    {'id': 'house-savings', 'name': 'House Savings', 'icon': 'home-location-alt'}
                ]
            }
        ]
    }
}


async def initialize_user_categories(user_id: str, db: AsyncSession) -> int:
    """
    Create default category tree for a new user
    Returns number of categories created
    """
    created_count = 0
    
    for type_key, type_data in DEFAULT_CATEGORIES.items():
        type_category = Category(
            id=str(uuid.uuid4()),
            user_id=user_id,
            parent_id=None,
            name=type_data['name'],
            code=type_data['id'],
            icon=type_data['icon'],
            category_type=type_key,
            active=True
        )
        db.add(type_category)
        created_count += 1
        
        for cat_data in type_data['categories']:
            category = Category(
                id=str(uuid.uuid4()),
                user_id=user_id,
                parent_id=type_category.id,
                name=cat_data['name'],
                code=cat_data['id'],
                icon=cat_data['icon'],
                category_type=type_key,
                active=True
            )
            db.add(category)
            created_count += 1
            
            for subcat_data in cat_data['subcategories']:
                subcategory = Category(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    parent_id=category.id,
                    name=subcat_data['name'],
                    code=subcat_data['id'],
                    icon=subcat_data['icon'],
                    category_type=type_key,
                    active=True
                )
                db.add(subcategory)
                created_count += 1
    
    await db.commit()
    print(f"✅ Created {created_count} default categories for user {user_id}")
    return created_count


async def get_or_create_uncategorized(user_id: str, db: AsyncSession) -> Category:
    """
    Get or create 'Uncategorized' category for user
    """
    query = select(Category).where(
        Category.user_id == user_id,
        Category.code == 'uncategorized'
    )
    result = await db.execute(query)
    uncategorized = result.scalar_one_or_none()
    
    if not uncategorized:
        uncategorized = Category(
            id=str(uuid.uuid4()),
            user_id=user_id,
            parent_id=None,
            name='Uncategorized',
            code='uncategorized',
            icon='circle-question',
            category_type='expense',
            active=True
        )
        db.add(uncategorized)
        await db.commit()
        await db.refresh(uncategorized)
        print(f"✅ Created 'Uncategorized' category for user {user_id}")
    
    return uncategorized