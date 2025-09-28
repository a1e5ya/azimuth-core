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

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# SQLite database URL
DATABASE_URL = f"sqlite:///{DATA_DIR}/finance.db"
ASYNC_DATABASE_URL = f"sqlite+aiosqlite:///{DATA_DIR}/finance.db"

print(f"Database URL: {DATABASE_URL}")
print(f"Async Database URL: {ASYNC_DATABASE_URL}")

# Async engine for production
async_engine = create_async_engine(
    ASYNC_DATABASE_URL, 
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300
)
AsyncSessionLocal = async_sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Sync engine for table creation
sync_engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)  # For local auth
    display_name = Column(String, nullable=True)
    locale = Column(String, default="en-US")
    currency = Column(String, default="EUR")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")
    category_mappings = relationship("CategoryMapping", back_populates="user", cascade="all, delete-orphan")

class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    account_type = Column(String, nullable=True)  # checking, savings, credit
    institution = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    parent_id = Column(String, ForeignKey("categories.id"), nullable=True)
    name = Column(String, nullable=False)
    code = Column(String, nullable=True)  # slug for system categories
    icon = Column(String, nullable=True)  # icon name
    color = Column(String, nullable=True)  # hex color code
    category_type = Column(String, nullable=False, default="expense")  # income, expense, transfer
    version = Column(Integer, default=1)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="categories")
    parent = relationship("Category", remote_side=[id], backref="children")
    transactions = relationship("Transaction", back_populates="category")
    category_mappings = relationship("CategoryMapping", back_populates="category")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    account_id = Column(String, ForeignKey("accounts.id"), nullable=True)
    posted_at = Column(DateTime, nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, default="EUR")
    merchant = Column(String, nullable=True)
    memo = Column(Text, nullable=True)
    mcc = Column(String, nullable=True)  # Merchant Category Code
    category_id = Column(String, ForeignKey("categories.id"), nullable=True)
    source_category = Column(String, default="user")  # user|rule|ml|llm|imported
    import_batch_id = Column(String, nullable=True, index=True)
    hash_dedupe = Column(String, nullable=True, index=True)  # For deduplication
    
    # Enhanced fields from CSV data
    transaction_type = Column(String, nullable=True)  # income, expense, transfer
    main_category = Column(String, nullable=True)  # Original main category from CSV
    csv_category = Column(String, nullable=True)  # Original category from CSV
    csv_subcategory = Column(String, nullable=True)  # Original subcategory from CSV
    csv_account = Column(String, nullable=True)  # Original account from CSV
    owner = Column(String, nullable=True)  # Owner from CSV
    csv_account_type = Column(String, nullable=True)  # Account type from CSV
    is_expense = Column(Boolean, default=False)  # From CSV
    is_income = Column(Boolean, default=False)  # From CSV
    year = Column(Integer, nullable=True)  # From CSV
    month = Column(Integer, nullable=True)  # From CSV
    year_month = Column(String, nullable=True)  # From CSV (YYYY-MM format)
    weekday = Column(String, nullable=True)  # From CSV
    transfer_pair_id = Column(String, nullable=True)  # For linked transfers
    
    # Metadata
    confidence_score = Column(Numeric(3, 2), nullable=True)  # ML confidence 0.00-1.00
    review_needed = Column(Boolean, default=False)  # Needs manual review
    tags = Column(JSON, nullable=True)  # Flexible tagging system
    notes = Column(Text, nullable=True)  # User notes
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")

class CategoryMapping(Base):
    __tablename__ = "category_mappings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    pattern_type = Column(String, nullable=False)  # keyword|regex|mcc|merchant_exact|csv_mapping
    pattern_value = Column(String, nullable=False)
    category_id = Column(String, ForeignKey("categories.id"), nullable=False)
    priority = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    confidence = Column(Numeric(3, 2), default=1.0)  # Rule confidence
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="category_mappings")
    category = relationship("Category", back_populates="category_mappings")

class CategoryVersion(Base):
    __tablename__ = "category_versions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    version = Column(Integer, nullable=False)
    label = Column(String, nullable=True)
    changes = Column(JSON, nullable=True)  # What changed
    created_at = Column(DateTime, default=datetime.utcnow)

class Goal(Base):
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

class Budget(Base):
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

class ImportBatch(Base):
    __tablename__ = "import_batches"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True)
    file_hash = Column(String, nullable=True)  # To detect duplicate files
    rows_total = Column(Integer, default=0)
    rows_imported = Column(Integer, default=0)
    rows_duplicated = Column(Integer, default=0)
    rows_errors = Column(Integer, default=0)
    status = Column(String, default="processing")  # processing|completed|failed
    error_message = Column(Text, nullable=True)
    summary_data = Column(JSON, nullable=True)  # Store processing summary
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class AuditLog(Base):
    __tablename__ = "audit_log"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=True)  # FK to users.id
    entity = Column(String, nullable=False)  # 'chat', 'auth', 'system', 'transaction', 'category'
    entity_id = Column(String, nullable=True)  # ID of affected entity
    action = Column(String, nullable=False)  # 'message', 'login', 'signup', 'error', 'import', 'create', 'update', 'delete'
    before_json = Column(JSON, nullable=True)  # State before change
    after_json = Column(JSON, nullable=True)  # State after change
    details = Column(JSON, nullable=True)    # Additional metadata
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Database session dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Sync version for initialization
def get_sync_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables (sync - for startup)
def create_tables():
    print("🔧 Creating database tables...")
    Base.metadata.create_all(bind=sync_engine)
    print("✅ Database tables created successfully!")

# Initialize database
async def init_database():
    """Initialize database connection and create tables if needed"""
    try:
        # Test connection
        async with AsyncSessionLocal() as session:
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
        
        # Create tables (sync operation)
        create_tables()
        
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False