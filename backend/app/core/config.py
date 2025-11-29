"""
Application Configuration Management

Loads and validates configuration from:
- Environment variables (.env file)
- Default values (for local development)

Configuration includes:
- Database connection (SQLite file path)
- JWT authentication settings
- Ollama AI service connection
- File upload limits and paths
- CORS origins for frontend
- Logging and rate limiting

Environment Variables:
- DATABASE_URL: SQLite database path
- JWT_SECRET_KEY: Secret for signing tokens
- OLLAMA_API_URL: Local Ollama service URL
- OLLAMA_MODEL: LLM model name (default: llama3.2:3b)
- ALLOWED_ORIGINS: Comma-separated CORS origins

File Structure:
- data/finance.db: SQLite database
- data/uploads/: Temporary CSV upload storage
- data/backups/: Database backup storage
- logs/: Application logs
"""

import os
import secrets
import warnings
from typing import List
from pathlib import Path
from dotenv import load_dotenv

# Suppress Pydantic protected namespace warnings
warnings.filterwarnings("ignore", message=".*conflict with protected namespace.*")

# Load environment variables from .env.local file (if exists)
load_dotenv(".env.local", verbose=False)

# ============================================================================
# PROJECT DIRECTORY STRUCTURE
# ============================================================================
# Get absolute path to project root (4 levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"


