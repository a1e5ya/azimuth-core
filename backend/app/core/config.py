import os
import secrets
from typing import List
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"

class Settings:
    """Local configuration for Azimuth Core - Privacy-focused personal finance app"""
    
    def __init__(self):
        # App Information
        self.APP_NAME = "Azimuth Core API"
        self.APP_DESCRIPTION = "Local Personal Finance Management - Complete Privacy"
        self.VERSION = "1.0.0"
        self.DEBUG = os.getenv("DEBUG", "true").lower() == "true"
        
        # Database Configuration (SQLite)
        self.DATABASE_URL = os.getenv(
            "DATABASE_URL", 
            f"sqlite:///{DATA_DIR}/finance.db"
        )
        self.ASYNC_DATABASE_URL = os.getenv(
            "ASYNC_DATABASE_URL",
            f"sqlite+aiosqlite:///{DATA_DIR}/finance.db"
        )
        
        # Security Configuration
        self.SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
        self.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
        self.JWT_ALGORITHM = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours
        
        # Server Configuration
        self.HOST = os.getenv("HOST", "0.0.0.0")
        self.PORT = int(os.getenv("PORT", "8001"))
        
        # Ollama Configuration
        self.OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
        self.OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        self.OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "30"))
        
        # File Upload Configuration
        self.MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", str(10 * 1024 * 1024)))  # 10MB
        self.ALLOWED_FILE_EXTENSIONS = [".csv", ".xlsx"]
        self.UPLOAD_DIR = DATA_DIR / "uploads"
        
        # Data Processing Configuration
        self.DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "EUR")
        self.DEFAULT_LOCALE = os.getenv("DEFAULT_LOCALE", "en-US")
        self.CSV_PROCESSING_BATCH_SIZE = int(os.getenv("CSV_PROCESSING_BATCH_SIZE", "1000"))
        
        # Privacy & Security Settings
        self.DATA_RETENTION_DAYS = int(os.getenv("DATA_RETENTION_DAYS", "0"))  # 0 = keep forever
        self.AUTO_BACKUP_ENABLED = os.getenv("AUTO_BACKUP_ENABLED", "false").lower() == "true"
        self.BACKUP_DIR = DATA_DIR / "backups"
        
        # Logging Configuration
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_DIR = PROJECT_ROOT / "logs"
        self.LOG_ROTATION = os.getenv("LOG_ROTATION", "daily")
        
        # Rate Limiting (for local security)
        self.RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
        self.RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
        self.RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds
        
        # Development Settings
        self.RELOAD = os.getenv("RELOAD", "false").lower() == "true"
        self.TESTING = os.getenv("TESTING", "false").lower() == "true"
        
        # Ensure directories exist
        self._ensure_directories()
    
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        """CORS origins for local development"""
        cors_env = os.getenv("ALLOWED_ORIGINS", "")
        
        if cors_env:
            # Parse from environment
            origins = [origin.strip() for origin in cors_env.split(",") if origin.strip()]
            print(f"✅ CORS Origins from env: {origins}")
            return origins
        
        # Default local origins
        default_origins = [
            "http://localhost:5173",    # Vite dev server
            "http://127.0.0.1:5173",   # Alternative localhost
            "http://localhost:3000",    # Alternative frontend port
            "http://127.0.0.1:3000",   # Alternative localhost
            "http://localhost:8080",    # Another common port
            "http://127.0.0.1:8080"    # Alternative localhost
        ]
        
        print(f"✅ Using default CORS origins: {default_origins}")
        return default_origins
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
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
        """Database configuration for SQLAlchemy"""
        return {
            "url": self.ASYNC_DATABASE_URL,
            "echo": self.DEBUG,
            "pool_pre_ping": True,
            "pool_recycle": 300
        }
    
    @property
    def ollama_config(self) -> dict:
        """Ollama LLM configuration"""
        return {
            "api_url": self.OLLAMA_API_URL,
            "model": self.OLLAMA_MODEL,
            "timeout": self.OLLAMA_TIMEOUT
        }
    
    @property
    def security_config(self) -> dict:
        """Security configuration"""
        return {
            "secret_key": self.SECRET_KEY,
            "jwt_secret_key": self.JWT_SECRET_KEY,
            "jwt_algorithm": self.JWT_ALGORITHM,
            "access_token_expire_minutes": self.ACCESS_TOKEN_EXPIRE_MINUTES
        }
    
    def get_environment_info(self) -> dict:
        """Get environment information for debugging"""
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
        """Validate configuration and return any issues"""
        issues = []
        
        # Check if Ollama is reachable
        try:
            import requests
            response = requests.get(f"{self.OLLAMA_API_URL}/api/tags", timeout=5)
            if response.status_code != 200:
                issues.append(f"Ollama not reachable at {self.OLLAMA_API_URL}")
        except Exception:
            issues.append(f"Cannot connect to Ollama at {self.OLLAMA_API_URL}")
        
        # Check if database directory is writable
        try:
            test_file = DATA_DIR / "test_write.tmp"
            test_file.write_text("test")
            test_file.unlink()
        except Exception:
            issues.append(f"Data directory not writable: {DATA_DIR}")
        
        # Check secret keys
        if len(self.SECRET_KEY) < 32:
            issues.append("SECRET_KEY should be at least 32 characters")
        
        if len(self.JWT_SECRET_KEY) < 32:
            issues.append("JWT_SECRET_KEY should be at least 32 characters")
        
        return issues

# Create settings instance
settings = Settings()

# Print configuration on import (only in debug mode)
if settings.DEBUG:
    print("🔧 Azimuth Core Configuration:")
    print(f"   App: {settings.APP_NAME} v{settings.VERSION}")
    print(f"   Database: {settings.DATABASE_URL}")
    print(f"   Ollama: {settings.OLLAMA_API_URL} ({settings.OLLAMA_MODEL})")
    print(f"   Data Dir: {DATA_DIR}")
    print(f"   CORS: {len(settings.ALLOWED_ORIGINS)} origins configured")
    
    # Validate configuration
    config_issues = settings.validate_config()
    if config_issues:
        print("⚠️ Configuration Issues:")
        for issue in config_issues:
            print(f"   - {issue}")
    else:
        print("✅ Configuration validation passed")