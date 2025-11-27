"""
Database Models and Connection Management

SQLAlchemy ORM models for:
- Users: Authentication and user profiles
- Owners: Account owners (e.g., family members)
- Accounts: Bank accounts linked to owners
- Transactions: Financial transactions with categorization
- Categories: Hierarchical category tree (3 levels: Type > Category > Subcategory)
- CategoryMappings: Rules for auto-categorization
- ImportBatch: CSV import tracking
- AuditLog: Activity logging for all operations
- Goals & Budgets: Financial planning features

Database: SQLite with async support (aiosqlite)
ORM: SQLAlchemy with declarative base
Connection: Async engine with connection pooling

File Location: data/finance.db
"""

import os
import asyncio
from sqlalchemy import Column, String, DateTime, Text, JSON, Numeric, Boolean, Integer, ForeignKey, create_engine, Index
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import uuid
from datetime import datetime
from typing import AsyncGenerator
from pathlib import Path

# ============================================================================
# PROJECT DIRECTORY STRUCTURE
# ============================================================================
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# ============================================================================
# DATABASE CONNECTION URLS
# ============================================================================
# SQLite database file location: data/finance.db
DATABASE_URL = f"sqlite:///{DATA_DIR}/finance.db"          # Sync engine (for table creation)
ASYNC_DATABASE_URL = f"sqlite+aiosqlite:///{DATA_DIR}/finance.db"  # Async engine (for queries)

# ============================================================================
# DATABASE ENGINES
# ============================================================================

# Async engine for production queries
# Uses aiosqlite for async SQLite operations
async_engine = create_async_engine(
    ASYNC_DATABASE_URL, 
    echo=False,              # Don't log SQL queries
    pool_pre_ping=True,      # Test connections before use
    pool_recycle=300         # Recycle connections after 5 minutes
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False   # Don't expire objects after commit
)

# Sync engine for initial table creation only
sync_engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# SQLAlchemy declarative base for all models
Base = declarative_base()


# ============================================================================
# USER MODEL - Authentication & Profile
# ============================================================================

class User(Base):
    """
    User account model for authentication
    
    Stores:
    - Authentication credentials (email, password_hash)
    - User preferences (display_name, locale, currency)
    - Creation timestamp
    
    Relationships:
    - One-to-many: accounts, categories, transactions, goals, budgets, owners
    """
    __tablename__ = "users"
    
    # Primary key: UUID string
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Authentication
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)  # Bcrypt hash
    
    # Profile
    display_name = Column(String, nullable=True)
    locale = Column(String, default="en-US")
    currency = Column(String, default="EUR")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships (one-to-many with cascade delete)
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")
    category_mappings = relationship("CategoryMapping", back_populates="user", cascade="all, delete-orphan")
    owners = relationship("Owner", back_populates="user", cascade="all, delete-orphan")


# ============================================================================
# OWNER MODEL - Account Owners (e.g., Family Members)
# ============================================================================

class Owner(Base):
    """
    Account owner model (e.g., family members)
    
    Allows tracking multiple people's accounts within one user account
    Example: "Egor", "Alex", "Lila"
    
    Stores:
    - Owner name and display color
    - Active status (soft delete)
    
    Relationships:
    - Many-to-one: user
    - One-to-many: accounts
    """
    __tablename__ = "owners"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    # Owner details
    name = Column(String, nullable=False)
    color = Column(String, nullable=True)  # Hex color for UI (#3b82f6)
    active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="owners")
    accounts = relationship("Account", back_populates="owner", cascade="all, delete-orphan")


# ============================================================================
# ACCOUNT MODEL - Bank Accounts
# ============================================================================

