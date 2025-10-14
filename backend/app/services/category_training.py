"""
Category Training Service - Learn from CSV data directly
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Any
from collections import defaultdict


class CategoryTrainingService:
    """Learn categorization patterns from CSV data"""
    
    def __init__(self, db: AsyncSession, user):
        self.db = db
        self.user = user
    
    def learn_from_csv_data(self, transactions_data: List[Dict]) -> Dict[str, Any]:
        """Learn patterns directly from CSV data with categories"""
        
        merchant_patterns = defaultdict(lambda: defaultdict(int))
        keyword_patterns = defaultdict(lambda: defaultdict(int))
        csv_patterns = defaultdict(lambda: defaultdict(int))
        
        for trans in transactions_data:
            # Get CSV categories
            main_cat = trans.get('main_category', '')
            csv_cat = trans.get('category', '')
            csv_subcat = trans.get('subcategory', '')
            
            if not main_cat or not csv_cat:
                continue
            
            # Build category key: "EXPENSES|Food|Groceries"
            category_key = f"{main_cat}|{csv_cat}"
            if csv_subcat:
                category_key += f"|{csv_subcat}"
            
            # Learn merchant patterns
            merchant = (trans.get('merchant', '') or '').lower().strip()
            if merchant:
                merchant_patterns[merchant][category_key] += 1
            
            # Learn keyword patterns from memo/message
            memo = trans.get('memo', '') or ''
            message = trans.get('message', '') or ''
            text = f"{memo} {message}".lower()
            
            words = text.split()
            for word in words:
                if len(word) > 3:  # Only meaningful words
                    keyword_patterns[word][category_key] += 1
            
            # Store exact CSV pattern
            csv_patterns[category_key][category_key] += 1
        
        # Extract strong patterns
        merchant_mappings = self._extract_strong_patterns(merchant_patterns, min_count=1)
        keyword_mappings = self._extract_strong_patterns(keyword_patterns, min_count=2)
        
        return {
            'total_transactions': len(transactions_data),
            'merchant_mappings': merchant_mappings,
            'keyword_mappings': keyword_mappings,
            'csv_patterns': list(csv_patterns.keys())
        }
    
    def _extract_strong_patterns(
        self, 
        patterns: Dict[str, Dict[str, int]], 
        min_count: int = 1,
        min_confidence: float = 0.7
    ) -> Dict[str, str]:
        """Extract patterns with high confidence"""
        
        strong_mappings = {}
        
        for pattern, categories in patterns.items():
            total = sum(categories.values())
            if total < min_count:
                continue
            
            best_category = max(categories.items(), key=lambda x: x[1])
            confidence = best_category[1] / total
            
            if confidence >= min_confidence:
                strong_mappings[pattern] = best_category[0]
        
        return strong_mappings


async def get_training_service(db: AsyncSession, user) -> CategoryTrainingService:
    """Get training service instance"""
    return CategoryTrainingService(db, user)