"""
LLM Categorization Service - Uses Ollama to categorize transactions
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Optional, Tuple
import json
import re

from ..models.database import Category, User
from ..services.ollama_client import llm_client
from ..services.category_training import CategoryTrainingService


class LLMCategorizationService:
    """Uses LLM with training data to categorize transactions"""
    
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
        self.training_service = CategoryTrainingService(db, user)
        self.user_categories_cache = None
    
    async def categorize_transaction(
        self,
        merchant: str,
        memo: str,
        amount: float,
        csv_main: str = None,
        csv_category: str = None,
        csv_subcategory: str = None
    ) -> Dict[str, any]:
        """Categorize single transaction using LLM + training data"""
        
        # Get training context
        training_data = await self.training_service.build_training_data()
        
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
        
        # Quick check: exact CSV match
        if csv_main and csv_category:
            csv_key = f"{csv_main}|{csv_category}"
            if csv_subcategory:
                csv_key += f"|{csv_subcategory}"
            
            if csv_key in training_data['csv_mappings']:
                category_path = training_data['csv_mappings'][csv_key]
                category = await self._find_category_by_path(category_path)
                if category:
                    return {
                        'category_id': category.id,
                        'confidence': 0.90,
                        'method': 'csv_exact',
                        'matched': csv_key
                    }
        
        # Use LLM for complex cases
        llm_result = await self._query_llm_for_category(
            merchant, memo, amount, csv_main, csv_category, csv_subcategory, training_data
        )
        
        return llm_result
    
    async def _query_llm_for_category(
        self,
        merchant: str,
        memo: str,
        amount: float,
        csv_main: str,
        csv_category: str,
        csv_subcategory: str,
        training_data: Dict
    ) -> Dict:
        """Query LLM with transaction details and training context"""
        
        # Build available categories list
        user_categories = await self._get_user_categories()
        categories_text = self._format_categories_for_llm(user_categories)
        
        # Build training examples
        training_examples = self._format_training_examples(training_data, limit=30)
        
        # Build prompt
        prompt = f"""You are a transaction categorizer. Based on learned patterns, categorize this transaction.

AVAILABLE CATEGORIES:
{categories_text}

LEARNED PATTERNS (from {training_data['total_approved']} approved transactions):
{training_examples}

TRANSACTION TO CATEGORIZE:
- Merchant: {merchant or 'Unknown'}
- Description: {memo or 'None'}
- Amount: €{abs(amount):.2f}
- CSV Category: {csv_main or ''} > {csv_category or ''} > {csv_subcategory or ''}

Respond ONLY with JSON format:
{{"category": "expense>Food>Groceries", "confidence": 0.85, "reason": "brief reason"}}

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
        
        # Fallback: return None (uncategorized)
        return {
            'category_id': None,
            'confidence': 0.0,
            'method': 'none',
            'reason': 'No match found'
        }
    
    def _parse_llm_response(self, text: str) -> Optional[Dict]:
        """Parse LLM JSON response"""
        try:
            # Extract JSON from response
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
            from sqlalchemy import select, and_
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
        # Group by type and parent
        types = {}
        for cat in categories:
            if not cat.parent_id:
                if cat.category_type not in types:
                    types[cat.category_type] = {'name': cat.name, 'children': []}
        
        for cat in categories:
            if cat.parent_id:
                for type_data in types.values():
                    if any(c.id == cat.parent_id for c in categories):
                        parent = next((c for c in categories if c.id == cat.parent_id), None)
                        if parent and not parent.parent_id:
                            type_data['children'].append(cat.name)
                            break
        
        lines = []
        for category_type, data in types.items():
            lines.append(f"{category_type}:")
            for child in data['children'][:15]:  # Limit for token efficiency
                lines.append(f"  - {child}")
        
        return "\n".join(lines)
    
    def _format_training_examples(self, training_data: Dict, limit: int = 30) -> str:
        """Format top training patterns for LLM"""
        lines = []
        
        # Top merchants
        lines.append("Top Merchant Patterns:")
        for merchant, category in list(training_data['merchant_mappings'].items())[:15]:
            lines.append(f"  '{merchant}' → {category}")
        
        # Top CSV patterns
        lines.append("\nTop CSV Patterns:")
        for csv, category in list(training_data['csv_mappings'].items())[:15]:
            lines.append(f"  '{csv}' → {category}")
        
        return "\n".join(lines)
    
    async def _find_category_by_path(self, path: str) -> Optional[Category]:
        """Find category by path like 'expense>Food>Groceries'"""
        parts = path.split('>')
        if len(parts) < 2:
            return None
        
        category_type = parts[0].lower()
        category_name = parts[1].strip()
        
        categories = await self._get_user_categories()
        
        # Find by name and type
        for cat in categories:
            if cat.name.lower() == category_name.lower() and cat.category_type == category_type:
                return cat
        
        return None


async def get_llm_categorizer(db: AsyncSession, user: User) -> LLMCategorizationService:
    """Get LLM categorization service instance"""
    return LLMCategorizationService(db, user)