"""
Category initialization service for Azimuth Core
Creates default categories for new users - INCLUDING TARGETS
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, List
import uuid
import random

from ..models.database import Category

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
                'subcolors': ['#B8E3E3', '#A3DBDB', '#8AD0D0', '#C9E8E8', '#D9F0F0', '#E3F4F4'],
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
                'subcolors': ['#A8DCC9', '#8BCCA9', '#6EC292', '#C5E6D7', '#D2EBDD', '#E0F0E4'],
                'subcategories': [
                    {'id': 'salary', 'name': 'Salary', 'icon': 'briefcase'}
                ]
            },
            {
                'id': 'other-income',
                'name': 'Other Income',
                'icon': 'gift',
                'color': '#5CB8C4',
                'subcolors': ['#C4E5EB', '#A9DDE4', '#8FCFDC', '#D0ECF0', '#DDEFF3', '#EAF4F6'],
                'subcategories': [
                    {'id': 'gifts-received', 'name': 'Gifts Received', 'icon': 'gift'}
                ]
            },
            {
                'id': 'investment-income',
                'name': 'Investment Income',
                'icon': 'credit-card',
                'color': '#1E9B7E',
                'subcolors': ['#9FD6C7', '#8BCFBD', '#6FC4A8', '#B9E3D8', '#C6E8DF', '#D3EDE6'],
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
                'subcolors': ['#D5C9F0', '#C7B8E8', '#B9A7E0', '#E3DBF7', '#EBE5F9', '#F3EFFB'],
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
                'subcolors': ['#C9C1DC', '#B8ACCE', '#A697C0', '#D7D0E6', '#E5E0F0', '#F0EDF7'],
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
                'subcolors': ['#C3BDD6', '#AFA6C9', '#9B8FBC', '#D1CDDF', '#DFDCe8', '#EDEAF3'],
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
                'subcolors': ['#E3CFF2', '#D9BFED', '#CFAFE8', '#ECDFF7', '#F5EBF9', '#F9F3FB'],
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
                'color': '#8B6FC4',
                'subcolors': ['#CDC1E3', '#BEAED9', '#AF9BCF', '#DBD1ED', '#E9E0F5', '#F4EEFC'],
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
                'subcolors': ['#C9DCF2', '#B5CEEC', '#A1C0E6', '#D7E6F7', '#E5F0FB', '#F2F7FD'],
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
                'subcolors': ['#C1D3EB', '#ADC4E3', '#99B5DB', '#CFE1F3', '#DDEAF7', '#EAF2FB'],
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
                'color': '#5C7FBF',
                'subcolors': ['#BBC9E3', '#A7B8DB', '#93A7D3', '#C9D7ED', '#D7E3F3', '#E5EFF9'],
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
                'color': '#D9A8A8',
                'subcolors': ['#F0DCDC', '#E8CCCC', '#E0BCBC', '#F7E6E6', '#FAEAEA', '#FCF3F3'],
                'subcategories': [
                    {'id': 'bureaucracy', 'name': 'Bureaucracy', 'icon': 'diploma'},
                    {'id': 'investment-accounts', 'name': 'Investment Accounts', 'icon': 'earnings'}
                ]
            },
            {
                'id': 'financial-services',
                'name': 'Financial Services',
                'icon': 'bank',
                'color': '#C49999',
                'subcolors': ['#E8D6D6', '#DFC5C5', '#D6B4B4', '#F0E2E2', '#F5EAEA', '#FAF2F2'],
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
        'color': '#F0C46C',
        'categories': [
            {
                'id': 'account-transfers',
                'name': 'Account Transfers',
                'icon': 'copy-alt',
                'color': '#F0C46C',
                'subcolors': ['#F7E6D0', '#F4D7B5', '#F9F0E4', '#F9E1C9', '#F7D19E', '#EED1A2'],
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
                'subcolors': ['#F0E4C1', '#E8D5A3', '#F7EACE', '#E3C886', '#EBCF90', '#F5EAD4'],
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
                'subcolors': ['#D88FA3', '#C97586', '#BA5B6A', '#EAB5C0', '#F2D5DC', '#F8E8EC'],
                'subcategories': []
            },
            {
                'id': 'expense-limits',
                'name': 'Expense Limits',
                'icon': 'euro',
                'color': '#FF6B6B',
                'subcolors': ['#FFB5B5', '#FF9F9F', '#FF8989', '#FFD6D6', '#FFE5E5', '#FFF0F0'],
                'subcategories': []
            },
            {
                'id': 'income-goals',
                'name': 'Income Goals',
                'icon': 'chart-histogram',
                'color': '#a33333',
                'subcolors': ['#D19999', '#C18080', '#B16666', '#E5CCCC', '#EEDEDE', '#F5EBEB'],
                'subcategories': []
            }
        ]
    }
}


async def initialize_user_categories(user_id: str, db: AsyncSession) -> int:
    """
    Create default category tree for a new user with colors
    NOW INCLUDES TARGETS AS 4TH MAIN CATEGORY
    Returns number of categories created
    """
    created_count = 0
    
    for type_key, type_data in DEFAULT_CATEGORIES.items():
        # Create main type category
        type_category = Category(
            id=str(uuid.uuid4()),
            user_id=user_id,
            parent_id=None,
            name=type_data['name'],
            code=type_data['id'],
            icon=type_data['icon'],
            color=type_data['color'],
            category_type=type_key,
            active=True
        )
        db.add(type_category)
        created_count += 1
        
        # Create child categories
        for cat_data in type_data['categories']:
            subcolors = cat_data.get('subcolors', [])
            random.shuffle(subcolors)
            
            category = Category(
                id=str(uuid.uuid4()),
                user_id=user_id,
                parent_id=type_category.id,
                name=cat_data['name'],
                code=cat_data['id'],
                icon=cat_data['icon'],
                color=cat_data['color'],
                category_type=type_key,
                active=True
            )
            db.add(category)
            created_count += 1
            
            # Create subcategories if they exist
            for idx, subcat_data in enumerate(cat_data.get('subcategories', [])):
                subcolor = subcolors[idx % len(subcolors)] if subcolors else cat_data['color']
                
                subcategory = Category(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    parent_id=category.id,
                    name=subcat_data['name'],
                    code=subcat_data['id'],
                    icon=subcat_data['icon'],
                    color=subcolor,
                    category_type=type_key,
                    active=True
                )
                db.add(subcategory)
                created_count += 1
    
    await db.commit()
    print(f"✅ Created {created_count} default categories for user {user_id} (including TARGETS)")
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
            color='#999999',
            category_type='expense',
            active=True
        )
        db.add(uncategorized)
        await db.commit()
        await db.refresh(uncategorized)
        print(f"✅ Created 'Uncategorized' category for user {user_id}")
    
    return uncategorized