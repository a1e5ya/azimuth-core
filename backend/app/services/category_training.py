"""
Category Training Service - Extract merchants/keywords after import
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import List, Dict
from datetime import datetime
import json
import re

from ..models.database import Category, Transaction, User
from ..services.ollama_client import llm_client


class CategoryTrainingService:
    """Extract and save training data for categories"""
    
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
        self.progress_callback = None  # ✅ For progress updates
    
    async def train_all_categories(self, progress_callback=None):
        """Train all categories that have transactions"""
        self.progress_callback = progress_callback
        
        print("🎓 Starting category training...")
        
        # Get all subcategories with transactions
        query = select(Category).where(
            and_(
                Category.user_id == self.user.id,
                Category.active == True
            )
        )
        result = await self.db.execute(query)
        categories = result.scalars().all()
        
        # Find subcategories (level 3)
        subcategories = [
            c for c in categories 
            if c.parent_id and any(p.id == c.parent_id and p.parent_id for p in categories)
        ]
        
        total = len(subcategories)
        trained_count = 0
        
        for idx, category in enumerate(subcategories, 1):
            success = await self.train_category(category.id)
            if success:
                trained_count += 1
            
            # ✅ Progress callback
            if self.progress_callback:
                await self.progress_callback(idx, total, category.name)
        
        await self.db.commit()
        print(f"✅ Trained {trained_count}/{total} categories")
        return trained_count
    
    async def train_category(self, category_id: str) -> bool:
        """Extract merchants and keywords for one category"""
        
        # Get training transactions
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
        
        # Extract merchants
        merchants = {}
        all_text = []
        
        for row in rows:
            if row.merchant:
                clean = row.merchant.strip()
                merchants[clean] = merchants.get(clean, 0) + row.count
                all_text.append(clean)
            if row.memo:
                all_text.append(row.memo.strip())
        
        top_merchants = sorted(merchants.items(), key=lambda x: x[1], reverse=True)[:10]
        merchant_names = [m[0] for m in top_merchants]
        
        # Extract keywords using LLM
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
        """Use LLM to extract keywords from transaction texts"""
        if not texts:
            return []
        
        combined_text = " | ".join(texts)
        
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
            response = await llm_client.query(prompt, max_tokens=100)
            if response['status'] == 'success':
                text = response['text'].strip()
                match = re.search(r'\[.*\]', text, re.DOTALL)
                if match:
                    return json.loads(match.group())[:8]
        except Exception as e:
            print(f"   ⚠️ Keyword extraction failed: {e}")
        
        return []