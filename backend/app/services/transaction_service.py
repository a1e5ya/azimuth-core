"""
Consolidated Transaction Service - WITH TRANSFER DETECTION
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_, func, or_, desc, asc, extract
from sqlalchemy.orm import selectinload, joinedload
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime, date, timedelta
import uuid
import hashlib
from fastapi import Depends, HTTPException

from ..models.database import (
    Transaction, Account, Category, ImportBatch, User, AuditLog, Owner, get_db
)
from ..services.csv_processor import process_csv_upload
from ..services.category_service import CategoryService
from ..auth.local_auth import get_current_user


# ============================================================================
# TRANSACTION IMPORT SERVICE
# ============================================================================

class TransactionImportService:
    """Handles CSV import with two modes: training (categorized) and account (uncategorized)"""
    
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
        self.category_service = CategoryService(db, user)
    
    async def import_from_csv(
        self, file_content: bytes, filename: str,
        import_mode: str = "training",  # "training" or "account"
        account_id: str = None,
        auto_categorize: bool = True
    ) -> Dict[str, Any]:
        """
        Import transactions with two modes:
        - training: Pre-categorized data, auto-creates categories from CSV
        - account: Uncategorized bank data, direct to account
        """
        
        print(f"📤 Starting import: {filename} (mode: {import_mode})")
        
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

            # Process CSV
            transactions_data, summary = process_csv_upload(
                file_content, filename, str(self.user.id), None
            )
            print(f"✅ Processed {len(transactions_data)} transactions")

            # Mode-specific handling
            if import_mode == "training":
                result = await self._import_training_data(
                    transactions_data, import_batch, auto_categorize
                )
            else:  # account mode
                result = await self._import_to_account(
                    transactions_data, import_batch, account_id
                )
            
            import_batch.rows_total = len(transactions_data)
            import_batch.rows_imported = len(transactions_data)
            import_batch.status = "completed"
            import_batch.completed_at = datetime.utcnow()
            import_batch.summary_data = {
                **summary,
                **result.get("stats", {}),
                "import_mode": import_mode
            }
            
            await self.db.commit()
            
            print(f"✅ Import complete: {len(transactions_data)} transactions")
            
            return {
                "success": True,
                "batch_id": str(import_batch.id),
                "summary": {
                    **summary,
                    "rows_inserted": len(transactions_data),
                    **result.get("stats", {})
                },
                "message": f"Imported {len(transactions_data)} transactions"
            }
            
        except Exception as e:
            print(f"❌ Import failed: {e}")
            if 'import_batch' in locals():
                import_batch.status = "failed"
                import_batch.error_message = str(e)
                await self.db.commit()
            
            return {
                "success": False,
                "message": f"Import failed: {str(e)}"
            }
    
    async def _import_training_data(
        self, transactions_data: List[Dict], import_batch: ImportBatch,
        auto_categorize: bool
    ) -> Dict[str, Any]:
        """Import pre-categorized training data with auto-creation"""
        
        # Auto-create owners and accounts
        owner_account_map = await self._auto_create_owners_and_accounts(transactions_data)
        print(f"✅ Created {len(owner_account_map)} account mappings")
        
        categorization_stats = {'auto_created': 0, 'csv_mapped': 0, 'none': 0}
        
        # Insert transactions
        for trans_data in transactions_data:
            # Determine account
            owner_name = trans_data.get('owner', '').strip()
            account_type = trans_data.get('bank_account_type', '').strip()
            key = (owner_name, account_type)
            transaction_account_id = str(owner_account_map[key].id) if key in owner_account_map else None
            
            # Auto-categorize with auto-creation
            category_id = None
            confidence_score = None
            source_category = "imported"
            
            if auto_categorize:
                csv_main = trans_data.get('main_category', '').strip()
                csv_cat = trans_data.get('category', '').strip()
                csv_subcat = trans_data.get('subcategory', '').strip()
                
                # Treat "-" as empty
                if csv_main == '-':
                    csv_main = ''
                if csv_cat == '-':
                    csv_cat = ''
                if csv_subcat == '-':
                    csv_subcat = ''
                
                if csv_main:
                    # Use ensure_categories_from_csv to auto-create
                    category = await self.category_service.ensure_categories_from_csv(
                        csv_main, csv_cat, csv_subcat
                    )
                    
                    if category:
                        category_id = category.id
                        confidence_score = 0.95
                        source_category = 'csv_mapped'
                        categorization_stats['auto_created'] += 1
                    else:
                        # If category creation failed, mark as Uncategorized
                        uncategorized = await self.category_service.get_or_create_uncategorized()
                        category_id = uncategorized.id
                        source_category = 'imported'
                        categorization_stats['none'] += 1
                else:
                    # If CSV has empty categories, mark as Uncategorized
                    uncategorized = await self.category_service.get_or_create_uncategorized()
                    category_id = uncategorized.id
                    source_category = 'imported'
                    categorization_stats['none'] += 1
            
            # Derive is_income/is_expense from main_category
            main_cat_raw = (trans_data.get('main_category') or '').strip()
            is_income = (main_cat_raw.upper() == 'INCOME')
            is_expense = (main_cat_raw.upper() == 'EXPENSES')
            
            transaction = Transaction(
                id=str(uuid.uuid4()),
                user_id=str(self.user.id),
                account_id=transaction_account_id,
                posted_at=trans_data['posted_at'],
                amount=trans_data['amount'],
                currency=trans_data.get('currency', 'EUR'),
                merchant=trans_data.get('merchant'),
                memo=trans_data.get('memo'),
                category_id=str(category_id) if category_id else None,
                import_batch_id=str(import_batch.id),
                hash_dedupe=trans_data['hash_dedupe'],
                source_category=source_category,
                main_category=main_cat_raw,
                category=trans_data.get('category', '').strip() if trans_data.get('category') else None,
                subcategory=trans_data.get('subcategory', '').strip() if trans_data.get('subcategory') else None,
                bank_account=trans_data.get('bank_account'),
                owner=trans_data.get('owner'),
                bank_account_type=trans_data.get('bank_account_type'),
                is_expense=is_expense,
                is_income=is_income,
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
    
        # Transfer detection
        from .transfer_detector import TransferDetector
        detector = TransferDetector(self.db, self.user)
        pairs_found = await detector.detect_pairs()
        
        # ✅ Train categories with detailed progress
        from .category_training import CategoryTrainingService
        trainer = CategoryTrainingService(self.db, self.user)
        
        training_log = []
        
        async def track_progress(current, total, category_name):
            """Store progress messages"""
            msg = f"Training {current}/{total}: {category_name}"
            training_log.append(msg)
            print(f"   📝 {msg}")
        
        trained_count = await trainer.train_all_categories(track_progress)
        
        return {
            "stats": {
                "categorization": categorization_stats,
                "auto_categorized": categorization_stats['auto_created'],
                "transfer_pairs_found": pairs_found,
                "categories_trained": trained_count,
                "training_log": training_log  # ✅ For chat display
            }
        }
    
    async def _import_to_account(
        self, transactions_data: List[Dict], import_batch: ImportBatch,
        account_id: str
    ) -> Dict[str, Any]:
        """Import uncategorized bank data directly to account"""
        
        # Verify account
        account_query = select(Account).where(
            and_(Account.id == account_id, Account.user_id == self.user.id)
        )
        account_result = await self.db.execute(account_query)
        account = account_result.scalar_one_or_none()
        
        if not account:
            raise Exception(f"Account {account_id} not found")
        
        print(f"✅ Importing to account: {account.name}")
        
        # Insert transactions (no categorization)
        for trans_data in transactions_data:
            transaction = Transaction(
                id=str(uuid.uuid4()),
                user_id=str(self.user.id),
                account_id=str(account.id),
                posted_at=trans_data['posted_at'],
                amount=trans_data['amount'],
                currency=trans_data.get('currency', 'EUR'),
                merchant=trans_data.get('merchant'),
                memo=trans_data.get('memo'),
                category_id=None,
                import_batch_id=str(import_batch.id),
                hash_dedupe=trans_data['hash_dedupe'],
                source_category='imported',
                main_category=None,
                category=None,
                subcategory=None,
                bank_account=None,
                owner=None,
                bank_account_type=None,
                is_expense=trans_data['amount'] < 0,
                is_income=trans_data['amount'] > 0,
                year=trans_data.get('year'),
                month=trans_data.get('month'),
                year_month=trans_data.get('year_month'),
                weekday=trans_data.get('weekday'),
                transfer_pair_id=None,
                confidence_score=None,
                review_needed=True
            )
            
            self.db.add(transaction)
        
        await self.db.commit()
    
        # Transfer detection
        from .transfer_detector import TransferDetector
        detector = TransferDetector(self.db, self.user)
        pairs_found = await detector.detect_pairs()
        
        # ✅ LLM categorization
        from .llm_categorizer import LLMCategorizationService
        llm_service = LLMCategorizationService(self.db, self.user)
        
        uncategorized_query = select(Transaction).where(
            and_(
                Transaction.import_batch_id == import_batch.id,
                Transaction.category_id.is_(None)
            )
        )
        uncategorized_result = await self.db.execute(uncategorized_query)
        uncategorized = uncategorized_result.scalars().all()
        
        categorized_by_llm = 0
        
        for transaction in uncategorized:
            result = await llm_service.categorize_transaction(
                merchant=transaction.merchant,
                memo=transaction.memo,
                amount=float(transaction.amount),
                csv_main=None,
                category=None,
                subcategory=None
            )
            
            if result['category_id']:
                transaction.category_id = result['category_id']
                transaction.source_category = result['method']
                transaction.confidence_score = result['confidence']
                transaction.review_needed = result['confidence'] < 0.7
                categorized_by_llm += 1
        
        await self.db.commit()
        
        # ✅ Train categories after LLM categorization
        from .category_training import CategoryTrainingService
        trainer = CategoryTrainingService(self.db, self.user)
        
        training_log = []
        
        async def track_progress(current, total, category_name):
            msg = f"Training {current}/{total}: {category_name}"
            training_log.append(msg)
            print(f"   📝 {msg}")
        
        trained_count = await trainer.train_all_categories(track_progress)
        
        return {
            "stats": {
                "uncategorized": len(transactions_data),
                "transfer_pairs_found": pairs_found,
                "llm_categorized": categorized_by_llm,
                "needs_review": len(transactions_data) - pairs_found - categorized_by_llm,
                "categories_trained": trained_count,
                "training_log": training_log  # ✅ NEW
            }
        }
    
    async def _auto_create_owners_and_accounts(self, transactions_data: List[Dict]) -> Dict:
        """Auto-create Owner and Account records from CSV data"""
        
        unique_combinations = set()
        for trans in transactions_data:
            owner_name = (trans.get('owner') or '').strip()
            bank_account = (trans.get('bank_account') or '').strip()
            account_type = (trans.get('bank_account_type') or '').strip()
            
            if owner_name and account_type:
                unique_combinations.add((owner_name, bank_account, account_type))
        
        owner_account_map = {}
        
        # Get existing owners
        existing_owners_query = select(Owner).where(Owner.user_id == self.user.id)
        existing_owners_result = await self.db.execute(existing_owners_query)
        existing_owners = {owner.name: owner for owner in existing_owners_result.scalars().all()}
        
        for owner_name, bank_account, account_type in sorted(unique_combinations):
            # Get or create owner
            if owner_name in existing_owners:
                owner = existing_owners[owner_name]
            else:
                colors = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6']
                color = colors[len(existing_owners) % len(colors)]
                
                owner = Owner(
                    id=str(uuid.uuid4()),
                    user_id=str(self.user.id),
                    name=owner_name,
                    color=color,
                    active=True
                )
                self.db.add(owner)
                await self.db.flush()
                existing_owners[owner_name] = owner
            
            # Check if account exists
            account_query = select(Account).where(
                and_(
                    Account.owner_id == owner.id,
                    Account.account_type == account_type
                )
            )
            account_result = await self.db.execute(account_query)
            account = account_result.scalar_one_or_none()
            
            if not account:
                account_name = bank_account if bank_account else f"{owner_name}'s {account_type}"
                
                account = Account(
                    id=str(uuid.uuid4()),
                    user_id=str(self.user.id),
                    owner_id=str(owner.id),
                    name=account_name,
                    account_type=account_type,
                    current_balance=0.0,
                    active=True
                )
                self.db.add(account)
                await self.db.flush()
            
            owner_account_map[(owner_name, account_type)] = account
        
        await self.db.commit()
        return owner_account_map


# ============================================================================
# TRANSACTION QUERIES & ANALYTICS
# ============================================================================

class TransactionQueries:
    """Database queries for transaction operations"""
    
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
    
    async def get_transaction_by_id(self, transaction_id: str) -> Optional[Transaction]:
        """Get single transaction by ID"""
        query = select(Transaction).options(
            selectinload(Transaction.assigned_category)
        ).where(
            and_(
                Transaction.id == uuid.UUID(transaction_id),
                Transaction.user_id == self.user.id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    

    async def get_transactions_with_filters(
        self, filters: Dict[str, Any]
    ) -> Tuple[List[Transaction], int]:
        """Get transactions with filters and pagination"""
        
        query = select(Transaction).where(Transaction.user_id == self.user.id)
        count_query = select(func.count(Transaction.id)).where(Transaction.user_id == self.user.id)
        
        # Build filter conditions
        conditions = []
        
        if filters.get('start_date'):
            conditions.append(Transaction.posted_at >= filters['start_date'])
        if filters.get('end_date'):
            conditions.append(Transaction.posted_at <= filters['end_date'])
        if filters.get('min_amount') is not None:
            conditions.append(Transaction.amount >= filters['min_amount'])
        if filters.get('max_amount') is not None:
            conditions.append(Transaction.amount <= filters['max_amount'])
        if filters.get('merchant'):
            search_term = f"%{filters['merchant']}%"
            conditions.append(
                or_(
                    Transaction.merchant.ilike(search_term),
                    Transaction.memo.ilike(search_term)
                )
            )
        if filters.get('category_id'):
            conditions.append(Transaction.category_id == uuid.UUID(filters['category_id']))
        if filters.get('main_category'):
            conditions.append(Transaction.main_category == filters['main_category'])
        if filters.get('review_needed') is not None:
            conditions.append(Transaction.review_needed == filters['review_needed'])
        
        # Array filters
        if filters.get('owners') and len(filters['owners']) > 0:
            conditions.append(Transaction.owner.in_(filters['owners']))
        if filters.get('account_types') and len(filters['account_types']) > 0:
            conditions.append(Transaction.bank_account_type.in_(filters['account_types']))
        if filters.get('main_categories') and len(filters['main_categories']) > 0:
            upper_categories = [cat.upper() for cat in filters['main_categories']]
            conditions.append(func.upper(Transaction.main_category).in_(upper_categories))
        if filters.get('categories') and len(filters['categories']) > 0:
            upper_categories = [cat.upper() for cat in filters['categories']]
            conditions.append(func.upper(Transaction.category).in_(upper_categories))
        if filters.get('subcategories') and len(filters['subcategories']) > 0:
            upper_subcategories = [sub.upper() for sub in filters['subcategories']]
            conditions.append(func.upper(Transaction.subcategory).in_(upper_subcategories))
        
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        
        # GET COUNT
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar()
        
        # Apply sorting
        sort_by = filters.get('sort_by', 'posted_at')
        sort_order = filters.get('sort_order', 'desc')
        sort_column = getattr(Transaction, sort_by, Transaction.posted_at)
        
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Pagination
        page = filters.get('page', 1)
        limit = filters.get('limit', 50)
        query = query.offset((page - 1) * limit).limit(limit)
        query = query.options(
        selectinload(Transaction.assigned_category).selectinload(Category.parent)
        )
        
        result = await self.db.execute(query)
        transactions = result.scalars().all()
        
        return transactions, total_count
    
    async def get_transaction_summary(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get comprehensive transaction summary"""
        
        base_conditions = [Transaction.user_id == self.user.id]
        if start_date:
            base_conditions.append(Transaction.posted_at >= start_date)
        if end_date:
            base_conditions.append(Transaction.posted_at <= end_date)
        
        base_condition = and_(*base_conditions)
        
        # Total count and amount
        count_query = select(
            func.count(Transaction.id),
            func.coalesce(func.sum(Transaction.amount), 0)
        ).where(base_condition)
        count_result = await self.db.execute(count_query)
        total_transactions, total_amount = count_result.first()
        
        # Date range
        date_query = select(
            func.min(Transaction.posted_at),
            func.max(Transaction.posted_at)
        ).where(base_condition)
        date_result = await self.db.execute(date_query)
        earliest, latest = date_result.first()
        
        # Amounts by type
        amounts_query = select(
            Transaction.main_category,
            func.sum(Transaction.amount).label('total_amount'),
            func.count(Transaction.id).label('count')
        ).where(base_condition).group_by(Transaction.main_category)
        
        amounts_result = await self.db.execute(amounts_query)
        
        by_type = {}
        income_amount = 0
        expense_amount = 0
        transfer_amount = 0
        
        for row in amounts_result:
            trans_type = row.main_category or 'unknown'
            amount = float(row.total_amount or 0)
            by_type[trans_type] = row.count
            
            if trans_type == 'INCOME':
                income_amount = amount
            elif trans_type == 'EXPENSES':
                expense_amount = abs(amount)
            elif trans_type == 'TRANSFERS':
                transfer_amount = amount
        
        # By month
        month_query = select(
            Transaction.year_month,
            func.sum(func.abs(Transaction.amount))
        ).where(base_condition).group_by(Transaction.year_month).order_by(Transaction.year_month)
        month_result = await self.db.execute(month_query)
        by_month = {row[0]: float(row[1] or 0) for row in month_result if row[0]}
        
        # Categorization stats
        categorized_query = select(func.count(Transaction.id)).where(
            and_(base_condition, Transaction.category_id.isnot(None))
        )
        categorized_result = await self.db.execute(categorized_query)
        categorized_count = categorized_result.scalar()
        
        # Recent imports
        import_query = select(
            Transaction.import_batch_id,
            func.count(Transaction.id)
        ).where(base_condition).group_by(
            Transaction.import_batch_id
        ).order_by(desc(func.max(Transaction.created_at))).limit(5)
        import_result = await self.db.execute(import_query)
        recent_imports = [
            {"batch_id": row[0], "count": row[1]} 
            for row in import_result if row[0]
        ]
        
        # Top merchants
        merchant_query = select(
            Transaction.merchant,
            func.count(Transaction.id),
            func.sum(func.abs(Transaction.amount))
        ).where(
            and_(base_condition, Transaction.merchant.isnot(None))
        ).group_by(Transaction.merchant).order_by(
            desc(func.sum(func.abs(Transaction.amount)))
        ).limit(10)
        merchant_result = await self.db.execute(merchant_query)
        top_merchants = [
            {"name": row[0], "count": row[1], "amount": float(row[2] or 0)}
            for row in merchant_result
        ]
        
        # Top categories
        category_query = select(
            Transaction.category,
            func.count(Transaction.id),
            func.sum(func.abs(Transaction.amount))
        ).where(
            and_(base_condition, Transaction.category.isnot(None))
        ).group_by(Transaction.category).order_by(
            desc(func.count(Transaction.id))
        ).limit(10)
        category_result = await self.db.execute(category_query)
        top_categories = [
            {"name": row[0], "count": row[1], "amount": float(row[2] or 0)}
            for row in category_result
        ]
        
        return {
            "total_transactions": total_transactions or 0,
            "total_amount": float(total_amount),
            "income_amount": income_amount,
            "expense_amount": expense_amount,
            "transfer_amount": transfer_amount,
            "categorized_count": categorized_count,
            "categorization_rate": categorized_count / total_transactions if total_transactions > 0 else 0,
            "date_range": {
                "earliest": earliest.isoformat() if earliest else None,
                "latest": latest.isoformat() if latest else None
            },
            "by_type": by_type,
            "by_month": by_month,
            "recent_imports": recent_imports,
            "top_merchants": top_merchants,
            "top_categories": top_categories
        }


# ============================================================================
# TRANSACTION CRUD SERVICE
# ============================================================================

class TransactionService:
    """Service for transaction CRUD operations"""
    
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
    
    async def categorize_transaction(
        self, transaction_id: str, category_id: str,
        confidence: float = 1.0, notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Categorize a single transaction"""
        try:
            transaction_query = select(Transaction).where(
                and_(
                    Transaction.id == uuid.UUID(transaction_id),
                    Transaction.user_id == self.user.id
                )
            )
            result = await self.db.execute(transaction_query)
            transaction = result.scalar_one_or_none()
            
            if not transaction:
                return {"success": False, "message": "Transaction not found"}
            
            category_query = select(Category).options(
                selectinload(Category.parent)
            ).where(
                and_(
                    Category.id == uuid.UUID(category_id),
                    Category.user_id == self.user.id
                )
            )
            category_result = await self.db.execute(category_query)
            category = category_result.scalar_one_or_none()
            
            if not category:
                return {"success": False, "message": "Category not found"}
            
            # Update category_id
            transaction.category_id = uuid.UUID(category_id)
            transaction.source_category = "user"
            transaction.confidence_score = confidence
            transaction.review_needed = False
            transaction.updated_at = datetime.utcnow()
            
            # UPDATE CSV FIELDS - Get full hierarchy
            main_cat = None
            mid_cat = None
            sub_cat = category.name
            
            if category.parent:
                mid_cat = category.parent.name
                if category.parent.parent:
                    main_cat = category.parent.parent.name
                else:
                    main_cat = category.parent.name
                    mid_cat = category.name
                    sub_cat = None
            else:
                main_cat = category.name
                mid_cat = None
                sub_cat = None
            
            transaction.main_category = main_cat
            transaction.category = mid_cat
            transaction.subcategory = sub_cat
            
            if notes:
                transaction.notes = notes
            
            await self.db.commit()
            
            return {
                "success": True,
                "message": f"Transaction categorized as {category.name}"
            }
            
        except Exception as e:
            await self.db.rollback()
            return {"success": False, "message": str(e)}
    
    async def update_transaction(
        self, transaction_id: str, merchant: Optional[str] = None,
        amount: Optional[float] = None, memo: Optional[str] = None,
        category_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update transaction details"""
        try:
            try:
                trans_uuid = uuid.UUID(transaction_id)
            except ValueError:
                return {"success": False, "message": "Invalid transaction ID format"}
            
            transaction_query = select(Transaction).where(
                and_(
                    Transaction.id == str(trans_uuid),
                    Transaction.user_id == str(self.user.id)
                )
            )
            result = await self.db.execute(transaction_query)
            transaction = result.scalar_one_or_none()
            
            if not transaction:
                return {"success": False, "message": "Transaction not found"}
            
            if merchant is not None:
                transaction.merchant = merchant
            if amount is not None:
                transaction.amount = amount
                transaction.is_expense = amount < 0
                transaction.is_income = amount > 0
            if memo is not None:
                transaction.memo = memo
            if category_id is not None:
                try:
                    cat_uuid = uuid.UUID(category_id)
                except ValueError:
                    return {"success": False, "message": "Invalid category ID format"}
                
                category_query = select(Category).where(
                    and_(
                        Category.id == str(cat_uuid),
                        Category.user_id == str(self.user.id)
                    )
                )
                category_result = await self.db.execute(category_query)
                category = category_result.scalar_one_or_none()
                
                if not category:
                    return {"success": False, "message": "Category not found"}
                
                transaction.category_id = str(cat_uuid)
                transaction.source_category = "user"
                transaction.review_needed = False
            
            transaction.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            return {
                "success": True,
                "message": "Transaction updated successfully"
            }
            
        except Exception as e:
            await self.db.rollback()
            print(f"❌ Update failed: {e}")
            return {"success": False, "message": str(e)}


    async def bulk_categorize(
        self, transaction_ids: List[str], category_id: str,
        confidence: float = 1.0
    ) -> Dict[str, Any]:
        """Bulk categorize multiple transactions"""
        try:
            try:
                cat_uuid = uuid.UUID(category_id)
            except ValueError:
                return {"success": False, "message": "Invalid category ID format", "updated_count": 0}
            
            category_query = select(Category).options(
                selectinload(Category.parent).selectinload(Category.parent)
            ).where(
                and_(
                    Category.id == str(cat_uuid),
                    Category.user_id == str(self.user.id)
                )
            )
            category_result = await self.db.execute(category_query)
            category = category_result.scalar_one_or_none()
            
            if not category:
                return {"success": False, "message": "Category not found", "updated_count": 0}
            
            # Get full hierarchy for CSV fields
            main_cat = None
            mid_cat = None
            sub_cat = category.name

            if category.parent:
                mid_cat = category.parent.name
                if category.parent.parent:
                    main_cat = category.parent.parent.name
                else:
                    main_cat = category.parent.name
                    mid_cat = category.name
                    sub_cat = None
            else:
                main_cat = category.name
                mid_cat = None
                sub_cat = None
            
            trans_ids = [str(uuid.UUID(tid)) for tid in transaction_ids]
            
            from sqlalchemy import update
            update_query = update(Transaction).where(
                and_(
                    Transaction.id.in_(trans_ids),
                    Transaction.user_id == str(self.user.id)
                )
            ).values(
                category_id=str(cat_uuid),
                main_category=main_cat,
                category=mid_cat,
                subcategory=sub_cat,
                source_category="user",
                confidence_score=confidence,
                review_needed=False,
                updated_at=datetime.utcnow()
            )
            
            result = await self.db.execute(update_query)
            await self.db.commit()
            
            return {
                "success": True,
                "message": f"Categorized {result.rowcount} transactions as {category.name}",
                "updated_count": result.rowcount
            }
            
        except Exception as e:
            await self.db.rollback()
            print(f"❌ Bulk categorize failed: {e}")
            return {"success": False, "message": str(e), "updated_count": 0}
    
    async def delete_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """Delete a transaction"""
        try:
            delete_query = delete(Transaction).where(
                and_(
                    Transaction.id == uuid.UUID(transaction_id),
                    Transaction.user_id == self.user.id
                )
            )
            await self.db.execute(delete_query)
            await self.db.commit()
            
            return {"success": True, "message": "Transaction deleted"}
        except Exception as e:
            await self.db.rollback()
            return {"success": False, "message": str(e)}


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_import_service(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TransactionImportService:
    return TransactionImportService(db, current_user)

def get_transaction_queries(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TransactionQueries:
    return TransactionQueries(db, current_user)

def get_transaction_service(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TransactionService:
    return TransactionService(db, current_user)