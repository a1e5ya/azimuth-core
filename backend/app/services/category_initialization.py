"""
Category initialization service for Azimuth Core
Creates default categories for new users
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
        'color': '#F17D99',
        'categories': [
            {
                'id': 'food',
                'name': 'Food',
                'icon': 'coffee',
                'color': '#F17D99',
                'subcolors': ['#F9D1DD', '#F7C3D2', '#F5B5C7', '#FBDFE8', '#F9EAF0', '#F6DCE2'],
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
                'color': '#9C4257',
                'subcolors': ['#D8C5C9', '#BF9FA6', '#E0D7D9', '#A87080', '#C9AEB3', '#E5D8DA'],
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
                'color': '#7A4F6A',
                'subcolors': ['#D6CBD2', '#C0A8B4', '#E3DDE1', '#9E7A8E', '#B398A7', '#C7B8C0'],
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
                'color': '#E85D9A',
                'subcolors': ['#F5C5DD', '#F2B7D5', '#F8D3E6', '#EFABCD', '#FADBED', '#EC9EC5'],
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
                'color': '#D96BB8',
                'subcolors': ['#F0C8E3', '#EBBADB', '#F5D6EC', '#E5ACD3', '#F8E2F1', '#FCEAF8'],
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
                'color': '#C45151',
                'subcolors': ['#EBD1D1', '#E0BCBC', '#F4E0E0', '#F0D8D8', '#D89999', '#E3B6B6'],
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
                'color': '#F57D65',
                'subcolors': ['#FBD8D1', '#F9C3B9', '#F7AEAA', '#FCF0EC', '#FFF4F2', '#FCD6CE'],
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
                'color': '#D15842',
                'subcolors': ['#F0D0C9', '#E7B9B0', '#F7E3DE', '#F2C7BB', '#E3A398', '#ECC9C1'],
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
                'color': '#D16345',
                'subcolors': ['#F0D2CB', '#E8C2B8', '#F5E0DB', '#F7E6E1', '#E0A79B', '#ECC9C1'],
                'subcategories': [
                    {'id': 'bureaucracy', 'name': 'Bureaucracy', 'icon': 'diploma'},
                    {'id': 'investment-accounts', 'name': 'Investment Accounts', 'icon': 'earnings'}
                ]
            },
            {
                'id': 'financial-services',
                'name': 'Financial Services',
                'icon': 'bank',
                'color': '#B85C42',
                'subcolors': ['#E8D3CC', '#DBC1B7', '#F0E7E3', '#CFA08D', '#E6C9BF', '#F2E8E4'],
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
    }
}


async def initialize_user_categories(user_id: str, db: AsyncSession) -> int:
    """
    Create default category tree for a new user with colors
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
            color=type_data['color'],
            category_type=type_key,
            active=True
        )
        db.add(type_category)
        created_count += 1
        
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
            
            for idx, subcat_data in enumerate(cat_data['subcategories']):
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
            color='#999999',
            category_type='expense',
            active=True
        )
        db.add(uncategorized)
        await db.commit()
        await db.refresh(uncategorized)
        print(f"✅ Created 'Uncategorized' category for user {user_id}")
    
    return uncategorized