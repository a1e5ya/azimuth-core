"""
Transfer Pair Detection Service
Automatically detects and links transfer pairs across different accounts
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import uuid

from ..models.database import Transaction, User, Category


class TransferDetector:
    """Detect and link transfer pairs across accounts"""
    
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
        
        # Transfer keywords in multiple languages
        self.transfer_keywords = [
            'transfer', 'siirto', 'överföring', 'tilisiirto',
            'kontoöverföring', 'internal transfer', 'own account',
            'from account', 'to account', 'between accounts'
        ]
        
        # Maximum days between paired transfers
        self.max_days_diff = 3
    
    async def detect_pairs(self) -> int:
        """
        Main entry point: detect all transfer pairs for user
        Returns number of pairs found
        """
        print("🔍 Starting transfer pair detection...")
        
        # Get unpaired transactions (last 90 days)
        candidates = await self._get_unpaired_candidates()
        
        if len(candidates) < 2:
            print("⚠️ Not enough transactions to detect pairs")
            return 0
        
        print(f"📊 Analyzing {len(candidates)} unpaired transactions")
        
        # Group by absolute amount for efficient matching
        by_amount = self._group_by_amount(candidates)
        
        # Find and link pairs
        pairs_found = 0
        for amount, transactions in by_amount.items():
            if len(transactions) < 2:
                continue
            
            pairs = self._find_pairs_in_group(transactions)
            
            for tx1, tx2 in pairs:
                await self._link_pair(tx1, tx2)
                pairs_found += 1
        
        await self.db.commit()
        
        print(f"✅ Linked {pairs_found} transfer pairs")
        return pairs_found
    
    async def _get_unpaired_candidates(self) -> List[Transaction]:
        """Get transactions that might be transfers but aren't paired yet"""
        
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)
        
        query = select(Transaction).where(
            and_(
                Transaction.user_id == self.user.id,
                Transaction.posted_at >= ninety_days_ago,
                Transaction.transfer_pair_id.is_(None),  # Not already paired
                Transaction.amount != 0  # Must have actual amount
            )
        ).order_by(Transaction.posted_at.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    def _group_by_amount(self, transactions: List[Transaction]) -> Dict[float, List[Transaction]]:
        """Group transactions by absolute amount"""
        by_amount = defaultdict(list)
        
        for tx in transactions:
            # Use absolute amount as key (€500 = €-500)
            key = abs(float(tx.amount))
            by_amount[key].append(tx)
        
        return by_amount
    
    def _find_pairs_in_group(self, transactions: List[Transaction]) -> List[Tuple[Transaction, Transaction]]:
        """Find transfer pairs within a group of same-amount transactions"""
        pairs = []
        used_indices = set()
        
        for i, tx1 in enumerate(transactions):
            if i in used_indices:
                continue
            
            for j, tx2 in enumerate(transactions[i+1:], start=i+1):
                if j in used_indices:
                    continue
                
                if self._is_transfer_pair(tx1, tx2):
                    pairs.append((tx1, tx2))
                    used_indices.add(i)
                    used_indices.add(j)
                    break  # tx1 is paired, move to next
        
        return pairs
    
    def _is_transfer_pair(self, tx1: Transaction, tx2: Transaction) -> bool:
        """
        Check if two transactions form a transfer pair
        
        Criteria:
        1. Same absolute amount
        2. Opposite signs (one positive, one negative)
        3. Within N days of each other
        4. Different accounts (if known)
        5. Bonus: transfer keywords in description
        """
        
        # 1. Amount must match (already grouped, but double-check)
        if abs(float(tx1.amount)) != abs(float(tx2.amount)):
            return False
        
        # 2. Must have opposite signs
        if (float(tx1.amount) > 0) == (float(tx2.amount) > 0):
            return False
        
        # 3. Date within max_days_diff
        date_diff = abs((tx1.posted_at - tx2.posted_at).days)
        if date_diff > self.max_days_diff:
            return False
        
        # 4. Different accounts (if we know them)
        if tx1.account_id and tx2.account_id:
            if tx1.account_id == tx2.account_id:
                return False  # Can't transfer to same account
        
        # 5. Transfer keywords boost confidence
        has_transfer_keyword = (
            self._has_transfer_keyword(tx1) or 
            self._has_transfer_keyword(tx2)
        )
        
        # If has explicit transfer keywords, definitely a pair
        if has_transfer_keyword:
            return True
        
        # If different accounts and all other criteria met, likely a transfer
        if tx1.account_id and tx2.account_id and tx1.account_id != tx2.account_id:
            return True
        
        # If same-day and exact amount match, also likely transfer
        if date_diff == 0:
            return True
        
        # Otherwise, need more evidence (within 1 day and different accounts)
        return date_diff <= 1 and tx1.account_id != tx2.account_id
    
    def _has_transfer_keyword(self, tx: Transaction) -> bool:
        """Check if transaction description contains transfer keywords"""
        text = f"{tx.merchant or ''} {tx.memo or ''}".lower()
        return any(keyword in text for keyword in self.transfer_keywords)
    
    async def _link_pair(self, tx1: Transaction, tx2: Transaction):
        """Link two transactions as a transfer pair"""
        
        # Generate unique pair ID
        pair_id = str(uuid.uuid4())
        
        # Update both transactions
        tx1.transfer_pair_id = pair_id
        tx2.transfer_pair_id = pair_id
        
        # Get or create transfer category
        transfer_category = await self._get_transfer_category()
        
        if transfer_category:
            tx1.category_id = transfer_category.id
            tx2.category_id = transfer_category.id
            tx1.source_category = 'transfer_detected'
            tx2.source_category = 'transfer_detected'
            tx1.confidence_score = 0.95
            tx2.confidence_score = 0.95
            tx1.review_needed = False
            tx2.review_needed = False
            
            # Update CSV fields to reflect transfer category
            tx1.main_category = 'TRANSFERS'
            tx2.main_category = 'TRANSFERS'
        
        print(f"🔗 Linked pair: {tx1.posted_at.date()} | {tx1.amount} ↔ {tx2.amount}")
    
    async def _get_transfer_category(self) -> Optional[Category]:
        """Get the transfer category (top-level TRANSFERS)"""
        from sqlalchemy import select
        
        query = select(Category).where(
            and_(
                Category.user_id == self.user.id,
                Category.category_type == 'transfers',
                Category.parent_id.is_(None)
            )
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def unlink_pair(self, transaction_id: str) -> bool:
        """
        Unlink a transfer pair (if user manually recategorizes)
        """
        query = select(Transaction).where(
            and_(
                Transaction.id == transaction_id,
                Transaction.user_id == self.user.id,
                Transaction.transfer_pair_id.isnot(None)
            )
        )
        
        result = await self.db.execute(query)
        tx = result.scalar_one_or_none()
        
        if not tx:
            return False
        
        pair_id = tx.transfer_pair_id
        
        # Find and unlink both transactions in the pair
        update_query = select(Transaction).where(
            Transaction.transfer_pair_id == pair_id
        )
        
        result = await self.db.execute(update_query)
        paired_transactions = result.scalars().all()
        
        for paired_tx in paired_transactions:
            paired_tx.transfer_pair_id = None
            # Keep category_id but change source
            if paired_tx.source_category == 'transfer_detected':
                paired_tx.source_category = 'user'
        
        await self.db.commit()
        print(f"🔓 Unlinked transfer pair: {pair_id}")
        
        return True


async def get_transfer_detector(db: AsyncSession, user: User) -> TransferDetector:
    """Get transfer detector instance"""
    return TransferDetector(db, user)