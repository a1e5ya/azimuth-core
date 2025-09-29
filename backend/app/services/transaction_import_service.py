"""
Transaction import service - COMPLETE FIX for SQLite UUID issue
Replace backend/app/services/transaction_import_service.py with this
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
from ..services.category_mappings import CategoryMapper, PatternType
from ..auth.local_auth import get_current_user

class TransactionImportService:
    """Service for importing and processing transaction data"""
    
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
        self.category_mapper = CategoryMapper()
    
    async def import_from_csv(
        self,
        file_content: bytes,
        filename: str,
        account_name: str = "Default Account",
        account_type: str = "checking",
        auto_categorize: bool = True
    ) -> Dict[str, Any]:
        """Import transactions from CSV"""
        
        print(f"📤 Starting import: {filename} ({len(file_content)} bytes)")
        
        try:
            # Generate file hash
            file_hash = hashlib.md5(file_content).hexdigest()
            
            # Create import batch
            import_batch = ImportBatch(
                user_id=str(self.user.id),  # SQLite: Convert UUID to string
                filename=filename,
                file_size=len(file_content),
                file_hash=file_hash,
                status="processing"
            )
            
            self.db.add(import_batch)
            await self.db.commit()
            await self.db.refresh(import_batch)
            print(f"✅ Created batch: {import_batch.id}")

            # Get or create account
            account = await self._get_or_create_account(account_name, account_type)

            # Process CSV
            print("🔄 Processing CSV...")
            transactions_data, summary = process_csv_upload(
                file_content, 
                filename, 
                str(self.user.id),
                str(account.id) if account else None
            )
            print(f"✅ Processed {len(transactions_data)} transactions")

            # Insert transactions - FIXED: All IDs as strings for SQLite
            inserted_count = 0
            for trans_data in transactions_data:
                transaction = Transaction(
                    id=str(uuid.uuid4()),  # String for SQLite
                    user_id=str(self.user.id),  # String for SQLite
                    account_id=trans_data.get('account_id'),  # Already string from CSV processor
                    posted_at=trans_data['posted_at'],
                    amount=trans_data['amount'],
                    currency=trans_data.get('currency', 'EUR'),
                    merchant=trans_data.get('merchant'),
                    memo=trans_data.get('memo'),
                    import_batch_id=str(import_batch.id),  # String for SQLite
                    hash_dedupe=trans_data['hash_dedupe'],
                    source_category="imported",
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
                    transfer_pair_id=trans_data.get('transfer_pair_id')
                )
                
                self.db.add(transaction)
                inserted_count += 1

            await self.db.commit()
            
            # Update batch status
            import_batch.rows_total = len(transactions_data)
            import_batch.rows_imported = inserted_count
            import_batch.rows_duplicated = 0
            import_batch.rows_errors = summary.get('errors', 0)
            import_batch.status = "completed"
            import_batch.completed_at = datetime.utcnow()
            import_batch.summary_data = {
                **summary,
                "auto_categorized_count": 0
            }
            
            await self.db.commit()
            
            print(f"✅ Import complete: {inserted_count} transactions")
            
            # Log import
            audit_entry = AuditLog(
                user_id=str(self.user.id),  # String for SQLite
                entity="transaction",
                action="bulk_import",
                details={
                    "filename": filename,
                    "batch_id": str(import_batch.id),
                    "rows_imported": inserted_count,
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
                    "batch_id": str(import_batch.id)
                },
                "message": f"Successfully imported {inserted_count} transactions"
            }
            
        except Exception as e:
            print(f"❌ Import failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Update batch on error
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
    
    async def _get_or_create_account(
        self, 
        account_name: str, 
        account_type: str
    ) -> Optional[Account]:
        """Get existing account or create new one"""
        
        if not account_name:
            return None
        
        # Find existing account
        result = await self.db.execute(
            select(Account).where(
                and_(Account.user_id == str(self.user.id), Account.name == account_name)
            )
        )
        account = result.scalar_one_or_none()
        
        if not account:
            # Create new account
            account = Account(
                user_id=str(self.user.id),  # String for SQLite
                name=account_name,
                account_type=account_type
            )
            self.db.add(account)
            await self.db.commit()
            await self.db.refresh(account)
            print(f"✅ Created account: {account.name}")
        
        return account
    
    async def _load_categorization_data(self):
        """Load user categories and mappings"""
        
        categories_result = await self.db.execute(
            select(Category).where(
                and_(Category.user_id == str(self.user.id), Category.active == True)
            )
        )
        user_categories = {cat.name.lower(): cat for cat in categories_result.scalars().all()}
        
        mappings_result = await self.db.execute(
            select(CategoryMapping).where(
                and_(CategoryMapping.user_id == str(self.user.id), CategoryMapping.active == True)
            ).order_by(CategoryMapping.priority.desc())
        )
        mappings = mappings_result.scalars().all()
        
        from ..services.category_mappings import CategoryMapping as CMMapping, PatternType
        
        cm_mappings = []
        for mapping in mappings:
            try:
                cm_mappings.append(CMMapping(
                    id=str(mapping.id),
                    user_id=str(mapping.user_id),
                    pattern_type=PatternType(mapping.pattern_type),
                    pattern_value=mapping.pattern_value,
                    category_id=str(mapping.category_id),
                    priority=mapping.priority,
                    confidence=float(mapping.confidence),
                    active=mapping.active,
                    description=f"{mapping.pattern_type}: {mapping.pattern_value}"
                ))
            except ValueError:
                continue
        
        self.category_mapper.load_mappings(cm_mappings)
        self.user_categories = user_categories
        
        print(f"🏷️ Loaded {len(user_categories)} categories and {len(cm_mappings)} mappings")
    
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
                        category_id=category_id,  # Already a string
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