class Settings:
    """
    Application configuration singleton
    
    Loads configuration from environment variables with fallback defaults
    Validates required settings on initialization
    Provides helper methods for service-specific configs
    """
    
    def __init__(self):
        """
        Initialize application settings from environment
        
        Creates required directories if they don't exist
        Generates secure random keys if not provided
        """
        
        # ====================================================================
        # APPLICATION METADATA
        # ====================================================================
        self.APP_NAME = "Azimuth Core API"
        self.APP_DESCRIPTION = "Local Personal Finance Management - Complete Privacy"
        self.VERSION = "1.0.0"
        self.DEBUG = os.getenv("DEBUG", "true").lower() == "true"
        
        # ====================================================================
        # DATABASE CONFIGURATION (SQLite)
        # ====================================================================
        # SQLite database file location: data/finance.db
        # Sync URL for table creation, Async URL for queries
        self.DATABASE_URL = os.getenv(
            "DATABASE_URL", 
            f"sqlite:///{DATA_DIR}/finance.db"
        )
        self.ASYNC_DATABASE_URL = os.getenv(
            "ASYNC_DATABASE_URL",
            f"sqlite+aiosqlite:///{DATA_DIR}/finance.db"
        )
        
        # ====================================================================
        # SECURITY & AUTHENTICATION
        # ====================================================================
        # Generate secure random keys if not provided in environment
        # Keys are 32-byte URL-safe base64 encoded strings
        self.SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
        self.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
        self.JWT_ALGORITHM = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")  # 24 hours default
        )
        
        # ====================================================================
        # SERVER CONFIGURATION
        # ====================================================================
        self.HOST = os.getenv("HOST", "0.0.0.0")  # Bind to all interfaces
        self.PORT = int(os.getenv("PORT", "8001"))
        
        # ====================================================================
        # OLLAMA LLM SERVICE CONFIGURATION
        # ====================================================================
        # Local Ollama service for transaction categorization
        # Default: http://localhost:11434 (Ollama's default port)
        self.OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
        self.OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        self.OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "30"))
        
        # ====================================================================
        # FILE UPLOAD CONFIGURATION
        # ====================================================================
        # CSV/XLSX transaction import settings
        self.MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", str(10 * 1024 * 1024)))  # 10MB
        self.ALLOWED_FILE_EXTENSIONS = [".csv", ".xlsx"]
        self.UPLOAD_DIR = DATA_DIR / "uploads"
        
        # ====================================================================
        # DATA PROCESSING SETTINGS
        # ====================================================================
        self.DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "EUR")
        self.DEFAULT_LOCALE = os.getenv("DEFAULT_LOCALE", "en-US")
        self.CSV_PROCESSING_BATCH_SIZE = int(os.getenv("CSV_PROCESSING_BATCH_SIZE", "1000"))
        
        # ====================================================================
        # PRIVACY & DATA RETENTION
        # ====================================================================
        # 0 = keep forever (no automatic deletion)
        self.DATA_RETENTION_DAYS = int(os.getenv("DATA_RETENTION_DAYS", "0"))
        self.AUTO_BACKUP_ENABLED = os.getenv("AUTO_BACKUP_ENABLED", "false").lower() == "true"
        self.BACKUP_DIR = DATA_DIR / "backups"
        
        # ====================================================================
        # LOGGING CONFIGURATION
        # ====================================================================
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_DIR = PROJECT_ROOT / "logs"
        self.LOG_ROTATION = os.getenv("LOG_ROTATION", "daily")
        
        # ====================================================================
        # RATE LIMITING (Security)
        # ====================================================================
        # Prevents abuse of API endpoints
        self.RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
        self.RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
        self.RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds
        
        # ====================================================================
        # DEVELOPMENT SETTINGS
        # ====================================================================
        self.RELOAD = os.getenv("RELOAD", "false").lower() == "true"  # Auto-reload on code changes
        self.TESTING = os.getenv("TESTING", "false").lower() == "true"
        
        # Create required directories (data, uploads, backups, logs)
        self._ensure_directories()
    
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        """
        CORS allowed origins for frontend requests
        
        Reads from ALLOWED_ORIGINS environment variable (comma-separated)
        Falls back to default localhost origins for development
        
        Format: "http://localhost:5173,http://localhost:3000"
        
        @returns {List[str]} List of allowed origin URLs
        """
        cors_env = os.getenv("ALLOWED_ORIGINS", "")
        
        if cors_env:
            # Parse comma-separated origins from environment
            origins = [origin.strip() for origin in cors_env.split(",") if origin.strip()]
            return origins
        
        # Default origins for local development (Vite + common ports)
        default_origins = [
            "http://localhost:5173",    # Vite dev server
            "http://127.0.0.1:5173",   # Alternative localhost
            "http://localhost:3000",    # Alternative frontend port
            "http://127.0.0.1:3000",
            "http://localhost:8080",
            "http://127.0.0.1:8080"
        ]
        
        return default_origins
    
    def _ensure_directories(self):
        """
        Create required directories if they don't exist
        
        Directories created:
        - data/: Main data storage
        - data/uploads/: Temporary CSV upload storage
        - data/backups/: Database backups
        - logs/: Application logs
        
        Uses exist_ok=True to avoid errors if already exists
        """
        directories = [
            DATA_DIR,
            self.UPLOAD_DIR,
            self.BACKUP_DIR,
            self.LOG_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @property 
    def database_config(self) -> dict:
        """
        SQLAlchemy database configuration
        
        Settings:
        - echo: Log SQL queries (if DEBUG mode)
        - pool_pre_ping: Test connections before use
        - pool_recycle: Recycle connections after 300s
        
        @returns {dict} Database connection parameters
        """
        return {
            "url": self.ASYNC_DATABASE_URL,
            "echo": self.DEBUG,
            "pool_pre_ping": True,
            "pool_recycle": 300
        }
    
    @property
    def ollama_config(self) -> dict:
        """
        Ollama LLM service configuration
        
        Used for AI-powered transaction categorization
        
        @returns {dict} Ollama connection parameters
        """
        return {
            "api_url": self.OLLAMA_API_URL,
            "model": self.OLLAMA_MODEL,
            "timeout": self.OLLAMA_TIMEOUT
        }
    
    @property
    def security_config(self) -> dict:
        """
        Security and authentication configuration
        
        Includes JWT signing keys and token expiration
        
        @returns {dict} Security parameters
        """
        return {
            "secret_key": self.SECRET_KEY,
            "jwt_secret_key": self.JWT_SECRET_KEY,
            "jwt_algorithm": self.JWT_ALGORITHM,
            "access_token_expire_minutes": self.ACCESS_TOKEN_EXPIRE_MINUTES
        }
    
    def get_environment_info(self) -> dict:
        """
        Get current environment configuration (for debugging)
        
        Returns non-sensitive configuration details
        Does NOT include secret keys or passwords
        
        @returns {dict} Environment configuration summary
        """
        return {
            "app_name": self.APP_NAME,
            "version": self.VERSION,
            "debug": self.DEBUG,
            "host": self.HOST,
            "port": self.PORT,
            "database_type": "SQLite",
            "database_path": str(DATA_DIR / "finance.db"),
            "ollama_url": self.OLLAMA_API_URL,
            "ollama_model": self.OLLAMA_MODEL,
            "data_directory": str(DATA_DIR),
            "upload_directory": str(self.UPLOAD_DIR),
            "log_directory": str(self.LOG_DIR),
            "cors_origins": self.ALLOWED_ORIGINS,
            "privacy_mode": "full_local",
            "cloud_services": "disabled"
        }
    
    def validate_config(self) -> List[str]:
        """
        Validate configuration and return warnings
        
        Checks:
        - Ollama service connectivity
        - Database directory write permissions
        - Secret key length (security)
        
        @returns {List[str]} List of configuration issues (empty if valid)
        """
        issues = []
        
        # Check Ollama service availability (non-blocking - warning only)
        try:
            import requests
            response = requests.get(f"{self.OLLAMA_API_URL}/api/tags", timeout=5)
            if response.status_code != 200:
                issues.append(f"Ollama not reachable at {self.OLLAMA_API_URL}")
        except Exception:
            issues.append(f"Cannot connect to Ollama at {self.OLLAMA_API_URL}")
        
        # Check database directory write permissions
        try:
            test_file = DATA_DIR / "test_write.tmp"
            test_file.write_text("test")
            test_file.unlink()
        except Exception:
            issues.append(f"Data directory not writable: {DATA_DIR}")
        
        # Validate secret key length (security requirement)
        if len(self.SECRET_KEY) < 32:
            issues.append("SECRET_KEY should be at least 32 characters")
        
        if len(self.JWT_SECRET_KEY) < 32:
            issues.append("JWT_SECRET_KEY should be at least 32 characters")
        
        return issues


# ============================================================================
# GLOBAL SETTINGS INSTANCE
# ============================================================================
# Single instance used throughout the application
settings = Settings()

# Display configuration summary on import (only in debug mode)
if settings.DEBUG:
    config_issues = settings.validate_config()
    if config_issues:
        for issue in config_issues:
            print(f"⚠️ Config: {issue}")