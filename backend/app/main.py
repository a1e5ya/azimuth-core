"""
Azimuth Core API - Main Application Entry Point

This module initializes the FastAPI application with:
- CORS middleware for cross-origin requests
- Database connection and table initialization (SQLite)
- Ollama LLM service connection check
- API route registration for all modules
- Health check endpoints

Database: SQLite (local file storage)
AI Service: Ollama (local LLM for transaction categorization)
Auth: JWT-based local authentication
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import sys
import os
from datetime import datetime

# Add parent directory to Python path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import configuration first (required for all other imports)
from app.core.config import settings

# Import all API routers
from app.routers import auth, chat, categories_router
from app.routers import transactions_router, backup_router
from app.routers import owners_router, accounts_router
from app.routers import dangerous_router, system_router, auth_profile_router
from app.models.database import init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager - handles startup and shutdown events
    
    Startup sequence:
    1. Validate configuration settings
    2. Initialize SQLite database and create tables
    3. Test Ollama LLM service connection
    
    Shutdown:
    - Clean shutdown message (connections closed automatically by FastAPI)
    
    @param app: FastAPI application instance
    """
    # ============================================================================
    # STARTUP SEQUENCE
    # ============================================================================
    
    print("\n🚀 Starting Azimuth Core API...")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Host: {settings.HOST}:{settings.PORT}")
    print("-" * 50)
    
    # Validate application configuration (database path, Ollama URL, etc.)
    config_issues = settings.validate_config()
    if config_issues:
        for issue in config_issues:
            print(f"⚠️ Configuration warning: {issue}")
    
    # Initialize database connection and create tables if they don't exist
    # Uses SQLAlchemy async engine with SQLite
    print("🔧 Initializing database...")
    db_success = await init_database()
    if not db_success:
        print("❌ CRITICAL: Database initialization failed!")
        raise RuntimeError("Database initialization failed - cannot start application")
    print("✅ Database connected and ready")
    
    # Test Ollama LLM service connection (used for transaction categorization)
    # Non-blocking - app will work without Ollama but AI features disabled
    print("🤖 Checking Ollama LLM service...")
    try:
        from app.services.ollama_client import llm_client
        ollama_status = await llm_client.check_model_availability()
        
        if ollama_status.get("ollama_running") and ollama_status.get("model_available"):
            print(f"✅ Ollama connected - Model: {settings.OLLAMA_MODEL}")
        elif ollama_status.get("ollama_running"):
            print(f"⚠️ Ollama running but model {settings.OLLAMA_MODEL} not available")
        else:
            print("⚠️ Ollama service not running - AI features will use fallbacks")
    except Exception as e:
        print(f"⚠️ Could not connect to Ollama: {e}")
    
    print("-" * 50)
    print("✨ Azimuth Core API is ready!")
    print(f"📖 API Docs: http://{settings.HOST}:{settings.PORT}/docs")
    print("-" * 50 + "\n")
    
    yield
    
    # ============================================================================
    # SHUTDOWN SEQUENCE
    # ============================================================================
    # FastAPI automatically closes database connections and cleans up resources


# Initialize FastAPI application with OpenAPI documentation
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",      # Swagger UI documentation
    redoc_url="/redoc"     # ReDoc documentation
)

# ============================================================================
# CORS MIDDLEWARE CONFIGURATION
# ============================================================================
# Allows frontend (Vue.js) to make requests from different origin
# Configured origins from settings (default: localhost:5173 for Vite dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,  # Allow cookies/auth headers
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# ============================================================================
# API ROUTE REGISTRATION
# ============================================================================
# Authentication: User registration, login, token verification
app.include_router(auth.router, prefix="/auth", tags=["authentication"])

# AI Chat: Ollama-powered financial assistant
app.include_router(chat.router, prefix="/chat", tags=["ai-chat"])

# Categories: Transaction category management (INCOME, EXPENSES, TRANSFERS)
app.include_router(categories_router.router, prefix="/categories", tags=["categories"])

# Transactions: Import, CRUD, filtering, categorization
app.include_router(transactions_router.router, prefix="/transactions", tags=["transactions"])

# Owners: Account owner management (e.g., family members)
app.include_router(owners_router.router, prefix="/owners", tags=["owners"])

# Accounts: Bank account management linked to owners
app.include_router(accounts_router.router, prefix="/accounts", tags=["accounts"])

# System: Health checks, stats, activity logs
app.include_router(system_router.router)

# User Profile: Update user settings
app.include_router(auth_profile_router.router)

# Backup: Database export/import
app.include_router(backup_router.router)

# Dangerous: Delete operations requiring password confirmation
app.include_router(dangerous_router.router)


@app.get("/health")
async def health_check():
    """
    System health check endpoint
    
    Checks status of:
    - Database connection (SQLite)
    - Ollama LLM service availability
    
    @returns {dict} Health status with service details
    """
    # Check Ollama LLM service status
    ollama_status = "unknown"
    try:
        from app.services.ollama_client import llm_client
        ollama_check = await llm_client.check_model_availability()
        
        if ollama_check.get("ollama_running") and ollama_check.get("model_available"):
            ollama_status = "ready"
        elif ollama_check.get("ollama_running"):
            ollama_status = "running_no_model"
        else:
            ollama_status = "offline"
    except Exception:
        ollama_status = "error"
    
    # Database is always "connected" if app started successfully
    database_status = "connected" if settings.DATABASE_URL else "not_configured"
    
    return {
        "status": "healthy",
        "app": "azimuth_core",
        "version": settings.VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": {"status": database_status, "type": "sqlite"},
            "ai": {"status": ollama_status, "model": settings.OLLAMA_MODEL}
        }
    }


@app.get("/")
async def root():
    """
    Root endpoint - API information
    
    @returns {dict} Basic API info with documentation links
    """
    return {
        "app": "Azimuth Core",
        "version": settings.VERSION,
        "api_docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    """
    Direct execution entry point
    
    Starts Uvicorn ASGI server with configured host/port
    Used for: python backend/app/main.py
    """
    uvicorn.run(
        "app.main:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )