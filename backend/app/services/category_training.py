"""
Category Training Service - Extract Merchants and Keywords

Analyzes categorized transactions to extract training patterns for auto-categorization.

Extracts two types of training data:
1. **Top Merchants** (by frequency)
   - Aggregates merchants from categorized transactions
   - Stores top 10 merchants per category
   - Used for fast merchant-based pattern matching
   
2. **Keywords** (using LLM analysis)
   - Analyzes merchant names and memos with Ollama
   - Extracts distinctive keywords and patterns
   - Stores up to 8 keywords per category
   - Used for keyword-based pattern matching

Training Data Usage:
- Auto-categorization of new transactions
- Pattern recognition in LLM categorizer
- Improving category suggestions
- Building merchant knowledge base

Database: SQLAlchemy async with Category, Transaction models
AI Service: Ollama (llama3.2:3b) for keyword extraction
Training Sources: csv_mapped and user-categorized transactions only
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import List, Dict
from datetime import datetime
import json
import re

from ..models.database import Category, Transaction, User
from ..services.ollama_client import llm_client


# ============================================================================
# CATEGORY TRAINING SERVICE
# ============================================================================

class CategoryTrainingService:
    """
    Extract and save training data for categories
    
    Analyzes user-categorized transactions to learn patterns:
    - Which merchants belong to which categories
    - What keywords appear in transaction descriptions
    
    Training Pipeline:
    1. Get all subcategories (leaf nodes in hierarchy)
    2. For each subcategory, find approved transactions
    3. Aggregate merchants by frequency
    4. Extract keywords using LLM analysis
    5. Save to category.training_merchants and category.training_keywords
    6. Update category.last_training_update timestamp
    
    Only trains on high-confidence sources to avoid bad patterns:
    - csv_mapped: Categories from CSV import
    - user: Manual user categorization
    - Excludes: AI-categorized (to avoid reinforcing mistakes)
    """
    
    def __init__(self, db: AsyncSession, user: User):
        """
        Initialize category training service
        
        @param db: Database session for async queries
        @param user: Current user (for filtering transactions)
        """
        self.db = db
        self.user = user
        self.progress_callback = None  # Optional callback for progress updates
    
    async def train_all_categories(self, progress_callback=None):
        """
        Train all categories that have transactions
        
        Process:
        1. Get all active categories for user
        2. Identify subcategories (level 3 in hierarchy)
        3. Train each subcategory individually
        4. Call progress callback if provided
        5. Commit all training updates
        
        Why only subcategories?
        - Subcategories are leaf nodes (most specific)
        - They have the most focused transaction patterns
        - Training higher levels would dilute patterns
        
        Progress Tracking:
        - Optional callback function for UI updates
        - Called after each category is trained
        - Signature: async callback(current: int, total: int, category_name: str)
        
        @param progress_callback: Optional async function for progress updates
        @returns {int} Number of categories successfully trained
        
        Example usage:
        ```python
        async def show_progress(current, total, name):
            print(f"Training {current}/{total}: {name}")
        
        trained = await trainer.train_all_categories(show_progress)
        ```
        """
        self.progress_callback = progress_callback
        
        print("🎯 Starting category training...")
        
        # STEP 1: Get all active categories for user
        query = select(Category).where(
            and_(
                Category.user_id == self.user.id,
                Category.active == True
            )
        )
        result = await self.db.execute(query)
        categories = result.scalars().all()
        
        # STEP 2: Find subcategories (level 3: has parent, and parent also has parent)
        subcategories = [
            c for c in categories 
            if c.parent_id and any(p.id == c.parent_id and p.parent_id for p in categories)
        ]
        
        total = len(subcategories)
        trained_count = 0
        
        # STEP 3: Train each subcategory
        for idx, category in enumerate(subcategories, 1):
            success = await self.train_category(category.id)
            if success:
                trained_count += 1
            
            # STEP 4: Call progress callback if provided
            if self.progress_callback:
                await self.progress_callback(idx, total, category.name)
        
        # STEP 5: Commit all training updates
        await self.db.commit()
        
        print(f"✅ Trained {trained_count}/{total} categories")
        return trained_count
    
    async def train_category(self, category_id: str) -> bool:
        """
        Extract merchants and keywords for one category
        
        Process:
        1. Get approved transactions for this category (csv_mapped or user)
        2. Aggregate merchants by frequency
        3. Extract top 10 merchants by transaction count
        4. Extract keywords from merchant names and memos using LLM
        5. Save training_merchants and training_keywords to category
        6. Update last_training_update timestamp
        
        Transaction Sources (Only High-Confidence):
        - csv_mapped: Categories from CSV import
        - user: Manual user categorization
        - Excludes: AI-categorized to avoid bad patterns
        
        Data Extraction:
        - Groups by (merchant, memo) to count frequencies
        - Limits to 50 transactions for performance
        - Takes top 10 merchants by count
        - Extracts up to 8 keywords via LLM
        
        @param category_id: Category UUID to train
        @returns {bool} True if training succeeded, False if no data
        """
        # STEP 1: Get training transactions (group by merchant to count frequencies)
        query = select(
            Transaction.merchant,
            Transaction.memo,
            func.count(Transaction.id).label('count')
        ).where(
            and_(
                Transaction.user_id == self.user.id,
                Transaction.category_id == category_id,
                or_(
                    Transaction.source_category == 'csv_mapped',
                    Transaction.source_category == 'user'
                )
            )
        ).group_by(Transaction.merchant, Transaction.memo).limit(50)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        if not rows:
            return False  # No approved transactions for this category
        
        # STEP 2: Extract merchants and aggregate by frequency
        merchants = {}  # merchant_name -> total_count
        all_text = []   # All merchant/memo text for keyword extraction
        
        for row in rows:
            if row.merchant:
                clean = row.merchant.strip()
                merchants[clean] = merchants.get(clean, 0) + row.count
                all_text.append(clean)
            if row.memo:
                all_text.append(row.memo.strip())
        
        # STEP 3: Get top 10 merchants by frequency
        top_merchants = sorted(merchants.items(), key=lambda x: x[1], reverse=True)[:10]
        merchant_names = [m[0] for m in top_merchants]
        
        # STEP 4: Extract keywords using LLM (analyze up to 30 texts)
        keywords = await self._extract_keywords(all_text[:30])
        
        # STEP 5: Save to category
        category_query = select(Category).where(Category.id == category_id)
        cat_result = await self.db.execute(category_query)
        category = cat_result.scalar_one_or_none()
        
        if category:
            category.training_merchants = merchant_names
            category.training_keywords = keywords
            category.last_training_update = datetime.utcnow()
            
            print(f"   📝 {category.name}: {len(merchant_names)} merchants, {len(keywords)} keywords")
            return True
        
        return False
    
    async def _extract_keywords(self, texts: List[str]) -> List[str]:
        """
        Use LLM to extract keywords from transaction texts
        
        Sends merchant names and memos to Ollama to extract:
        - Brand names (e.g., "k-market", "shell", "spotify")
        - Place types (e.g., "restaurant", "grocery", "gas station")
        - Activity keywords (e.g., "parking", "insurance", "streaming")
        
        Filters out generic words and focuses on distinctive patterns
        that help identify transaction categories.
        
        LLM Prompt Strategy:
        - Combines texts with separator (|)
        - Asks for 5-8 short keywords
        - Emphasizes brands, places, activity types
        - Requests lowercase, single words or 2-word phrases
        - Expects JSON array response
        
        Parsing:
        - Extracts JSON array using regex
        - Limits to max 8 keywords
        - Returns empty list if extraction fails
        
        @param texts: List of merchant names and memos
        @returns {List[str]} List of extracted keywords (max 8)
        
        Example:
        ```python
        texts = ["K-Market Lauttasaari", "K-Market Espoo", "K-Supermarket"]
        keywords = await self._extract_keywords(texts)
        # Result: ["k-market", "grocery", "food", "supermarket"]
        ```
        """
        if not texts:
            return []
        
        # Combine texts with separator
        combined_text = " | ".join(texts)
        
        # Build prompt for LLM
        prompt = f"""Analyze these merchants/descriptions. Extract 5-8 SHORT keywords.

Text: {combined_text}

Rules:
- Single words or 2-word phrases
- Focus on brands, places, activity types
- Remove generic words like "purchase"
- Lowercase

JSON array only:
["keyword1", "keyword2"]"""

        try:
            # Query Ollama LLM
            response = await llm_client.query(prompt, max_tokens=100)
            
            if response['status'] == 'success':
                text = response['text'].strip()
                
                # Extract JSON array from response
                # Handles cases where LLM adds explanation before/after JSON
                match = re.search(r'\[.*\]', text, re.DOTALL)
                if match:
                    keywords = json.loads(match.group())[:8]  # Max 8 keywords
                    return keywords
                    
        except Exception as e:
            print(f"   ⚠️ Keyword extraction failed: {e}")
        
        # Return empty list if LLM fails
        return []