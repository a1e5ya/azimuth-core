"""
Transfer Pair Detection Service - Automatic Transfer Identification

Automatically detects and links transfer pairs across different accounts.

Detection Criteria:
1. Same absolute amount (±0 tolerance)
2. Opposite signs (one positive, one negative)
3. Within 3 days of each other
4. Different accounts (if known)
5. Bonus: Transfer keywords in description

Keywords (Multi-language):
- English: transfer, internal transfer, own account, between accounts
- Finnish: siirto, tilisiirto
- Swedish: överföring, kontoöverföring

Process:
1. Get unpaired transactions (last 90 days)
2. Group by absolute amount for efficient matching
3. Find pairs within each amount group
4. Link pairs with unique transfer_pair_id
5. Categorize as TRANSFERS with high confidence

Database: SQLAlchemy async with Transaction, Category models
Performance: Optimized with amount-based grouping (O(n) instead of O(n²))
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import uuid

from ..models.database import Transaction, User, Category


# ============================================================================
# TRANSFER DETECTOR CLASS
# ============================================================================

class TransferDetector:
    """
    Detect and link transfer pairs across accounts
    
    Identifies transactions that represent the same money movement
    between two accounts:
    - Account A: -€100 (outgoing)
    - Account B: +€100 (incoming)
    
    Automatically categorizes as TRANSFERS with 95% confidence.
    """
    
    def __init__(self, db: AsyncSession, user: User):
        """
        Initialize transfer detector
        
        @param db: Database session for async operations
        @param user: Current user (for filtering transactions)
        """
        self.db = db
        self.user = user
        
        # Transfer keywords in multiple languages
        # Used as bonus signal for pair detection
        self.transfer_keywords = [
            'transfer', 'siirto', 'överföring', 'tilisiirto',
            'kontoöverföring', 'internal transfer', 'own account',
            'from account', 'to account', 'between accounts'
        ]
        
        # Maximum days between paired transfers
        # Some transfers take 1-2 days to process
        self.max_days_diff = 3
    
    async def detect_pairs(self) -> int:
        """
        Main entry point: detect all transfer pairs for user
        
        Process:
        1. Get unpaired transactions (last 90 days only for performance)
        2. Group by absolute amount (e.g., €100 and -€100 in same group)
        3. Find pairs within each amount group
        4. Link pairs with unique transfer_pair_id
        5. Update category to TRANSFERS
        6. Commit all changes
        
        Performance optimization:
        - Groups transactions by amount before comparing
        - Only checks within same-amount groups (huge speedup)
        - Marks used transactions to avoid duplicate pairing
        
        @returns {int} Number of pairs found and linked
        """
        print("🔍 Starting transfer pair detection...")
        
        # STEP 1: Get unpaired transaction candidates
        candidates = await self._get_unpaired_candidates()
        
        if len(candidates) < 2:
            print("⚠️ Not enough transactions to detect pairs")
            return 0
        
        print(f"📊 Analyzing {len(candidates)} unpaired transactions")
        
        # STEP 2: Group by absolute amount for efficient matching
        by_amount = self._group_by_amount(candidates)
        
        # STEP 3: Find and link pairs
        pairs_found = 0
        for amount, transactions in by_amount.items():
            if len(transactions) < 2:
                continue  # Need at least 2 transactions to make a pair
            
            # Find all valid pairs in this amount group
            pairs = self._find_pairs_in_group(transactions)
            
            # Link each pair
            for tx1, tx2 in pairs:
                await self._link_pair(tx1, tx2)
                pairs_found += 1
        
        # STEP 4: Commit all changes
        await self.db.commit()
        
        print(f"✅ Linked {pairs_found} transfer pairs")
        return pairs_found
    
    async def _get_unpaired_candidates(self) -> List[Transaction]:
        """
        Get transactions that might be transfers but aren't paired yet
        
        Filters:
        - Belongs to current user
        - Posted in last 90 days (performance optimization)
        - Not already paired (transfer_pair_id is NULL)
        - Has non-zero amount
        
        Sorted by posted_at descending (newest first).
        
        @returns {List[Transaction]} Unpaired transactions
        """
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
        """
        Group transactions by absolute amount
        
        Groups €500 and -€500 together since they could be transfer pairs.
        Uses absolute value as dictionary key.
        
        Example:
        ```python
        {
            100.0: [tx1(+100), tx2(-100), tx3(+100)],
            250.5: [tx4(-250.5), tx5(+250.5)]
        }
        ```
        
        This grouping allows O(n) pair detection instead of O(n²).
        
        @param transactions: All candidate transactions
        @returns {Dict} Transactions grouped by absolute amount
        """
        by_amount = defaultdict(list)
        
        for tx in transactions:
            # Use absolute amount as key (€500 = €-500)
            key = abs(float(tx.amount))
            by_amount[key].append(tx)
        
        return by_amount
    
    def _find_pairs_in_group(self, transactions: List[Transaction]) -> List[Tuple[Transaction, Transaction]]:
        """
        Find transfer pairs within a group of same-amount transactions
        
        Compares each transaction with all others in the group.
        Uses greedy matching: first valid pair found is accepted.
        
        Process:
        1. Iterate through transactions
        2. For each transaction, check all following transactions
        3. If valid pair found, mark both as used
        4. Continue with next unused transaction
        
        This prevents one transaction from being paired twice.
        
        @param transactions: All transactions with same absolute amount
        @returns {List[Tuple]} List of (tx1, tx2) pairs found
        """
        pairs = []
        used_indices = set()
        
        # Compare each transaction with all following transactions
        for i, tx1 in enumerate(transactions):
            if i in used_indices:
                continue  # This transaction already paired
            
            for j, tx2 in enumerate(transactions[i+1:], start=i+1):
                if j in used_indices:
                    continue  # This transaction already paired
                
                # Check if these two form a valid transfer pair
                if self._is_transfer_pair(tx1, tx2):
                    pairs.append((tx1, tx2))
                    used_indices.add(i)
                    used_indices.add(j)
                    break  # tx1 is paired, move to next
        
        return pairs
    
    def _is_transfer_pair(self, tx1: Transaction, tx2: Transaction) -> bool:
        """
        Check if two transactions form a valid transfer pair
        
        Validation criteria (ALL must be true):
        1. Same absolute amount (already grouped, but double-check)
        2. Opposite signs (one positive, one negative)
        3. Within max_days_diff days of each other (default: 3 days)
        4. Different accounts, if both accounts are known
        
        Bonus signals (strengthen confidence but not required):
        5. Transfer keywords in merchant or memo
        6. Same-day transactions
        
        Decision tree:
        - If has transfer keywords → definitely a pair
        - If different accounts + all criteria → definitely a pair
        - If same day + exact amount → likely a pair
        - If within 1 day + different accounts → likely a pair
        - Otherwise → need more evidence
        
        @param tx1: First transaction
        @param tx2: Second transaction
        @returns {bool} True if these form a valid transfer pair
        """
        # CRITERION 1: Amount must match (already grouped, but double-check)
        if abs(float(tx1.amount)) != abs(float(tx2.amount)):
            return False
        
        # CRITERION 2: Must have opposite signs
        if (float(tx1.amount) > 0) == (float(tx2.amount) > 0):
            return False  # Both positive or both negative
        
        # CRITERION 3: Date within max_days_diff
        date_diff = abs((tx1.posted_at - tx2.posted_at).days)
        if date_diff > self.max_days_diff:
            return False  # Too far apart in time
        
        # CRITERION 4: Different accounts (if we know them)
        if tx1.account_id and tx2.account_id:
            if tx1.account_id == tx2.account_id:
                return False  # Can't transfer to same account
        
        # BONUS SIGNAL 5: Transfer keywords boost confidence
        has_transfer_keyword = (
            self._has_transfer_keyword(tx1) or 
            self._has_transfer_keyword(tx2)
        )
        
        # Decision tree
        if has_transfer_keyword:
            # Explicit transfer keywords → definitely a pair
            return True
        
        if tx1.account_id and tx2.account_id and tx1.account_id != tx2.account_id:
            # Different accounts and all other criteria met → likely a transfer
            return True
        
        # BONUS SIGNAL 6: Same-day transactions
        if date_diff == 0:
            # Same day and exact amount match → also likely transfer
            return True
        
        # Need more evidence (within 1 day and different accounts)
        return date_diff <= 1 and tx1.account_id != tx2.account_id
    
    def _has_transfer_keyword(self, tx: Transaction) -> bool:
        """
        Check if transaction description contains transfer keywords
        
        Searches in both merchant and memo fields (case-insensitive).
        
        Keywords checked:
        - English: transfer, internal transfer, own account, between accounts
        - Finnish: siirto, tilisiirto
        - Swedish: överföring, kontoöverföring
        
        @param tx: Transaction to check
        @returns {bool} True if transfer keyword found
        """
        text = f"{tx.merchant or ''} {tx.memo or ''}".lower()
        return any(keyword in text for keyword in self.transfer_keywords)
    
    async def _link_pair(self, tx1: Transaction, tx2: Transaction):
        """
        Link two transactions as a transfer pair
        
        Actions performed:
        1. Generate unique pair_id (UUID)
        2. Assign pair_id to both transactions
        3. Get or create TRANSFERS category
        4. Categorize both transactions as TRANSFERS
        5. Set confidence to 95% (very high)
        6. Mark as not needing review
        7. Update CSV fields (main_category = 'TRANSFERS')
        
        Note: Changes are not committed here - caller commits all pairs at once.
        
        @param tx1: First transaction in pair
        @param tx2: Second transaction in pair
        """
        # STEP 1: Generate unique pair ID
        pair_id = str(uuid.uuid4())
        
        # STEP 2: Assign pair_id to both transactions
        tx1.transfer_pair_id = pair_id
        tx2.transfer_pair_id = pair_id
        
        # STEP 3: Get or create transfer category
        transfer_category = await self._get_transfer_category()
        
        if transfer_category:
            # STEP 4-7: Update categorization
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
        """
        Get the transfer category (top-level TRANSFERS)
        
        Searches for:
        - Category type = 'transfers'
        - No parent (top-level category)
        - Belongs to current user
        
        @returns {Category|None} TRANSFERS category or None if not found
        """
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
        
        Use case: User decides these aren't actually a transfer pair.
        
        Process:
        1. Find transaction by ID
        2. Get its transfer_pair_id
        3. Find all transactions with same pair_id (should be 2)
        4. Remove pair_id from both
        5. Change source from 'transfer_detected' to 'user'
        6. Keep category_id (user can recategorize separately)
        
        @param transaction_id: UUID of one transaction in the pair
        @returns {bool} True if pair was unlinked, False if not found
        """
        # STEP 1: Find transaction
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
        
        # STEP 2: Find and unlink both transactions in the pair
        update_query = select(Transaction).where(
            Transaction.transfer_pair_id == pair_id
        )
        
        result = await self.db.execute(update_query)
        paired_transactions = result.scalars().all()
        
        # STEP 3: Remove pairing from all transactions
        for paired_tx in paired_transactions:
            paired_tx.transfer_pair_id = None
            # Keep category_id but change source
            if paired_tx.source_category == 'transfer_detected':
                paired_tx.source_category = 'user'
        
        await self.db.commit()
        print(f"🔓 Unlinked transfer pair: {pair_id}")
        
        return True


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

async def get_transfer_detector(db: AsyncSession, user: User) -> TransferDetector:
    """
    Dependency injection for TransferDetector
    
    Used in FastAPI route handlers to inject detector with:
    - Database session
    - Current authenticated user
    
    Example:
    ```python
    @router.post("/detect-transfers")
    async def detect_transfers(
        detector: TransferDetector = Depends(get_transfer_detector)
    ):
        pairs_found = await detector.detect_pairs()
        return {"pairs_found": pairs_found}
    ```
    
    @param db: Injected database session
    @param user: Injected current user
    @returns {TransferDetector} Initialized detector instance
    """
    return TransferDetector(db, user)