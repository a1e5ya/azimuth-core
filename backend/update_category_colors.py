#!/usr/bin/env python3
"""
Script to update colors for existing categories
Run this to apply new color scheme to existing categories
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.database import async_engine, AsyncSessionLocal, Category
from sqlalchemy import select, update


COLOR_MAP = {
    'income': '#00C9A0',
    'benefits-support': '#4DB8B8',
    'employment-income': '#2EAD8E',
    'other-income': '#5CB8C4',
    'investment-income': '#1E9B7E',
    
    'expenses': '#9B7EDE',
    'food': '#9B7EDE',
    'family': '#7B68B8',
    'housing-utilities': '#6A5B9B',
    'shopping': '#BA8ED9',
    'leisure-culture': '#8B6FC4',
    'health': '#7A9FD9',
    'transport': '#6B8FCC',
    'insurance': '#5C7FBF',
    'financial-management': '#D9A8A8',
    'financial-services': '#C49999',
    
    'transfers': '#F0C46C',
    'account-transfers': '#F0C46C',
    'savings-transfer': '#D4A647',
}

SUBCOLOR_MAP = {
    'benefits-support': ['#B8E3E3', '#A3DBDB', '#8AD0D0', '#C9E8E8', '#D9F0F0', '#E3F4F4'],
    'employment-income': ['#A8DCC9', '#8BCCA9', '#6EC292', '#C5E6D7', '#D2EBDD', '#E0F0E4'],
    'other-income': ['#C4E5EB', '#A9DDE4', '#8FCFDC', '#D0ECF0', '#DDEFF3', '#EAF4F6'],
    'investment-income': ['#9FD6C7', '#8BCFBD', '#6FC4A8', '#B9E3D8', '#C6E8DF', '#D3EDE6'],
    
    'food': ['#D5C9F0', '#C7B8E8', '#B9A7E0', '#E3DBF7', '#EBE5F9', '#F3EFFB'],
    'family': ['#C9C1DC', '#B8ACCE', '#A697C0', '#D7D0E6', '#E5E0F0', '#F0EDF7'],
    'housing-utilities': ['#C3BDD6', '#AFA6C9', '#9B8FBC', '#D1CDDF', '#DFDC E8', '#EDEAF3'],
    'shopping': ['#E3CFF2', '#D9BFED', '#CFAFE8', '#ECDFF7', '#F5EBF9', '#F9F3FB'],
    'leisure-culture': ['#CDC1E3', '#BEAED9', '#AF9BCF', '#DBD1ED', '#E9E0F5', '#F4EEFC'],
    'health': ['#C9DCF2', '#B5CEEC', '#A1C0E6', '#D7E6F7', '#E5F0FB', '#F2F7FD'],
    'transport': ['#C1D3EB', '#ADC4E3', '#99B5DB', '#CFE1F3', '#DDEAF7', '#EAF2FB'],
    'insurance': ['#BBC9E3', '#A7B8DB', '#93A7D3', '#C9D7ED', '#D7E3F3', '#E5EFF9'],
    'financial-management': ['#F0DCDC', '#E8CCCC', '#E0BCBC', '#F7E6E6', '#FAEAEA', '#FCF3F3'],
    'financial-services': ['#E8D6D6', '#DFC5C5', '#D6B4B4', '#F0E2E2', '#F5EAEA', '#FAF2F2'],
    
    'account-transfers': ['#F7E6D0', '#F4D7B5', '#F9F0E4', '#F9E1C9', '#F7D19E', '#EED1A2'],
    'savings-transfer': ['#F0E4C1', '#E8D5A3', '#F7EACE', '#E3C886', '#EBCF90', '#F5EAD4'],
}


async def update_category_colors():
    """Update colors for all existing categories"""
    
    print("🎨 Starting category color update...")
    
    async with AsyncSessionLocal() as db:
        query = select(Category)
        result = await db.execute(query)
        categories = result.scalars().all()
        
        total_categories = len(categories)
        print(f"📊 Found {total_categories} categories to update")
        
        updated = 0
        
        for category in categories:
            try:
                if category.code in COLOR_MAP:
                    new_color = COLOR_MAP[category.code]
                    
                    if category.color != new_color:
                        category.color = new_color
                        updated += 1
                        print(f"✅ Updated {category.name} ({category.code}): {category.color} → {new_color}")
                
                if category.parent_id and category.code:
                    parent_query = select(Category).where(Category.id == category.parent_id)
                    parent_result = await db.execute(parent_query)
                    parent = parent_result.scalar_one_or_none()
                    
                    if parent and parent.code in SUBCOLOR_MAP:
                        subcolors = SUBCOLOR_MAP[parent.code]
                        
                        sibling_query = select(Category).where(Category.parent_id == category.parent_id)
                        sibling_result = await db.execute(sibling_query)
                        siblings = sibling_result.scalars().all()
                        
                        for idx, sibling in enumerate(siblings):
                            if sibling.id == category.id:
                                new_color = subcolors[idx % len(subcolors)]
                                if category.color != new_color:
                                    category.color = new_color
                                    updated += 1
                                    print(f"✅ Updated subcategory {category.name}: {category.color} → {new_color}")
                                break
                
            except Exception as e:
                print(f"❌ Failed to update {category.name}: {e}")
                continue
        
        await db.commit()
        
        print("\n" + "=" * 60)
        print("📈 Color Update Complete!")
        print(f"✅ Updated {updated} categories")
        print("=" * 60)


async def main():
    print("\n" + "=" * 60)
    print("  Category Color Update Script")
    print("  Apply new color scheme to existing categories")
    print("=" * 60)
    
    try:
        await update_category_colors()
    except Exception as e:
        print(f"\n❌ Update failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())