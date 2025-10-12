#!/usr/bin/env python3
"""
Script to clean up ALL duplicate categories
Removes duplicates at all levels: types, categories, and subcategories
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.database import async_engine, AsyncSessionLocal, Category, Transaction, User
from sqlalchemy import select, delete, and_


async def cleanup_all_duplicates():
    """Remove duplicate categories at all levels for all users"""
    
    print("🧹 Starting complete duplicate category cleanup...")
    
    async with AsyncSessionLocal() as db:
        user_query = select(User)
        user_result = await db.execute(user_query)
        users = user_result.scalars().all()
        
        print(f"📊 Found {len(users)} users")
        
        for user in users:
            print(f"\n👤 Processing user: {user.email}")
            
            query = select(Category).where(Category.user_id == user.id).order_by(Category.created_at)
            result = await db.execute(query)
            all_categories = result.scalars().all()
            
            seen_codes = {}
            duplicates_to_delete = []
            
            for category in all_categories:
                if not category.code:
                    continue
                
                key = f"{category.parent_id}:{category.code}"
                
                if key in seen_codes:
                    print(f"  🗑️  Found duplicate: {category.name} (code: {category.code}, ID: {category.id})")
                    duplicates_to_delete.append({
                        'duplicate': category,
                        'keep': seen_codes[key]
                    })
                else:
                    seen_codes[key] = category
                    print(f"  ✅ Keeping: {category.name} (code: {category.code}, ID: {category.id})")
            
            for item in duplicates_to_delete:
                dup = item['duplicate']
                keep = item['keep']
                
                child_query = select(Category).where(Category.parent_id == dup.id)
                child_result = await db.execute(child_query)
                children = child_result.scalars().all()
                
                for child in children:
                    existing_child_query = select(Category).where(
                        and_(
                            Category.parent_id == keep.id,
                            Category.code == child.code
                        )
                    )
                    existing_child_result = await db.execute(existing_child_query)
                    existing_child = existing_child_result.scalar_one_or_none()
                    
                    if existing_child:
                        trans_query = select(Transaction).where(Transaction.category_id == str(child.id))
                        trans_result = await db.execute(trans_query)
                        child_transactions = trans_result.scalars().all()
                        
                        for trans in child_transactions:
                            trans.category_id = str(existing_child.id)
                        
                        if child_transactions:
                            print(f"     ↳ Moved {len(child_transactions)} transactions from duplicate child {child.name}")
                        
                        await db.delete(child)
                    else:
                        child.parent_id = keep.id
                        print(f"     ↳ Moving child: {child.name}")
                
                trans_query = select(Transaction).where(Transaction.category_id == str(dup.id))
                trans_result = await db.execute(trans_query)
                transactions = trans_result.scalars().all()
                
                for trans in transactions:
                    trans.category_id = str(keep.id)
                
                if transactions:
                    print(f"     ↳ Moved {len(transactions)} transactions")
                
                await db.delete(dup)
            
            if duplicates_to_delete:
                await db.commit()
                print(f"  ✅ Cleaned up {len(duplicates_to_delete)} duplicates")
            else:
                print(f"  ✅ No duplicates found")
        
        print("\n" + "=" * 60)
        print("✅ Complete Cleanup Finished!")
        print("=" * 60)


async def main():
    print("\n" + "=" * 60)
    print("  Complete Duplicate Category Cleanup Script")
    print("  Remove ALL duplicate categories at all levels")
    print("=" * 60)
    
    try:
        await cleanup_all_duplicates()
    except Exception as e:
        print(f"\n❌ Cleanup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())