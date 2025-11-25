from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import sys
import os
from datetime import datetime

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import settings FIRST
from app.core.config import settings

print("🔧 Azimuth Core CORS Configuration:")
print(f"   ALLOWED_ORIGINS: {settings.ALLOWED_ORIGINS}")

# Import routers - UPDATED for merged files
from app.routers import auth, chat, categories_router
from app.routers import transactions_router, backup_router
from app.routers import owners_router, accounts_router
from app.routers import dangerous_router, system_router, auth_profile_router
from app.models.database import init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Azimuth Core API...")
    print(f"🔧 Database: SQLite at {settings.DATABASE_URL}")
    print(f"🤖 Ollama: {settings.OLLAMA_API_URL} ({settings.OLLAMA_MODEL})")
    
    # Validate configuration
    config_issues = settings.validate_config()
    if config_issues:
        print("⚠️ Configuration warnings:")
        for issue in config_issues:
            print(f"   - {issue}")
    
    # Initialize database
    db_success = await init_database()
    if not db_success:
        print("❌ Failed to initialize database!")
    else:
        print("✅ Database initialized successfully")
    
    # Test Ollama connection
    try:
        from app.services.ollama_client import llm_client
        ollama_status = await llm_client.check_model_availability()
        if ollama_status.get("ollama_running"):
            if ollama_status.get("model_available"):
                print(f"✅ Ollama model {settings.OLLAMA_MODEL} is ready")
            else:
                print(f"⚠️ Ollama running but model {settings.OLLAMA_MODEL} not found")
                print(f"   Available models: {ollama_status.get('available_models', [])}")
        else:
            print("⚠️ Ollama service not running - AI features will use fallbacks")
    except Exception as e:
        print(f"⚠️ Could not check Ollama status: {e}")
    
    print("✅ Azimuth Core API startup complete!")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Azimuth Core API...")

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
print(f"🌐 Setting up CORS with {len(settings.ALLOWED_ORIGINS)} origins")
print(f"   Origins: {settings.ALLOWED_ORIGINS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Include routers - SIMPLIFIED
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(chat.router, prefix="/chat", tags=["ai-chat"])
app.include_router(categories_router.router, prefix="/categories", tags=["categories"])

# Single unified transactions router
app.include_router(transactions_router.router, prefix="/transactions", tags=["transactions"])

app.include_router(owners_router.router, prefix="/owners", tags=["owners"])
app.include_router(accounts_router.router, prefix="/accounts", tags=["accounts"])

app.include_router(dangerous_router.router)
app.include_router(system_router.router)
app.include_router(auth_profile_router.router)
app.include_router(backup_router.router)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    
    # Check Ollama status
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
    """Root endpoint"""
    return {
        "app": "Azimuth Core",
        "version": settings.VERSION,
        "api_docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    print(f"🚀 Starting Azimuth Core on {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "app.main:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )