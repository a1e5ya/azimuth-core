"""
Consolidated Transaction Service - Handles all transaction operations
Merged from: transaction_import_service, transaction_queries, 
             transaction_service, parts of transaction_analytics
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_, func, or_, desc, asc, extract
from sqlalchemy.orm import selectinload
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
    """Handles CSV import and auto-categorization"""
    
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
        """Import transactions with mode selection and auto-create owners/accounts"""
        
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

            # Auto-create owners and accounts in training mode
            owner_account_map = {}
            
            if import_mode == "training":
                owner_account_map = await self._auto_create_owners_and_accounts(transactions_data)
                print(f"✅ Created {len(owner_account_map)} account mappings")
            
            elif import_mode == "account" and account_id:
                account_query = select(Account).where(
                    and_(Account.id == account_id, Account.user_id == self.user.id)
                )
                account_result = await self.db.execute(account_query)
                account = account_result.scalar_one_or_none()
                
                if not account:
                    raise Exception(f"Account {account_id} not found")
                
                print(f"✅ Using account: {account.name}")

            # Get user categories
            user_categories_query = select(Category).where(
                and_(Category.user_id == self.user.id, Category.active == True)
            )
            user_categories_result = await self.db.execute(user_categories_query)
            user_categories = user_categories_result.scalars().all()
            
            categorization_stats = {'csv_exact': 0, 'none': 0}

            # Insert transactions
            for trans_data in transactions_data:
                category_id = None
                confidence_score = None
                source_category = "imported"
                
                # Determine account
                transaction_account_id = None
                
                if import_mode == "training":
                    owner_name = trans_data.get('owner', '').strip()
                    account_type = trans_data.get('bank_account_type', '').strip()
                    key = (owner_name, account_type)
                    if key in owner_account_map:
                        transaction_account_id = str(owner_account_map[key].id)
                
                elif import_mode == "account" and account:
                    transaction_account_id = str(account.id)
                
                # Auto-categorize with auto-creation
                if auto_categorize:
                    csv_main = trans_data.get('main_category', '')
                    csv_cat = trans_data.get('category', '')
                    csv_subcat = trans_data.get('subcategory', '')
                    
                    # Use ensure_categories_from_csv to auto-create if needed
                    if csv_main:
                        category = await self.category_service.ensure_categories_from_csv(
                            csv_main, csv_cat, csv_subcat
                        )
                        
                        if category:
                            category_id = category.id
                            confidence_score = 0.95
                            source_category = 'csv_mapped'
                            categorization_stats['csv_exact'] += 1
                        else:
                            categorization_stats['none'] += 1
                    else:
                        categorization_stats['none'] += 1
                
                # FIXED: Derive is_income/is_expense from main_category STRING
                main_cat_upper = (trans_data.get('main_category') or '').upper()
                is_income = (main_cat_upper == 'INCOME')
                is_expense = (main_cat_upper == 'EXPENSES')
                
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
                    main_category=trans_data.get('main_category'),
                    category=trans_data.get('category'),
                    subcategory=trans_data.get('subcategory'),
                    bank_account=trans_data.get('bank_account'),
                    owner=trans_data.get('owner'),
                    bank_account_type=trans_data.get('bank_account_type'),
                    is_expense=is_expense,  # FIXED
                    is_income=is_income,    # FIXED
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
            
            # Link transfer pairs
            await self._link_transfer_pairs(str(import_batch.id))
            
            import_batch.rows_total = len(transactions_data)
            import_batch.rows_imported = len(transactions_data)
            import_batch.status = "completed"
            import_batch.completed_at = datetime.utcnow()
            import_batch.summary_data = {
                **summary,
                "categorization": categorization_stats,
                "import_mode": import_mode
            }
            
            await self.db.commit()
            
            total_categorized = categorization_stats['csv_exact']
            print(f"✅ Import complete: {len(transactions_data)} transactions")
            
            return {
                "success": True,
                "batch_id": str(import_batch.id),
                "summary": {
                    **summary,
                    "rows_inserted": len(transactions_data),
                    "categorization": categorization_stats,
                    "auto_categorized": total_categorized
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
    
    async def _link_transfer_pairs(self, batch_id: str):
        """Link transfer pairs by Transfer_Pair_ID"""
        
        # Get transactions with transfer_pair_id
        query = select(Transaction).where(
            and_(
                Transaction.import_batch_id == batch_id,
                Transaction.transfer_pair_id.isnot(None)
            )
        )
        result = await self.db.execute(query)
        transactions = result.scalars().all()
        
        # Group by transfer_pair_id
        pairs = {}
        for trans in transactions:
            pair_id = trans.transfer_pair_id
            if pair_id not in pairs:
                pairs[pair_id] = []
            pairs[pair_id].append(trans)
        
        # Verify pairs (should have 2 transactions: one positive, one negative)
        linked_count = 0
        for pair_id, pair_transactions in pairs.items():
            if len(pair_transactions) == 2:
                amounts = [float(t.amount) for t in pair_transactions]
                # Should net to ~0
                if abs(sum(amounts)) < 0.01:
                    linked_count += 1
                    print(f"✓ Linked transfer pair: {pair_id}")
        
        print(f"✅ Linked {linked_count} transfer pairs")


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
            conditions.append(Transaction.merchant.ilike(f"%{filters['merchant']}%"))
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
            conditions.append(Transaction.main_category.in_(filters['main_categories']))
        
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        
        # Get count
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
        query = query.options(selectinload(Transaction.assigned_category))
        
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
        
        # Total count
        count_query = select(func.count(Transaction.id)).where(base_condition)
        count_result = await self.db.execute(count_query)
        total_transactions = count_result.scalar()
        
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
        
        # Categorization stats
        categorized_query = select(func.count(Transaction.id)).where(
            and_(base_condition, Transaction.category_id.isnot(None))
        )
        categorized_result = await self.db.execute(categorized_query)
        categorized_count = categorized_result.scalar()
        
        return {
            "total_transactions": total_transactions,
            "income_amount": income_amount,
            "expense_amount": expense_amount,
            "transfer_amount": transfer_amount,
            "categorized_count": categorized_count,
            "categorization_rate": categorized_count / total_transactions if total_transactions > 0 else 0,
            "by_type": by_type
        }
    
    async def get_spending_trends(
        self, months: int = 12, category_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get spending trends over time"""
        
        conditions = [
            Transaction.user_id == self.user.id,
            Transaction.main_category == 'EXPENSES'
        ]
        
        if category_id:
            conditions.append(Transaction.category_id == uuid.UUID(category_id))
        
        query = select(
            Transaction.year_month,
            func.sum(func.abs(Transaction.amount)).label('total_amount'),
            func.count(Transaction.id).label('transaction_count')
        ).where(and_(*conditions)).group_by(
            Transaction.year_month
        ).order_by(Transaction.year_month.desc()).limit(months)
        
        result = await self.db.execute(query)
        trends = []
        
        for row in result:
            if row.year_month:
                trends.append({
                    "month": row.year_month,
                    "amount": float(row.total_amount),
                    "transaction_count": row.transaction_count
                })
        
        trends.reverse()
        return trends


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
            
            category_query = select(Category).where(
                and_(
                    Category.id == uuid.UUID(category_id),
                    Category.user_id == self.user.id
                )
            )
            category_result = await self.db.execute(category_query)
            category = category_result.scalar_one_or_none()
            
            if not category:
                return {"success": False, "message": "Category not found"}
            
            transaction.category_id = uuid.UUID(category_id)
            transaction.source_category = "user"
            transaction.confidence_score = confidence
            transaction.review_needed = False
            transaction.updated_at = datetime.utcnow()
            
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