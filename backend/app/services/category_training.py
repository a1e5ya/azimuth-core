"""
Category Training Service - Extract Merchants and Keywords

Analyzes categorized transactions to extract:
- Top merchants (by frequency)
- Keywords (using LLM analysis)

Used for:
- Auto-categorization of new transactions
- Pattern recognition
- Improving category suggestions

Process:
1. Find all subcategories with transactions
2. For each subcategory, aggregate merchants
3. Extract keywords using Ollama LLM
4. Save to category.training_merchants and category.training_keywords

Database: SQLAlchemy async with Category, Transaction models
AI Service: Ollama (llama3.2:3b) for keyword extraction
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
    
    This data is used for auto-categorizing future transactions
    """
    
    def __init__(self, db: AsyncSession, user: User):
        """
        Initialize category training service
        
        @param db: Database session
        @param user: Current user (for filtering transactions)
        """
        self.db = db
        self.user = user
        self.progress_callback = None  # Optional callback for progress updates
    
    async def train_all_categories(self, progress_callback=None):
        """
        Train all categories that have transactions
        
        Process:
        1. Get all active subcategories (level 3 in hierarchy)
        2. For each subcategory, analyze transactions
        3. Extract top merchants and keywords
        4. Save to category training fields
        5. Commit all changes
        
        Only trains subcategories (leaf nodes) since they have the most specific data
        
        @param progress_callback: Optional async function(current, total, category_name)
        @returns {int} Number of categories successfully trained
        """
        self.progress_callback = progress_callback
        
        print("🎯 Starting category training...")
        
        # Get all active categories for user
        query = select(Category).where(
            and_(
                Category.user_id == self.user.id,
                Category.active == True
            )
        )
        result = await self.db.execute(query)
        categories = result.scalars().all()
        
        # Find subcategories (level 3: has parent_id, and parent also has parent_id)
        subcategories = [
            c for c in categories 
            if c.parent_id and any(p.id == c.parent_id and p.parent_id for p in categories)
        ]
        
        total = len(subcategories)
        trained_count = 0
        
        # Train each subcategory
        for idx, category in enumerate(subcategories, 1):
            success = await self.train_category(category.id)
            if success:
                trained_count += 1
            
            # Call progress callback if provided
            if self.progress_callback:
                await self.progress_callback(idx, total, category.name)
        
        # Commit all training updates
        await self.db.commit()
        
        print(f"✅ Trained {trained_count}/{total} categories")
        return trained_count
    
    async def train_category(self, category_id: str) -> bool:
        """
        Extract merchants and keywords for one category
        
        Process:
        1. Get all transactions for this category (user-categorized or CSV-mapped)
        2. Aggregate merchants by frequency
        3. Extract top 10 merchants
        4. Extract keywords from merchant names and memos using LLM
        5. Save to category.training_merchants and category.training_keywords
        
        Only uses transactions with source_category='csv_mapped' or 'user'
        (excludes AI-categorized to avoid reinforcing mistakes)
        
        @param category_id: Category UUID
        @returns {bool} True if training succeeded, False if no data
        """
        # Get training transactions (group by merchant to count frequencies)
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
            return False
        
        # Extract merchants and aggregate by frequency
        merchants = {}
        all_text = []
        
        for row in rows:
            if row.merchant:
                clean = row.merchant.strip()
                merchants[clean] = merchants.get(clean, 0) + row.count
                all_text.append(clean)
            if row.memo:
                all_text.append(row.memo.strip())
        
        # Get top 10 merchants by frequency
        top_merchants = sorted(merchants.items(), key=lambda x: x[1], reverse=True)[:10]
        merchant_names = [m[0] for m in top_merchants]
        
        # Extract keywords using LLM (analyze up to 30 texts)
        keywords = await self._extract_keywords(all_text[:30])
        
        # Save to category
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
        - Brand names
        - Place types (restaurant, grocery, etc.)
        - Activity keywords
        
        Filters out generic words and focuses on distinctive patterns
        
        @param texts: List of merchant names and memos
        @returns {List[str]} List of extracted keywords (max 8)
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
- Remove generic words
- Lowercase

JSON array only:
["keyword1", "keyword2"]"""

        try:
            # Query Ollama LLM
            response = await llm_client.query(prompt, max_tokens=100)
            
            if response['status'] == 'success':
                text = response['text'].strip()
                
                # Extract JSON array from response
                match = re.search(r'\[.*\]', text, re.DOTALL)
                if match:
                    keywords = json.loads(match.group())[:8]  # Max 8 keywords
                    return keywords
                    
        except Exception as e:
            print(f"   ⚠️ Keyword extraction failed: {e}")
        
        # Return empty list if LLM fails
        return []