class Account(Base):
    """
    Bank account model linked to owners
    
    Stores:
    - Account name and type (Main, Kopio, Reserv, BSP)
    - Current balance
    - Institution (optional)
    
    Relationships:
    - Many-to-one: user, owner
    - One-to-many: transactions
    """
    __tablename__ = "accounts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    owner_id = Column(String, ForeignKey("owners.id"), nullable=False, index=True)
    
    # Account details
    name = Column(String, nullable=False)  # Display name
    account_type = Column(String, nullable=False)  # Main, Kopio, Reserv, BSP
    institution = Column(String, nullable=True)  # Bank name (optional)
    
    # Financial tracking
    current_balance = Column(Numeric(12, 2), default=0.0)
    
    # Metadata
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="accounts")
    owner = relationship("Owner", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")


# ============================================================================
# CATEGORY MODEL - Hierarchical Category Tree
# ============================================================================

class Category(Base):
    """
    Hierarchical category model (3 levels)
    
    Level 1: Type (INCOME, EXPENSES, TRANSFERS, TARGETS)
    Level 2: Category (Food, Transport, Salary)
    Level 3: Subcategory (Groceries, Fuel, Monthly Salary)
    
    Stores:
    - Category name, icon, color
    - Parent reference for hierarchy
    - Training data (merchants, keywords) for auto-categorization
    - Version tracking for category changes
    
    Relationships:
    - Many-to-one: user, parent
    - One-to-many: children, transactions, category_mappings
    """
    __tablename__ = "categories"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    parent_id = Column(String, ForeignKey("categories.id"), nullable=True)
    
    # Category details
    name = Column(String, nullable=False)
    code = Column(String, nullable=True)  # Slug for system categories (e.g., "groceries")
    icon = Column(String, nullable=True)  # Icon name (e.g., "coffee")
    color = Column(String, nullable=True)  # Hex color (#9B7EDE)
    category_type = Column(String, nullable=False, default="expense")  # income, expense, transfer
    version = Column(Integer, default=1)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # AI Training data (learned from categorized transactions)
    training_merchants = Column(JSON, nullable=True)  # ["S-MARKET", "LIDL"]
    training_keywords = Column(JSON, nullable=True)   # ["grocery", "food"]
    last_training_update = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="categories")
    parent = relationship("Category", remote_side=[id], backref="children")
    transactions = relationship("Transaction", back_populates="assigned_category")
    category_mappings = relationship("CategoryMapping", back_populates="category")


# ============================================================================
# TRANSACTION MODEL - Financial Transactions
# ============================================================================

class Transaction(Base):
    """
    Financial transaction model
    
    Stores:
    - Core transaction data (date, amount, merchant, memo)
    - Category assignment (FK to Category + denormalized strings for performance)
    - Account/owner information
    - Financial flags (is_income, is_expense)
    - Date components (year, month, weekday) for filtering
    - Transfer pair linking
    - Categorization metadata (source, confidence)
    - Import tracking
    
    Relationships:
    - Many-to-one: user, account, assigned_category
    """
    __tablename__ = "transactions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    account_id = Column(String, ForeignKey("accounts.id"), nullable=True)
    
    # Core transaction data
    posted_at = Column(DateTime, nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, default="EUR")
    merchant = Column(String, nullable=True)
    memo = Column(Text, nullable=True)
    
    # Categories (denormalized strings from CSV for performance)
    # These are STRING fields, not relationships
    main_category = Column(String, nullable=True)  # INCOME, EXPENSES, TRANSFERS
    category = Column(String, nullable=True)  # Food, Transport, etc.
    subcategory = Column(String, nullable=True)  # Groceries, Fuel, etc.
    
    # Account info (from CSV import)
    bank_account = Column(String, nullable=True)  # Egor_Main, Alex_Kopio
    owner = Column(String, nullable=True)  # Egor, Alex, Lila
    bank_account_type = Column(String, nullable=True)  # Main, Kopio, Reserv
    
    # Financial flags
    is_expense = Column(Boolean, default=False)
    is_income = Column(Boolean, default=False)
    
    # Date components (for efficient filtering)
    year = Column(Integer, nullable=True)
    month = Column(Integer, nullable=True)
    year_month = Column(String, nullable=True)  # YYYY-MM
    weekday = Column(String, nullable=True)
    
    # Transfer linking (pairs of transactions between accounts)
    transfer_pair_id = Column(String, nullable=True)
    
    # Categorization metadata (FK to Category table)
    category_id = Column(String, ForeignKey("categories.id"), nullable=True)
    source_category = Column(String, default="imported")  # imported|user|rule|ml|llm
    confidence_score = Column(Numeric(3, 2), nullable=True)
    review_needed = Column(Boolean, default=False)
    
    # Import tracking
    import_batch_id = Column(String, nullable=True, index=True)
    hash_dedupe = Column(String, nullable=True, index=True)  # SHA256 for duplicate detection
    
    # Metadata
    tags = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")
    assigned_category = relationship("Category", back_populates="transactions")


