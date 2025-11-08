# app/routers/__init__.py

# Import all routers for easy access
from . import auth
from . import chat
from . import categories_router
from . import transactions_router

# Make routers available for import
__all__ = [
    "auth",
    "chat",
    "categories_router",
    "transactions_router"
]