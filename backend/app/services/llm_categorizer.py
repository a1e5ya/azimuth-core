"""
LLM Categorization Service - Uses Ollama to categorize transactions
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload  # ADD THIS
from typing import Dict, List, Optional
import json
import re

from ..models.database import Category, User, Transaction
from ..services.ollama_client import llm_client


class LLMCategorizationService:
    """Uses LLM with training data to categorize transactions"""
    
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
        self.user_categories_cache = None
    
    async def _build_training_data(self) -> Dict:
        """Build training data from categorized transactions"""
        
        query = select(Transaction).options(
            selectinload(Transaction.assigned_category)
        ).where(
            and_(
                Transaction.user_id == self.user.id,
                Transaction.category_id.isnot(None),
                or_(
                    Transaction.source_category == 'csv_mapped',
                    Transaction.source_category == 'user'
                )
            )
        ).limit(1000)
        
        result = await self.db.execute(query)
        transactions = result.scalars().all()
        
        merchant_mappings = {}
        csv_mappings = {}
        
        for tx in transactions:
            if tx.merchant and tx.assigned_category:
                merchant_key = tx.merchant.lower().strip()
                merchant_mappings[merchant_key] = f"{tx.assigned_category.category_type}>{tx.assigned_category.name}"
            
            if tx.main_category and tx.category and tx.assigned_category:
                csv_key = f"{tx.main_category}|{tx.category}"
                if tx.subcategory:
                    csv_key += f"|{tx.subcategory}"
                csv_mappings[csv_key] = f"{tx.assigned_category.category_type}>{tx.assigned_category.name}"
        
        return {
            'total_approved': len(transactions),
            'merchant_mappings': merchant_mappings,
            'csv_mappings': csv_mappings
        }
    
    async def categorize_transaction(
        self,
        merchant: str,
        memo: str,
        amount: float,
        csv_main: str = None,
        category: str = None,
        subcategory: str = None
    ) -> Dict[str, any]:
        """Categorize single transaction using LLM + training data"""
        
        print(f"🤖 LLM categorizing: {merchant or memo} (€{amount})")
        
        training_data = await self._build_training_data()
        
        # Quick check: exact merchant match
        merchant_key = (merchant or '').lower().strip()
        if merchant_key in training_data['merchant_mappings']:
            category_path = training_data['merchant_mappings'][merchant_key]
            category = await self._find_category_by_path(category_path)
            if category:
                return {
                    'category_id': category.id,
                    'confidence': 0.95,
                    'method': 'merchant_exact',
                    'matched': merchant_key
                }
        
        # Use LLM for complex cases
        llm_result = await self._query_llm_for_category(
            merchant, memo, amount, csv_main, category, subcategory, training_data
        )
        
        return llm_result
    
    async def _query_llm_for_category(
        self,
        merchant: str,
        memo: str,
        amount: float,
        csv_main: str,
        category: str,
        subcategory: str,
        training_data: Dict
    ) -> Dict:
        """Query LLM with transaction details and training context"""
        
        user_categories = await self._get_user_categories()
        categories_text = self._format_categories_for_llm(user_categories)
        training_examples = self._format_training_examples(training_data, limit=30)
        
        prompt = f"""Categorize this transaction based on learned patterns.

CATEGORIES:
{categories_text}

PATTERNS ({training_data['total_approved']} transactions):
{training_examples}

TRANSACTION:
- Merchant: {merchant or 'Unknown'}
- Description: {memo or 'None'}
- Amount: €{abs(amount):.2f}

Respond ONLY with JSON:
{{"category": "type>name", "confidence": 0.85, "reason": "brief reason"}}

Response:"""

        try:
            llm_response = await llm_client.query(prompt, max_tokens=100)
            
            if llm_response['status'] == 'success':
                result = self._parse_llm_response(llm_response['text'])
                
                if result:
                    category = await self._find_category_by_path(result['category'])
                    if category:
                        return {
                            'category_id': category.id,
                            'confidence': result['confidence'],
                            'method': 'llm',
                            'reason': result.get('reason', 'LLM suggestion')
                        }
        
        except Exception as e:
            print(f"LLM categorization failed: {e}")
        
        return {
            'category_id': None,
            'confidence': 0.0,
            'method': 'none',
            'reason': 'No match found'
        }
    
    def _parse_llm_response(self, text: str) -> Optional[Dict]:
        """Parse LLM JSON response"""
        try:
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return {
                    'category': data.get('category', ''),
                    'confidence': float(data.get('confidence', 0.5)),
                    'reason': data.get('reason', '')
                }
        except:
            pass
        return None
    
    async def _get_user_categories(self) -> List[Category]:
        """Get all active user categories with caching"""
        if self.user_categories_cache is None:
            query = select(Category).where(
                and_(
                    Category.user_id == self.user.id,
                    Category.active == True
                )
            )
            result = await self.db.execute(query)
            self.user_categories_cache = result.scalars().all()
        
        return self.user_categories_cache
    
    def _format_categories_for_llm(self, categories: List[Category]) -> str:
        """Format categories as tree for LLM"""
        lines = []
        for cat in categories[:20]:  # Limit for token efficiency
            lines.append(f"- {cat.category_type}>{cat.name}")
        return "\n".join(lines)
    
    def _format_training_examples(self, training_data: Dict, limit: int = 30) -> str:
        """Format top training patterns for LLM"""
        lines = []
        
        lines.append("Top Merchants:")
        for merchant, category in list(training_data['merchant_mappings'].items())[:10]:
            lines.append(f"  '{merchant}' → {category}")
        
        return "\n".join(lines)
    
    async def _find_category_by_path(self, path: str) -> Optional[Category]:
        """Find category by path like 'expense>Food'"""
        parts = path.split('>')
        if len(parts) < 2:
            return None
        
        category_type = parts[0].lower()
        category_name = parts[1].strip()
        
        categories = await self._get_user_categories()
        
        for cat in categories:
            if cat.name.lower() == category_name.lower() and cat.category_type == category_type:
                return cat
        
        return None