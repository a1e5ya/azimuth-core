"""
Transaction import service - DEBUG CATEGORY MATCHING
"""
from fastapi import Depends
from ..models.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Dict, Any, Optional
import uuid
import hashlib
from datetime import datetime

from ..models.database import (
    Transaction, Account, Category, ImportBatch, User, AuditLog, CategoryMapping
)
from ..services.csv_processor import process_csv_upload
from ..services.category_training import CategoryTrainingService
from ..auth.local_auth import get_current_user

class TransactionImportService:
    """Service for importing and processing transaction data"""
    
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
    
    async def import_from_csv(
        self,
        file_content: bytes,
        filename: str,
        account_name: str = "Default Account",
        account_type: str = "checking",
        auto_categorize: bool = True
    ) -> Dict[str, Any]:
        """Import transactions - LEARN from CSV categories first"""
        
        print(f"📤 Starting import: {filename} ({len(file_content)} bytes)")
        
        try:
            file_hash = hashlib.md5(file_content).hexdigest()
            
            import_batch = ImportBatch(
                user_id=str(self.user.id),
                filename=filename,
                file_size=len(file_content),
                file_hash=file_hash,
                status="processing"
            )
            
            self.db.add(import_batch)
            await self.db.commit()
            await self.db.refresh(import_batch)
            print(f"✅ Created batch: {import_batch.id}")

            account = await self._get_or_create_account(account_name, account_type)

            print("🔄 Processing CSV...")
            transactions_data, summary = process_csv_upload(
                file_content, 
                filename, 
                str(self.user.id),
                str(account.id) if account else None
            )
            print(f"✅ Processed {len(transactions_data)} transactions")

            # Get user's categories
            user_categories = await self._get_user_categories()
            print(f"📋 Available user categories: {len(user_categories)}")
            for cat in user_categories[:10]:
                parent_name = ""
                if cat.parent_id:
                    parent = next((c for c in user_categories if c.id == cat.parent_id), None)
                    if parent:
                        parent_name = f" (parent: {parent.name})"
                print(f"   - {cat.name}{parent_name} [type: {cat.category_type}]")
            
            # Debug first few transactions
            print(f"🔍 Sample CSV categories from first 5 transactions:")
            for i, trans in enumerate(transactions_data[:5]):
                print(f"   {i+1}. Main: '{trans.get('main_category')}' | Cat: '{trans.get('csv_category')}' | Sub: '{trans.get('csv_subcategory')}'")
            
            categorization_stats = {
                'csv_exact': 0,
                'none': 0
            }

            print(f"🎯 Mapping to user categories...")
            
            for idx, trans_data in enumerate(transactions_data):
                            if idx % 1000 == 0 and idx > 0:
                                print(f"   Progress: {idx}/{len(transactions_data)}")
                            
                            category_id = None
                            confidence_score = None
                            source_category = "imported"
                            
                            if auto_categorize:
                                csv_main = trans_data.get('main_category', '')
                                csv_cat = trans_data.get('csv_category', '')
                                csv_subcat = trans_data.get('csv_subcategory', '')
                                
                                category = await self._find_category_for_csv(
                                    csv_main, csv_cat, csv_subcat, user_categories
                                )
                                
                                if category:
                                    category_id = category.id
                                    confidence_score = 0.95
                                    source_category = 'csv_mapped'
                                    categorization_stats['csv_exact'] += 1
                                    
                                    # DEBUG: Print first 5 successful matches
                                    if idx < 5:
                                        print(f"   ✅ Matched: '{csv_cat}' / '{csv_subcat}' → {category.name} (ID: {category.id})")
                                else:
                                    categorization_stats['none'] += 1
                                    if idx < 5:
                                        print(f"   ❌ No match: '{csv_cat}' / '{csv_subcat}'")
                            
                            # CRITICAL DEBUG: Check what we're about to save
                            if idx < 3:
                                print(f"\n   🔍 Transaction {idx} before save:")
                                print(f"      category_id type: {type(category_id)}, value: {category_id}")
                                print(f"      Will save as: {str(category_id) if category_id else None}")
                            
                            transaction = Transaction(
                                id=str(uuid.uuid4()),
                                user_id=str(self.user.id),
                                account_id=trans_data.get('account_id'),
                                posted_at=trans_data['posted_at'],
                                amount=trans_data['amount'],
                                currency=trans_data.get('currency', 'EUR'),
                                merchant=trans_data.get('merchant'),
                                memo=trans_data.get('memo'),
                                category_id=str(category_id) if category_id else None,  # Make sure it's a string
                                import_batch_id=str(import_batch.id),
                                hash_dedupe=trans_data['hash_dedupe'],
                                source_category=source_category,
                                transaction_type=trans_data.get('transaction_type'),
                                main_category=trans_data.get('main_category'),
                                csv_category=trans_data.get('csv_category'),
                                csv_subcategory=trans_data.get('csv_subcategory'),
                                csv_account=trans_data.get('csv_account'),
                                owner=trans_data.get('owner'),
                                csv_account_type=trans_data.get('csv_account_type'),
                                is_expense=trans_data.get('is_expense', False),
                                is_income=trans_data.get('is_income', False),
                                year=trans_data.get('year'),
                                month=trans_data.get('month'),
                                year_month=trans_data.get('year_month'),
                                weekday=trans_data.get('weekday'),
                                transfer_pair_id=trans_data.get('transfer_pair_id'),
                                confidence_score=confidence_score,
                                review_needed=not category_id
                            )
                            
                            self.db.add(transaction)
            
            await self.db.commit()
            inserted_count = len(transactions_data)
            
            import_batch.rows_total = len(transactions_data)
            import_batch.rows_imported = inserted_count
            import_batch.rows_duplicated = 0
            import_batch.rows_errors = summary.get('errors', 0)
            import_batch.status = "completed"
            import_batch.completed_at = datetime.utcnow()
            import_batch.summary_data = {
                **summary,
                "categorization": categorization_stats
            }
            
            await self.db.commit()
            
            total_categorized = categorization_stats['csv_exact']
            
            elapsed = (datetime.utcnow() - import_batch.created_at).total_seconds()
            print(f"✅ Import complete: {inserted_count} transactions in {elapsed:.1f}s")
            print(f"📊 Categorization: {total_categorized}/{inserted_count} mapped ({total_categorized/inserted_count*100:.1f}%)")
            
            audit_entry = AuditLog(
                user_id=str(self.user.id),
                entity="transaction",
                action="bulk_import",
                details={
                    "filename": filename,
                    "batch_id": str(import_batch.id),
                    "rows_imported": inserted_count,
                    "categorization": categorization_stats,
                    "summary": summary
                }
            )
            self.db.add(audit_entry)
            await self.db.commit()
            
            return {
                "success": True,
                "batch_id": str(import_batch.id),
                "summary": {
                    **summary,
                    "rows_inserted": inserted_count,
                    "batch_id": str(import_batch.id),
                    "categorization": categorization_stats,
                    "auto_categorized": total_categorized,
                    "categorization_rate": (total_categorized / inserted_count * 100) if inserted_count > 0 else 0
                },
                "message": f"Imported {inserted_count} transactions. {total_categorized} matched ({total_categorized/inserted_count*100:.1f}%)."
            }
            
        except Exception as e:
            print(f"❌ Import failed: {e}")
            import traceback
            traceback.print_exc()
            
            if 'import_batch' in locals():
                try:
                    import_batch.status = "failed"
                    import_batch.error_message = str(e)
                    import_batch.completed_at = datetime.utcnow()
                    await self.db.commit()
                except:
                    await self.db.rollback()
            
            return {
                "success": False,
                "batch_id": "",
                "summary": {"error": str(e)},
                "message": f"Import failed: {str(e)}"
            }
    
    async def _get_user_categories(self) -> List:
        """Get all active user categories"""
        query = select(Category).where(
            and_(
                Category.user_id == self.user.id,
                Category.active == True
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def _find_category_for_csv(
        self,
        csv_main: str,
        csv_cat: str,
        csv_subcat: str,
        user_categories: List
    ) -> Optional[Category]:
        """Find matching user category - EXACT and FUZZY matching"""
        
        # Normalize inputs
        csv_main = (csv_main or '').lower().strip()
        csv_cat = (csv_cat or '').lower().strip()
        csv_subcat = (csv_subcat or '').lower().strip()
        
        # Try exact subcategory match
        if csv_subcat:
            for cat in user_categories:
                if cat.name.lower().strip() == csv_subcat:
                    return cat
        
        # Try exact category match
        if csv_cat:
            for cat in user_categories:
                if cat.name.lower().strip() == csv_cat:
                    return cat
        
        # Try fuzzy subcategory match
        if csv_subcat:
            for cat in user_categories:
                cat_name = cat.name.lower().strip()
                if csv_subcat in cat_name or cat_name in csv_subcat:
                    return cat
        
        # Try fuzzy category match
        if csv_cat:
            for cat in user_categories:
                cat_name = cat.name.lower().strip()
                if csv_cat in cat_name or cat_name in csv_cat:
                    return cat
        
        return None
    
    async def _get_or_create_account(
        self, 
        account_name: str, 
        account_type: str
    ) -> Optional[Account]:
        """Get existing account or create new one"""
        
        if not account_name:
            return None
        
        result = await self.db.execute(
            select(Account).where(
                and_(Account.user_id == str(self.user.id), Account.name == account_name)
            )
        )
        account = result.scalar_one_or_none()
        
        if not account:
            account = Account(
                user_id=str(self.user.id),
                name=account_name,
                account_type=account_type
            )
            self.db.add(account)
            await self.db.commit()
            await self.db.refresh(account)
            print(f"✅ Created account: {account.name}")
        
        return account
    
    async def create_default_category_mappings(self):
        """Create default category mappings"""
        
        categories_result = await self.db.execute(
            select(Category).where(Category.user_id == str(self.user.id))
        )
        user_categories = {cat.name.lower(): str(cat.id) for cat in categories_result.scalars().all()}
        
        default_mappings = [
            ("keyword", "starbucks", "cafes & coffee", 90),
            ("keyword", "mcdonald", "restaurants", 90),
            ("keyword", "netflix", "subscriptions", 95),
        ]
        
        created_count = 0
        for pattern_type, pattern_value, category_name, priority in default_mappings:
            category_id = user_categories.get(category_name.lower())
            if category_id:
                existing = await self.db.execute(
                    select(CategoryMapping).where(
                        and_(
                            CategoryMapping.user_id == str(self.user.id),
                            CategoryMapping.pattern_type == pattern_type,
                            CategoryMapping.pattern_value == pattern_value.lower()
                        )
                    )
                )
                
                if not existing.scalar_one_or_none():
                    mapping = CategoryMapping(
                        user_id=str(self.user.id),
                        pattern_type=pattern_type,
                        pattern_value=pattern_value.lower(),
                        category_id=category_id,
                        priority=priority,
                        confidence=0.9,
                        active=True
                    )
                    self.db.add(mapping)
                    created_count += 1
        
        if created_count > 0:
            await self.db.commit()
            print(f"✅ Created {created_count} default mappings")
        
        return created_count

def get_import_service(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TransactionImportService:
    """Get transaction import service instance"""
    return TransactionImportService(db, current_user)