# ============================================================================
# CATEGORY MAPPING MODEL - Auto-Categorization Rules
# ============================================================================

class CategoryMapping(Base):
    """
    Category mapping rules for auto-categorization
    
    Pattern types:
    - keyword: Match text in merchant/memo
    - regex: Regular expression matching
    - mcc: Merchant Category Code
    - merchant_exact: Exact merchant name match
    - csv_mapping: CSV column value mapping
    
    Stores:
    - Pattern type and value
    - Target category
    - Priority (higher = applied first)
    - Confidence score
    
    Relationships:
    - Many-to-one: user, category
    """
    __tablename__ = "category_mappings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Pattern matching
    pattern_type = Column(String, nullable=False)  # keyword|regex|mcc|merchant_exact|csv_mapping
    pattern_value = Column(String, nullable=False)
    category_id = Column(String, ForeignKey("categories.id"), nullable=False)
    
    # Rule metadata
    priority = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    confidence = Column(Numeric(3, 2), default=1.0)  # Rule confidence (0.0-1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="category_mappings")
    category = relationship("Category", back_populates="category_mappings")


# ============================================================================
# CATEGORY VERSION MODEL - Category History Tracking
# ============================================================================

class CategoryVersion(Base):
    """
    Category version history for rollback support
    
    Tracks changes to category structure
    Allows reverting to previous category trees
    
    Stores:
    - Version number
    - Label (e.g., "Before Q2 cleanup")
    - JSON of changes made
    """
    __tablename__ = "category_versions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    version = Column(Integer, nullable=False)
    label = Column(String, nullable=True)
    changes = Column(JSON, nullable=True)  # What changed
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# GOAL MODEL - Financial Goals
# ============================================================================

class Goal(Base):
    """
    Financial goal model
    
    Goal types:
    - savings: Save X amount
    - spending: Limit spending to X
    - paydown: Pay off X debt
    
    Stores:
    - Goal name and type
    - Target and current amounts
    - Target date (optional)
    - Category scope (which categories apply)
    - Status (active/done/archived)
    
    Relationships:
    - Many-to-one: user
    """
    __tablename__ = "goals"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    name = Column(String, nullable=False)
    goal_type = Column(String, nullable=False)  # savings|spending|paydown
    target_amount = Column(Numeric(12, 2), nullable=False)
    current_amount = Column(Numeric(12, 2), default=0.0)
    target_date = Column(DateTime, nullable=True)
    category_scope = Column(JSON, nullable=True)  # Which categories apply
    status = Column(String, default="active")  # active|done|archived
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="goals")


# ============================================================================
# BUDGET MODEL - Monthly Budgets
# ============================================================================

