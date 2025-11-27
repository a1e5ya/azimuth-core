"""
Transaction Models - Pydantic Schemas for API Requests/Responses

This module defines all Pydantic models used by the transactions router:
- Response models (TransactionResponse, TransactionSummary, etc.)
- Request models (TransactionUpdate, BulkCategorizeRequest, etc.)
- Filter models (TransactionFilters, AnalyticsFilters, etc.)
- Utility models (DateRange, CategoryDistribution, etc.)

Used for:
- API request validation
- API response serialization
- Type checking and documentation
- OpenAPI schema generation
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date


# ============================================================================
# TRANSACTION RESPONSE MODELS
# ============================================================================

class TransactionResponse(BaseModel):
    """
    Single transaction response with full details
    
    Includes:
    - Core transaction data (id, amount, date, merchant)
    - Category information (linked category + CSV categories)
    - Account information (account_id, bank_account, owner)
    - Financial flags (is_income, is_expense)
    - Date components (year, month, weekday)
    - Metadata (confidence, tags, notes)
    """
    # Core fields
    id: str
    account_id: Optional[str]
    posted_at: str
    amount: str
    currency: str
    merchant: Optional[str]
    memo: Optional[str]
    
    # Category (linked via FK)
    category_id: Optional[str]
    category_name: Optional[str]
    category_icon: Optional[str]
    parent_category_name: Optional[str]
    source_category: str  # imported|user|rule|ml|llm
    
    # Import tracking
    import_batch_id: Optional[str]
    
    # Account info (from CSV)
    bank_account: Optional[str]  # Egor_Main, Alex_Kopio
    bank_account_type: Optional[str]  # Main, Kopio, Reserv
    
    # CSV categories (denormalized strings for performance)
    main_category: Optional[str]  # INCOME, EXPENSES, TRANSFERS
    category: Optional[str]  # Food, Transport
    subcategory: Optional[str]  # Groceries, Fuel
    owner: Optional[str]  # Egor, Alex, Lila
    
    # Financial flags
    is_expense: bool
    is_income: bool
    
    # Date components (for filtering)
    year: Optional[int]
    month: Optional[int]
    year_month: Optional[str]  # YYYY-MM
    weekday: Optional[str]
    
    # Transfer linking
    transfer_pair_id: Optional[str]
    
    # Categorization metadata
    confidence_score: Optional[float]
    review_needed: bool
    
    # User metadata
    tags: Optional[List[str]]
    notes: Optional[str]
    
    # Timestamps
    created_at: str


class TransactionSummary(BaseModel):
    """
    Transaction summary statistics
    
    Aggregates:
    - Total counts and amounts by type
    - Categorization rate
    - Date range
    - Monthly breakdown
    - Recent imports
    - Top merchants and categories
    """
    total_transactions: int
    total_amount: float
    income_amount: float
    expense_amount: float
    transfer_amount: float
    categorized_count: int
    categorization_rate: float  # Percentage (0-100)
    date_range: Dict[str, Optional[str]]  # {earliest, latest}
    by_type: Dict[str, int]  # {income: X, expense: Y, transfer: Z}
    by_month: Dict[str, float]  # {YYYY-MM: amount}
    recent_imports: List[Dict[str, Any]]
    top_merchants: List[Dict[str, Any]]
    top_categories: List[Dict[str, Any]]


class ImportResponse(BaseModel):
    """CSV/XLSX import result"""
    success: bool
    batch_id: str
    summary: Dict[str, Any]
    message: str


class DeleteResponse(BaseModel):
    """Transaction deletion result"""
    success: bool
    message: str
    deleted_count: int = 1


class SpendingTrendsResponse(BaseModel):
    """Spending trends over time"""
    trends: List[Dict[str, Any]]
    months: int
    category_filter: Optional[str]


class MerchantAnalysisResponse(BaseModel):
    """Merchant spending analysis"""
    merchants: List[Dict[str, Any]]
    analysis_criteria: Dict[str, Any]


class ReviewTransactionsResponse(BaseModel):
    """Paginated transactions needing review"""
    transactions: List[Dict[str, Any]]
    total_count: int
    page: int
    limit: int
    has_more: bool


class BulkOperationResponse(BaseModel):
    """Bulk operation result"""
    success: bool
    message: str
    updated_count: int


# ============================================================================
# TRANSACTION REQUEST MODELS
# ============================================================================

class CategoryAssignment(BaseModel):
    """Assign category to transaction"""
    category_id: str
    confidence: Optional[float] = 1.0
    notes: Optional[str] = None


class TransactionUpdate(BaseModel):
    """Update transaction fields (all optional)"""
    merchant: Optional[str] = None
    memo: Optional[str] = None
    amount: Optional[float] = None
    category_id: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class BulkCategorizeRequest(BaseModel):
    """Bulk categorize multiple transactions"""
    transaction_ids: List[str]
    category_id: str
    confidence: float = 1.0


# ============================================================================
# FILTER MODELS
# ============================================================================

class TransactionFilters(BaseModel):
    """
    Transaction list filters
    
    Supports filtering by:
    - Date range (start_date, end_date)
    - Amount range (min_amount, max_amount)
    - Merchant (partial match)
    - Category (category_id)
    - Account (account_id)
    - Main category (INCOME, EXPENSES, TRANSFERS)
    - Review status (review_needed)
    - Owners (list of owner names)
    - Account types (list of types)
    - Main categories (list)
    
    Supports sorting by any field
    Supports pagination
    """
    # Pagination
    page: int = 1
    limit: int = 50
    
    # Date filters
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # Amount filters
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    
    # Text filters
    merchant: Optional[str] = None  # Partial match
    
    # Category filters
    category_id: Optional[str] = None
    main_category: Optional[str] = None  # INCOME, EXPENSES, TRANSFERS
    main_categories: Optional[List[str]] = None  # Multiple main categories
    
    # Account filters
    account_id: Optional[str] = None
    account_types: Optional[List[str]] = None  # Main, Kopio, Reserv, BSP
    owners: Optional[List[str]] = None  # Egor, Alex, Lila
    
    # Review filter
    review_needed: Optional[bool] = None
    
    # Sorting
    sort_by: str = "posted_at"  # Field name
    sort_order: str = "desc"  # asc|desc


class ImportFilters(BaseModel):
    """CSV/XLSX import options"""
    auto_categorize: bool = True  # Use LLM/rules for categorization


class AnalyticsFilters(BaseModel):
    """Analytics query filters"""
    months: int = 12  # Number of months to analyze
    category_id: Optional[str] = None  # Filter by category


class MerchantAnalyticsFilters(BaseModel):
    """Merchant analysis filters"""
    limit: int = 20  # Top N merchants
    min_transactions: int = 2  # Minimum transaction count


# ============================================================================
# UTILITY MODELS
# ============================================================================

class DateRange(BaseModel):
    """Date range with earliest and latest dates"""
    earliest: Optional[str]  # YYYY-MM-DD
    latest: Optional[str]  # YYYY-MM-DD


class TransactionTypeBreakdown(BaseModel):
    """Transaction count by type"""
    income: int = 0
    expense: int = 0
    transfer: int = 0
    unknown: int = 0


class CategoryDistribution(BaseModel):
    """Category spending distribution"""
    category_name: str
    count: int
    total_amount: float


class MerchantStats(BaseModel):
    """
    Merchant statistics
    
    Includes:
    - Transaction count
    - Total and average amounts
    - Transaction frequency
    - Date range
    """
    merchant: str
    transaction_count: int
    total_amount: float
    average_amount: float
    frequency_per_month: float
    first_transaction: str  # ISO date
    last_transaction: str  # ISO date


class ImportBatchInfo(BaseModel):
    """Import batch metadata"""
    id: str
    filename: str
    rows_imported: int
    status: str  # processing|completed|failed
    created_at: str  # ISO datetime


class OperationResult(BaseModel):
    """Generic operation result"""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None