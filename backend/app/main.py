from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import sys
import os
from datetime import datetime



# Add parent directory to path so we can import app modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import settings FIRST
from app.core.config import settings

# NOW we can use settings for debug output
print("🔧 Azimuth Core CORS Configuration:")
print(f"   ALLOWED_ORIGINS: {settings.ALLOWED_ORIGINS}")

# Import other modules after settings
from app.routers import auth, chat, categories_router
from app.routers import transactions_router, transaction_import_router, transaction_analytics_router
from app.routers import owners_router, accounts_router
from app.routers import dangerous_router, system_router, auth_profile_router
from app.models.database import init_database

# Lifespan manager for startup/shutdown events
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

# CORS middleware with local development support - CRITICAL FIX
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

# Include routers with updated structure
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(chat.router, prefix="/chat", tags=["ai-chat"])
app.include_router(categories_router.router, prefix="/categories", tags=["categories"])

# Transaction routers - separated by functionality
app.include_router(transactions_router.router, prefix="/transactions", tags=["transactions"])
app.include_router(transaction_import_router.router, prefix="/transactions", tags=["csv-import"])
app.include_router(transaction_analytics_router.router, prefix="/transactions/analytics", tags=["analytics"])
app.include_router(owners_router.router, prefix="/owners", tags=["owners"])
app.include_router(accounts_router.router, prefix="/accounts", tags=["accounts"])

app.include_router(dangerous_router.router)
app.include_router(system_router.router)
app.include_router(auth_profile_router.router)

@app.get("/health")
async def health_check():
    """Health check endpoint with comprehensive system status"""
    
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
    
    # Database status
    database_status = "connected" if settings.DATABASE_URL else "not_configured"
    
    return {
        "status": "healthy",
        "app": "azimuth_core",
        "version": settings.VERSION,
        "description": "Local Personal Finance Management - Complete Privacy",
        "timestamp": datetime.utcnow().isoformat(),
        
        # System Status
        "services": {
            "database": {
                "status": database_status,
                "type": "sqlite",
                "location": "local"
            },
            "ai": {
                "status": ollama_status,
                "provider": "ollama",
                "model": settings.OLLAMA_MODEL,
                "location": "local"
            }
        },
        
        # Configuration Info
        "config": {
            "privacy_mode": "full_local",
            "cloud_services": "disabled",
            "data_location": "local_only",
            "cors_origins": len(settings.ALLOWED_ORIGINS),
            "debug": settings.DEBUG
        },
        
        # Available Features
        "features": [
            "local_authentication",
            "csv_transaction_import", 
            "ai_powered_chat",
            "transaction_categorization",
            "financial_analytics",
            "data_privacy_guaranteed",
            "offline_capable"
        ],
        
        # API Endpoints
        "endpoints": {
            "authentication": "/auth/*",
            "ai_chat": "/chat/*", 
            "transactions": "/transactions/*",
            "analytics": "/transactions/analytics/*",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/")
async def root():
    """Root endpoint with app information"""
    return {
        "app": "Azimuth Core",
        "tagline": "Local Personal Finance Management - Complete Privacy",
        "version": settings.VERSION,
        "description": "A privacy-focused personal finance application that runs completely locally",
        
        "key_features": [
            "🔒 Complete Privacy - All data stays on your device",
            "🤖 Local AI - Powered by Ollama with llama3.2 20B (no cloud AI services)",
            "📊 CSV Import - Import transactions from any bank",
            "🏷️ Smart Categorization - AI-powered transaction classification", 
            "📈 Financial Analytics - Spending insights and trends",
            "🚀 One-Click Setup - Easy installation and startup"
        ],
        
        "getting_started": {
            "1": "Create an account at /auth/register",
            "2": "Import your CSV transaction files",
            "3": "Chat with AI for financial insights",
            "4": "Explore analytics and spending patterns"
        },
        
        "api_docs": "/docs",
        "privacy": "zero_data_transmission",
        "local_ai": f"Ollama {settings.OLLAMA_MODEL}",
        "database": "SQLite (local file)",
        
        "system_info": {
            "host": settings.HOST,
            "port": settings.PORT,
            "environment": "local_development" if settings.DEBUG else "local_production",
            "startup_time": datetime.utcnow().isoformat()
        }
    }

@app.get("/privacy")
async def privacy_info():
    """Privacy information endpoint"""
    return {
        "privacy_policy": "complete_local_processing",
        "data_location": "your_device_only",
        "external_connections": "none",
        "ai_processing": "local_ollama_only",
        "cloud_services": "disabled",
        
        "guarantees": [
            "No data transmitted to external servers",
            "No cloud AI services used",
            "No external analytics or tracking", 
            "All data stored in local SQLite database",
            "You own and control all your financial data"
        ],
        
        "data_storage": {
            "database": "SQLite file on your device",
            "location": str(settings.DATA_DIR),
            "encryption": "file_system_level",
            "backup": "manual_local_only"
        },
        
        "ai_processing": {
            "provider": "Ollama (local)",
            "model": settings.OLLAMA_MODEL,
            "data_sent": "prompts_only_local_processing",
            "external_apis": "none"
        }
    }

@app.get("/system")
async def system_info():
    """System information for debugging"""
    return settings.get_environment_info()

if __name__ == "__main__":
    print(f"🚀 Starting Azimuth Core on {settings.HOST}:{settings.PORT}")
    print(f"📖 API Documentation: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"🔒 Privacy Info: http://{settings.HOST}:{settings.PORT}/privacy")
    
    uvicorn.run(
        "app.main:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )

