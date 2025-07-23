# JSON-based database initialization
# This module provides database functionality without SQLite dependencies

def init_app(app=None):
    """Initialize database for the application"""
    # No initialization needed for JSON-based storage
    pass

def get_db():
    """Get database instance - compatibility function"""
    from .models import Database
    return Database()

def close_db(e=None):
    """Close database connection - compatibility function"""
    # No connection to close for JSON-based storage
    pass