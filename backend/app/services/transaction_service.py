"""
Transaction service - Business logic for transaction operations
FIXED FOR LOCAL AUTH - NO FIREBASE DEPENDENCIES
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_, func, or_
from sqlalchemy.orm import selectinload
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

from ..models.database import Transaction, Category, User, AuditLog, ImportBatch, get_db
from ..auth.local_auth import get_current_user
from fastapi import Depends, HTTPException

class TransactionService:
    """Service for transaction operations"""
    
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
    
    async def categorize_transaction(
        self, 
        transaction_id: str, 
        category_id: str,
        confidence: float = 1.0,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Categorize a single transaction with proper error handling"""
        try:
            # Get transaction with user verification
            transaction_query = select(Transaction).where(
                and_(
                    Transaction.id == uuid.UUID(transaction_id),
                    Transaction.user_id == self.user.id
                )
            )
            result = await self.db.execute(transaction_query)
            transaction = result.scalar_one_or_none()
            
            if not transaction:
                return {
                    "success": False,
                    "message": "Transaction not found"
                }
            
            # Verify category belongs to user
            category_query = select(Category).where(
                and_(
                    Category.id == uuid.UUID(category_id),
                    Category.user_id == self.user.id
                )
            )
            category_result = await self.db.execute(category_query)
            category = category_result.scalar_one_or_none()
            
            if not category:
                return {
                    "success": False,
                    "message": "Category not found or access denied"
                }
            
            # Store old values for audit
            old_values = {
                "category_id": str(transaction.category_id) if transaction.category_id else None,
                "confidence_score": float(transaction.confidence_score) if transaction.confidence_score else None,
                "source_category": transaction.source_category,
                "notes": transaction.notes
            }
            
            # Update transaction
            transaction.category_id = uuid.UUID(category_id)
            transaction.source_category = "user"
            transaction.confidence_score = confidence
            transaction.review_needed = False
            transaction.updated_at = datetime.utcnow()
            
            if notes:
                transaction.notes = notes
            
            await self.db.commit()
            
            # Log the categorization - FIXED: No firebase_uid
            audit_entry = AuditLog(
                user_id=self.user.id,
                entity="transaction",
                entity_id=str(transaction.id),
                action="categorize",
                before_json=old_values,
                after_json={
                    "category_id": str(transaction.category_id),
                    "category_name": category.name,
                    "confidence_score": float(transaction.confidence_score),
                    "source_category": transaction.source_category,
                    "notes": transaction.notes
                }
            )
            self.db.add(audit_entry)
            await self.db.commit()
            
            print(f"✅ Transaction categorized: {transaction_id} -> {category.name}")
            
            return {
                "success": True,
                "message": f"Transaction categorized as {category.name}",
                "category": {
                    "id": str(category.id),
                    "name": category.name,
                    "icon": category.icon
                }
            }
            
        except Exception as e:
            print(f"❌ Failed to categorize transaction {transaction_id}: {e}")
            await self.db.rollback()
            return {
                "success": False,
                "message": f"Failed to categorize transaction: {str(e)}"
            }
    
    async def bulk_categorize_transactions(
        self,
        transaction_ids: List[str],
        category_id: str,
        confidence: float = 1.0
    ) -> Dict[str, Any]:
        """Bulk categorize multiple transactions"""
        try:
            if not transaction_ids:
                return {
                    "success": False,
                    "message": "No transaction IDs provided",
                    "updated_count": 0
                }
            
            # Verify category exists and belongs to user
            category_query = select(Category).where(
                and_(
                    Category.id == uuid.UUID(category_id),
                    Category.user_id == self.user.id
                )
            )
            category_result = await self.db.execute(category_query)
            category = category_result.scalar_one_or_none()
            
            if not category:
                return {
                    "success": False,
                    "message": "Category not found or access denied",
                    "updated_count": 0
                }
            
            # Get transactions
            transaction_uuids = [uuid.UUID(tid) for tid in transaction_ids]
            transactions_query = select(Transaction).where(
                and_(
                    Transaction.id.in_(transaction_uuids),
                    Transaction.user_id == self.user.id
                )
            )
            result = await self.db.execute(transactions_query)
            transactions = result.scalars().all()
            
            if len(transactions) != len(transaction_ids):
                return {
                    "success": False,
                    "message": "Some transactions not found or access denied",
                    "updated_count": 0
                }
            
            # Update all transactions
            updated_count = 0
            for transaction in transactions:
                transaction.category_id = uuid.UUID(category_id)
                transaction.source_category = "user"
                transaction.confidence_score = confidence
                transaction.review_needed = False
                transaction.updated_at = datetime.utcnow()
                updated_count += 1
            
            await self.db.commit()
            
            # Log bulk operation - FIXED: No firebase_uid
            audit_entry = AuditLog(
                user_id=self.user.id,
                entity="transaction",
                action="bulk_categorize",
                details={
                    "category_id": category_id,
                    "category_name": category.name,
                    "transaction_count": updated_count,
                    "transaction_ids": transaction_ids
                }
            )
            self.db.add(audit_entry)
            await self.db.commit()
            
            print(f"✅ Bulk categorized {updated_count} transactions as {category.name}")
            
            return {
                "success": True,
                "message": f"Successfully categorized {updated_count} transactions as {category.name}",
                "updated_count": updated_count
            }
            
        except Exception as e:
            print(f"❌ Bulk categorization failed: {e}")
            await self.db.rollback()
            return {
                "success": False,
                "message": f"Bulk categorization failed: {str(e)}",
                "updated_count": 0
            }
    
    async def delete_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """Delete a single transaction"""
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
                return {
                    "success": False,
                    "message": "Transaction not found",
                    "deleted_count": 0
                }
            
            # Store transaction details for audit log
            transaction_details = {
                "id": str(transaction.id),
                "posted_at": transaction.posted_at.isoformat(),
                "amount": str(transaction.amount),
                "merchant": transaction.merchant
            }
            
            # Delete the transaction
            delete_query = delete(Transaction).where(
                and_(
                    Transaction.id == uuid.UUID(transaction_id),
                    Transaction.user_id == self.user.id
                )
            )
            await self.db.execute(delete_query)
            await self.db.commit()
            
            # Log the deletion - FIXED: No firebase_uid
            audit_entry = AuditLog(
                user_id=self.user.id,
                entity="transaction",
                entity_id=transaction_id,
                action="delete",
                before_json=transaction_details,
                after_json=None,
                details={"reason": "user_requested"}
            )
            self.db.add(audit_entry)
            await self.db.commit()
            
            return {
                "success": True,
                "message": "Transaction deleted successfully",
                "deleted_count": 1
            }
            
        except Exception as e:
            print(f"❌ Failed to delete transaction: {e}")
            await self.db.rollback()
            return {
                "success": False,
                "message": f"Failed to delete transaction: {str(e)}",
                "deleted_count": 0
            }

# Helper function - FIXED: Use get_current_user from local_auth
def get_transaction_service(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TransactionService:
    """Get transaction service instance"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return TransactionService(db, current_user)