"""
LLM Categorization Service - AI-Powered Transaction Categorization

Uses trained patterns and Ollama LLM to automatically categorize transactions.

Three-tier categorization approach:
1. **Merchant Pattern Matching** (90% confidence)
   - Exact or substring match on trained merchant names
   - Fast, deterministic categorization
   
2. **Keyword Pattern Matching** (80% confidence)
   - Match trained keywords in merchant/memo text
   - Covers common transaction patterns
   
3. **LLM Fallback** (Variable confidence)
   - Uses Ollama with context from trained patterns
   - Handles novel transactions and edge cases

Training Data Sources:
- CSV-mapped transactions (source_category='csv_mapped')
- User-categorized transactions (source_category='user')

Database: SQLAlchemy async with Category, Transaction models
AI Service: Ollama (llama3.2:3b) for intelligent categorization
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from typing import Dict, List, Optional, Tuple
import json
import re

from ..models.database import Category, User, Transaction
from ..services.ollama_client import llm_client


# ============================================================================
# LLM CATEGORIZATION SERVICE
# ============================================================================

class LLMCategorizationService:
    """
    Uses LLM with training data to categorize transactions
    
    Categorization pipeline:
    1. Check trained merchant patterns (highest confidence)
    2. Check trained keyword patterns (high confidence)
    3. Fall back to LLM with context (variable confidence)
    
    Each method returns:
    - category_id: UUID of matched category
    - confidence: Float 0.0-1.0 confidence score
    - method: Source of categorization (merchant_pattern, keyword_pattern, llm, none)
    - main_category, category, subcategory: CSV field values for hierarchy
    """
    
    def __init__(self, db: AsyncSession, user: User):
        """
        Initialize LLM categorization service
        
        @param db: Database session for async queries
        @param user: Current user (for filtering categories)
        """
        self.db = db
        self.user = user
        self.user_categories_cache = None  # Cache to avoid repeated queries
    
    async def _build_training_data(self) -> Dict:
        """
        Build training data from approved categorized transactions
        
        Extracts two types of mappings:
        1. Merchant → Category (for pattern matching)
        2. CSV path → Category (for CSV-based categorization)
        
        Only uses high-confidence sources:
        - csv_mapped: Categories from CSV import
        - user: Manual user categorization
        
        Excludes AI-categorized transactions to avoid reinforcing errors.
        
        Process:
        1. Query approved transactions with categories
        2. Build merchant_name → category_path mapping
        3. Build csv_path → category_path mapping
        4. Return both mappings with total count
        
        @returns {Dict} Training data with merchant/CSV mappings
        """
        # Query approved categorized transactions (limit 1000 for performance)
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
        
        # Build merchant mappings: merchant_name → category_path
        merchant_mappings = {}
        csv_mappings = {}
        
        for tx in transactions:
            # Merchant-based mapping
            if tx.merchant and tx.assigned_category:
                merchant_key = tx.merchant.lower().strip()
                merchant_mappings[merchant_key] = f"{tx.assigned_category.category_type}>{tx.assigned_category.name}"
            
            # CSV-based mapping (main|category|subcategory → category_path)
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
        """
        Categorize single transaction using three-tier approach
        
        Process:
        1. **Merchant Pattern Matching** (90% confidence)
           - Check if merchant matches any trained merchants
           - Return immediately if match found
           
        2. **Keyword Pattern Matching** (80% confidence)
           - Check if text contains any trained keywords
           - Return immediately if match found
           
        3. **LLM Fallback** (Variable confidence)
           - Query Ollama with transaction details
           - Use training data as context
           - Return LLM suggestion
        
        @param merchant: Merchant name from transaction
        @param memo: Transaction memo/description
        @param amount: Transaction amount (for context)
        @param csv_main: CSV main category (optional, for context)
        @param category: CSV category (optional, for context)
        @param subcategory: CSV subcategory (optional, for context)
        @returns {Dict} Categorization result with confidence and method
        """
        print(f"🤖 LLM categorizing: {merchant or memo} (€{amount})")
        
        # STEP 1: Check trained merchant patterns (highest priority)
        merchant_lower = (merchant or '').lower().strip()
        memo_lower = (memo or '').lower().strip()
        
        if merchant_lower:
            match = await self._match_trained_merchant(merchant_lower)
            if match:
                # Get full category hierarchy for CSV fields
                main_cat, cat, subcat = await self._get_category_hierarchy(match['category'])
                print(f"   ✅ Matched merchant pattern: {merchant_lower} → {match['category'].name}")
                return {
                    'category_id': match['category'].id,
                    'confidence': 0.90,
                    'method': 'merchant_pattern',
                    'matched': merchant_lower,
                    'main_category': main_cat,
                    'category': cat,
                    'subcategory': subcat
                }
        
        # STEP 2: Check trained keyword patterns (high priority)
        combined_text = f"{merchant_lower} {memo_lower}".strip()
        if combined_text:
            match = await self._match_trained_keywords(combined_text)
            if match:
                # Get full category hierarchy for CSV fields
                main_cat, cat, subcat = await self._get_category_hierarchy(match['category'])
                print(f"   ✅ Matched keyword pattern: {match['matched_keyword']} → {match['category'].name}")
                return {
                    'category_id': match['category'].id,
                    'confidence': 0.80,
                    'method': 'keyword_pattern',
                    'matched': match['matched_keyword'],
                    'main_category': main_cat,
                    'category': cat,
                    'subcategory': subcat
                }
        
        # STEP 3: Fallback to LLM (no patterns matched)
        print(f"   🤖 No pattern match, using LLM...")
        training_data = await self._build_training_data()
        
        llm_result = await self._query_llm_for_category(
            merchant, memo, amount, csv_main, category, subcategory, training_data
        )
        
        return llm_result
    
    async def _match_trained_merchant(self, merchant_lower: str) -> Optional[Dict]:
        """
        Check if merchant matches any trained merchant patterns
        
        Matching rules:
        - Exact match: "k-market" == "k-market"
        - Substring match: "k-market lauttasaari" contains "k-market"
        
        Uses lowercase comparison for case-insensitive matching.
        
        @param merchant_lower: Lowercase merchant name
        @returns {Dict|None} Match result with category, or None
        """
        # Get all user categories (cached)
        categories = await self._get_user_categories()
        
        # Check each category's trained merchants
        for cat in categories:
            if not cat.training_merchants:
                continue
            
            for trained_merchant in cat.training_merchants:
                trained_lower = trained_merchant.lower().strip()
                
                # Check for exact or substring match
                if trained_lower == merchant_lower or trained_lower in merchant_lower:
                    return {'category': cat, 'matched_merchant': trained_merchant}
        
        return None
    
    async def _match_trained_keywords(self, text: str) -> Optional[Dict]:
        """
        Check if text contains any trained keywords
        
        Keyword matching:
        - Looks for keyword anywhere in combined merchant + memo text
        - Case-insensitive comparison
        - Returns first match found (highest priority keywords should be most specific)
        
        @param text: Combined merchant + memo text (lowercase)
        @returns {Dict|None} Match result with category and keyword, or None
        """
        # Get all user categories (cached)
        categories = await self._get_user_categories()
        
        # Check each category's trained keywords
        for cat in categories:
            if not cat.training_keywords:
                continue
            
            for keyword in cat.training_keywords:
                keyword_lower = keyword.lower().strip()
                
                # Check if keyword appears in text
                if keyword_lower in text:
                    return {'category': cat, 'matched_keyword': keyword}
        
        return None
    
    async def _get_category_hierarchy(self, category: Category) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Get main/category/subcategory strings from category object
        
        Traverses category tree to build full hierarchy:
        - Level 3: grandparent > parent > self (full 3-level path)
        - Level 2: parent > self (2-level path)
        - Level 1: self only (type)
        
        Process:
        1. Get all user categories (for parent lookup)
        2. Find parent and grandparent
        3. Determine level based on parent chain
        4. Return appropriate strings for each level
        
        @param category: Category object (can be any level)
        @returns {Tuple} (main_category, category, subcategory) strings
        """
        # Get all categories for parent lookup
        categories = await self._get_user_categories()
        
        # Find parent and grandparent in hierarchy
        parent = next((c for c in categories if c.id == category.parent_id), None) if category.parent_id else None
        grandparent = next((c for c in categories if parent and c.id == parent.parent_id), None) if parent and parent.parent_id else None
        
        # Determine hierarchy level and return appropriate strings
        if grandparent and not grandparent.parent_id:
            # Level 3: grandparent (type) > parent (category) > self (subcategory)
            return grandparent.name, parent.name, category.name
        elif parent and not parent.parent_id:
            # Level 2: parent (type) > self (category)
            return parent.name, category.name, None
        else:
            # Level 1: self (type) only
            return category.name, None, None
    
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
        """
        Query LLM with transaction details and training context
        
        Builds comprehensive prompt with:
        - Available categories (top 20)
        - Training examples (top 30 merchant patterns)
        - Transaction details (merchant, memo, amount)
        
        LLM response format (JSON):
        ```json
        {
          "category": "type>name",
          "confidence": 0.85,
          "reason": "brief explanation"
        }
        ```
        
        Process:
        1. Build category list for LLM context
        2. Build training examples from merchant mappings
        3. Construct prompt with all context
        4. Query Ollama LLM
        5. Parse JSON response
        6. Find category by path (type>name)
        7. Return result with hierarchy
        
        @param merchant: Merchant name
        @param memo: Transaction memo
        @param amount: Transaction amount
        @param csv_main: CSV main category (optional)
        @param category: CSV category (optional)
        @param subcategory: CSV subcategory (optional)
        @param training_data: Pre-built training data dict
        @returns {Dict} Categorization result
        """
        # Get user categories and format for LLM
        user_categories = await self._get_user_categories()
        categories_text = self._format_categories_for_llm(user_categories)
        training_examples = self._format_training_examples(training_data, limit=30)
        
        # Build LLM prompt
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
            # Query Ollama LLM
            llm_response = await llm_client.query(prompt, max_tokens=100)
            
            if llm_response['status'] == 'success':
                # Parse LLM response
                result = self._parse_llm_response(llm_response['text'])
                
                if result:
                    # Find category by path (type>name)
                    category = await self._find_category_by_path(result['category'])
                    if category:
                        # Get full hierarchy for CSV fields
                        main_cat, cat, subcat = await self._get_category_hierarchy(category)
                        return {
                            'category_id': category.id,
                            'confidence': result['confidence'],
                            'method': 'llm',
                            'reason': result.get('reason', 'LLM suggestion'),
                            'main_category': main_cat,
                            'category': cat,
                            'subcategory': subcat
                        }
        
        except Exception as e:
            print(f"❌ LLM categorization failed: {e}")
        
        # Return no match if LLM failed
        return {
            'category_id': None,
            'confidence': 0.0,
            'method': 'none',
            'reason': 'No match found',
            'main_category': None,
            'category': None,
            'subcategory': None
        }
    
    def _parse_llm_response(self, text: str) -> Optional[Dict]:
        """
        Parse LLM JSON response
        
        Extracts JSON object from LLM response text:
        1. Find JSON object using regex (handles extra text)
        2. Parse JSON string
        3. Extract required fields (category, confidence, reason)
        
        Example response:
        ```
        Based on the transaction, here's my suggestion:
        {"category": "expenses>Food", "confidence": 0.85, "reason": "Grocery store"}
        ```
        
        @param text: Raw LLM response text
        @returns {Dict|None} Parsed result with category/confidence/reason, or None
        """
        try:
            # Find JSON object in response (may have surrounding text)
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return {
                    'category': data.get('category', ''),
                    'confidence': float(data.get('confidence', 0.5)),
                    'reason': data.get('reason', '')
                }
        except Exception as e:
            print(f"⚠️ Failed to parse LLM response: {e}")
        
        return None
    
    async def _get_user_categories(self) -> List[Category]:
        """
        Get all active user categories with caching
        
        Caches categories in memory to avoid repeated queries.
        Cache is per-service instance (per-request).
        
        @returns {List[Category]} All active categories for user
        """
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
        """
        Format categories as tree for LLM context
        
        Creates simple list format:
        - expenses>Food
        - expenses>Transport
        - income>Salary
        
        Limits to top 20 categories to avoid overwhelming LLM context.
        
        @param categories: List of category objects
        @returns {str} Formatted category list
        """
        lines = []
        for cat in categories[:20]:  # Limit to top 20 for brevity
            lines.append(f"- {cat.category_type}>{cat.name}")
        return "\n".join(lines)
    
    def _format_training_examples(self, training_data: Dict, limit: int = 30) -> str:
        """
        Format top training patterns for LLM context
        
        Shows most common merchant → category mappings:
        - 'k-market' → expenses>Food
        - 'shell' → expenses>Transport
        
        Limits to specified number of examples to keep prompt concise.
        
        @param training_data: Training data dict with merchant_mappings
        @param limit: Maximum number of examples to include
        @returns {str} Formatted training examples
        """
        lines = []
        
        lines.append("Top Merchants:")
        # Show top N merchant mappings
        for merchant, category in list(training_data['merchant_mappings'].items())[:limit]:
            lines.append(f"  '{merchant}' → {category}")
        
        return "\n".join(lines)
    
    async def _find_category_by_path(self, path: str) -> Optional[Category]:
        """
        Find category by path like 'expenses>Food'
        
        Path format: "type>name"
        - type: Category type (expenses, income, etc.)
        - name: Category name (Food, Transport, etc.)
        
        Case-insensitive matching on category name.
        
        @param path: Category path (type>name)
        @returns {Category|None} Matched category or None
        """
        parts = path.split('>')
        if len(parts) < 2:
            return None
        
        category_type = parts[0].lower()
        category_name = parts[1].strip()
        
        # Get all user categories
        categories = await self._get_user_categories()
        
        # Find matching category
        for cat in categories:
            if cat.name.lower() == category_name.lower() and cat.category_type == category_type:
                return cat
        
        return None