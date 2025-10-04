#!/usr/bin/env python3
"""
One-time migration script to initialize categories for existing users
Run this after deploying the category system
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.database import async_engine, AsyncSessionLocal, User
from app.services.category_initialization import initialize_user_categories
from sqlalchemy import select


async def migrate_all_users():
    """Initialize categories for all existing users"""
    
    print("🔄 Starting category migration for existing users...")
    
    async with AsyncSessionLocal() as db:
        query = select(User)
        result = await db.execute(query)
        users = result.scalars().all()
        
        total_users = len(users)
        print(f"📊 Found {total_users} users to migrate")
        
        migrated = 0
        failed = 0
        
        for index, user in enumerate(users, 1):
            try:
                print(f"\n[{index}/{total_users}] Processing user: {user.email}")
                
                created_count = await initialize_user_categories(user.id, db)
                
                print(f"✅ Created {created_count} categories for {user.email}")
                migrated += 1
                
            except Exception as e:
                print(f"❌ Failed for {user.email}: {e}")
                failed += 1
                continue
    
    print("\n" + "=" * 60)
    print("📈 Migration Complete!")
    print(f"✅ Successfully migrated: {migrated} users")
    if failed > 0:
        print(f"❌ Failed: {failed} users")
    print("=" * 60)


async def main():
    print("\n" + "=" * 60)
    print("  Category Migration Script")
    print("  Initialize default categories for existing users")
    print("=" * 60)
    
    try:
        await migrate_all_users()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())