class Budget(Base):
    """
    Monthly budget model
    
    Stores:
    - Budget name and month (YYYY-MM)
    - Category scope (optional)
    - Limit and spent amounts
    - Rollover setting
    
    Relationships:
    - Many-to-one: user
    """
    __tablename__ = "budgets"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    category_id = Column(String, ForeignKey("categories.id"), nullable=True)
    
    name = Column(String, nullable=False)
    month = Column(String, nullable=False)  # YYYY-MM format
    limit_amount = Column(Numeric(12, 2), nullable=False)
    spent_amount = Column(Numeric(12, 2), default=0.0)
    rollover = Column(Boolean, default=False)  # Rollover unused amount
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="budgets")


# ============================================================================
# IMPORT BATCH MODEL - CSV Import Tracking
# ============================================================================

class ImportBatch(Base):
    """
    Import batch tracking for CSV uploads
    
    Stores:
    - File metadata (name, size, hash)
    - Import statistics (total, imported, duplicated, errors)
    - Processing status
    - Summary data (JSON)
    
    Used for:
    - Duplicate file detection (file_hash)
    - Import history
    - Rollback support
    """
    __tablename__ = "import_batches"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # File metadata
    filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True)
    file_hash = Column(String, nullable=True)  # To detect duplicate files
    
    # Import statistics
    rows_total = Column(Integer, default=0)
    rows_imported = Column(Integer, default=0)
    rows_duplicated = Column(Integer, default=0)
    rows_errors = Column(Integer, default=0)
    
    # Processing status
    status = Column(String, default="processing")  # processing|completed|failed
    error_message = Column(Text, nullable=True)
    summary_data = Column(JSON, nullable=True)  # Store processing summary
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


# ============================================================================
# AUDIT LOG MODEL - Activity Logging
# ============================================================================

class AuditLog(Base):
    """
    Audit log for all user actions
    
    Logged entities:
    - chat: AI chat messages
    - auth: Login, logout, registration
    - system: System events
    - transaction: Transaction CRUD
    - category: Category changes
    
    Logged actions:
    - message, login, signup, error
    - import, create, update, delete
    
    Stores:
    - Before/after state (JSON)
    - Additional details (JSON)
    - IP address and user agent
    
    Relationships:
    - Many-to-one: user (nullable for system events)
    """
    __tablename__ = "audit_log"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=True)  # FK to users.id
    
    # Event details
    entity = Column(String, nullable=False)  # 'chat', 'auth', 'system', 'transaction', 'category'
    entity_id = Column(String, nullable=True)  # ID of affected entity
    action = Column(String, nullable=False)  # 'message', 'login', 'signup', 'error', 'import', 'create', 'update', 'delete'
    
    # State tracking
    before_json = Column(JSON, nullable=True)  # State before change
    after_json = Column(JSON, nullable=True)  # State after change
    details = Column(JSON, nullable=True)    # Additional metadata
    
    # Request metadata
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# DATABASE SESSION MANAGEMENT
# ============================================================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session dependency for FastAPI
    
    Usage in endpoints:
    @router.get("/transactions")
    async def get_transactions(db: AsyncSession = Depends(get_db)):
        ...
    
    Yields async session and ensures cleanup on request completion
    
    @yields {AsyncSession} Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_db():
    """
    Sync database session (for initialization only)
    
    Used only for table creation during startup
    Most operations should use async get_db() instead
    
    @yields {Session} Sync database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def create_tables():
    """
    Create all database tables (sync operation)
    
    Uses SQLAlchemy's create_all() to generate tables from models
    Only creates tables that don't already exist (safe to call multiple times)
    
    Called during application startup
    """
    Base.metadata.create_all(bind=sync_engine)


async def init_database():
    """
    Initialize database connection and create tables
    
    Process:
    1. Test async connection with simple query
    2. Create tables if they don't exist (sync operation)
    
    Called during FastAPI lifespan startup
    
    @returns {bool} True if successful, False on error
    """
    try:
        # Test async connection
        async with AsyncSessionLocal() as session:
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
        
        # Create tables (sync operation)
        create_tables()
        
        return True
        
    except Exception as e:
        console.error(f"❌ Database initialization failed: {e}")
        return False