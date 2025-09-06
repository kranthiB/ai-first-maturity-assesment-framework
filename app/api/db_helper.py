"""
Database Helper for API Endpoints

Provides database session management for API endpoints.
"""

from flask import current_app
from sqlalchemy.orm import sessionmaker
from app.models.database import get_database_adapter


def get_db_session():
    """
    Get a database session for the current application context.
    
    Returns:
        Session: SQLAlchemy session object
    """
    adapter = get_database_adapter(current_app.config)
    Session = sessionmaker(bind=adapter.get_engine())
    return Session()


def close_db_session(session):
    """
    Close a database session safely.
    
    Args:
        session: SQLAlchemy session to close
    """
    try:
        session.close()
    except Exception:
        pass  # Ignore errors during session cleanup
