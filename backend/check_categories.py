#!/usr/bin/env python3
"""
Quick script to check transaction categorization in database
Run from backend folder: python check_categories.py
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.database import AsyncSessionLocal, Transaction, Category
from sqlalchemy import select, func, and_

async def check_transactions():
    async with AsyncSessionLocal() as db:
        # Count total transactions
        total_result = await db.execute(select(func.count(Transaction.id)))
        total = total_result.scalar()
        
        # Count categorized
        cat_result = await db.execute(
            select(func.count(Transaction.id)).where(Transaction.category_id.isnot(None))
        )
        categorized = cat_result.scalar()
        
        # Get 5 sample transactions
        sample_result = await db.execute(select(Transaction).limit(5))
        samples = sample_result.scalars().all()
        
        print(f"\n📊 DATABASE CHECK")
        print(f"=" * 60)
        print(f"Total transactions: {total}")
        print(f"Categorized: {categorized}")
        print(f"Uncategorized: {total - categorized}")
        print(f"\n📋 Sample Transactions:")
        print("=" * 60)
        
        for i, t in enumerate(samples, 1):
            print(f"\n{i}. ID: {t.id}")
            print(f"   Merchant: {t.merchant}")
            print(f"   Amount: {t.amount}")
            print(f"   CSV Category: {t.csv_category}")
            print(f"   CSV Subcategory: {t.csv_subcategory}")
            print(f"   category_id: {t.category_id}")
            print(f"   source_category: {t.source_category}")
        
        # Check categories
        cat_count_result = await db.execute(select(func.count(Category.id)))
        cat_count = cat_count_result.scalar()
        
        print(f"\n\n📁 CATEGORIES")
        print(f"=" * 60)
        print(f"Total categories: {cat_count}")
        
        # Get some subcategories
        subcat_result = await db.execute(
            select(Category).where(Category.parent_id.isnot(None)).limit(5)
        )
        subcats = subcat_result.scalars().all()
        
        print(f"\nSample subcategories:")
        for cat in subcats:
            print(f"  - {cat.name} (ID: {cat.id})")

if __name__ == "__main__":
    asyncio.run(check_transactions())