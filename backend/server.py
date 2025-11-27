"""
Development Server Wrapper

Simple wrapper script to run the FastAPI application with Uvicorn ASGI server
Adds current directory to Python path for proper module imports

Usage:
    python backend/server.py

This is an alternative to running directly from main.py
Useful for development server with auto-reload enabled
"""

import sys
import os

# Add backend directory to Python path
# Allows imports like: from app.main import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the FastAPI application instance from main module
from app.main import app

if __name__ == "__main__":
    """
    Start development server with Uvicorn
    
    Configuration:
    - Host: 0.0.0.0 (accessible from network)
    - Port: 8001
    - Reload: True (auto-reload on code changes)
    
    Server will restart automatically when Python files change
    """
    import uvicorn
    
    uvicorn.run(
        "server:app",       # Module path to app instance
        host="0.0.0.0",     # Bind to all network interfaces
        port=8001,          # API server port
        reload=True         # Enable auto-reload for development
    )